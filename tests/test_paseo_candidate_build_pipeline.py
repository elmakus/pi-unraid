from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_candidate_build.py"
WORKFLOW = ROOT / ".github" / "workflows" / "paseo-candidate-build.yml"
DOCKERFILE = (ROOT / "Dockerfile").read_text()
ACCEPTED = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())

SPEC = importlib.util.spec_from_file_location("paseo_candidate_build", SCRIPT)
BUILD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILD)


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def target_candidate() -> dict:
    target = copy.deepcopy(ACCEPTED)
    target["candidate_id"] = "sha256:" + "a" * 64
    versions = {
        "paseo": "9.9.1",
        "pi": "9.9.2",
        "specpi": "9.9.3",
        "pi_mcp_adapter": "9.9.4",
        "playwright": "9.9.5",
        "github_cli": "9.9.6",
        "docker_cli": "9.9.7",
        "docker_compose": "9.9.8",
    }
    for name, version in versions.items():
        target["components"][name]["version"] = version
    target["components"]["paseo"]["artifact"]["reference"] = (
        "ghcr.io/getpaseo/paseo@sha256:" + "b" * 64
    )
    target["components"]["github_cli"]["artifact"]["digest"] = "sha256:" + "c" * 64
    target["components"]["docker_compose"]["artifact"]["digest"] = "sha256:" + "d" * 64
    return target


class CandidateBuildRenderingTests(unittest.TestCase):
    def test_render_changes_only_candidate_bound_literals(self):
        target = target_candidate()
        rendered = BUILD.render_dockerfile(DOCKERFILE, ACCEPTED, target)

        self.assertIn(
            f"FROM {target['components']['paseo']['artifact']['reference']}",
            rendered,
        )
        self.assertIn(f'io.pi-unraid.candidate-id="{target["candidate_id"]}"', rendered)
        self.assertIn(f'PI_UNRAID_CANDIDATE_ID="{target["candidate_id"]}"', rendered)
        for name, env_name in (
            ("pi", "PI_UNRAID_PI_VERSION"),
            ("specpi", "PI_UNRAID_SPECPI_VERSION"),
            ("pi_mcp_adapter", "PI_UNRAID_PI_MCP_ADAPTER_VERSION"),
            ("playwright", "PI_UNRAID_PLAYWRIGHT_VERSION"),
            ("github_cli", "PI_UNRAID_GH_VERSION"),
            ("docker_cli", "PI_UNRAID_DOCKER_CLI_VERSION"),
            ("docker_compose", "PI_UNRAID_DOCKER_COMPOSE_VERSION"),
        ):
            self.assertIn(f'{env_name}="{target["components"][name]["version"]}"', rendered)
        self.assertIn("c" * 64, rendered)
        self.assertIn("d" * 64, rendered)
        self.assertNotIn(ACCEPTED["candidate_id"], rendered)

    def test_render_fails_closed_when_accepted_binding_is_missing(self):
        target = target_candidate()
        broken = DOCKERFILE.replace(
            f'PI_UNRAID_PI_VERSION="{ACCEPTED["components"]["pi"]["version"]}"',
            'PI_UNRAID_PI_VERSION="unexpected"',
        )
        with self.assertRaises(BUILD.CandidateBuildError):
            BUILD.render_dockerfile(broken, ACCEPTED, target)


class CandidateBuildHandoffTests(unittest.TestCase):
    def write_json(self, path: Path, value: dict) -> bytes:
        raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return raw

    def make_files(self, root: Path):
        accepted_path = root / "accepted.json"
        candidate_path = root / "candidate.json"
        evidence_path = root / "handoff.json"
        accepted_raw = self.write_json(accepted_path, ACCEPTED)
        target = target_candidate()
        candidate_raw = self.write_json(candidate_path, target)
        evidence = {
            "schema_version": 1,
            "status": "update",
            "candidate_id": target["candidate_id"],
            "accepted_candidate_id": ACCEPTED["candidate_id"],
            "candidate_file_sha256": digest(candidate_raw),
            "source_sha": "1" * 40,
            "source_ref": "refs/heads/main",
        }
        evidence_raw = self.write_json(evidence_path, evidence)
        return accepted_path, candidate_path, evidence_path, accepted_raw, candidate_raw, evidence_raw

    def test_handoff_binds_candidate_bytes_parent_and_default_ref(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            accepted, candidate, evidence, _, candidate_raw, _ = self.make_files(root)
            c, raw, e, _, a = BUILD.verify_handoff(
                candidate,
                evidence,
                accepted,
                source_parent="1" * 40,
                expected_source_ref="refs/heads/main",
            )
            self.assertEqual(raw, candidate_raw)
            self.assertEqual(c["candidate_id"], e["candidate_id"])
            self.assertEqual(a["candidate_id"], e["accepted_candidate_id"])

    def test_handoff_rejects_stale_parent_and_tampered_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            accepted, candidate, evidence, *_ = self.make_files(root)
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_handoff(
                    candidate,
                    evidence,
                    accepted,
                    source_parent="2" * 40,
                    expected_source_ref="refs/heads/main",
                )
            candidate.write_bytes(candidate.read_bytes() + b" ")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_handoff(
                    candidate,
                    evidence,
                    accepted,
                    source_parent="1" * 40,
                    expected_source_ref="refs/heads/main",
                )

    def test_prepare_uses_isolated_context_and_exact_target_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            accepted, candidate, evidence, _, candidate_raw, _ = self.make_files(root)
            source = root / "source"
            (source / "config").mkdir(parents=True)
            (source / "scripts").mkdir()
            (source / "Dockerfile").write_text(DOCKERFILE)
            (source / "config" / "paseo-candidate.json").write_text(
                json.dumps(ACCEPTED, sort_keys=True, indent=2) + "\n"
            )
            fake_buildx = mock.Mock()
            fake_buildx.verify_build_inputs.return_value = {
                "candidate_id": target_candidate()["candidate_id"]
            }
            stage = root / "stage"
            with mock.patch.object(BUILD, "load_buildx", return_value=fake_buildx):
                result = BUILD.prepare_context(
                    candidate_path=candidate,
                    evidence_path=evidence,
                    accepted_path=accepted,
                    source_root=source,
                    stage_dir=stage,
                    source_head="3" * 40,
                    source_parent="1" * 40,
                    expected_source_ref="refs/heads/main",
                )
            self.assertEqual((stage / "config" / "paseo-candidate.json").read_bytes(), candidate_raw)
            self.assertEqual(
                json.loads((source / "config" / "paseo-candidate.json").read_text())["candidate_id"],
                ACCEPTED["candidate_id"],
            )
            self.assertEqual(result["status"], "prepared")
            fake_buildx.verify_build_inputs.assert_called_once()


class CandidateBuildPackagingTests(unittest.TestCase):
    def test_package_requires_green_build_and_preserves_same_image_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = target_candidate()
            candidate = root / "candidate.json"
            candidate_raw = (json.dumps(target, sort_keys=True) + "\n").encode()
            candidate.write_bytes(candidate_raw)
            handoff = root / "handoff.json"
            handoff.write_text(json.dumps({
                "candidate_id": target["candidate_id"],
                "accepted_candidate_id": ACCEPTED["candidate_id"],
                "candidate_file_sha256": digest(candidate_raw),
                "source_sha": "1" * 40,
                "source_ref": "refs/heads/main",
            }))
            image_id = "sha256:" + "e" * 64
            record = root / "record.json"
            record.write_text(json.dumps({
                "candidate": {"candidate_id": target["candidate_id"]},
                "tag": "pi-unraid:paseo-test",
                "image": {"id": image_id},
                "phases": {
                    name: {"status": "ok"}
                    for name in ("resolution_readback", "builder_ensure", "build", "test")
                },
            }))
            archive = root / "image.tar"
            evidence = root / "tested.json"

            def fake_run(argv):
                if argv[:3] == ["docker", "image", "inspect"]:
                    return mock.Mock(stdout=image_id + "\n")
                if argv[:3] == ["docker", "image", "save"]:
                    archive.write_bytes(b"exact-tested-image")
                    return mock.Mock(stdout="")
                raise AssertionError(argv)

            with mock.patch.object(BUILD, "run_checked", side_effect=fake_run):
                result = BUILD.package_tested_image(
                    candidate_path=candidate,
                    handoff_evidence_path=handoff,
                    build_record_path=record,
                    archive_path=archive,
                    evidence_path=evidence,
                    source_head="4" * 40,
                )
            self.assertEqual(result["image_id"], image_id)
            self.assertEqual(result["image_archive_sha256"], digest(b"exact-tested-image"))
            self.assertEqual(json.loads(evidence.read_text())["status"], "tested_image_preserved")

    def test_package_refuses_unverified_test_phase(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = target_candidate()
            candidate = root / "candidate.json"
            candidate_raw = (json.dumps(target) + "\n").encode()
            candidate.write_bytes(candidate_raw)
            handoff = root / "handoff.json"
            handoff.write_text(json.dumps({
                "candidate_id": target["candidate_id"],
                "candidate_file_sha256": digest(candidate_raw),
            }))
            record = root / "record.json"
            record.write_text(json.dumps({
                "candidate": {"candidate_id": target["candidate_id"]},
                "tag": "pi-unraid:paseo-test",
                "image": {"id": "sha256:" + "e" * 64},
                "phases": {
                    "resolution_readback": {"status": "ok"},
                    "builder_ensure": {"status": "ok"},
                    "build": {"status": "ok"},
                    "test": {"status": "failed"},
                },
            }))
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.package_tested_image(
                    candidate_path=candidate,
                    handoff_evidence_path=handoff,
                    build_record_path=record,
                    archive_path=root / "image.tar",
                    evidence_path=root / "evidence.json",
                    source_head="4" * 40,
                )


class CandidateBuildWorkflowTests(unittest.TestCase):
    def test_workflow_is_candidate_only_build_once_and_credential_free(self):
        text = WORKFLOW.read_text()
        self.assertIn("pull_request:", text)
        self.assertIn("candidates/paseo-update/candidate.json", text)
        self.assertIn("automation/paseo-update-candidate", text)
        self.assertIn("github.event.pull_request.head.sha", text)
        self.assertIn("contents: read", text)
        self.assertIn("git rev-parse HEAD^", text)
        self.assertEqual(text.count("paseo_buildx.py build"), 1)
        self.assertIn("--with-smoke", text)
        self.assertIn("--smoke-profile core", text)
        self.assertIn("git merge-base --is-ancestor", text)
        self.assertIn("git diff --name-only HEAD^ HEAD", text)
        self.assertIn("paseo_candidate_build.py package", text)
        self.assertIn("image.tar", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertNotIn("resolve-paseo-candidate.py", text)
        for forbidden in (
            "docker/login-action",
            "docker push",
            "build-push-action",
            "--push",
            ":accepted",
            "ssh ",
        ):
            self.assertNotIn(forbidden, text)

    def test_buildx_smoke_can_bind_to_isolated_candidate_context(self):
        spec = importlib.util.spec_from_file_location(
            "paseo_buildx_for_candidate_test", ROOT / "scripts" / "paseo_buildx.py"
        )
        buildx = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(buildx)
        stage = Path("/isolated/staged-candidate")
        suite = buildx.smoke_suite("pi-unraid:paseo-test", "/candidate.json", stage)
        for _, argv in suite:
            script = Path(argv[1])
            self.assertTrue(str(script).startswith(str(stage / "scripts")))

        core = buildx.smoke_suite("pi-unraid:paseo-test", "/candidate.json", stage, "core")
        self.assertEqual(
            [name for name, _ in core],
            ["image_provenance", "persistence_ownership", "instruction_plane"],
        )


if __name__ == "__main__":
    unittest.main()
