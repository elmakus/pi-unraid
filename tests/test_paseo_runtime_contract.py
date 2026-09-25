from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = (ROOT / "compose.yaml").read_text()
SMOKE = (ROOT / "scripts" / "verify-compose-foundation.sh").read_text()
CONFIGURE = (ROOT / "scripts" / "configure-paseo-runtime.sh").read_text()


class PaseoRuntimeContractTests(unittest.TestCase):
    def test_paseo_service_replaces_legacy_pi_runtime(self) -> None:
        self.assertRegex(COMPOSE, r"(?m)^  paseo:\s*$")
        self.assertNotRegex(COMPOSE, r"(?m)^  pi:\s*$")
        for forbidden in (
            "/home/pi",
            "PI_UID",
            "PI_GID",
            "PI_CODEX_LB_",
            "pi-unraid-service",
            "codex_lb_client",
            "host.docker.internal",
        ):
            self.assertNotIn(forbidden, COMPOSE)

    def test_native_home_external_workspace_and_explicit_host_paths(self) -> None:
        for target in ("/home/paseo", "/projects", "/worktrees"):
            self.assertIn(f"target: {target}", COMPOSE)
        self.assertEqual(COMPOSE.count("create_host_path: false"), 3)
        self.assertIn("/mnt/user/appdata/pi-unraid/paseo-home", COMPOSE)
        self.assertIn("/mnt/user/projects", COMPOSE)
        self.assertIn("/mnt/user/pi-worktrees", COMPOSE)

    def test_upstream_supported_user_mapping_and_runtime_limits(self) -> None:
        self.assertIn('user: "${PASEO_UID:-99}:${PASEO_GID:-100}"', COMPOSE)
        self.assertIn('shm_size: "1gb"', COMPOSE)
        self.assertIn("restart: unless-stopped", COMPOSE)
        self.assertIn('max-size: "10m"', COMPOSE)
        self.assertIn('max-file: "3"', COMPOSE)
        for forbidden in (
            "cpus:",
            "mem_limit:",
            "mem_reservation:",
            "deploy:",
            "privileged:",
            "network_mode: host",
            "/var/run/docker.sock",
        ):
            self.assertNotIn(forbidden, COMPOSE)

    def test_no_raw_port_or_entrypoint_override(self) -> None:
        self.assertNotRegex(COMPOSE, r"(?m)^\s+ports:\s*$")
        self.assertNotRegex(COMPOSE, r"(?m)^\s+(entrypoint|command|healthcheck):\s*")
        self.assertNotRegex(COMPOSE, r"(?m)^\s+secrets:\s*$")

    def test_worktree_root_has_reproducible_native_config_path(self) -> None:
        self.assertIn(
            "paseo daemon config set worktrees.root /worktrees --home /home/paseo/.paseo",
            CONFIGURE,
        )
        self.assertIn("scripts/configure-paseo-runtime.sh", SMOKE)
        self.assertNotIn("PASEO_WORKTREES_ROOT", COMPOSE)
        self.assertIn('cfg["worktrees"]["root"] == "/worktrees"', CONFIGURE)


if __name__ == "__main__":
    unittest.main()
