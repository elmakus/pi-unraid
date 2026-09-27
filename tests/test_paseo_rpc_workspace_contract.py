from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_rpc_workspace_flow.py"
WORKFLOW = (ROOT / ".github" / "workflows" / "paseo-rpc-workspace.yml").read_text()
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

    def test_fixture_chown_covers_nested_content(self) -> None:
        # CI run 36265204193 RED: host-created fixture .git stayed
        # runner-owned after a non-recursive chown, so container git failed
        # with dubious ownership. The transfer must be recursive.
        with mock.patch.object(FLOW, "run_command", return_value="") as mocked:
            FLOW.chown_fixture("img:tag", Path("/tmp/fixture"))
        argv = mocked.call_args.args[0]
        self.assertIn("-R", argv)
        self.assertIn("99:100", argv)
        for target in ("/fixture/home", "/fixture/projects", "/fixture/worktrees"):
            self.assertIn(target, argv)

    def test_flow_uses_recursive_fixture_chown(self) -> None:
        self.assertIn("chown_fixture(image, fixture)", HARNESS)

    def test_nested_ownership_probe_covers_workspace_mounts(self) -> None:
        snippet = FLOW.nested_ownership_snippet()
        for mount in ("/home/paseo", "/projects", "/worktrees"):
            self.assertIn(mount, snippet)
        self.assertIn("-not -user 99", snippet)
        self.assertIn("-not -group 100", snippet)
        self.assertIn("foreign=", snippet)
        self.assertIn("check_nested_ownership(image, home, projects, worktrees)", HARNESS)

    def test_flow_failure_emits_machine_readable_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "flow.json"
            FLOW.write_failure_report(report, "disposable", "boom")
            payload = json.loads(report.read_text())
        self.assertEqual(payload["outcome"], "failed")
        self.assertEqual(payload["card"], "M06-T01")
        self.assertIs(payload["full_green_claimed"], False)
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "flow.json"
            report.write_text('{"outcome": "integrated_flow_green"}')
            FLOW.write_failure_report(report, "disposable", "boom")
            self.assertIn("integrated_flow_green", report.read_text())

    def test_piped_workflow_steps_preserve_command_failure(self) -> None:
        blocks = re.split(r"(?m)^      - name: ", WORKFLOW)
        piped = [block for block in blocks if "| tee" in block]
        self.assertGreaterEqual(len(piped), 3)
        for block in piped:
            self.assertIn("set -o pipefail", block)

    def test_recovery_verifier_accepts_exact_durable_state(self) -> None:
        detail = FLOW.verify_recovered_state(
            head_before="abc123",
            head_after="abc123",
            status_porcelain="",
            state_json_text=FLOW.fixture_state_text(),
            project_text=FLOW.fixture_project_text(),
            sessions_absent=True,
        )
        self.assertEqual(detail["project"], "m06-t01-fixture-project")
        self.assertEqual(detail["selection_method"], "explicit")
        self.assertIn("TASK_BOARD.toml", detail["board"]["path"])
        self.assertIs(detail["sessions_absent"], True)

    def test_recovery_verifier_rejects_session_presence(self) -> None:
        with self.assertRaises(SystemExit):
            FLOW.verify_recovered_state(
                head_before="abc123",
                head_after="abc123",
                status_porcelain="",
                state_json_text=FLOW.fixture_state_text(),
                project_text=FLOW.fixture_project_text(),
                sessions_absent=False,
            )

    def test_recovery_verifier_rejects_head_mismatch(self) -> None:
        with self.assertRaises(SystemExit):
            FLOW.verify_recovered_state(
                head_before="abc123",
                head_after="def456",
                status_porcelain="",
                state_json_text=FLOW.fixture_state_text(),
                project_text=FLOW.fixture_project_text(),
                sessions_absent=True,
            )

    def test_recovery_verifier_rejects_dirty_worktree(self) -> None:
        with self.assertRaises(SystemExit):
            FLOW.verify_recovered_state(
                head_before="abc123",
                head_after="abc123",
                status_porcelain="?? PROJECT.md",
                state_json_text=FLOW.fixture_state_text(),
                project_text=FLOW.fixture_project_text(),
                sessions_absent=True,
            )

    def test_recovery_verifier_rejects_absent_or_corrupt_state(self) -> None:
        for bad_state in ("", "not json", '{"project": "wrong-project"}',
                          json.dumps({"project": "m06-t01-fixture-project"})):
            with self.assertRaises(SystemExit, msg=bad_state[:30]):
                FLOW.verify_recovered_state(
                    head_before="abc123",
                    head_after="abc123",
                    status_porcelain="",
                    state_json_text=bad_state,
                    project_text=FLOW.fixture_project_text(),
                    sessions_absent=True,
                )
        with self.assertRaises(SystemExit):
            FLOW.verify_recovered_state(
                head_before="abc123",
                head_after="abc123",
                status_porcelain="",
                state_json_text=FLOW.fixture_state_text(),
                project_text="unrelated text",
                sessions_absent=True,
            )

    def test_fixture_commit_is_contentful_canonical_state(self) -> None:
        # Recovery reads from the Git object store via argv ["show",
        # "HEAD:<path>"], never a joined shell string.
        self.assertIn('"show", "HEAD:canonical-state.json"', HARNESS)
        self.assertIn('"show", "HEAD:PROJECT.md"', HARNESS)
        self.assertNotIn("--allow-empty", HARNESS)
        self.assertIn("verify_recovered_state", HARNESS)

    # Observed CI shape (run 36268682202, PIDs vary per run; the witness
    # takes the daemon worker pid dynamically, never hardcoded).
    OBSERVED_PS = (
        "    PID    PPID COMMAND          COMMAND\n"
        "      1       0 tini             /usr/bin/tini -- /usr/local/bin/paseo-docker-entrypoint\n"
        "      7       1 Paseo Supervisor Paseo Supervisor\n"
        "     48       7 Paseo Daemon     Paseo Daemon\n"
        "     60      48 node             /usr/local/bin/node /usr/local/lib/node_modules/@getpaseo/server/dist/server/terminal/terminal-worker-process.js\n"
        "    219      48 pi               pi\n"
        "   1004       0 sh               sh -c ps -eo pid,ppid,comm,args\n"
        "   1010    1004 ps               ps -eo pid,ppid,comm,args\n"
    )

    def test_daemon_child_witness_accepts_observed_shape(self) -> None:
        # The literal `pi --mode rpc` predicate missed this real spawn: the
        # daemon's pi child shows bare `pi` (argv/title normalization). The
        # repaired witness matches comm/argv-basename plus daemon ancestry.
        candidates = FLOW.find_pi_children(self.OBSERVED_PS)
        self.assertEqual([(c["pid"], c["ppid"]) for c in candidates], [("219", "48")])
        hit = FLOW.bind_daemon_child(candidates, "48", FLOW.pid_info_map(self.OBSERVED_PS))
        self.assertIsNotNone(hit)
        self.assertEqual(hit["pid"], "219")
        self.assertEqual(hit["parent_match"], "worker_pid")

    def test_daemon_child_witness_rejects_wrong_parent(self) -> None:
        impostor = (
            "    PID    PPID COMM COMMAND\n"
            "     48       7 Paseo Daemon Paseo Daemon\n"
            "    219    1004 pi pi\n"
            "   1004       0 sh sh -c probe\n"
        )
        candidates = FLOW.find_pi_children(impostor)
        self.assertEqual(len(candidates), 1)
        self.assertIsNone(FLOW.bind_daemon_child(candidates, "48", FLOW.pid_info_map(impostor)))

    def test_daemon_child_witness_avoids_false_positives(self) -> None:
        noise = (
            "    PID    PPID COMM COMMAND\n"
            "     11       7 pip pip install something\n"
            "     12       7 happy /usr/local/bin/happy --serve\n"
            "     13       7 node node app.js --pi-flag\n"
            "     14       7 sh sh -c ps -eo pid,ppid,comm,args\n"
        )
        self.assertEqual(FLOW.find_pi_children(noise), [])
        self.assertIsNone(FLOW.bind_daemon_child([], "48", {}))

    def test_worker_pid_parse(self) -> None:
        self.assertEqual(FLOW.parse_worker_pid("home: /home/paseo/.paseo\nworkerPid: 48\n"), "48")
        self.assertIsNone(FLOW.parse_worker_pid("no pid here\n"))

    def test_agent_table_id_parse(self) -> None:
        table = (
            "AGENT ID                              STATUS      PROVIDER    CWD\n"
            "d6057fcc-ff7f-462b-a0aa-ed51e740a4a3  running     pi          /projects\n"
        )
        self.assertEqual(FLOW.parse_agent_id(table), "d6057fcc-ff7f-462b-a0aa-ed51e740a4a3")
        self.assertEqual(FLOW.parse_agent_id('{"id": "abc"}'), "abc")
        self.assertIsNone(FLOW.parse_agent_id("nothing here\n"))

    def test_pi_agent_binding(self) -> None:
        listing = json.dumps([{"id": "d6057fcc-ff7f-462b-a0aa-ed51e740a4a3",
                               "provider": "pi/unknown/unknown", "status": "error"}])
        bound = FLOW.find_pi_agent(listing, "d6057fcc-ff7f-462b-a0aa-ed51e740a4a3")
        self.assertIsNotNone(bound)
        self.assertEqual(bound["status"], "error")
        self.assertIsNone(FLOW.find_pi_agent(listing, "other-id"))
        other = json.dumps([{"id": "x", "provider": "codex/y", "status": "running"}])
        self.assertIsNone(FLOW.find_pi_agent(other, "x"))
        self.assertIsNone(FLOW.find_pi_agent("not json", "x"))

    def test_agent_error_classification(self) -> None:
        self.assertEqual(FLOW.classify_agent_error("running", "ok"), "none")
        self.assertEqual(FLOW.classify_agent_error("error", "provider login required"), "model_auth")
        self.assertEqual(FLOW.classify_agent_error("error", "model api key missing"), "model_auth")
        self.assertEqual(FLOW.classify_agent_error("error", "weird internal fault"), "other")
        self.assertEqual(FLOW.classify_agent_error("error", ""), "unknown")

    def test_spawn_blocker_classifier(self) -> None:
        self.assertEqual(FLOW.classify_spawn_blocker("Error: RELAY_DISABLED"), "relay_disabled")
        self.assertEqual(FLOW.classify_spawn_blocker("not onboarded"), "onboarding")
        for text in ("401 unauthorized", "provider login required",
                     "missing api key", "forbidden"):
            self.assertEqual(FLOW.classify_spawn_blocker(text), "auth", text)
        self.assertIsNone(FLOW.classify_spawn_blocker("spawn ok"))
        self.assertIsNone(FLOW.classify_spawn_blocker(""))

    def test_pi_diagnostic_check_requires_frozen_version(self) -> None:
        self.assertTrue(FLOW.check_pi_diagnostic('{"provider": "pi", "version": "0.87.1"}'))
        self.assertFalse(FLOW.check_pi_diagnostic('{"provider": "pi"}'))
        self.assertFalse(FLOW.check_pi_diagnostic(""))

    def test_paseo_spawn_uses_documented_cli_path(self) -> None:
        self.assertIn("provider diagnostic pi", HARNESS)
        self.assertIn('"run", "--provider", "pi"', HARNESS)
        self.assertIn("paseo_spawn_probe", HARNESS)
        self.assertIn("PASEO_SPAWN_BLOCKED", HARNESS)

    def test_paseo_spawn_refuses_production_scope(self) -> None:
        refused = run_harness("paseo-spawn", "--scope", "production", "--image", "example:tag")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("refusing non-disposable scope", refused.stderr)

    def test_secret_redactor_masks_trust_anchors(self) -> None:
        offer = "connect https://app.paseo.sh/#offer=abc123DEF456 end"
        self.assertNotIn("abc123DEF456", FLOW.redact_secrets(offer))
        self.assertIn("offer=<redacted>", FLOW.redact_secrets(offer))
        bearer = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload"
        redacted = FLOW.redact_secrets(bearer)
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", redacted)
        self.assertIn("Bearer <redacted>", redacted)
        assignment = "db password=hunter2 active"
        redacted = FLOW.redact_secrets(assignment)
        self.assertNotIn("hunter2", redacted)
        self.assertIn("password=<redacted>", redacted)

    def test_secret_redactor_preserves_benign_text(self) -> None:
        text = "pi 0.87.1 available; relay disabled; 2 mounts"
        self.assertEqual(FLOW.redact_secrets(text), text)

    def test_run_output_gate_classification_wired(self) -> None:
        self.assertIn("classify_spawn_blocker(run_out)", HARNESS)

    def test_main_emits_report_on_unexpected_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "spawn.json"
            with mock.patch.object(FLOW, "paseo_spawn_probe",
                                   side_effect=RuntimeError("boom")):
                with self.assertRaises(RuntimeError):
                    with contextlib.redirect_stdout(io.StringIO()):
                        FLOW.main(["paseo-spawn", "--scope", "disposable",
                                   "--image", "img:tag", "--report", str(report)])
            payload = json.loads(report.read_text())
        self.assertEqual(payload["outcome"], "failed")
        self.assertIn("boom", payload["error"])

    def test_main_emits_report_on_system_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "spawn.json"
            with mock.patch.object(FLOW, "paseo_spawn_probe",
                                   side_effect=SystemExit("no child")):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stdout(io.StringIO()):
                        FLOW.main(["paseo-spawn", "--scope", "disposable",
                                   "--image", "img:tag", "--report", str(report)])
            payload = json.loads(report.read_text())
        self.assertEqual(payload["outcome"], "failed")

    def test_failure_report_write_failure_does_not_mask_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "missing-dir" / "spawn.json"
            with mock.patch.object(FLOW, "paseo_spawn_probe",
                                   side_effect=RuntimeError("original")):
                with self.assertRaises(RuntimeError, msg="original must propagate, not OSError"):
                    FLOW.main(["paseo-spawn", "--scope", "disposable",
                               "--image", "img:tag", "--report", str(report)])

    def test_spawn_probe_collects_diagnostics(self) -> None:
        for marker in ("collect_spawn_diagnostics", "daemon.log", "paseo ls",
                       "docker logs", "ps -ef", "sessions", "--tail"):
            self.assertIn(marker, HARNESS, marker)

    def test_harness_is_secret_safe(self) -> None:
        self.assertIsNone(FLOW.SECRET_VALUE_PATTERN.search(HARNESS))
        for forbidden in (
            "OPENAI_API_KEY=", "ANTHROPIC_API_KEY=", "GITHUB_TOKEN=",
            "MUSE_API_KEY=", "CODEX_API_KEY=", "BEGIN PRIVATE KEY",
        ):
            self.assertNotIn(forbidden, HARNESS)


if __name__ == "__main__":
    unittest.main()
