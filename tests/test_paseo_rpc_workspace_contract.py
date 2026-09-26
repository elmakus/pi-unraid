from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_rpc_workspace_flow.py"
SPEC = importlib.util.spec_from_file_location("paseo_rpc_workspace_flow", SCRIPT)
FLOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FLOW)

COMPOSE = (ROOT / "compose.yaml").read_text()
HARNESS = SCRIPT.read_text()


def run_harness(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=120,
    )


class RpcWorkspaceContractTests(unittest.TestCase):
    def test_static_readback_verdict_is_technical_green_only(self) -> None:
        completed = run_harness("readback")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["card"], "M06-T01")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["verdict"], "technical_green_ha_outstanding")
        self.assertIs(report["full_green_claimed"], False)

    def test_candidate_identity_is_exact_and_frozen(self) -> None:
        identity, violations = FLOW.check_candidate_identity(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(
            identity["candidate_id"],
            "sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69",
        )
        self.assertEqual(identity["paseo_version"], "0.9.2")
        self.assertEqual(identity["pi_version"], "0.87.1")
        self.assertEqual(
            identity["base_digest"],
            "sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136",
        )
        self.assertIs(identity["frozen"], True)

    def test_workspace_mounts_outside_home_intended_roots_only(self) -> None:
        shape = FLOW.parse_compose_shape(COMPOSE)
        self.assertEqual(shape["targets"], ["/home/paseo", "/projects", "/worktrees"])
        self.assertEqual(shape["create_host_path_false"], 3)
        self.assertTrue(shape["paseo_service"])
        self.assertFalse(shape["legacy_pi_service"])
        for target in shape["targets"]:
            self.assertNotIn(target, ("/", "/mnt", "/home", "/mnt/user"))

    def test_ownership_shm_no_caps_bounded_logs(self) -> None:
        shape = FLOW.parse_compose_shape(COMPOSE)
        self.assertTrue(shape["user"])
        self.assertTrue(shape["shm_1gb"])
        self.assertTrue(shape["restart_unless_stopped"])
        self.assertTrue(shape["log_max_size"])
        self.assertTrue(shape["log_max_file"])
        self.assertEqual(shape["forbidden_present"], [])
        self.assertFalse(shape["ports_block"])
        self.assertFalse(shape["entrypoint_override"])
        self.assertFalse(shape["secrets_block"])
        self.assertEqual(FLOW.check_compose_shape(shape), [])
        mutated = FLOW.parse_compose_shape(COMPOSE + "\n    mem_limit: 1g\n")
        self.assertIn("mem_limit:", mutated["forbidden_present"])
        self.assertTrue(
            any("forbidden runtime keys" in item for item in FLOW.check_compose_shape(mutated))
        )

    def test_autostart_validated_without_enablement_path(self) -> None:
        report, violations = FLOW.check_autostart(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["restart_policy"], "unless-stopped")
        self.assertIs(report["config_validated"], True)
        self.assertIs(report["production_autostart_enabled"], False)
        self.assertIsNone(report["production_enablement_path"])
        for args in (["--help"], ["flow", "--help"]):
            completed = run_harness(*args)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertNotIn("enable", completed.stdout.lower())
        refused = run_harness("flow", "--scope", "production", "--image", "example:tag")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("refusing non-disposable scope", refused.stderr)

    def test_explicit_selection_and_recovery_rules(self) -> None:
        report, violations = FLOW.check_instruction_plane(ROOT)
        self.assertEqual(violations, [])
        self.assertIs(report["explicit_selection"], True)
        self.assertIs(report["no_inference"], True)
        self.assertIs(report["recovery_before_mutation"], True)
        self.assertIs(report["no_second_board"], True)
        self.assertIn("project-recovery", report["skills"])

    def test_rpc_on_demand_without_permanent_process(self) -> None:
        report, violations = FLOW.check_rpc_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["on_demand_mechanism"], "pi --mode rpc --no-session")
        self.assertIs(report["on_demand_proven_by_smoke"], True)
        self.assertIs(report["permanent_rpc_required"], False)
        self.assertIs(report["absence_without_session_is_failure"], False)
        self.assertNotIn("rpc", COMPOSE.lower())

    def test_ha_deferral_list_is_fail_closed(self) -> None:
        report = FLOW.build_readback(ROOT)
        deferred = {item["need"]: item["owner"] for item in report["ha_deferred"]}
        for need in (
            "secret_supply", "oauth_device_flow", "account_choice",
            "two_factor_approval", "manual_login_approval", "real_phone_pairing",
            "interactive_github_auth", "graphql_credential_materialization",
            "authenticated_graphql_mutation", "manual_ux_judgment",
        ):
            self.assertEqual(deferred.get(need), "M07-T02", need)
        self.assertEqual(deferred.get("production_confirmation"), "M07-T03")

    def test_scope_guard_refuses_production_paths(self) -> None:
        with self.assertRaises(SystemExit):
            FLOW.guard_disposable_scope("production", Path("/tmp"))
        with self.assertRaises(SystemExit):
            FLOW.guard_disposable_scope("staged", Path("/tmp"))
        for bad in (
            "/mnt/user/appdata/pi-unraid/paseo-home",
            "/mnt/user/projects",
            "/mnt/user/pi-worktrees",
            "/etc",
            "/home",
        ):
            with self.assertRaises(SystemExit, msg=bad):
                FLOW.guard_disposable_scope("disposable", Path(bad))
        self.assertEqual(
            FLOW.guard_disposable_scope("disposable", Path("/tmp")), Path("/tmp")
        )

    def test_rpc_response_validation(self) -> None:
        good = json.dumps({"id": "probe", "type": "response",
                           "command": "get_state", "success": True})
        self.assertIs(FLOW.validate_rpc_response(good + "\n", "probe"), True)
        with self.assertRaises(SystemExit):
            FLOW.validate_rpc_response("not json\n", "probe")
        bad = json.dumps({"id": "probe", "type": "response",
                          "command": "get_state", "success": False})
        with self.assertRaises(SystemExit):
            FLOW.validate_rpc_response(bad + "\n", "probe")

    def test_docker_run_places_image_before_command(self) -> None:
        with mock.patch.object(FLOW, "run_command", return_value="ok") as mocked:
            FLOW.docker_run("img:tag", ["-i", "--shm-size=1gb"], ["pi", "--mode", "rpc"])
        argv = mocked.call_args.args[0]
        self.assertLess(argv.index("img:tag"), argv.index("pi"))
        self.assertEqual(argv[:3], ["docker", "run", "--rm"])

    def test_harness_is_secret_safe(self) -> None:
        self.assertIsNone(FLOW.SECRET_VALUE_PATTERN.search(HARNESS))
        for forbidden in (
            "OPENAI_API_KEY=", "ANTHROPIC_API_KEY=", "GITHUB_TOKEN=",
            "MUSE_API_KEY=", "CODEX_API_KEY=", "BEGIN PRIVATE KEY",
        ):
            self.assertNotIn(forbidden, HARNESS)


if __name__ == "__main__":
    unittest.main()
