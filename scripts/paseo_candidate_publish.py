#!/usr/bin/env python3
"""Publish one preserved M03 tested image to GHCR without rebuilding it."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
GHCR_REPOSITORY = re.compile(r"^ghcr\.io/[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?/[a-z0-9][a-z0-9._/-]*$")
SCHEMA_VERSION = 1


class CandidatePublishError(RuntimeError):
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
        raise CandidatePublishError(f"unreadable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise CandidatePublishError(f"JSON object required: {path}")
    return value, raw


def run_checked(argv: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CandidatePublishError(f"command failed to execute: {argv[0]}") from exc
    if proc.returncode != 0:
        raise CandidatePublishError(
            f"command failed ({proc.returncode}): {' '.join(argv)}: "
            f"{(proc.stderr or proc.stdout)[-2000:]}"
        )
    return proc


def parse_registry_digest(output: str) -> str:
    for line in output.splitlines():
        fields = line.strip().split()
        if len(fields) == 2 and fields[0] == "Digest:" and SHA256.fullmatch(fields[1]):
            return fields[1]
    raise CandidatePublishError("registry readback did not expose one OCI digest")


def verify_inputs(
    *,
    artifact_dir: Path,
    candidate_path: Path,
    handoff_path: Path,
    source_head: str,
) -> tuple[dict, dict, dict, dict, bytes, bytes, bytes]:
    if not GIT_SHA.fullmatch(source_head):
        raise CandidatePublishError("exact 40-hex candidate source head is required")

    candidate, candidate_raw = load_json_bytes(candidate_path)
    handoff, handoff_raw = load_json_bytes(handoff_path)
    record, record_raw = load_json_bytes(artifact_dir / "build-record.json")
    tested, tested_raw = load_json_bytes(artifact_dir / "tested-image-evidence.json")
    archive = artifact_dir / "image.tar"

    candidate_id = str(candidate.get("candidate_id") or "")
    image_id = str((record.get("image") or {}).get("id") or "")
    if not SHA256.fullmatch(candidate_id) or not SHA256.fullmatch(image_id):
        raise CandidatePublishError("candidate or tested image identity is invalid")
    if tested.get("status") != "tested_image_preserved":
        raise CandidatePublishError("tested-image handoff is not publishable")
    if tested.get("candidate_id") != candidate_id or handoff.get("candidate_id") != candidate_id:
        raise CandidatePublishError("candidate identity mismatch")
    if tested.get("accepted_candidate_id") != handoff.get("accepted_candidate_id"):
        raise CandidatePublishError("accepted-candidate identity mismatch")
    if tested.get("candidate_file_sha256") != sha256_bytes(candidate_raw):
        raise CandidatePublishError("candidate byte digest mismatch")
    if tested.get("handoff_evidence_sha256") != sha256_bytes(handoff_raw):
        raise CandidatePublishError("handoff evidence byte digest mismatch")
    if tested.get("build_record_sha256") != sha256_bytes(record_raw):
        raise CandidatePublishError("build record byte digest mismatch")
    if (record.get("candidate") or {}).get("candidate_id") != candidate_id:
        raise CandidatePublishError("build record candidate mismatch")
    if tested.get("image_id") != image_id:
        raise CandidatePublishError("tested image ID mismatch")
    if tested.get("source_head") != source_head:
        raise CandidatePublishError("tested image source head mismatch")
    if tested.get("discovery_source_sha") != handoff.get("source_sha"):
        raise CandidatePublishError("discovery source SHA mismatch")
    if tested.get("discovery_source_ref") != handoff.get("source_ref"):
        raise CandidatePublishError("discovery source ref mismatch")
    if not archive.is_file() or tested.get("image_archive_sha256") != sha256_file(archive):
        raise CandidatePublishError("tested image archive hash mismatch")

    return candidate, handoff, record, tested, candidate_raw, record_raw, tested_raw


def publish(
    *,
    artifact_dir: Path,
    candidate_path: Path,
    handoff_path: Path,
    source_head: str,
    repository: str,
    output_path: Path,
) -> dict:
    repository = repository.strip().lower()
    if not GHCR_REPOSITORY.fullmatch(repository) or ":accepted" in repository:
        raise CandidatePublishError("repository must be an untagged ghcr.io namespace/image path")

    candidate, handoff, record, tested, candidate_raw, record_raw, tested_raw = verify_inputs(
        artifact_dir=artifact_dir,
        candidate_path=candidate_path,
        handoff_path=handoff_path,
        source_head=source_head,
    )
    candidate_id = candidate["candidate_id"]
    image_id = tested["image_id"]
    local_tag = str(record.get("tag") or "")
    if not local_tag:
        raise CandidatePublishError("build record lacks local tested-image tag")

    archive = artifact_dir / "image.tar"
    run_checked(["docker", "image", "load", "-i", str(archive)])
    loaded_id = run_checked(
        ["docker", "image", "inspect", local_tag, "--format", "{{.Id}}"]
    ).stdout.strip()
    if loaded_id != image_id:
        raise CandidatePublishError("loaded image does not match tested image ID")

    candidate_ref = f"{repository}:candidate-{candidate_id.removeprefix('sha256:')}"
    run_checked(["docker", "image", "tag", local_tag, candidate_ref])
    run_checked(["docker", "image", "push", candidate_ref])

    first = run_checked(["docker", "buildx", "imagetools", "inspect", candidate_ref]).stdout
    digest = parse_registry_digest(first)
    immutable_ref = f"{repository}@{digest}"
    second = run_checked(["docker", "buildx", "imagetools", "inspect", immutable_ref]).stdout
    readback_digest = parse_registry_digest(second)
    if readback_digest != digest:
        raise CandidatePublishError("immutable registry digest readback mismatch")

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "published",
        "candidate_id": candidate_id,
        "accepted_candidate_id": handoff.get("accepted_candidate_id"),
        "source_head": source_head,
        "discovery_source_sha": handoff.get("source_sha"),
        "discovery_source_ref": handoff.get("source_ref"),
        "candidate_file_sha256": sha256_bytes(candidate_raw),
        "handoff_evidence_sha256": tested["handoff_evidence_sha256"],
        "build_record_sha256": sha256_bytes(record_raw),
        "tested_image_evidence_sha256": sha256_bytes(tested_raw),
        "image_id": image_id,
        "image_archive_sha256": tested["image_archive_sha256"],
        "repository": repository,
        "candidate_ref": candidate_ref,
        "digest": digest,
        "immutable_ref": immutable_ref,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    publish_parser = sub.add_parser("publish")
    publish_parser.add_argument("--artifact-dir", type=Path, required=True)
    publish_parser.add_argument("--candidate", type=Path, required=True)
    publish_parser.add_argument("--handoff-evidence", type=Path, required=True)
    publish_parser.add_argument("--source-head", required=True)
    publish_parser.add_argument("--repository", required=True)
    publish_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = publish(
            artifact_dir=args.artifact_dir,
            candidate_path=args.candidate,
            handoff_path=args.handoff_evidence,
            source_head=args.source_head,
            repository=args.repository,
            output_path=args.output,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CandidatePublishError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"candidate publication failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
