from __future__ import annotations

import importlib
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

guard = importlib.import_module("unraid_host_safety_guard")
ssh = importlib.import_module("unraid_ssh_fallback")
router = importlib.import_module("unraid_host_control_router")
graphql = importlib.import_module("unraid_graphql_host_control")
POLICY = json.loads((ROOT / "config" / "unraid-host-control" / "host-safety-policy.json").read_text())


class FakeProc:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class UnraidHostControlGuardContractTests(unittest.TestCase):
    def test_policy_classifies_exact_high_impact_gates_and_graphql_ordinary_surface(self) -> None:
        expected_gated = {
            "ssh_admin_command", "host_reboot", "docker_engine_restart", "unraid_os_upgrade",
            "disk_format", "broad_share_delete", "broad_appdata_delete", "broad_network_change",
        }
        self.assertEqual(set(POLICY["gated_operations"]), expected_gated)
        for operation in expected_gated:
            rule = POLICY["gated_operations"][operation]
            self.assertTrue(rule["mutating"])
            self.assertEqual(rule["pre_readback"], "evidence_file")
            self.assertEqual(rule["user_gate"], "external_user_authorization")
            self.assertEqual(rule["rollback_anchor"], "required_if_applicable")
        expected_graphql = {f"graphql_container_{action}" for action in ("start", "stop", "restart", "pause", "unpause")}
        self.assertTrue(expected_graphql.issubset(POLICY["ordinary_operations"]))
        for operation in expected_graphql:
            rule = POLICY["ordinary_operations"][operation]
            self.assertEqual(rule["transport"], "graphql")
            self.assertTrue(rule["mutating"])
            self.assertEqual(rule["pre_readback"], "transport_internal")
            self.assertEqual(rule["user_gate"], "none")

    def test_unknown_operation_fails_closed(self) -> None:
        with self.assertRaises(guard.GuardError) as ctx:
            guard.evaluate("unclassified-danger", scope="sha256:test", policy=POLICY)
        self.assertEqual(ctx.exception.kind, "policy")

    def test_gated_command_binds_authorization_pre_readback_and_anchor_to_exact_scope(self) -> None:
        scope = guard.command_scope(["/usr/local/sbin/example-admin", "--target", "demo"])
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            pre, auth, anchor = td / "pre.json", td / "auth.json", td / "anchor.json"
            pre.write_text(json.dumps({"schema_version": 1, "kind": "pre_mutation_readback", "scope": scope, "ok": True}))
            auth.write_text(json.dumps({"schema_version": 1, "kind": "external_user_authorization", "scope": scope, "ok": True}))
            anchor.write_text(json.dumps({"schema_version": 1, "kind": "rollback_anchor", "scope": scope, "ok": True}))
            pre.chmod(0o644); auth.chmod(0o600); anchor.chmod(0o644)
            with self.assertRaises(guard.GuardError):
                guard.evaluate("ssh_admin_command", scope=scope, pre_readback_file=str(pre), policy=POLICY)
            decision = guard.evaluate(
                "ssh_admin_command", scope=scope, pre_readback_file=str(pre), authorization_file=str(auth),
                rollback_anchor_file=str(anchor), rollback_applicable=True, policy=POLICY,
            )
            self.assertEqual(decision["classification"], "gated")
            wrong = td / "wrong.json"
            wrong.write_text(json.dumps({"schema_version": 1, "kind": "external_user_authorization", "scope": "sha256:wrong", "ok": True}))
            wrong.chmod(0o600)
            with self.assertRaises(guard.GuardError):
                guard.evaluate(
                    "ssh_admin_command", scope=scope, pre_readback_file=str(pre),
                    authorization_file=str(wrong), policy=POLICY,
                )

    def test_ssh_identity_is_private_and_status_is_secret_safe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            identity, known = td / "id_ed25519", td / "known_hosts"
            private_value = "PRIVATE-MATERIAL-NOT-TO-PRINT"
            identity.write_text(private_value); identity.chmod(0o600)
            known.write_text("tower ssh-ed25519 AAAATEST\n"); known.chmod(0o644)
            config = ssh.validate_config("tower", "root", str(identity), str(known))
            payload = ssh.status(config)
            self.assertNotIn(private_value, json.dumps(payload))
            self.assertEqual(payload["identity_mode"], "600")
            self.assertTrue(payload["identity_fingerprint"].startswith("sha256:"))
            identity.chmod(0o644)
            with self.assertRaises(ssh.SshFallbackError):
                ssh.validate_config("tower", "root", str(identity), str(known))

    def test_ssh_transport_is_batch_only_strict_host_key_and_no_shell_true(self) -> None:
        source = (SCRIPTS / "unraid_ssh_fallback.py").read_text()
        self.assertNotIn("shell=True", source)
        config = {"host": "tower", "user": "root", "identity_file": "/secret/id", "known_hosts_file": "/secret/known_hosts"}
        joined = " ".join(ssh.ssh_argv(config, "uname -s"))
        for token in (
            "BatchMode=yes", "PasswordAuthentication=no", "KbdInteractiveAuthentication=no",
            "IdentitiesOnly=yes", "StrictHostKeyChecking=yes", "UserKnownHostsFile=/secret/known_hosts",
        ):
            self.assertIn(token, joined)

    def test_forced_smoke_marker_has_pre_post_and_automatic_restore(self) -> None:
        config = {"host": "tower", "user": "root", "identity_file": "id", "known_hosts_file": "kh"}
        sequence = [FakeProc("absent"), FakeProc(""), FakeProc("present"), FakeProc(""), FakeProc("absent")]
        with mock.patch.object(ssh, "run_remote", side_effect=sequence) as run:
            result = ssh.smoke_marker(config, reason="forced_test", policy=POLICY)
        self.assertEqual(result["pre_state"], "absent")
        self.assertEqual(result["post_state"], "present")
        self.assertEqual(result["restored_state"], "absent")
        self.assertEqual(result["rollback"], "automatic_cleanup")
        self.assertEqual(run.call_count, 5)
        with self.assertRaises(ssh.SshFallbackError):
            ssh.smoke_marker(config, reason="api_gap", policy=POLICY)

    def test_router_prefers_graphql_falls_back_only_on_outage_and_is_not_sticky(self) -> None:
        config = {"host": "tower", "user": "root", "identity_file": "id", "known_hosts_file": "kh"}
        with mock.patch.object(router, "graphql_readback", return_value={"info": {"id": "x"}}) as gql, \
             mock.patch.object(ssh, "readback", return_value={"ok": True, "transport": "ssh", "fallback_reason": "forced_test", "data": {}}) as sr:
            primary = router.routed_readback(
                endpoint="http://tower/graphql", api_key_file="/secret/key", ssh_config=None,
                explicit_reason=None, policy=POLICY,
            )
            self.assertEqual(primary["transport"], "graphql")
            gql.assert_called_once(); sr.assert_not_called()
            forced = router.routed_readback(
                endpoint="http://tower/graphql", api_key_file="/secret/key", ssh_config=config,
                explicit_reason="forced_test", policy=POLICY,
            )
            self.assertEqual(forced["transport"], "ssh")
            self.assertFalse(forced["primary_attempted"])
            again = router.routed_readback(
                endpoint="http://tower/graphql", api_key_file="/secret/key", ssh_config=None,
                explicit_reason=None, policy=POLICY,
            )
            self.assertEqual(again["transport"], "graphql")
            self.assertTrue(again["primary_attempted"])
        outage = graphql.HostControlError("transport", "down")
        with mock.patch.object(router, "graphql_readback", side_effect=outage), mock.patch.object(ssh, "readback") as sr:
            with self.assertRaises(router.RouterError) as ctx:
                router.routed_readback(
                    endpoint="http://tower/graphql", api_key_file="/secret/key", ssh_config=None,
                    explicit_reason=None, policy=POLICY,
                )
            self.assertEqual(ctx.exception.kind, "fallback_unavailable")
            sr.assert_not_called()
        with mock.patch.object(router, "graphql_readback", side_effect=outage), \
             mock.patch.object(ssh, "readback", return_value={"ok": True, "transport": "ssh", "fallback_reason": "api_outage", "data": {}}) as sr:
            fallback = router.routed_readback(
                endpoint="http://tower/graphql", api_key_file="/secret/key", ssh_config=config,
                explicit_reason=None, policy=POLICY,
            )
            self.assertEqual(fallback["transport"], "ssh")
            self.assertEqual(fallback["fallback_reason"], "api_outage")
            sr.assert_called_once()
        denied = graphql.HostControlError("graphql", "permission denied")
        with mock.patch.object(router, "graphql_readback", side_effect=denied), mock.patch.object(ssh, "readback") as sr:
            with self.assertRaises(router.RouterError) as ctx:
                router.routed_readback(
                    endpoint="http://tower/graphql", api_key_file="/secret/key", ssh_config=config,
                    explicit_reason=None, policy=POLICY,
                )
            self.assertEqual(ctx.exception.kind, "primary_failed_closed")
            sr.assert_not_called()

    def test_generic_ssh_admin_output_is_digest_only(self) -> None:
        config = {"host": "tower", "user": "root", "identity_file": "id", "known_hosts_file": "kh"}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            command, pre, auth = td / "command.json", td / "pre.json", td / "auth.json"
            argv = ["/usr/bin/example", "--safe"]
            command.write_text(json.dumps({"schema_version": 1, "argv": argv, "rollback_applicable": False})); command.chmod(0o644)
            scope = guard.command_scope(argv)
            pre.write_text(json.dumps({"schema_version": 1, "kind": "pre_mutation_readback", "scope": scope, "ok": True})); pre.chmod(0o644)
            auth.write_text(json.dumps({"schema_version": 1, "kind": "external_user_authorization", "scope": scope, "ok": True})); auth.chmod(0o600)
            secretish = "do-not-emit-this"
            with mock.patch.object(ssh, "run_remote", return_value=FakeProc(secretish, secretish)):
                result = ssh.gated_exec(
                    config, reason="os_plugin_filesystem_recovery", command_file=str(command),
                    authorization_file=str(auth), pre_readback_file=str(pre),
                    rollback_anchor_file=None, policy=POLICY,
                )
            self.assertNotIn(secretish, json.dumps(result))
            self.assertEqual(result["operation"], "ssh_admin_command")

    def test_image_and_ci_surface_include_ssh_fallback_contract(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text()
        smoke = (ROOT / "scripts" / "smoke_paseo_image.py").read_text()
        workflow = (ROOT / ".github" / "workflows" / "paseo-child-image.yml").read_text()
        self.assertIn("openssh-client", dockerfile)
        self.assertIn("ssh -V", smoke)
        self.assertIn("tests/test_unraid_host_control_guard_contract.py", workflow)
        self.assertIn(
            'git rev-parse 16e5a14f1f0357b8af40fa23602c6d6c1da24724:implementation/workstreams/feature-paseo-gui-runtime/results/M03-T01.md',
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
