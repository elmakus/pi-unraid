"""Source-qualified negative controls; synthetic transport, no real inference.

These tests import the actual pinned installed Pi implementation READ ONLY.
Every transport call has an explicit in-memory fake and a disposable explicit
key. No auth resolver/store is invoked. Child HOME/env are private and scrubbed.
Missing pinned dependencies are failure, never skip/fallback.
"""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from tests.test_m07_t05_validator_adapter import A, T


class TransportQualificationTests(unittest.TestCase):
    def run_qualification(self, scenario):
        node = T._find_node()
        self.assertIsNotNone(node, 'pinned qualification needs Node; no silent skip')
        pi = Path('/usr/local/lib/node_modules/@earendil-works/pi-coding-agent')
        self.assertTrue(pi.is_dir(), 'pinned official source unavailable')
        with tempfile.TemporaryDirectory(prefix='pud-transport-') as td:
            root = Path(td)
            witness = root / 'witness.jsonl'
            marker = root / 'transport-entered'
            proc = subprocess.run([
                node, str(T.ROOT / 'tests/fixtures/m07_t05_transport_qualification.mjs'),
                str(pi), str(T.ROOT / 'config/pi-agent/extensions/m07-t05-witness.js'), scenario,
            ], cwd=root, env={'HOME':str(root), 'PATH':'/usr/bin:/bin',
                'M07_T05_TEST_ID':'synthetic-owned', 'M07_T05_WITNESS_FILE':str(witness),
                'PUD_SYNTHETIC_FETCH_MARKER':str(marker)},
                text=True, capture_output=True, timeout=25)
            if scenario in ('broken-abort', 'missing-signal'):
                self.assertEqual(proc.returncode, 42, proc.stderr)
                self.assertFalse(marker.exists(), 'transport was entered before process fail-stop')
                outcome = {'process_returncode':proc.returncode, 'transport_marker':marker.exists()}
            else:
                self.assertEqual(proc.returncode, 0, proc.stderr)
                outcome = json.loads(proc.stdout)
                self.assertEqual(marker.exists(), scenario == 'throw-only-control')
            rows = (A.load_witness_events(witness, 'synthetic-owned')
                    if witness.exists() and not witness.is_symlink() else [])
            return outcome, rows

    def test_supported_abort_blocks_actual_sdk_after_actual_runner_catches_error(self):
        outcome, rows = self.run_qualification('abort')
        self.assertEqual(outcome['fetches'], 0)
        self.assertGreater(outcome['caughtErrors'], 0)
        self.assertFalse(outcome['fixedMaxSupported'])
        self.assertEqual(A.classify_aggregated_witness(rows, test_id='synthetic-owned')['gate'], 'FAIL')

    def test_throw_only_negative_control_reaches_fake_transport(self):
        outcome, rows = self.run_qualification('throw-only-control')
        self.assertEqual(outcome['fetches'], 1)
        self.assertEqual(rows, [])

    def test_unprivate_or_symlink_witness_failure_blocks_actual_fake_transport(self):
        for scenario in ('unprivate-witness', 'symlink-witness'):
            with self.subTest(scenario=scenario):
                outcome, rows = self.run_qualification(scenario)
                self.assertEqual(outcome['fetches'], 0)
                self.assertGreater(outcome['caughtErrors'], 0)
                self.assertEqual(rows, [])

    def test_unqualified_abort_context_fail_stops_only_opted_in_child_before_transport(self):
        for scenario in ('broken-abort','missing-signal'):
            with self.subTest(scenario=scenario):
                outcome, rows = self.run_qualification(scenario)
                self.assertEqual(outcome['process_returncode'], 42)
                self.assertFalse(outcome['transport_marker'])
                self.assertEqual(A.classify_aggregated_witness(rows, test_id='synthetic-owned')['gate'], 'FAIL')

    def test_supported_hook_context_wrong_provider_or_thinking_never_passes(self):
        node = T._find_node()
        self.assertIsNotNone(node)
        # Reproduce Main's diagnostic: payload looks like meta/max, actual
        # supported context is codex-lb/max OR meta/xhigh. The shipped observer
        # must record actual context, abort, and not produce synthetic PASS.
        script = """
import {pathToFileURL} from 'node:url';
const mod = await import(pathToFileURL(process.argv[1]).href);
const handlers = {};
mod.default({on:(k,fn)=>handlers[k]=fn});
const controller = new AbortController();
const ctx = {model:{provider:process.argv[2], id:'muse-spark-1.3-contributor'},
  thinkingLevel:process.argv[3], signal:controller.signal, abort:()=>controller.abort()};
try { await handlers.before_provider_request({payload:{model:ctx.model.id, reasoning:{effort:'max'}}},ctx); } catch {}
if (!controller.signal.aborted) process.exit(2);
"""
        for provider, thinking in [('codex-lb','max'), ('meta','xhigh')]:
            with self.subTest(provider=provider, thinking=thinking), tempfile.TemporaryDirectory() as td:
                path = Path(td) / 'witness.jsonl'
                proc = subprocess.run([node, '--input-type=module', '-e', script,
                    str(T.ROOT / 'config/pi-agent/extensions/m07-t05-witness.js'), provider, thinking],
                    cwd=td, env={'HOME':td, 'PATH':'/usr/bin:/bin',
                    'M07_T05_TEST_ID':'owned', 'M07_T05_WITNESS_FILE':str(path)},
                    text=True, capture_output=True, timeout=10)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                rows = A.load_witness_events(path, 'owned')
                result = A.classify_aggregated_witness(rows, test_id='owned')
                self.assertEqual(result['gate'], 'FAIL')
                self.assertEqual(result['observed']['provider'], provider)
                self.assertEqual(result['observed']['thinking'], thinking)


if __name__ == '__main__':
    unittest.main()
