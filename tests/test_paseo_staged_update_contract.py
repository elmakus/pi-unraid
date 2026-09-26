#!/usr/bin/env python3
"""Reusable Paseo staged-update transaction contract tests (M05-T03)."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_staged_update.py"
MODULE_SOURCE = SCRIPT.read_text()

spec = importlib.util.spec_from_file_location("paseo_staged_update", SCRIPT)
staged = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(staged)

CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
CANDIDATE_ID = CANDIDATE["candidate_id"]
PI_VERSION = CANDIDATE["components"]["pi"]["version"]
NEW_TAG = f"pi-unraid:paseo-{CANDIDATE_ID.removeprefix('sha256:')[:12]}"
NEW_IMAGE_ID = "sha256:" + "ab" * 32
PRIOR_TAG = "pi-unraid:paseo-000000000001"
PRIOR_IMAGE_ID = "sha256:" + "01" * 32

RESULT_DIR = "implementation/workstreams/feature-paseo-gui-runtime/results"
DEPENDENCIES = (
    ("b7aa565649d14168e0d4b2d2d06044c08aac46a0", f"{RESULT_DIR}/M05-T02B.md",
     "7bdb9fffcbada5f0dc6475f3bb2b7be92d8e1d20"),
    ("40ad9529f7f3bb05a27caa306d21a3cdc83c5bcd", f"{RESULT_DIR}/M05-T01-R02.md",
     "7b3855238c59f35f2cd2af05a0d1456db34832db"),
    ("727b6f25a3b957551d10c9c24d9e9d1e26efd6ab", f"{RESULT_DIR}/M02-T01.md",
     "e5075d474bb7aaf0583baf66757add56fb556253"),
    ("e9a412557bfbe927a64b1f7ba0d892f5f059e08a", f"{RESULT_DIR}/M04-T02.md",
     "c6adc8514548b701c3aa959df9f5a6f4ff581a9d"),
)

EXPECTED_PHASE_ORDER = ["preflight", "build", "fast_checks", "temp_smoke",
                        "promote", "post_smoke", "rollback"]


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeDocker:
    """Scripted Docker/Compose surface for transaction orchestration tests."""

    def __init__(self, candidate_id=CANDIDATE_ID, pi_version=PI_VERSION):
        self.candidate_id = candidate_id
        self.pi_version = pi_version
        self.images = {
            PRIOR_TAG: {"id": PRIOR_IMAGE_ID, "label": candidate_id},
            NEW_TAG: {"id": NEW_IMAGE_ID, "label": candidate_id},
        }
        self.containers: dict[str, dict] = {}
        self.aliases: dict[str, str] = {}
        self.calls: list[list[str]] = []
        self.counter = 0

    def label_for(self, image_id):
        for entry in self.images.values():
            if entry["id"] == image_id:
                return entry["label"]
        return None

    def __call__(self, argv, env=None, timeout=120):
        self.calls.append(list(argv))
        if argv[:3] == ["docker", "image", "inspect"]:
            return self._image_inspect(argv[3])
        if argv[:2] == ["docker", "inspect"]:
            return self._container_inspect(argv[2])
        if argv[:2] == ["docker", "tag"]:
            return self._tag(argv[2], argv[3])
        if argv[:2] == ["docker", "exec"]:
            return self._exec(argv[2], argv[3:])
        if argv[:2] == ["docker", "run"]:
            return Completed(0, "", "")
        if argv[:2] == ["docker", "compose"]:
            return self._compose(argv)
        if argv[:1] == ["bash"]:
            return Completed(0, "", "")
        return Completed(1, "", f"unexpected argv: {argv}")

    def _image_inspect(self, tag):
        entry = self.images.get(tag)
        if entry is None:
            return Completed(1, "", f"no such image: {tag}")
        payload = [{"Id": entry["id"], "RepoDigests": [],
                    "Config": {"Labels": {"io.pi-unraid.candidate-id": entry["label"]}}}]
        return Completed(0, json.dumps(payload), "")

    def _container_inspect(self, cid):
        for project, container in self.containers.items():
            if container["id"] == cid or container["id"].startswith(cid):
                return Completed(0, json.dumps([{
                    "Id": container["id"], "Image": container["image"],
                    "State": {"Running": container["running"],
                              "Health": {"Status": "healthy"}}}]), "")
        return Completed(1, "", f"no such container: {cid}")

    def _tag(self, image_id, alias):
        self.aliases[alias] = image_id
        self.images[alias] = {"id": image_id, "label": self.label_for(image_id)}
        return Completed(0, "", "")

    def _exec(self, cid, rest):
        # Faithful to real `docker exec` resolution: a bare shell builtin such
        # as `command` is not an executable and must fail; probes must go
        # through `sh -c` instead.
        if rest and rest[0] == "command":
            return Completed(1, "", "exec: \"command\": executable file not found")
        if rest[:2] == ["printenv", "PI_UNRAID_CANDIDATE_ID"]:
            return Completed(0, self.candidate_id + "\n", "")
        if rest == ["sh", "-c", "command -v pi"]:
            return Completed(0, "/opt/pi/bin/pi\n", "")
        if rest[:2] == ["test", "-f"]:
            return Completed(0, "", "")
        if rest == ["pi", "--version"]:
            return Completed(0, f"pi {self.pi_version}\n", "")
        return Completed(1, "", f"unexpected exec: {rest}")

    def _compose(self, argv):
        try:
            project = argv[argv.index("-p") + 1]
        except (ValueError, IndexError):
            return Completed(1, "", "compose project missing")
        if "ps" in argv:
            container = self.containers.get(project)
            if container is None:
                return Completed(0, "", "")
            return Completed(0, container["id"] + "\n", "")
        if "up" in argv:
            tag = None
            files = [argv[i + 1] for i, token in enumerate(argv)
                     if token == "-f" and i + 1 < len(argv)]
            for item in reversed(files):
                text = Path(item).read_text() if Path(item).is_file() else ""
                for line in text.splitlines():
                    line = line.strip()
                    if line.startswith("image:"):
                        tag = line.split("image:", 1)[1].strip().strip('"')
                        break
                if tag is not None:
                    break
            if tag is None or tag not in self.images:
                return Completed(1, "", f"compose up has no known image: {tag}")
            self.counter += 1
            cid = f"{project}-cid-{self.counter:04d}"
            self.containers[project] = {"id": cid, "image": self.images[tag]["id"],
                                        "running": True}
            return Completed(0, "", "")
        if "down" in argv:
            self.containers.pop(project, None)
            return Completed(0, "", "")
        return Completed(1, "", f"unexpected compose argv: {argv}")


def make_home(root: Path) -> Path:
    home = root / "home"
    (home / ".paseo").mkdir(parents=True)
    (home / ".paseo" / "config.json").write_text(json.dumps(
        {"daemon": {"relay": {"enabled": False}}, "worktrees": {"root": "/worktrees"}}))
    (home / ".paseo" / "daemon-keypair.json").write_text("secret-bearing-fixture")
    (home / "session-state.json").write_text(json.dumps({"sessions": ["a", "b"]}))
    return home


def snapshot_tree(root: Path) -> dict:
    data = {}
    for item in sorted(root.rglob("*")):
        if item.is_file() and not item.is_symlink():
            data[item.relative_to(root).as_posix()] = item.read_bytes()
    return data


def write_anchor(path: Path, role: str, tag=PRIOR_TAG, image_id=PRIOR_IMAGE_ID,
                 project="pi-unraid-staged-active", home="/tmp/home") -> dict:
    anchor = {
        "schema_version": 1,
        "role": role,
        "candidate_id": CANDIDATE_ID,
        "image_tag": tag,
        "image_id": image_id,
        "runtime": {"compose_project": project, "service": "paseo",
                    "container_id": f"{project}-cid-seed"},
        "home": {"host_path": home},
        "pi_version": PI_VERSION,
        "recorded_at": "2026-09-26T00:00:00+00:00",
    }
    path.write_text(json.dumps(anchor))
    return anchor


def write_retention(path: Path, tags) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": 1, "max_entries": 3,
        "entries": [{"tag": tag, "image_id": "sha256:x", "candidate_id": CANDIDATE_ID,
                     "record": "/tmp/record.json", "protected_at": "t"} for tag in tags],
    }))


def update_args(td: Path, **overrides):
    values = {
        "scope": "disposable",
        "candidate": str(ROOT / "config" / "paseo-candidate.json"),
        "context": str(ROOT),
        "state_root": str(td / "state"),
        "tower_root": str(td / "tower"),
        "active_project": "pi-unraid-staged-active",
        "home_host": str(td / "home"),
        "projects_host": str(td / "projects"),
        "worktrees_host": str(td / "worktrees"),
        "uid": "99",
        "gid": "100",
        "wait_timeout": 5,
        "record": str(td / "record.json"),
        "builder": "pi-unraid-paseo",
        "buildx_state_dir": str(td / "buildx-state"),
        "cache_dir": None,
        "retain": 3,
        "build_timeout": 60,
        "smoke_timeout": 60,
    }
    values.update(overrides)
    return type("Args", (), values)()


def staged_env(td: Path, fake: FakeDocker, project="pi-unraid-staged-active"):
    home = make_home(td)
    (td / "projects").mkdir(exist_ok=True)
    (td / "worktrees").mkdir(exist_ok=True)
    state = td / "state"
    state.mkdir(parents=True, exist_ok=True)
    write_anchor(state / "active.json", "active", home=str(home), project=project)
    write_anchor(state / "rollback.json", "rollback", home=str(home), project=project)
    write_retention(td / "tower" / "retention.json", [PRIOR_TAG])
    staged.write_override(state / "active.override.yaml", PRIOR_TAG)
    fake.containers[project] = {"id": f"{project}-cid-seed", "image": PRIOR_IMAGE_ID,
                                "running": True}
    return home


@contextmanager
def build_mocks(fake_tag=NEW_TAG, fake_id=NEW_IMAGE_ID, build_rc=0):
    def fake_main(argv):
        record_path = Path(argv[argv.index("--record") + 1])
        record = {
            "schema_version": 1,
            "command": "build",
            "builder": {"name": "pi-unraid-paseo"},
            "candidate": {"path": "candidate.json", "candidate_id": CANDIDATE_ID},
            "context": str(ROOT),
            "tag": fake_tag,
            "image": {"id": fake_id, "digests": [], "candidate_label": CANDIDATE_ID},
            "phases": {"build": {"status": "ok", "duration_ms": 3, "detail": {}}},
        }
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record))
        return build_rc

    def fake_retain(profile, record_path, max_entries):
        record = json.loads(Path(record_path).read_text())
        retention_file = Path(profile["retention_file"])
        try:
            current = json.loads(retention_file.read_text())
        except OSError:
            current = {"schema_version": 1, "entries": []}
        entry = {"tag": record["tag"], "image_id": record["image"]["id"],
                 "candidate_id": CANDIDATE_ID}
        entries = [item for item in current.get("entries", [])
                   if item.get("tag") != entry["tag"]]
        entries.insert(0, entry)
        data = {"schema_version": 1, "max_entries": max_entries,
                "entries": entries[:max_entries]}
        retention_file.parent.mkdir(parents=True, exist_ok=True)
        retention_file.write_text(json.dumps(data))
        return data

    with mock.patch.object(staged.buildx, "main", side_effect=fake_main), \
         mock.patch.object(staged.tower, "retain_record", side_effect=fake_retain), \
         mock.patch.object(staged.buildx, "run_smoke_suite",
                           return_value={"smokes": [{"name": "s", "status": "ok"}]}):
        yield


class PredecessorBindingTests(unittest.TestCase):
    def test_exact_four_dependency_bindings(self):
        for commit, path, blob in DEPENDENCIES:
            pinned = subprocess.run(
                ["git", "rev-parse", f"{commit}:{path}"],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(pinned.returncode, 0, pinned.stderr)
            self.assertEqual(pinned.stdout.strip(), blob, path)
            working = subprocess.run(
                ["git", "hash-object", path], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(working.returncode, 0, working.stderr)
            self.assertEqual(working.stdout.strip(), blob, path)

    def test_current_p3_adr_requirements_authority_revalidated(self):
        plan = (ROOT / "planning" / "PASEO_GUI_RUNTIME_P3.md").read_text()
        self.assertIn("Status: frozen", plan)
        self.assertIn("M05-T03 Staged update/cutover/rollback", plan)
        for name in ("ADR_PGR_003_UNRAID_ADMIN_SAFETY.md", "ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md"):
            self.assertIn("Status: `accepted`", (ROOT / "decisions" / name).read_text())
        requirements = (ROOT / "requirements" / "PASEO_GUI_RUNTIME.md").read_text()
        self.assertIn("Revision: `R2`", requirements)
        self.assertIn("Status: `approved`", requirements)
        staged.resolver.validate(CANDIDATE)
        material = {k: v for k, v in CANDIDATE.items() if k != "candidate_id"}
        expected = "sha256:" + hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(CANDIDATE_ID, expected)


class ScopeGuardTests(unittest.TestCase):
    def test_only_disposable_scope_is_accepted(self):
        self.assertEqual(staged.check_scope("disposable"), "disposable")
        for scope in ("production", "", "DISPOSABLE", "tower"):
            with self.subTest(scope=scope), self.assertRaises(staged.StagedUpdateError):
                staged.check_scope(scope)

    def test_update_refuses_production_scope_before_any_work(self):
        with tempfile.TemporaryDirectory() as td:
            args = update_args(Path(td), scope="production")
            with mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertEqual(staged.cmd_update(args), 2)
            self.assertFalse((Path(td) / "record.json").exists())

    def test_disposable_project_namespace_is_enforced(self):
        ok = staged.check_disposable_project("pi-unraid-staged-active")
        self.assertEqual(ok, "pi-unraid-staged-active")
        for bad in ("pi-unraid", "paseo", "pi-unraid-staged", "", "other-project"):
            with self.subTest(bad=bad), self.assertRaises(staged.StagedUpdateError):
                staged.check_disposable_project(bad)

    def test_production_home_and_state_paths_are_refused(self):
        with self.assertRaises(staged.StagedUpdateError):
            staged.check_home_host(Path("/mnt/user/appdata/pi-unraid/paseo-home"))
        with self.assertRaises(staged.StagedUpdateError):
            staged.check_state_root(Path("/mnt/user/appdata/pi-unraid/deployment-state"))
        self.assertEqual(staged.check_home_host(Path("/tmp/disposable-home")),
                         Path("/tmp/disposable-home"))

    def test_no_floating_resolution_surface(self):
        lowered = MODULE_SOURCE.lower()
        for token in ("releases/latest", ":latest", "resolve_live", "urlopen",
                      "urllib", "registry.npmjs", "api.github.com"):
            self.assertNotIn(token, lowered, token)

    def test_no_legacy_lifecycle_substitution_surface(self):
        for token in ("update.sh", "pi-unraid-service", "pi-unraid-pi-1", "/home/pi",
                      "NODE_IMAGE", "NOPASSWD", "pi-unraid-entrypoint",
                      "groupmod --new-name pi", "usermod --login pi",
                      "node:24-bookworm-slim"):
            self.assertNotIn(token, MODULE_SOURCE, token)

    def test_update_reconcile_doctor_remain_distinct(self):
        lowered = MODULE_SOURCE.lower()
        for token in ("environment_capability_control", "environment_capability_inventory",
                      "reconcile", "doctor"):
            self.assertNotIn(token, lowered, token)
        parser = staged.build_parser()
        actions = [a for a in parser._actions
                   if isinstance(a, __import__("argparse").ArgumentParser)]
        self.assertEqual(actions, [])

    def test_no_registry_runner_or_push_surface(self):
        lowered = MODULE_SOURCE.lower()
        for token in ("docker login", "--push", "type=registry", "actions-runner",
                      "ghcr.io/elmakus"):
            self.assertNotIn(token, lowered, token)


class FrozenBindingTests(unittest.TestCase):
    def test_accepted_candidate_binds_the_build_context(self):
        readback = staged.verify_frozen_binding(
            CANDIDATE, (ROOT / "Dockerfile").read_text(), ROOT)
        self.assertEqual(readback["candidate_id"], CANDIDATE_ID)
        self.assertEqual(staged.buildx.image_tag(CANDIDATE_ID), NEW_TAG)

    def test_tampered_candidate_is_rejected(self):
        broken = json.loads(json.dumps(CANDIDATE))
        broken["components"]["pi"]["version"] = "0.0.0"
        with self.assertRaises(staged.StagedUpdateError):
            staged.verify_frozen_binding(
                broken, (ROOT / "Dockerfile").read_text(), ROOT)

    def test_candidate_id_mismatch_is_rejected(self):
        broken = json.loads(json.dumps(CANDIDATE))
        broken["candidate_id"] = "sha256:" + "00" * 32
        with self.assertRaises(staged.StagedUpdateError):
            staged.verify_frozen_binding(
                broken, (ROOT / "Dockerfile").read_text(), ROOT)

    def test_missing_candidate_file_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(staged.StagedUpdateError):
                staged.load_frozen_candidate(Path(td) / "absent.json")


class AnchorHomeTests(unittest.TestCase):
    def test_anchor_schema_validation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "active.json"
            write_anchor(path, "active")
            self.assertEqual(staged.load_anchor(path, "active")["role"], "active")
            with self.assertRaises(staged.StagedUpdateError):
                staged.load_anchor(Path(td) / "absent.json", "active")
            path.write_text(json.dumps({"schema_version": 99}))
            with self.assertRaises(staged.StagedUpdateError):
                staged.load_anchor(path, "active")
            write_anchor(path, "rollback")
            with self.assertRaises(staged.StagedUpdateError):
                staged.load_anchor(path, "active")

    def test_home_fingerprint_is_stable_and_content_free(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(Path(td))
            first = staged.fingerprint_home(home)
            second = staged.fingerprint_home(home)
            self.assertEqual(first, second)
            rendered = json.dumps(first)
            self.assertNotIn("secret-bearing-fixture", rendered)
            self.assertNotIn("sessions", rendered)
            (home / "new-session.json").write_text("{}")
            third = staged.fingerprint_home(home)
            self.assertNotEqual(first["digest"], third["digest"])

    def test_temp_tree_removal_refuses_foreign_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "state"
            root.mkdir()
            home = make_home(Path(td))
            with self.assertRaises(staged.StagedUpdateError):
                staged.remove_temp_tree(root, home)
            with self.assertRaises(staged.StagedUpdateError):
                staged.remove_temp_tree(root, root / "active.json")
            owned = root / "tmp-owned"
            owned.mkdir()
            staged.remove_temp_tree(root, owned)
            self.assertFalse(owned.exists())


class PreflightTests(unittest.TestCase):
    def config(self, td: Path, fake: FakeDocker, **overrides):
        home = staged_env(Path(td), fake)
        cfg = {
            "candidate_path": ROOT / "config" / "paseo-candidate.json",
            "context_dir": ROOT,
            "state_root": Path(td) / "state",
            "active_file": Path(td) / "state" / "active.json",
            "rollback_file": Path(td) / "state" / "rollback.json",
            "retention_file": Path(td) / "tower" / "retention.json",
            "active_project": "pi-unraid-staged-active",
            "home_host": home,
            "uid": "99",
            "gid": "100",
        }
        cfg.update(overrides)
        return cfg, home

    def test_preflight_accepts_coherent_anchors(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeDocker()
            cfg, _ = self.config(td, fake)
            detail = staged.phase_preflight(cfg, fake, {})
            self.assertEqual(detail["expected"]["candidate_id"], CANDIDATE_ID)
            self.assertEqual(detail["expected"]["image_tag"], NEW_TAG)
            self.assertTrue(detail["observed"]["home"]["writable"])
            self.assertEqual(detail["observed"]["retention"], {PRIOR_TAG: True})

    def test_home_marker_is_checked_through_runtime_not_host_path(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "home"
            home.mkdir()
            calls = []

            def marker_missing(argv, env=None, timeout=120):
                calls.append(list(argv))
                return Completed(1, "", "marker missing")

            with self.assertRaises(staged.StagedUpdateError):
                staged.check_home_live(marker_missing, home, NEW_TAG, "99", "100", {})
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][:2], ["docker", "run"])
            self.assertIn(f"{home}:/home/paseo:ro", calls[0])
            self.assertIn(f"test -f /home/paseo/{staged.HOME_MARKER}", calls[0])

    def test_preflight_rejects_live_image_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeDocker()
            cfg, _ = self.config(td, fake)
            fake.images[PRIOR_TAG] = {"id": "sha256:" + "ff" * 32,
                                      "label": CANDIDATE_ID}
            with self.assertRaises(staged.StagedUpdateError):
                staged.phase_preflight(cfg, fake, {})

    def test_preflight_rejects_stopped_prior_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeDocker()
            cfg, _ = self.config(td, fake)
            fake.containers["pi-unraid-staged-active"]["running"] = False
            with self.assertRaises(staged.StagedUpdateError):
                staged.phase_preflight(cfg, fake, {})

    def test_preflight_rejects_unprotected_rollback_anchors(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeDocker()
            cfg, _ = self.config(td, fake)
            write_retention(Path(td) / "tower" / "retention.json", ["pi-unraid:paseo-other"])
            with self.assertRaises(staged.StagedUpdateError):
                staged.phase_preflight(cfg, fake, {})

    def test_preflight_rejects_anchor_home_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeDocker()
            cfg, home = self.config(td, fake)
            write_anchor(cfg["active_file"], "active", home="/tmp/somewhere-else",
                         project=cfg["active_project"])
            with self.assertRaises(staged.StagedUpdateError):
                staged.phase_preflight(cfg, fake, {})

    def test_preflight_rejects_ambiguous_containers(self):
        with tempfile.TemporaryDirectory() as td:
            fake = FakeDocker()
            cfg, _ = self.config(td, fake)

            real = fake._compose

            def ambiguous(argv):
                if "ps" in argv:
                    return Completed(0, "aaa\nbbb\n", "")
                return real(argv)
            fake._compose = ambiguous
            with self.assertRaises(staged.StagedUpdateError):
                staged.phase_preflight(cfg, fake, {})


class ExecHygieneTests(unittest.TestCase):
    def test_pi_present_probe_runs_through_sh(self):
        fake = FakeDocker()
        cid = "probe-cid"
        fake.containers["probe-project"] = {"id": cid, "image": NEW_IMAGE_ID,
                                            "running": True}
        probes = staged.runtime_probes(
            fake, cid, NEW_IMAGE_ID, CANDIDATE_ID, PI_VERSION, {})
        self.assertIn("pi_present", [p["name"] for p in probes])
        exec_argv = [c for c in fake.calls if c[:2] == ["docker", "exec"]]
        self.assertTrue(exec_argv)
        for argv in exec_argv:
            self.assertNotEqual(argv[3], "command")
        self.assertIn(["docker", "exec", cid, "sh", "-c", "command -v pi"], exec_argv)

    def test_fake_rejects_bare_builtin_like_real_docker(self):
        fake = FakeDocker()
        proc = fake(["docker", "exec", "cid", "command", "-v", "pi"], {}, 60)
        self.assertNotEqual(proc.returncode, 0)

    def test_no_bare_builtin_exec_in_module_source(self):
        self.assertNotIn('"exec", container_id, "command"', MODULE_SOURCE)


class TransactionTests(unittest.TestCase):
    def run_update(self, td: Path, fake: FakeDocker, **overrides):
        home = staged_env(td, fake)
        before = snapshot_tree(home)
        args = update_args(td, **overrides)
        with build_mocks(), \
                mock.patch.object(staged, "_run", side_effect=fake), \
                mock.patch.object(sys, "stdout", io.StringIO()), \
                mock.patch.object(sys, "stderr", io.StringIO()):
            rc = staged.cmd_update(args)
        record = json.loads((td / "record.json").read_text())
        return rc, record, home, before

    def test_success_promotes_and_rotates_rollback_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            rc, record, home, before = self.run_update(td_path, fake)
            self.assertEqual(rc, 0)
            self.assertEqual(record["outcome"], "promoted")
            self.assertEqual(record["recovery"]["decision"], "promoted")
            self.assertEqual(record["phase_order"], EXPECTED_PHASE_ORDER)
            for name in EXPECTED_PHASE_ORDER:
                phase = record["phases"][name]
                self.assertIn(phase["status"], ("ok", "skipped"), name)
                self.assertIsInstance(phase["duration_ms"], int, name)
                if phase["status"] == "ok":
                    self.assertIn("expected", phase["detail"], name)
                    self.assertIn("observed", phase["detail"], name)
                else:
                    self.assertIn("reason", phase["detail"], name)
            self.assertEqual(record["phases"]["rollback"]["status"], "skipped")
            active = json.loads((td_path / "state" / "active.json").read_text())
            self.assertEqual(active["image_tag"], NEW_TAG)
            self.assertEqual(active["image_id"], NEW_IMAGE_ID)
            rollback = json.loads((td_path / "state" / "rollback.json").read_text())
            self.assertEqual(rollback["image_tag"], PRIOR_TAG)
            self.assertEqual(rollback["role"], "rollback")
            override = (td_path / "state" / "active.override.yaml").read_text()
            self.assertIn(NEW_TAG, override)
            self.assertEqual(fake.aliases.get(staged.STAGED_ALIAS), NEW_IMAGE_ID)
            retention = json.loads((td_path / "tower" / "retention.json").read_text())
            tags = {item["tag"] for item in retention["entries"]}
            self.assertTrue({PRIOR_TAG, NEW_TAG}.issubset(tags))
            self.assertEqual(snapshot_tree(home), before)
            self.assertEqual(
                [p for p in (td_path / "state").iterdir() if p.name.startswith("tmp-")], [])

    def test_failed_build_leaves_active_runtime_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            home = staged_env(td_path, fake)
            before = snapshot_tree(home)
            active_before = (td_path / "state" / "active.json").read_text()
            override_before = (td_path / "state" / "active.override.yaml").read_text()
            args = update_args(td_path)
            with build_mocks(build_rc=1), \
                    mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                rc = staged.cmd_update(args)
            self.assertEqual(rc, 1)
            record = json.loads((td_path / "record.json").read_text())
            self.assertEqual(record["outcome"], "failed")
            self.assertEqual(record["recovery"]["decision"], "no_mutation")
            self.assertEqual(record["recovery"]["trigger"], "build")
            self.assertEqual(record["phases"]["build"]["status"], "failed")
            for name in ("fast_checks", "temp_smoke", "promote", "post_smoke", "rollback"):
                self.assertEqual(record["phases"][name]["status"], "skipped", name)
            self.assertEqual((td_path / "state" / "active.json").read_text(), active_before)
            self.assertEqual(
                (td_path / "state" / "active.override.yaml").read_text(), override_before)
            self.assertEqual(snapshot_tree(home), before)
            self.assertNotIn(staged.STAGED_ALIAS, fake.aliases)

    def test_temp_smoke_failure_leaves_active_runtime_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            with mock.patch.dict(os.environ, {staged.FORCE_TEMP_SMOKE_FAIL_ENV: "1"}):
                rc, record, home, before = self.run_update(td_path, fake)
            self.assertEqual(rc, 1)
            self.assertEqual(record["outcome"], "failed")
            self.assertEqual(record["recovery"]["decision"], "no_mutation")
            self.assertEqual(record["recovery"]["trigger"], "temp_smoke")
            self.assertEqual(record["phases"]["temp_smoke"]["status"], "failed")
            active = json.loads((td_path / "state" / "active.json").read_text())
            self.assertEqual(active["image_tag"], PRIOR_TAG)
            self.assertEqual(snapshot_tree(home), before)
            self.assertNotIn(staged.STAGED_ALIAS, fake.aliases)

    def test_post_smoke_failure_restores_prior_coherent_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            with mock.patch.dict(os.environ, {staged.FORCE_POST_SMOKE_FAIL_ENV: "1"}):
                rc, record, home, before = self.run_update(td_path, fake)
            self.assertEqual(rc, 1)
            self.assertEqual(record["outcome"], "rolled_back")
            self.assertEqual(record["recovery"]["decision"], "rolled_back")
            self.assertEqual(record["recovery"]["trigger"], "post_smoke")
            self.assertEqual(record["phases"]["post_smoke"]["status"], "failed")
            self.assertEqual(record["phases"]["rollback"]["status"], "ok")
            active = json.loads((td_path / "state" / "active.json").read_text())
            self.assertEqual(active["image_tag"], PRIOR_TAG)
            self.assertEqual(active["image_id"], PRIOR_IMAGE_ID)
            override = (td_path / "state" / "active.override.yaml").read_text()
            self.assertIn(PRIOR_TAG, override)
            self.assertEqual(fake.aliases.get(staged.STAGED_ALIAS), PRIOR_IMAGE_ID)
            self.assertEqual(snapshot_tree(home), before)

    def test_ambiguous_rollback_fails_closed_without_restoration(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()

            def losing_call(argv, env=None, timeout=120):
                if argv[:2] == ["docker", "tag"] and argv[2] == NEW_IMAGE_ID:
                    fake.images.pop(PRIOR_TAG, None)
                return fake(argv, env, timeout)

            home = staged_env(td_path, fake)
            before = snapshot_tree(home)
            args = update_args(td_path)
            with build_mocks(), \
                    mock.patch.object(staged, "_run", side_effect=losing_call), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()), \
                    mock.patch.dict(os.environ, {staged.FORCE_POST_SMOKE_FAIL_ENV: "1"}):
                rc = staged.cmd_update(args)
            record = json.loads((td_path / "record.json").read_text())
            self.assertEqual(rc, 1)
            self.assertEqual(record["outcome"], "fail_closed")
            self.assertEqual(record["recovery"]["decision"], "fail_closed")
            self.assertIn("ambiguous", record["recovery"]["reason"])
            self.assertEqual(record["phases"]["rollback"]["status"], "skipped")
            active = json.loads((td_path / "state" / "active.json").read_text())
            self.assertEqual(active["image_tag"], NEW_TAG)
            self.assertEqual(snapshot_tree(home), before)

    def test_failed_rollback_fails_closed_with_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            home = staged_env(td_path, fake)
            args = update_args(td_path)
            with build_mocks(), \
                    mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()), \
                    mock.patch.dict(os.environ, {staged.FORCE_POST_SMOKE_FAIL_ENV: "1"}), \
                    mock.patch.object(staged, "phase_rollback",
                                      side_effect=staged.StagedUpdateError("recreate refused")):
                rc = staged.cmd_update(args)
            self.assertEqual(rc, 1)
            record = json.loads((td_path / "record.json").read_text())
            self.assertEqual(record["outcome"], "fail_closed")
            self.assertEqual(record["recovery"]["decision"], "fail_closed")
            self.assertEqual(record["phases"]["rollback"]["status"], "failed")

    def test_promotion_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            home = staged_env(td_path, fake)
            args = update_args(td_path)
            with build_mocks(), \
                    mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()), \
                    mock.patch.object(staged, "phase_promote",
                                      side_effect=staged.StagedUpdateError("cutover broke")):
                rc = staged.cmd_update(args)
            self.assertEqual(rc, 1)
            record = json.loads((td_path / "record.json").read_text())
            self.assertEqual(record["outcome"], "fail_closed")
            self.assertEqual(record["recovery"]["trigger"], "promote")

    def test_fast_checks_refuse_retention_loss(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            home = staged_env(td_path, fake)
            args = update_args(td_path)

            def dropping_retain(profile, record_path, max_entries):
                return {"schema_version": 1, "entries": []}

            with build_mocks(), \
                    mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()), \
                    mock.patch.object(staged.tower, "retain_record",
                                      side_effect=dropping_retain):
                rc = staged.cmd_update(args)
            self.assertEqual(rc, 1)
            record = json.loads((td_path / "record.json").read_text())
            self.assertEqual(record["phases"]["fast_checks"]["status"], "failed")
            self.assertEqual(record["recovery"]["decision"], "no_mutation")


class RecoveryMatrixTests(unittest.TestCase):
    def matrix_config(self, td: Path, fake: FakeDocker):
        home = staged_env(td, fake)
        return {
            "rollback_file": td / "state" / "rollback.json",
            "retention_file": td / "tower" / "retention.json",
            "home_host": home,
            "home_fingerprint": staged.fingerprint_home(home),
        }

    def test_unambiguous_when_prior_coherent(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            cfg = self.matrix_config(td_path, fake)
            safe, reason = staged.rollback_unambiguous(cfg, fake, {})
            self.assertTrue(safe, reason)

    def test_ambiguous_when_prior_image_missing(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            del fake.images[PRIOR_TAG]
            cfg = self.matrix_config(td_path, fake)
            safe, reason = staged.rollback_unambiguous(cfg, fake, {})
            self.assertFalse(safe)
            self.assertIn("not available", reason)

    def test_ambiguous_when_prior_label_mismatches(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            fake.images[PRIOR_TAG] = {"id": PRIOR_IMAGE_ID, "label": "sha256:" + "ee" * 32}
            cfg = self.matrix_config(td_path, fake)
            safe, _ = staged.rollback_unambiguous(cfg, fake, {})
            self.assertFalse(safe)

    def test_ambiguous_when_home_changed(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            cfg = self.matrix_config(td_path, fake)
            (cfg["home_host"] / "drift.json").write_text("{}")
            safe, reason = staged.rollback_unambiguous(cfg, fake, {})
            self.assertFalse(safe)
            self.assertIn("HOME", reason)

    def test_ambiguous_when_retention_lost(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            cfg = self.matrix_config(td_path, fake)
            write_retention(td_path / "tower" / "retention.json", [NEW_TAG])
            safe, reason = staged.rollback_unambiguous(cfg, fake, {})
            self.assertFalse(safe)
            self.assertIn("retention", reason)


class InitReadbackTests(unittest.TestCase):
    def init_args(self, td: Path, **overrides):
        values = {
            "scope": "disposable",
            "candidate": str(ROOT / "config" / "paseo-candidate.json"),
            "context": str(ROOT),
            "state_root": str(td / "state"),
            "tower_root": str(td / "tower"),
            "active_project": "pi-unraid-staged-active",
            "home_host": str(td / "home"),
            "projects_host": str(td / "projects"),
            "worktrees_host": str(td / "worktrees"),
            "uid": "99",
            "gid": "100",
            "wait_timeout": 5,
            "force": False,
        }
        values.update(overrides)
        return type("Args", (), values)()

    def test_init_seeds_anchors_from_verified_live_state(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            home = make_home(td_path)
            (td_path / "projects").mkdir(exist_ok=True)
            (td_path / "worktrees").mkdir(exist_ok=True)
            write_retention(td_path / "tower" / "retention.json", [NEW_TAG])
            with mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()):
                rc = staged.cmd_init(self.init_args(td_path))
            self.assertEqual(rc, 0)
            active = json.loads((td_path / "state" / "active.json").read_text())
            rollback = json.loads((td_path / "state" / "rollback.json").read_text())
            self.assertEqual(active["image_tag"], NEW_TAG)
            self.assertEqual(active["image_id"], NEW_IMAGE_ID)
            self.assertTrue(rollback.get("seed"))
            self.assertIn(NEW_TAG, (td_path / "state" / "active.override.yaml").read_text())

    def test_init_refuses_existing_anchors_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            staged_env(td_path, fake)
            with mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertEqual(staged.cmd_init(self.init_args(td_path)), 2)

    def test_init_refuses_unprotected_seed_image(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            make_home(td_path)
            (td_path / "projects").mkdir(exist_ok=True)
            (td_path / "worktrees").mkdir(exist_ok=True)
            write_retention(td_path / "tower" / "retention.json", [PRIOR_TAG])
            with mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertEqual(staged.cmd_init(self.init_args(td_path)), 1)

    def test_readback_is_idempotent_and_coherent(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            staged_env(td_path, fake)
            outputs = []
            for _ in range(2):
                with mock.patch.object(staged, "_run", side_effect=fake), \
                        mock.patch.object(sys, "stdout", io.StringIO()) as out:
                    rc = staged.cmd_readback(self.init_args(td_path))
                self.assertEqual(rc, 0)
                outputs.append(out.getvalue())
            self.assertEqual(outputs[0], outputs[1])
            payload = json.loads(outputs[0])
            self.assertTrue(payload["coherent"])
            self.assertEqual(payload["mismatches"], [])

    def test_readback_reports_incoherence_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            staged_env(td_path, fake)
            fake.containers["pi-unraid-staged-active"]["running"] = False
            before = (td_path / "state" / "active.json").read_text()
            with mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()) as out:
                rc = staged.cmd_readback(self.init_args(td_path))
            self.assertEqual(rc, 1)
            payload = json.loads(out.getvalue())
            self.assertFalse(payload["coherent"])
            self.assertTrue(payload["mismatches"])
            self.assertEqual((td_path / "state" / "active.json").read_text(), before)


class HomePreservationTests(unittest.TestCase):
    def test_no_destructive_home_path_in_module(self):
        self.assertNotIn("restore_home", MODULE_SOURCE)
        for line in MODULE_SOURCE.splitlines():
            stripped = line.strip()
            if stripped.startswith(("#", "import ", "from ")):
                continue
            self.assertNotIn("rmtree(home", line)
            self.assertNotIn("rmtree(cfg[\"home_host\"])", line)

    def test_home_bytes_identical_across_promote_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            fake = FakeDocker()
            home = staged_env(td_path, fake)
            before = snapshot_tree(home)
            args = update_args(td_path)
            with build_mocks(), \
                    mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertEqual(staged.cmd_update(args), 0)
            mid = snapshot_tree(home)
            self.assertEqual(mid, before)
            args2 = update_args(td_path, record=str(td_path / "record2.json"))
            with build_mocks(), \
                    mock.patch.object(staged, "_run", side_effect=fake), \
                    mock.patch.object(sys, "stdout", io.StringIO()), \
                    mock.patch.object(sys, "stderr", io.StringIO()), \
                    mock.patch.dict(os.environ, {staged.FORCE_POST_SMOKE_FAIL_ENV: "1"}):
                self.assertEqual(staged.cmd_update(args2), 1)
            self.assertEqual(snapshot_tree(home), before)


if __name__ == "__main__":
    unittest.main()
