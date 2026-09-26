#!/usr/bin/env python3
"""Disposable HOME preservation-evidence contract tests (M05-T03 CI repair).

The workflow must prove persistent HOME preservation without demanding
impossible byte/mtime stability of a live HOME: seeded state must survive
byte-identical (no wipe, no overwrite, no destructive restore) while
legitimate daemon additions are reported, not failed.
"""
from __future__ import annotations

import importlib.util
import builtins
import inspect
import io
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_staged_home_evidence.py"

spec = importlib.util.spec_from_file_location("paseo_staged_home_evidence", SCRIPT)
evidence = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(evidence)

TAG = "pi-unraid:paseo-test"
SECRET = "secret-bearing-keypair-bytes"
SESSIONS = json.dumps({"sessions": ["a", "b"]})


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_home(root: Path) -> Path:
    home = root / "home"
    (home / ".paseo").mkdir(parents=True)
    (home / ".paseo" / "config.json").write_text(json.dumps(
        {"daemon": {"relay": {"enabled": False}}, "worktrees": {"root": "/worktrees"}}))
    (home / ".paseo" / "daemon-keypair.json").write_text(SECRET)
    (home / "session-state.json").write_text(SESSIONS)
    return home


class FakeRuntime:
    """Simulated runtime-identity transport over a fixture HOME."""

    def __init__(self, home: Path):
        self.home = home
        self.calls: list[list[str]] = []

    def __call__(self, argv, env=None, timeout=120):
        self.calls.append(list(argv))
        if argv[:2] != ["docker", "run"]:
            return Completed(1, "", f"unexpected argv: {argv}")
        if "python3" in argv:
            payload = evidence.collect_home(self.home)
            return Completed(0, json.dumps(payload, sort_keys=True), "")
        if evidence.SENTINEL_NAME in argv[-1]:
            text = ""
            for token in argv:
                if token.startswith("STAGED_SENTINEL_TEXT="):
                    text = token.split("=", 1)[1]
            (self.home / evidence.SENTINEL_NAME).write_text(text)
            return Completed(0, "", "")
        return Completed(1, "", f"unexpected argv: {argv}")


def seed_args(home: Path, out: Path, sentinel_text="36254030414:abc123"):
    return type("Args", (), {
        "home_host": str(home), "tag": TAG, "uid": "99", "gid": "100",
        "sentinel_text": sentinel_text, "out": str(out)})()


def verify_args(home: Path, manifest: Path, report: Path):
    return type("Args", (), {
        "home_host": str(home), "tag": TAG, "uid": "99", "gid": "100",
        "manifest": str(manifest), "report": str(report)})()


def seed_manifest(td: Path, runtime: FakeRuntime) -> Path:
    home = runtime.home
    manifest = td / "seed-manifest.json"
    with mock.patch.object(sys, "stdout", io.StringIO()):
        rc = evidence.cmd_seed(seed_args(home, manifest), run_fn=runtime)
    assert rc == 0
    return manifest



class CollectTests(unittest.TestCase):
    def test_collect_inventories_bytes_as_hashes_and_relay_state(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(Path(td))
            got = evidence.collect_home(home)
            self.assertTrue(got["marker_present"])
            self.assertIs(got["relay_enabled"], False)
            self.assertIn(".paseo/config.json", got["entries"])
            self.assertIn(".paseo/daemon-keypair.json", got["entries"])
            self.assertIn("session-state.json", got["entries"])
            rendered = json.dumps(got, sort_keys=True)
            self.assertNotIn(SECRET, rendered)
            self.assertNotIn(SESSIONS, rendered)

    def test_embedded_collector_source_is_standalone_and_identical(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(Path(td))
            namespace: dict = {}
            exec(inspect.getsource(evidence.collect_home), namespace)  # noqa: S102
            self.assertEqual(namespace["collect_home"](home),
                             evidence.collect_home(home))
            source = evidence.collector_source()
            self.assertIn("def collect_home", source)
            self.assertIn("collect_home('/home/paseo')", source)

    def test_collect_uses_runtime_identity_and_read_only_mount(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(Path(td))
            runtime = FakeRuntime(home)
            evidence.collect_via_runtime(runtime, home, TAG, "99", "100")
            self.assertEqual(len(runtime.calls), 1)
            argv = runtime.calls[0]
            self.assertEqual(argv[:4], ["docker", "run", "--rm", "--user"])
            self.assertIn("99:100", argv)
            self.assertIn(f"{home}:/home/paseo:ro", argv)

    def test_unreadable_seeded_file_fails_collection(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(Path(td))
            real_open = builtins.open

            def deny_secret(path, *args, **kwargs):
                if str(path).endswith("daemon-keypair.json"):
                    raise PermissionError("secret unreadable")
                return real_open(path, *args, **kwargs)

            with mock.patch("builtins.open", side_effect=deny_secret):
                with self.assertRaises(PermissionError):
                    evidence.collect_home(home)

    def test_symlinks_are_inventoried_without_following_targets(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(Path(td))
            outside = Path(td) / "outside"
            outside.mkdir()
            (outside / "private").write_text(SECRET)
            (home / "linked-dir").symlink_to(outside, target_is_directory=True)
            (home / "linked-file").symlink_to(outside / "private")
            got = evidence.collect_home(home)
            self.assertEqual(got["entries"]["linked-dir"]["kind"], "symlink")
            self.assertEqual(got["entries"]["linked-file"]["kind"], "symlink")
            self.assertNotIn("linked-dir/private", got["entries"])
            self.assertNotIn(SECRET, json.dumps(got))


class CompareTests(unittest.TestCase):
    def manifest(self) -> dict:
        return {"schema_version": 1, "relay_enabled": False,
                "entries": {"a": {"size": 1, "sha256": "aa"},
                            ".paseo/config.json": {"size": 2, "sha256": "bb"}}}

    def current(self, **overrides) -> dict:
        data = {"relay_enabled": False, "marker_present": True,
                "entries": {"a": {"size": 1, "sha256": "aa"},
                            ".paseo/config.json": {"size": 2, "sha256": "bb"}}}
        data.update(overrides)
        return data

    def test_clean_state_is_ok(self):
        report = evidence.compare_manifest(self.manifest(), self.current())
        self.assertTrue(report["ok"])
        self.assertEqual(report["added"], [])

    def test_added_daemon_state_is_reported_not_failed(self):
        now = self.current()
        now["entries"]["daemon-heartbeat.json"] = {"size": 5, "sha256": "cc"}
        report = evidence.compare_manifest(self.manifest(), now)
        self.assertTrue(report["ok"])
        self.assertEqual(report["added"], ["daemon-heartbeat.json"])

    def test_removed_seeded_entry_fails(self):
        now = self.current()
        del now["entries"]["a"]
        report = evidence.compare_manifest(self.manifest(), now)
        self.assertFalse(report["ok"])
        self.assertEqual(report["missing"], ["a"])

    def test_altered_seeded_entry_fails_with_hashes_not_bytes(self):
        now = self.current()
        now["entries"]["a"] = {"size": 1, "sha256": "zz"}
        report = evidence.compare_manifest(self.manifest(), now)
        self.assertFalse(report["ok"])
        self.assertEqual(report["altered"], ["a"])
        self.assertEqual(report["altered_detail"]["a"],
                         {"expected": "aa", "observed": "zz"})

    def test_relay_flip_fails(self):
        report = evidence.compare_manifest(self.manifest(), self.current(relay_enabled=True))
        self.assertFalse(report["ok"])
        self.assertTrue(report["relay_changed"])

    def test_lost_marker_fails(self):
        now = self.current(marker_present=False)
        del now["entries"][".paseo/config.json"]
        report = evidence.compare_manifest(self.manifest(), now)
        self.assertFalse(report["ok"])


class SeedVerifyFlowTests(unittest.TestCase):
    def verify(self, td: Path, runtime: FakeRuntime, manifest: Path):
        report = Path(td) / f"report-{len(runtime.calls)}.json"
        stdout = io.StringIO()
        with mock.patch.object(sys, "stdout", stdout), \
                mock.patch.object(sys, "stderr", io.StringIO()):
            rc = evidence.cmd_verify(verify_args(runtime.home, manifest, report),
                                     run_fn=runtime)
        return rc, json.loads(report.read_text()), stdout.getvalue()

    def test_seed_verify_round_trip_with_sentinel(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            manifest = seed_manifest(td_path, runtime)
            data = json.loads(manifest.read_text())
            self.assertEqual(data["sentinel"], evidence.SENTINEL_NAME)
            self.assertIn(evidence.SENTINEL_NAME, data["entries"])
            self.assertIs(data["relay_enabled"], False)
            self.assertNotIn(SECRET, manifest.read_text())
            rc, report, _ = self.verify(td_path, runtime, manifest)
            self.assertEqual(rc, 0)
            self.assertTrue(report["ok"])

    def test_directory_mtime_noise_is_not_a_failure(self):
        # Regression for CI 36254030414: a transient create/delete cycle
        # retouches directory mtimes while the file set is identical.
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            manifest = seed_manifest(td_path, runtime)
            probe = runtime.home / ".pi-unraid-write-probe"
            probe.touch()
            probe.unlink()
            rc, report, _ = self.verify(td_path, runtime, manifest)
            self.assertEqual(rc, 0)
            self.assertTrue(report["ok"])
            self.assertEqual(report["added"], [])

    def test_added_runtime_state_passes_and_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            manifest = seed_manifest(td_path, runtime)
            (runtime.home / "browser-session.json").write_text('{"tabs": 1}')
            rc, report, _ = self.verify(td_path, runtime, manifest)
            self.assertEqual(rc, 0)
            self.assertTrue(report["ok"])
            self.assertEqual(report["added"], ["browser-session.json"])

    def test_destructive_restore_loses_the_sentinel_and_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            manifest = seed_manifest(td_path, runtime)
            (runtime.home / evidence.SENTINEL_NAME).unlink()
            rc, report, _ = self.verify(td_path, runtime, manifest)
            self.assertEqual(rc, 1)
            self.assertFalse(report["ok"])
            self.assertIn(evidence.SENTINEL_NAME, report["missing"])

    def test_wiped_relay_config_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            manifest = seed_manifest(td_path, runtime)
            (runtime.home / ".paseo" / "config.json").write_text(json.dumps(
                {"daemon": {"relay": {"enabled": True}}}))
            rc, report, _ = self.verify(td_path, runtime, manifest)
            self.assertEqual(rc, 1)
            self.assertFalse(report["ok"])
            self.assertIn(".paseo/config.json", report["altered"])
            self.assertTrue(report["relay_changed"])

    def test_seed_refuses_home_without_runtime_marker(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            home = td_path / "home"
            home.mkdir()
            runtime = FakeRuntime(home)
            with mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                rc = evidence.cmd_seed(
                    seed_args(home, td_path / "manifest.json"), run_fn=runtime)
            self.assertEqual(rc, 2)

    def test_seed_refuses_unsafe_sentinel_text(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            home = make_home(td_path)
            runtime = FakeRuntime(home)
            with mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                rc = evidence.cmd_seed(
                    seed_args(home, td_path / "manifest.json",
                              sentinel_text='x"; rm -rf / #'), run_fn=runtime)
            self.assertEqual(rc, 2)

    def test_verify_refuses_missing_or_foreign_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            with mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                rc = evidence.cmd_verify(
                    verify_args(runtime.home, td_path / "absent.json",
                                td_path / "report.json"), run_fn=runtime)
            self.assertEqual(rc, 2)

    def test_verify_refuses_manifest_bound_to_another_home(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            runtime = FakeRuntime(make_home(td_path))
            manifest = seed_manifest(td_path, runtime)
            data = json.loads(manifest.read_text())
            data["home"] = "/tmp/another-home"
            manifest.write_text(json.dumps(data))
            with mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                rc = evidence.cmd_verify(
                    verify_args(runtime.home, manifest, td_path / "report.json"),
                    run_fn=runtime)
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
