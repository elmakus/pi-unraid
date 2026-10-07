#!/usr/bin/env python3
"""Typed OCI/platform-local/legacy predecessor mapping for M07-T06.

New accepted candidates are always OCI identities (immutable manifest
digests). The original legacy predecessor may be represented only as a
verified local image-ID plus an independently recoverable
archive/configuration anchor. A local image-ID is never a registry
manifest digest; publishing a legacy image merely to manufacture a
registry identity is forbidden.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
KINDS = ("oci", "local", "legacy")


class LegacyIdentityError(RuntimeError):
    pass


def _req_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise LegacyIdentityError(f"{label} must be an immutable sha256 identity")
    return value


def validate(record: object) -> dict:
    """Validate the typed predecessor mapping shape (no I/O)."""
    if not isinstance(record, dict):
        raise LegacyIdentityError("predecessor mapping must be an object")
    kind = record.get("kind")
    if kind not in KINDS:
        raise LegacyIdentityError("unsupported predecessor kind")
    if kind == "oci":
        _req_digest(record.get("digest"), "OCI predecessor digest")
        repo = str(record.get("repository") or "").strip().lower()
        if not repo:
            raise LegacyIdentityError("OCI predecessor repository is required")
        if set(record) - {"kind", "digest", "repository"}:
            raise LegacyIdentityError("OCI predecessor carries ambiguous extra identity")
        return {"kind": "oci", "digest": record["digest"], "repository": repo}
    if kind == "local":
        _req_digest(record.get("image_id"), "local predecessor image-ID")
        if set(record) - {"kind", "image_id", "repository"}:
            raise LegacyIdentityError("local predecessor carries ambiguous extra identity")
        out: dict = {"kind": "local", "image_id": record["image_id"]}
        if record.get("repository") is not None:
            out["repository"] = str(record["repository"]).strip().lower()
        return out
    # legacy: verified local image-ID plus independently recoverable anchor.
    _req_digest(record.get("image_id"), "legacy predecessor image-ID")
    anchor = str(record.get("archive_path") or "")
    if not anchor:
        raise LegacyIdentityError("legacy predecessor archive anchor is required")
    _req_digest(record.get("archive_sha256"), "legacy archive digest")
    _req_digest(record.get("config_digest"), "legacy configuration digest")
    state = str(record.get("state_identity") or "")
    if not state:
        raise LegacyIdentityError("legacy predecessor state identity is required")
    if set(record) - {"kind", "image_id", "archive_path", "archive_sha256",
                      "config_digest", "state_identity"}:
        raise LegacyIdentityError("legacy predecessor carries ambiguous extra identity")
    return {"kind": "legacy", "image_id": record["image_id"],
            "archive_path": anchor, "archive_sha256": record["archive_sha256"],
            "config_digest": record["config_digest"], "state_identity": state}


def verify_anchor(record: dict, *, base_dir: Path | None = None) -> dict:
    """Verify the legacy archive/configuration anchor is independently recoverable."""
    typed = validate(record)
    if typed["kind"] != "legacy":
        return typed
    anchor_path = Path(typed["archive_path"])
    if base_dir is not None and not anchor_path.is_absolute():
        anchor_path = base_dir / anchor_path
    if not anchor_path.is_file() or anchor_path.is_symlink():
        raise LegacyIdentityError("legacy archive anchor is not independently retrievable")
    actual = "sha256:" + hashlib.sha256(anchor_path.read_bytes()).hexdigest()
    if actual != typed["archive_sha256"]:
        raise LegacyIdentityError("legacy archive/config mismatch: archive bytes differ")
    # The configuration anchor is a digest binding; its bytes live in the
    # independently recoverable archive. A missing state identity cannot be
    # treated as a verified predecessor.
    if not typed["state_identity"]:
        raise LegacyIdentityError("legacy state identity is missing")
    out = dict(typed)
    out["archive_path"] = str(anchor_path.resolve())
    return out


def verify_imported_image(record: dict, *, inspect_image_id: str,
                          repo_digests: list[str] | None) -> dict:
    """Verify an imported/recovered image matches the declared local identity.

    ``inspect_image_id`` is the ``docker image inspect --format {{.Id}}``
    value; ``repo_digests`` is the parsed ``.RepoDigests`` list (may be
    empty for a never-pushed legacy image). A legacy/local image-ID used
    as a registry manifest digest is rejected: RepoDigests entries must
    not be relabeled, and a legacy image must never be published merely
    to manufacture a registry identity.
    """
    typed = validate(record)
    if typed["kind"] == "oci":
        return typed
    _req_digest(inspect_image_id, "inspected image identity")
    if inspect_image_id != typed["image_id"]:
        raise LegacyIdentityError("imported image identity mismatch")
    for entry in (repo_digests or []):
        if "@" in entry:
            manifest = entry.rsplit("@", 1)[1]
            if manifest == typed["image_id"]:
                raise LegacyIdentityError(
                    "local image-ID relabeled as manifest digest")
    return typed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    checker = sub.add_parser("validate")
    checker.add_argument("record")
    anchor = sub.add_parser("verify-anchor")
    anchor.add_argument("record")
    anchor.add_argument("--base-dir", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        if args.cmd == "validate":
            out = validate(record)
        else:
            out = verify_anchor(record, base_dir=args.base_dir)
        print(json.dumps(out, sort_keys=True))
        return 0
    except (LegacyIdentityError, OSError, ValueError) as exc:
        print(f"legacy identity failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
