from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = (ROOT / "compose.yaml").read_text()
CONFIGURE = (ROOT / "scripts" / "configure-paseo-runtime.sh").read_text()
SMOKE = (ROOT / "scripts" / "verify-compose-foundation.sh").read_text()
ACCESS = (ROOT / "scripts" / "paseo-relay-access.sh").read_text()
DOC = (ROOT / "docs" / "PASEO_RELAY_AUTH.md").read_text()


class PaseoRelayAuthContractTests(unittest.TestCase):
    def test_relay_is_disabled_until_explicit_human_consent(self) -> None:
        self.assertIn(
            "paseo daemon config set daemon.relay.enabled false --home /home/paseo/.paseo",
            CONFIGURE,
        )
        self.assertIn('cfg["daemon"]["relay"]["enabled"] is False', CONFIGURE)
        self.assertIn("require_tty", ACCESS)
        self.assertIn("read -r answer", ACCESS)
        self.assertIn("[y/N]", ACCESS)
        self.assertIn("paseo daemon pair --relay --home /home/paseo/.paseo", ACCESS)
        self.assertIn("Pairing cancelled; Relay was not enabled by this helper.", ACCESS)

    def test_no_raw_port_or_secret_environment_wiring(self) -> None:
        self.assertNotIn("ports:", COMPOSE)
        for forbidden in (
            "PASEO_PASSWORD",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GITHUB_TOKEN",
            "MUSE_API_KEY",
            "CODEX_API_KEY",
        ):
            self.assertNotIn(forbidden, COMPOSE)

    def test_smoke_proves_default_off_then_persistent_enabled_relay_and_identity(self) -> None:
        self.assertIn('"code":"RELAY_DISABLED"', SMOKE)
        self.assertIn("paseo daemon pair --relay --json", SMOKE)
        self.assertIn('cfg["daemon"]["relay"]["enabled"] is True', SMOKE)
        self.assertIn("daemon-keypair.json", SMOKE)
        self.assertIn("keypair_sha_before", SMOKE)
        self.assertIn("keypair_sha_after", SMOKE)
        self.assertIn('= "600"', SMOKE)
        self.assertIn("{{len .HostConfig.PortBindings}}", SMOKE)
        self.assertIn('"relay_default_disabled":true', SMOKE)
        self.assertIn('"relay_enabled_after_consent":true', SMOKE)
        self.assertIn('"relay_enabled_after_recreate":true', SMOKE)
        self.assertIn('"daemon_identity_persisted":true', SMOKE)

    def test_readback_is_metadata_only_and_revocation_fails_closed(self) -> None:
        self.assertIn('"device_revocation_cli": "unsupported"', ACCESS)
        self.assertIn('"supported":false', ACCESS)
        self.assertNotIn("read_text())", ACCESS.replace('(home / "config.json").read_text())', ""))
        self.assertIn("never prints the keypair", DOC)
        self.assertIn("no command for listing and individually revoking", DOC)

    def test_first_time_authentication_is_explicit_and_home_backed(self) -> None:
        self.assertIn("auth-shell", ACCESS)
        self.assertIn("require_tty", ACCESS)
        self.assertIn('exec -w /home/paseo paseo sh', ACCESS)
        self.assertIn(
            "First-time provider or account authentication is never part of normal container startup",
            DOC,
        )
        self.assertIn("getpaseo/paseo@v0.9.2", DOC)


if __name__ == "__main__":
    unittest.main()
