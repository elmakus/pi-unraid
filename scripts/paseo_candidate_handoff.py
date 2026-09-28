#!/usr/bin/env python3
"""Prepare a deterministic non-production candidate handoff for M03-T01."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SCHEMA_VERSION = 1


class HandoffError(RuntimeError):
    pass


def load_candidate(path: Path) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffError(f"candidate is unreadable: {path}") from exc
    candidate_id = data.get("candidate_id") if isinstance(data, dict) else None
    if not SHA256.fullmatch(str(candidate_id or "")):
        raise HandoffError(f"candidate has invalid candidate_id: {path}")
    return data, raw


def prepare(candidate_path: Path, accepted_path: Path, stage_dir: Path, source_sha: str, source_ref: str) -> dict:
    candidate, raw = load_candidate(candidate_path)
    accepted, _ = load_candidate(accepted_path)
    candidate_id = candidate["candidate_id"]
    accepted_id = accepted["candidate_id"]
    status = "no_op" if candidate_id == accepted_id else "update"
    result = {"status": status, "candidate_id": candidate_id, "accepted_candidate_id": accepted_id}
    if status == "no_op":
        return result
    if not source_sha.strip() or not source_ref.strip():
        raise HandoffError("update handoff requires source SHA and ref")
    stage_dir.mkdir(parents=True, exist_ok=False)
    candidate_target = stage_dir / "candidate.json"
    candidate_target.write_bytes(raw)
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "status": "update",
        "candidate_id": candidate_id,
        "accepted_candidate_id": accepted_id,
        "candidate_file_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "source_sha": source_sha,
        "source_ref": source_ref,
    }
    (stage_dir / "evidence.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return result


def write_github_output(path: Path | None, result: dict) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8") as handle:
        for key in ("status", "candidate_id", "accepted_candidate_id"):
            handle.write(f"{key}={result[key]}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare one exact candidate handoff only on material change.")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--accepted", type=Path, required=True)
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        if args.stage_dir.exists():
            raise HandoffError(f"stage directory already exists: {args.stage_dir}")
        result = prepare(args.candidate, args.accepted, args.stage_dir, args.source_sha, args.source_ref)
        write_github_output(args.github_output, result)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (HandoffError, OSError, TypeError, ValueError) as exc:
        print(f"candidate handoff failed: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
