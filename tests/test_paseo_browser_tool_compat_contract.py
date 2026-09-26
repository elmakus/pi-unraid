from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_browser_tool_compat.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "paseo-browser-tool-compat.yml"
CARD_PATH = ROOT / "implementation" / "workstreams" / "feature-paseo-gui-runtime" / "cards" / "M06-T02.md"
SPEC = importlib.util.spec_from_file_location("paseo_browser_tool_compat", SCRIPT)
FLOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FLOW)

HARNESS = SCRIPT.read_text()
DOCKERFILE = (ROOT / "Dockerfile").read_text()
COMPOSE = (ROOT / "compose.yaml").read_text()


def run_harness(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=120,
    )


def workflow_text() -> str:
    return WORKFLOW_PATH.read_text()


class BrowserToolCompatContractTests(unittest.TestCase):
    def test_static_readback_verdict_is_technical_green_only(self) -> None:
        completed = run_harness("readback")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["card"], "M06-T02")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["verdict"], "technical_green_ha_outstanding")
        self.assertIs(report["full_green_claimed"], False)

    def test_readback_report_file_matches_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "readback.json"
            completed = run_harness("readback", "--report", str(report_path))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(report_path.read_text()), json.loads(completed.stdout))

    def test_candidate_identity_is_exact_and_frozen(self) -> None:
        identity, violations = FLOW.check_candidate_identity(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(
            identity["candidate_id"],
            "sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69",
        )
        self.assertEqual(identity["paseo_version"], "0.9.2")
        self.assertEqual(identity["pi_version"], "0.87.1")
        self.assertEqual(identity["playwright_version"], "1.63.0")
        self.assertEqual(identity["chromium_version"], "153.0.8010.12")
        self.assertEqual(identity["chromium_revision"], "1243")
        self.assertEqual(identity["specpi_version"], "0.34.0")
        self.assertEqual(identity["pi_mcp_adapter_version"], "2.37.0")
        self.assertEqual(identity["gh_version"], "2.101.0")
        self.assertEqual(identity["docker_cli_version"], "29.8.1")
        self.assertEqual(identity["docker_compose_version"], "5.5.1")
        self.assertEqual(identity["node_version"], "22.23.3")
        self.assertEqual(
            identity["base_digest"],
            "sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136",
        )
        self.assertIs(identity["frozen"], True)

    def test_candidate_mismatch_is_a_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
            candidate["components"]["playwright"]["version"] = "9.9.9"
            (root / "config" / "paseo-candidate.json").write_text(json.dumps(candidate))
            (root / "Dockerfile").write_text(DOCKERFILE)
            _, violations = FLOW.check_candidate_identity(root)
            self.assertIn("playwright version mismatch", violations)

    def test_candidate_unreadable_is_a_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, violations = FLOW.check_candidate_identity(Path(tmp))
            self.assertTrue(any("unreadable" in item for item in violations))

    def test_browser_tooling_static_shape_is_green(self) -> None:
        report, violations = FLOW.check_browser_tooling(ROOT)
        self.assertEqual(violations, [])
        self.assertTrue(report["playwright_global_install"])
        self.assertTrue(report["chromium_install"])
        self.assertTrue(report["browsers_path"])
        self.assertTrue(report["xvfb"])
        self.assertTrue(report["gh_pinned"])
        self.assertTrue(report["docker_cli_pinned"])
        self.assertTrue(report["docker_compose_pinned"])
        self.assertFalse(report["socket_mounted"])
        self.assertFalse(report["ports_published"])
        self.assertEqual(report["automation_profile"], "/m06t02/profile")
        self.assertEqual(report["automation_downloads"], "/m06t02/downloads")

    def test_socket_mount_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Dockerfile").write_text(DOCKERFILE)
            (root / "compose.yaml").write_text(COMPOSE + "\n      - /var/run/docker.sock:/var/run/docker.sock\n")
            _, violations = FLOW.check_browser_tooling(root)
            self.assertIn("host docker socket must not be mounted", violations)

    def test_published_ports_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Dockerfile").write_text(DOCKERFILE)
            (root / "compose.yaml").write_text(COMPOSE + "\n    ports:\n      - 3000:3000\n")
            _, violations = FLOW.check_browser_tooling(root)
            self.assertIn("no public dev-server ports allowed", violations)

    def test_extension_policy_defers_wishlist_without_activation_path(self) -> None:
        report, violations = FLOW.check_extension_policy(ROOT)
        self.assertEqual(violations, [])
        self.assertEqual(report["specpi_scope_policy"], "inactive_in_fresh_session")
        self.assertTrue(report["compatibility_schema"])
        self.assertEqual(report["wishlist_owner"], "M07-T05")
        self.assertIsNone(report["wishlist_activation_path"])

    def test_ha_deferred_covers_interactive_and_postdeploy_needs(self) -> None:
        deferred = {(item["need"], item["owner"]) for item in FLOW.HA_DEFERRED}
        self.assertEqual(len(deferred), 12)
        for need, owner in (
            ("authenticated_github_workflow", "M07-T02"),
            ("manual_headed_ux_judgment", "M07-T02"),
            ("secret_supply", "M07-T02"),
            ("real_phone_pairing", "M07-T02"),
            ("graphql_credential_materialization", "M07-T02"),
            ("authenticated_graphql_mutation", "M07-T02"),
            ("specpi_wishlist_activation", "M07-T05"),
            ("production_confirmation", "M07-T03"),
        ):
            self.assertIn((need, owner), deferred)

    def test_scope_guard_refuses_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as ctx:
                FLOW.guard_disposable_scope("production", Path(tmp))
            self.assertIn("refusing non-disposable scope", str(ctx.exception))

    def test_scope_guard_refuses_fixture_outside_system_temp(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            FLOW.guard_disposable_scope("disposable", ROOT / "tmp-fixture")
        self.assertIn("refusing fixture root outside system temp", str(ctx.exception))

    def test_scope_guard_accepts_system_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            resolved = FLOW.guard_disposable_scope("disposable", Path(tmp))
            self.assertTrue(resolved.is_dir())

    def test_headless_script_captures_screenshot_and_pdf(self) -> None:
        js = FLOW.HEADLESS_JS
        self.assertIn("chromium.launch({headless:true})", js)
        self.assertIn("/m06t02/downloads/headless.png", js)
        self.assertIn("screenshot({path:", js)
        self.assertIn("/m06t02/downloads/headless.pdf", js)
        self.assertIn("pdf({path:", js)
        self.assertIn("capture=ok", js)
        self.assertIn(FLOW.PLAYWRIGHT_MODULE, js)

    def test_headed_script_uses_persistent_automation_profile_and_downloads(self) -> None:
        js = FLOW.HEADED_JS
        self.assertIn("launchPersistentContext('/m06t02/profile'", js)
        self.assertIn("headless:false", js)
        self.assertIn("downloadsPath:'/m06t02/downloads'", js)
        self.assertIn("waitForEvent('download'", js)
        self.assertIn("/m06t02/downloads/headed.png", js)
        self.assertNotIn("pdf({path:", js)
        for personal in (".config/google-chrome", ".config/chromium", ".mozilla",
                         "/home/paseo", "/root"):
            self.assertNotIn(personal, js)

    def test_headed_phase_runs_under_xvfb(self) -> None:
        source = HARNESS
        headed_call = source[source.index("def phase_browser_headed_xvfb"):source.index("def phase_profile_isolation")]
        self.assertIn('"xvfb-run", "-a"', headed_call)

    def test_personal_profile_paths_are_forbidden(self) -> None:
        self.assertEqual(
            list(FLOW.PERSONAL_PROFILE_PATHS),
            [".config/google-chrome", ".config/chromium", ".mozilla", ".pki"],
        )

    def test_flow_has_all_card_phases(self) -> None:
        for phase in ("phase_image_labels", "phase_browser_headless",
                      "phase_browser_headed_xvfb", "phase_profile_isolation",
                      "phase_dev_baseline", "phase_gh_unauth", "phase_docker_tooling",
                      "phase_extension_compat", "disposable_flow"):
            self.assertTrue(callable(getattr(FLOW, phase)), phase)

    def test_flow_reports_browser_tool_compat_green_only(self) -> None:
        self.assertIn('"browser_tool_compat_green"', HARNESS)
        self.assertNotIn("integrated_flow_green", HARNESS)
        occurrences = [match.start() for match in re.finditer("full GREEN", HARNESS)]
        self.assertEqual(len(occurrences), 1)
        self.assertIn("never", HARNESS[max(0, occurrences[0] - 30):occurrences[0]])

    def test_flow_requires_docker_runner(self) -> None:
        with mock.patch.object(FLOW.shutil, "which", return_value=None):
            with self.assertRaises(SystemExit) as ctx:
                FLOW.disposable_flow(ROOT, "image:tag", None)
            self.assertIn("Docker runner (CI)", str(ctx.exception))

    def test_production_scope_refused_before_flow(self) -> None:
        completed = run_harness("flow", "--scope", "production", "--image", "image:tag")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("refusing non-disposable scope", completed.stderr)

    def test_container_flags_stay_nonroot_with_browser_shm(self) -> None:
        flags = FLOW.container_flags("/host:/mnt")
        self.assertEqual(flags[:3], ["--user", "99:100", "--shm-size=1gb"])
        self.assertEqual(flags[3:5], ["-v", "/host:/mnt"])

    def test_version_line_parsing(self) -> None:
        self.assertEqual(FLOW.parse_version_line("version=153.0.8010.12\n", "version="),
                         "153.0.8010.12")
        with self.assertRaises(SystemExit):
            FLOW.parse_version_line("no version here\n", "version=")

    def test_failure_report_written_once_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "failure.json"
            written = FLOW.write_failure_report(report_path, "disposable", "boom")
            self.assertIsNotNone(written)
            payload = json.loads(report_path.read_text())
            self.assertEqual(payload["card"], "M06-T02")
            self.assertEqual(payload["outcome"], "failed")
            self.assertFalse(payload["full_green_claimed"])
            self.assertFalse(payload["production_mutation"])
            self.assertIsNone(FLOW.write_failure_report(report_path, "disposable", "other"))
            self.assertEqual(json.loads(report_path.read_text())["error"], "boom")
            self.assertIsNone(FLOW.write_failure_report(None, "disposable", "boom"))

    def test_secret_scan_rejects_credential_like_text(self) -> None:
        FLOW.scan_secret_safe("gh auth status: not logged in", "probe")
        with self.assertRaises(SystemExit):
            FLOW.scan_secret_safe("token ghp_1234567890abcdefghij", "probe")
        with self.assertRaises(SystemExit):
            FLOW.scan_secret_safe("-----BEGIN OPENSSH PRIVATE KEY-----", "probe")

    def test_extension_leg_reuses_proven_delivery_wrapper(self) -> None:
        self.assertIn("configure-pi-global-capabilities.sh", HARNESS)
        self.assertIn('"status", image', HARNESS)
        phase_source = HARNESS[HARNESS.index("def phase_extension_compat"):HARNESS.index("def disposable_flow")]
        self.assertIn("capability_status(root, image, home)", phase_source)
        self.assertIn('"apply", image', phase_source)
        self.assertIn("package_missing_or_invalid", phase_source)

    def test_extension_leg_asserts_wishlist_inactive_schema(self) -> None:
        phase_source = HARNESS[HARNESS.index("def phase_extension_compat"):HARNESS.index("def disposable_flow")]
        self.assertIn("wishlist_activation_performed", phase_source)
        self.assertIn('"wishlist_owner": "M07-T05"', HARNESS)
        self.assertIn("specpi_improvement_wishlist", phase_source)

    def test_record_appends_phase_entries(self) -> None:
        phases: list[dict] = []
        FLOW.record(phases, "fixture", "ok", {"root": "/tmp/x"})
        self.assertEqual(phases, [{"name": "fixture", "status": "ok", "detail": {"root": "/tmp/x"}}])

    def test_workflow_exists_with_predecessor_bindings(self) -> None:
        text = workflow_text()
        for commit, blob in (
            ("0f8538f7d226c6c022b5070aeca42375ba2d751a", "e01bd1dd4d84c94ec9b29f7bd1914e7160162d82"),
            ("fb6195831d047ede2f359146b69ede2690e84ef3", "e31658fda900d748010bedc6caa0bb3aacf8c430"),
            ("dd3047320faf92f0dfe9d0ac0a0f5ff590e11250", "4ccca450fa664344ef3ded7de33de7df7c79d8f9"),
            ("4e60c855a84b2e74d50de812db1ba9cc156af400", "be820f52901a9d2d4a40b71c3da6d19ffc08edea"),
            ("bbc862c37c0da81a08a91876499cfe865be958ab", "3772f647f5a0c55e856d3ae8e3feb05c6fb3e1f5"),
        ):
            self.assertIn(commit, text)
            self.assertIn(blob, text)

    def test_workflow_bindings_match_card_dependencies(self) -> None:
        card = CARD_PATH.read_text()
        text = workflow_text()
        bindings = re.findall(r"results/\S+?\.md@([0-9a-f]{40}):([0-9a-f]{40})", card)
        self.assertEqual(len(bindings), 5)
        for commit, blob in bindings:
            self.assertIn(commit, text)
            self.assertIn(blob, text)

    def test_workflow_runs_complete_suite_plus_flow_asserts(self) -> None:
        text = workflow_text()
        for suite in (
            "tests/test_paseo_browser_tool_compat_contract.py",
            "tests/test_paseo_candidate_resolver.py",
            "tests/test_paseo_child_image_contract.py",
            "tests/test_paseo_runtime_contract.py",
            "tests/test_paseo_relay_auth_contract.py",
            "tests/test_pi_instruction_plane_contract.py",
            "tests/test_pi_global_capabilities_contract.py",
            "tests/test_unraid_graphql_host_control_contract.py",
            "tests/test_unraid_host_control_guard_contract.py",
            "tests/test_unraid_host_control_doctor_contract.py",
            "tests/test_environment_capability_inventory_contract.py",
            "tests/test_environment_capability_control_contract.py",
            "tests/test_paseo_buildx_contract.py",
            "tests/test_paseo_tower_build_contract.py",
            "tests/test_paseo_staged_update_contract.py",
            "tests/test_paseo_staged_home_evidence_contract.py",
            "tests/test_paseo_rpc_workspace_contract.py",
        ):
            self.assertIn(suite, text)
        self.assertIn("browser_tool_compat_green", text)
        for phase in ("browser_headless", "browser_headed_xvfb", "profile_isolation",
                      "dev_baseline", "gh_unauth", "docker_tooling", "extension_compat"):
            self.assertIn(phase, text)

    def test_workflow_covers_readback_build_refusal_and_artifacts(self) -> None:
        text = workflow_text()
        self.assertIn("paseo_browser_tool_compat.py readback", text)
        self.assertIn("technical_green_ha_outstanding", text)
        self.assertIn("paseo_buildx.py build", text)
        self.assertIn("paseo_buildx.py test", text)
        self.assertIn("refusing non-disposable scope", text)
        self.assertIn("upload-artifact", text)
        self.assertIn("set -o pipefail", text)
        self.assertIn("feat/paseo-gui-runtime", text)

    def test_workflow_proves_disposable_scope_and_production_untouched(self) -> None:
        text = workflow_text()
        self.assertIn("/mnt/user/appdata/pi-unraid", text)
        self.assertIn("--filter ancestor=", text)

    def test_browser_flags_use_default_image_user_with_shm(self) -> None:
        flags = FLOW.browser_flags("/host:/mnt")
        self.assertNotIn("--user", flags)
        self.assertIn("--shm-size=1gb", flags)
        self.assertEqual(flags[-2:], ["-v", "/host:/mnt"])

    def test_browser_legs_use_default_user_and_debug_runner(self) -> None:
        headless_source = HARNESS[HARNESS.index("def phase_browser_headless"):HARNESS.index("def phase_browser_headed_xvfb")]
        headed_source = HARNESS[HARNESS.index("def phase_browser_headed_xvfb"):HARNESS.index("def phase_profile_isolation")]
        for source in (headless_source, headed_source):
            self.assertIn("browser_flags(", source)
            self.assertIn("docker_run_browser(", source)
            self.assertNotIn("container_flags(", source)

    def test_isolation_probe_stays_on_runtime_identity(self) -> None:
        isolation_source = HARNESS[HARNESS.index("def phase_profile_isolation"):HARNESS.index("def phase_dev_baseline")]
        self.assertIn("container_flags(", isolation_source)
        self.assertNotIn("browser_flags(", isolation_source)

    def test_prepare_browser_dirs_makes_fixture_writable(self) -> None:
        import os
        import stat
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            downloads = Path(tmp) / "downloads"
            profile.mkdir()
            downloads.mkdir()
            FLOW.prepare_browser_dirs(profile, downloads)
            self.assertEqual(stat.S_IMODE(os.stat(profile).st_mode), 0o777)
            self.assertEqual(stat.S_IMODE(os.stat(downloads).st_mode), 0o777)

    def test_bounded_output_keeps_tail_with_marker(self) -> None:
        self.assertEqual(FLOW.bounded_output("short"), "short")
        long_text = "x" * 7000 + "TAIL"
        bounded = FLOW.bounded_output(long_text)
        self.assertTrue(bounded.startswith("...[truncated]..."))
        self.assertTrue(bounded.endswith("TAIL"))
        self.assertLess(len(bounded), len(long_text))

    def test_browser_probe_failure_carries_full_output(self) -> None:
        proc = subprocess.CompletedProcess(
            args=["docker"], returncode=1,
            stdout="version=1.2.3\n", stderr="BROWSER_ERROR:boom-detail\n",
        )
        with mock.patch.object(FLOW, "run_command_unchecked", return_value=proc):
            with self.assertRaises(SystemExit) as ctx:
                FLOW.docker_run_browser("image", [], ["node"], what="headed xvfb browser probe")
        message = str(ctx.exception)
        self.assertIn("headed xvfb browser probe failed (1)", message)
        self.assertIn("BROWSER_ERROR:boom-detail", message)

    def test_browser_probe_output_is_secret_scanned(self) -> None:
        proc = subprocess.CompletedProcess(
            args=["docker"], returncode=1,
            stdout="token ghp_1234567890abcdefghij\n", stderr="",
        )
        with mock.patch.object(FLOW, "run_command_unchecked", return_value=proc):
            with self.assertRaises(SystemExit) as ctx:
                FLOW.docker_run_browser("image", [], ["node"], what="probe")
        self.assertIn("secret-like value", str(ctx.exception))

    def test_failure_report_carries_phases_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "failure.json"
            written = FLOW.write_failure_report(
                report_path, "disposable", "boom",
                extra={"phases_completed": ["fixture", "image_labels"]})
            self.assertIsNotNone(written)
            payload = json.loads(report_path.read_text())
            self.assertEqual(payload["phases_completed"], ["fixture", "image_labels"])
            self.assertEqual(payload["outcome"], "failed")


if __name__ == "__main__":
    unittest.main()
