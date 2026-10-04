"""Actual pinned Paseo provider selection across separate fake-only processes.

Metadata only, no sockets/provider transport/auth resolution. A scrubbed
synthetic daemon inherits a disposable synthetic key; official launch code
selects/spawns a separate Pi fake serving only public official model data.
This is not the missing full validator/daemon positive fixture.
"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from tests.test_m07_t05_validator_adapter import A, T


class CatalogProcessTests(unittest.TestCase):
    def test_actual_paseo_mapping_and_selected_process_exclude_fixed_max(self):
        node = T._find_node()
        self.assertIsNotNone(node, 'qualification requires Node, never skip')
        with tempfile.TemporaryDirectory(prefix='pud-catalog-process-') as td:
            fixtures = T.ROOT / 'tests/fixtures'
            proc = subprocess.run([node, str(fixtures / 'm07_t05_catalog_daemon.mjs'),
                '/usr/local/lib/node_modules/@getpaseo/server',
                str(fixtures / 'm07_t05_catalog_pi_rpc.mjs')], cwd=td,
                env={'HOME':td, 'PATH':'/usr/local/bin:/usr/bin:/bin',
                    'META_API_KEY':'synthetic-disposable-credential',
                    'PUD_SYNTHETIC_RPC_TRACE':str(Path(td)/'trace.jsonl'),
                    'PUD_SYNTHETIC_PI_ROOT':'/usr/local/lib/node_modules/@earendil-works/pi-coding-agent'},
                text=True, capture_output=True, timeout=25)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertFalse(result['fixedMaxSupported'])
            self.assertNotEqual(result['daemonPid'], result['selectedPiPid'])
            # Feed ACTUAL producer-transformed options to the product preflight;
            # no hand-authored supported options or copied PASS label.
            def external_catalog(argv, **kwargs):
                self.assertEqual(argv[:5], ['paseo','provider','models','pi','--thinking'])
                return subprocess.CompletedProcess(argv,0,stdout=json.dumps([
                    {'id':result['fixedModel'], 'thinkingOptionIds':result['options']}]))
            with self.assertRaises(A.AdapterBlocked):
                A.preflight_candidate_profile(external_catalog,candidate_home='/synthetic/private-daemon')


if __name__ == '__main__':
    unittest.main()
