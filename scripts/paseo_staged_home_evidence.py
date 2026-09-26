#!/usr/bin/env python3
"""Disposable HOME preservation evidence for the M05-T03 staged transaction.

A live Paseo HOME cannot be required to be byte- or mtime-stable across a
transaction: the running daemon may append legitimate runtime state, and a
directory mtime shifts on any transient create/delete cycle even when the
file set is restored identically. A whole-HOME ``find %P %s %T@`` hash
therefore fails on healthy runs.

This helper proves the Card's actual requirement instead, through the
runtime identity and read-only mounts:

* every protected seeded entry is still present with byte-identical
  content (content is compared as SHA-256, so secret-bearing state is
  never printed or stored); the post-init seed must include the real
  daemon keypair, server id, Relay-enabled config and representative
  session/browser markers;
* the ``.paseo/config.json`` marker stays readable and the persisted
  Relay setting is unchanged;
* a run-specific sentinel written after fixture configuration is still
  intact, which rules out a destructive restore to a pristine snapshot;
* volatile daemon state (logs, pid, runtime cache, model downloads) is
  reported separately and never fails, while other added entries are
  reported, not hidden and not treated as preservation failures.

Any protected seeded entry removed or altered, a flipped Relay setting,
or a lost sentinel fails closed with a machine-readable report.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = 1
HOME_MARKER = ".paseo/config.json"
SENTINEL_NAME = ".pi-unraid-staged-sentinel"
SENTINEL_TEXT_RE = re.compile(r"[A-Za-z0-9_.:/+=@-]+")

# Volatile daemon state that must never fail preservation: logs, pid files,
# ephemeral runtime caches and model downloads. Everything else under HOME is
# protected persistent state (pairing identity, server id, config/Relay,
# sentinel, representative session/browser markers). The staged transaction
# uses the identical classification so phase guards and end-to-end evidence
# agree on what routine daemon writes may change.
VOLATILE_HOME_EXACT = frozenset({
    ".paseo/daemon.log",
    ".paseo/paseo.pid",
})
VOLATILE_HOME_PREFIXES = (
    ".paseo/models/",
    ".paseo/runtime/",
    ".paseo/logs/",
    ".paseo/cache/",
    ".paseo/tmp/",
)

EXIT_FAILED = 1
EXIT_VALIDATION = 2


def is_volatile_home_path(rel: str) -> bool:
    """Return True for volatile daemon state that preservation must ignore."""
    if rel in VOLATILE_HOME_EXACT:
        return True
    for prefix in VOLATILE_HOME_PREFIXES:
        if rel.startswith(prefix):
            return True
    if rel.startswith(".paseo/") and rel.endswith(".log"):
        return True
    return False


def collect_home(root) -> dict:
    """Inventory a Paseo HOME as content hashes plus the Relay setting.

    Self-contained (stdlib only, no module globals) so this exact source
    also runs inside the runtime container via ``python3 -c``. Only
    relative names, sizes and SHA-256 digests are returned; file bytes
    never leave the collector.
    """
    import hashlib
    import json
    import os

    root = os.fspath(root)
    entries = {}
    def walk_error(exc):
        raise exc

    for dirpath, dirnames, filenames in os.walk(root, onerror=walk_error):
        dirnames.sort()
        for name in list(dirnames):
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                rel = os.path.relpath(path, root)
                target = os.readlink(path).encode("utf-8", "surrogateescape")
                entries[rel] = {"kind": "symlink", "size": len(target),
                                "sha256": hashlib.sha256(target).hexdigest()}
                dirnames.remove(name)
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            if os.path.islink(path):
                target = os.readlink(path).encode("utf-8", "surrogateescape")
                entries[rel] = {"kind": "symlink", "size": len(target),
                                "sha256": hashlib.sha256(target).hexdigest()}
                continue
            digest = hashlib.sha256()
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(65536), b""):
                    digest.update(chunk)
            entries[rel] = {"kind": "file", "size": os.path.getsize(path),
                            "sha256": digest.hexdigest()}
    relay_enabled = None
    try:
        with open(os.path.join(root, ".paseo", "config.json"), "rb") as handle:
            config = json.loads(handle.read().decode("utf-8"))
        relay_enabled = ((config.get("daemon") or {}).get("relay") or {}).get("enabled")
    except (OSError, ValueError):
        relay_enabled = None
    return {"entries": entries, "relay_enabled": relay_enabled,
            "marker_present": ".paseo/config.json" in entries}


def collector_source() -> str:
    """Render the in-container collector program for ``python3 -c``."""
    return (
        inspect.getsource(collect_home)
        + "\nimport json, sys\n"
        + "sys.stdout.write(json.dumps(collect_home('/home/paseo'), sort_keys=True))\n"
    )


class EvidenceError(RuntimeError):
    """Fail-closed HOME evidence error."""


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _run(argv: list[str], env: dict[str, str] | None = None, timeout: int = 120):
    try:
        return subprocess.run(
            argv, text=True, capture_output=True, timeout=timeout,
            env=env if env is not None else dict(os.environ),
        )
    except OSError as exc:
        return subprocess.CompletedProcess(argv, 127, "", str(exc))


def _tail(text: str, limit: int = 1500) -> str:
    text = text or ""
    return text[-limit:] if len(text) > limit else text


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(data, sort_keys=True, indent=2) + "\n"
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(rendered)
    os.replace(tmp, path)


def collect_via_runtime(run_fn, home: Path, tag: str, uid: str, gid: str) -> dict:
    """Collect the HOME inventory through the runtime identity, read-only."""
    if not home.is_dir():
        raise EvidenceError(f"HOME host path is not a directory: {home}")
    proc = run_fn(
        ["docker", "run", "--rm", "--user", f"{uid}:{gid}",
         "-v", f"{home}:/home/paseo:ro", tag,
         "python3", "-c", collector_source()],
        dict(os.environ), 180,
    )
    if proc.returncode != 0:
        raise EvidenceError(
            f"runtime HOME inventory failed (rc={proc.returncode}): "
            f"{_tail(proc.stderr or proc.stdout)}"
        )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise EvidenceError("runtime HOME inventory returned unreadable JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        raise EvidenceError("runtime HOME inventory has an unexpected shape")
    return data


def write_sentinel(run_fn, home: Path, tag: str, uid: str, gid: str, text: str) -> None:
    """Write the run sentinel through the runtime identity (one bounded write)."""
    if not text or SENTINEL_TEXT_RE.fullmatch(text) is None:
        raise EvidenceError("sentinel text uses an unsupported charset")
    if not home.is_dir():
        raise EvidenceError(f"HOME host path is not a directory: {home}")
    proc = run_fn(
        ["docker", "run", "--rm", "--user", f"{uid}:{gid}",
         "-v", f"{home}:/home/paseo",
         "-e", f"STAGED_SENTINEL_TEXT={text}", tag,
         "sh", "-c",
         f"printf '%s' \"$STAGED_SENTINEL_TEXT\" > /home/paseo/{SENTINEL_NAME}"],
        dict(os.environ), 120,
    )
    if proc.returncode != 0:
        raise EvidenceError(
            f"sentinel write failed (rc={proc.returncode}): "
            f"{_tail(proc.stderr or proc.stdout)}"
        )


def compare_manifest(manifest: dict, current: dict) -> dict:
    """Compare current HOME state against the seed manifest.

    Removed or altered protected seeded entries, a flipped Relay setting,
    or a lost marker fail. Volatile daemon state (logs, pid, runtime cache,
    model downloads) is reported separately and never fails, so routine
    daemon writes cannot break a healthy run. Added entries are reported,
    not failed, with volatile additions listed separately for transparency.
    """
    seeded = manifest.get("entries") or {}
    now = current.get("entries") or {}
    raw_missing = sorted(set(seeded) - set(now))
    raw_altered = sorted(key for key in set(seeded) & set(now)
                         if (seeded[key] or {}).get("sha256") != (now[key] or {}).get("sha256")
                         or (seeded[key] or {}).get("kind") != (now[key] or {}).get("kind"))
    added = sorted(set(now) - set(seeded))
    missing = [key for key in raw_missing if not is_volatile_home_path(key)]
    altered = [key for key in raw_altered if not is_volatile_home_path(key)]
    volatile_missing = [key for key in raw_missing if is_volatile_home_path(key)]
    volatile_altered = [key for key in raw_altered if is_volatile_home_path(key)]
    volatile_added = [key for key in added if is_volatile_home_path(key)]
    protected_added = [key for key in added if not is_volatile_home_path(key)]
    relay_expected = manifest.get("relay_enabled")
    relay_observed = current.get("relay_enabled")
    relay_changed = relay_expected != relay_observed
    marker_ok = bool(current.get("marker_present")) and HOME_MARKER not in missing \
        and HOME_MARKER not in altered
    altered_detail = {key: {"expected": (seeded[key] or {}).get("sha256"),
                            "observed": (now[key] or {}).get("sha256")} for key in altered}
    ok = not missing and not altered and not relay_changed and marker_ok
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "missing": missing,
        "altered": altered,
        "altered_detail": altered_detail,
        "added": added,
        "protected_added": protected_added,
        "volatile_missing": volatile_missing,
        "volatile_altered": volatile_altered,
        "volatile_added": volatile_added,
        "relay_expected": relay_expected,
        "relay_observed": relay_observed,
        "relay_changed": relay_changed,
        "marker_present": bool(current.get("marker_present")),
        "seeded_entries": len(seeded),
        "current_entries": len(now),
    }


def load_manifest(path: Path) -> dict:
    try:
        raw = path.read_text()
    except FileNotFoundError as exc:
        raise EvidenceError(f"seed manifest is missing: {path}") from exc
    except OSError as exc:
        raise EvidenceError(f"seed manifest is unreadable: {path}") from exc
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"seed manifest is not valid JSON: {path}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceError(f"seed manifest uses an unsupported schema: {path}")
    if not isinstance(manifest.get("entries"), dict):
        raise EvidenceError(f"seed manifest lacks an entry inventory: {path}")
    return manifest


def cmd_seed(args: argparse.Namespace, run_fn=None) -> int:
    run_fn = run_fn or _run
    try:
        home = Path(args.home_host)
        if args.sentinel_text is not None:
            write_sentinel(run_fn, home, args.tag, args.uid, args.gid,
                           args.sentinel_text)
        current = collect_via_runtime(run_fn, home, args.tag, args.uid, args.gid)
        if not current.get("marker_present"):
            raise EvidenceError(
                f"seed HOME lacks a runtime-readable marker {HOME_MARKER}")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "home": str(home),
            "tag": args.tag,
            "seeded_at": _utcnow(),
            "sentinel": SENTINEL_NAME if args.sentinel_text is not None else None,
            "entries": current["entries"],
            "relay_enabled": current.get("relay_enabled"),
            "marker_present": True,
        }
        atomic_write_json(Path(args.out), manifest)
    except EvidenceError as exc:
        print(f"home evidence seed refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    print(json.dumps({
        "manifest": str(args.out), "entries": len(manifest["entries"]),
        "relay_enabled": manifest["relay_enabled"],
        "sentinel": manifest["sentinel"], "marker_present": True,
    }, sort_keys=True))
    return 0


def cmd_verify(args: argparse.Namespace, run_fn=None) -> int:
    run_fn = run_fn or _run
    try:
        manifest = load_manifest(Path(args.manifest))
        if manifest.get("home") != str(Path(args.home_host)) or manifest.get("tag") != args.tag:
            raise EvidenceError("seed manifest does not match the requested HOME and image")
        current = collect_via_runtime(
            run_fn, Path(args.home_host), args.tag, args.uid, args.gid)
        report = compare_manifest(manifest, current)
        report["manifest"] = str(args.manifest)
        report["checked_at"] = _utcnow()
        atomic_write_json(Path(args.report), report)
    except EvidenceError as exc:
        print(f"home evidence verify refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    print(json.dumps({
        "report": str(args.report), "ok": report["ok"],
        "missing": report["missing"], "altered": report["altered"],
        "added": report["added"], "relay_changed": report["relay_changed"],
        "seeded_entries": report["seeded_entries"],
        "current_entries": report["current_entries"],
    }, sort_keys=True))
    if not report["ok"]:
        print("HOME preservation check failed: seeded state was removed or altered",
              file=sys.stderr)
        return EXIT_FAILED
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed and verify disposable HOME preservation evidence.")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--home-host", required=True)
        target.add_argument("--tag", required=True)
        target.add_argument("--uid", default="99")
        target.add_argument("--gid", default="100")

    seed = sub.add_parser("seed", help="write the sentinel and record the manifest")
    common(seed)
    seed.add_argument("--sentinel-text", default=None)
    seed.add_argument("--out", required=True)

    verify = sub.add_parser("verify", help="verify current HOME against the manifest")
    common(verify)
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None, run_fn=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "seed":
        return cmd_seed(args, run_fn=run_fn)
    if args.command == "verify":
        return cmd_verify(args, run_fn=run_fn)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
