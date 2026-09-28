from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "config" / "llm-test-policy.json").read_text())
DOC = (ROOT / "docs" / "LLM_TEST_POLICY.md").read_text()
AGENTS = (ROOT / "config" / "pi-agent" / "AGENTS.md").read_text()
RUNNER = ROOT / "scripts" / "run-llm-test.sh"


class LlmTestPolicyContractTests(unittest.TestCase):
    def test_exact_real_llm_test_profile_is_fixed(self) -> None:
        profile = POLICY["real_llm_tests"]
        self.assertEqual(profile["provider"], "codex-lb")
        self.assertEqual(profile["model"], "gpt-6-luna")
        self.assertEqual(profile["thinking"], "low")
        self.assertFalse(profile["fallback_allowed"])
        self.assertIn("gpt-6-astra", profile["forbidden_models"])

    def test_human_and_agent_instructions_are_explicit(self) -> None:
        for text in (DOC, AGENTS):
            self.assertIn("gpt-6-luna", text)
            self.assertIn("low", text)
            self.assertIn("gpt-6-astra", text)
        self.assertIn("NEVER use `gpt-6-astra`", AGENTS)
        self.assertIn("If `gpt-6-luna` is unavailable", DOC)

    def test_canonical_runner_emits_only_luna_low_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "paseo"
            capture = Path(tmp) / "args.txt"
            fake.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$CAPTURE\"\n")
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp}:{env['PATH']}"
            env["CAPTURE"] = str(capture)
            result = subprocess.run(
                [str(RUNNER), "TEST_MARKER", str(ROOT)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            args = capture.read_text().splitlines()
            self.assertIn("codex-lb/gpt-6-luna", args)
            self.assertIn("low", args)
            self.assertNotIn("gpt-6-astra", args)


if __name__ == "__main__":
    unittest.main()
