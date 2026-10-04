#!/usr/bin/env python3
"""Prepare and package one exact M03 candidate build without re-resolution."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SCHEMA_VERSION = 1


class CandidateBuildError(RuntimeError):
    pass


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def load_json_bytes(path: Path) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateBuildError(f"unreadable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise CandidateBuildError(f"JSON object required: {path}")
    return value, raw


def load_buildx(root: Path):
    path = root / "scripts" / "paseo_buildx.py"
    spec = importlib.util.spec_from_file_location("paseo_buildx_candidate_stage", path)
    if spec is None or spec.loader is None:
        raise CandidateBuildError(f"cannot load build verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPANION_SOURCE_REL = Path("config/pi-agent")
COMPANION_SCHEMA_VERSION = 1


def load_instruction_plane():
    # Installer rules come from this builder's own tooling (not from the
    # candidate source under inspection) so the declared identity is exactly
    # what ``apply`` enforces.
    path = Path(__file__).resolve().parent / "pi_instruction_plane.py"
    spec = importlib.util.spec_from_file_location("pi_instruction_plane_companion_stage", path)
    if spec is None or spec.loader is None:
        raise CandidateBuildError(f"cannot load instruction-plane installer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def companion_bundle_identity(source_root: Path) -> dict:
    """Declare the frozen companion policy/provider/instruction bundle.

    The identity (file set, per-path modes, content digest) is computed with
    the installer's own ``safe_files``/``managed_mode``/``digest_source`` so
    the declared binding is exactly what ``apply`` enforces: ``bin/*`` tools
    deploy as ``0755``, every other instruction file as ``0644``. The payload
    itself is delivered by the instruction plane from this frozen source, not
    by the image; this record binds the image inputs and the companion to one
    source state for eligibility. Secret-free: paths, modes and digests only.
    """
    try:
        installer = load_instruction_plane()
        source = source_root / COMPANION_SOURCE_REL
        files = installer.safe_files(source)
        modes = {rel.as_posix(): f"{installer.managed_mode(rel):04o}" for rel in files}
        digest = installer.digest_source(source, files)
    except CandidateBuildError:
        raise
    except (SystemExit, Exception) as exc:
        # Installer refuses unsafe/missing sources via SystemExit; either way
        # the bundle is unverifiable and must fail closed, never bind.
        raise CandidateBuildError(f"companion bundle is unverifiable: {exc}") from exc
    return {
        "schema_version": COMPANION_SCHEMA_VERSION,
        "source": COMPANION_SOURCE_REL.as_posix(),
        "files": [rel.as_posix() for rel in files],
        "modes": modes,
        "source_digest": digest,
    }


def verify_companion_binding(source_root: Path, declared: dict) -> dict:
    """Fail closed unless the source tree matches the declared binding.

    Changed content, added/removed files, wrong modes, wrong digest, missing
    source or malformed declarations never preserve the same binding: each
    raises ``CandidateBuildError`` instead of reporting bound state.
    """
    if not isinstance(declared, dict):
        raise CandidateBuildError("companion binding declaration must be an object")
    if declared.get("schema_version") != COMPANION_SCHEMA_VERSION:
        raise CandidateBuildError("companion binding schema is unsupported")
    if declared.get("source") != COMPANION_SOURCE_REL.as_posix():
        raise CandidateBuildError("companion binding source is not the frozen instruction bundle")
    declared_files = declared.get("files")
    declared_modes = declared.get("modes")
    declared_digest = declared.get("source_digest")
    if not isinstance(declared_files, list) or not all(isinstance(item, str) for item in declared_files):
        raise CandidateBuildError("companion binding files must be a list of paths")
    if not isinstance(declared_modes, dict) or not isinstance(declared_digest, str):
        raise CandidateBuildError("companion binding modes/digest are malformed")
    actual = companion_bundle_identity(source_root)
    if actual["files"] != declared_files:
        missing = sorted(set(declared_files) - set(actual["files"]))
        added = sorted(set(actual["files"]) - set(declared_files))
        raise CandidateBuildError(
            f"companion bundle file set changed (missing={missing} added={added})"
        )
    mismatched = sorted(
        rel for rel in declared_files if actual["modes"].get(rel) != declared_modes.get(rel)
    )
    if mismatched:
        raise CandidateBuildError(f"companion bundle modes changed: {mismatched}")
    if actual["source_digest"] != declared_digest:
        raise CandidateBuildError("companion bundle digest mismatch")
    return {
        "status": "bound",
        "source": actual["source"],
        "source_digest": actual["source_digest"],
        "files": len(actual["files"]),
    }


def verify_handoff(
    candidate_path: Path,
    evidence_path: Path,
    accepted_path: Path,
    *,
    source_parent: str,
    expected_source_ref: str,
) -> tuple[dict, bytes, dict, bytes, dict]:
    candidate, candidate_raw = load_json_bytes(candidate_path)
    evidence, evidence_raw = load_json_bytes(evidence_path)
    accepted, _ = load_json_bytes(accepted_path)

    candidate_id = str(candidate.get("candidate_id") or "")
    accepted_id = str(accepted.get("candidate_id") or "")
    if not SHA256.fullmatch(candidate_id) or not SHA256.fullmatch(accepted_id):
        raise CandidateBuildError("candidate identities must be immutable sha256 values")
    if evidence.get("schema_version") != 1 or evidence.get("status") != "update":
        raise CandidateBuildError("handoff evidence is not a material-change record")
    if evidence.get("candidate_id") != candidate_id:
        raise CandidateBuildError("handoff candidate identity mismatch")
    if evidence.get("accepted_candidate_id") != accepted_id:
        raise CandidateBuildError("handoff accepted-candidate identity mismatch")
    if candidate_id == accepted_id:
        raise CandidateBuildError("material-change handoff cannot equal the accepted candidate")
    if evidence.get("candidate_file_sha256") != sha256_bytes(candidate_raw):
        raise CandidateBuildError("handoff candidate byte digest mismatch")
    if evidence.get("source_sha") != source_parent:
        raise CandidateBuildError("candidate branch parent does not match frozen discovery source SHA")
    if evidence.get("source_ref") != expected_source_ref:
        raise CandidateBuildError("candidate discovery source ref is not the expected default branch")
    return candidate, candidate_raw, evidence, evidence_raw, accepted


def _component(candidate: dict, name: str) -> dict:
    try:
        value = candidate["components"][name]
    except (KeyError, TypeError) as exc:
        raise CandidateBuildError(f"candidate lacks component {name}") from exc
    if not isinstance(value, dict):
        raise CandidateBuildError(f"candidate component is invalid: {name}")
    return value


def replace_exact(text: str, old: str, new: str, description: str) -> str:
    if old == new:
        if old not in text:
            raise CandidateBuildError(f"Dockerfile lacks accepted {description}")
        return text
    count = text.count(old)
    if count != 1:
        raise CandidateBuildError(
            f"Dockerfile accepted {description} must occur exactly once; found {count}"
        )
    return text.replace(old, new, 1)


def render_dockerfile(text: str, accepted: dict, candidate: dict) -> str:
    """Render only candidate-bound Dockerfile literals from accepted to candidate."""
    a = accepted
    c = candidate

    mappings: list[tuple[str, str, str]] = [
        (
            f"FROM {_component(a, 'paseo')['artifact']['reference']}",
            f"FROM {_component(c, 'paseo')['artifact']['reference']}",
            "Paseo parent reference",
        ),
        (
            f'io.pi-unraid.candidate-id="{a["candidate_id"]}"',
            f'io.pi-unraid.candidate-id="{c["candidate_id"]}"',
            "candidate label",
        ),
        (
            f'PI_UNRAID_CANDIDATE_ID="{a["candidate_id"]}"',
            f'PI_UNRAID_CANDIDATE_ID="{c["candidate_id"]}"',
            "candidate environment identity",
        ),
    ]

    label_components = (
        ("paseo", "io.pi-unraid.paseo-version"),
        ("pi", "io.pi-unraid.pi-version"),
        ("specpi", "io.pi-unraid.specpi-version"),
        ("pi_mcp_adapter", "io.pi-unraid.pi-mcp-adapter-version"),
        ("playwright", "io.pi-unraid.playwright-version"),
    )
    for name, label in label_components:
        mappings.append(
            (
                f'{label}="{_component(a, name)["version"]}"',
                f'{label}="{_component(c, name)["version"]}"',
                f"{name} label",
            )
        )

    env_components = (
        ("pi", "PI_UNRAID_PI_VERSION"),
        ("specpi", "PI_UNRAID_SPECPI_VERSION"),
        ("pi_mcp_adapter", "PI_UNRAID_PI_MCP_ADAPTER_VERSION"),
        ("playwright", "PI_UNRAID_PLAYWRIGHT_VERSION"),
        ("github_cli", "PI_UNRAID_GH_VERSION"),
        ("docker_cli", "PI_UNRAID_DOCKER_CLI_VERSION"),
        ("docker_compose", "PI_UNRAID_DOCKER_COMPOSE_VERSION"),
    )
    for name, env_name in env_components:
        mappings.append(
            (
                f'{env_name}="{_component(a, name)["version"]}"',
                f'{env_name}="{_component(c, name)["version"]}"',
                f"{name} environment version",
            )
        )

    for old, new, description in mappings:
        text = replace_exact(text, old, new, description)

    for name in ("github_cli", "docker_compose"):
        old_digest = _component(a, name)["artifact"]["digest"].removeprefix("sha256:")
        new_digest = _component(c, name)["artifact"]["digest"].removeprefix("sha256:")
        text = replace_exact(text, old_digest, new_digest, f"{name} artifact digest")

    return text


def prepare_context(
    *,
    candidate_path: Path,
    evidence_path: Path,
    accepted_path: Path,
    source_root: Path,
    stage_dir: Path,
    source_head: str,
    source_parent: str,
    expected_source_ref: str,
) -> dict:
    if stage_dir.exists():
        raise CandidateBuildError(f"stage directory already exists: {stage_dir}")
    if not source_head.strip() or not source_parent.strip():
        raise CandidateBuildError("source head/parent are required")

    candidate, candidate_raw, evidence, evidence_raw, accepted = verify_handoff(
        candidate_path,
        evidence_path,
        accepted_path,
        source_parent=source_parent,
        expected_source_ref=expected_source_ref,
    )
    dockerfile_path = source_root / "Dockerfile"
    try:
        original_dockerfile = dockerfile_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CandidateBuildError(f"source Dockerfile is unreadable: {dockerfile_path}") from exc

    rendered = render_dockerfile(original_dockerfile, accepted, candidate)
    shutil.copytree(
        source_root,
        stage_dir,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )
    staged_dockerfile = stage_dir / "Dockerfile"
    staged_dockerfile.write_text(rendered, encoding="utf-8")
    staged_candidate = stage_dir / "config" / "paseo-candidate.json"
    staged_candidate.write_bytes(candidate_raw)

    buildx = load_buildx(source_root)
    try:
        readback = buildx.verify_build_inputs(candidate, rendered, stage_dir)
    except Exception as exc:
        raise CandidateBuildError(f"rendered context failed exact build-input verification: {exc}") from exc

    companion = companion_bundle_identity(source_root)
    # Enforce the declared binding against the actual staged payload before
    # any record is written: a divergent staged copy fails here, not downstream.
    verify_companion_binding(stage_dir, companion)
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "prepared",
        "candidate_id": candidate["candidate_id"],
        "accepted_candidate_id": accepted["candidate_id"],
        "candidate_file_sha256": sha256_bytes(candidate_raw),
        "handoff_evidence_sha256": sha256_bytes(evidence_raw),
        "source_head": source_head,
        "source_parent": source_parent,
        "source_ref": evidence["source_ref"],
        "stage_dir": str(stage_dir),
        "build_readback": readback,
        "companion_bundle": companion,
    }
    (stage_dir / ".pi-unraid-candidate-build-input.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def run_checked(argv: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CandidateBuildError(f"command failed to execute: {argv[0]}") from exc
    if proc.returncode != 0:
        raise CandidateBuildError(
            f"command failed ({proc.returncode}): {' '.join(argv)}: "
            f"{(proc.stderr or proc.stdout)[-2000:]}"
        )
    return proc


def package_tested_image(
    *,
    candidate_path: Path,
    handoff_evidence_path: Path,
    build_record_path: Path,
    archive_path: Path,
    evidence_path: Path,
    source_head: str,
    build_input_path: Path | None = None,
) -> dict:
    candidate, candidate_raw = load_json_bytes(candidate_path)
    handoff, handoff_raw = load_json_bytes(handoff_evidence_path)
    record, record_raw = load_json_bytes(build_record_path)

    candidate_id = candidate.get("candidate_id")
    if not SHA256.fullmatch(str(candidate_id or "")):
        raise CandidateBuildError("candidate identity is invalid")
    if handoff.get("candidate_id") != candidate_id:
        raise CandidateBuildError("build package handoff candidate mismatch")
    if handoff.get("candidate_file_sha256") != sha256_bytes(candidate_raw):
        raise CandidateBuildError("build package candidate byte digest mismatch")
    if (record.get("candidate") or {}).get("candidate_id") != candidate_id:
        raise CandidateBuildError("build record candidate mismatch")
    phases = record.get("phases") or {}
    for phase in ("resolution_readback", "builder_ensure", "build", "test"):
        if (phases.get(phase) or {}).get("status") != "ok":
            raise CandidateBuildError(f"build record phase is not GREEN: {phase}")

    tag = str(record.get("tag") or "")
    image_id = str((record.get("image") or {}).get("id") or "")
    if not tag or not SHA256.fullmatch(image_id):
        raise CandidateBuildError("build record lacks exact tested image identity")

    companion_declared = None
    if build_input_path is not None:
        # Retain and check the prepared companion declaration through the
        # package evidence before any external action: a missing/malformed
        # declaration or an inconsistent candidate linkage fails here, before
        # any docker invocation. Omitted input preserves the prior behavior.
        try:
            build_input = json.loads(Path(build_input_path).read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise CandidateBuildError(f"build-input record is unreadable: {exc}") from exc
        if not isinstance(build_input, dict):
            raise CandidateBuildError("build-input record must be an object")
        if build_input.get("candidate_id") != candidate_id:
            raise CandidateBuildError("build-input record candidate mismatch")
        companion_declared = build_input.get("companion_bundle")
        if not isinstance(companion_declared, dict):
            raise CandidateBuildError("build-input record lacks companion bundle declaration")
        if companion_declared.get("schema_version") != COMPANION_SCHEMA_VERSION:
            raise CandidateBuildError("build-input companion declaration schema is unsupported")
        for key in ("source", "files", "modes", "source_digest"):
            if key not in companion_declared:
                raise CandidateBuildError(
                    f"build-input companion declaration lacks {key}"
                )

    before = run_checked(["docker", "image", "inspect", tag, "--format", "{{.Id}}"]).stdout.strip()
    if before != image_id:
        raise CandidateBuildError("local tested image no longer matches build record")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        raise CandidateBuildError(f"image archive already exists: {archive_path}")
    run_checked(["docker", "image", "save", "-o", str(archive_path), tag])
    after = run_checked(["docker", "image", "inspect", tag, "--format", "{{.Id}}"]).stdout.strip()
    if after != image_id:
        raise CandidateBuildError("local image identity changed while preserving tested artifact")

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "tested_image_preserved",
        "candidate_id": candidate_id,
        "accepted_candidate_id": handoff.get("accepted_candidate_id"),
        "candidate_file_sha256": sha256_bytes(candidate_raw),
        "handoff_evidence_sha256": sha256_bytes(handoff_raw),
        "build_record_sha256": sha256_bytes(record_raw),
        "image_id": image_id,
        "image_archive_format": "docker-save",
        "image_archive_sha256": sha256_file(archive_path),
        "source_head": source_head,
        "discovery_source_sha": handoff.get("source_sha"),
        "discovery_source_ref": handoff.get("source_ref"),
    }
    if companion_declared is not None:
        result["companion_bundle"] = companion_declared
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--candidate", type=Path, required=True)
    prepare.add_argument("--handoff-evidence", type=Path, required=True)
    prepare.add_argument("--accepted", type=Path, required=True)
    prepare.add_argument("--source-root", type=Path, required=True)
    prepare.add_argument("--stage-dir", type=Path, required=True)
    prepare.add_argument("--source-head", required=True)
    prepare.add_argument("--source-parent", required=True)
    prepare.add_argument("--expected-source-ref", required=True)

    package = sub.add_parser("package")
    package.add_argument("--candidate", type=Path, required=True)
    package.add_argument("--handoff-evidence", type=Path, required=True)
    package.add_argument("--build-record", type=Path, required=True)
    package.add_argument("--archive", type=Path, required=True)
    package.add_argument("--evidence", type=Path, required=True)
    package.add_argument("--source-head", required=True)
    package.add_argument(
        "--build-input",
        type=Path,
        default=None,
        help="optional prepare-stage build-input record carrying the companion bundle declaration",
    )

    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_context(
                candidate_path=args.candidate,
                evidence_path=args.handoff_evidence,
                accepted_path=args.accepted,
                source_root=args.source_root,
                stage_dir=args.stage_dir,
                source_head=args.source_head,
                source_parent=args.source_parent,
                expected_source_ref=args.expected_source_ref,
            )
        else:
            result = package_tested_image(
                candidate_path=args.candidate,
                handoff_evidence_path=args.handoff_evidence,
                build_record_path=args.build_record,
                archive_path=args.archive,
                evidence_path=args.evidence,
                source_head=args.source_head,
                build_input_path=args.build_input,
            )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CandidateBuildError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"candidate build handoff failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
