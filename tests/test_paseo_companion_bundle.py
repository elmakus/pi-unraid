from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "paseo_candidate_build_companion", ROOT / "scripts" / "paseo_candidate_build.py"
)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)

REPO_DOCKERFILE = (ROOT / "Dockerfile").read_text()
REPO_ACCEPTED = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())

XSPEC = importlib.util.spec_from_file_location(
    "paseo_buildx_companion_entry", ROOT / "scripts" / "paseo_buildx.py"
)
assert XSPEC and XSPEC.loader
BUILDX = importlib.util.module_from_spec(XSPEC)
XSPEC.loader.exec_module(BUILDX)


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def synthetic_target() -> dict:
    """A material-change candidate that passes the real resolver.

    Only the playwright version/source-tag move (consistent plain semver),
    with the candidate_id re-derived by the exact frozen formula, so the
    real prepare/buildx/package chain exercises genuine verification.
    """
    target = copy.deepcopy(REPO_ACCEPTED)
    target["components"]["playwright"]["version"] = "1.64.0"
    target["components"]["playwright"]["source"]["tag"] = "v1.64.0"
    tmp = json.loads(json.dumps(target))
    tmp.pop("candidate_id", None)
    target["candidate_id"] = "sha256:" + hashlib.sha256(
        json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert target["candidate_id"] != REPO_ACCEPTED["candidate_id"]
    return target


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
        handoff_doc = {
            "candidate_id": target["candidate_id"],
            "accepted_candidate_id": "sha256:" + "d" * 64,
            "candidate_file_sha256": _digest(candidate_raw),
            "source_sha": "1" * 40,
            "source_ref": "refs/heads/main",
        }
        handoff = root / "handoff.json"
        handoff_raw = (json.dumps(handoff_doc, sort_keys=True) + "\n").encode()
        handoff.write_bytes(handoff_raw)
        image_id = "sha256:" + "f" * 64
        record = root / "record.json"
        record.write_text(json.dumps({
            "candidate": {"candidate_id": target["candidate_id"]},
            "companion_bundle": companion,
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
            "candidate_file_sha256": _digest(candidate_raw),
            "handoff_evidence_sha256": _digest(handoff_raw),
            "source_head": "4" * 40,
            "source_parent": "1" * 40,
            "source_ref": "refs/heads/main",
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
                "not_prepared": dict(base, status="staged"),
                "false_digest": dict(base, companion_bundle=dict(
                    companion, source_digest="sha256:" + "0" * 64)),
                "malformed_digest": dict(base, companion_bundle=dict(
                    companion, source_digest="not-a-digest")),
                "wrong_source": dict(base, companion_bundle=dict(
                    companion, source="config/elsewhere")),
                "empty_files": dict(base, companion_bundle=dict(companion, files=[])),
                "modes_key_mismatch": dict(base, companion_bundle=dict(
                    companion, modes={"AGENTS.md": "0644"})),
                "extra_mode_key": dict(base, companion_bundle=dict(
                    companion, modes={**companion["modes"], "EXTRA.md": "0644"})),
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

    def test_package_rejects_prepared_identity_divergence(self) -> None:
        # The prepared byte digests and source/candidate/handoff provenance
        # are re-checked against the ACTUAL inputs before any docker call:
        # tampered candidate/handoff bytes, wrong source linkage and a wrong
        # invoking head each fail with zero external actions.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            companion = BUILD.companion_bundle_identity(ROOT)
            candidate, handoff, record, build_input, image_id = self.make_package_inputs(
                root, companion
            )
            base_candidate = (root / "candidate.json").read_bytes()
            base_handoff = (root / "handoff.json").read_bytes()
            base_input = json.loads(build_input.read_text())

            def attempt(source_head="4" * 40):
                docker = self.fake_docker(root, image_id)
                with mock.patch.object(BUILD, "run_checked", docker):
                    with self.assertRaises(BUILD.CandidateBuildError):
                        BUILD.package_tested_image(
                            candidate_path=candidate,
                            handoff_evidence_path=handoff,
                            build_record_path=record,
                            archive_path=root / "image.tar",
                            evidence_path=root / "tested.json",
                            source_head=source_head,
                            build_input_path=build_input,
                        )
                docker.assert_not_called()

            def reset():
                (root / "candidate.json").write_bytes(base_candidate)
                (root / "handoff.json").write_bytes(base_handoff)
                build_input.write_text(json.dumps(base_input) + "\n")

            # Tampered candidate bytes re-pointed through the handoff so the
            # legacy byte check passes: only the prepared-candidate gate fires.
            reset()
            tampered_raw = base_candidate + b" "
            (root / "candidate.json").write_bytes(tampered_raw)
            repointed = json.loads(base_handoff.decode())
            repointed["candidate_file_sha256"] = _digest(tampered_raw)
            repointed_raw = (json.dumps(repointed, sort_keys=True) + "\n").encode()
            (root / "handoff.json").write_bytes(repointed_raw)
            build_input.write_text(json.dumps(dict(
                base_input, handoff_evidence_sha256=_digest(repointed_raw)
            )) + "\n")
            attempt()

            # Same-content handoff rewritten with different bytes: the legacy
            # content check passes, the prepared-handoff gate fires.
            reset()
            reordered_raw = (json.dumps(
                json.loads(base_handoff.decode()),
                sort_keys=True, separators=(",", ":")) + "\n").encode()
            assert reordered_raw != base_handoff
            (root / "handoff.json").write_bytes(reordered_raw)
            attempt()

            # Wrong prepared source/candidate linkage and invoking head.
            reset()
            doc = json.loads(build_input.read_text())
            for name, patched in (
                ("wrong_parent", dict(doc, source_parent="2" * 40)),
                ("wrong_ref", dict(doc, source_ref="refs/heads/other")),
            ):
                with self.subTest(linkage=name):
                    build_input.write_text(json.dumps(patched) + "\n")
                    attempt()
            reset()
            with self.subTest(linkage="wrong_head"):
                attempt(source_head="5" * 40)

    def test_package_rejects_unbound_legacy_and_mismatched_build_record(self) -> None:
        # A build record without a bound companion (legacy unbound build) or
        # with a different companion than prepared cannot be packaged: the
        # legacy path is mechanically inaccessible as the R2 path.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            companion = BUILD.companion_bundle_identity(ROOT)
            candidate, handoff, record, build_input, image_id = self.make_package_inputs(
                root, companion
            )
            base_record = json.loads(record.read_text())
            other = dict(companion, source_digest="sha256:" + "0" * 64)
            for name, patched in (
                ("legacy_unbound", {k: v for k, v in base_record.items()
                                      if k != "companion_bundle"}),
                ("legacy_null", dict(base_record, companion_bundle=None)),
                ("prepared_mismatch", dict(base_record, companion_bundle=other)),
            ):
                with self.subTest(record=name):
                    record.write_text(json.dumps(patched) + "\n")
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


class CompanionBuildEntryTests(unittest.TestCase):
    """The REAL prepare/build/package entrypoints enforce one binding.

    A synthetic material-change target passes the genuine resolver, so
    prepare runs unmocked; only Docker subprocess calls (and the smoke
    scripts, which need a real image) are faked. Every rejection happens
    before any external call.
    """
    IMAGE_ID = "sha256:" + "f" * 64

    def make_r2_source(self, root: Path) -> Path:
        source = root / "source"
        (source / "config").mkdir(parents=True)
        (source / "scripts").mkdir(parents=True)
        (source / "Dockerfile").write_text(REPO_DOCKERFILE)
        (source / "config" / "paseo-candidate.json").write_text(
            json.dumps(REPO_ACCEPTED, sort_keys=True, indent=2) + "\n"
        )
        # Mirror the tooling tree so the real prepare-time buildx/resolver
        # load inside the fixture source behaves like a true checkout.
        for script in sorted((ROOT / "scripts").glob("*.py")):
            shutil.copyfile(script, source / "scripts" / script.name)
        shutil.copyfile(
            ROOT / "config" / "environment-capabilities.json",
            source / "config" / "environment-capabilities.json",
        )
        agent = source / "config" / "pi-agent"
        (agent / "bin").mkdir(parents=True)
        (agent / "AGENTS.md").write_text("# fixture companion\n")
        tool = agent / "bin" / "tool.sh"
        tool.write_text("#!/bin/sh\nexit 0\n")
        tool.chmod(0o755)
        return source

    def run_real_prepare(self, root: Path):
        target = synthetic_target()
        candidate = root / "candidate.json"
        candidate_raw = (json.dumps(target, sort_keys=True) + "\n").encode()
        candidate.write_bytes(candidate_raw)
        accepted = root / "accepted.json"
        accepted.write_text(json.dumps(REPO_ACCEPTED, sort_keys=True) + "\n")
        handoff = root / "handoff.json"
        handoff.write_text(json.dumps({
            "schema_version": 1,
            "status": "update",
            "candidate_id": target["candidate_id"],
            "accepted_candidate_id": REPO_ACCEPTED["candidate_id"],
            "candidate_file_sha256": _digest(candidate_raw),
            "source_sha": "1" * 40,
            "source_ref": "refs/heads/main",
        }) + "\n")
        source = self.make_r2_source(root)
        stage = root / "stage"
        result = BUILD.prepare_context(
            candidate_path=candidate,
            evidence_path=handoff,
            accepted_path=accepted,
            source_root=source,
            stage_dir=stage,
            source_head="3" * 40,
            source_parent="1" * 40,
            expected_source_ref="refs/heads/main",
        )
        return target, candidate, handoff, stage, result

    def docker_runner(self, calls: list, target_id: str):
        def runner(argv, env, timeout):
            calls.append(argv)
            if argv[:3] == ["docker", "buildx", "inspect"]:
                return Completed(0, "ok")
            if argv[:3] == ["docker", "buildx", "build"]:
                return Completed(0, "done")
            if argv[:3] == ["docker", "image", "inspect"]:
                return Completed(0, json.dumps([{
                    "Id": self.IMAGE_ID,
                    "RepoDigests": [],
                    "Config": {"Labels": {
                        "io.pi-unraid.candidate-id": target_id}},
                }]))
            raise AssertionError(argv)
        return runner

    def build_args(self, root: Path, stage: Path, with_input: bool = True,
                   with_smoke: bool = False):
        argv = [
            "build",
            "--candidate", str(stage / "config" / "paseo-candidate.json"),
            "--context", str(stage),
            "--record", str(root / "build-record.json"),
            "--state-dir", str(root / "state"),
        ]
        if with_input:
            argv += ["--build-input",
                     str(stage / BUILDX.BUILD_INPUT_FILENAME)]
        if with_smoke:
            argv += ["--with-smoke", "--smoke-profile", "core"]
        return BUILDX.build_parser().parse_args(argv)

    def test_build_verifies_and_retains_prepared_binding(self) -> None:
        # Positive: the real build entrypoint verifies the staged payload
        # against the prepared record and retains the same declaration.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target, _, _, stage, prepared = self.run_real_prepare(root)
            declared = prepared["companion_bundle"]
            calls: list = []
            args = self.build_args(root, stage)
            with mock.patch.object(
                    BUILDX, "_run", side_effect=self.docker_runner(calls, target["candidate_id"])):
                rc = BUILDX.cmd_build(args)
            self.assertEqual(rc, 0)
            self.assertTrue(any(c[2] == "build" for c in calls))
            record = json.loads((root / "build-record.json").read_text())
            self.assertEqual(record["phases"]["resolution_readback"]["status"], "ok")
            self.assertEqual(record["companion_bundle"], declared)
            self.assertEqual(
                record["phases"]["resolution_readback"]["detail"]["companion_bundle"],
                declared,
            )

    def test_build_rejects_post_prepare_mutations_before_external_calls(self) -> None:
        # Post-prepare staged content/file-set mutations fail the AUTOMATIC
        # build entrypoint (not just the helper) with zero docker calls.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target, _, _, stage, _ = self.run_real_prepare(root)
            bundle = stage / "config" / "pi-agent"
            mutations = {
                "content": lambda: (bundle / "AGENTS.md").write_text("# mutated\n"),
                "added": lambda: (bundle / "EXTRA.md").write_text("# added\n"),
                "removed": lambda: (bundle / "AGENTS.md").unlink(),
            }
            for name, mutate in mutations.items():
                with self.subTest(mutation=name):
                    mutate()
                    calls: list = []
                    args = self.build_args(root, stage)
                    with mock.patch.object(
                            BUILDX, "_run",
                            side_effect=self.docker_runner(calls, target["candidate_id"])):
                        rc = BUILDX.cmd_build(args)
                    self.assertEqual(rc, BUILDX.EXIT_VALIDATION)
                    self.assertEqual(calls, [])
                    record = json.loads((root / "build-record.json").read_text())
                    self.assertEqual(
                        record["phases"]["resolution_readback"]["status"], "failed")
                    # Restore the fixture payload for the next variant.
                    (bundle / "AGENTS.md").write_text("# fixture companion\n")
                    extra = bundle / "EXTRA.md"
                    if extra.exists():
                        extra.unlink()

    def test_build_rejects_missing_and_false_build_input(self) -> None:
        # Omitted record path, false digest and wrong candidate each fail
        # the real build entrypoint before builder/external actions.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target, _, _, stage, prepared = self.run_real_prepare(root)
            record_path = stage / BUILDX.BUILD_INPUT_FILENAME
            base = json.loads(record_path.read_text())
            cases = {
                "missing_file": None,
                "false_digest": dict(base, companion_bundle=dict(
                    base["companion_bundle"],
                    source_digest="sha256:" + "0" * 64)),
                "wrong_candidate": dict(base, candidate_id="sha256:" + "0" * 64),
                "malformed": dict(base, companion_bundle={"source": "config/pi-agent"}),
            }
            for name, doc in cases.items():
                with self.subTest(case=name):
                    if doc is None:
                        record_path.unlink()
                    else:
                        record_path.write_text(json.dumps(doc) + "\n")
                    calls: list = []
                    args = self.build_args(root, stage)
                    with mock.patch.object(
                            BUILDX, "_run",
                            side_effect=self.docker_runner(calls, target["candidate_id"])):
                        rc = BUILDX.cmd_build(args)
                    self.assertEqual(rc, BUILDX.EXIT_VALIDATION, name)
                    self.assertEqual(calls, [])
                    # Restore the prepared record for the next variant.
                    record_path.write_text(json.dumps(base, sort_keys=True, indent=2) + "\n")

    def test_legacy_build_without_build_input_is_not_r2_eligible(self) -> None:
        # Omission still builds locally (legacy flow preserved) but leaves
        # an explicitly unbound record that the package gate rejects with
        # zero docker calls: no silent bypass into eligibility.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target, _, handoff, stage, prepared = self.run_real_prepare(root)
            declared = prepared["companion_bundle"]
            calls: list = []
            args = self.build_args(root, stage, with_input=False, with_smoke=True)
            smoke_detail = {"profile": "core", "smokes": [
                {"name": "image_provenance", "status": "ok", "duration_ms": 1}]}
            with mock.patch.object(
                    BUILDX, "_run",
                    side_effect=self.docker_runner(calls, target["candidate_id"])), \
                    mock.patch.object(BUILDX, "run_smoke_suite",
                                      return_value=smoke_detail):
                rc = BUILDX.cmd_build(args)
            self.assertEqual(rc, 0)
            record = json.loads((root / "build-record.json").read_text())
            self.assertIsNone(record["companion_bundle"])
            self.assertIn(
                "unbound-legacy",
                record["phases"]["resolution_readback"]["detail"]["companion_status"],
            )
            docker = mock.Mock()
            with mock.patch.object(BUILD, "run_checked", docker):
                with self.assertRaises(BUILD.CandidateBuildError):
                    BUILD.package_tested_image(
                        candidate_path=stage / "config" / "paseo-candidate.json",
                        handoff_evidence_path=handoff,
                        build_record_path=root / "build-record.json",
                        archive_path=root / "image.tar",
                        evidence_path=root / "tested.json",
                        source_head="3" * 40,
                        build_input_path=stage / BUILDX.BUILD_INPUT_FILENAME,
                    )
            docker.assert_not_called()
            self.assertEqual(declared["source"], "config/pi-agent")

    def test_same_binding_survives_prepare_build_package_handoff(self) -> None:
        # End-to-end: one frozen identity flows prepare -> build record ->
        # package evidence through the normal artifact handoff.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target, _, handoff, stage, prepared = self.run_real_prepare(root)
            declared = prepared["companion_bundle"]
            calls: list = []
            args = self.build_args(root, stage, with_smoke=True)
            smoke_detail = {"profile": "core", "smokes": [
                {"name": "image_provenance", "status": "ok", "duration_ms": 1}]}
            with mock.patch.object(
                    BUILDX, "_run",
                    side_effect=self.docker_runner(calls, target["candidate_id"])), \
                    mock.patch.object(BUILDX, "run_smoke_suite",
                                      return_value=smoke_detail):
                rc = BUILDX.cmd_build(args)
            self.assertEqual(rc, 0)
            archive = root / "image.tar"

            def fake_run(argv):
                if argv[:3] == ["docker", "image", "inspect"]:
                    return mock.Mock(stdout=self.IMAGE_ID + "\n")
                if argv[:3] == ["docker", "image", "save"]:
                    archive.write_bytes(b"exact-tested-image")
                    return mock.Mock(stdout="")
                raise AssertionError(argv)

            package_docker = mock.Mock(side_effect=fake_run)
            with mock.patch.object(BUILD, "run_checked", package_docker):
                result = BUILD.package_tested_image(
                    candidate_path=stage / "config" / "paseo-candidate.json",
                    handoff_evidence_path=handoff,
                    build_record_path=root / "build-record.json",
                    archive_path=archive,
                    evidence_path=root / "tested.json",
                    source_head="3" * 40,
                    build_input_path=stage / BUILDX.BUILD_INPUT_FILENAME,
                )
            self.assertTrue(package_docker.called)
            stored_record = json.loads((root / "build-record.json").read_text())
            self.assertEqual(stored_record["companion_bundle"], declared)
            self.assertEqual(result["companion_bundle"], declared)
            stored = json.loads((root / "tested.json").read_text())
            self.assertEqual(stored["companion_bundle"]["source_digest"],
                             declared["source_digest"])
            self.assertEqual(stored["candidate_id"], target["candidate_id"])


if __name__ == "__main__":
    unittest.main()
