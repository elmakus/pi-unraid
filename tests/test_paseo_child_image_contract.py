#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (ROOT / "Dockerfile").read_text()
CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())


class PaseoChildImageContractTests(unittest.TestCase):
    def component(self, name: str) -> dict:
        return CANDIDATE["components"][name]

    def test_exact_paseo_parent_and_candidate_identity(self):
        paseo = self.component("paseo")
        self.assertIn(f"FROM {paseo['artifact']['reference']}", DOCKERFILE)
        self.assertIn(f'io.pi-unraid.candidate-id="{CANDIDATE["candidate_id"]}"', DOCKERFILE)
        self.assertIn(f'PI_UNRAID_CANDIDATE_ID="{CANDIDATE["candidate_id"]}"', DOCKERFILE)
        self.assertNotRegex(DOCKERFILE, r"(?m)^ARG\s+PASEO_(?:IMAGE|VERSION)")
        self.assertNotIn("ghcr.io/getpaseo/paseo:latest", DOCKERFILE)

    def test_candidate_drives_independent_tool_versions(self):
        expected = {
            "PI_UNRAID_PI_VERSION": self.component("pi")["version"],
            "PI_UNRAID_PLAYWRIGHT_VERSION": self.component("playwright")["version"],
            "PI_UNRAID_GH_VERSION": self.component("github_cli")["version"],
            "PI_UNRAID_DOCKER_CLI_VERSION": self.component("docker_cli")["version"],
            "PI_UNRAID_DOCKER_COMPOSE_VERSION": self.component("docker_compose")["version"],
        }
        for env_name, version in expected.items():
            self.assertIn(f'{env_name}="{version}"', DOCKERFILE)

        gh_digest = self.component("github_cli")["artifact"]["digest"].removeprefix("sha256:")
        compose_digest = self.component("docker_compose")["artifact"]["digest"].removeprefix("sha256:")
        self.assertIn(gh_digest, DOCKERFILE)
        self.assertIn(compose_digest, DOCKERFILE)
        self.assertIn("docker-${PI_UNRAID_DOCKER_CLI_VERSION}.tgz", DOCKERFILE)
        self.assertNotIn("releases/latest", DOCKERFILE)
        self.assertNotIn("/latest/", DOCKERFILE)

    def test_browser_is_image_owned_and_supports_xvfb(self):
        playwright = self.component("playwright")
        self.assertIn('PLAYWRIGHT_BROWSERS_PATH="/opt/ms-playwright"', DOCKERFILE)
        self.assertIn('"playwright@${PI_UNRAID_PLAYWRIGHT_VERSION}"', DOCKERFILE)
        self.assertIn("playwright install --with-deps chromium", DOCKERFILE)
        self.assertIn("xvfb", DOCKERFILE)
        self.assertIn("command -v Xvfb", DOCKERFILE)
        self.assertEqual(playwright["chromium"]["revision"], "1243")

    def test_general_development_baseline_is_present(self):
        for token in (
            "build-essential",
            "git-lfs",
            "python3",
            "python3-pip",
            "ripgrep",
            "fd-find",
            "iproute2",
            "dnsutils",
            "netcat-openbsd",
        ):
            self.assertIn(token, DOCKERFILE)

    def test_legacy_standalone_pi_contract_is_not_carried_forward(self):
        forbidden = (
            "node:24-bookworm-slim",
            "NODE_IMAGE",
            "/home/pi",
            "NOPASSWD",
            "pi-unraid-entrypoint",
            "pi-unraid-service",
            "groupmod --new-name pi",
            "usermod --login pi",
        )
        for token in forbidden:
            self.assertNotIn(token, DOCKERFILE)

        self.assertIsNone(re.search(r"(?m)^\s*USER\s+", DOCKERFILE))
        self.assertIsNone(re.search(r"(?m)^\s*ENTRYPOINT\s+", DOCKERFILE))
        self.assertIsNone(re.search(r"(?m)^\s*CMD\s+", DOCKERFILE))
        self.assertIn("WORKDIR /workspace", DOCKERFILE)

    def test_candidate_has_no_compatibility_exception(self):
        self.assertEqual(CANDIDATE["policy"]["compatibility_exceptions"], [])
        self.assertTrue(CANDIDATE["policy"]["build_must_not_reresolve"])


if __name__ == "__main__":
    unittest.main()
