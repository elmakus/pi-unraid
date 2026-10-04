"""Synthetic regression for strict readback, acquisition and cleanup.

No real Docker/Paseo/provider is reachable: all external execution is replaced
by the existing isolated fake boundary. These tests do NOT qualify that older
boundary as full source-faithful realization evidence. The observer and guard
are actual shipped programs in the inherited harness; daemon reconstruction
remains an explicit full-Card gap, not an acceptance waiver.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from tests import test_m07_t05_validator_adapter as H
T = H.T
A, V = H.A, H.V


class ReadbackCleanupTests(unittest.TestCase):
    def validate(self, **kwargs):
        with tempfile.TemporaryDirectory() as td, T.LocalCodexServer() as server:
            return H._run_validate(Path(td), server_base=server.base,
                                   execution_class='real', **kwargs)

    def test_all_malformed_wrong_subject_and_unknown_field_rows_rejected(self):
        positive = [dict(test_id='owned', kind='request', model=A.FIXED_MODEL, effort='max'),
                    dict(test_id='owned', kind='response', status='200'),
                    dict(test_id='owned', kind='terminal', status='completed'),
                    dict(test_id='owned', kind='terminal', status='settled')]
        base = '\n'.join(map(json.dumps, positive))
        self.assertEqual(A.aggregate_witness(A.parse_witness_readback(base, 'owned'),
                         test_id='owned', expected_model=A.FIXED_MODEL)['gate'], 'PASS')
        for row in ('{broken', '[]', '{}', json.dumps(dict(test_id='other', kind='terminal', status='aborted')),
                    json.dumps(dict(test_id='owned', kind='response', status=200)),
                    json.dumps(dict(test_id='owned', kind='terminal', status='settled', extra='public'))):
            with self.subTest(row=row), self.assertRaises(A.AdapterError):
                A.parse_witness_readback(base + '\n' + row, 'owned')

    def test_malformed_and_wrong_subject_at_genuine_validate_boundary(self):
        original = T.make_fake_docker
        for appended in ('{broken', json.dumps(dict(test_id='another', kind='terminal', status='aborted'))):
            def boundary(*args, **kwargs):
                fake = original(*args, **kwargs)
                def run(argv, **opts):
                    proc = fake(argv, **opts)
                    if argv[:2] == ['docker', 'exec'] and 'witness-read' in argv[-1]:
                        proc.stdout += '\n' + appended
                    return proc
                return run
            with self.subTest(appended=appended), mock.patch.object(T, 'make_fake_docker', side_effect=boundary):
                result, calls, state = self.validate()
                self.assertEqual(result['status'], 'FAIL', result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertTrue(any('guarded-dispatch' in str(c) for c in calls))

    def test_daemon_without_selected_pi_blocks_before_dispatch(self):
        daemon = dict(home='/home/paseo/.paseo', listen='127.0.0.1:7777', pid=1234,
                      daemonVersion=T.REAL_PASEO, localDaemon='running', connectedDaemon='reachable',
                      workerPid=1235, serverId='synthetic-server', daemonNode='/usr/bin/node',
                      providers=['codex-lb'])
        result, calls, _ = self.validate(daemon_json=daemon)
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertFalse(any('guarded-dispatch' in str(c) for c in calls))

    def test_failed_container_removal_cannot_coexist_with_real_success(self):
        result, calls, _ = self.validate(extra_state={'remove_failure': True})
        self.assertEqual(result['status'], 'BLOCKED', result)
        self.assertFalse(result['real_validation_satisfied'])
        self.assertEqual(result['cleanup']['status'], 'INCOMPLETE')
        self.assertIn('acquired container removal failed', result['cleanup']['issues'])
        self.assertTrue(any(c[:2] == ['docker', 'rm'] for c in calls))

    def test_positive_absence_is_exact_not_generic_inspect_failure(self):
        ident = 'disposable-object'
        for text in ('No such', 'permission denied', 'transport failed',
                     'Error: No such object: other'):
            self.assertFalse(V._positive_absence(mock.Mock(returncode=1, stdout='', stderr=text), ident))
        self.assertTrue(V._positive_absence(mock.Mock(returncode=1, stdout='',
                        stderr=f'Error: No such object: {ident}'), ident))

    def test_hold_entrypoint_prevents_upstream_start_before_staging(self):
        result, calls, _ = self.validate()
        self.assertEqual(result['status'], 'PASS', result)
        argv = next(c for c in calls if c[:2] == ['docker', 'run'])
        self.assertEqual(argv[argv.index('--entrypoint') + 1], '/bin/sh')
        self.assertIn('--no-healthcheck', argv)
        self.assertEqual(argv[-2:], ['-c', 'exec sleep infinity'])
        self.assertFalse(result['execution_class'] == 'fixture' and result['real_validation_satisfied'])

    def test_failed_absence_does_not_create_any_network_or_container(self):
        original = T.make_fake_docker
        def boundary(*args, **kwargs):
            fake = original(*args, **kwargs)
            def run(argv, **opts):
                if argv[:3] == ['docker', 'network', 'inspect']:
                    kwargs['calls'].append(argv)
                    return mock.Mock(returncode=1, stdout='', stderr='synthetic permission failure')
                return fake(argv, **opts)
            return run
        with mock.patch.object(T, 'make_fake_docker', side_effect=boundary):
            result, calls, _ = self.validate()
        self.assertEqual(result['status'], 'BLOCKED', result)
        self.assertFalse(any(c[:3] == ['docker', 'network', 'create'] or c[:2] == ['docker', 'run'] for c in calls))


class FrozenDeliveryTests(unittest.TestCase):
    def test_generated_helper_bytes_match_frozen_delivered_payload(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            observer = A.stage_witness_extension(p / 'observer.js')
            loader = A.stage_candidate_env(p / 'loader.sh')
            self.assertEqual(observer.read_bytes(), (T.ROOT / 'config/pi-agent/extensions/m07-t05-witness.js').read_bytes())
            self.assertEqual(loader.read_bytes(), (T.ROOT / 'config/pi-agent/bin/m07-t05-candidate-env.sh').read_bytes())
        for filename in ('paseo_codex_noninference.py', 'paseo_codex_candidate_check.py'):
            self.assertEqual((T.ROOT / 'scripts' / filename).read_bytes(),
                             (T.ROOT / 'config/pi-agent/bin' / filename).read_bytes())

    def test_used_validation_source_mutation_breaks_existing_companion_binding(self):
        from tests import test_paseo_candidate_build_pipeline as B
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(T.ROOT / 'config/pi-agent', root / 'config/pi-agent')
            B.validation_sources(root)
            declared = B.BUILD.companion_bundle_identity(root)
            B.BUILD.verify_companion_binding(root, declared)
            victim = root / 'scripts/paseo_candidate_muse_adapter.py'
            victim.write_bytes(victim.read_bytes() + b'\n# synthetic public mutation\n')
            with self.assertRaises(B.BUILD.CandidateBuildError):
                B.BUILD.verify_companion_binding(root, declared)

    def test_shipped_observer_does_not_register_without_candidate_opt_in(self):
        node = T._find_node()
        self.assertIsNotNone(node, 'this verification requires Node; no silent skip')
        script = "const m=await import(process.argv[1]);let n=0;m.default({on:()=>n++});if(n!==0)process.exit(1);"
        proc = subprocess.run([node, '--input-type=module', '-e', script,
                               str(T.ROOT / 'config/pi-agent/extensions/m07-t05-witness.js')],
                              env={'PATH': '/usr/bin:/bin'}, text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 0)


if __name__ == '__main__':
    unittest.main()
