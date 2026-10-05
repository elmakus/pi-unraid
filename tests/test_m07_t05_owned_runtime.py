"""Integrated external-only process/transport fixture. No real daemon/auth/inference.

Namespace path translation only; guard, loader, wrapper, bridge and observer
bytes execute unchanged otherwise. Public pinned buildPiLaunch is metadata-only.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import unittest
from tests.test_m07_t05_validator_adapter import A, T
from tests import test_m07_t05_validator_adapter as H


class OwnedRuntimeFixture:
    def __init__(self, root, fault=None, secret_file=None, mounted_home=None):
        self.root = Path(root)
        self.home = Path(mounted_home) if mounted_home is not None else self.root / 'home'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.home.mkdir(exist_ok=True)
        self.tmp = self.root / 'tmp'
        self.tmp.mkdir()
        self.secret = Path(secret_file) if secret_file is not None else self.root / 'synthetic-meta'
        if secret_file is None:
            self.secret.write_text('META_API_KEY=synthetic-disposable-only\n')
            self.secret.chmod(0o600)
        # Genuine validator fixtures translate the mounted operator-input path
        # to the SAME synthetic file, never substitute/copy credential values.
        self.maps = [('/usr/local/lib/node_modules/@getpaseo/cli/dist/utils/client.js',
                      str(self.root / 'external.mjs')),
                     ('/home/paseo', str(self.home)), ('/usr/local/bin', str(self.bin)),
                     ('/run/secrets/pi-unraid-meta', str(self.secret)), ('/tmp', str(self.tmp))]
        self.fault = fault or {}
        (self.home / 'fake-fault.json').write_text(json.dumps(self.fault))
        fixture = T.ROOT / 'tests/fixtures/m07_t05_owned_external.mjs'
        shutil.copyfile(fixture, self.root / 'external.mjs')
        self.agent = self.home / '.pi/agent'
        # One applied tree: genuine Tower fixtures execute the mounted tree,
        # not a second unobserved six-file copy. Only namespace strings change.
        source_agent = self.agent if mounted_home is not None else T.ROOT / 'config/pi-agent'
        sources = [(p.relative_to(source_agent), p.read_text()) for p in source_agent.rglob('*') if p.is_file()]
        for rel, content in sources:
            target = self.agent / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.translate(content))
            target.chmod(0o755 if rel.parts[0] == 'bin' else 0o644)
        node = T._find_node()
        if node is None:
            raise RuntimeError('Node required; no hidden skip')
        (self.bin / 'node').symlink_to(node)
        (self.bin / 'paseo').write_text(f'#!/bin/sh\nexec {node} {self.root}/external.mjs cli "$@"\n')
        (self.bin / 'pi').write_text(f'#!{node}\n' +
            f"import {{runFakePi}} from '{self.root}/external.mjs';\n" +
            f"if(process.argv.includes('--version'))console.log('{self.fault.get('version', '0.87.1')}');else await runFakePi();\n")
        # Node uses .js as ESM only with a private package declaration.
        (self.bin / 'package.json').write_text('{"type":"module"}')
        for p in (self.bin / 'paseo', self.bin / 'pi'):
            p.chmod(0o755)
        if mounted_home is None:
            A.stage_private_runtime(self.home, uid=os.getuid(), gid=os.getgid())
            import stat
            source = T.ROOT / 'config/pi-agent'
            files = sorted(p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file())
            self.applied_code = A.stage_applied_interval(self.home, source,
                {'files': files, 'modes': {rel: '%04o' % stat.S_IMODE((source / rel).stat().st_mode) for rel in files}},
                nonce='standalone-synthetic', uid=os.getuid(), gid=os.getgid())
        config = self.home / '.paseo/config.json'
        config.write_text(self.translate(config.read_text()))
        manifest = self.home / '.m07-t05/applied-manifest.json'
        manifest.write_text(self.translate(manifest.read_text()))

    def translate(self, text):
        import re
        import base64
        import zlib
        # Source-frozen child code travels compressed to bound Docker exec argv.
        # Translate ONLY namespace paths in that transport envelope too; never
        # alter checker logic, expectations, hashes or acceptance observations.
        envelopes = []
        def envelope(match):
            try:
                source = zlib.decompress(base64.b64decode(match.group())).decode('utf8')
            except (ValueError, zlib.error, UnicodeError):
                return match.group()
            encoded = base64.b64encode(zlib.compress(self.translate(source).encode())).decode('ascii')
            envelopes.append(encoded)
            return f'__FROZEN_ENVELOPE_{len(envelopes) - 1}__'
        text = re.sub(r'[A-Za-z0-9+/=]{200,}', envelope, text)
        mapping = dict(self.maps)
        text = re.sub('|'.join(re.escape(k) for k in mapping), lambda m: mapping[m.group()], text)
        for index, encoded in enumerate(envelopes):
            text = text.replace(f'__FROZEN_ENVELOPE_{index}__', encoded)
        return text

    def restore(self, text):
        import re
        mapping = {v: k for k, v in self.maps}
        return re.sub('|'.join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)),
                      lambda m: mapping[m.group()], text)

    def execute(self, argv, timeout=30):
        # Every external executable is explicit: only fixture paseo/pi, shipped
        # programs and system metadata/shell utilities. Never ordinary env.
        argv = [self.translate(str(arg)) for arg in argv]
        result = subprocess.run(argv, env={'PATH':str(self.bin)+':/usr/bin:/bin',
            'HOME':str(self.home)}, cwd=self.tmp, text=True, capture_output=True, timeout=timeout)
        status = self.home / '.paseo/fake-status.json'
        if status.exists() and not hasattr(self, '_daemon_pid'):
            self._daemon_pid = json.loads(status.read_text())['pid']
            self._daemon_start = Path(f'/proc/{self._daemon_pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        result.stdout = self.restore(result.stdout)
        result.stderr = 'synthetic external failure' if result.returncode else ''
        return result

    def exec(self, argv, timeout=30):
        return self.execute(A.controlled_candidate_argv(argv), timeout)

    def calls(self):
        file = self.home / 'fake-calls.jsonl'
        return [json.loads(line)['method'] for line in file.read_text().splitlines()] if file.exists() else []

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        if getattr(self, '_closed', False):
            return
        self._closed = True
        reference = self.home / '.m07-t05/applied.json'
        if reference.exists():
            try:
                info = json.loads(reference.read_text())
                current = Path(f"/proc/{info['pid']}/stat").read_text().rsplit(')', 1)[1].split()[19]
                if current == info['start']:
                    os.killpg(info['pid'], signal.SIGTERM)
            except (ProcessLookupError, FileNotFoundError):
                pass
        pid = getattr(self, '_daemon_pid', None)
        if pid is not None:
            try:
                current = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
                if current == self._daemon_start:
                    os.killpg(pid, signal.SIGTERM)
            except (ProcessLookupError, FileNotFoundError):
                pass

    def run(self):
        peer = A.start_applied_interval(self.exec, self.applied_code)
        daemon = A.ensure_candidate_daemon(self.exec, candidate_home='/home/paseo/.paseo',
            expected_version='0.9.2', env_loader='/home/paseo/.pi/agent/bin/m07-t05-candidate-env.sh',
            meta_pointer='/run/secrets/pi-unraid-meta')
        pi = A.observe_pi_version(self.exec, expected_version='0.87.1')
        A.preflight_candidate_profile(self.exec, candidate_home='/home/paseo/.paseo')
        return A.dispatch_owned_runtime(self.exec, daemon=daemon, pi=pi, test_id='synthetic-owned',
            witness='/tmp/m07-t05-witness.jsonl', applied_peer=peer)


class OwnedRuntimeTests(unittest.TestCase):
    def test_actual_pinned_workspace_schema_rejects_uuid_without_transport(self):
        script = """
import {WorkspaceCreateRequestSchema} from '/usr/local/lib/node_modules/@getpaseo/protocol/dist/messages.js';
const base={type:'workspace.create.request',requestId:'synthetic-request',source:{kind:'directory',path:'/synthetic'}};
console.log(JSON.stringify([
 WorkspaceCreateRequestSchema.safeParse({...base,workspaceId:'2b30e061-0c31-4e63-90cd-69eb0c8aa318'}).success,
 WorkspaceCreateRequestSchema.safeParse({...base,workspaceId:'wks_0123456789abcdef'}).success,
 WorkspaceCreateRequestSchema.safeParse({...base,workspaceId:'wks_0123456789abcdeF'}).success]));
"""
        with tempfile.TemporaryDirectory(prefix='pud-pinned-schema-') as td:
            proc = subprocess.run([T._find_node(), '--input-type=module', '-e', script],
                cwd=td, env={'HOME':td,'PATH':'/usr/bin:/bin'},
                text=True, capture_output=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), [False, True, False])

    def test_genuine_validator_reaches_same_private_guard_and_process_path(self):
        with tempfile.TemporaryDirectory(prefix='pud-owned-validator-') as td, T.LocalCodexServer() as server:
            result, calls, state = H._run_validate(Path(td), server_base=server.base, execution_class='fixture')
            self.assertEqual(result['status'], 'PASS', result)
            self.assertFalse(result['real_validation_satisfied'])
            observed_calls = state['runtime_calls_before_cleanup']
            self.assertEqual(observed_calls.count('prompt'), 1)
            self.assertEqual(observed_calls.count('fake-transport'), 1)
            binding = result['subject']['owned_runtime']['process']
            self.assertEqual(binding['agent_id'], result['subject']['owned_runtime']['agent_id'])
            self.assertTrue(any('--candidate-owned' in str(call) for call in calls))

    def test_genuine_validator_uncertainty_preserves_ids_and_owned_objects(self):
        for fault in ('inspection', 'create_uncertain', 'wrong_pi_bytes', 'config_replacement', 'prompt_uncertain'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='pud-owned-validator-') as td, T.LocalCodexServer() as server:
                result, calls, state = H._run_validate(Path(td), server_base=server.base,
                    execution_class='fixture', extra_state={'runtime_fault': {fault: True}})
                self.assertEqual(result['status'], 'UNKNOWN', result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertFalse(any(call[:2] == ['docker', 'rm'] for call in calls))
                if fault == 'prompt_uncertain':
                    self.assertEqual(state['_owned_runtime'].calls().count('prompt'), 1)
                    self.assertEqual(state['_owned_runtime'].calls().count('fake-transport'), 1)
                else:
                    self.assertNotIn('prompt', state['_owned_runtime'].calls())
                reference = json.loads((Path(state['work']) / 'home/.m07-t05/owned.json').read_text())
                self.assertRegex(reference['requested_agent_id'], r'^[0-9a-f-]{36}$')
                self.assertFalse(reference['replay'])
                state['_owned_runtime'].close()

    def test_actual_separate_selected_process_and_guarded_exchange(self):
        with tempfile.TemporaryDirectory(prefix='pud-owned-') as td:
            f = OwnedRuntimeFixture(td)
            try:
                result = f.run()
                self.assertEqual(result['status'], 'PASS')
                self.assertNotEqual(result['process']['pid'], result['daemon']['worker_pid'])
                self.assertEqual(result['process']['ppid'], result['daemon']['worker_pid'])
                self.assertEqual(result['process']['agent_id'], result['agent_id'])
                self.assertEqual(result['process']['workspace_id'], result['workspace_id'])
                self.assertEqual(f.calls().count('prompt'), 1)
                self.assertEqual(f.calls().count('fake-transport'), 1)
                rows = A.parse_witness_readback((f.tmp / 'm07-t05-witness.jsonl').read_text(),
                    'synthetic-owned', result['process'])
                self.assertEqual(A.classify_aggregated_witness(rows, test_id='synthetic-owned')['gate'], 'PASS')
                refs = json.loads((f.home / '.m07-t05/owned.json').read_text())
                self.assertEqual(refs['dispatch'], 'settled')
                self.assertEqual(refs['agent_id'], result['agent_id'])
            finally:
                f.close()

    def test_reachable_mismatch_and_uncertainty_never_replays_or_prompts(self):
        for fault in ('wrong_server','server_replacement','process','workspace','wrong_agent','wrong_agent_env',
                      'profile','thinking','auth','selector','workspace_uncertain','create_uncertain','inspection',
                      'config_replacement','reference_replacement','wrong_pi_bytes','extra_proof','create_pending',
                      'unsupported_creation','process_collision','missing_effective_model'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='pud-owned-') as td:
                f = OwnedRuntimeFixture(td, {fault:True})
                try:
                    with self.assertRaises(A.AdapterBlocked):
                        f.run()
                    # Assert while resources still exist, BEFORE fixture cleanup.
                    self.assertNotIn('prompt', f.calls())
                    self.assertNotIn('fake-transport', f.calls())
                    refs = json.loads((f.home / '.m07-t05/owned.json').read_text())
                    self.assertFalse(refs['replay'])
                    self.assertNotIn('synthetic-sensitive-never-emit', json.dumps(refs))
                    if fault == 'process_collision':
                        self.assertEqual((f.home / '.m07-t05/processes' /
                            (refs['requested_agent_id'] + '.json')).read_text(), 'private unrelated acquisition')
                    self.assertRegex(refs['requested_agent_id'], r'^[0-9a-f-]{36}$')
                    self.assertRegex(refs['requested_workspace_id'], r'^wks_[a-f0-9]{16}$')
                    if fault not in ('wrong_server','workspace_uncertain','unsupported_creation'):
                        self.assertIsNotNone(refs['workspace_id'])
                finally:
                    f.close()

    def test_negative_completion_retains_actual_ids_without_resend(self):
        for fault in ('completion', 'prompt_uncertain', 'server_replacement_after_prompt'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='pud-owned-') as td:
                f = OwnedRuntimeFixture(td, {fault: True})
                try:
                    with self.assertRaises(A.AdapterBlocked):
                        f.run()
                    self.assertEqual(f.calls().count('prompt'), 1)
                    self.assertEqual(f.calls().count('fake-transport'), 1)
                    refs = json.loads((f.home / '.m07-t05/owned.json').read_text())
                    self.assertIsNotNone(refs['agent_id'])
                    self.assertEqual(refs['dispatch'], 'prompt_pending' if fault == 'prompt_uncertain' else 'prompt_sent')
                    self.assertFalse(refs['replay'])
                finally:
                    f.close()

    def test_request_context_or_replaced_binding_blocks_actual_fake_transport(self):
        for fault in ('request_profile', 'binding_replacement'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='pud-owned-') as td:
                f = OwnedRuntimeFixture(td, {fault: True})
                try:
                    try:
                        result = f.run()
                    except A.AdapterBlocked:
                        result = None
                    self.assertEqual(f.calls().count('prompt'), 1)
                    self.assertNotIn('fake-transport', f.calls())
                    rows = f.tmp / 'm07-t05-witness.jsonl'
                    if result is not None and rows.exists():
                        parsed = A.parse_witness_readback(rows.read_text(), 'synthetic-owned', result['process'])
                        self.assertNotEqual(A.classify_aggregated_witness(parsed, test_id='synthetic-owned')['gate'], 'PASS')
                    refs = json.loads((f.home / '.m07-t05/owned.json').read_text())
                    self.assertIsNotNone(refs['agent_id'])
                    self.assertFalse(refs['replay'])
                finally:
                    f.close()

    def test_pinned_protocol_snapshot_omissions_types_and_binding_fail_before_prompt(self):
        faults = [{'snapshot_omit': [key]} for key in
                  ('id', 'workspaceId', 'cwd', 'provider', 'runtimeInfo', 'effectiveThinkingOptionId')]
        faults += [{'snapshot_patch': {key: value}} for key, value in
                   (('id', 7), ('workspaceId', False), ('cwd', '/foreign'),
                    ('provider', 'codex'), ('runtimeInfo', {'provider':'pi','sessionId':None,'model':None}),
                    ('effectiveThinkingOptionId', None), ('effectiveThinkingOptionId', 'xhigh'),
                    ('labels', {'paseo.parent-agent-id':'foreign-parent'}))]
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='pud-supported-snapshot-') as td:
                fixture = OwnedRuntimeFixture(td, fault)
                try:
                    with self.assertRaises(A.AdapterBlocked):
                        fixture.run()
                    self.assertNotIn('prompt', fixture.calls())
                    self.assertNotIn('fake-transport', fixture.calls())
                    reference = json.loads((fixture.home / '.m07-t05/owned.json').read_text())
                    self.assertRegex(reference['requested_workspace_id'], r'^wks_[a-f0-9]{16}$')
                    self.assertRegex(reference['requested_agent_id'], r'^[0-9a-f-]{36}$')
                    self.assertFalse(reference['replay'])
                finally:
                    fixture.close()

    def test_actual_pi_boundary_rejects_ambient_selectors_and_missing_acquisition_env(self):
        faults = [{'pi_ambient': {key: value}} for key, value in
                  (('PASEO_WORKSPACE_ID','foreign'), ('PASEO_HOST','foreign'), ('PASEO_SERVER','foreign'),
                   ('PASEO_PASSWORD','synthetic-unused'), ('NODE_OPTIONS','--no-warnings'),
                   ('PI_CODING_AGENT_DIR','/nonexistent-fixture'), ('PI_AGENT_DIR','/nonexistent-fixture'))]
        faults += [{'pi_env_omit':[key]} for key in
                   ('META_API_KEY', 'PASEO_AGENT_ID', 'M07_T05_TEST_ID', 'M07_T05_PROCESS_DIR')]
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix='pud-supported-env-') as td:
                fixture = OwnedRuntimeFixture(td, fault)
                try:
                    with self.assertRaises(A.AdapterBlocked):
                        fixture.run()
                    self.assertNotIn('prompt', fixture.calls())
                    self.assertNotIn('fake-transport', fixture.calls())
                    reference = json.loads((fixture.home / '.m07-t05/owned.json').read_text())
                    self.assertFalse(reference['replay'])
                finally:
                    fixture.close()

    def test_genuine_validator_post_effect_inspection_uncertainty_retains_one_exchange(self):
        with tempfile.TemporaryDirectory(prefix='pud-owned-post-effect-') as td, T.LocalCodexServer() as server:
            result, calls, state = H._run_validate(Path(td), server_base=server.base,
                extra_state={'runtime_fault':{'inspection_after_prompt':True}})
            runtime = state['_owned_runtime']
            try:
                self.assertEqual(result['status'], 'UNKNOWN', result)
                self.assertFalse(result['real_validation_satisfied'])
                self.assertEqual(runtime.calls().count('prompt'), 1)
                self.assertEqual(runtime.calls().count('fake-transport'), 1)
                self.assertFalse(any(call[:2] == ['docker','rm'] for call in calls))
                reference = json.loads((Path(state['work']) / 'home/.m07-t05/owned.json').read_text())
                self.assertIsNotNone(reference['agent_id'])
                self.assertIsNotNone(reference['workspace_id'])
                self.assertFalse(reference['replay'])
            finally:
                runtime.close()

    def test_reference_collision_cannot_acquire_or_mutate(self):
        with tempfile.TemporaryDirectory(prefix='pud-owned-') as td:
            f = OwnedRuntimeFixture(td)
            reference = f.home / '.m07-t05/owned.json'
            reference.write_text('private unrelated object')
            reference.chmod(0o600)
            try:
                with self.assertRaises(A.AdapterBlocked):
                    f.run()
                self.assertNotIn('workspace', f.calls())
                self.assertEqual(reference.read_text(), 'private unrelated object')
            finally:
                f.close()


if __name__ == '__main__':
    unittest.main()
