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
                    before = boundary == 'guard-entry' and argv[:2] == ['docker', 'exec'] and '--candidate-owned' in str(argv[-1])
                    if before and not observed['mutated']:
                        mutate(state['_owned_runtime']); observed['mutated'] = True
                    outcome = external(argv, **options)
                    after = (boundary == 'catalog' and 'provider' in argv and 'models' in argv
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
