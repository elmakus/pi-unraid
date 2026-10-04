from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paseo_candidate_build_companion", ROOT / "scripts" / "paseo_candidate_build.py"
)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def make_source(root: Path) -> Path:
    source = root / "source"
    agent = source / "config" / "pi-agent"
    (agent / "bin").mkdir(parents=True)
    (agent / "policies").mkdir(parents=True)
    (agent / "AGENTS.md").write_text("# fixture companion\n")
    tool = agent / "bin" / "tool.sh"
    tool.write_text("#!/bin/sh\nexit 0\n")
    tool.chmod(0o755)
    (agent / "policies" / "p.json").write_text("{}\n")
    return source


class CompanionBundleBindingTests(unittest.TestCase):
    def test_identity_declares_files_modes_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            self.assertEqual(identity["schema_version"], 1)
            self.assertEqual(identity["source"], "config/pi-agent")
            self.assertEqual(
                identity["files"], ["AGENTS.md", "bin/tool.sh", "policies/p.json"]
            )
            self.assertEqual(
                identity["modes"],
                {"AGENTS.md": "0644", "bin/tool.sh": "0755", "policies/p.json": "0644"},
            )
            self.assertTrue(identity["source_digest"].startswith("sha256:"))
            # Deterministic across calls.
            again = BUILD.companion_bundle_identity(source)
            self.assertEqual(again, identity)

    def test_identity_is_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            text = json.dumps(identity, sort_keys=True)
            for forbidden in ("PRIVATE KEY", "API_KEY=", "GITHUB_TOKEN=", "ghp_"):
                self.assertNotIn(forbidden, text)

    def test_verify_accepts_matching_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            bound = BUILD.verify_companion_binding(source, identity)
            self.assertEqual(bound["status"], "bound")
            self.assertEqual(bound["source_digest"], identity["source_digest"])
            self.assertEqual(bound["files"], 3)

    def test_changed_content_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            (source / "config" / "pi-agent" / "AGENTS.md").write_text("# mutated\n")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, identity)

    def test_removed_file_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            (source / "config" / "pi-agent" / "policies" / "p.json").unlink()
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, identity)

    def test_added_file_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            (source / "config" / "pi-agent" / "EXTRA.md").write_text("# extra\n")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, identity)

    def test_wrong_declared_digest_or_modes_do_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            wrong_digest = dict(identity, source_digest="sha256:" + "0" * 64)
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, wrong_digest)
            wrong_modes = dict(identity, modes=dict(identity["modes"], **{"AGENTS.md": "0755"}))
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, wrong_modes)

    def test_malformed_declaration_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            for bad in (
                None,
                [],
                dict(identity, schema_version=2),
                dict(identity, source="config/elsewhere"),
                dict(identity, files="AGENTS.md"),
                dict(identity, modes={}),
            ):
                with self.subTest(bad=repr(bad)[:60]):
                    with self.assertRaises(BUILD.CandidateBuildError):
                        BUILD.verify_companion_binding(source, bad)

    def test_missing_source_and_symlink_are_unverifiable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.companion_bundle_identity(root / "absent")
            source = make_source(root)
            (source / "config" / "pi-agent" / "link.md").symlink_to("AGENTS.md")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.companion_bundle_identity(source)

    def test_real_source_bundle_binds_and_matches_declared_modes(self) -> None:
        identity = BUILD.companion_bundle_identity(ROOT)
        self.assertIn("bin/run-llm-test.sh", identity["files"])
        self.assertEqual(identity["modes"]["bin/run-llm-test.sh"], "0755")
        bound = BUILD.verify_companion_binding(ROOT, identity)
        self.assertEqual(bound["status"], "bound")


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _candidate(cid: str) -> dict:
    return {
        "schema_version": 1,
        "candidate_id": cid,
        "components": {
            "paseo": {
                "version": "0.9.2",
                "artifact": {"reference": "ghcr.io/getpaseo/paseo@sha256:" + "a" * 64},
            },
            "pi": {"version": "0.87.1"},
            "specpi": {"version": "0.34.0"},
            "pi_mcp_adapter": {"version": "2.37.0"},
            "playwright": {"version": "1.63.0"},
            "github_cli": {
                "version": "2.101.0",
                "artifact": {"digest": "sha256:" + "b" * 64},
            },
            "docker_cli": {"version": "29.8.1"},
            "docker_compose": {
                "version": "5.5.1",
                "artifact": {"digest": "sha256:" + "c" * 64},
            },
        },
    }


def _dockerfile_for(accepted: dict) -> str:
    lines = [f"FROM {accepted['components']['paseo']['artifact']['reference']}"]
    lines.append(f"LABEL io.pi-unraid.candidate-id=\"{accepted['candidate_id']}\"")
    lines.append(f"ENV PI_UNRAID_CANDIDATE_ID=\"{accepted['candidate_id']}\"")
    for name, label in (
        ("paseo", "io.pi-unraid.paseo-version"),
        ("pi", "io.pi-unraid.pi-version"),
        ("specpi", "io.pi-unraid.specpi-version"),
        ("pi_mcp_adapter", "io.pi-unraid.pi-mcp-adapter-version"),
        ("playwright", "io.pi-unraid.playwright-version"),
    ):
        lines.append(f"LABEL {label}=\"{accepted['components'][name]['version']}\"")
    for name, env_name in (
        ("pi", "PI_UNRAID_PI_VERSION"),
        ("specpi", "PI_UNRAID_SPECPI_VERSION"),
        ("pi_mcp_adapter", "PI_UNRAID_PI_MCP_ADAPTER_VERSION"),
        ("playwright", "PI_UNRAID_PLAYWRIGHT_VERSION"),
        ("github_cli", "PI_UNRAID_GH_VERSION"),
        ("docker_cli", "PI_UNRAID_DOCKER_CLI_VERSION"),
        ("docker_compose", "PI_UNRAID_DOCKER_COMPOSE_VERSION"),
    ):
        lines.append(f"ENV {env_name}=\"{accepted['components'][name]['version']}\"")
    lines.append(accepted["components"]["github_cli"]["artifact"]["digest"].removeprefix("sha256:"))
    lines.append(accepted["components"]["docker_compose"]["artifact"]["digest"].removeprefix("sha256:"))
    return "\n".join(lines) + "\n"


class CompanionPrepareIntegrationTests(unittest.TestCase):
    def make_inputs(self, root: Path):
        accepted = _candidate("sha256:" + "d" * 64)
        target = _candidate("sha256:" + "e" * 64)
        accepted_path = root / "accepted.json"
        accepted_path.write_text(json.dumps(accepted, sort_keys=True) + "\n")
        candidate_path = root / "candidate.json"
        candidate_raw = (json.dumps(target, sort_keys=True) + "\n").encode()
        candidate_path.write_bytes(candidate_raw)
        evidence_path = root / "handoff.json"
        evidence_path.write_text(json.dumps({
            "schema_version": 1,
            "status": "update",
            "candidate_id": target["candidate_id"],
            "accepted_candidate_id": accepted["candidate_id"],
            "candidate_file_sha256": _digest(candidate_raw),
            "source_sha": "1" * 40,
            "source_ref": "refs/heads/main",
        }) + "\n")
        source = root / "source"
        (source / "config").mkdir(parents=True)
        (source / "scripts").mkdir()
        (source / "Dockerfile").write_text(_dockerfile_for(accepted))
        (source / "config" / "paseo-candidate.json").write_text(
            json.dumps(accepted, sort_keys=True, indent=2) + "\n"
        )
        agent = source / "config" / "pi-agent"
        (agent / "bin").mkdir(parents=True)
        (agent / "AGENTS.md").write_text("# fixture companion\n")
        tool = agent / "bin" / "tool.sh"
        tool.write_text("#!/bin/sh\nexit 0\n")
        tool.chmod(0o755)
        return accepted_path, candidate_path, evidence_path, source

    def run_prepare(self, root: Path):
        accepted, candidate, evidence, source = self.make_inputs(root)
        fake_buildx = mock.Mock()
        fake_buildx.verify_build_inputs.return_value = {"candidate_id": "sha256:" + "e" * 64}
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
        return result, stage

    def test_prepare_records_and_enforces_staged_companion(self) -> None:
        # Real entrypoint: the staged record carries the declaration AND the
        # staged payload is verified against it before the record is written.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result, stage = self.run_prepare(root)
            companion = result["companion_bundle"]
            self.assertEqual(companion["source"], "config/pi-agent")
            self.assertEqual(companion["files"], ["AGENTS.md", "bin/tool.sh"])
            stored = json.loads((stage / ".pi-unraid-candidate-build-input.json").read_text())
            self.assertEqual(stored["companion_bundle"], companion)
            bound = BUILD.verify_companion_binding(stage, companion)
            self.assertEqual(bound["status"], "bound")

    def test_post_prepare_staged_mutation_breaks_binding(self) -> None:
        # Content mutation and file-set mutation of the staged payload each
        # fail against the declared record from the real prepare run.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result, stage = self.run_prepare(root)
            companion = result["companion_bundle"]
            staged_agents = stage / "config" / "pi-agent" / "AGENTS.md"
            staged_agents.write_text("# mutated after prepare\n")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(stage, companion)
            staged_agents.write_text("# fixture companion\n")
            BUILD.verify_companion_binding(stage, companion)
            (stage / "config" / "pi-agent" / "EXTRA.md").write_text("# added\n")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(stage, companion)


class CompanionPackageChainTests(unittest.TestCase):
    def make_package_inputs(self, root: Path, companion):
        target = _candidate("sha256:" + "e" * 64)
        candidate = root / "candidate.json"
        candidate_raw = (json.dumps(target, sort_keys=True) + "\n").encode()
        candidate.write_bytes(candidate_raw)
        handoff = root / "handoff.json"
        handoff.write_text(json.dumps({
            "candidate_id": target["candidate_id"],
            "accepted_candidate_id": "sha256:" + "d" * 64,
            "candidate_file_sha256": _digest(candidate_raw),
            "source_sha": "1" * 40,
            "source_ref": "refs/heads/main",
        }) + "\n")
        image_id = "sha256:" + "f" * 64
        record = root / "record.json"
        record.write_text(json.dumps({
            "candidate": {"candidate_id": target["candidate_id"]},
            "tag": "pi-unraid:paseo-test",
            "image": {"id": image_id},
            "phases": {name: {"status": "ok"} for name in (
                "resolution_readback", "builder_ensure", "build", "test")},
        }) + "\n")
        build_input = root / "build-input.json"
        build_input.write_text(json.dumps({
            "schema_version": 1,
            "status": "prepared",
            "candidate_id": target["candidate_id"],
            "companion_bundle": companion,
        }) + "\n")
        return candidate, handoff, record, build_input, image_id

    def fake_docker(self, root: Path, image_id: str):
        archive = root / "image.tar"

        def fake_run(argv):
            if argv[:3] == ["docker", "image", "inspect"]:
                return mock.Mock(stdout=image_id + "\n")
            if argv[:3] == ["docker", "image", "save"]:
                archive.write_bytes(b"exact-tested-image")
                return mock.Mock(stdout="")
            raise AssertionError(argv)

        return mock.Mock(side_effect=fake_run)

    def test_package_retains_companion_before_external_actions(self) -> None:
        # Real package entrypoint with mocked Docker: the companion declaration
        # is retained in the package evidence alongside image identity.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            companion = BUILD.companion_bundle_identity(ROOT)
            candidate, handoff, record, build_input, image_id = self.make_package_inputs(
                root, companion
            )
            docker = self.fake_docker(root, image_id)
            with mock.patch.object(BUILD, "run_checked", docker):
                result = BUILD.package_tested_image(
                    candidate_path=candidate,
                    handoff_evidence_path=handoff,
                    build_record_path=record,
                    archive_path=root / "image.tar",
                    evidence_path=root / "tested.json",
                    source_head="4" * 40,
                    build_input_path=build_input,
                )
            self.assertEqual(result["companion_bundle"], companion)
            stored = json.loads((root / "tested.json").read_text())
            self.assertEqual(stored["companion_bundle"]["source_digest"], companion["source_digest"])
            self.assertTrue(docker.called)

    def test_package_rejects_bad_companion_before_external_actions(self) -> None:
        # Missing/malformed/inconsistent declarations fail BEFORE any docker
        # call (mock asserts no external action occurred).
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            companion = BUILD.companion_bundle_identity(ROOT)
            candidate, handoff, record, build_input, image_id = self.make_package_inputs(
                root, companion
            )
            base = json.loads(build_input.read_text())
            variants = {
                "missing_declaration": {k: v for k, v in base.items() if k != "companion_bundle"},
                "malformed_declaration": dict(base, companion_bundle={"source": "config/pi-agent"}),
                "wrong_schema": dict(base, companion_bundle=dict(companion, schema_version=2)),
                "candidate_mismatch": dict(base, candidate_id="sha256:" + "0" * 64),
            }
            for name, doc in variants.items():
                with self.subTest(variant=name):
                    build_input.write_text(json.dumps(doc) + "\n")
                    docker = self.fake_docker(root, image_id)
                    with mock.patch.object(BUILD, "run_checked", docker):
                        with self.assertRaises(BUILD.CandidateBuildError):
                            BUILD.package_tested_image(
                                candidate_path=candidate,
                                handoff_evidence_path=handoff,
                                build_record_path=record,
                                archive_path=root / "image.tar",
                                evidence_path=root / "tested.json",
                                source_head="4" * 40,
                                build_input_path=build_input,
                            )
                    docker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
