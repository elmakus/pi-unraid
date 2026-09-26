#!/usr/bin/env python3
"""Local Buildx/BuildKit foundation contract tests (M05-T02A)."""
from __future__ import annotations

import hashlib
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
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

SCRIPT = ROOT / "scripts" / "paseo_buildx.py"
DOCKERFILE = (ROOT / "Dockerfile").read_text()
CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
MODULE_SOURCE = SCRIPT.read_text()

spec = importlib.util.spec_from_file_location("paseo_buildx", SCRIPT)
buildx = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(buildx)

M05_T01_COMMIT = "40ad9529f7f3bb05a27caa306d21a3cdc83c5bcd"
M05_T01_BLOB = "7b3855238c59f35f2cd2af05a0d1456db34832db"
M01_T03_COMMIT = "bbc862c37c0da81a08a91876499cfe865be958ab"
M01_T03_BLOB = "3772f647f5a0c55e856d3ae8e3feb05c6fb3e1f5"

RESULT_M05 = "implementation/workstreams/feature-paseo-gui-runtime/results/M05-T01-R02.md"
RESULT_M01 = "implementation/workstreams/feature-paseo-gui-runtime/results/M01-T03.md"


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class PredecessorBindingTests(unittest.TestCase):
    def test_exact_m05_t01_r02_and_m01_t03_bindings(self):
        for commit, path, blob in (
            (M05_T01_COMMIT, RESULT_M05, M05_T01_BLOB),
            (M01_T03_COMMIT, RESULT_M01, M01_T03_BLOB),
        ):
            pinned = subprocess.run(
                ["git", "rev-parse", f"{commit}:{path}"],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(pinned.returncode, 0, pinned.stderr)
            self.assertEqual(pinned.stdout.strip(), blob, path)
            working = subprocess.run(
                ["git", "hash-object", path], cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(working.returncode, 0, working.stderr)
            self.assertEqual(working.stdout.strip(), blob, path)

    def test_frozen_candidate_and_provenance_revalidated(self):
        rspec = importlib.util.spec_from_file_location(
            "m05t02a_resolver", ROOT / "scripts" / "resolve-paseo-candidate.py")
        resolver = importlib.util.module_from_spec(rspec)
        assert rspec.loader is not None
        rspec.loader.exec_module(resolver)
        candidate = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
        resolver.validate(candidate)
        tmp = json.loads(json.dumps(candidate))
        claimed = tmp.pop("candidate_id")
        expected = "sha256:" + hashlib.sha256(
            json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(claimed, expected)
        self.assertEqual(claimed, CANDIDATE["candidate_id"])
        paseo = CANDIDATE["components"]["paseo"]
        self.assertIn(f"FROM {paseo['artifact']['reference']}", DOCKERFILE)
        self.assertIn(f'io.pi-unraid.candidate-id="{claimed}"', DOCKERFILE)


class NamespaceTests(unittest.TestCase):
    def test_dedicated_namespace_separate_from_workstation_and_runtime(self):
        name = buildx.BUILDER_NAME_DEFAULT
        self.assertEqual(name, "pi-unraid-paseo")
        self.assertNotEqual(name, buildx.RUNTIME_SERVICE_NAME)
        self.assertNotIn("workstation", name.lower())
        self.assertNotIn(name, (ROOT / "compose.yaml").read_text())
        self.assertNotIn("chatgpt-ce-workstation", MODULE_SOURCE)
        self.assertNotIn("/home/paseo", MODULE_SOURCE)
        self.assertNotIn("/mnt/user", MODULE_SOURCE)

    def test_persistent_state_location_is_configurable(self):
        self.assertEqual(buildx.ENV_STATE_DIR, "PI_UNRAID_BUILDX_STATE_DIR")
        self.assertTrue(str(buildx.STATE_DIR_DEFAULT).endswith(".local/share/pi-unraid/buildx"))
        env = buildx.docker_env(Path("/tmp/example-state"))
        self.assertEqual(env["DOCKER_CONFIG"], "/tmp/example-state")

    def test_builder_is_created_or_reused_without_mutating_default(self):
        calls: list[list[str]] = []

        def reused(argv, env, timeout):
            calls.append(argv)
            return Completed(0, "Name: pi-unraid-paseo\nDriver: docker-container\n")

        info = buildx.ensure_builder(reused, "pi-unraid-paseo", Path(tempfile.mkdtemp()), {})
        self.assertTrue(info["reused"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:3], ["docker", "buildx", "inspect"])

        calls.clear()

        def missing(argv, env, timeout):
            calls.append(argv)
            if argv[2] == "inspect":
                return Completed(1, "", "not found")
            return Completed(0, "pi-unraid-paseo\n")

        with tempfile.TemporaryDirectory() as td:
            info = buildx.ensure_builder(missing, "pi-unraid-paseo", Path(td), {})
        self.assertFalse(info["reused"])
        self.assertEqual(info["driver"], "docker-container")
        create = calls[1]
        self.assertEqual(create[:3], ["docker", "buildx", "create"])
        self.assertIn("pi-unraid-paseo", create)
        self.assertIn("docker-container", create)
        for argv in calls:
            self.assertNotIn("use", argv)

    def test_runtime_and_workstation_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            for bad in ("paseo", "workstation-build", "WorkStation-x", ""):
                with self.assertRaises(buildx.BuildxError, msg=bad):
                    buildx.ensure_builder(lambda a, e, t: Completed(0), bad, Path(td), {})


class IdentityTests(unittest.TestCase):
    def test_immutable_tag_derives_only_from_candidate(self):
        first = buildx.image_tag(CANDIDATE["candidate_id"])
        second = buildx.image_tag(CANDIDATE["candidate_id"])
        self.assertEqual(first, second)
        self.assertRegex(first, r"^pi-unraid:paseo-[0-9a-f]{12}$")
        other = buildx.image_tag("sha256:" + "0" * 64)
        self.assertNotEqual(first, other)
        for bad in ("", "latest", "sha256:zzz", "v1.2.3"):
            with self.assertRaises(buildx.BuildxError, msg=bad):
                buildx.image_tag(bad)


class FailClosedTests(unittest.TestCase):
    def write_candidate(self, td: Path, mutate=None) -> Path:
        data = json.loads(json.dumps(CANDIDATE))
        if mutate:
            mutate(data)
        path = td / "candidate.json"
        path.write_text(json.dumps(data))
        return path

    def test_mismatched_candidate_fails_before_any_docker_call(self):
        seen: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            bad = self.write_candidate(tdp, lambda c: c["components"].__setitem__(
                "pi", {**c["components"]["pi"], "version": "0.99.0"}))
            with self.assertRaises(buildx.BuildxError):
                buildx.verify_build_inputs(json.loads(bad.read_text()), DOCKERFILE, ROOT)
            tampered = self.write_candidate(tdp, lambda c: c.update(candidate_id="sha256:" + "1" * 64))
            with self.assertRaises(buildx.BuildxError):
                buildx.verify_build_inputs(json.loads(tampered.read_text()), DOCKERFILE, ROOT)
            self.assertEqual(seen, [])

    def test_missing_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            with self.assertRaises(buildx.BuildxError):
                buildx.load_candidate(tdp / "absent.json")
            (tdp / "Dockerfile").write_text("FROM scratch\n")
            with self.assertRaises(buildx.BuildxError):
                buildx.verify_build_inputs(CANDIDATE, "FROM scratch\n", tdp)
            with self.assertRaises(buildx.BuildxError):
                buildx.verify_build_inputs(CANDIDATE, DOCKERFILE, tdp / "absent-context")

    def test_build_failure_never_reaches_prune(self):
        calls: list[list[str]] = []

        def runner(argv, env, timeout):
            calls.append(argv)
            if argv[2] == "inspect":
                return Completed(0, "ok")
            if argv[2] == "build":
                return Completed(1, "", "boom")
            return Completed(0, "")

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            parser = buildx.build_parser()
            args = parser.parse_args([
                "build", "--candidate", str(ROOT / "config" / "paseo-candidate.json"),
                "--context", str(ROOT), "--record", str(tdp / "record.json"),
                "--state-dir", str(tdp / "state"), "--with-smoke", "--with-prune",
            ])
            with mock.patch.object(buildx, "_run", side_effect=runner):
                rc = buildx.cmd_build(args)
            self.assertEqual(rc, buildx.EXIT_BUILD)
            self.assertTrue(any(c[2] == "build" for c in calls))
            self.assertFalse(any(c[2] == "prune" for c in calls))
            record = json.loads((tdp / "record.json").read_text())
            self.assertEqual(record["phases"]["build"]["status"], "failed")
            self.assertEqual(record["phases"]["prune"]["status"], "skipped")

    def test_accepted_candidate_is_never_mutated(self):
        accepted = ROOT / "config" / "paseo-candidate.json"
        before = hashlib.sha256(accepted.read_bytes()).hexdigest()

        def runner(argv, env, timeout):
            if argv[:3] == ["docker", "buildx", "inspect"]:
                return Completed(0, "ok")
            if argv[:3] == ["docker", "buildx", "build"]:
                return Completed(0, "done")
            if argv[:3] == ["docker", "image", "inspect"]:
                return Completed(0, json.dumps([{
                    "Id": "sha256:" + "a" * 64,
                    "RepoDigests": [],
                    "Config": {"Labels": {
                        "io.pi-unraid.candidate-id": CANDIDATE["candidate_id"]}},
                }]))
            return Completed(0, "")

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            parser = buildx.build_parser()
            args = parser.parse_args([
                "build", "--context", str(ROOT), "--record", str(tdp / "record.json"),
                "--state-dir", str(tdp / "state"),
            ])
            with mock.patch.object(buildx, "_run", side_effect=runner):
                rc = buildx.cmd_build(args)
        self.assertEqual(rc, 0)
        self.assertEqual(hashlib.sha256(accepted.read_bytes()).hexdigest(), before)


class TimingsAndPruneTests(unittest.TestCase):
    WARM_PROGRESS = (
        "#1 [internal] load build definition from Dockerfile\n"
        "#1 DONE 0.0s\n"
        "#2 [internal] load metadata for ghcr.io/getpaseo/paseo\n"
        "#2 DONE 0.0s\n"
        "#3 [1/8] FROM ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136\n"
        "#3 CACHED\n"
        "#4 [2/8] RUN set -eux; apt-get update; apt-get install -y --no-install-recommends build-essential\n"
        "#4 CACHED\n"
        "#5 [3/8] RUN set -eux; npm install -g --ignore-scripts playwright@1.63.0\n"
        "#5 CACHED\n"
        "#6 [4/8] RUN set -eux; npm install -g --ignore-scripts @earendil-works/pi-coding-agent@0.87.1\n"
        "#6 CACHED\n"
        "#7 [5/8] RUN set -eux; curl -fsSL https://github.com/cli/cli/releases/download/v2.101.0/gh.tar.gz\n"
        "#7 CACHED\n"
        "#8 [6/8] RUN set -eux; curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-29.8.1.tgz\n"
        "#8 CACHED\n"
        "#9 [7/8] RUN set -eux; curl -fsSL https://github.com/docker/compose/releases/download/v5.5.1/docker-compose\n"
        "#9 CACHED\n"
        "#10 [8/8] WORKDIR /workspace\n"
        "#10 CACHED\n"
        "#11 exporting to image\n"
        "#11 DONE 0.4s\n"
    )

    def run_mock_build(self, extra_args, build_stdout="done", build_stderr=""):
        calls: list[list[str]] = []

        def runner(argv, env, timeout):
            calls.append(argv)
            if argv[:3] == ["docker", "buildx", "inspect"]:
                return Completed(0, "ok")
            if argv[:3] == ["docker", "buildx", "build"]:
                return Completed(0, build_stdout, build_stderr)
            if argv[:3] == ["docker", "image", "inspect"]:
                return Completed(0, json.dumps([{
                    "Id": "sha256:" + "b" * 64,
                    "RepoDigests": ["pi-unraid@sha256:" + "c" * 64],
                    "Config": {"Labels": {
                        "io.pi-unraid.candidate-id": CANDIDATE["candidate_id"]}},
                }]))
            if argv[:3] == ["docker", "buildx", "prune"]:
                return Completed(0, "Total: 1GB")
            return Completed(0, "")

        td = tempfile.TemporaryDirectory()
        tdp = Path(td.name)
        parser = buildx.build_parser()
        args = parser.parse_args([
            "build", "--context", str(ROOT), "--record", str(tdp / "record.json"),
            "--state-dir", str(tdp / "state"), *extra_args,
        ])
        with mock.patch.object(buildx, "_run", side_effect=runner):
            rc = buildx.cmd_build(args)
        record = json.loads((tdp / "record.json").read_text())
        td.cleanup()
        return rc, record, calls

    def test_phase_timings_are_machine_readable(self):
        rc, record, _ = self.run_mock_build([])
        self.assertEqual(rc, 0)
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(
            set(record["phases"]),
            {"resolution_readback", "builder_ensure", "build", "test", "prune"},
        )
        for name, phase in record["phases"].items():
            self.assertIn(phase["status"], ("ok", "skipped", "failed"), name)
            self.assertIsInstance(phase["duration_ms"], int, name)
            self.assertGreaterEqual(phase["duration_ms"], 0, name)
            self.assertIsInstance(phase["detail"], dict, name)
        self.assertEqual(record["phases"]["resolution_readback"]["status"], "ok")
        self.assertEqual(record["phases"]["build"]["status"], "ok")
        self.assertEqual(record["phases"]["test"]["status"], "skipped")
        self.assertEqual(record["phases"]["prune"]["status"], "skipped")
        self.assertEqual(record["candidate"]["candidate_id"], CANDIDATE["candidate_id"])
        self.assertEqual(record["image"]["id"], "sha256:" + "b" * 64)
        self.assertTrue(record["tag"].startswith("pi-unraid:paseo-"))

    def test_cached_steps_counted_from_full_progress(self):
        self.assertEqual(buildx.count_cached_steps(self.WARM_PROGRESS), 8)
        self.assertEqual(buildx.count_cached_steps(""), 0)
        self.assertEqual(buildx.count_cached_steps(None or ""), 0)
        lookalikes = (
            "reading CACHED lists...\n"
            "  #4 CACHED with leading spaces\n"
            "step CACHED done\n"
        )
        self.assertEqual(buildx.count_cached_steps(lookalikes), 0)

    def test_build_record_carries_cached_steps(self):
        rc, record, _ = self.run_mock_build([], build_stdout="", build_stderr=self.WARM_PROGRESS)
        self.assertEqual(rc, 0)
        self.assertEqual(record["phases"]["build"]["detail"]["cached_steps"], 8)

    def test_build_echo_keeps_stderr_progress(self):
        # Regression: plain progress (including #N CACHED) is written to
        # stderr; echoing stdout alone drops the cache evidence from the log.
        proc = Completed(0, "", self.WARM_PROGRESS)
        buf = io.StringIO()
        with mock.patch.object(sys, "stdout", buf):
            buildx.print_build_output(proc)
        echoed = buf.getvalue()
        for step in ("#3 CACHED", "#4 CACHED", "#10 CACHED"):
            self.assertIn(step, echoed)

    def test_build_with_prune_requires_with_smoke(self):
        calls: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            parser = buildx.build_parser()
            args = parser.parse_args([
                "build", "--context", str(ROOT), "--record", str(tdp / "record.json"),
                "--state-dir", str(tdp / "state"), "--with-prune",
            ])
            with mock.patch.object(buildx, "_run", side_effect=lambda a, e, t: calls.append(a)):
                rc = buildx.cmd_build(args)
        self.assertEqual(rc, buildx.EXIT_VALIDATION)
        self.assertEqual(calls, [])
        self.assertFalse((tdp / "record.json").exists())

    def test_prune_is_bounded_scoped_and_ordered_after_build(self):
        rc, record, calls = self.run_mock_build(["--with-smoke", "--with-prune"])
        self.assertEqual(rc, 0)
        self.assertEqual(record["phases"]["test"]["status"], "ok")
        self.assertEqual(
            [s["name"] for s in record["phases"]["test"]["detail"]["smokes"]],
            ["image_provenance", "persistence_ownership",
             "instruction_plane", "global_capabilities"],
        )
        prunes = [c for c in calls if c[:3] == ["docker", "buildx", "prune"]]
        self.assertEqual(len(prunes), 1)
        prune = prunes[0]
        self.assertIn("--builder", prune)
        self.assertIn("pi-unraid-paseo", prune)
        self.assertIn("--keep-storage", prune)
        self.assertIn("8GB", prune)
        self.assertIn("--force", prune)
        order = [[c[2] for c in calls].index("build"), [c[2] for c in calls].index("prune")]
        self.assertLess(order[0], order[1])
        self.assertEqual(record["phases"]["prune"]["status"], "ok")
        self.assertNotIn("system", " ".join(prune))
        self.assertNotIn("until=", " ".join(prune))

    def test_prune_bound_must_be_explicit_size(self):
        with self.assertRaises(buildx.BuildxError):
            buildx.run_prune(lambda a, e, t: Completed(0), "pi-unraid-paseo", "all", {})

    def test_invalid_prune_bound_is_rejected_before_docker(self):
        calls: list[list[str]] = []
        parser = buildx.build_parser()
        with tempfile.TemporaryDirectory() as td:
            args = parser.parse_args([
                "prune", "--record", str(Path(td) / "record.json"),
                "--keep-storage", "all",
            ])
            with mock.patch.object(buildx, "_run", side_effect=lambda a, e, t: calls.append(a)):
                rc = buildx.cmd_prune(args)
        self.assertEqual(rc, buildx.EXIT_VALIDATION)
        self.assertEqual(calls, [])

    def test_prune_requires_record_flag(self):
        parser = buildx.build_parser()
        with self.assertRaises(SystemExit) as ctx:
            parser.parse_args(["prune"])
        self.assertEqual(ctx.exception.code, 2)

    def test_local_cache_backend_is_opt_in(self):
        _, _, plain = self.run_mock_build([])
        builds = [c for c in plain if c[:3] == ["docker", "buildx", "build"]]
        self.assertEqual(len(builds), 1)
        self.assertNotIn("--cache-to", builds[0])
        self.assertNotIn("--cache-from", builds[0])
        with tempfile.TemporaryDirectory() as td:
            _, _, cached = self.run_mock_build(["--cache-dir", td])
        builds = [c for c in cached if c[:3] == ["docker", "buildx", "build"]]
        self.assertIn("--cache-from", builds[0])
        self.assertIn("--cache-to", builds[0])
        joined = " ".join(builds[0])
        self.assertIn("type=local", joined)
        self.assertIn("mode=max", joined)
        self.assertNotIn("type=registry", joined)


class GatedTestPruneFlowTests(unittest.TestCase):
    TAG = "pi-unraid:paseo-b4e0c1e7c276"

    def write_record(self, tdp: Path, build_status="ok", test_status="skipped",
                     builder="pi-unraid-paseo") -> Path:
        record = {
            "schema_version": 1,
            "command": "build",
            "builder": {"name": builder, "driver": "docker-container",
                        "reused": False, "state_dir": str(tdp / "state")},
            "candidate": {"path": str(ROOT / "config" / "paseo-candidate.json"),
                          "candidate_id": CANDIDATE["candidate_id"]},
            "context": str(ROOT),
            "tag": self.TAG,
            "image": {"id": "sha256:" + "d" * 64, "digests": [],
                      "candidate_label": CANDIDATE["candidate_id"]},
            "cache": {"local_dir": None},
            "started_at": "2026-09-26T00:00:00+00:00",
            "finished_at": "2026-09-26T00:01:00+00:00",
            "phases": {
                "resolution_readback": {"status": "ok", "duration_ms": 5, "detail": {}},
                "builder_ensure": {"status": "ok", "duration_ms": 5, "detail": {}},
                "build": {"status": build_status, "duration_ms": 1000,
                          "detail": {"tag": self.TAG, "cached_steps": 8}},
                "test": {"status": test_status, "duration_ms": 0, "detail": {}},
                "prune": {"status": "skipped", "duration_ms": 0, "detail": {}},
            },
        }
        path = tdp / "record.json"
        path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
        return path

    def test_suite_runs_all_four_smokes_in_order(self):
        suite = buildx.smoke_suite(self.TAG, "/tmp/candidate.json")
        self.assertEqual([name for name, _ in suite],
                         ["image_provenance", "persistence_ownership",
                          "instruction_plane", "global_capabilities"])
        self.assertIn("smoke_paseo_image.py", suite[0][1][1])
        self.assertEqual(suite[0][1][-2:], [self.TAG, "/tmp/candidate.json"])
        for _, argv in suite[1:]:
            self.assertEqual(argv[0], "bash")
            self.assertEqual(argv[-1], self.TAG)

    def test_command_measures_test_phase_and_preserves_build(self):
        calls: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            path = self.write_record(tdp)
            parser = buildx.build_parser()
            args = parser.parse_args(["test", "--record", str(path)])
            with mock.patch.object(
                    buildx, "_run",
                    side_effect=lambda a, e, t: (calls.append(a), Completed(0, "ok\n"))[1]):
                rc = buildx.cmd_test(args)
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 4)
            record = json.loads(path.read_text())
        self.assertEqual(record["phases"]["test"]["status"], "ok")
        self.assertGreaterEqual(record["phases"]["test"]["duration_ms"], 0)
        self.assertEqual(
            [s["name"] for s in record["phases"]["test"]["detail"]["smokes"]],
            ["image_provenance", "persistence_ownership",
             "instruction_plane", "global_capabilities"],
        )
        self.assertEqual(record["phases"]["build"]["status"], "ok")
        self.assertEqual(record["phases"]["build"]["detail"]["cached_steps"], 8)
        self.assertEqual(record["image"]["id"], "sha256:" + "d" * 64)
        self.assertEqual(record["phases"]["prune"]["status"], "skipped")

    def test_command_refuses_without_successful_build(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            bad_build = self.write_record(tdp, build_status="failed")
            bad_build.rename(tdp / "failed.json")
            cases = [tdp / "failed.json", tdp / "absent.json"]
            broken = tdp / "broken.json"
            broken.write_text("{not json")
            cases.append(broken)
            for case in cases:
                with self.subTest(case=case.name):
                    before = case.read_bytes() if case.exists() else None
                    calls: list[list[str]] = []
                    parser = buildx.build_parser()
                    args = parser.parse_args(["test", "--record", str(case)])
                    with mock.patch.object(
                            buildx, "_run",
                            side_effect=lambda a, e, t: calls.append(a)):
                        rc = buildx.cmd_test(args)
                    self.assertEqual(rc, buildx.EXIT_VALIDATION)
                    self.assertEqual(calls, [])
                    if before is not None:
                        self.assertEqual(case.read_bytes(), before)

    def test_failed_smoke_fails_fast_and_blocks_later_smokes(self):
        calls: list[list[str]] = []

        def runner(argv, env, timeout):
            calls.append(argv)
            if "verify-compose-foundation.sh" in argv[1]:
                return Completed(1, "", "ownership drift")
            return Completed(0, "ok\n")

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            path = self.write_record(tdp)
            parser = buildx.build_parser()
            args = parser.parse_args(["test", "--record", str(path)])
            with mock.patch.object(buildx, "_run", side_effect=runner):
                rc = buildx.cmd_test(args)
            self.assertEqual(rc, buildx.EXIT_BUILD)
            self.assertEqual(len(calls), 2)
            record = json.loads(path.read_text())
        self.assertEqual(record["phases"]["test"]["status"], "failed")
        self.assertIn("persistence_ownership", record["phases"]["test"]["detail"]["error"])
        self.assertEqual(record["phases"]["build"]["status"], "ok")
        self.assertEqual(record["phases"]["prune"]["status"], "skipped")

    def test_prune_refuses_until_build_and_test_succeed(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            for build_status, test_status in (("ok", "skipped"), ("ok", "failed"),
                                              ("failed", "skipped")):
                path = self.write_record(tdp, build_status=build_status,
                                         test_status=test_status)
                before = path.read_bytes()
                calls: list[list[str]] = []
                parser = buildx.build_parser()
                args = parser.parse_args(["prune", "--record", str(path)])
                with mock.patch.object(
                        buildx, "_run",
                        side_effect=lambda a, e, t: calls.append(a)):
                    rc = buildx.cmd_prune(args)
                self.assertEqual(rc, buildx.EXIT_VALIDATION, (build_status, test_status))
                self.assertEqual(calls, [])
                self.assertEqual(path.read_bytes(), before)

    def test_prune_refuses_builder_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            path = self.write_record(tdp, test_status="ok", builder="pi-unraid-paseo")
            before = path.read_bytes()
            calls: list[list[str]] = []
            parser = buildx.build_parser()
            args = parser.parse_args(["prune", "--record", str(path),
                                      "--builder", "pi-unraid-other"])
            with mock.patch.object(
                    buildx, "_run",
                    side_effect=lambda a, e, t: calls.append(a)):
                rc = buildx.cmd_prune(args)
            self.assertEqual(rc, buildx.EXIT_VALIDATION)
            self.assertEqual(calls, [])
            self.assertEqual(path.read_bytes(), before)

    def test_prune_measures_phase_and_preserves_record(self):
        calls: list[list[str]] = []
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            path = self.write_record(tdp, test_status="ok")
            parser = buildx.build_parser()
            args = parser.parse_args(["prune", "--record", str(path)])
            with mock.patch.object(buildx, "_run", side_effect=lambda a, e, t: (
                    calls.append(a), Completed(0, "Total: 1GB"))[1]), \
                    mock.patch.object(sys, "stdout", buf):
                rc = buildx.cmd_prune(args)
            self.assertEqual(rc, 0)
            record = json.loads(path.read_text())
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:3], ["docker", "buildx", "prune"])
        self.assertIn("--keep-storage", calls[0])
        self.assertEqual(record["phases"]["prune"]["status"], "ok")
        self.assertEqual(record["phases"]["prune"]["detail"]["keep_storage"], "8GB")
        self.assertEqual(record["phases"]["build"]["status"], "ok")
        self.assertEqual(record["phases"]["test"]["status"], "ok")
        summary = json.loads(buf.getvalue())
        self.assertEqual(summary["command"], "prune")
        self.assertEqual(summary["builder"], "pi-unraid-paseo")

    def test_full_test_then_prune_sequence(self):
        calls: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            path = self.write_record(tdp)
            parser = buildx.build_parser()
            with mock.patch.object(
                    buildx, "_run",
                    side_effect=lambda a, e, t: (calls.append(a), Completed(0, "ok\n"))[1]):
                self.assertEqual(buildx.cmd_test(parser.parse_args(["test", "--record", str(path)])), 0)
                prune_before = [c for c in calls if c[:3] == ["docker", "buildx", "prune"]]
                self.assertEqual(prune_before, [])
                self.assertEqual(
                    buildx.cmd_prune(parser.parse_args(["prune", "--record", str(path)])), 0)
            record = json.loads(path.read_text())
        self.assertEqual(record["phases"]["test"]["status"], "ok")
        self.assertEqual(record["phases"]["prune"]["status"], "ok")
        self.assertEqual(len(record["phases"]["test"]["detail"]["smokes"]), 4)

class NoForbiddenSurfaceTests(unittest.TestCase):
    def scanned_source(self) -> str:
        # The deny-list constants themselves name the forbidden tokens so the
        # build path can reject them; scan everything outside those blocks.
        source = re.sub(
            r"FLOATING_CHANNEL_TOKENS = \(.*?\)\n", "", MODULE_SOURCE, flags=re.S)
        source = re.sub(
            r"LEGACY_TOKENS = \(.*?\)\n", "", source, flags=re.S)
        return source

    def test_no_latest_resolution_registry_or_legacy_surface(self):
        source = self.scanned_source()
        lowered = source.lower()
        for token in ("releases/latest", ":latest", "/latest/", "@latest"):
            self.assertNotIn(token, lowered, token)
        for token in ("resolve_live", "urllib", "socket", "http.client", "requests",
                      "--push", "docker login", "type=registry", "system prune",
                      "builder rm", "buildx use"):
            self.assertNotIn(token, source, token)
        for token in ("node:24-bookworm-slim", "/home/pi", "NOPASSWD",
                      "pi-unraid-entrypoint", "pi-unraid-service", "host.docker.internal"):
            self.assertNotIn(token, source, token)
        # The deny lists must still cover those tokens (fail-closed checks).
        for token in buildx.FLOATING_CHANNEL_TOKENS:
            self.assertIn(token, MODULE_SOURCE)
        for token in ("node:24-bookworm-slim", "/home/pi", "NOPASSWD",
                      "pi-unraid-entrypoint", "pi-unraid-service"):
            self.assertIn(token, buildx.LEGACY_TOKENS)

    def test_no_latest_resolution_or_legacy_pi_lifecycle(self):
        lowered = DOCKERFILE.lower()
        self.assertNotIn("releases/latest", lowered)
        self.assertNotIn(":latest", lowered)
        self.assertNotIn("@latest", lowered)
        for token in ("node:24-bookworm-slim", "NODE_IMAGE", "/home/pi", "NOPASSWD",
                      "pi-unraid-entrypoint", "pi-unraid-service"):
            self.assertNotIn(token, DOCKERFILE, token)


class DockerfileInvalidationTests(unittest.TestCase):
    def run_blocks(self):
        blocks = []
        current: list[str] = []
        for line in DOCKERFILE.splitlines():
            if line.startswith("RUN ") and current:
                blocks.append("\n".join(current))
                current = [line]
            elif line.startswith("RUN "):
                current = [line]
            elif current and (line.startswith(" ") or line.startswith("\t") or not line.strip()):
                current.append(line)
            elif current:
                blocks.append("\n".join(current))
                current = []
        if current:
            blocks.append("\n".join(current))
        return blocks

    def test_independently_versioned_components_keep_own_layers(self):
        blocks = self.run_blocks()
        pi_blocks = [b for b in blocks if "pi-coding-agent@" in b]
        pw_blocks = [b for b in blocks if "playwright@" in b]
        self.assertEqual(len(pi_blocks), 1)
        self.assertEqual(len(pw_blocks), 1)
        self.assertIsNot(pi_blocks[0], pw_blocks[0])
        self.assertNotIn("pi-coding-agent", pw_blocks[0])
        self.assertNotIn("playwright@", pi_blocks[0])
        # Slowest browser layer first so Pi-only bumps reuse it.
        self.assertLess(blocks.index(pw_blocks[0]), blocks.index(pi_blocks[0]))
        for needle in ("gh_${PI_UNRAID_GH_VERSION}", "docker-${PI_UNRAID_DOCKER_CLI_VERSION}",
                       "docker/compose"):
            holders = [b for b in blocks if needle in b]
            self.assertEqual(len(holders), 1, needle)

    def test_build_inputs_still_consume_only_frozen_candidate(self):
        readback = buildx.verify_build_inputs(CANDIDATE, DOCKERFILE, ROOT)
        self.assertEqual(readback["candidate_id"], CANDIDATE["candidate_id"])
        poisoned = DOCKERFILE.replace(
            f'PI_UNRAID_PI_VERSION="{CANDIDATE["components"]["pi"]["version"]}"',
            'PI_UNRAID_PI_VERSION="0.99.0"',
        )
        with self.assertRaises(buildx.BuildxError):
            buildx.verify_build_inputs(CANDIDATE, poisoned, ROOT)
        latest_dockerfile = DOCKERFILE + "\nRUN echo ghcr.io/getpaseo/paseo:latest\n"
        with self.assertRaises(buildx.BuildxError):
            buildx.verify_build_inputs(CANDIDATE, latest_dockerfile, ROOT)


if __name__ == "__main__":
    unittest.main()
