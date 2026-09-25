#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,}$")


def fail(message: str) -> None:
    print(json.dumps({"ok": False, "error": message}, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)


def fingerprint(key: str) -> str:
    return "sha256:" + hashlib.sha256(key.encode()).hexdigest()[:16]


def validate_target(path: Path) -> None:
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        fail("credential parent must be an existing non-symlink directory")
    if path.is_symlink():
        fail("credential target must not be a symlink")
    if path.exists() and not path.is_file():
        fail("credential target must be a regular file")


def read_secret() -> str:
    if sys.stdin.isatty():
        value = getpass.getpass("Unraid API key: ")
    else:
        value = sys.stdin.read().strip()
    if not KEY_PATTERN.fullmatch(value):
        fail("invalid Unraid API key format")
    return value


def atomic_write(path: Path, value: str) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(value + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def status(path: Path) -> dict:
    validate_target(path)
    if not path.exists():
        return {"ok": True, "present": False}
    st = path.stat()
    mode = stat.S_IMODE(st.st_mode)
    value = path.read_text().strip()
    valid = bool(KEY_PATTERN.fullmatch(value))
    return {
        "ok": True,
        "present": True,
        "valid_format": valid,
        "mode": format(mode, "03o"),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "private_mode": (mode & 0o077) == 0,
        "fingerprint": fingerprint(value) if valid else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "status"))
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    path = Path(args.path)

    if args.action == "status":
        print(json.dumps(status(path), sort_keys=True))
        return 0

    validate_target(path)
    value = read_secret()
    before = status(path)
    if (
        before.get("present")
        and before.get("valid_format")
        and path.read_text().strip() == value
        and before.get("private_mode")
    ):
        print(
            json.dumps(
                {
                    "ok": True,
                    "changed": False,
                    "fingerprint": fingerprint(value),
                    "mode": before.get("mode"),
                },
                sort_keys=True,
            )
        )
        return 0

    atomic_write(path, value)
    after = status(path)
    if not after.get("valid_format") or not after.get("private_mode"):
        fail("credential write did not pass readback")
    print(
        json.dumps(
            {
                "ok": True,
                "changed": True,
                "fingerprint": after["fingerprint"],
                "mode": after["mode"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
