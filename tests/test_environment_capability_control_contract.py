from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

INVENTORY_PATH = SCRIPTS / "environment_capability_inventory.py"
CONTROL_PATH = SCRIPTS / "environment_capability_control.py"
DEFINITION_PATH = ROOT / "config" / "environment-capabilities.json"
CANDIDATE_PATH = ROOT / "config" / "paseo-candidate.json"

inventory_spec = importlib.util.spec_from_file_location("environment_inventory_for_control", INVENTORY_PATH)
inventory = importlib.util.module_from_spec(inventory_spec)
assert inventory_spec.loader is not None
inventory_spec.loader.exec_module(inventory)
sys.modules["environment_capability_inventory"] = inventory

control_spec = importlib.util.spec_from_file_location("environment_control", CONTROL_PATH)
control = importlib.util.module_from_spec(control_spec)
assert control_spec.loader is not None
control_spec.loader.exec_module(control)

DEFINITION = json.loads(DEFINITION_PATH.read_text())
CANDIDATE = json.loads(CANDIDATE_PATH.read_text())


class EnvironmentCapabilityControlContractTests(unittest.TestCase):
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

    def _derive(self, observations: dict) -> dict:
        return inventory.derive_inventory(DEFINITION, CANDIDATE, ROOT, observations)

    def test_quick_and_full_doctor_are_deterministic_machine_and_human_surfaces(self) -> None:
        payload = self._derive(self._perfect_observations())
        quick_a = control.doctor(payload, depth="quick")
        quick_b = control.doctor(payload, depth="quick")
        full = control.doctor(payload, depth="full")

        self.assertEqual(quick_a, quick_b)
        self.assertEqual(quick_a["state"], "GREEN")
        self.assertEqual(full["state"], "GREEN")
        self.assertEqual(full["doctor"], "environment_capabilities")
        self.assertIn("GREEN:", full["summary"])
        self.assertLess(len(quick_a["checks"]), len(full["checks"]))
        self.assertEqual(len(full["checks"]), len(DEFINITION["capabilities"]))
        self.assertTrue(quick_a["deferred_capabilities"])
        self.assertEqual(full["deferred_capabilities"], [])

    def test_full_doctor_reports_missing_mismatch_unobserved_and_unexpected(self) -> None:
        observations = self._perfect_observations()
        observations["pi"] = {"present": False}
        observations["node"]["version"] = "wrong-version"
        observations.pop("specpi")
        observations["unknown-extra"] = {"present": True, "version": "anything"}

        result = control.doctor(self._derive(observations), depth="full")
        by_id = {item["id"]: item for item in result["checks"]}

        self.assertEqual(result["state"], "RED")
        self.assertEqual(by_id["pi"]["drift"], "missing")
        self.assertEqual(by_id["node"]["drift"], "version_mismatch")
        self.assertEqual(by_id["specpi"]["drift"], "unobserved")
        self.assertEqual(result["unexpected_observations"][0]["drift"], "unexpected")
        self.assertNotIn("unknown-extra", json.dumps(result))

    def test_optional_unobserved_full_check_is_warn_when_no_red_drift_exists(self) -> None:
        observations = self._perfect_observations()
        observations.pop("specpi")
        result = control.doctor(self._derive(observations), depth="full")
        self.assertEqual(result["state"], "WARN")
        specpi = next(item for item in result["checks"] if item["id"] == "specpi")
        self.assertEqual(specpi["health"], "WARN")
        self.assertEqual(specpi["drift"], "unobserved")

    def test_reconcile_targets_only_missing_or_mismatched_approved_state(self) -> None:
        observations = self._perfect_observations()
        observations["pi"] = {"present": False}
        observations["node"]["version"] = "wrong-version"
        observations["unknown-extra"] = {"present": True, "version": "anything"}
        payload = self._derive(observations)

        plan = control.build_reconcile_plan(payload)
        actions = {item["capability_id"]: item for item in plan["actions"]}

        self.assertEqual(set(actions), {"node", "pi"})
        self.assertEqual(actions["pi"]["operation"], "restore_desired_state")
        self.assertEqual(actions["pi"]["desired_version"], CANDIDATE["components"]["pi"]["version"])
        self.assertFalse(plan["desired_state_mutation"])
        self.assertEqual(plan["unexpected_policy"], "report_only_never_delete")
        self.assertEqual(len(plan["unexpected_observations"]), 1)
        self.assertNotIn("unknown-extra", json.dumps(plan))

    def test_reconcile_refuses_unknown_or_duplicate_requested_capabilities(self) -> None:
        payload = self._derive(self._perfect_observations())
        secret = "RAW-CREDENTIAL-IN-CAPABILITY-ID"
        with self.assertRaises(control.CapabilityControlError) as caught:
            control.build_reconcile_plan(payload, requested_ids=[f"not-approved-{secret}"])
        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("sha256:", str(caught.exception))
        with self.assertRaises(control.CapabilityControlError):
            control.build_reconcile_plan(payload, requested_ids=["pi", "pi"])

    def test_reconcile_readback_can_claim_restoration_only_after_exact_green_readback(self) -> None:
        before_observations = self._perfect_observations()
        before_observations["pi"] = {"present": False}
        before = self._derive(before_observations)
        plan = control.build_reconcile_plan(before)

        after = self._derive(self._perfect_observations())
        result = control.verify_reconcile_readback(before, after, plan)

        self.assertEqual(result["state"], "GREEN")
        self.assertEqual(result["actions"], [{
            "capability_id": "pi",
            "status": "restored",
            "pre": {"health": "RED", "drift": "missing"},
            "post": {"health": "GREEN", "drift": "none"},
        }])
        self.assertFalse(result["desired_state_mutation"])
        self.assertIn("restored=1", result["summary"])

        unresolved = control.verify_reconcile_readback(before, before, plan)
        self.assertEqual(unresolved["state"], "RED")
        self.assertEqual(unresolved["actions"][0]["status"], "unresolved")
        self.assertEqual(
            unresolved["actions"][0]["post"],
            {"health": "RED", "drift": "missing"},
        )

    def test_reconcile_apply_uses_only_canonical_actions_and_requires_readback(self) -> None:
        before_observations = self._perfect_observations()
        before_observations["pi"] = {"present": False}
        before = self._derive(before_observations)
        after = self._derive(self._perfect_observations())
        executed = []
        observations = []

        result = control.apply_reconcile(
            before,
            execute=lambda action: executed.append(action),
            observe=lambda: observations.append("readback") or after,
        )

        self.assertEqual(result["state"], "GREEN")
        self.assertEqual(result["applied_actions"], 1)
        self.assertEqual([item["capability_id"] for item in executed], ["pi"])
        self.assertEqual(executed[0]["operation"], "restore_desired_state")
        self.assertEqual(observations, ["readback"])

    def test_reconcile_readback_rejects_tampered_plan(self) -> None:
        before_observations = self._perfect_observations()
        before_observations["pi"] = {"present": False}
        before = self._derive(before_observations)
        plan = control.build_reconcile_plan(before)
        tampered = copy.deepcopy(plan)
        tampered["actions"][0]["desired_version"] = "not-the-frozen-version"
        after = self._derive(self._perfect_observations())

        with self.assertRaises(control.CapabilityControlError):
            control.verify_reconcile_readback(before, after, tampered)

    def test_reconcile_readback_rejects_desired_state_or_candidate_change(self) -> None:
        before_observations = self._perfect_observations()
        before_observations["pi"] = {"present": False}
        before = self._derive(before_observations)
        plan = control.build_reconcile_plan(before)
        after = self._derive(self._perfect_observations())

        changed_desired = copy.deepcopy(after)
        pi = next(item for item in changed_desired["capabilities"] if item["id"] == "pi")
        pi["desired"]["version"] = "different-version"
        with self.assertRaises(control.CapabilityControlError):
            control.verify_reconcile_readback(before, changed_desired, plan)

        changed_candidate = copy.deepcopy(after)
        changed_candidate["candidate_id"] = "sha256:different"
        with self.assertRaises(control.CapabilityControlError):
            control.verify_reconcile_readback(before, changed_candidate, plan)

    def test_reconcile_never_silently_accepts_disappearing_unexpected_extra(self) -> None:
        before_observations = self._perfect_observations()
        before_observations["pi"] = {"present": False}
        before_observations["unknown-extra"] = {"present": True, "version": "anything"}
        before = self._derive(before_observations)
        plan = control.build_reconcile_plan(before)

        after_without_extra = self._derive(self._perfect_observations())
        result = control.verify_reconcile_readback(before, after_without_extra, plan)

        self.assertEqual(result["state"], "RED")
        self.assertEqual(len(result["unexpected_disappeared"]), 1)

    def test_control_surface_is_read_only_and_does_not_own_update_or_or_pw_policy(self) -> None:
        raw = CONTROL_PATH.read_text()
        forbidden_imports = ("import subprocess", "import requests", "import urllib")
        for token in forbidden_imports:
            self.assertNotIn(token, raw)
        self.assertNotIn('add_parser("update")', raw)
        self.assertNotIn('"operation": "delete', raw)
        self.assertNotIn("shell=True", raw)
        for token in (
            "role_ceiling",
            "assignment_eligibility",
            "task_scoped_grant",
            "task_board",
            "workflow_state",
        ):
            self.assertNotIn(token, raw)


if __name__ == "__main__":
    unittest.main()
