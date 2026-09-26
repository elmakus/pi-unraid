from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pi_global_capabilities.py"
CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())

spec = importlib.util.spec_from_file_location("pi_global_capabilities", SCRIPT)
manager = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(manager)


class PiGlobalCapabilitiesContractTests(unittest.TestCase):
    def _desired(self) -> dict:
        env = {
            "PI_UNRAID_CANDIDATE_ID": CANDIDATE["candidate_id"],
            "PI_UNRAID_PI_VERSION": CANDIDATE["components"]["pi"]["version"],
            "PI_UNRAID_SPECPI_VERSION": CANDIDATE["components"]["specpi"]["version"],
            "PI_UNRAID_PI_MCP_ADAPTER_VERSION": CANDIDATE["components"]["pi_mcp_adapter"]["version"],
        }
        return manager.validate_candidate(CANDIDATE, env)

    def _materialize_exact(self, home: Path, desired: dict) -> None:
        agent = home / ".pi/agent"
        npm = agent / "npm"
        node_modules = npm / "node_modules"
        node_modules.mkdir(parents=True)
        settings = {"packages": [desired[key]["source"] for key in sorted(desired)]}
        (agent / "settings.json").write_text(json.dumps(settings))
        lock = {"packages": {}}
        for key, want in desired.items():
            package_dir = node_modules / want["package"]
            package_dir.mkdir(parents=True)
            (package_dir / "package.json").write_text(
                json.dumps({"name": want["package"], "version": want["version"]})
            )
            lock["packages"][f"node_modules/{want['package']}"] = {
                "version": want["version"],
                "integrity": want["integrity"],
            }
        (npm / "package-lock.json").write_text(json.dumps(lock))

    def test_candidate_and_image_bind_exact_managed_versions(self) -> None:
        desired = self._desired()
        self.assertEqual(desired["specpi"]["version"], "0.34.0")
        self.assertEqual(desired["pi_mcp_adapter"]["version"], "2.37.0")
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn('PI_UNRAID_SPECPI_VERSION="0.34.0"', dockerfile)
        self.assertIn('PI_UNRAID_PI_MCP_ADAPTER_VERSION="2.37.0"', dockerfile)
        self.assertNotIn("specpi@latest", dockerfile)
        self.assertNotIn("pi-mcp-adapter@latest", dockerfile)

    def test_exact_install_remains_red_until_compatibility_marker(self) -> None:
        desired = self._desired()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self._materialize_exact(home, desired)
            before = manager.build_status(
                home,
                CANDIDATE["candidate_id"],
                desired,
                runtime_pi_version="0.87.1",
                expected_pi_version="0.87.1",
            )
            self.assertFalse(before["in_sync"])
            self.assertEqual(before["compatibility"]["reason"], "compatibility_smoke_missing")
            self.assertTrue(all(item["installed_exact"] for item in before["packages"].values()))
            self.assertTrue(all(item["state"] == "RED" for item in before["packages"].values()))

            path = manager._compatibility_path(home)
            path.parent.mkdir(parents=True)
            manager._atomic_json(
                path,
                manager._compatibility_payload(CANDIDATE["candidate_id"], desired, "0.87.1"),
                mode=0o600,
            )
            after = manager.build_status(
                home,
                CANDIDATE["candidate_id"],
                desired,
                runtime_pi_version="0.87.1",
                expected_pi_version="0.87.1",
            )
            self.assertTrue(after["in_sync"])
            self.assertTrue(after["compatibility"]["verified"])

    def test_unexpected_values_are_fingerprinted_not_exposed(self) -> None:
        desired = self._desired()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self._materialize_exact(home, desired)
            settings_path = home / ".pi/agent/settings.json"
            settings = json.loads(settings_path.read_text())
            settings["packages"][0] = "npm:pi-mcp-adapter@9.9.9-raw-sentinel"
            settings_path.write_text(json.dumps(settings))
            status = manager.build_status(
                home,
                CANDIDATE["candidate_id"],
                desired,
                runtime_pi_version="0.87.1",
                expected_pi_version="0.87.1",
            )
            encoded = json.dumps(status, sort_keys=True)
            self.assertNotIn("9.9.9-raw-sentinel", encoded)
            self.assertIn("source_fingerprint", encoded)

    def test_snapshot_contains_only_prior_managed_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = {
                "theme": "dark",
                "packages": [
                    {"source": "npm:unrelated-example@1.2.3", "autoload": False},
                    "npm:specpi@0.33.0",
                ],
                "customUnrelated": {"keep": "sentinel"},
            }
            (agent / "settings.json").write_text(json.dumps(settings))
            self.assertTrue(manager.write_snapshot(home, CANDIDATE["candidate_id"]))
            snapshot = json.loads(manager._snapshot_path(home).read_text())
            self.assertEqual(len(snapshot["prior_managed_packages"]), 1)
            self.assertEqual(snapshot["prior_managed_packages"][0]["key"], "specpi")
            encoded = json.dumps(snapshot)
            self.assertNotIn("unrelated-example", encoded)
            self.assertNotIn("customUnrelated", encoded)


if __name__ == "__main__":
    unittest.main()
