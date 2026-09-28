from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_relay_doctor_readiness.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "paseo-relay-doctor-readiness.yml"
CARD_PATH = ROOT / "implementation" / "workstreams" / "feature-paseo-gui-runtime" / "cards" / "M06-T03.md"
SPEC = importlib.util.spec_from_file_location("paseo_relay_doctor_readiness", SCRIPT)
FLOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FLOW)

HARNESS = SCRIPT.read_text()
COMPOSE = (ROOT / "compose.yaml").read_text()
ACCESS = (ROOT / "scripts" / "paseo-relay-access.sh").read_text()
CONFIGURE = (ROOT / "scripts" / "configure-paseo-runtime.sh").read_text()
SMOKE = (ROOT / "scripts" / "verify-compose-foundation.sh").read_text()
DOC = (ROOT / "docs" / "PASEO_RELAY_AUTH.md").read_text()


def run_harness(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=120,
    )


class RelayDoctorReadinessContractTests(unittest.TestCase):
    def test_static_readback_verdict_is_technical_slice_green_only(self) -> None:
        completed = run_harness("readback")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["card"], "M06-T03")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["verdict"], "technical_green_ha_outstanding")
        self.assertIs(report["full_green_claimed"], False)

    def test_readback_report_file_matches_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "readback.json"
            completed = run_harness("readback", "--report", str(report_path))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(report_path.read_text()), json.loads(completed.stdout))

    def test_readback_structure_covers_all_acceptance_surfaces(self) -> None:
        report = FLOW.build_readback(ROOT)
        for key in ("candidate", "relay", "runtime_network", "inventory",
                    "capability_control", "healthcheck", "auth_fingerprints",
                    "activation_policy", "ha_deferred"):
            self.assertIn(key, report)
        self.assertEqual(len(report["ha_deferred"]), 14)
        self.assertIs(report["full_green_claimed"], False)

    def test_ha_deferral_owners_match_p4_wave(self) -> None:
        owners = {(item["need"], item["owner"]) for item in FLOW.HA_DEFERRED}
        for need in ("real_phone_pairing", "secret_supply", "oauth_device_flow",
                     "account_choice", "two_factor_approval", "manual_login_approval",
                     "interactive_github_auth", "authenticated_github_workflow",
                     "graphql_credential_materialization", "authenticated_graphql_mutation",
                     "manual_ux_judgment"):
            self.assertIn((need, "M07-T02"), owners)
        self.assertIn(("pairing_transfer_ux", "M07-T03"), owners)
        self.assertIn(("production_confirmation", "M07-T03"), owners)
        self.assertIn(("specpi_wishlist_activation", "M07-T05"), owners)

    def test_no_wishlist_activation_path_and_phone_unclaimed(self) -> None:
        report, violations = FLOW.check_no_activation_path(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["wishlist_owner"], "M07-T05")
        self.assertIsNone(report["wishlist_activation_path"])
        self.assertIs(report["phone_pairing_claimed"], False)

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

    def test_candidate_mismatch_is_a_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, violations = FLOW.check_candidate_identity(root)
            self.assertTrue(violations)
            config = root / "config"
            config.mkdir()
            (config / "paseo-candidate.json").write_text(json.dumps({
                "candidate_id": "sha256:wrong",
                "components": {"paseo": {"version": "0.0.0", "artifact": {"digest": "x"}},
                               "pi": {"version": "0.0.0"}},
                "policy": {"build_must_not_reresolve": True},
            }))
            (root / "Dockerfile").write_text("FROM scratch\n")
            _, violations = FLOW.check_candidate_identity(root)
            self.assertIn("candidate_id mismatch", violations)

    def test_relay_default_disabled_at_configure_time(self) -> None:
        self.assertIn(
            "paseo daemon config set daemon.relay.enabled false --home /home/paseo/.paseo",
            CONFIGURE,
        )
        self.assertIn('cfg["daemon"]["relay"]["enabled"] is False', CONFIGURE)
        report, violations = FLOW.check_relay_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertIs(report["default_disabled"], True)

    def test_pairing_helper_requires_explicit_consent_gate(self) -> None:
        for marker in ("require_tty", "read -r answer", "[y/N]",
                       "paseo daemon pair --relay --home /home/paseo/.paseo",
                       "Pairing cancelled; Relay was not enabled by this helper."):
            self.assertIn(marker, ACCESS)
        report, _ = FLOW.check_relay_policy(ROOT)
        self.assertIs(report["consent_gate"], True)

    def test_first_auth_stays_explicit_and_home_backed(self) -> None:
        self.assertIn("auth-shell", ACCESS)
        self.assertIn("exec -w /home/paseo paseo sh", ACCESS)
        self.assertIn(
            "First-time provider or account authentication is never part of normal container startup",
            DOC,
        )

    def test_status_is_metadata_only_and_never_prints_keypair(self) -> None:
        for marker in ('"relay_enabled"', '"daemon_keypair"',
                       '"pairing_requires_human_action"',
                       '"device_revocation_cli": "unsupported"'):
            self.assertIn(marker, ACCESS)
        self.assertNotIn('daemon-keypair.json").read_text', ACCESS)
        self.assertIn("never prints the keypair", DOC)
        report, _ = FLOW.check_relay_policy(ROOT)
        self.assertIs(report["metadata_only_status"], True)

    def test_revocation_fails_closed_where_upstream_lacks_support(self) -> None:
        self.assertIn('"supported":false', ACCESS)
        self.assertIn("no-individual-device-revocation-cli", ACCESS)
        self.assertIn("no command for listing and individually revoking", DOC)
        report, _ = FLOW.check_relay_policy(ROOT)
        self.assertIs(report["revocation_supported"], False)
        self.assertEqual(report["revocation_reason"], "no-individual-device-revocation-cli")

    def test_m02_relay_smoke_boundary_markers_are_present(self) -> None:
        for marker in ('"code":"RELAY_DISABLED"', "paseo daemon pair --relay --json",
                       'cfg["daemon"]["relay"]["enabled"] is True', "daemon-keypair.json",
                       "keypair_sha_before", "keypair_sha_after", '= "600"',
                       "{{len .HostConfig.PortBindings}}", '"relay_default_disabled":true',
                       '"relay_enabled_after_consent":true',
                       '"relay_enabled_after_recreate":true',
                       '"daemon_identity_persisted":true'):
            self.assertIn(marker, SMOKE)

    def test_zero_public_ports_and_only_bounded_codex_file_secret(self) -> None:
        report, violations = FLOW.check_runtime_network_shape(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["public_ports"], 0)
        self.assertIs(report["ports_published"], False)
        self.assertIs(report["file_secret_wiring"], True)
        self.assertNotIn("ports:", COMPOSE)

    def test_no_secret_env_or_forbidden_runtime_keys(self) -> None:
        report, _ = FLOW.check_runtime_network_shape(ROOT)
        self.assertEqual(report["secret_env_wiring"], [])
        self.assertEqual(report["forbidden_keys"], [])
        for token in ("PASEO_PASSWORD", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                      "GITHUB_TOKEN", "MUSE_API_KEY", "CODEX_API_KEY",
                      "CODEX_LB_API_KEY:", "/var/run/docker.sock"):
            self.assertNotIn(token, COMPOSE)

    def test_runtime_identity_shape_preserved(self) -> None:
        self.assertIn('user: "${PASEO_UID:-99}:${PASEO_GID:-100}"', COMPOSE)
        self.assertIn('shm_size: "1gb"', COMPOSE)
        self.assertIn("driver: json-file", COMPOSE)

    def test_inventory_authority_and_coverage(self) -> None:
        report, violations = FLOW.check_inventory_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["authority"], "environment_availability_only")
        self.assertEqual(report["capabilities"], 12)
        self.assertEqual(report["green_state"], "GREEN")
        self.assertEqual(report["drift_state"], "RED")

    def test_inventory_drift_classification_without_silent_deletion(self) -> None:
        report, _ = FLOW.check_inventory_policy(ROOT)
        self.assertEqual(report["drift"]["pi"], "missing")
        self.assertEqual(report["drift"]["node"], "version_mismatch")
        self.assertEqual(report["drift"]["unexpected"], "reported_fingerprinted")

    def test_inventory_desired_state_has_no_duplicate_literals_or_network(self) -> None:
        definition_text = (ROOT / "config" / "environment-capabilities.json").read_text()
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        for component in candidate["components"].values():
            version = component.get("version")
            if isinstance(version, str):
                self.assertNotIn(version, definition_text)
        script_text = (ROOT / "scripts" / "environment_capability_inventory.py").read_text()
        for token in ("import urllib", "import requests", "import subprocess"):
            self.assertNotIn(token, script_text)

    def test_inventory_derivation_is_secret_safe(self) -> None:
        inventory, _ = FLOW._load_scripts()
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        bare = inventory.derive_inventory(definition, candidate, ROOT)
        perfect = {
            item["id"]: {"present": True, "version": item["desired"]["version"],
                         "location": item["runtime_location"]["value"]}
            for item in bare["capabilities"]
        }
        secret = "CONTRACT-SECRET-PROBE-MUST-NOT-APPEAR"
        perfect["pi"]["version"] = secret
        derived = inventory.derive_inventory(definition, candidate, ROOT, perfect)
        text = json.dumps(derived)
        self.assertNotIn(secret, text)
        self.assertIn("version_fingerprint", text)

    def test_doctor_quick_and_full_are_green_machine_readable(self) -> None:
        report, violations = FLOW.check_control_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["quick_state"], "GREEN")
        self.assertEqual(report["full_state"], "GREEN")
        self.assertEqual(report["full_checks"], 12)
        self.assertLess(report["quick_checks"], report["full_checks"])
        self.assertEqual(report["reconcile_green_plan"], "clean")
        self.assertEqual(report["unexpected_policy"], "report_only_never_delete")

    def test_reconcile_targets_only_drifted_approved_state(self) -> None:
        inventory, control = FLOW._load_scripts()
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        bare = inventory.derive_inventory(definition, candidate, ROOT)
        perfect = {
            item["id"]: {"present": True, "version": item["desired"]["version"],
                         "location": item["runtime_location"]["value"]}
            for item in bare["capabilities"]
        }
        drifted_obs = dict(perfect)
        drifted_obs["pi"] = {"present": False}
        drifted_obs["node"] = {"present": True, "version": "drift", "location": "drift"}
        drifted = inventory.derive_inventory(definition, candidate, ROOT, drifted_obs)
        plan = control.build_reconcile_plan(drifted)
        self.assertEqual(sorted(a["capability_id"] for a in plan["actions"]), ["node", "pi"])
        self.assertTrue(all(a["operation"] == "restore_desired_state" for a in plan["actions"]))
        self.assertIs(plan["desired_state_mutation"], False)

    def test_reconcile_readback_claims_restoration_only_on_exact_green(self) -> None:
        inventory, control = FLOW._load_scripts()
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        bare = inventory.derive_inventory(definition, candidate, ROOT)
        perfect = {
            item["id"]: {"present": True, "version": item["desired"]["version"],
                         "location": item["runtime_location"]["value"]}
            for item in bare["capabilities"]
        }
        drifted_obs = dict(perfect)
        drifted_obs["pi"] = {"present": False}
        drifted = inventory.derive_inventory(definition, candidate, ROOT, drifted_obs)
        green = inventory.derive_inventory(definition, candidate, ROOT, dict(perfect))
        plan = control.build_reconcile_plan(drifted)
        restored = control.verify_reconcile_readback(drifted, green, plan)
        self.assertEqual(restored["state"], "GREEN")
        unresolved = control.verify_reconcile_readback(drifted, drifted, plan)
        self.assertEqual(unresolved["state"], "RED")

    def test_reconcile_never_silently_accepts_disappearing_extra(self) -> None:
        inventory, control = FLOW._load_scripts()
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        bare = inventory.derive_inventory(definition, candidate, ROOT)
        perfect = {
            item["id"]: {"present": True, "version": item["desired"]["version"],
                         "location": item["runtime_location"]["value"]}
            for item in bare["capabilities"]
        }
        drifted_obs = dict(perfect)
        drifted_obs["pi"] = {"present": False}
        drifted_obs["m06t03-vanishing-extra"] = {"present": True, "version": "x"}
        drifted = inventory.derive_inventory(definition, candidate, ROOT, drifted_obs)
        plan = control.build_reconcile_plan(drifted)
        clean = inventory.derive_inventory(definition, candidate, ROOT, dict(perfect))
        result = control.verify_reconcile_readback(drifted, clean, plan)
        self.assertEqual(result["state"], "RED")
        self.assertEqual(len(result["unexpected_disappeared"]), 1)

    def test_control_surface_owns_no_update_delete_or_policy(self) -> None:
        raw = (ROOT / "scripts" / "environment_capability_control.py").read_text()
        for token in ('add_parser("update")', '"operation": "delete', "shell=True",
                      "import subprocess", "import requests", "import urllib",
                      "role_ceiling", "assignment_eligibility", "task_scoped_grant",
                      "task_board", "workflow_state"):
            self.assertNotIn(token, raw)

    def test_healthcheck_is_lightweight_parent_inherited(self) -> None:
        report, violations = FLOW.check_healthcheck_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["probe"], "http_health")
        self.assertEqual(report["path"], "/api/health")
        self.assertEqual(report["port"], 6767)
        self.assertIs(report["compose_override"], False)

    def test_health_probe_markers_in_smoke_and_inventory(self) -> None:
        self.assertIn("/api/health", SMOKE)
        self.assertIn("6767", SMOKE)
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        paseo = next(c for c in definition["capabilities"] if c["id"] == "paseo")
        self.assertEqual(paseo["probe"]["kind"], "http_health")
        self.assertEqual(paseo["probe"]["path"], "/api/health")

    def test_auth_health_is_bounded_fingerprints_only(self) -> None:
        report, violations = FLOW.check_auth_fingerprint_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertIs(report["fingerprints_only"], True)
        self.assertEqual(report["surfaces"], ["inventory_version", "inventory_location",
                                              "unexpected_id", "reconcile_refusal"])

    def test_credential_injection_leaves_only_fingerprints(self) -> None:
        inventory, _ = FLOW._load_scripts()
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        bare = inventory.derive_inventory(definition, candidate, ROOT)
        perfect = {
            item["id"]: {"present": True, "version": item["desired"]["version"],
                         "location": item["runtime_location"]["value"]}
            for item in bare["capabilities"]
        }
        secret = "INJECTION-PROBE-SECRET-MUST-NOT-APPEAR"
        tainted = dict(perfect)
        tainted["pi"] = {"present": True, "version": secret,
                         "location": f"https://u:{secret}@x.invalid", "token": secret}
        text = json.dumps(inventory.derive_inventory(definition, candidate, ROOT, tainted))
        self.assertNotIn(secret, text)
        self.assertNotIn("token", text)
        self.assertIn("version_fingerprint", text)
        self.assertIn("location_fingerprint", text)

    def test_reconcile_refusal_fingerprints_unknown_ids(self) -> None:
        inventory, control = FLOW._load_scripts()
        definition = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        bare = inventory.derive_inventory(definition, candidate, ROOT)
        perfect = {
            item["id"]: {"present": True, "version": item["desired"]["version"],
                         "location": item["runtime_location"]["value"]}
            for item in bare["capabilities"]
        }
        payload = inventory.derive_inventory(definition, candidate, ROOT, dict(perfect))
        secret = "REFUSAL-PROBE-SECRET"
        with self.assertRaises(Exception) as caught:
            control.build_reconcile_plan(payload, requested_ids=[f"unknown-{secret}"])
        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("sha256:", str(caught.exception))

    def test_harness_refuses_non_disposable_scope(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            FLOW.guard_disposable_scope("production", Path(tempfile.gettempdir()))
        self.assertIn("refusing non-disposable scope", str(caught.exception))

    def test_harness_refuses_fixture_root_outside_temp(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            FLOW.guard_disposable_scope("disposable", Path("/mnt/user/appdata/pi-unraid"))
        self.assertIn("refusing fixture root outside system temp", str(caught.exception))

    def test_harness_accepts_temp_fixture_root(self) -> None:
        resolved = FLOW.guard_disposable_scope("disposable", Path(tempfile.gettempdir()))
        self.assertTrue(resolved.is_absolute())

    def test_failure_report_is_machine_readable_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "failure.json"
            text = FLOW.write_failure_report(path, "disposable", "probe failure")
            self.assertIsNotNone(text)
            payload = json.loads(path.read_text())
            self.assertEqual(payload["card"], "M06-T03")
            self.assertEqual(payload["outcome"], "failed")
            self.assertIs(payload["full_green_claimed"], False)
            self.assertIs(payload["production_mutation"], False)
            self.assertIsNone(FLOW.write_failure_report(path, "disposable", "second"))

    def test_kv_probe_parsing_keeps_single_line_semantics(self) -> None:
        values = FLOW.parse_kv_output("sha=abc123\nmode=600:99:100\nidentity_check=done\n")
        self.assertEqual(values, {"sha": "abc123", "mode": "600:99:100",
                                  "identity_check": "done"})
        joined = FLOW.parse_kv_output("network_tools=/a /b /c /d\n")
        self.assertEqual(joined["network_tools"].split(), ["/a", "/b", "/c", "/d"])

    def test_secret_scan_flags_high_confidence_patterns_only(self) -> None:
        FLOW.scan_secret_safe("relay_enabled sha=abc health GREEN", "clean context")
        with self.assertRaises(SystemExit):
            FLOW.scan_secret_safe("leak ghp_" + "A" * 24 + " end", "gh token")
        with self.assertRaises(SystemExit):
            FLOW.scan_secret_safe("-----BEGIN PRIVATE KEY-----", "pem block")

    def test_bounded_output_truncates_long_diagnostics(self) -> None:
        self.assertEqual(FLOW.bounded_output("short"), "short")
        long_text = "x" * 7000
        truncated = FLOW.bounded_output(long_text)
        self.assertLess(len(truncated), len(long_text))
        self.assertIn("truncated", truncated)

    def test_inventory_and_doctor_phases_pass_without_docker(self) -> None:
        drift = FLOW.phase_inventory_drift(ROOT)
        self.assertEqual(drift["green_state"], "GREEN")
        self.assertEqual(drift["drift_state"], "RED")
        self.assertEqual(drift["unexpected_deleted"], 0)
        reconcile = FLOW.phase_reconcile_doctor(ROOT)
        self.assertEqual(reconcile["restored_state"], "WARN")
        self.assertEqual(reconcile["restored_warn_reason"], "unexpected_extra_still_reported")
        self.assertEqual(reconcile["unrestored_state"], "RED")
        self.assertEqual(reconcile["drifted_full_state"], "RED")
        fingerprints = FLOW.phase_auth_fingerprints(ROOT)
        self.assertIs(fingerprints["fingerprints_only"], True)

    def test_flow_refuses_without_docker_or_production_scope(self) -> None:
        completed = run_harness("flow", "--scope", "production", "--image", "dummy:tag")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("refusing non-disposable scope", completed.stderr)

    def test_workflow_pins_all_six_predecessor_bindings(self) -> None:
        text = WORKFLOW_PATH.read_text()
        for commit, path, blob in (
            ("724d24e6d25d9a405998d8c6f48bbe65318ba4b4",
             "implementation/workstreams/feature-paseo-gui-runtime/results/M06-T02.md",
             "13a49bd857c50b79213561ece74e06a585069d73"),
            ("0f8538f7d226c6c022b5070aeca42375ba2d751a",
             "implementation/workstreams/feature-paseo-gui-runtime/results/M06-T01.md",
             "e01bd1dd4d84c94ec9b29f7bd1914e7160162d82"),
            ("d70e95292c561ad7ca5491027a221a7c22177574",
             "implementation/workstreams/feature-paseo-gui-runtime/results/M02-T02.md",
             "7b8574df581ace7e62125b8dc79fb48c1e491e7d"),
            ("727b6f25a3b957551d10c9c24d9e9d1e26efd6ab",
             "implementation/workstreams/feature-paseo-gui-runtime/results/M02-T01.md",
             "e5075d474bb7aaf0583baf66757add56fb556253"),
            ("affd83590ec534ed144b9048a2b9075434761f27",
             "implementation/workstreams/feature-paseo-gui-runtime/results/M04-T01.md",
             "5173447ec3ab8775450a9defbf193aede63ca290"),
            ("e9a412557bfbe927a64b1f7ba0d892f5f059e08a",
             "implementation/workstreams/feature-paseo-gui-runtime/results/M04-T02.md",
             "c6adc8514548b701c3aa959df9f5a6f4ff581a9d"),
        ):
            self.assertIn(commit, text)
            self.assertIn(path, text)
            self.assertIn(blob, text)

    def test_workflow_covers_suite_readback_flow_refusal_and_upload(self) -> None:
        text = WORKFLOW_PATH.read_text()
        self.assertIn("tests/test_paseo_relay_doctor_readiness_contract.py", text)
        self.assertIn("tests/test_paseo_rpc_workspace_contract.py", text)
        self.assertIn("tests/test_paseo_browser_tool_compat_contract.py", text)
        self.assertIn("paseo_relay_doctor_readiness.py readback", text)
        self.assertIn("paseo_relay_doctor_readiness.py flow", text)
        self.assertIn("relay_doctor_readiness_green", text)
        self.assertIn("refusing non-disposable scope", text)
        self.assertIn("/mnt/user/appdata/pi-unraid", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("set -o pipefail", text)

    def test_card_binds_scope_acceptance_and_dependencies(self) -> None:
        card = CARD_PATH.read_text()
        self.assertIn("Card ID: M06-T03", card)
        self.assertIn("Relay default-disabled fail-closed without consent", card)
        self.assertIn("synthetic-identity persistence/recreate survival", card)
        self.assertIn("zero public ports", card)
        self.assertIn("GREEN/WARN/RED", card)
        self.assertIn("technical slice GREEN only", card)
        self.assertIn("claims no full GREEN", card)
        for blob in ("13a49bd857c50b79213561ece74e06a585069d73",
                     "e01bd1dd4d84c94ec9b29f7bd1914e7160162d82",
                     "7b8574df581ace7e62125b8dc79fb48c1e491e7d",
                     "e5075d474bb7aaf0583baf66757add56fb556253",
                     "5173447ec3ab8775450a9defbf193aede63ca290",
                     "c6adc8514548b701c3aa959df9f5a6f4ff581a9d"):
            self.assertIn(blob, card)


if __name__ == "__main__":
    unittest.main()
