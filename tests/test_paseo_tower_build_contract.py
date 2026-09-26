import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_tower_build.py"
spec = importlib.util.spec_from_file_location("paseo_tower_build", SCRIPT)
tower = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tower)
SOURCE = SCRIPT.read_text()


def completed(rc=0, out="", err=""):
    return subprocess.CompletedProcess([], rc, out, err)


class ProfileTests(unittest.TestCase):
    def test_profile_is_bounded_and_isolated(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = Path(td) / "appdata" / "pi-unraid"
            root = boundary / "buildx"
            profile = tower.resolve_profile(root, boundary, "pi-unraid-paseo")
            self.assertEqual(profile["builder"], "pi-unraid-paseo")
            self.assertEqual(profile["state_dir"], root / "docker-config")
            self.assertEqual(profile["cache_dir"], root / "cache")
            self.assertEqual(profile["retention_file"], root / "retention.json")
            with self.assertRaises(tower.TowerBuildError):
                tower.resolve_profile(Path(td) / "outside", boundary, "pi-unraid-paseo")
            with self.assertRaises(tower.TowerBuildError):
                tower.resolve_profile(boundary, boundary, "pi-unraid-paseo")

    def test_prepare_uses_persistent_profile_and_bootstraps_builder(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = Path(td) / "appdata" / "pi-unraid"
            profile = tower.resolve_profile(boundary / "buildx", boundary, "pi-unraid-paseo")
            calls = []

            def runner(argv, env=None, timeout=120):
                calls.append(argv)
                if argv[:2] == ["docker", "inspect"]:
                    return completed(0, '[{"Mounts":[{"Type":"volume","Name":"state"}]}]')
                return completed(0, "ok")

            with mock.patch.object(
                tower.buildx, "ensure_builder",
                return_value={"name": "pi-unraid-paseo", "driver": "docker-container", "reused": False}
            ), mock.patch.object(tower, "_run", side_effect=runner):
                data = tower.prepare_profile(profile)
            self.assertTrue(Path(profile["state_dir"]).is_dir())
            self.assertTrue(Path(profile["cache_dir"]).is_dir())
            self.assertIn(
                ["docker", "buildx", "inspect", "--bootstrap", "pi-unraid-paseo"], calls
            )
            self.assertEqual(data["buildkit_mounts"][0]["Name"], "state")
            self.assertTrue(Path(profile["readback_file"]).is_file())


class RetentionTests(unittest.TestCase):
    def make_record(self, path, idx=1, build="ok", test="ok"):
        candidate = "sha256:" + f"{idx:012x}" + "0" * 52
        record = {
            "schema_version": 1,
            "command": "build",
            "builder": {"name": "pi-unraid-paseo"},
            "candidate": {"path": "candidate.json", "candidate_id": candidate},
            "context": str(ROOT),
            "tag": f"pi-unraid:paseo-{candidate[7:19]}",
            "image": {"id": "sha256:" + f"{100 + idx:064x}"[-64:], "digests": [],
                      "candidate_label": candidate},
            "phases": {
                "build": {"status": build, "duration_ms": 1, "detail": {}},
                "test": {"status": test, "duration_ms": 1, "detail": {}},
                "prune": {"status": "skipped", "duration_ms": 0, "detail": {}},
            },
        }
        path.write_text(json.dumps(record))
        return record

    def test_retain_requires_successful_build_and_test(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            profile = tower.resolve_profile(td / "buildx", td, "pi-unraid-paseo")
            bad = td / "bad.json"
            self.make_record(bad, build="failed")
            with self.assertRaises(tower.TowerBuildError):
                tower.retain_record(profile, bad, 3)
            bad2 = td / "bad2.json"
            self.make_record(bad2, test="failed")
            with self.assertRaises(tower.TowerBuildError):
                tower.retain_record(profile, bad2, 3)

    def test_retention_is_bounded_deduplicated_and_atomic(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            profile = tower.resolve_profile(td / "buildx", td, "pi-unraid-paseo")
            with mock.patch.object(tower, "inspect_record_image", return_value={}):
                for idx in (1, 2, 3, 4):
                    path = td / f"r{idx}.json"
                    self.make_record(path, idx=idx)
                    data = tower.retain_record(profile, path, 3)
            self.assertEqual(len(data["entries"]), 3)
            self.assertTrue(data["entries"][0]["tag"].endswith("000000000004"))
            self.assertFalse(any(e["tag"].endswith("000000000001") for e in data["entries"]))
            again = td / "again.json"
            self.make_record(again, idx=4)
            with mock.patch.object(tower, "inspect_record_image", return_value={}):
                data = tower.retain_record(profile, again, 3)
            self.assertEqual(len(data["entries"]), 3)

    def test_image_cleanup_removes_only_unprotected_managed_tags(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            profile = tower.resolve_profile(td / "buildx", td, "pi-unraid-paseo")
            Path(profile["root"]).mkdir(parents=True)
            tower.atomic_json(Path(profile["retention_file"]), {
                "schema_version": 1,
                "max_entries": 3,
                "entries": [{"tag": "pi-unraid:paseo-protected", "image_id": "sha256:1"}],
            })
            calls = []
            with mock.patch.object(
                tower, "managed_image_tags",
                return_value=["pi-unraid:paseo-old", "pi-unraid:paseo-protected"]
            ), mock.patch.object(
                tower, "_run",
                side_effect=lambda argv, env=None, timeout=120: (calls.append(argv), completed())[1]
            ):
                result = tower.prune_unprotected_images(profile)
            self.assertEqual(result["removed"], ["pi-unraid:paseo-old"])
            self.assertEqual(result["skipped"], ["pi-unraid:paseo-protected"])
            self.assertEqual(calls, [["docker", "image", "rm", "pi-unraid:paseo-old"]])


class BuildFlowTests(unittest.TestCase):
    def profile(self, td):
        return tower.resolve_profile(Path(td) / "appdata" / "buildx", Path(td), "pi-unraid-paseo")

    def args(self, td):
        return type("Args", (), {
            "record": str(Path(td) / "record.json"),
            "candidate": str(tower.buildx.DEFAULT_CANDIDATE),
            "context": str(ROOT),
            "keep_storage": "8GB",
            "with_prune": False,
            "build_label": [],
            "retain": 3,
            "prune_images": False,
        })()

    def test_failed_build_never_reaches_retention_or_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            profile = self.profile(td)
            with mock.patch.object(tower, "prepare_profile", return_value={}),                  mock.patch.object(tower.buildx, "main", return_value=1),                  mock.patch.object(tower, "retain_record") as retain,                  mock.patch.object(tower, "prune_unprotected_images") as cleanup:
                self.assertEqual(tower.cmd_build(self.args(td), profile), 1)
            retain.assert_not_called()
            cleanup.assert_not_called()

    def test_successful_build_retains_before_optional_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            profile = self.profile(td)
            order = []
            args = self.args(td)
            args.prune_images = True
            with mock.patch.object(tower, "prepare_profile", side_effect=lambda p: order.append("prepare")),                  mock.patch.object(tower.buildx, "main", side_effect=lambda a: order.append("build") or 0),                  mock.patch.object(tower, "retain_record", side_effect=lambda *a: order.append("retain") or {}),                  mock.patch.object(tower, "prune_unprotected_images", side_effect=lambda p: order.append("cleanup") or {}),                  mock.patch.object(tower, "readback", side_effect=lambda p: order.append("readback") or {}):
                self.assertEqual(tower.cmd_build(args, profile), 0)
            self.assertEqual(order, ["prepare", "build", "retain", "cleanup", "readback"])


class ScopeGuardTests(unittest.TestCase):
    def test_no_registry_runner_or_floating_resolution_surface(self):
        lowered = SOURCE.lower()
        for token in ("docker login", "--push", "type=registry", "actions-runner",
                      "ghcr.io/elmakus", "releases/latest"):
            self.assertNotIn(token, lowered, token)


if __name__ == "__main__":
    unittest.main()
