#!/usr/bin/env python3
"""Tower-local persistent Buildx/cache/image-retention profile for Paseo (M05-T02B)."""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "paseo_buildx.py"
DEFAULT_ROOT = Path("/mnt/user/appdata/pi-unraid/buildx")
DEFAULT_BOUNDARY = Path("/mnt/user/appdata/pi-unraid")
DEFAULT_BUILDER = "pi-unraid-paseo"
DEFAULT_RETAIN = 3
DEFAULT_CACHE_MAX = "8GB"
RETENTION_SCHEMA = 1
IMAGE_PREFIX = "pi-unraid:paseo-"


def _load_buildx():
    spec = importlib.util.spec_from_file_location("paseo_buildx", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


buildx = _load_buildx()


class TowerBuildError(RuntimeError):
    pass


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _run(argv: list[str], env: dict[str, str] | None = None, timeout: int = 120):
    try:
        return subprocess.run(
            argv, text=True, capture_output=True, timeout=timeout, env=env or dict(os.environ)
        )
    except OSError as exc:
        return subprocess.CompletedProcess(argv, 127, "", str(exc))


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def parse_storage_bytes(value: str) -> int:
    match = re.fullmatch(r"([0-9]+(?:\\.[0-9]+)?)\\s*(B|KB|MB|GB|TB)", (value or "").strip(), re.I)
    if not match:
        raise TowerBuildError(f"cache bound is invalid: {value!r}")
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    return int(float(match.group(1)) * units[match.group(2).upper()])


def cache_size_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    total = 0
    for item in root.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            pass
    return total


def _digest_strings(obj) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, dict):
        for value in obj.values():
            found.update(_digest_strings(value))
    elif isinstance(obj, list):
        for value in obj:
            found.update(_digest_strings(value))
    elif isinstance(obj, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", obj):
        found.add(obj)
    return found


def reachable_local_cache_blobs(cache_dir: Path) -> set[str]:
    """Return OCI blob digests reachable from the current local-cache index."""
    index = cache_dir / "index.json"
    if not index.is_file():
        return set()
    try:
        root = json.loads(index.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TowerBuildError(f"local cache index is unreadable: {index}") from exc
    reachable = _digest_strings(root)
    queue = list(reachable)
    seen = set()
    while queue:
        digest = queue.pop()
        if digest in seen:
            continue
        seen.add(digest)
        blob = cache_dir / "blobs" / "sha256" / digest.split(":", 1)[1]
        try:
            if not blob.is_file() or blob.stat().st_size > 2 * 1024 * 1024:
                continue
            nested = json.loads(blob.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        for child in _digest_strings(nested):
            if child not in reachable:
                reachable.add(child)
                queue.append(child)
    return reachable


def compact_local_cache(profile: dict, max_storage: str) -> dict:
    """Post-success OCI cache GC plus a fail-safe hard cap."""
    cache_dir = Path(profile["cache_dir"])
    max_bytes = parse_storage_bytes(max_storage)
    before = cache_size_bytes(cache_dir)
    reachable = reachable_local_cache_blobs(cache_dir)
    removed_blobs = 0
    removed_bytes = 0
    blob_root = cache_dir / "blobs" / "sha256"
    if blob_root.is_dir():
        for blob in blob_root.iterdir():
            if not blob.is_file():
                continue
            digest = f"sha256:{blob.name}"
            if digest in reachable:
                continue
            try:
                size = blob.stat().st_size
                blob.unlink()
                removed_blobs += 1
                removed_bytes += size
            except OSError as exc:
                raise TowerBuildError(f"cannot prune stale local-cache blob: {blob}") from exc

    after_gc = cache_size_bytes(cache_dir)
    cleared_over_bound = False
    if after_gc > max_bytes:
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cleared_over_bound = True
    after = cache_size_bytes(cache_dir)
    result = {
        "schema_version": 1,
        "max_storage": max_storage,
        "max_bytes": max_bytes,
        "bytes_before": before,
        "bytes_after_gc": after_gc,
        "bytes_after": after,
        "reachable_blobs": len(reachable),
        "removed_blobs": removed_blobs,
        "removed_bytes": removed_bytes,
        "cleared_over_bound": cleared_over_bound,
        "pruned_at": _utcnow(),
    }
    atomic_json(Path(profile["cache_policy_file"]), result)
    return result


def resolve_profile(root: Path, boundary: Path, builder: str) -> dict[str, Path | str]:
    root = root.expanduser().resolve()
    boundary = boundary.expanduser().resolve()
    try:
        root.relative_to(boundary)
    except ValueError as exc:
        raise TowerBuildError(f"Tower build root {root} is outside accepted boundary {boundary}") from exc
    if root == boundary:
        raise TowerBuildError("Tower build root must be a dedicated child of the appdata boundary")
    return {
        "root": root,
        "boundary": boundary,
        "builder": buildx.validate_builder_name(builder),
        "state_dir": root / "docker-config",
        "cache_dir": root / "cache",
        "records_dir": root / "records",
        "retention_file": root / "retention.json",
        "cache_policy_file": root / "cache-policy.json",
        "readback_file": root / "tower-readback.json",
    }


def prepare_profile(profile: dict) -> dict:
    for key in ("root", "state_dir", "cache_dir", "records_dir"):
        Path(profile[key]).mkdir(parents=True, exist_ok=True)
    env = buildx.docker_env(Path(profile["state_dir"]))
    info = buildx.ensure_builder(_run, str(profile["builder"]), Path(profile["state_dir"]), env)
    boot = _run(
        ["docker", "buildx", "inspect", "--bootstrap", str(profile["builder"])], env, 180
    )
    if boot.returncode != 0:
        raise TowerBuildError(f"builder bootstrap failed: {(boot.stderr or boot.stdout)[-1200:]}")
    container = f"buildx_buildkit_{profile['builder']}0"
    inspect = _run(["docker", "inspect", container], env, 60)
    mounts = []
    if inspect.returncode == 0:
        try:
            mounts = json.loads(inspect.stdout)[0].get("Mounts") or []
        except (json.JSONDecodeError, IndexError, KeyError):
            mounts = []
    data = {
        "schema_version": 1,
        "builder": info,
        "paths": {k: str(profile[k]) for k in ("root", "state_dir", "cache_dir", "records_dir")},
        "buildkit_container": container,
        "buildkit_mounts": mounts,
        "prepared_at": _utcnow(),
    }
    atomic_json(Path(profile["readback_file"]), data)
    return data


def load_retention(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": RETENTION_SCHEMA, "entries": []}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TowerBuildError(f"retention file unreadable: {path}") from exc
    if data.get("schema_version") != RETENTION_SCHEMA or not isinstance(data.get("entries"), list):
        raise TowerBuildError("retention file uses an unsupported schema")
    return data


def validated_record(record_path: Path) -> dict:
    record = buildx.load_build_record(record_path)
    phases = record.get("phases") or {}
    if (phases.get("build") or {}).get("status") != "ok":
        raise TowerBuildError("record has no successful build")
    if (phases.get("test") or {}).get("status") != "ok":
        raise TowerBuildError("record has no successful smoke/test")
    tag = record.get("tag") or ""
    image = record.get("image") or {}
    candidate = record.get("candidate") or {}
    if not tag.startswith(IMAGE_PREFIX):
        raise TowerBuildError(f"record tag is outside managed Paseo namespace: {tag!r}")
    if not image.get("id") or not candidate.get("candidate_id"):
        raise TowerBuildError("record lacks immutable image/candidate identity")
    return record


def inspect_record_image(record: dict, state_dir: Path) -> dict:
    tag = record["tag"]
    ident = buildx.read_image_identity(_run, tag, buildx.docker_env(state_dir))
    if ident.get("id") != record["image"]["id"]:
        raise TowerBuildError("live image id does not match build record")
    if ident.get("candidate_label") != record["candidate"]["candidate_id"]:
        raise TowerBuildError("live candidate label does not match build record")
    return ident


def retain_record(profile: dict, record_path: Path, max_entries: int) -> dict:
    if max_entries < 1 or max_entries > 20:
        raise TowerBuildError("retention bound must be between 1 and 20")
    record = validated_record(record_path)
    inspect_record_image(record, Path(profile["state_dir"]))
    current = load_retention(Path(profile["retention_file"]))
    entry = {
        "candidate_id": record["candidate"]["candidate_id"],
        "image_id": record["image"]["id"],
        "tag": record["tag"],
        "record": str(record_path.resolve()),
        "protected_at": _utcnow(),
    }
    entries = [
        item for item in current["entries"]
        if item.get("candidate_id") != entry["candidate_id"] and item.get("tag") != entry["tag"]
    ]
    entries.insert(0, entry)
    data = {
        "schema_version": RETENTION_SCHEMA,
        "max_entries": max_entries,
        "entries": entries[:max_entries],
    }
    atomic_json(Path(profile["retention_file"]), data)
    return data


def managed_image_tags() -> list[str]:
    proc = _run([
        "docker", "image", "ls", "--filter", "reference=pi-unraid:paseo-*",
        "--format", "{{.Repository}}:{{.Tag}}"
    ], timeout=60)
    if proc.returncode != 0:
        raise TowerBuildError(f"image list failed: {(proc.stderr or proc.stdout)[-800:]}")
    return sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})


def prune_unprotected_images(profile: dict) -> dict:
    retention = load_retention(Path(profile["retention_file"]))
    protected = {item.get("tag") for item in retention["entries"] if item.get("tag")}
    removed = []
    skipped = []
    for tag in managed_image_tags():
        if tag in protected:
            skipped.append(tag)
            continue
        proc = _run(["docker", "image", "rm", tag], timeout=180)
        if proc.returncode != 0:
            raise TowerBuildError(f"image cleanup failed for {tag}: {(proc.stderr or proc.stdout)[-800:]}")
        removed.append(tag)
    return {"protected": sorted(protected), "removed": removed, "skipped": skipped}


def readback(profile: dict) -> dict:
    env = buildx.docker_env(Path(profile["state_dir"]))
    inspect = _run(["docker", "buildx", "inspect", str(profile["builder"])], env, 60)
    retention = load_retention(Path(profile["retention_file"]))
    protected = []
    for entry in retention["entries"]:
        tag = entry.get("tag")
        if not tag:
            continue
        live = _run(["docker", "image", "inspect", tag], env, 60)
        protected.append({"tag": tag, "present": live.returncode == 0, "image_id": entry.get("image_id")})
    cache_bytes = 0
    cache_dir = Path(profile["cache_dir"])
    if cache_dir.exists():
        for item in cache_dir.rglob("*"):
            try:
                if item.is_file():
                    cache_bytes += item.stat().st_size
            except OSError:
                pass
    data = {
        "schema_version": 1,
        "builder": str(profile["builder"]),
        "builder_visible": inspect.returncode == 0,
        "builder_readback": (inspect.stdout or inspect.stderr)[-2400:],
        "paths": {k: str(profile[k]) for k in ("root", "state_dir", "cache_dir", "records_dir")},
        "cache_bytes": cache_bytes,
        "cache_policy": (
            json.loads(Path(profile["cache_policy_file"]).read_text())
            if Path(profile["cache_policy_file"]).is_file() else None
        ),
        "retention": retention,
        "protected_images": protected,
        "read_at": _utcnow(),
    }
    atomic_json(Path(profile["readback_file"]), data)
    return data


def cmd_build(args, profile: dict) -> int:
    prepare_profile(profile)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record = Path(args.record) if args.record else Path(profile["records_dir"]) / f"build-{stamp}.json"
    metadata = record.with_suffix(".metadata.json")
    inner = [
        "build", "--candidate", args.candidate, "--context", args.context,
        "--record", str(record), "--metadata", str(metadata),
        "--builder", str(profile["builder"]), "--state-dir", str(profile["state_dir"]),
        "--cache-dir", str(profile["cache_dir"]), "--with-smoke",
        "--keep-storage", args.keep_storage,
    ]
    if args.with_prune:
        inner.append("--with-prune")
    for label in args.build_label:
        inner += ["--build-label", label]
    rc = buildx.main(inner)
    if rc != 0:
        return rc
    compact_local_cache(profile, args.cache_max)
    retain_record(profile, record, args.retain)
    if args.prune_images:
        prune_unprotected_images(profile)
    readback(profile)
    print(json.dumps({"record": str(record), "retention": str(profile["retention_file"])}, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Persistent Tower-local Paseo build/cache/retention profile")
    p.add_argument("--root", default=os.environ.get("PI_UNRAID_TOWER_BUILDX_ROOT", str(DEFAULT_ROOT)))
    p.add_argument("--boundary", default=str(DEFAULT_BOUNDARY))
    p.add_argument("--builder", default=DEFAULT_BUILDER)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("readback")
    retain = sub.add_parser("retain")
    retain.add_argument("--record", required=True)
    retain.add_argument("--max", type=int, default=DEFAULT_RETAIN)
    retain.add_argument("--prune-images", action="store_true")
    build = sub.add_parser("build")
    build.add_argument("--candidate", default=str(buildx.DEFAULT_CANDIDATE))
    build.add_argument("--context", default=str(ROOT))
    build.add_argument("--record")
    build.add_argument("--keep-storage", default=buildx.KEEP_STORAGE_DEFAULT)
    build.add_argument("--retain", type=int, default=DEFAULT_RETAIN)
    build.add_argument("--cache-max", default=DEFAULT_CACHE_MAX)
    build.add_argument("--build-label", action="append", default=[])
    build.add_argument("--with-prune", action="store_true")
    build.add_argument("--prune-images", action="store_true")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = resolve_profile(Path(args.root), Path(args.boundary), args.builder)
        if args.command == "prepare":
            print(json.dumps(prepare_profile(profile), sort_keys=True))
            return 0
        if args.command == "readback":
            print(json.dumps(readback(profile), sort_keys=True))
            return 0
        if args.command == "retain":
            data = retain_record(profile, Path(args.record), args.max)
            cleanup = prune_unprotected_images(profile) if args.prune_images else None
            print(json.dumps({"retention": data, "cleanup": cleanup}, sort_keys=True))
            return 0
        if args.command == "build":
            return cmd_build(args, profile)
    except (TowerBuildError, buildx.BuildxError) as exc:
        print(f"tower build refused: {exc}", file=sys.stderr)
        return 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
