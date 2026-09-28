from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "paseo-codex-lb-entrypoint.sh"


class PaseoCodexLbEntrypointContractTests(unittest.TestCase):
    def run_wrapper(self, secret_text: str, inherited: str = "stale") -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = root / "codex-lb.env"
            secret.write_text(secret_text)
            upstream = root / "upstream.sh"
            upstream.write_text(
                "#!/bin/sh\n"
                "printf 'KEY=%s\\n' \"${CODEX_LB_API_KEY-UNSET}\"\n"
                "printf 'ARGS=%s\\n' \"$*\"\n"
            )
            upstream.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "PI_CODEX_LB_SECRET_FILE": str(secret),
                "PI_UNRAID_PASEO_UPSTREAM_ENTRYPOINT": str(upstream),
                "CODEX_LB_API_KEY": inherited,
            })
            return subprocess.run(
                [str(WRAPPER), "hello", "world"],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

    def test_valid_named_secret_is_exported_to_upstream(self) -> None:
        result = self.run_wrapper("CODEX_LB_API_KEY=fixture-secret\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "KEY=fixture-secret\nARGS=hello world\n")
        self.assertNotIn("fixture-secret", result.stderr)

    def test_valid_raw_secret_is_supported(self) -> None:
        result = self.run_wrapper("fixture-raw-secret\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("KEY=fixture-raw-secret\n", result.stdout)

    def test_empty_secret_clears_stale_environment_and_allows_degraded_start(self) -> None:
        result = self.run_wrapper("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("KEY=UNSET\n", result.stdout)
        self.assertNotIn("stale", result.stdout + result.stderr)

    def test_nonempty_malformed_secret_fails_closed_without_leakage(self) -> None:
        result = self.run_wrapper("WRONG_NAME=do-not-print-this\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dedicated Codex-LB secret is non-empty but invalid", result.stderr)
        self.assertNotIn("do-not-print-this", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
