from __future__ import annotations

import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "scripts" / "unraid_graphql_host_control.py"
CREDENTIAL_PATH = ROOT / "scripts" / "configure_unraid_graphql_credential.py"
COMPOSE = (ROOT / "compose.yaml").read_text()
PROFILE = json.loads((ROOT / "config" / "unraid-host-control" / "permission-profile.json").read_text())

spec = importlib.util.spec_from_file_location("host_control", CLIENT_PATH)
host_control = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(host_control)


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class UnraidGraphqlHostControlContractTests(unittest.TestCase):
    def test_surface_is_bounded_and_has_no_ssh_or_docker_socket(self) -> None:
        source = CLIENT_PATH.read_text() + "\n" + CREDENTIAL_PATH.read_text()
        self.assertEqual(
            host_control.ALLOWED_ACTIONS,
            ("start", "stop", "restart", "pause", "unpause"),
        )
        for forbidden in (
            "/var/run/docker.sock",
            "subprocess",
            "paramiko",
            "ssh ",
            "reboot",
            "shutdown",
            "mkfs",
            "iptables",
            "nft ",
            "rm -rf",
        ):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("/var/run/docker.sock", COMPOSE)
        self.assertNotIn('source: "/"', COMPOSE)
        self.assertEqual(PROFILE["roles"], [])
        self.assertEqual(
            PROFILE["permissions"],
            [
                {"resource": "INFO", "actions": ["READ_ANY"]},
                {"resource": "DOCKER", "actions": ["READ_ANY", "UPDATE_ANY"]},
            ],
        )
        self.assertEqual(PROFILE["docker_mutations"], list(host_control.ALLOWED_ACTIONS))

    def test_api_key_file_must_be_private(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "key"
            path.write_text("a" * 64 + "\n")
            path.chmod(0o644)
            with self.assertRaises(host_control.HostControlError) as ctx:
                host_control.load_api_key(str(path))
            self.assertEqual(ctx.exception.kind, "credential")
            path.chmod(0o600)
            self.assertEqual(host_control.load_api_key(str(path)), "a" * 64)

    def test_graphql_uses_header_and_fails_closed_on_errors(self) -> None:
        ok = FakeResponse({"data": {"info": {"id": "info"}}})
        with mock.patch.object(host_control.urllib.request, "urlopen", return_value=ok) as call:
            data = host_control.graphql(
                "http://tower/graphql",
                "b" * 64,
                "query { info { id } }",
            )
        self.assertEqual(data["info"]["id"], "info")
        request = call.call_args.args[0]
        self.assertEqual(request.get_header("X-api-key"), "b" * 64)

        bad = FakeResponse({"errors": [{"message": "permission denied"}], "data": None})
        with mock.patch.object(host_control.urllib.request, "urlopen", return_value=bad):
            with self.assertRaises(host_control.HostControlError) as ctx:
                host_control.graphql(
                    "http://tower/graphql",
                    "b" * 64,
                    "query { info { id } }",
                )
        self.assertEqual(ctx.exception.kind, "graphql")


    def test_cli_fails_closed_with_machine_readable_missing_or_invalid_credential(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.key"
            for path, prepare in (
                (missing, None),
                (Path(td) / "invalid.key", "not-a-valid-key\n"),
            ):
                if prepare is not None:
                    path.write_text(prepare)
                    path.chmod(0o600)
                run = subprocess.run(
                    [
                        sys.executable,
                        str(CLIENT_PATH),
                        "--endpoint",
                        "http://tower/graphql",
                        "--api-key-file",
                        str(path),
                        "readback",
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(run.returncode, 0)
                payload = json.loads(run.stderr)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["error"], "credential")

    def test_only_allowlisted_mutations_can_be_built(self) -> None:
        for action in host_control.ALLOWED_ACTIONS:
            query = host_control.action_query(action)
            self.assertIn(f"{action}(id: $id)", query)
            self.assertNotIn("removeContainer", query)
            self.assertNotIn("updateAllContainers", query)
        with self.assertRaises(host_control.HostControlError):
            host_control.action_query("removeContainer")

    def test_credential_install_is_atomic_private_and_secret_safe(self) -> None:
        key = "c" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "unraid-api.key"
            run = subprocess.run(
                [
                    sys.executable,
                    str(CREDENTIAL_PATH),
                    "install",
                    "--path",
                    str(path),
                ],
                input=key + "\n",
                text=True,
                capture_output=True,
                check=True,
            )
            result = json.loads(run.stdout)
            self.assertTrue(result["changed"])
            self.assertNotIn(key, run.stdout + run.stderr)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(path.read_text().strip(), key)

            status = subprocess.run(
                [
                    sys.executable,
                    str(CREDENTIAL_PATH),
                    "status",
                    "--path",
                    str(path),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            payload = json.loads(status.stdout)
            self.assertTrue(payload["present"])
            self.assertTrue(payload["private_mode"])
            self.assertNotIn(key, status.stdout + status.stderr)

    def test_credential_target_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "real"
            target.write_text("d" * 64 + "\n")
            target.chmod(0o600)
            link = Path(td) / "link"
            link.symlink_to(target)
            run = subprocess.run(
                [
                    sys.executable,
                    str(CREDENTIAL_PATH),
                    "status",
                    "--path",
                    str(link),
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(run.returncode, 0)
            self.assertNotIn("d" * 64, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
