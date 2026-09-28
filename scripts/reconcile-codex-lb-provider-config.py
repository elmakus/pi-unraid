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
from urllib.parse import urlsplit

SCHEMA_VERSION = 1
PROVIDER_ID = "codex-lb"
PROVIDER_API = "openai-responses"
API_KEY_REFS = {"$CODEX_LB_API_KEY", "${CODEX_LB_API_KEY}"}


class ReconcileError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReconcileError(f"codex-lb provider config: {message}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_regular_file(path: Path) -> tuple[bytes, int]:
    if path.is_symlink():
        fail(f"refusing symlink: {path}")
    try:
        file_stat = path.stat()
    except FileNotFoundError:
        fail(f"configuration does not exist: {path}")
    if not stat.S_ISREG(file_stat.st_mode):
        fail(f"configuration is not a regular file: {path}")
    return path.read_bytes(), stat.S_IMODE(file_stat.st_mode)


def parse_document(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        fail("models.json is not valid UTF-8 JSON; preserved unchanged")
    if not isinstance(value, dict):
        fail("models.json root must be an object; preserved unchanged")
    return value


def valid_base_url(value: Any) -> bool:
    if not isinstance(value, str) or not value or value.strip() != value:
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        return False
    return parsed.path.rstrip("/").endswith("/v1")


def valid_model_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and value.strip() == value
        and not any(ch.isspace() or ord(ch) <= 0x1F or ord(ch) == 0x7F for ch in value)
    )


def validate_provider(doc: dict[str, Any], *, require_static: bool) -> dict[str, Any]:
    providers = doc.get("providers")
    if not isinstance(providers, dict):
        fail("models.json providers must be an object; preserved unchanged")
    provider = providers.get(PROVIDER_ID)
    if not isinstance(provider, dict):
        fail("codex-lb provider is missing or invalid; preserved unchanged")
    if provider.get("api") != PROVIDER_API:
        fail("codex-lb provider must use openai-responses; preserved unchanged")
    base_url = provider.get("baseUrl")
    if not valid_base_url(base_url):
        fail("codex-lb baseUrl must be HTTP(S), secret-free, and end in /v1; preserved unchanged")
    if provider.get("apiKey") not in API_KEY_REFS:
        fail("codex-lb apiKey must remain a CODEX_LB_API_KEY reference; preserved unchanged")

    if "models" in provider:
        models = provider["models"]
        if not isinstance(models, list) or not models:
            fail("codex-lb static models must be a non-empty array before migration")
        for item in models:
            if not isinstance(item, dict) or not valid_model_id(item.get("id")):
                fail("codex-lb static model list contains an invalid id; preserved unchanged")
    elif require_static:
        fail("codex-lb is already dynamic but no reversible migration is established")
    return provider


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


def render_without_static_models(doc: dict[str, Any]) -> bytes:
    cloned = json.loads(json.dumps(doc))
    del cloned["providers"][PROVIDER_ID]["models"]
    return (json.dumps(cloned, sort_keys=True, indent=2) + "\n").encode("utf-8")


def manifest_path(state_dir: Path) -> Path:
    return state_dir / "manifest.json"


def snapshot_path(state_dir: Path) -> Path:
    return state_dir / "models.json.before"


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


def status(models_file: Path, state_dir: Path) -> dict[str, Any]:
    raw, mode = read_regular_file(models_file)
    doc = parse_document(raw)
    provider = validate_provider(doc, require_static=False)
    manifest = load_manifest(state_dir)
    return {
        "action": "status",
        "dynamic": "models" not in provider,
        "models_sha256": sha256(raw),
        "mode": format(mode, "04o"),
        "rollback_available": manifest is not None and snapshot_path(state_dir).is_file(),
    }


def migrate(models_file: Path, state_dir: Path) -> dict[str, Any]:
    raw, mode = read_regular_file(models_file)
    doc = parse_document(raw)
    provider = validate_provider(doc, require_static=False)
    existing_manifest = load_manifest(state_dir)

    if "models" not in provider:
        if existing_manifest and existing_manifest.get("after_sha256") == sha256(raw):
            return {
                "action": "migrate",
                "changed": False,
                "dynamic": True,
                "rollback_available": snapshot_path(state_dir).is_file(),
                "models_sha256": sha256(raw),
            }
        fail("codex-lb is already dynamic without the expected rollback anchor")

    if existing_manifest is not None or state_dir.exists():
        fail("rollback state already exists; refusing to replace it")

    migrated = render_without_static_models(doc)
    migrated_doc = parse_document(migrated)
    validate_provider(migrated_doc, require_static=False)

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
        atomic_write(models_file, migrated, mode)
    except Exception:
        shutil.rmtree(state_dir, ignore_errors=True)
        raise

    return {
        "action": "migrate",
        "changed": True,
        "dynamic": True,
        "rollback_available": True,
        "before_sha256": sha256(raw),
        "models_sha256": sha256(migrated),
    }


def rollback(models_file: Path, state_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(state_dir)
    if manifest is None:
        fail("no rollback manifest is available")
    snapshot = snapshot_path(state_dir)
    snapshot_raw, _snapshot_mode = read_regular_file(snapshot)
    current_raw, _current_mode = read_regular_file(models_file)

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
        fail("current configuration changed after migration; refusing destructive rollback")

    restored_doc = parse_document(snapshot_raw)
    validate_provider(restored_doc, require_static=True)
    atomic_write(models_file, snapshot_raw, mode)
    shutil.rmtree(state_dir)
    return {
        "action": "rollback",
        "changed": True,
        "restored_prior_state": True,
        "models_sha256": sha256(snapshot_raw),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("status", "migrate", "rollback"))
    parser.add_argument("models_file", type=Path)
    parser.add_argument("state_dir", type=Path)
    args = parser.parse_args()

    try:
        result = {
            "status": status,
            "migrate": migrate,
            "rollback": rollback,
        }[args.action](args.models_file, args.state_dir)
    except ReconcileError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())