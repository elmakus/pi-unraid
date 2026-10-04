from __future__ import annotations

import json
import os
import shutil
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
        # Positive control: with the fixed R2 policy and a fake-only Paseo, the
        # delivered launcher exits 0 and a dispatch IS observed carrying exactly
        # the fixed profile. This proves the snapshot mechanism observes real
        # dispatches (negative assertions below are therefore meaningful).
        snap = self._run_delivered_launcher(
            self.fixed_policy(), ["TEST_MARKER", str(ROOT)]
        )
        self.assertEqual(snap["returncode"], 0, snap["stderr"])
        self.assertTrue(snap["dispatched"], "valid policy must dispatch to fake Paseo")
        self.assertIn("meta/muse-spark-1.3-contributor", snap["dispatch_lines"])
        self.assertIn("max", snap["dispatch_lines"])
        self.assertNotIn("gpt-6-astra", snap["dispatch_lines"])
        self.assertNotIn("gpt-6-luna", snap["dispatch_lines"])

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
        # into a disposable symlink-free agent root and resolve executables ONLY
        # through a test-owned bindir (symlinks to the real jq/bash plus an
        # optional fake paseo). No ambient PATH entry is visible, so a real
        # Paseo binary elsewhere on any host can never be reached: dispatch is
        # fake-only by construction, and absence of paseo is truly unavailable.
        # Returns a snapshot dict captured BEFORE the temp dir is cleaned.
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
            bindir = root / "bindir"
            bindir.mkdir()
            # Only the tools the delivered launcher invokes (dirname/jq) plus
            # the interpreter: nothing else on the host can leak into resolution.
            for tool in ("dirname", "jq", "bash"):
                target = shutil.which(tool)
                self.assertIsNotNone(target, f"synthetic fixture requires {tool}")
                os.symlink(target, bindir / tool)
            marker = root / "dispatched.txt"
            if with_paseo:
                fake = bindir / "paseo"
                fake.write_text(
                    '#!/bin/sh\nprintf "%s\\n" "$@" > "$DISPATCH_MARKER"\n'
                )
                fake.chmod(0o755)
            env = {"PATH": str(bindir), "DISPATCH_MARKER": str(marker)}
            proc = subprocess.run(
                [str(launcher)] + argv,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            snapshot = {
                "returncode": proc.returncode,
                "stderr": proc.stderr,
                "stdout": proc.stdout,
                "dispatched": marker.is_file(),
                "dispatch_lines": (
                    marker.read_text().splitlines() if marker.is_file() else []
                ),
            }
        return snapshot

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
                snap = self._run_delivered_launcher(policy, ["SYNTHETIC_PROMPT_NO_INFERENCE"])
                self.assertEqual(snap["returncode"], 3, snap["stderr"])
                self.assertFalse(snap["dispatched"], "rejected profile must not dispatch")

    def test_delivered_launcher_rejects_missing_forbidden_entry_and_missing_policy(self) -> None:
        policy = self.fixed_policy()
        policy["real_llm_tests"]["forbidden_models"] = []
        snap = self._run_delivered_launcher(policy, ["SYNTHETIC_PROMPT_NO_INFERENCE"])
        self.assertEqual(snap["returncode"], 3, snap["stderr"])
        self.assertFalse(snap["dispatched"])
        snap = self._run_delivered_launcher(None, ["SYNTHETIC_PROMPT_NO_INFERENCE"])
        self.assertNotEqual(snap["returncode"], 0, snap["stderr"])
        self.assertFalse(snap["dispatched"])

    def test_delivered_launcher_native_args_rejects_bad_profile_without_inference(self) -> None:
        policy = self.fixed_policy()
        policy["real_llm_tests"]["thinking"] = "xhigh"
        snap = self._run_delivered_launcher(policy, ["--native-create-agent-args"])
        self.assertEqual(snap["returncode"], 3, snap["stderr"])
        self.assertFalse(snap["dispatched"])

    def test_delivered_launcher_fails_closed_when_execution_is_unavailable(self) -> None:
        # Valid policy but no Paseo in the isolated bindir: the guard validates,
        # then the unresolvable binary fails nonzero with no dispatch. Because
        # PATH contains only the test-owned bindir, unavailability holds on any
        # host regardless of ambient binaries.
        snap = self._run_delivered_launcher(
            self.fixed_policy(), ["SYNTHETIC_PROMPT_NO_INFERENCE"], with_paseo=False
        )
        self.assertNotEqual(snap["returncode"], 0, snap["stderr"])
        self.assertFalse(snap["dispatched"])


if __name__ == "__main__":
    unittest.main()
