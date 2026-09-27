from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

DOCTOR_PATH = SCRIPTS / "unraid_host_control_doctor.py"
POLICY_PATH = ROOT / "config" / "unraid-host-control" / "host-safety-policy.json"

spec = importlib.util.spec_from_file_location("host_doctor", DOCTOR_PATH)
doctor = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(doctor)

POLICY = json.loads(POLICY_PATH.read_text())


class HostControlDoctorContractTests(unittest.TestCase):
    def test_policy_health_is_green_and_detects_gate_drift(self) -> None:
        green = doctor.policy_check(POLICY)
        self.assertEqual(green["state"], "GREEN")
        self.assertEqual(green["primary_transport"], "graphql")

        drift = json.loads(json.dumps(POLICY))
        drift["gated_operations"]["host_reboot"]["user_gate"] = "none"
        red = doctor.policy_check(drift)
        self.assertEqual(red["state"], "RED")
        self.assertEqual(red["error"], "policy")

    def test_graphql_check_is_read_only_and_secret_safe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            key_file = Path(td) / "api-key"
            secret = "c" * 64
            key_file.write_text(secret)
            key_file.chmod(0o600)
            payload = {
                "info": {"id": "tower"},
                "docker": {"containers": [{"id": "docker:demo"}]},
            }
            with mock.patch.object(doctor.graphql_control, "graphql", return_value=payload) as gql, \
                 mock.patch.object(doctor.graphql_control, "perform_container_action") as mutate:
                result = doctor.graphql_check("http://tower/graphql", str(key_file))
            self.assertEqual(result["state"], "GREEN")
            self.assertEqual(result["capabilities"]["container_count"], 1)
            self.assertNotIn(secret, json.dumps(result))
            self.assertTrue(result["credential"]["fingerprint"].startswith("sha256:"))
            mutate.assert_not_called()
            gql.assert_called_once()

    def test_graphql_failures_map_to_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            key_file = Path(td) / "api-key"
            key_file.write_text("d" * 64)
            key_file.chmod(0o600)
            failure = doctor.graphql_control.HostControlError("graphql", "GraphQL request failed")
            with mock.patch.object(doctor.graphql_control, "graphql", side_effect=failure):
                result = doctor.graphql_check("http://tower/graphql", str(key_file))
        self.assertEqual(result["state"], "RED")
        self.assertEqual(result["error"], "graphql")

    def test_graphql_transport_auth_and_protocol_failures_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            key_file = Path(td) / "api-key"
            secret = "f" * 64
            key_file.write_text(secret)
            key_file.chmod(0o600)

            cases = (
                (
                    doctor.graphql_control.HostControlError(
                        "transport",
                        "GraphQL endpoint is unreachable",
                    ),
                    "transport",
                    None,
                ),
                (
                    doctor.graphql_control.HostControlError(
                        "http",
                        "GraphQL endpoint returned an HTTP error",
                        status=401,
                    ),
                    "auth",
                    401,
                ),
                (
                    doctor.graphql_control.HostControlError(
                        "protocol",
                        "GraphQL endpoint returned invalid JSON",
                    ),
                    "protocol",
                    None,
                ),
            )

            for failure, expected_error, expected_status in cases:
                with self.subTest(expected_error=expected_error), \
                     mock.patch.object(doctor.graphql_control, "graphql", side_effect=failure):
                    result = doctor.graphql_check("http://tower/graphql", str(key_file))
                self.assertEqual(result["state"], "RED")
                self.assertEqual(result["error"], expected_error)
                self.assertNotIn(secret, json.dumps(result))
                if expected_status is None:
                    self.assertNotIn("http_status", result)
                else:
                    self.assertEqual(result["http_status"], expected_status)

    def test_ssh_quick_and_full_checks_remain_read_only_and_secret_safe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            identity = td / "id"
            known = td / "known_hosts"
            secret = "PRIVATE-KEY-MATERIAL"
            identity.write_text(secret)
            known.write_text("tower ssh-ed25519 AAAATEST")
            identity.chmod(0o600)
            known.chmod(0o644)

            quick = doctor.ssh_check(
                host="tower",
                user="root",
                identity_file=str(identity),
                known_hosts_file=str(known),
                depth="quick",
                policy=POLICY,
            )
            self.assertEqual(quick["state"], "GREEN")
            self.assertEqual(quick["reachability"], "not_checked")
            self.assertNotIn(secret, json.dumps(quick))

            with mock.patch.object(doctor.ssh_fallback, "probe", return_value={"probe": "GREEN"}) as probe, \
                 mock.patch.object(doctor.ssh_fallback, "gated_exec") as gated, \
                 mock.patch.object(doctor.ssh_fallback, "smoke_marker") as smoke:
                full = doctor.ssh_check(
                    host="tower",
                    user="root",
                    identity_file=str(identity),
                    known_hosts_file=str(known),
                    depth="full",
                    policy=POLICY,
                )
            self.assertEqual(full["state"], "GREEN")
            self.assertEqual(full["reachability"], "GREEN")
            probe.assert_called_once()
            gated.assert_not_called()
            smoke.assert_not_called()

    def test_optional_ssh_degradation_is_warn_but_core_failure_is_red(self) -> None:
        self.assertEqual(
            doctor.aggregate_state(
                {"state": "GREEN"},
                {"state": "WARN"},
                {"state": "GREEN"},
            ),
            "WARN",
        )
        self.assertEqual(
            doctor.aggregate_state(
                {"state": "RED"},
                {"state": "GREEN"},
                {"state": "GREEN"},
            ),
            "RED",
        )
        self.assertEqual(
            doctor.aggregate_state(
                {"state": "GREEN"},
                {"state": "GREEN"},
                {"state": "RED"},
            ),
            "RED",
        )

    def test_machine_and_human_surfaces_and_authority_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            key_file = Path(td) / "api-key"
            key_file.write_text("e" * 64)
            key_file.chmod(0o600)
            payload = {"info": {"id": "tower"}, "docker": {"containers": []}}
            with mock.patch.object(doctor.graphql_control, "graphql", return_value=payload), \
                 mock.patch.object(doctor.graphql_control, "perform_container_action") as mutate, \
                 mock.patch.object(doctor.ssh_fallback, "gated_exec") as gated, \
                 mock.patch.object(doctor.ssh_fallback, "smoke_marker") as smoke:
                result = doctor.doctor(
                    endpoint="http://tower/graphql",
                    api_key_file=str(key_file),
                    ssh_host=None,
                    ssh_user=None,
                    ssh_identity_file=None,
                    ssh_known_hosts_file=None,
                    depth="quick",
                    policy_path=POLICY_PATH,
                )
            self.assertEqual(result["state"], "WARN")
            self.assertIn("WARN:", result["summary"])
            self.assertEqual(result["doctor"], "unraid_host_control")
            self.assertNotIn("recovery", result["doctor"].lower())
            self.assertNotIn("orchestration", result["doctor"].lower())
            mutate.assert_not_called()
            gated.assert_not_called()
            smoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()
