#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

MANIFEST_VERSION = 1
AGENT_REL = Path(".pi/agent")
STATE_REL = Path(".pi-unraid/instruction-plane")


def fail(message: str):
    raise SystemExit(f"pi instruction-plane error: {message}")


def parse_rel(value: str) -> Path:
    rel = Path(value)
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        fail(f"unsafe managed path: {value}")
    return rel


def safe_files(source: Path) -> list[Path]:
    if not source.is_dir():
        fail(f"source directory does not exist: {source}")
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            fail(f"symlinks are not allowed in managed source: {path}")
        if path.is_file():
            rel = parse_rel(path.relative_to(source).as_posix())
            files.append(rel)
    if not files:
        fail("managed source contains no files")
    if Path("AGENTS.md") not in files:
        fail("managed source must contain AGENTS.md")
    return files


def digest_source(source: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for rel in files:
        digest.update(rel.as_posix().encode())
        digest.update(b"\0")
        digest.update((source / rel).read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


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


def write_json(path: Path, payload: dict) -> None:
    atomic_write(path, (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode(), 0o600)


def manifest_files(manifest) -> list[Path]:
    if not isinstance(manifest, dict):
        return []
    values = manifest.get("files", [])
    if not isinstance(values, list):
        fail("managed manifest files must be a list")
    return [parse_rel(item) for item in values if isinstance(item, str)]


def target_matches(source: Path, agent: Path, files: list[Path]) -> bool:
    return all(
        (agent / rel).is_file()
        and not (agent / rel).is_symlink()
        and (agent / rel).read_bytes() == (source / rel).read_bytes()
        for rel in files
    )


def apply(source: Path, home: Path) -> dict:
    files = safe_files(source)
    source_digest = digest_source(source, files)
    agent = home / AGENT_REL
    state = home / STATE_REL
    current_path = state / "current.json"
    previous = state / "previous"
    current = load_json(current_path)

    if (
        isinstance(current, dict)
        and current.get("schema_version") == MANIFEST_VERSION
        and current.get("source_digest") == source_digest
        and current.get("files") == [path.as_posix() for path in files]
        and target_matches(source, agent, files)
    ):
        return {
            "action": "apply",
            "changed": False,
            "in_sync": True,
            "source_digest": source_digest,
            "files": len(files),
        }

    state.mkdir(parents=True, exist_ok=True)
    os.chmod(state, 0o700)
    if previous.exists():
        shutil.rmtree(previous)
    (previous / "files").mkdir(parents=True)
    os.chmod(previous, 0o700)

    prior_files = manifest_files(current)
    affected = sorted(set(prior_files) | set(files), key=lambda path: path.as_posix())
    present: list[str] = []
    modes: dict[str, int] = {}
    for rel in affected:
        target = agent / rel
        if target.is_symlink():
            fail(f"refusing to manage symlink target: {target}")
        if target.is_file():
            present.append(rel.as_posix())
            modes[rel.as_posix()] = target.stat().st_mode & 0o777
            backup = previous / "files" / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(target, backup)
            os.chmod(backup, 0o600)

    write_json(
        previous / "manifest.json",
        {
            "schema_version": MANIFEST_VERSION,
            "affected": [path.as_posix() for path in affected],
            "present": present,
            "modes": modes,
            "prior_manifest": current,
        },
    )
    os.chmod(previous, 0o700)

    for rel in prior_files:
        if rel not in files:
            target = agent / rel
            if target.is_file() and not target.is_symlink():
                target.unlink()

    agent.mkdir(parents=True, exist_ok=True)
    os.chmod(agent, 0o755)
    for rel in files:
        target = agent / rel
        if target.exists() and not target.is_file():
            fail(f"refusing to replace non-file target: {target}")
        if target.is_symlink():
            fail(f"refusing to replace symlink target: {target}")
        atomic_write(target, (source / rel).read_bytes(), 0o644)

    write_json(
        current_path,
        {
            "schema_version": MANIFEST_VERSION,
            "source_digest": source_digest,
            "files": [path.as_posix() for path in files],
        },
    )
    os.chmod(state, 0o700)
    return {
        "action": "apply",
        "changed": True,
        "in_sync": True,
        "source_digest": source_digest,
        "files": len(files),
    }


def rollback(source: Path, home: Path) -> dict:
    safe_files(source)
    agent = home / AGENT_REL
    state = home / STATE_REL
    current_path = state / "current.json"
    previous = state / "previous"
    snapshot = load_json(previous / "manifest.json")
    if not isinstance(snapshot, dict):
        fail("no rollback snapshot is available")

    current = load_json(current_path)
    current_files = manifest_files(current)
    raw_affected = snapshot.get("affected", [])
    if not isinstance(raw_affected, list):
        fail("rollback affected paths must be a list")
    affected = [parse_rel(item) for item in raw_affected if isinstance(item, str)]
    raw_present = snapshot.get("present", [])
    if not isinstance(raw_present, list):
        fail("rollback present paths must be a list")
    present = {parse_rel(item).as_posix() for item in raw_present if isinstance(item, str)}
    raw_modes = snapshot.get("modes", {})
    if not isinstance(raw_modes, dict):
        fail("rollback modes must be an object")

    for rel in sorted(set(current_files) | set(affected), key=lambda path: path.as_posix()):
        target = agent / rel
        if target.is_symlink():
            fail(f"refusing rollback through symlink target: {target}")
        if rel.as_posix() in present:
            backup = previous / "files" / rel
            if not backup.is_file():
                fail(f"rollback snapshot is incomplete for {rel}")
            mode = raw_modes.get(rel.as_posix(), 0o644)
            if not isinstance(mode, int) or mode < 0 or mode > 0o777:
                fail(f"invalid rollback mode for {rel}")
            atomic_write(target, backup.read_bytes(), mode)
        elif target.is_file():
            target.unlink()

    prior = snapshot.get("prior_manifest")
    if isinstance(prior, dict):
        write_json(current_path, prior)
    else:
        current_path.unlink(missing_ok=True)

    shutil.rmtree(previous)
    os.chmod(state, 0o700)
    return {"action": "rollback", "changed": True, "restored_prior_state": True}


def status(source: Path, home: Path) -> dict:
    files = safe_files(source)
    source_digest = digest_source(source, files)
    agent = home / AGENT_REL
    current = load_json(home / STATE_REL / "current.json")
    in_sync = (
        isinstance(current, dict)
        and current.get("schema_version") == MANIFEST_VERSION
        and current.get("source_digest") == source_digest
        and current.get("files") == [path.as_posix() for path in files]
        and target_matches(source, agent, files)
    )
    return {
        "action": "status",
        "in_sync": in_sync,
        "source_digest": source_digest,
        "files": len(files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("apply", "rollback", "status"))
    parser.add_argument("source")
    parser.add_argument("home")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    home = Path(args.home).resolve()
    if not home.is_dir():
        fail(f"HOME directory does not exist: {home}")

    handler = {"apply": apply, "rollback": rollback, "status": status}[args.action]
    print(json.dumps(handler(source, home), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
