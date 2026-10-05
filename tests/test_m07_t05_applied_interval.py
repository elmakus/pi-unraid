"""Genuine producer/Tower/shipped runtime; mutations only at external boundaries.
All PASS flags below are structural synthetic mechanics, never real evidence.
"""
import json
import os
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tests import test_m07_t05_validator_adapter as H

T = H.T


class AppliedIntervalTests(unittest.TestCase):
    def exercise(self, mutate=None, boundary='catalog', execution_class='real'):
        original = T.make_fake_docker
        observed = {'mutated': False}
        with tempfile.TemporaryDirectory(prefix='applied-interval-') as td, T.LocalCodexServer() as server:
            def factory(*args, **kwargs):
                external = original(*args, **kwargs)
                state = kwargs['state']
                def run(argv, **options):
                    bootstrap = (boundary == 'bootstrap' and argv[:2] == ['docker', 'exec']
                                 and 'interval startup unknown' in str(argv[-1]))
                    if bootstrap and not observed.get('bootstrap_reached'):
                        # Real Docker already has the namespace. Materialize ONLY
                        # the equivalent external fake namespace before injection;
                        # no product checker or acceptance function is replaced.
                        external([*argv[:-1], 'pass'], **options)
                        observed['bootstrap_reached'] = True
                        mutate(state['_owned_runtime']); observed['mutated'] = True
                    before = boundary == 'guard-entry' and argv[:2] == ['docker', 'exec'] and '--candidate-owned' in str(argv[-1])
                    if before and not observed['mutated']:
                        mutate(state['_owned_runtime']); observed['mutated'] = True
                    outcome = external(argv, **options)
                    after = (boundary == 'catalog' and 'provider' in argv and 'models' in argv
                             or boundary == 'readback' and 'file-readback' in str(argv[-1])
                             or boundary == 'completion' and '--candidate-owned' in str(argv[-1]))
                    if mutate and after and not observed['mutated']:
                        mutate(state['_owned_runtime']); observed['mutated'] = True
                    return outcome
                return run
            with mock.patch.object(T, 'make_fake_docker', side_effect=factory):
                result, calls, state = H._run_validate(Path(td), server_base=server.base, execution_class=execution_class)
            runtime = state.get('_owned_runtime')
            methods = state.get('runtime_calls_before_cleanup', runtime.calls() if runtime else [])
            refs = runtime.home / '.m07-t05/owned.json' if runtime else None
            retained = json.loads(refs.read_text()) if refs and refs.exists() else None
            if runtime:
                observed['shadow_module_executed_before_cleanup'] = (runtime.tmp / 'shadow-module-executed').exists()
                runtime.close()
            return result, calls, methods, observed, retained

    def test_unchanged_fixture_and_structural_real_gate(self):
        for execution in ('fixture', 'real'):
            with self.subTest(execution=execution):
                result, calls, methods, _, _ = self.exercise(execution_class=execution)
                self.assertEqual(result['status'], 'PASS', result.get('reason'))
                self.assertEqual(result['checks']['applied_payload_interval'], 'PASS')
                self.assertEqual(result['real_validation_satisfied'], execution == 'real')
                self.assertEqual(methods.count('prompt'), 1)
                self.assertEqual(methods.count('fake-transport'), 1)
                command = next(c for c in calls if c[:2] == ['docker', 'run'])
                self.assertTrue(any(c.endswith(':/home/paseo/.pi/agent:ro') for c in command))

    def test_every_declared_member_byte_drift_after_catalog(self):
        members = sorted(p.relative_to(T.ROOT / 'config/pi-agent').as_posix()
                         for p in (T.ROOT / 'config/pi-agent').rglob('*') if p.is_file())
        for member in members:
            with self.subTest(member=member):
                def mutate(runtime):
                    file = runtime.agent / member
                    file.write_bytes(file.read_bytes() + b'\nsynthetic byte drift\n')
                result, calls, methods, observed, _ = self.exercise(mutate)
                self.assertTrue(observed['mutated'])
                self.assertEqual(result['status'], 'FAIL', result.get('reason'))
                self.assertFalse(result['real_validation_satisfied'])
                self.assertNotIn('prompt', methods)
                self.assertNotIn('fake-transport', methods)
                self.assertFalse(any('--candidate-owned' in str(c[-1]) for c in calls))

    def test_set_mode_omission_replacement_and_write_restore(self):
        def extra(r):
            (r.agent / 'extensions/unowned-extra.js').write_text('// external synthetic addition\n')
        def mode(r):
            (r.agent / 'bin/run-llm-test.sh').chmod(0o777)
        def omit(r):
            (r.agent / 'extensions/m07-t05-witness.js').unlink()
        def replace(r):
            target = r.agent / 'policies/llm-test-policy.json'
            raw = target.read_bytes(); target.unlink(); target.write_bytes(raw); target.chmod(0o644)
        def restore(r):
            target = r.agent / 'bin/run-llm-test.sh'
            raw = target.read_bytes(); target.write_bytes(raw + b'\n# transient change\n'); target.write_bytes(raw)
        def symlink(r):
            target = r.agent / 'policies/llm-test-policy.json'
            outside = r.root / 'unowned-policy'; outside.write_bytes(target.read_bytes())
            target.unlink(); target.symlink_to(outside)
        def root_replace(r):
            detached = r.root / 'unowned-detached-agent'
            r.agent.rename(detached); shutil.copytree(detached, r.agent)
        def parent_mode(r):
            r.agent.parent.chmod(0o755)
        for mutation in (extra, mode, omit, replace, restore, symlink, root_replace, parent_mode):
            with self.subTest(mutation=mutation.__name__):
                result, _, methods, _, _ = self.exercise(mutation)
                self.assertEqual(result['status'], 'FAIL', result.get('reason'))
                self.assertFalse(result['real_validation_satisfied'])
                self.assertNotIn('prompt', methods); self.assertNotIn('fake-transport', methods)

    def test_source_frozen_bootstrap_rejects_substituted_checker_and_expectations(self):
        def checker(r):
            file = r.agent / 'bin/m07-t05-applied.py'
            text = file.read_text()
            marker = "if __name__ == '__main__':"
            assert text.count(marker) == 1
            file.write_text(text.replace(marker, 'snapshot = lambda root, rows: {}\n' + marker))
        def coupled(r):
            file = r.agent / 'bin/run-llm-test.sh'
            suffix = '\n# coupled external bootstrap drift\n'
            file.write_text(file.read_text() + suffix)
            manifest = r.home / '.m07-t05/applied-manifest.json'
            doc = json.loads(manifest.read_text())
            doc['files']['bin/run-llm-test.sh']['content'] += suffix
            manifest.write_text(json.dumps(doc, sort_keys=True))
        def checker_coupled(r):
            checker(r)
            file = r.home / '.m07-t05/applied-manifest.json'
            doc = json.loads(file.read_text())
            doc['files']['bin/m07-t05-applied.py']['content'] = (r.agent / 'bin/m07-t05-applied.py').read_text()
            file.write_text(json.dumps(doc, sort_keys=True))
        def manifest_symlink(r):
            file = r.home / '.m07-t05/applied-manifest.json'
            outside = r.root / 'external-manifest'; outside.write_bytes(file.read_bytes()); outside.chmod(0o600)
            file.unlink(); file.symlink_to(outside)
        def manifest(r):
            file = r.home / '.m07-t05/applied-manifest.json'
            doc = json.loads(file.read_text()); doc['files'].pop('bin/run-llm-test.sh')
            file.write_text(json.dumps(doc, sort_keys=True))
        def manifest_omit(r):
            (r.home / '.m07-t05/applied-manifest.json').unlink()
        def manifest_mode(r):
            (r.home / '.m07-t05/applied-manifest.json').chmod(0o644)
        def file_mode(r):
            (r.agent / 'bin/run-llm-test.sh').chmod(0o777)
        def file_omit(r):
            (r.agent / 'extensions/m07-t05-witness.js').unlink()
        def extra(r):
            (r.agent / 'unexpected').write_text('external addition')
        def config(r):
            file = r.home / '.paseo/config.json'
            doc = json.loads(file.read_text()); doc['pluginsEnabled'] = True
            file.write_text(json.dumps(doc))
        def checker_symlink(r):
            file = r.agent / 'bin/m07-t05-applied.py'
            outside = r.root / 'substituted-checker'; outside.write_bytes(file.read_bytes())
            file.unlink(); file.symlink_to(outside)
        for mutation in (checker, coupled, checker_coupled, manifest, manifest_omit,
                         manifest_mode, manifest_symlink, file_mode, file_omit, extra,
                         config, checker_symlink):
            with self.subTest(mutation=mutation.__name__):
                result, calls, methods, seen, _ = self.exercise(mutation, boundary='bootstrap')
                self.assertTrue(seen['bootstrap_reached']); self.assertTrue(seen['mutated'])
                self.assertEqual(result['status'], 'FAIL', result.get('reason'))
                self.assertFalse(result['real_validation_satisfied'])
                self.assertNotIn('prompt', methods); self.assertNotIn('fake-transport', methods)
                self.assertFalse(any('--candidate-owned' in str(c[-1]) for c in calls))
                self.assertFalse(any('daemon-bringup' in str(c[-1]) for c in calls))

    def test_frozen_instructions_ignore_writable_cwd_python_modules(self):
        observed = {}
        def substitute(r):
            marker = r.tmp / 'shadow-module-executed'
            for name in ('json', 'subprocess', 'socket', 'hashlib', 'base64', 'zlib'):
                (r.tmp / (name + '.py')).write_text(
                    'from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("substituted")\n'
                    'raise RuntimeError("external cwd code must never execute")\n')
            observed['marker'] = marker
        result, calls, methods, seen, _ = self.exercise(substitute, boundary='bootstrap')
        self.assertTrue(seen['bootstrap_reached']); self.assertTrue(seen['mutated'])
        self.assertEqual(result['status'], 'PASS', result.get('reason'))
        self.assertEqual(methods.count('prompt'), 1); self.assertEqual(methods.count('fake-transport'), 1)
        self.assertFalse(seen['shadow_module_executed_before_cleanup'])
        startup = next(c for c in calls if 'interval startup unknown' in str(c[-1]))
        self.assertIn('-I', startup); self.assertIn('-S', startup); self.assertIn('-B', startup)

    def test_bootstrap_transport_uncertainty_never_admits_runtime_effects(self):
        original = T.make_fake_docker
        for fault in ('missing', 'wrong-digest', 'wrong-pid', 'exit'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='m7unknown-') as td, T.LocalCodexServer() as server:
                seen = {'injected': False}
                def factory(*args, **kwargs):
                    external = original(*args, **kwargs)
                    def run(argv, **options):
                        result = external(argv, **options)
                        if (argv[:2] == ['docker', 'exec'] and 'interval startup unknown' in str(argv[-1])
                                and not seen['injected']):
                            self.assertEqual(result.returncode, 0)
                            doc = json.loads(result.stdout)
                            if fault == 'missing':
                                result.stdout = ''
                            elif fault == 'exit':
                                result.returncode = 20
                            else:
                                doc['manifest_sha256' if fault == 'wrong-digest' else 'pid'] = '0' * 64 if fault == 'wrong-digest' else 0
                                result.stdout = json.dumps(doc)
                            seen['injected'] = True
                        return result
                    return run
                with mock.patch.object(T, 'make_fake_docker', side_effect=factory):
                    result, calls, state = H._run_validate(Path(td), server_base=server.base)
                runtime = state.get('_owned_runtime')
                methods = state.get('runtime_calls_before_cleanup', runtime.calls() if runtime else [])
                if runtime:
                    runtime.close()
                self.assertTrue(seen['injected'])
                self.assertEqual(result['status'], 'FAIL', result.get('reason'))
                self.assertFalse(result['real_validation_satisfied'])
                self.assertNotIn('prompt', methods); self.assertNotIn('fake-transport', methods)
                self.assertFalse(any('daemon-bringup' in str(c[-1]) for c in calls))

    def test_private_inputs_restore_and_replacement_inside_readback_interval(self):
        def manifest_restore(r):
            file = r.home / '.m07-t05/applied-manifest.json'
            raw = file.read_bytes(); file.write_bytes(raw + b' '); file.write_bytes(raw)
        def config_replace(r):
            file = r.home / '.paseo/config.json'
            raw = file.read_bytes(); file.unlink(); file.write_bytes(raw); file.chmod(0o600)
        def config_restore(r):
            file = r.home / '.paseo/config.json'
            raw = file.read_bytes(); file.write_bytes(raw + b' '); file.write_bytes(raw)
        def payload_restore(r):
            file = r.agent / 'bin/m07-t05-applied.py'
            raw = file.read_bytes(); file.write_bytes(raw + b'\n# transient substitution\n'); file.write_bytes(raw)
        def payload_replace(r):
            file = r.agent / 'bin/run-llm-test.sh'
            raw = file.read_bytes(); file.unlink(); file.write_bytes(raw); file.chmod(0o755)
        for mutation in (manifest_restore, config_replace, config_restore, payload_restore, payload_replace):
            with self.subTest(mutation=mutation.__name__):
                result, _, methods, seen, _ = self.exercise(mutation, boundary='readback')
                self.assertTrue(seen['mutated'])
                self.assertEqual(result['status'], 'FAIL', result.get('reason'))
                self.assertFalse(result['real_validation_satisfied'])
                self.assertNotIn('prompt', methods); self.assertNotIn('fake-transport', methods)

    def test_guard_entry_drift_rejected_without_prompt(self):
        def mutate(r):
            file = r.agent / 'bin/run-llm-test.sh'
            file.write_bytes(file.read_bytes() + b'\n# guard entry drift\n')
        result, _, methods, _, _ = self.exercise(mutate, boundary='guard-entry')
        self.assertIn(result['status'], ('FAIL', 'UNKNOWN'))
        self.assertFalse(result['real_validation_satisfied'])
        self.assertNotIn('prompt', methods); self.assertNotIn('fake-transport', methods)

    def test_completion_drift_is_unknown_retains_actual_ids_without_replay_or_rm(self):
        def mutate(r):
            file = r.agent / 'extensions/m07-t05-witness.js'
            file.write_bytes(file.read_bytes() + b'\n// completion boundary drift\n')
        result, calls, methods, _, refs = self.exercise(mutate, boundary='completion')
        self.assertEqual(result['status'], 'UNKNOWN', result.get('reason'))
        self.assertFalse(result['real_validation_satisfied'])
        self.assertEqual(methods.count('prompt'), 1); self.assertEqual(methods.count('fake-transport'), 1)
        self.assertFalse(any(c[:3] == ['docker', 'rm', '-f'] for c in calls))
        self.assertEqual(refs['workspace_id'], refs['requested_workspace_id'])
        self.assertEqual(refs['agent_id'], refs['requested_agent_id'])
        self.assertFalse(refs['replay'])

    def test_readonly_mount_omission_type_and_source_are_required_before_exec(self):
        original = T.make_fake_docker
        for fault in ('missing', 'writable', 'numeric', 'source'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
                def factory(*args, **kwargs):
                    external = original(*args, **kwargs)
                    def run(argv, **options):
                        result = external(argv, **options)
                        if argv[:2] == ['docker', 'inspect'] and result.returncode == 0:
                            objects = json.loads(result.stdout)
                            mounts = objects[0]['Mounts']
                            applied = next(m for m in mounts if m['Destination'] == '/home/paseo/.pi/agent')
                            if fault == 'missing':
                                mounts.remove(applied)
                            elif fault == 'source':
                                applied['Source'] = str(Path(td) / 'foreign')
                            else:
                                applied['RW'] = True if fault == 'writable' else 0
                            result.stdout = json.dumps(objects)
                        return result
                    return run
                with mock.patch.object(T, 'make_fake_docker', side_effect=factory):
                    result, calls, state = H._run_validate(Path(td), server_base=server.base)
                self.assertEqual(result['status'], 'FAIL')
                self.assertFalse(result['real_validation_satisfied'])
                self.assertFalse(any(c[:2] == ['docker', 'exec'] for c in calls))
                self.assertFalse(any(c[:3] == ['docker', 'rm', '-f'] for c in calls))

    def test_replaced_interval_reference_cannot_borrow_old_peer(self):
        def mutate(r):
            file = r.home / '.m07-t05/applied.json'
            data = json.loads(file.read_text()); data['pid'] = os.getpid(); file.write_text(json.dumps(data))
        result, _, methods, _, _ = self.exercise(mutate)
        self.assertEqual(result['status'], 'FAIL')
        self.assertFalse(result['real_validation_satisfied'])
        self.assertNotIn('prompt', methods)


if __name__ == '__main__':
    unittest.main()
