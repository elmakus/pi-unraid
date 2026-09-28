from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = (ROOT / "compose.yaml").read_text()
DOCKERFILE = (ROOT / "Dockerfile").read_text()
HELPER = ROOT / "scripts" / "pi-unraid-provider"
LAUNCHER = ROOT / "scripts" / "paseo-pi-launcher"
ADR = (ROOT / "decisions" / "PIB_ADR_008_LLM_TEST_MODEL_POLICY.md").read_text()


def load_policy():
    path = ROOT / "scripts" / "paseo_llm_test_policy.py"
    spec = importlib.util.spec_from_file_location("paseo_llm_test_policy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PaseoPiCodexLbSecretInheritanceContractTests(unittest.TestCase):
    def test_compose_uses_file_secret_and_supported_pi_command_without_secret_value_env(self) -> None:
        self.assertIn("PI_COMMAND: /usr/local/bin/paseo-pi-launcher", COMPOSE)
        self.assertIn("PI_CODEX_LB_SECRET_FILE: /run/secrets/pi-unraid-codex-lb", COMPOSE)
        self.assertIn('"host.docker.internal:host-gateway"', COMPOSE)
        self.assertIn("source: codex_lb_client", COMPOSE)
        self.assertIn("target: pi-unraid-codex-lb", COMPOSE)
        self.assertIn("/mnt/user/appdata/pi-unraid/secrets/codex-lb.env", COMPOSE)
        self.assertNotIn("CODEX_LB_API_KEY:", COMPOSE)

    def test_image_installs_repo_owned_launcher_and_secret_helper(self) -> None:
        self.assertIn(
            "COPY --chmod=0755 scripts/pi-unraid-provider /usr/local/bin/pi-unraid-provider",
            DOCKERFILE,
        )
        self.assertIn(
            "COPY --chmod=0755 scripts/paseo-pi-launcher /usr/local/bin/paseo-pi-launcher",
            DOCKERFILE,
        )
        launcher = LAUNCHER.read_text()
        self.assertIn('exec "$provider" exec "$real_pi" "$@"', launcher)
        self.assertNotIn("CODEX_LB_API_KEY", launcher)

    def test_dynamic_provider_config_is_preserved_and_secret_reaches_only_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            agent = home / ".pi" / "agent"
            agent.mkdir(parents=True)
            models = agent / "models.json"
            original = {
                "providers": {
                    "codex-lb": {
                        "api": "openai-responses",
                        "apiKey": "${CODEX_LB_API_KEY}",
                        "baseUrl": "http://host.docker.internal:2455/v1",
                    }
                }
            }
            models.write_text(json.dumps(original, indent=2) + "\n")
            secret = root / "codex-lb.env"
            sentinel = "unit-test-secret-value-never-log"
            secret.write_text(f"CODEX_LB_API_KEY={sentinel}\n")
            secret.chmod(0o600)
            fake_pi = root / "fake-pi"
            fake_pi.write_text(
                "#!/bin/sh\n"
                "[ -n \"${CODEX_LB_API_KEY:-}\" ] || exit 41\n"
                "printf 'KEY_PRESENT=1\\n'\n"
                "printf 'ARGS=%s\\n' \"$*\"\n"
            )
            fake_pi.chmod(0o755)
            helper_copy = root / "pi-unraid-provider"
            shutil.copy2(HELPER, helper_copy)
            helper_copy.chmod(0o755)
            env = dict(os.environ)
            env.update({
                "HOME": str(home),
                "PI_UNRAID_PROVIDER_HELPER": str(helper_copy),
                "PI_UNRAID_REAL_PI_COMMAND": str(fake_pi),
                "PI_CODEX_LB_SECRET_FILE": str(secret),
            })
            proc = subprocess.run(
                [
                    str(LAUNCHER),
                    "--mode",
                    "rpc",
                    "--model",
                    "codex-lb/gpt-6-luna",
                    "--thinking",
                    "low",
                ],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("KEY_PRESENT=1", proc.stdout)
            self.assertIn("--thinking low", proc.stdout)
            self.assertNotIn(sentinel, proc.stdout + proc.stderr)
            self.assertEqual(json.loads(models.read_text()), original)

    def test_llm_test_policy_is_luna_low_and_rejects_astra_and_substitution(self) -> None:
        policy = load_policy()
        self.assertEqual(policy.TEST_MODEL, "codex-lb/gpt-6-luna")
        self.assertEqual(policy.TEST_THINKING, "low")
        self.assertEqual(policy.FORBIDDEN_TEST_MODEL, "codex-lb/gpt-6-astra")
        policy.validate_llm_test_selection(model="codex-lb/gpt-6-luna", thinking="low")
        for model, thinking in (
            ("codex-lb/gpt-6-astra", "low"),
            ("codex-lb/gpt-6-sol", "low"),
            ("codex-lb/gpt-6-luna", "medium"),
        ):
            with self.assertRaises(policy.LlmTestPolicyError):
                policy.validate_llm_test_selection(model=model, thinking=thinking)
        self.assertIn("MUST NOT be used for LLM-backed test traffic", ADR)
        self.assertIn("gpt-6-luna", ADR)
        self.assertIn("low", ADR)


if __name__ == "__main__":
    unittest.main()
