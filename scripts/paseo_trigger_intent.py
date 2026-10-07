#!/usr/bin/env python3
"""Crash-safe narrow trigger-intent record for the Update + Verify action.

The intent file is guard-local (a sibling of the exact guard file), not a
universal action ledger. It records that the fixed-target trigger was
issued for one guard binding so a helper restart that observes an
uncertain trigger occurrence reads back the intent instead of blindly
reissuing a second update. Interruption before the trigger leaves no
intent (safe to trigger); interruption after the trigger leaves a
durable intent (observe only, never re-trigger).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

SCHEMA_VERSION = 1
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class TriggerIntentError(RuntimeError):
    pass


def intent_path_for(guard_path: Path) -> Path:
    """Return the guard-local intent sibling path (no universal store)."""
    guard_path = Path(guard_path)
    return guard_path.parent / (guard_path.name + ".trigger-intent")


def _req_binding(value: object) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise TriggerIntentError("trigger intent binding must be an immutable digest")
    return value


def readback(guard_path: Path, binding: str) -> dict | None:
    """Read back the narrow intent without creating one.

    Returns None when no trigger was issued for this guard (safe to
    trigger), the intent record when a trigger may already have occurred
    (observe only), and raises on a stale/corrupt binding.
    """
    binding = _req_binding(binding)
    path = intent_path_for(guard_path)
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TriggerIntentError("trigger intent is corrupt; observe, never reissue") from exc
    if not isinstance(record, dict) or record.get("schema_version") != SCHEMA_VERSION:
        raise TriggerIntentError("trigger intent uses an unsupported schema")
    if record.get("binding_digest") != binding:
        raise TriggerIntentError("stale trigger intent binding")
    if record.get("intent") != "trigger-requested":
        raise TriggerIntentError("trigger intent is malformed")
    return record


def record(guard_path: Path, binding: str) -> dict:
    """Atomically persist the trigger intent (idempotent for same binding)."""
    binding = _req_binding(binding)
    path = intent_path_for(guard_path)
    existing = readback(guard_path, binding) if path.exists() else None
    if existing is not None:
        return existing
    # A foreign intent for another binding must not be silently replaced;
    # the caller observes the ambiguity fail-closed instead.
    if path.exists():
        raise TriggerIntentError("stale trigger intent binding")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "intent": "trigger-requested",
        "binding_digest": binding,
        "guard": str(Path(guard_path).resolve()) if Path(guard_path).exists() else str(guard_path),
        "issued_at": int(time.time()),
        "pid": os.getpid(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return payload


def clear(guard_path: Path, binding: str) -> None:
    """Remove the intent only for terminal guard states (commit/recover path owns this)."""
    binding = _req_binding(binding)
    path = intent_path_for(guard_path)
    if not path.exists():
        return
    current = readback(guard_path, binding)
    if current is None:
        return
    path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guard", type=Path, required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--action", choices=("record", "readback"), required=True)
    args = parser.parse_args()
    try:
        if args.action == "record":
            out = record(args.guard, args.binding)
        else:
            out = readback(args.guard, args.binding)
        print(json.dumps(out, sort_keys=True))
        return 0
    except (TriggerIntentError, OSError, ValueError) as exc:
        print(f"trigger intent failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
