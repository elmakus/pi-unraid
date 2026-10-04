"""Reach actual producer -> shipped validator under external-only fakes.

All records originate from genuine producer functions; only controlled mutations
for negative controls reserialize them. No real inference/auth/Docker/Git remote.
"""
import copy
import hashlib
import json
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

    def test_source_commit_ref_parent_config_and_archive_mutations_before_effects(self):
        original = T.build_artifact_chain
        for defect in ('head', 'parent', 'ref', 'commit-proof', 'file-map', 'source-bytes',
                       'source-missing', 'source-untracked', 'dockerfile', 'readback',
                       'build-command', 'build-context', 'phase-type', 'smoke-omission',
                       'archive-bytes', 'archive-format', 'archive-hash', 'candidate-ref',
                       'schema-bool', 'prepared-omission'):
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
                elif defect == 'archive-format': tested['image_archive_format'] = 'oci-layout'
                elif defect == 'archive-hash': publication['image_archive_sha256'] = 'sha256:' + '0' * 64
                elif defect == 'candidate-ref': publication['candidate_ref'] = publication['repository'] + ':accepted'
                elif defect == 'schema-bool': tested['schema_version'] = True
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
