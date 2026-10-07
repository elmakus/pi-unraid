#!/usr/bin/env python3
"""Narrow merge-safe Muse max delivery (M07-T05A).

Merges exactly one documented override —
``meta.modelOverrides.muse-spark-1.3-contributor.thinkingLevelMap.max = "max"``
— from the frozen secret-free fragment
``models.muse-max-override.json`` into the candidate-effective
``models.json`` that pinned Pi reads, preserving every unrelated
provider/model setting verbatim.

This is the ONLY writer of the derived effective file in the candidate
path. It never installs or overwrites a whole ``models.json`` from the
fragment alone: the existing file (when present) is read, validated as a
JSON object, and only the single nested key is ensured via the documented
shallow key-merge. Unknown override IDs are ignored by Pi and are never
added here. An explicit ``null`` for the required key in the EFFECTIVE
file is overwritten to ``"max"`` by this delivery; a ``null`` observed
without this delivery remains clamped to ``xhigh`` by Pi and must fail
closed upstream.

Secret-free: the fragment and this program carry no credential, apiKey,
command (``!``), or environment interpolation. Existing ``apiKey``
references (for example the codex-lb ``${CODEX_LB_API_KEY}`` reference)
are preserved byte-identically and never output. ``auth.json`` is never
read or written. HOME mutation is limited to the single effective
``models.json`` path supplied by the caller.

Fail-closed: malformed JSON, non-object roots, non-object ``providers``,
symlinks, non-regular files, unsafe fragment shapes (extra providers,
extra models, extra override keys, secrets, commands), or an unsafe
existing configuration preserves the existing file unchanged and exits
non-zero. Writes are atomic (mkstemp + fsync + os.replace) with mode
``0600``. Re-running with identical inputs is idempotent (no change,
same bytes).

Usage (candidate-local, via the existing companion path):
  paseo-muse-max-merge.py --fragment <frag> --models <models.json>
  paseo-muse-max-merge.py --fragment <frag> --models <models.json> --check
``--check`` verifies without writing: the fragment must be exactly the
required minimal shape and the effective file must already carry
``max="max"`` with unrelated settings intact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

FIXED_PROVIDER = "meta"
FIXED_MODEL = "muse-spark-1.3-contributor"
FIXED_THINKING = "max"
FRAGMENT_FILENAME = "models.muse-max-override.json"
EFFECTIVE_FILENAME = "models.json"


class MuseMaxMergeError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise MuseMaxMergeError(f"muse-max merge: {message}")


def read_regular_bytes(path: Path, *, what: str) -> bytes:
    if path.is_symlink():
        fail(f"refusing symlink for {what}: {path}")
    try:
        st = path.stat()
    except FileNotFoundError:
        fail(f"{what} does not exist: {path}")
    except OSError as exc:
        fail(f"{what} unreadable: {path}: {exc}")
    if not stat.S_ISREG(st.st_mode):
        fail(f"{what} is not a regular file: {path}")
    if st.st_size > 1048576:
        fail(f"{what} exceeds size bound: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        fail(f"{what} unreadable: {path}: {exc}")


def parse_json_object(raw: bytes, *, what: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        fail(f"{what} is not valid UTF-8 JSON; preserved unchanged")
    if not isinstance(value, dict):
        fail(f"{what} root must be an object; preserved unchanged")
    return value


def _has_command_or_interpolation(value: Any) -> bool:
    if isinstance(value, str):
        return value.startswith("!") or "$" in value
    if isinstance(value, dict):
        return any(_has_command_or_interpolation(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_command_or_interpolation(v) for v in value)
    return False


def validate_fragment(doc: Any) -> dict[str, Any]:
    """Require EXACTLY the minimal secret-free fragment, nothing else."""
    if not isinstance(doc, dict):
        fail("fragment root must be an object")
    if set(doc.keys()) != {"providers"}:
        fail("fragment must contain only 'providers'")
    providers = doc.get("providers")
    if not isinstance(providers, dict):
        fail("fragment providers must be an object")
    if set(providers.keys()) != {FIXED_PROVIDER}:
        fail("fragment must contain only the 'meta' provider")
    meta = providers.get(FIXED_PROVIDER)
    if not isinstance(meta, dict):
        fail("fragment meta provider must be an object")
    if set(meta.keys()) != {"modelOverrides"}:
        fail("fragment meta provider must contain only 'modelOverrides'")
    overrides = meta.get("modelOverrides")
    if not isinstance(overrides, dict):
        fail("fragment modelOverrides must be an object")
    if set(overrides.keys()) != {FIXED_MODEL}:
        fail("fragment must override only 'muse-spark-1.3-contributor'")
    entry = overrides.get(FIXED_MODEL)
    if not isinstance(entry, dict):
        fail("fragment model entry must be an object")
    if set(entry.keys()) != {"thinkingLevelMap"}:
        fail("fragment model entry must contain only 'thinkingLevelMap'")
    tlm = entry.get("thinkingLevelMap")
    if not isinstance(tlm, dict):
        fail("fragment thinkingLevelMap must be an object")
    if set(tlm.keys()) != {FIXED_THINKING}:
        fail("fragment thinkingLevelMap must contain only 'max'")
    if tlm.get(FIXED_THINKING) != "max":
        fail("fragment thinkingLevelMap.max must be exactly \"max\"")
    if _has_command_or_interpolation(doc):
        fail("fragment must be secret-free (no commands or interpolation)")
    for key in ("apiKey", "authHeader", "headers", "baseUrl", "models", "api", "oauth"):
        if key in meta:
            fail(f"fragment must not carry provider routing/secret key: {key}")
    return doc


def validate_existing_effective(doc: Any) -> dict[str, Any]:
    """Validate the existing effective file shape without mutating it."""
    if not isinstance(doc, dict):
        fail("existing models.json root must be an object; preserved unchanged")
    providers = doc.get("providers", {})
    if "providers" in doc and not isinstance(providers, dict):
        fail("existing models.json providers must be an object; preserved unchanged")
    if isinstance(providers, dict):
        for pid, pentry in providers.items():
            if not isinstance(pid, str) or not pid or any(
                ch.isspace() or ord(ch) <= 0x1F or ord(ch) == 0x7F for ch in pid
            ):
                fail("existing provider id is invalid; preserved unchanged")
            if not isinstance(pentry, dict):
                fail(f"existing provider entry is not an object: {pid}; preserved unchanged")
    return doc


def merge_effective(existing: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    """Narrow merge: ensure only the required nested key, preserve all else.

    Shallow key-merge at the thinkingLevelMap level, matching pinned Pi
    ``applyModelOverride`` (``{...model.thinkingLevelMap,
    ...override.thinkingLevelMap}``): other thinking levels, other model
    overrides, other meta keys, and all unrelated providers are preserved
    verbatim. Unknown IDs are never added.
    """
    validate_fragment(fragment)
    validate_existing_effective(existing)
    merged = json.loads(json.dumps(existing))
    providers = merged.setdefault("providers", {})
    if not isinstance(providers, dict):
        fail("existing models.json providers must be an object; preserved unchanged")
    meta = providers.setdefault(FIXED_PROVIDER, {})
    if not isinstance(meta, dict):
        fail("existing meta provider entry is not an object; preserved unchanged")
    overrides = meta.setdefault("modelOverrides", {})
    if not isinstance(overrides, dict):
        fail("existing meta modelOverrides is not an object; preserved unchanged")
    entry = overrides.setdefault(FIXED_MODEL, {})
    if not isinstance(entry, dict):
        fail("existing contributor override entry is not an object; preserved unchanged")
    tlm = entry.setdefault("thinkingLevelMap", {})
    if not isinstance(tlm, dict):
        fail("existing contributor thinkingLevelMap is not an object; preserved unchanged")
    tlm[FIXED_THINKING] = "max"
    return merged


def verify_effective(doc: Any) -> dict[str, Any]:
    """Verify the effective file already carries the required delivery."""
    if not isinstance(doc, dict):
        fail("effective models.json root must be an object")
    try:
        providers = doc["providers"]
        meta = providers[FIXED_PROVIDER]
        overrides = meta["modelOverrides"]
        entry = overrides[FIXED_MODEL]
        tlm = entry["thinkingLevelMap"]
        value = tlm[FIXED_THINKING]
    except (KeyError, TypeError, AttributeError):
        fail("effective models.json lacks the required muse max override")
    if value != "max":
        fail("effective muse max override is not exactly \"max\" (null/clamped)")
    if not isinstance(providers, dict) or not isinstance(meta, dict):
        fail("effective providers shape is invalid")
    return doc


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def render_canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8")


def atomic_write_0600(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        fail(f"refusing symlink target: {path}")
    if path.exists() and not path.is_file():
        fail(f"refusing non-file target: {path}")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def apply_merge(fragment_path: Path, models_path: Path, *, check_only: bool = False) -> dict[str, Any]:
    frag_raw = read_regular_bytes(fragment_path, what="fragment")
    frag_doc = parse_json_object(frag_raw, what="fragment")
    validate_fragment(frag_doc)
    if models_path.is_symlink():
        fail(f"refusing symlink for effective file: {models_path}")
    if models_path.exists():
        if not models_path.is_file():
            fail(f"refusing non-file effective target: {models_path}")
        eff_raw = read_regular_bytes(models_path, what="effective models.json")
        eff_doc = parse_json_object(eff_raw, what="effective models.json")
        validate_existing_effective(eff_doc)
    else:
        eff_doc = {"providers": {}}
        eff_raw = b""
    merged = merge_effective(eff_doc, frag_doc)
    rendered = render_canonical(merged)
    if check_only:
        verify_effective(merged)
        current = models_path.read_bytes() if models_path.exists() else b""
        if current != rendered:
            fail("effective models.json differs from required merged bytes")
        st = models_path.stat()
        mode = stat.S_IMODE(st.st_mode)
        if mode != 0o600:
            fail(f"effective models.json mode is not 0600: {mode:04o}")
        return {
            "action": "check",
            "changed": False,
            "fragment_sha256": sha256_bytes(frag_raw),
            "effective_sha256": sha256_bytes(rendered),
            "mode": "0600",
        }
    if models_path.exists():
        current = models_path.read_bytes()
        st = models_path.stat()
        mode = stat.S_IMODE(st.st_mode)
        if current == rendered and mode == 0o600:
            verify_effective(merged)
            return {
                "action": "apply",
                "changed": False,
                "fragment_sha256": sha256_bytes(frag_raw),
                "effective_sha256": sha256_bytes(rendered),
                "mode": "0600",
            }
    atomic_write_0600(models_path, rendered)
    verify_effective(json.loads(rendered.decode("utf-8")))
    return {
        "action": "apply",
        "changed": True,
        "fragment_sha256": sha256_bytes(frag_raw),
        "effective_sha256": sha256_bytes(rendered),
        "mode": "0600",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Narrow muse-max merge")
    parser.add_argument("--fragment", required=True, type=Path)
    parser.add_argument("--models", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = apply_merge(args.fragment, args.models, check_only=args.check)
    except MuseMaxMergeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 20
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
