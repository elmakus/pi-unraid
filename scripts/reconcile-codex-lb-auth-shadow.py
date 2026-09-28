#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PROVIDER_ID = "codex-lb"


class ReconcileError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReconcileError(f"codex-lb auth shadow: {message}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_regular_file(path: Path) -> tuple[bytes, int] | None:
    if path.is_symlink():
        fail(f"refusing symlink: {path}")
    try:
        file_stat = path.stat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(file_stat.st_mode):
        fail(f"auth store is not a regular file: {path}")
    return path.read_bytes(), stat.S_IMODE(file_stat.st_mode)


def parse_document(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        fail("auth.json is not valid UTF-8 JSON; preserved unchanged")
    if not isinstance(value, dict):
        fail("auth.json root must be an object; preserved unchanged")
    return value


def validate_shadow(doc: dict[str, Any]) -> bool:
    if PROVIDER_ID not in doc:
        return False
    entry = doc[PROVIDER_ID]
    if not isinstance(entry, dict):
        fail("codex-lb auth entry is invalid; preserved unchanged")
    if entry.get("type") != "api_key":
        fail("codex-lb auth entry is not an api_key; preserved unchanged")
    key = entry.get("key")
    if not isinstance(key, str) or not key:
        fail("codex-lb auth entry has no usable key; preserved unchanged")
    return True


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def write_secret_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(
        path,
        (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        0o600,
    )


def manifest_path(state_dir: Path) -> Path:
    return state_dir / "manifest.json"


def snapshot_path(state_dir: Path) -> Path:
    return state_dir / "auth.json.before"


def load_manifest(state_dir: Path) -> dict[str, Any] | None:
    path = manifest_path(state_dir)
    if not path.exists():
        return None
    if path.is_symlink():
        fail("rollback manifest is a symlink")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        fail("rollback manifest is invalid")
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        fail("rollback manifest has an unsupported schema")
    return value


def render_without_shadow(doc: dict[str, Any]) -> bytes:
    cloned = json.loads(json.dumps(doc))
    cloned.pop(PROVIDER_ID, None)
    return (json.dumps(cloned, sort_keys=True, indent=2) + "\n").encode("utf-8")


def status(auth_file: Path, state_dir: Path) -> dict[str, Any]:
    loaded = read_regular_file(auth_file)
    manifest = load_manifest(state_dir)
    if loaded is None:
        return {
            "action": "status",
            "auth_present": False,
            "shadow_present": False,
            "auth_sha256": None,
            "rollback_available": manifest is not None and snapshot_path(state_dir).is_file(),
        }
    raw, mode = loaded
    doc = parse_document(raw)
    shadow = validate_shadow(doc)
    return {
        "action": "status",
        "auth_present": True,
        "shadow_present": shadow,
        "auth_sha256": sha256(raw),
        "mode": format(mode, "04o"),
        "rollback_available": manifest is not None and snapshot_path(state_dir).is_file(),
    }


def migrate(auth_file: Path, state_dir: Path) -> dict[str, Any]:
    loaded = read_regular_file(auth_file)
    if loaded is None:
        if state_dir.exists():
            fail("rollback state exists while auth.json is absent")
        return {
            "action": "migrate",
            "changed": False,
            "shadow_removed": False,
            "auth_present": False,
            "rollback_available": False,
        }

    raw, mode = loaded
    doc = parse_document(raw)
    if not validate_shadow(doc):
        if state_dir.exists():
            fail("rollback state exists but codex-lb auth shadow is already absent")
        return {
            "action": "migrate",
            "changed": False,
            "shadow_removed": False,
            "auth_present": True,
            "rollback_available": False,
            "auth_sha256": sha256(raw),
        }

    if state_dir.exists():
        fail("rollback state already exists; refusing to replace it")

    migrated = render_without_shadow(doc)
    migrated_doc = parse_document(migrated)
    if validate_shadow(migrated_doc):
        fail("codex-lb auth shadow remained after migration")

    state_dir.mkdir(parents=True, mode=0o700)
    os.chmod(state_dir, 0o700)
    atomic_write(snapshot_path(state_dir), raw, 0o600)
    write_secret_json(
        manifest_path(state_dir),
        {
            "schema_version": SCHEMA_VERSION,
            "before_sha256": sha256(raw),
            "after_sha256": sha256(migrated),
            "mode": mode,
        },
    )
    try:
        atomic_write(auth_file, migrated, mode)
    except Exception:
        shutil.rmtree(state_dir, ignore_errors=True)
        raise

    return {
        "action": "migrate",
        "changed": True,
        "shadow_removed": True,
        "auth_present": True,
        "rollback_available": True,
        "before_sha256": sha256(raw),
        "auth_sha256": sha256(migrated),
    }


def rollback(auth_file: Path, state_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(state_dir)
    if manifest is None:
        fail("no rollback manifest is available")
    snap = snapshot_path(state_dir)
    snap_loaded = read_regular_file(snap)
    current_loaded = read_regular_file(auth_file)
    if snap_loaded is None or current_loaded is None:
        fail("rollback snapshot/current auth store is unavailable")
    snapshot_raw, _ = snap_loaded
    current_raw, _ = current_loaded

    before_sha = manifest.get("before_sha256")
    after_sha = manifest.get("after_sha256")
    mode = manifest.get("mode")
    if not isinstance(before_sha, str) or not isinstance(after_sha, str):
        fail("rollback manifest is incomplete")
    if not isinstance(mode, int) or mode < 0 or mode > 0o777:
        fail("rollback manifest contains an invalid mode")
    if sha256(snapshot_raw) != before_sha:
        fail("rollback snapshot integrity check failed")
    if sha256(current_raw) != after_sha:
        fail("current auth store changed after migration; refusing destructive rollback")

    restored = parse_document(snapshot_raw)
    if not validate_shadow(restored):
        fail("rollback snapshot does not contain the prior codex-lb auth entry")

    atomic_write(auth_file, snapshot_raw, mode)
    shutil.rmtree(state_dir)
    return {
        "action": "rollback",
        "changed": True,
        "restored_prior_state": True,
        "auth_sha256": sha256(snapshot_raw),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("status", "migrate", "rollback"))
    parser.add_argument("auth_file", type=Path)
    parser.add_argument("state_dir", type=Path)
    args = parser.parse_args()
    try:
        result = {
            "status": status,
            "migrate": migrate,
            "rollback": rollback,
        }[args.action](args.auth_file, args.state_dir)
    except ReconcileError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
