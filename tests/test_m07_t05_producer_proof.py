"""Reach actual producer -> shipped validator under external-only fakes.

All records originate from genuine producer functions; only controlled mutations
for negative controls reserialize them. No real inference/auth/Docker/Git remote.
"""
import copy
import hashlib
import io
import json
import tarfile
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from tests import test_m07_t05_validator_adapter as H

T, V = H.T, H.V


def relink(chain):
    candidate, handoff, prepared, tested_path, record_path, publication_path = chain
    tested = json.loads(tested_path.read_bytes())
    publication = json.loads(publication_path.read_bytes())
    for path, key in ((record_path, 'build_record_sha256'), (candidate, 'candidate_file_sha256'),
                      (handoff, 'handoff_evidence_sha256')):
        digest = 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
        tested[key] = publication[key] = digest
    tested_path.write_text(json.dumps(tested))
    publication['tested_image_evidence_sha256'] = 'sha256:' + hashlib.sha256(tested_path.read_bytes()).hexdigest()
    publication_path.write_text(json.dumps(publication))


class ProducerProofTests(unittest.TestCase):
    def test_actual_complete_chain_reaches_guarded_fixture_exchange(self):
        with tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
            result, calls, state = H._run_validate(Path(td), server_base=server.base)
            self.assertEqual(result['status'], 'PASS', result)
            self.assertEqual(result['checks']['immutable_source_configuration'], 'PASS')
            self.assertFalse(result['real_validation_satisfied'])
            self.assertEqual(state['runtime_calls_before_cleanup'].count('prompt'), 1)
            self.assertEqual(state['runtime_calls_before_cleanup'].count('fake-transport'), 1)

    def test_changed_configuration_after_acquisition_is_rejected_before_prompt(self):
        original = T.make_fake_docker
        with tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
            root = Path(td)
            def boundary(*args, **kwargs):
                external = original(*args, **kwargs)
                def run(argv, **options):
                    outcome = external(argv, **options)
                    if argv[:2] == ['docker', 'exec'] and 'models' in argv and 'provider' in argv:
                        config = T.fixture_source(root) / '.github/workflows/paseo-candidate-build.yml'
                        config.write_text(config.read_text() + '\n# synthetic post-acquisition configuration drift\n')
                    return outcome
                return run
            with mock.patch.object(T, 'make_fake_docker', side_effect=boundary):
                result, calls, state = H._run_validate(root, server_base=server.base)
            self.assertEqual(result['status'], 'FAIL', result)
            self.assertFalse(result['real_validation_satisfied'])
            self.assertNotIn('prompt', state['runtime_calls_before_cleanup'])
            self.assertNotIn('fake-transport', state['runtime_calls_before_cleanup'])
            self.assertFalse(any('guarded-dispatch' in str(call) for call in calls))

    def test_actual_validator_rejects_numeric_mount_booleans_before_exec_or_cleanup_removal(self):
        original = T.make_fake_docker
        for destination, value in (('/home/paseo', 1), (V.CODEX_SECRET_TARGET, 0)):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
                def boundary(*args, **kwargs):
                    external = original(*args, **kwargs)
                    def run(argv, **options):
                        proc = external(argv, **options)
                        if argv[:2] == ['docker', 'inspect'] and kwargs['state'].get('ran') and proc.returncode == 0:
                            docs = json.loads(proc.stdout)
                            for mount in docs[0]['Mounts']:
                                if mount['Destination'] == destination:
                                    mount['RW'] = value
                            proc.stdout = json.dumps(docs)
                        return proc
                    return run
                with mock.patch.object(T, 'make_fake_docker', side_effect=boundary):
                    result, calls, state = H._run_validate(Path(td), server_base=server.base)
                self.assertEqual(result['status'], 'FAIL', result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertFalse(any(call[:2] == ['docker', 'exec'] for call in calls))
                self.assertFalse(any(call[:2] == ['docker', 'rm'] for call in calls))
                self.assertTrue(Path(state['work']).exists())
                self.assertEqual((Path(td) / 'codex.env').read_text(), 'CODEX_LB_API_KEY=fixture-codex\n')

    def test_partial_network_or_container_receipt_loss_retains_references_without_replay(self):
        original = T.make_fake_docker
        for effect in ('network', 'container'):
            with self.subTest(effect=effect), tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
                def boundary(*args, **kwargs):
                    external = original(*args, **kwargs)
                    def run(argv, **options):
                        proc = external(argv, **options)
                        if ((effect == 'network' and argv[:3] == ['docker', 'network', 'create'])
                                or (effect == 'container' and argv[:2] == ['docker', 'run'])):
                            raise V.ValidationError('synthetic lost receipt after external acquisition')
                        return proc
                    return run
                with mock.patch.object(T, 'make_fake_docker', side_effect=boundary):
                    result, calls, state = H._run_validate(Path(td), server_base=server.base)
                self.assertEqual(result['status'], 'UNKNOWN', result)
                self.assertEqual(result['terminal_class'], 'unknown')
                self.assertFalse(result['real_validation_satisfied'])
                self.assertEqual(sum(call[:3] == ['docker','network','create'] for call in calls), 1)
                self.assertEqual(sum(call[:2] == ['docker','run'] for call in calls), int(effect == 'container'))
                self.assertFalse(any(call[:2] == ['docker','exec'] for call in calls))
                self.assertFalse(any(call[:2] == ['docker','rm'] or call[:3] == ['docker','network','rm'] for call in calls))
                reference = Path(result['owned_reference'])
                self.assertTrue(reference.exists())
                acquired = json.loads(reference.read_bytes())
                self.assertEqual(acquired['network']['name'], 'pi-unraid-validator')
                self.assertTrue(acquired['attempt_nonce'])
                self.assertTrue(reference.stat().st_mode & 0o777 == 0o600)
                self.assertEqual((Path(td) / 'muse.env').read_text(), 'META_API_KEY=fixture-meta\n')

    def test_network_cleanup_failure_retains_private_usable_nonce_and_object_references(self):
        original = T.make_fake_docker
        for fault in ('remove', 'inspect'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
                def boundary(*args, **kwargs):
                    external = original(*args, **kwargs)
                    def run(argv, **options):
                        state = kwargs['state']
                        if fault == 'remove' and argv[:3] == ['docker','network','rm']:
                            kwargs['calls'].append(argv)
                            return mock.Mock(returncode=1, stdout='', stderr='synthetic network removal failure')
                        if (fault == 'inspect' and argv[:3] == ['docker','network','inspect']
                                and state.get('_owned_runtime') and not state.get('ran')):
                            kwargs['calls'].append(argv)
                            raise V.ValidationError('synthetic cleanup transport failure')
                        return external(argv, **options)
                    return run
                with mock.patch.object(T, 'make_fake_docker', side_effect=boundary):
                    result, calls, state = H._run_validate(Path(td), server_base=server.base)
                self.assertEqual(result['status'], 'BLOCKED', result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertEqual(result['cleanup']['status'], 'INCOMPLETE')
                self.assertEqual(state['runtime_calls_before_cleanup'].count('prompt'), 1)
                self.assertEqual(state['runtime_calls_before_cleanup'].count('fake-transport'), 1)
                work = Path(result['recovery_reference']['work'])
                self.assertTrue(work.exists())
                reference = json.loads(Path(result['subject']['owned_test']).read_bytes())
                self.assertEqual(reference['attempt_nonce'], (work / '.attempt-nonce').read_text().strip())
                self.assertEqual(reference['network']['id'], result['recovery_reference']['network_id'])
                self.assertTrue((work / 'home/.m07-t05/owned.json').exists())

    def test_self_consistently_relinked_archive_platform_rootfs_and_layer_forgeries(self):
        original = T.build_artifact_chain
        for fault in ('architecture', 'os', 'rootfs', 'layer'):
            def changed(td, **kwargs):
                chain = original(td, **kwargs)
                _, _, _, tested_path, record_path, publication_path = chain
                archive_path = tested_path.parent / 'image.tar'
                with tarfile.open(archive_path) as archive:
                    entries = {v.name:archive.extractfile(v).read() for v in archive.getmembers() if v.isfile()}
                manifest = json.loads(entries['manifest.json'])
                old_name = manifest[0]['Config']
                config = json.loads(entries.pop(old_name))
                if fault == 'architecture': config['architecture'] = True
                elif fault == 'os': config['os'] = 'windows'
                elif fault == 'rootfs': config['rootfs']['type'] = True
                elif fault == 'layer': config['rootfs']['diff_ids'][0] = 'sha256:' + '0'*64
                config_bytes = json.dumps(config, sort_keys=True).encode()
                image_id = 'sha256:' + hashlib.sha256(config_bytes).hexdigest()
                new_name = image_id[7:] + '.json'
                entries[new_name] = config_bytes
                manifest[0]['Config'] = new_name
                entries['manifest.json'] = json.dumps(manifest).encode()
                with tarfile.open(archive_path, 'w') as archive:
                    for name, raw in entries.items():
                        member = tarfile.TarInfo(name);member.size = len(raw)
                        archive.addfile(member, io.BytesIO(raw))
                archive_sha = 'sha256:' + hashlib.sha256(archive_path.read_bytes()).hexdigest()
                for path in (tested_path, publication_path):
                    record = json.loads(path.read_bytes())
                    record.update(image_id=image_id, image_archive_sha256=archive_sha)
                    path.write_text(json.dumps(record))
                record = json.loads(record_path.read_bytes())
                record['image']['id'] = image_id
                record_path.write_text(json.dumps(record))
                relink(chain)
                return chain
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
                with mock.patch.object(T, 'build_artifact_chain', side_effect=changed):
                    result, calls, _ = H._run_validate(Path(td), server_base=server.base, execution_class='real')
                self.assertEqual(result['status'], 'FAIL', result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertEqual(calls, [])

    def test_source_commit_ref_parent_config_and_archive_mutations_before_effects(self):
        original = T.build_artifact_chain
        for defect in ('head', 'parent', 'ref', 'commit-proof', 'file-map', 'source-bytes',
                       'source-missing', 'source-untracked', 'dockerfile', 'readback',
                       'build-command', 'build-context', 'phase-type', 'smoke-omission',
                       'archive-bytes', 'archive-missing', 'archive-format', 'archive-hash', 'candidate-ref',
                       'schema-bool', 'source-schema', 'companion-schema', 'builder-type',
                       'builder-driver', 'cache-type', 'image-type', 'prepared-omission'):
            def changed(td, **kwargs):
                chain = original(td, **kwargs)
                _, _, prepared_path, tested_path, record_path, publication_path = chain
                prepared = json.loads(prepared_path.read_bytes())
                tested = json.loads(tested_path.read_bytes())
                record = json.loads(record_path.read_bytes())
                publication = json.loads(publication_path.read_bytes())
                source = T.fixture_source(td)
                if defect == 'head': prepared['source_head'] = '1' * 40
                elif defect == 'parent': prepared['source_parent'] = '2' * 40
                elif defect == 'ref': prepared['source_ref'] = 'refs/heads/foreign'
                elif defect == 'commit-proof': prepared['source_identity']['commit_sha256'] = 'sha256:' + '0' * 64
                elif defect == 'file-map': prepared['staged_files'].pop('Dockerfile')
                elif defect == 'source-bytes': (source / 'scripts/paseo_buildx.py').write_text('# wrong source')
                elif defect == 'source-missing': (source / '.dockerignore').unlink()
                elif defect == 'source-untracked': (source / 'unexpected-input').write_text('synthetic untracked build input')
                elif defect == 'dockerfile': (source / 'Dockerfile').write_text('# changed configuration')
                elif defect == 'readback': prepared['build_readback']['pi_version'] = '9.9.9'
                elif defect == 'build-command': record['build_configuration']['argv'].append('--push')
                elif defect == 'build-context': record['context'] = '/foreign-context'
                elif defect == 'phase-type': record['phases']['test']['duration_ms'] = True
                elif defect == 'smoke-omission': record['phases']['test']['detail']['smokes'].pop()
                elif defect == 'archive-bytes': (tested_path.parent / 'image.tar').write_bytes(b'not-docker-save')
                elif defect == 'archive-missing': (tested_path.parent / 'image.tar').unlink()
                elif defect == 'archive-format': tested['image_archive_format'] = 'oci-layout'
                elif defect == 'archive-hash': publication['image_archive_sha256'] = 'sha256:' + '0' * 64
                elif defect == 'candidate-ref': publication['candidate_ref'] = publication['repository'] + ':accepted'
                elif defect == 'schema-bool': tested['schema_version'] = True
                elif defect == 'source-schema': prepared['source_identity']['schema_version'] = True
                elif defect == 'companion-schema': prepared['companion_bundle']['schema_version'] = True
                elif defect in ('builder-type', 'builder-driver'):
                    if defect == 'builder-type': record['builder']['reused'] = int(record['builder']['reused'])
                    else: record['builder']['driver'] = 'shell'
                    record['phases']['builder_ensure']['detail'] = {k:v for k,v in record['builder'].items() if k != 'state_dir'}
                elif defect == 'cache-type': record['cache']['local_dir'] = 0
                elif defect == 'image-type': record['image']['digests'] = {}
                elif defect == 'prepared-omission': prepared.pop('source_identity')
                prepared_path.write_text(json.dumps(prepared))
                # Keep strings/byte links self-consistent to isolate actual proofs.
                record['prepared_source'] = prepared
                record_path.write_text(json.dumps(record))
                tested_path.write_text(json.dumps(tested))
                publication_path.write_text(json.dumps(publication))
                relink(chain)
                return chain
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
                with mock.patch.object(T, 'build_artifact_chain', side_effect=changed):
                    result, calls, _ = H._run_validate(Path(td), server_base=server.base, execution_class='real')
                self.assertIn(result['status'], ('FAIL', 'BLOCKED'), result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertEqual(calls, [], 'rejection must precede Docker/acquisition/dispatch')


if __name__ == '__main__':
    unittest.main()
