from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "environment_capability_inventory.py"
DEFINITION_PATH = ROOT / "config" / "environment-capabilities.json"
CANDIDATE_PATH = ROOT / "config" / "paseo-candidate.json"

spec = importlib.util.spec_from_file_location("environment_inventory", SCRIPT)
inventory = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(inventory)

DEFINITION = json.loads(DEFINITION_PATH.read_text())
CANDIDATE = json.loads(CANDIDATE_PATH.read_text())


class EnvironmentCapabilityInventoryContractTests(unittest.TestCase):
    def _perfect_observations(self) -> dict:
        derived = inventory.derive_inventory(DEFINITION, CANDIDATE, ROOT)
        return {
            item["id"]: {
                "present": True,
                "version": item["desired"]["version"],
                "location": item["runtime_location"]["value"],
            }
            for item in derived["capabilities"]
        }

    def test_definition_covers_frozen_candidate_and_repository_capabilities(self) -> None:
        inventory.validate_definition(DEFINITION)
        ids = {item["id"] for item in DEFINITION["capabilities"]}
        self.assertTrue(set(CANDIDATE["components"]).issubset(ids))
        self.assertTrue({"chromium", "base_tooling", "pi_instruction_plane"}.issubset(ids))
        self.assertEqual(DEFINITION["authority"], "environment_availability_only")

        raw = DEFINITION_PATH.read_text().lower()
        forbidden = (
            "role_ceilings",
            "action_classification",
            "role_default_bundles",
            "assignment_eligibility",
            "task_scoped_grants",
            "task_board",
            "workflow_state",
        )
        for token in forbidden:
            self.assertNotIn(token, raw)

    def test_desired_state_is_derived_without_duplicate_version_literals_or_network(self) -> None:
        derived = inventory.derive_inventory(DEFINITION, CANDIDATE, ROOT)
        by_id = {item["id"]: item for item in derived["capabilities"]}

        for component_id, component in CANDIDATE["components"].items():
            self.assertEqual(by_id[component_id]["desired"]["version"], component["version"])

        self.assertEqual(
            by_id["chromium"]["desired"]["version"],
            CANDIDATE["components"]["playwright"]["chromium"]["browser_version"],
        )
        self.assertEqual(
            by_id["base_tooling"]["desired"]["version"],
            CANDIDATE["policy"]["generic_base_tooling_identity"],
        )
        self.assertEqual(
            by_id["base_tooling"]["desired"]["members"],
            CANDIDATE["policy"]["generic_base_tooling"],
        )
        self.assertTrue(by_id["pi_instruction_plane"]["desired"]["version"].startswith("sha256:"))
        self.assertEqual(
            by_id["pi_instruction_plane"]["desired"]["version"],
            inventory.repo_tree_identity(ROOT, "config/pi-agent"),
        )

        definition_text = DEFINITION_PATH.read_text()
        for component in CANDIDATE["components"].values():
            version = component.get("version")
            if isinstance(version, str):
                self.assertNotIn(version, definition_text)

        script_text = SCRIPT.read_text()
        self.assertNotIn("import urllib", script_text)
        self.assertNotIn("import requests", script_text)
        self.assertNotIn("import subprocess", script_text)

    def test_observations_classify_exact_missing_mismatch_and_unexpected_drift(self) -> None:
        observations = self._perfect_observations()
        green = inventory.derive_inventory(DEFINITION, CANDIDATE, ROOT, observations)
        self.assertEqual(green["state"], "GREEN")
        self.assertTrue(all(item["health"] == "GREEN" for item in green["capabilities"]))
        self.assertTrue(all(item["drift"] == "none" for item in green["capabilities"]))
        self.assertTrue(
            all(item["observed"]["version"] == item["desired"]["version"] for item in green["capabilities"])
        )
        self.assertTrue(
            all(
                item["observed"]["location"] == item["runtime_location"]["value"]
                for item in green["capabilities"]
            )
        )

        missing_observations = copy.deepcopy(observations)
        missing_observations["pi"] = {"present": False}
        missing = inventory.derive_inventory(
            DEFINITION, CANDIDATE, ROOT, missing_observations
        )
        missing_pi = next(item for item in missing["capabilities"] if item["id"] == "pi")
        self.assertEqual(missing["state"], "RED")
        self.assertEqual(missing_pi["health"], "RED")
        self.assertEqual(missing_pi["drift"], "missing")

        mismatch_observations = copy.deepcopy(observations)
        mismatch_observations["node"]["version"] = "not-the-frozen-version"
        mismatch = inventory.derive_inventory(
            DEFINITION, CANDIDATE, ROOT, mismatch_observations
        )
        mismatch_node = next(
            item for item in mismatch["capabilities"] if item["id"] == "node"
        )
        self.assertEqual(mismatch["state"], "RED")
        self.assertEqual(mismatch_node["drift"], "version_mismatch")
        self.assertNotIn("version", mismatch_node["observed"])
        self.assertEqual(
            mismatch_node["observed"]["version_fingerprint"],
            inventory._observation_fingerprint("not-the-frozen-version"),
        )

        unexpected_observations = copy.deepcopy(observations)
        unexpected_observations["unknown_extra"] = {
            "present": True,
            "version": "arbitrary",
            "delete": True,
        }
        unexpected = inventory.derive_inventory(
            DEFINITION, CANDIDATE, ROOT, unexpected_observations
        )
        self.assertEqual(unexpected["state"], "WARN")
        self.assertEqual(
            unexpected["unexpected_observations"],
            [
                {
                    "id_fingerprint": inventory._observation_fingerprint("unknown_extra"),
                    "health": "WARN",
                    "drift": "unexpected",
                }
            ],
        )
        unexpected_json = json.dumps(unexpected)
        self.assertNotIn("unknown_extra", unexpected_json)
        self.assertNotIn("delete", unexpected_json)

    def test_output_is_deterministic_and_observations_are_secret_safe(self) -> None:
        observations = self._perfect_observations()
        secret = "RAW-CREDENTIAL-MATERIAL-MUST-NOT-APPEAR"
        observations["pi"]["token"] = secret
        observations["pi"]["credential"] = secret
        observations["pi"]["version"] = secret
        observations["pi"]["location"] = f"https://user:{secret}@example.invalid"
        observations[f"unknown-{secret}"] = {"token": secret, "present": True}

        first = inventory.derive_inventory(DEFINITION, CANDIDATE, ROOT, observations)
        second = inventory.derive_inventory(DEFINITION, CANDIDATE, ROOT, observations)
        first_json = json.dumps(first, sort_keys=True, separators=(",", ":"))
        second_json = json.dumps(second, sort_keys=True, separators=(",", ":"))

        self.assertEqual(first_json, second_json)
        self.assertNotIn(secret, first_json)
        self.assertNotIn("token", first_json)
        self.assertNotIn("credential", first_json)

        pi_observed = next(
            item["observed"] for item in first["capabilities"] if item["id"] == "pi"
        )
        self.assertEqual(
            pi_observed["version_fingerprint"],
            inventory._observation_fingerprint(secret),
        )
        self.assertEqual(
            pi_observed["location_fingerprint"],
            inventory._observation_fingerprint(
                f"https://user:{secret}@example.invalid"
            ),
        )
        self.assertNotIn("version", pi_observed)
        self.assertNotIn("location", pi_observed)

    def test_definition_rejects_or_and_pw_policy_fields(self) -> None:
        for forbidden_key in ("role_ceilings", "action_classification", "task_board"):
            with self.subTest(forbidden_key=forbidden_key):
                bad = copy.deepcopy(DEFINITION)
                bad[forbidden_key] = {}
                with self.assertRaises(inventory.InventoryError):
                    inventory.validate_definition(bad)


if __name__ == "__main__":
    unittest.main()
