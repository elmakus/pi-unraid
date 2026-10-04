from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "config" / "pi-agent" / "policies" / "llm-test-policy.json").read_text())
DOC = (ROOT / "docs" / "LLM_TEST_POLICY.md").read_text()
GLOBAL_DOC = (ROOT / "config" / "pi-agent" / "policies" / "LLM_TEST_POLICY.md").read_text()
AGENTS = (ROOT / "config" / "pi-agent" / "AGENTS.md").read_text()
RUNNER = ROOT / "config" / "pi-agent" / "bin" / "run-llm-test.sh"


class LlmTestPolicyContractTests(unittest.TestCase):
    def test_exact_real_llm_test_profile_is_fixed(self) -> None:
        profile = POLICY["real_llm_tests"]
        self.assertEqual(profile["provider"], "meta")
        self.assertEqual(profile["model"], "muse-spark-1.3-contributor")
        self.assertEqual(profile["thinking"], "max")
        self.assertFalse(profile["fallback_allowed"])
        self.assertIn("gpt-6-astra", profile["forbidden_models"])

    def test_human_and_agent_instructions_are_explicit(self) -> None:
        self.assertEqual(DOC, GLOBAL_DOC)
        for text in (DOC, GLOBAL_DOC, AGENTS):
            self.assertIn("muse-spark-1.3-contributor", text)
            self.assertIn("max", text)
            self.assertIn("gpt-6-astra", text)
        self.assertIn("NEVER use `gpt-6-astra`", AGENTS)
        self.assertIn("If `meta/muse-spark-1.3-contributor`", DOC)
        # Superseded test-only Luna/low profile must not remain as real-test authority.
        for text in (DOC, GLOBAL_DOC, AGENTS):
            self.assertNotIn("gpt-6-luna", text)
        self.assertNotIn("codex-lb/gpt-6-luna", GLOBAL_DOC)

    def test_canonical_runner_emits_only_fixed_profile_without_fallback(self) -> None:
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
            self.assertIn("meta/muse-spark-1.3-contributor", args)
            self.assertIn("max", args)
            self.assertNotIn("gpt-6-astra", args)
            self.assertNotIn("gpt-6-luna", args)

    def test_native_create_agent_args_emits_fixed_shape_without_inference(self) -> None:
        # Validates policy without inference and emits caller-scoped create_agent fields.
        result = subprocess.run(
            [str(RUNNER), "--native-create-agent-args"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["provider"], "pi/meta/muse-spark-1.3-contributor")
        self.assertEqual(payload["settings"]["thinkingOptionId"], "max")
        self.assertTrue(payload["notifyOnFinish"])

    def _run_delivered_launcher(self, policy, argv, with_paseo=True):
        # Exercise the actual repo-delivered guard bytes: copy the real launcher
        # into a disposable symlink-free agent root; no symlinks, no inference.
        # Returns (completed_process, dispatch_marker_path).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "agent"
            (agent / "bin").mkdir(parents=True)
            (agent / "policies").mkdir(parents=True)
            launcher = agent / "bin" / "run-llm-test.sh"
            launcher.write_bytes(RUNNER.read_bytes())
            launcher.chmod(0o755)
            if policy is not None:
                (agent / "policies" / "llm-test-policy.json").write_text(
                    json.dumps(policy)
                )
            fakebin = root / "fakebin"
            fakebin.mkdir()
            marker = root / "dispatched.txt"
            if with_paseo:
                fake = fakebin / "paseo"
                fake.write_text(
                    '#!/bin/sh\nprintf "%s\\n" "$@" > "$DISPATCH_MARKER"\n'
                )
                fake.chmod(0o755)
            env = {"PATH": f"{fakebin}:/usr/bin:/bin", "DISPATCH_MARKER": str(marker)}
            proc = subprocess.run(
                [str(launcher)] + argv,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return proc, marker

    def fixed_policy(self):
        return {
            "schema": 1,
            "real_llm_tests": {
                "provider": "meta",
                "model": "muse-spark-1.3-contributor",
                "thinking": "max",
                "forbidden_models": ["gpt-6-astra"],
                "fallback_allowed": False,
            },
        }

    def test_delivered_launcher_rejects_bad_profile_without_dispatch_or_fallback(self) -> None:
        # The delivered guard must fail closed on every mutated profile facet:
        # nonzero exit and no dispatch to any (fake) Paseo/model — i.e. no
        # silent fallback or substitution. All calls use the fake executable.
        cases = {
            "bad_provider": ("codex-lb", "muse-spark-1.3-contributor", "max", False),
            "bad_model_luna": ("meta", "gpt-6-luna", "max", False),
            "bad_model_astra": ("meta", "gpt-6-astra", "max", False),
            "downgraded_xhigh": ("meta", "muse-spark-1.3-contributor", "xhigh", False),
            "downgraded_low": ("meta", "muse-spark-1.3-contributor", "low", False),
            "fallback_allowed": ("meta", "muse-spark-1.3-contributor", "max", True),
        }
        for name, (provider, model, thinking, fallback) in cases.items():
            with self.subTest(case=name):
                policy = self.fixed_policy()
                profile = policy["real_llm_tests"]
                profile["provider"] = provider
                profile["model"] = model
                profile["thinking"] = thinking
                profile["fallback_allowed"] = fallback
                proc, marker = self._run_delivered_launcher(
                    policy, ["SYNTHETIC_PROMPT_NO_INFERENCE"]
                )
                self.assertEqual(proc.returncode, 3, proc.stderr)
                self.assertFalse(marker.exists(), "rejected profile must not dispatch")

    def test_delivered_launcher_rejects_missing_forbidden_entry_and_missing_policy(self) -> None:
        policy = self.fixed_policy()
        policy["real_llm_tests"]["forbidden_models"] = []
        proc, marker = self._run_delivered_launcher(policy, ["SYNTHETIC_PROMPT_NO_INFERENCE"])
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertFalse(marker.exists())
        proc, marker = self._run_delivered_launcher(None, ["SYNTHETIC_PROMPT_NO_INFERENCE"])
        self.assertNotEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(marker.exists())

    def test_delivered_launcher_native_args_rejects_bad_profile_without_inference(self) -> None:
        policy = self.fixed_policy()
        policy["real_llm_tests"]["thinking"] = "xhigh"
        proc, marker = self._run_delivered_launcher(policy, ["--native-create-agent-args"])
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertFalse(marker.exists())

    def test_delivered_launcher_fails_closed_when_execution_is_unavailable(self) -> None:
        # Valid policy but no executable on PATH: the guard validates, then the
        # missing binary fails nonzero with no dispatch. PATH keeps only system
        # dirs (jq/bash) and excludes /usr/local/bin where real paseo lives.
        proc, marker = self._run_delivered_launcher(
            self.fixed_policy(), ["SYNTHETIC_PROMPT_NO_INFERENCE"], with_paseo=False
        )
        self.assertNotEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
