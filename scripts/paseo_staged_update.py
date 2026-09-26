#!/usr/bin/env python3
"""Reusable Paseo staged-update transaction over disposable runtimes (M05-T03).

One Paseo-specific repeatable path consumes a frozen accepted or explicitly
staged candidate plus immutable local image/provenance and never resolves a
floating channel on its own: candidate schema/identity validation is delegated
to the read-only M05-T01 resolver ``validate`` entrypoint, and the build
context Dockerfile must match the frozen candidate before any Docker
invocation, exactly like the M05-T02A foundation.

Phase order is fixed: ``preflight`` then ``build`` then ``fast_checks`` then
``temp_smoke`` then ``promote`` then ``post_smoke``. A failed build, fast
check or temporary-runtime smoke leaves the recorded active runtime/alias and
the persistent HOME untouched. Successful temporary smoke permits one bounded
promotion with exact pre/post readback; a failed post-promotion smoke restores
the prior coherent runtime/image alias only when the rollback is unambiguous
and safe, otherwise the transaction fails closed with explicit recovery
evidence. Valid HOME/Relay/browser/session state is never rolled back merely
because the runtime/image is rolled back, and destructive HOME restore is
never automatic: this module contains no HOME restore path at all.

Scope is disposable-only in this Card. ``--scope`` accepts only
``disposable``; any production scope is refused because live production
cutover belongs to M07. Compose projects must live in the disposable
``pi-unraid-staged-`` namespace, and the known production HOME and
deployment-state paths are refused. Every run writes one machine-readable
record with phase identity, per-phase timings, expected/observed state and
the recovery decision.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "config" / "paseo-candidate.json"
COMPOSE_FILE = ROOT / "compose.yaml"
CONFIGURE_RUNTIME = ROOT / "scripts" / "configure-paseo-runtime.sh"
BUILDX_SCRIPT = ROOT / "scripts" / "paseo_buildx.py"
TOWER_SCRIPT = ROOT / "scripts" / "paseo_tower_build.py"

STAGED_SCHEMA_VERSION = 1
ANCHOR_SCHEMA_VERSION = 1
ACTIVE_SERVICE = "paseo"
DISPOSABLE_PROJECT_PREFIX = "pi-unraid-staged-"
STAGED_ALIAS = "pi-unraid:paseo-staged-active"
PRODUCTION_PROJECTS = frozenset({"pi-unraid"})
PRODUCTION_HOME = Path("/mnt/user/appdata/pi-unraid/paseo-home")
PRODUCTION_DEPLOYMENT_STATE = Path("/mnt/user/appdata/pi-unraid/deployment-state")
HOME_MARKER = ".paseo/config.json"
WRITE_PROBE = ".pi-unraid-write-probe"
MAX_HOME_ENTRIES = 20000

FORCE_TEMP_SMOKE_FAIL_ENV = "PI_UNRAID_STAGED_FORCE_TEMP_SMOKE_FAIL"
FORCE_POST_SMOKE_FAIL_ENV = "PI_UNRAID_STAGED_FORCE_POST_SMOKE_FAIL"

EXIT_FAILED = 1
EXIT_VALIDATION = 2


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


buildx = _load_module("paseo_staged_buildx", BUILDX_SCRIPT)
tower = _load_module("paseo_staged_tower", TOWER_SCRIPT)
resolver = buildx._load_resolver()


class StagedUpdateError(RuntimeError):
    """Fail-closed staged-update error."""


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


class Recorder:
    def __init__(self) -> None:
        self.phases: dict[str, dict] = {}

    def record(self, name: str, status: str, duration_ms: int, detail: dict) -> None:
        self.phases[name] = {"status": status, "duration_ms": duration_ms, "detail": detail}

    def skip_rest(self, names: list[str], reason: str) -> None:
        for name in names:
            if name not in self.phases:
                self.record(name, "skipped", 0, {"reason": reason})


# ---------------------------------------------------------------------------
# Scope and identity guards
# ---------------------------------------------------------------------------

def check_scope(scope: str) -> str:
    """Accept only the disposable scope; live cutover belongs to M07."""
    if (scope or "") != "disposable":
        raise StagedUpdateError(
            f"scope {scope!r} is refused: this transaction runs only against disposable "
            "runtimes; live production cutover belongs to M07"
        )
    return scope


def check_disposable_project(name: str, what: str = "compose project") -> str:
    """Require the disposable project namespace; refuse production names."""
    value = (name or "").strip()
    if not value:
        raise StagedUpdateError(f"{what} name is missing")
    if value in PRODUCTION_PROJECTS:
        raise StagedUpdateError(
            f"{what} {value!r} is a production name and is refused here; "
            "live production cutover belongs to M07"
        )
    if not value.startswith(DISPOSABLE_PROJECT_PREFIX):
        raise StagedUpdateError(
            f"{what} {value!r} is outside the disposable "
            f"{DISPOSABLE_PROJECT_PREFIX!r} namespace"
        )
    return value


def check_state_root(path: Path) -> Path:
    """Refuse the production deployment-state path as staged state."""
    resolved = path.expanduser()
    try:
        same = resolved.resolve() == PRODUCTION_DEPLOYMENT_STATE.resolve()
    except OSError:
        same = False
    if resolved == PRODUCTION_DEPLOYMENT_STATE or same:
        raise StagedUpdateError(
            f"state root {path} is the production deployment-state path and is refused"
        )
    return path


def check_home_host(path: Path) -> Path:
    """Refuse the production Paseo HOME as a disposable transaction HOME."""
    if path.expanduser() == PRODUCTION_HOME:
        raise StagedUpdateError(
            f"HOME host path {path} is the production Paseo HOME and is refused here"
        )
    return path


# ---------------------------------------------------------------------------
# Frozen candidate binding (read-only; never resolves a floating channel)
# ---------------------------------------------------------------------------

def load_frozen_candidate(path: Path) -> dict:
    try:
        raw = path.read_text()
    except FileNotFoundError as exc:
        raise StagedUpdateError(f"candidate file is missing: {path}") from exc
    except OSError as exc:
        raise StagedUpdateError(f"candidate file is unreadable: {path}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StagedUpdateError(f"candidate file is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise StagedUpdateError("candidate must be a JSON object")
    return data


def verify_frozen_binding(candidate: dict, dockerfile_text: str, context_dir: Path) -> dict:
    """Validate the frozen candidate and its build-context binding.

    Pure with respect to Docker/network: schema/identity validation goes
    through the M05-T01 resolver ``validate`` entrypoint, the
    ``candidate_id`` self-hash is recomputed, and the Dockerfile binding uses
    the shared M05-T02A verifier.
    """
    if not isinstance(candidate, dict):
        raise StagedUpdateError("candidate must be an object")
    try:
        resolver.validate(candidate)
    except resolver.ResolutionError as exc:
        raise StagedUpdateError(f"candidate failed validation: {exc}") from exc
    import hashlib

    claimed = candidate.get("candidate_id")
    material = {k: v for k, v in candidate.items() if k != "candidate_id"}
    expected = "sha256:" + hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if claimed != expected:
        raise StagedUpdateError("candidate_id does not match the frozen candidate material")
    try:
        readback = buildx.verify_build_inputs(candidate, dockerfile_text, context_dir)
    except buildx.BuildxError as exc:
        raise StagedUpdateError(f"build-context binding failed: {exc}") from exc
    return readback


# ---------------------------------------------------------------------------
# Anchors, HOME fingerprint and live readback
# ---------------------------------------------------------------------------

def fingerprint_home(home: Path) -> dict:
    """Fingerprint HOME structure without reading file contents.

    Only relative names, sizes and mtimes feed the digest, so secret-bearing
    HOME state never enters the transaction record. Content comparison is
    deliberately out of scope: preservation means no entry added, removed or
    resized/retouched across the bounded transaction window.
    """
    entries: list[list] = []
    truncated = False
    if home.is_dir():
        for item in sorted(home.rglob("*")):
            try:
                rel = item.relative_to(home).as_posix()
                if item.is_symlink() or item.is_file():
                    stat = item.stat()
                    entries.append([rel, stat.st_size, stat.st_mtime_ns])
                elif item.is_dir():
                    entries.append([rel + "/", 0, 0])
            except OSError:
                continue
            if len(entries) >= MAX_HOME_ENTRIES:
                truncated = True
                break
    import hashlib

    digest = "sha256:" + hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "path": str(home),
        "entries": len(entries),
        "truncated": truncated,
        "digest": digest,
    }


def load_anchor(path: Path, role: str) -> dict:
    try:
        raw = path.read_text()
    except FileNotFoundError as exc:
        raise StagedUpdateError(f"{role} anchor is missing: {path}") from exc
    except OSError as exc:
        raise StagedUpdateError(f"{role} anchor is unreadable: {path}") from exc
    try:
        anchor = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StagedUpdateError(f"{role} anchor is not valid JSON: {path}") from exc
    if not isinstance(anchor, dict):
        raise StagedUpdateError(f"{role} anchor must be a JSON object")
    if anchor.get("schema_version") != ANCHOR_SCHEMA_VERSION:
        raise StagedUpdateError(f"{role} anchor uses an unsupported schema")
    if anchor.get("role") != role:
        raise StagedUpdateError(f"{role} anchor carries role {anchor.get('role')!r}")
    for key in ("candidate_id", "image_tag", "image_id"):
        if not anchor.get(key):
            raise StagedUpdateError(f"{role} anchor lacks immutable identity: {key}")
    runtime = anchor.get("runtime")
    if not isinstance(runtime, dict) or not runtime.get("compose_project"):
        raise StagedUpdateError(f"{role} anchor lacks runtime identity")
    home = anchor.get("home")
    if not isinstance(home, dict) or not home.get("host_path"):
        raise StagedUpdateError(f"{role} anchor lacks HOME identity")
    return anchor


def write_anchor(path: Path, anchor: dict) -> None:
    atomic_write_json(path, anchor)


def read_live_image(run_fn, tag: str, env: dict[str, str]) -> dict:
    proc = run_fn(["docker", "image", "inspect", tag], env, 60)
    if proc.returncode != 0:
        raise StagedUpdateError(
            f"image inspect failed for {tag} (rc={proc.returncode}): "
            f"{_tail(proc.stderr or proc.stdout)}"
        )
    try:
        entry = json.loads(proc.stdout)[0]
    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        raise StagedUpdateError(f"image inspect returned unreadable JSON for {tag}") from exc
    labels = (entry.get("Config", {}) or {}).get("Labels") or {}
    image_id = entry.get("Id")
    if not image_id:
        raise StagedUpdateError(f"image {tag} has no immutable Id")
    return {"tag": tag, "id": image_id, "candidate_label": labels.get("io.pi-unraid.candidate-id")}


def read_live_container(run_fn, project: str, env: dict[str, str]) -> dict | None:
    """Read the single disposable active container, or None when absent.

    More than one container id for the service is ambiguous prior state and
    fails closed.
    """
    proc = run_fn(
        ["docker", "compose", "-p", project, "-f", str(COMPOSE_FILE),
         "ps", "-q", ACTIVE_SERVICE],
        env, 60,
    )
    if proc.returncode != 0:
        raise StagedUpdateError(
            f"compose ps failed for {project} (rc={proc.returncode}): "
            f"{_tail(proc.stderr or proc.stdout)}"
        )
    ids = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    if not ids:
        return None
    if len(ids) != 1:
        raise StagedUpdateError(
            f"ambiguous prior runtime: {len(ids)} containers answer for "
            f"{project}/{ACTIVE_SERVICE}"
        )
    inspect = run_fn(["docker", "inspect", ids[0]], env, 60)
    if inspect.returncode != 0:
        raise StagedUpdateError(f"container inspect failed for {ids[0][:12]}")
    try:
        entry = json.loads(inspect.stdout)[0]
    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        raise StagedUpdateError("container inspect returned unreadable JSON") from exc
    state = entry.get("State", {}) or {}
    health = (state.get("Health", {}) or {}).get("Status")
    return {
        "id": entry.get("Id"),
        "image": entry.get("Image"),
        "running": bool(state.get("Running")),
        "health": health,
    }


def check_home_marker_live(run_fn, home: Path, tag: str, uid: str, gid: str,
                           env: dict[str, str]) -> dict:
    """Read-only marker proof through the runtime identity, never host traversal."""
    if not home.is_dir():
        raise StagedUpdateError(f"HOME anchor is not a directory: {home}")
    marker = run_fn(
        ["docker", "run", "--rm", "--user", f"{uid}:{gid}",
         "-v", f"{home}:/home/paseo:ro", tag,
         "sh", "-c", f"test -f /home/paseo/{HOME_MARKER}"],
        env, 120,
    )
    if marker.returncode != 0:
        raise StagedUpdateError(
            f"HOME anchor lacks a runtime-readable marker {HOME_MARKER}: "
            f"{_tail(marker.stderr or marker.stdout)}"
        )
    return {"path": str(home), "marker": HOME_MARKER, "readable": True}


def check_home_live(run_fn, home: Path, tag: str, uid: str, gid: str,
                    env: dict[str, str]) -> dict:
    """Prove the HOME anchor is present and writable; read no HOME content."""
    marker = check_home_marker_live(run_fn, home, tag, uid, gid, env)
    probe = run_fn(
        ["docker", "run", "--rm", "--user", f"{uid}:{gid}",
         "-v", f"{home}:/home/paseo", tag,
         "sh", "-c", f"touch /home/paseo/{WRITE_PROBE} && rm /home/paseo/{WRITE_PROBE}"],
        env, 120,
    )
    if probe.returncode != 0:
        raise StagedUpdateError(
            f"HOME anchor is not writable through the runtime image: "
            f"{_tail(probe.stderr or probe.stdout)}"
        )
    return {**marker, "writable": True}


def retention_protects(retention_file: Path, tags: list[str]) -> dict:
    """Return per-tag protection readback from the Tower retention file."""
    try:
        retention = tower.load_retention(retention_file)
    except tower.TowerBuildError as exc:
        raise StagedUpdateError(f"retention readback failed: {exc}") from exc
    protected = {item.get("tag") for item in retention.get("entries", []) if item.get("tag")}
    return {tag: tag in protected for tag in tags}


# ---------------------------------------------------------------------------
# Compose helpers (disposable projects only)
# ---------------------------------------------------------------------------

def compose_env(home: Path, projects: Path, worktrees: Path, uid: str, gid: str) -> dict[str, str]:
    env = dict(os.environ)
    env["PASEO_HOME_HOST"] = str(home)
    env["PASEO_PROJECTS_HOST"] = str(projects)
    env["PASEO_WORKTREES_HOST"] = str(worktrees)
    env["PASEO_UID"] = uid
    env["PASEO_GID"] = gid
    return env


def write_override(path: Path, tag: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'services:\n  {ACTIVE_SERVICE}:\n    image: "{tag}"\n')


def compose_up(run_fn, project: str, files: list[Path], env: dict[str, str],
               timeout: int = 300) -> None:
    argv = ["docker", "compose", "-p", project]
    for item in files:
        argv += ["-f", str(item)]
    argv += ["up", "-d"]
    proc = run_fn(argv, env, timeout)
    if proc.returncode != 0:
        raise StagedUpdateError(
            f"compose up failed for {project} (rc={proc.returncode}): "
            f"{_tail(proc.stderr or proc.stdout)}"
        )


def compose_down(run_fn, project: str, files: list[Path], env: dict[str, str]) -> None:
    argv = ["docker", "compose", "-p", project]
    for item in files:
        argv += ["-f", str(item)]
    argv += ["down", "-v"]
    proc = run_fn(argv, env, 180)
    if proc.returncode != 0:
        raise StagedUpdateError(
            f"compose down failed for {project} (rc={proc.returncode}): "
            f"{_tail(proc.stderr or proc.stdout)}"
        )


def wait_running(run_fn, project: str, env: dict[str, str], timeout_s: int) -> dict:
    """Wait until exactly one running container answers; fail closed."""
    deadline = time.monotonic() + max(timeout_s, 1)
    last: dict | None = None
    while time.monotonic() < deadline:
        last = read_live_container(run_fn, project, env)
        if last is not None and last["running"]:
            return last
        time.sleep(2)
    raise StagedUpdateError(
        f"runtime {project}/{ACTIVE_SERVICE} never reached running: "
        f"{json.dumps(last, sort_keys=True) if last else 'absent'}"
    )


def runtime_probes(run_fn, container_id: str, image_id: str, candidate_id: str,
                   pi_version: str, env: dict[str, str]) -> list[dict]:
    """Fast bounded probes against one running runtime container."""
    probes: list[dict] = []

    def check(name: str, argv: list[str], timeout: int = 60) -> None:
        proc = run_fn(argv, env, timeout)
        if proc.returncode != 0:
            raise StagedUpdateError(
                f"runtime probe failed: {name} (rc={proc.returncode}): "
                f"{_tail(proc.stderr or proc.stdout)}"
            )
        probes.append({"name": name, "status": "ok", "observed": _tail(proc.stdout or "ok", 300)})

    inspect = run_fn(["docker", "inspect", container_id], env, 60)
    if inspect.returncode != 0:
        raise StagedUpdateError("runtime probe failed: container inspect")
    try:
        entry = json.loads(inspect.stdout)[0]
    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        raise StagedUpdateError("runtime probe failed: unreadable container inspect") from exc
    if entry.get("Image") != image_id:
        raise StagedUpdateError(
            "runtime probe failed: container image does not match the expected image"
        )
    probes.append({"name": "container_image", "status": "ok", "observed": entry.get("Image")})
    check("candidate_env", ["docker", "exec", container_id, "printenv", "PI_UNRAID_CANDIDATE_ID"])
    observed_candidate = (probes[-1]["observed"] or "").strip()
    if observed_candidate != candidate_id:
        raise StagedUpdateError(
            "runtime probe failed: container candidate env does not match the frozen candidate"
        )
    check("pi_present", ["docker", "exec", container_id, "sh", "-c", "command -v pi"])
    check("home_marker",
          ["docker", "exec", container_id, "test", "-f", f"/home/paseo/{HOME_MARKER}"])
    check("pi_version", ["docker", "exec", container_id, "pi", "--version"])
    if pi_version not in (probes[-1]["observed"] or ""):
        raise StagedUpdateError(
            "runtime probe failed: container Pi version does not match the frozen candidate"
        )
    return probes


def remove_temp_tree(state_root: Path, path: Path, run_fn=None,
                     image_tag: str | None = None,
                     env: dict[str, str] | None = None) -> None:
    """Remove only a transaction-owned temp tree under the state root.

    Host removal runs first. Temporary fixtures are chowned to the runtime
    uid/gid and containers running as that identity create restricted
    modes inside them, so an invoking user that owns neither the files nor
    the directories cannot remove the tree from the host. When host
    removal is blocked and a runner is available, one bounded root-owned
    container removes exactly the validated ``tmp-*`` leaf under the
    validated state root, with no shell interpolation. Anything left
    behind fails closed with the litter path; foreign paths are never
    mounted or removed, and cleanup failures are never suppressed.
    """
    root = state_root.resolve()
    target = path.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise StagedUpdateError(f"refusing to remove outside the state root: {path}") from exc
    if target == root or not target.name.startswith("tmp-"):
        raise StagedUpdateError(f"refusing to remove a non-temporary path: {path}")
    if not target.exists() and not target.is_symlink():
        return
    try:
        shutil.rmtree(target, ignore_errors=False)
        return
    except OSError as host_exc:
        if not target.exists() and not target.is_symlink():
            return
        if run_fn is None or image_tag is None:
            raise StagedUpdateError(
                f"temporary cleanup failed for {target}: {host_exc}; "
                "leftover disposable litter remains under the state root"
            ) from host_exc
        last_host_error = host_exc
    leaf = target.name
    proc = run_fn(
        ["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "rm",
         "-v", f"{root}:/cleanup-state", image_tag,
         "-rf", f"/cleanup-state/{leaf}"],
        env if env is not None else {}, 180,
    )
    if proc.returncode != 0:
        raise StagedUpdateError(
            f"temporary cleanup failed for {target}: {last_host_error}; "
            f"container repair also failed: {_tail(proc.stderr or proc.stdout)}; "
            "leftover disposable litter remains under the state root"
        ) from last_host_error
    if target.exists() or target.is_symlink():
        try:
            shutil.rmtree(target, ignore_errors=False)
        except OSError as retry_exc:
            raise StagedUpdateError(
                f"temporary cleanup failed for {target}: {retry_exc}; "
                "leftover disposable litter remains under the state root"
            ) from retry_exc


# ---------------------------------------------------------------------------
# Transaction phases
# ---------------------------------------------------------------------------

def phase_preflight(cfg: dict, run_fn, env: dict[str, str]) -> dict:
    """Verify frozen binding plus prior coherent anchors before any mutation."""
    candidate = load_frozen_candidate(cfg["candidate_path"])
    dockerfile_text = (cfg["context_dir"] / "Dockerfile").read_text()
    readback = verify_frozen_binding(candidate, dockerfile_text, cfg["context_dir"])
    candidate_id = readback["candidate_id"]
    tag = buildx.image_tag(candidate_id)

    active = load_anchor(cfg["active_file"], "active")
    rollback_anchor = load_anchor(cfg["rollback_file"], "rollback")
    if active["home"]["host_path"] != str(cfg["home_host"]):
        raise StagedUpdateError("active anchor HOME does not match the transaction HOME")
    if active["runtime"]["compose_project"] != cfg["active_project"]:
        raise StagedUpdateError("active anchor runtime does not match the transaction runtime")

    live_image = read_live_image(run_fn, active["image_tag"], env)
    if live_image["id"] != active["image_id"]:
        raise StagedUpdateError("live active image id does not match the active anchor")
    if live_image["candidate_label"] != active["candidate_id"]:
        raise StagedUpdateError("live active candidate label does not match the active anchor")
    live_container = read_live_container(run_fn, cfg["active_project"], env)
    if live_container is None or not live_container["running"]:
        raise StagedUpdateError("prior active runtime is not running; prior state is ambiguous")
    if live_container["image"] != active["image_id"]:
        raise StagedUpdateError("prior active container image does not match the active anchor")
    rollback_live = read_live_image(run_fn, rollback_anchor["image_tag"], env)
    if rollback_live["id"] != rollback_anchor["image_id"]:
        raise StagedUpdateError("live rollback image id does not match the rollback anchor")
    home_live = check_home_live(
        run_fn, cfg["home_host"], active["image_tag"], cfg["uid"], cfg["gid"], env)
    home_fp = fingerprint_home(cfg["home_host"])
    protection = retention_protects(
        cfg["retention_file"], [active["image_tag"], rollback_anchor["image_tag"]])
    missing = sorted(tag_name for tag_name, kept in protection.items() if not kept)
    if missing:
        raise StagedUpdateError(
            f"retention does not protect rollback anchors: {', '.join(missing)}"
        )
    return {
        "expected": {
            "candidate_id": candidate_id,
            "image_tag": tag,
            "active": {k: active[k] for k in ("candidate_id", "image_tag", "image_id")},
            "rollback": {k: rollback_anchor[k]
                         for k in ("candidate_id", "image_tag", "image_id")},
        },
        "observed": {
            "candidate_id": candidate_id,
            "image_tag": tag,
            "live_image": live_image,
            "live_container": {k: live_container[k] for k in ("image", "running", "health")},
            "rollback_image": rollback_live,
            "home": {**home_live, "fingerprint": home_fp},
            "retention": protection,
            "pi_version": readback["pi_version"],
        },
        "readback": readback,
    }


def phase_build(cfg: dict) -> dict:
    """Build the frozen candidate image; no smoke runs inside this phase."""
    record_path = cfg["state_root"] / f"build-{_stamp()}-{os.getpid()}.json"
    argv = ["build", "--candidate", str(cfg["candidate_path"]),
           "--context", str(cfg["context_dir"]), "--record", str(record_path),
           "--builder", cfg["builder"], "--state-dir", str(cfg["buildx_state_dir"]),
           "--progress", "plain", "--build-timeout", str(cfg["build_timeout"])]
    if cfg.get("cache_dir"):
        argv += ["--cache-dir", str(cfg["cache_dir"])]
    rc = buildx.main(argv)
    if rc != 0:
        raise StagedUpdateError(f"candidate build failed (rc={rc})")
    try:
        record = buildx.load_build_record(record_path)
    except buildx.BuildxError as exc:
        raise StagedUpdateError(f"build record is unreadable: {exc}") from exc
    phases = record.get("phases") or {}
    if (phases.get("build") or {}).get("status") != "ok":
        raise StagedUpdateError("build record has no successful build phase")
    image = record.get("image") or {}
    if not image.get("id"):
        raise StagedUpdateError("build record lacks an immutable image id")
    if image.get("candidate_label") != (record.get("candidate") or {}).get("candidate_id"):
        raise StagedUpdateError("build record candidate label does not match its candidate")
    return {
        "expected": {"candidate_id": cfg["candidate_id"]},
        "observed": {"tag": record.get("tag"), "image_id": image.get("id"),
                     "record": str(record_path),
                     "cached_steps": (phases.get("build") or {}).get("detail", {}).get(
                         "cached_steps")},
        "record_path": str(record_path),
        "record": record,
    }


def phase_fast_checks(cfg: dict, run_fn, env: dict[str, str], build: dict) -> dict:
    """Bind/test the built image to the frozen candidate, then protect it."""
    record_path = Path(build["record_path"])
    record = build["record"]
    tag = record.get("tag")
    if tag != cfg["image_tag"]:
        raise StagedUpdateError("built tag does not match the frozen candidate tag")
    live = read_live_image(run_fn, tag, env)
    if live["id"] != (record.get("image") or {}).get("id"):
        raise StagedUpdateError("live image id does not match the build record")
    if live["candidate_label"] != cfg["candidate_id"]:
        raise StagedUpdateError("live candidate label does not match the frozen candidate")
    test_rc = buildx.main(
        ["test", "--record", str(record_path),
         "--smoke-timeout", str(cfg["smoke_timeout"])])
    if test_rc != 0:
        raise StagedUpdateError(f"candidate fast smoke/test failed (rc={test_rc})")
    try:
        record = buildx.load_build_record(record_path)
    except buildx.BuildxError as exc:
        raise StagedUpdateError(f"tested build record is unreadable: {exc}") from exc
    build["record"] = record
    profile = {"state_dir": Path(cfg["buildx_state_dir"]),
               "retention_file": Path(cfg["retention_file"])}
    try:
        retention = tower.retain_record(profile, record_path, cfg["retain"])
    except tower.TowerBuildError as exc:
        raise StagedUpdateError(f"retention of the new image failed: {exc}") from exc
    protected = {item.get("tag") for item in retention.get("entries", []) if item.get("tag")}
    required = {cfg["active_anchor"]["image_tag"],
                cfg["rollback_anchor"]["image_tag"], tag}
    if not required.issubset(protected):
        raise StagedUpdateError("retention lost a required active/rollback/new image entry")
    return {
        "expected": {"tag": tag, "image_id": live["id"],
                     "candidate_id": cfg["candidate_id"]},
        "observed": {"image": live, "retention": sorted(protected)},
    }


def phase_temp_smoke(cfg: dict, run_fn, env: dict[str, str]) -> dict:
    """Gate promotion on a temporary non-production runtime plus full smoke."""
    if os.environ.get(FORCE_TEMP_SMOKE_FAIL_ENV) == "1":
        raise StagedUpdateError("injected temporary-smoke failure")
    tmp_project = check_disposable_project(
        f"{DISPOSABLE_PROJECT_PREFIX}tmp-{_stamp()}-{os.getpid()}".lower()
        .replace(":", "").replace("_", "-")[:60],
        "temporary runtime",
    )
    tmp_root = cfg["state_root"] / f"tmp-{_stamp()}-{os.getpid()}"
    home = tmp_root / "home"
    projects = tmp_root / "projects"
    worktrees = tmp_root / "worktrees"
    for item in (home, projects, worktrees):
        item.mkdir(parents=True)
    tmp_env = compose_env(home, projects, worktrees, cfg["uid"], cfg["gid"])
    try:
        chown = run_fn(
            ["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "chown",
             "-v", f"{tmp_root}:/fixture", cfg["image_tag"],
             "-R", f"{cfg['uid']}:{cfg['gid']}",
             "/fixture/home", "/fixture/projects", "/fixture/worktrees"],
            env, 180,
        )
        if chown.returncode != 0:
            raise StagedUpdateError("temporary fixture ownership setup failed")
        configured = run_fn(
            ["bash", str(CONFIGURE_RUNTIME), cfg["image_tag"], str(home),
             str(worktrees), cfg["uid"], cfg["gid"]],
            env, 300,
        )
        if configured.returncode != 0:
            raise StagedUpdateError(
                f"temporary HOME configuration failed: "
                f"{_tail(configured.stderr or configured.stdout)}"
            )
        # Relay consent simulation stays inside this disposable fixture: the
        # pairing offer is captured and never printed.
        pair = run_fn(
            ["docker", "run", "--rm", "--user", f"{cfg['uid']}:{cfg['gid']}",
             "-v", f"{home}:/home/paseo", cfg["image_tag"],
             "paseo", "daemon", "pair", "--relay", "--json", "--home", "/home/paseo/.paseo"],
            env, 120,
        )
        if pair.returncode != 0:
            raise StagedUpdateError("temporary Relay pairing simulation failed")
        tmp_override = tmp_root / "tmp.override.yaml"
        write_override(tmp_override, cfg["image_tag"])
        compose_up(run_fn, tmp_project, [COMPOSE_FILE, tmp_override], tmp_env)
        try:
            live = wait_running(run_fn, tmp_project, tmp_env, cfg["wait_timeout"])
            probes = runtime_probes(
                run_fn, live["id"], cfg["image_id"], cfg["candidate_id"],
                cfg["pi_version"], tmp_env)
        finally:
            compose_down(run_fn, tmp_project, [COMPOSE_FILE, tmp_override], tmp_env)
        suite = (buildx.load_build_record(
            Path(cfg["build_record_path"])).get("phases", {}).get("test", {}).get("detail", {}))
    finally:
        in_flight = sys.exception()
        try:
            remove_temp_tree(cfg["state_root"], tmp_root, run_fn=run_fn,
                             image_tag=cfg["image_tag"], env=env)
        except StagedUpdateError as cleanup_exc:
            if in_flight is None:
                raise
            raise StagedUpdateError(
                f"{in_flight}; temporary cleanup also failed: {cleanup_exc}"
            ) from in_flight
    after = fingerprint_home(cfg["home_host"])
    if after["digest"] != cfg["home_fingerprint"]["digest"]:
        raise StagedUpdateError("persistent HOME changed during temporary smoke")
    return {
        "expected": {"image_tag": cfg["image_tag"], "image_id": cfg["image_id"],
                     "project": tmp_project},
        "observed": {"probes": probes, "suite": suite,
                     "home_preserved": True, "project": tmp_project},
    }


def phase_promote(cfg: dict, run_fn, env: dict[str, str]) -> dict:
    """Bounded promotion of the disposable active runtime with readback."""
    before_container = read_live_container(run_fn, cfg["active_project"], env)
    before_home = fingerprint_home(cfg["home_host"])
    tag_alias = run_fn(
        ["docker", "tag", cfg["image_id"], STAGED_ALIAS], env, 120)
    if tag_alias.returncode != 0:
        raise StagedUpdateError("promotion alias tagging failed")
    write_override(cfg["override_file"], cfg["image_tag"])
    compose_up(run_fn, cfg["active_project"],
               [COMPOSE_FILE, cfg["override_file"]], env)
    live = wait_running(run_fn, cfg["active_project"], env, cfg["wait_timeout"])
    if live["image"] != cfg["image_id"]:
        raise StagedUpdateError("promoted container image does not match the new image")
    alias_live = read_live_image(run_fn, STAGED_ALIAS, env)
    if alias_live["id"] != cfg["image_id"]:
        raise StagedUpdateError("promotion alias does not resolve to the new image")
    after_home = fingerprint_home(cfg["home_host"])
    if after_home["digest"] != before_home["digest"]:
        raise StagedUpdateError("persistent HOME changed during promotion")
    active = {
        "schema_version": ANCHOR_SCHEMA_VERSION,
        "role": "active",
        "candidate_id": cfg["candidate_id"],
        "image_tag": cfg["image_tag"],
        "image_id": cfg["image_id"],
        "runtime": {"compose_project": cfg["active_project"],
                    "service": ACTIVE_SERVICE, "container_id": live["id"]},
        "home": {"host_path": str(cfg["home_host"])},
        "recorded_at": _utcnow(),
    }
    write_anchor(cfg["active_file"], active)
    return {
        "expected": {"image_tag": cfg["image_tag"], "image_id": cfg["image_id"]},
        "observed": {
            "before_container": ({k: before_container[k] for k in ("image", "running")}
                                 if before_container else None),
            "container": {k: live[k] for k in ("image", "running", "health")},
            "alias": alias_live,
            "home_preserved": True,
        },
    }


def phase_post_smoke(cfg: dict, run_fn, env: dict[str, str]) -> dict:
    """Verify the promoted disposable runtime; HOME must be preserved."""
    if os.environ.get(FORCE_POST_SMOKE_FAIL_ENV) == "1":
        raise StagedUpdateError("injected post-promotion-smoke failure")
    live = read_live_container(run_fn, cfg["active_project"], env)
    if live is None or not live["running"]:
        raise StagedUpdateError("promoted runtime is not running")
    if live["image"] != cfg["image_id"]:
        raise StagedUpdateError("promoted runtime image does not match the new image")
    probes = runtime_probes(
        run_fn, live["id"], cfg["image_id"], cfg["candidate_id"],
        cfg["pi_version"], env)
    alias_live = read_live_image(run_fn, STAGED_ALIAS, env)
    if alias_live["id"] != cfg["image_id"]:
        raise StagedUpdateError("post-promotion alias does not resolve to the new image")
    after = fingerprint_home(cfg["home_host"])
    if after["digest"] != cfg["home_fingerprint"]["digest"]:
        raise StagedUpdateError("persistent HOME changed across promotion")
    return {
        "expected": {"image_tag": cfg["image_tag"], "image_id": cfg["image_id"]},
        "observed": {"probes": probes, "alias": alias_live, "home_preserved": True},
    }


def rollback_unambiguous(cfg: dict, run_fn, env: dict[str, str]) -> tuple[bool, str]:
    """Decide whether automatic restoration of the prior anchor is safe.

    Restoration is unambiguous only when the recorded prior anchor is
    intact, its image is live with matching identity, and HOME is preserved.
    Anything else fails closed; HOME state is never restored automatically.
    """
    try:
        prior = load_anchor(cfg["rollback_file"], "rollback")
    except StagedUpdateError as exc:
        return False, f"rollback anchor is not usable: {exc}"
    try:
        live = read_live_image(run_fn, prior["image_tag"], env)
    except StagedUpdateError as exc:
        return False, f"prior image is not available: {exc}"
    if live["id"] != prior["image_id"]:
        return False, "live prior image id does not match the rollback anchor"
    if live["candidate_label"] != prior["candidate_id"]:
        return False, "live prior candidate label does not match the rollback anchor"
    after = fingerprint_home(cfg["home_host"])
    if after["digest"] != cfg["home_fingerprint"]["digest"]:
        return False, "HOME changed across promotion; automatic restore is unsafe"
    protection = retention_protects(cfg["retention_file"], [prior["image_tag"]])
    if not protection.get(prior["image_tag"]):
        return False, "prior image lost retention protection"
    return True, "prior anchor, image, retention and HOME are coherent"


def phase_rollback(cfg: dict, run_fn, env: dict[str, str], prior: dict) -> dict:
    """Restore the prior coherent runtime/image alias; HOME stays untouched."""
    before_home = fingerprint_home(cfg["home_host"])
    tag_alias = run_fn(["docker", "tag", prior["image_id"], STAGED_ALIAS], env, 120)
    if tag_alias.returncode != 0:
        raise StagedUpdateError("rollback alias tagging failed")
    write_override(cfg["override_file"], prior["image_tag"])
    compose_up(run_fn, cfg["active_project"],
               [COMPOSE_FILE, cfg["override_file"]], env)
    live = wait_running(run_fn, cfg["active_project"], env, cfg["wait_timeout"])
    if live["image"] != prior["image_id"]:
        raise StagedUpdateError("restored container image does not match the prior image")
    probes = runtime_probes(
        run_fn, live["id"], prior["image_id"], prior["candidate_id"],
        cfg["prior_pi_version"], env)
    after_home = fingerprint_home(cfg["home_host"])
    if after_home["digest"] != before_home["digest"]:
        raise StagedUpdateError("persistent HOME changed during rollback")
    restored = {
        "schema_version": ANCHOR_SCHEMA_VERSION,
        "role": "active",
        "candidate_id": prior["candidate_id"],
        "image_tag": prior["image_tag"],
        "image_id": prior["image_id"],
        "runtime": {"compose_project": cfg["active_project"],
                    "service": ACTIVE_SERVICE, "container_id": live["id"]},
        "home": {"host_path": str(cfg["home_host"])},
        "recorded_at": _utcnow(),
    }
    write_anchor(cfg["active_file"], restored)
    return {
        "expected": {"image_tag": prior["image_tag"], "image_id": prior["image_id"]},
        "observed": {
            "container": {k: live[k] for k in ("image", "running", "health")},
            "probes": probes,
            "home_preserved": True,
        },
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def base_config(args: argparse.Namespace) -> dict:
    check_scope(args.scope)
    project = check_disposable_project(args.active_project, "active runtime")
    state_root = check_state_root(Path(args.state_root))
    home_host = check_home_host(Path(args.home_host))
    projects_host = Path(args.projects_host)
    worktrees_host = Path(args.worktrees_host)
    tower_root = Path(args.tower_root)
    return {
        "scope": "disposable",
        "candidate_path": Path(args.candidate),
        "context_dir": Path(args.context),
        "state_root": state_root,
        "active_file": state_root / "active.json",
        "rollback_file": state_root / "rollback.json",
        "override_file": state_root / "active.override.yaml",
        "retention_file": tower_root / "retention.json",
        "active_project": project,
        "home_host": home_host,
        "projects_host": projects_host,
        "worktrees_host": worktrees_host,
        "uid": args.uid,
        "gid": args.gid,
        "builder": args.builder,
        "buildx_state_dir": Path(args.buildx_state_dir),
        "cache_dir": Path(args.cache_dir) if args.cache_dir else None,
        "retain": args.retain,
        "build_timeout": args.build_timeout,
        "smoke_timeout": args.smoke_timeout,
        "wait_timeout": args.wait_timeout,
    }


def cmd_update(args: argparse.Namespace) -> int:
    try:
        cfg = base_config(args)
    except StagedUpdateError as exc:
        print(f"staged update refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    recorder = Recorder()
    started = _utcnow()
    state_root = cfg["state_root"]
    state_root.mkdir(parents=True, exist_ok=True)
    record_path = Path(args.record) if args.record else state_root / f"staged-{_stamp()}.json"
    env = compose_env(cfg["home_host"], cfg["projects_host"], cfg["worktrees_host"],
                      cfg["uid"], cfg["gid"])
    run_fn = _run
    outcome = "failed"
    recovery: dict = {"trigger": "none", "decision": "none", "reason": "not started"}
    summary: dict = {"candidate_id": "", "image_tag": "", "image_id": ""}

    def finish(code: int) -> int:
        record = {
            "schema_version": STAGED_SCHEMA_VERSION,
            "command": "update",
            "scope": "disposable",
            "state_root": str(state_root),
            "candidate": {"path": str(cfg["candidate_path"]),
                          "candidate_id": summary["candidate_id"]},
            "active_project": cfg["active_project"],
            "home": {"host_path": str(cfg["home_host"])},
            "new_image": {"tag": summary["image_tag"], "id": summary["image_id"]},
            "outcome": outcome,
            "recovery": recovery,
            "started_at": started,
            "finished_at": _utcnow(),
            "phase_order": list(recorder.phases),
            "phases": recorder.phases,
        }
        atomic_write_json(record_path, record)
        print(json.dumps({"outcome": outcome, "recovery": recovery,
                          "record": str(record_path)}, sort_keys=True))
        return code

    # Phase 1: preflight (no mutation).
    begin = time.monotonic()
    try:
        preflight = phase_preflight(cfg, run_fn, env)
    except (StagedUpdateError, OSError) as exc:
        recorder.record("preflight", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["build", "fast_checks", "temp_smoke", "promote",
                            "post_smoke", "rollback"], "prior phase failed")
        outcome = "failed"
        recovery = {"trigger": "preflight", "decision": "no_mutation",
                    "reason": f"preflight refused the transaction: {exc}"}
        return finish(EXIT_VALIDATION)
    recorder.record("preflight", "ok", int((time.monotonic() - begin) * 1000),
                    {k: preflight[k] for k in ("expected", "observed")})
    cfg["candidate_id"] = preflight["expected"]["candidate_id"]
    cfg["image_tag"] = preflight["expected"]["image_tag"]
    cfg["pi_version"] = preflight["observed"]["pi_version"]
    cfg["home_fingerprint"] = preflight["observed"]["home"]["fingerprint"]
    cfg["active_anchor"] = load_anchor(cfg["active_file"], "active")
    cfg["rollback_anchor"] = load_anchor(cfg["rollback_file"], "rollback")
    prior_candidate = load_frozen_candidate(cfg["candidate_path"])
    try:
        cfg["prior_pi_version"] = (
            cfg["rollback_anchor"].get("pi_version")
            or prior_candidate["components"]["pi"]["version"]
        )
    except KeyError:
        cfg["prior_pi_version"] = prior_candidate["components"]["pi"]["version"]
    summary["candidate_id"] = cfg["candidate_id"]
    summary["image_tag"] = cfg["image_tag"]

    # Phase 2: build.
    begin = time.monotonic()
    try:
        build = phase_build(cfg)
    except StagedUpdateError as exc:
        recorder.record("build", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["fast_checks", "temp_smoke", "promote",
                            "post_smoke", "rollback"], "prior phase failed")
        outcome = "failed"
        recovery = {"trigger": "build", "decision": "no_mutation",
                    "reason": f"build failed before promotion: {exc}"}
        return finish(EXIT_FAILED)
    recorder.record("build", "ok", int((time.monotonic() - begin) * 1000),
                    {k: build[k] for k in ("expected", "observed")})
    cfg["image_id"] = build["observed"]["image_id"]
    cfg["build_record_path"] = build["record_path"]
    summary["image_id"] = cfg["image_id"]

    # Phase 3: fast checks.
    begin = time.monotonic()
    try:
        fast = phase_fast_checks(cfg, run_fn, env, build)
    except StagedUpdateError as exc:
        recorder.record("fast_checks", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["temp_smoke", "promote", "post_smoke", "rollback"],
                           "prior phase failed")
        outcome = "failed"
        recovery = {"trigger": "fast_checks", "decision": "no_mutation",
                    "reason": f"fast checks failed before promotion: {exc}"}
        return finish(EXIT_FAILED)
    recorder.record("fast_checks", "ok", int((time.monotonic() - begin) * 1000),
                    {k: fast[k] for k in ("expected", "observed")})

    # Phase 4: temporary smoke (promotion gate).
    begin = time.monotonic()
    try:
        temp = phase_temp_smoke(cfg, run_fn, env)
    except StagedUpdateError as exc:
        recorder.record("temp_smoke", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["promote", "post_smoke", "rollback"], "prior phase failed")
        outcome = "failed"
        recovery = {"trigger": "temp_smoke", "decision": "no_mutation",
                    "reason": f"temporary smoke failed; active runtime left untouched: {exc}"}
        return finish(EXIT_FAILED)
    recorder.record("temp_smoke", "ok", int((time.monotonic() - begin) * 1000),
                    {k: temp[k] for k in ("expected", "observed")})

    # Phase 5: bounded promotion.
    begin = time.monotonic()
    try:
        promoted = phase_promote(cfg, run_fn, env)
    except StagedUpdateError as exc:
        recorder.record("promote", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["post_smoke", "rollback"], "prior phase failed")
        outcome = "fail_closed"
        recovery = {"trigger": "promote", "decision": "fail_closed",
                    "reason": f"promotion failed mid-cutover; manual readback required: {exc}"}
        return finish(EXIT_FAILED)
    recorder.record("promote", "ok", int((time.monotonic() - begin) * 1000),
                    {k: promoted[k] for k in ("expected", "observed")})

    # Phase 6: post-promotion smoke.
    begin = time.monotonic()
    try:
        post = phase_post_smoke(cfg, run_fn, env)
    except StagedUpdateError as exc:
        recorder.record("post_smoke", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        # Phase 7: automatic rollback only when unambiguous and safe.
        rollback_begin = time.monotonic()
        safe, verdict = rollback_unambiguous(cfg, run_fn, env)
        if not safe:
            recorder.record("rollback", "skipped", 0, {"reason": verdict})
            outcome = "fail_closed"
            recovery = {"trigger": "post_smoke", "decision": "fail_closed",
                        "reason": f"post-promotion smoke failed and rollback is ambiguous: "
                                  f"{exc}; {verdict}"}
            return finish(EXIT_FAILED)
        try:
            rolled = phase_rollback(cfg, run_fn, env, cfg["rollback_anchor"])
        except StagedUpdateError as rollback_exc:
            recorder.record("rollback", "failed",
                            int((time.monotonic() - rollback_begin) * 1000),
                            {"error": str(rollback_exc)})
            outcome = "fail_closed"
            recovery = {"trigger": "post_smoke", "decision": "fail_closed",
                        "reason": f"post-promotion smoke failed ({exc}) and automatic "
                                  f"rollback failed ({rollback_exc}); manual readback required"}
            return finish(EXIT_FAILED)
        recorder.record("rollback", "ok",
                        int((time.monotonic() - rollback_begin) * 1000),
                        {k: rolled[k] for k in ("expected", "observed")})
        outcome = "rolled_back"
        recovery = {"trigger": "post_smoke", "decision": "rolled_back",
                    "reason": f"post-promotion smoke failed ({exc}); prior coherent "
                              f"runtime/image alias restored; HOME preserved"}
        return finish(EXIT_FAILED)
    recorder.record("post_smoke", "ok", int((time.monotonic() - begin) * 1000),
                    {k: post[k] for k in ("expected", "observed")})
    recorder.record("rollback", "skipped", 0, {"reason": "post-promotion smoke passed"})
    # Promotion succeeded: the pre-promotion anchor becomes the rollback anchor.
    write_anchor(cfg["rollback_file"], {**cfg["active_anchor"], "role": "rollback"})
    outcome = "promoted"
    recovery = {"trigger": "none", "decision": "promoted",
                "reason": "all phases passed; prior anchor retained as rollback anchor"}
    return finish(0)


def cmd_init(args: argparse.Namespace) -> int:
    """Seed disposable active/rollback anchors from verified live state."""
    try:
        check_scope(args.scope)
        project = check_disposable_project(args.active_project, "active runtime")
        state_root = check_state_root(Path(args.state_root))
        home_host = check_home_host(Path(args.home_host))
        candidate = load_frozen_candidate(Path(args.candidate))
        context_dir = Path(args.context)
        readback = verify_frozen_binding(
            candidate, (context_dir / "Dockerfile").read_text(), context_dir)
    except (StagedUpdateError, OSError) as exc:
        print(f"staged init refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    candidate_id = readback["candidate_id"]
    tag = buildx.image_tag(candidate_id)
    state_root.mkdir(parents=True, exist_ok=True)
    active_file = state_root / "active.json"
    rollback_file = state_root / "rollback.json"
    override_file = state_root / "active.override.yaml"
    retention_file = Path(args.tower_root) / "retention.json"
    if not args.force and (active_file.exists() or rollback_file.exists()):
        print("staged init refused: anchors already exist; pass --force to re-seed",
              file=sys.stderr)
        return EXIT_VALIDATION
    env = compose_env(home_host, Path(args.projects_host), Path(args.worktrees_host),
                      args.uid, args.gid)
    try:
        live_image = read_live_image(_run, tag, env)
        if live_image["candidate_label"] != candidate_id:
            raise StagedUpdateError("seed image candidate label does not match the candidate")
        home_live = check_home_live(_run, home_host, tag, args.uid, args.gid, env)
        home_fp = fingerprint_home(home_host)
        protection = retention_protects(retention_file, [tag])
        if not protection.get(tag):
            raise StagedUpdateError(f"seed image is not retention-protected: {tag}")
        write_override(override_file, tag)
        compose_up(_run, project, [COMPOSE_FILE, override_file], env)
        live = wait_running(_run, project, env, args.wait_timeout)
        if live["image"] != live_image["id"]:
            raise StagedUpdateError("seed container image does not match the seed image")
        probes = runtime_probes(
            _run, live["id"], live_image["id"], candidate_id,
            readback["pi_version"], env)
    except StagedUpdateError as exc:
        print(f"staged init failed: {exc}", file=sys.stderr)
        return EXIT_FAILED
    anchor = {
        "schema_version": ANCHOR_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "image_tag": tag,
        "image_id": live_image["id"],
        "runtime": {"compose_project": project, "service": ACTIVE_SERVICE,
                    "container_id": live["id"]},
        "home": {"host_path": str(home_host)},
        "pi_version": readback["pi_version"],
        "recorded_at": _utcnow(),
    }
    write_anchor(active_file, {**anchor, "role": "active"})
    write_anchor(rollback_file, {**anchor, "role": "rollback", "seed": True})
    print(json.dumps({
        "active": str(active_file), "rollback": str(rollback_file),
        "image": live_image["id"], "home": home_live,
        "home_fingerprint": home_fp["digest"], "probes": len(probes),
    }, sort_keys=True))
    return 0


def cmd_readback(args: argparse.Namespace) -> int:
    """Idempotent live-versus-recorded readback; never mutates."""
    try:
        check_scope(args.scope)
        project = check_disposable_project(args.active_project, "active runtime")
        state_root = check_state_root(Path(args.state_root))
        active = load_anchor(state_root / "active.json", "active")
        rollback_anchor = load_anchor(state_root / "rollback.json", "rollback")
    except StagedUpdateError as exc:
        print(f"staged readback refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    env = compose_env(Path(args.home_host), Path(args.projects_host),
                      Path(args.worktrees_host), args.uid, args.gid)
    mismatches: list[str] = []
    live: dict = {"image": None, "container": None, "home": None, "retention": None}
    try:
        live["image"] = read_live_image(_run, active["image_tag"], env)
        if live["image"]["id"] != active["image_id"]:
            mismatches.append("active image id differs from the recorded anchor")
        if live["image"]["candidate_label"] != active["candidate_id"]:
            mismatches.append("active candidate label differs from the recorded anchor")
    except StagedUpdateError as exc:
        mismatches.append(f"active image readback failed: {exc}")
    try:
        container = read_live_container(_run, project, env)
        live["container"] = container
        if container is None or not container["running"]:
            mismatches.append("active runtime is not running")
        elif container["image"] != active["image_id"]:
            mismatches.append("active container image differs from the recorded anchor")
    except StagedUpdateError as exc:
        mismatches.append(f"active runtime readback failed: {exc}")
    home = Path(args.home_host)
    try:
        marker = check_home_marker_live(
            _run, home, active["image_tag"], args.uid, args.gid, env)
        live["home"] = {**marker, "fingerprint": fingerprint_home(home)}
    except StagedUpdateError as exc:
        live["home"] = {"path": str(home)}
        mismatches.append(f"HOME anchor marker readback failed: {exc}")
    try:
        live["retention"] = retention_protects(
            Path(args.tower_root) / "retention.json",
            [active["image_tag"], rollback_anchor["image_tag"]])
        for tag_name, kept in live["retention"].items():
            if not kept:
                mismatches.append(f"retention no longer protects {tag_name}")
    except StagedUpdateError as exc:
        mismatches.append(f"retention readback failed: {exc}")
    payload = {
        "schema_version": STAGED_SCHEMA_VERSION,
        "scope": "disposable",
        "state_root": str(state_root),
        "recorded": {"active": active, "rollback": rollback_anchor},
        "live": live,
        "coherent": not mismatches,
        "mismatches": mismatches,
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0 if not mismatches else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reusable Paseo staged-update transaction over disposable runtimes.")
    parser.add_argument("--scope", default="disposable",
                        help="only 'disposable' is accepted; M07 owns live cutover")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--candidate", default=str(DEFAULT_CANDIDATE))
        target.add_argument("--context", default=str(ROOT))
        target.add_argument("--state-root", required=True)
        target.add_argument("--tower-root", required=True,
                            help="directory holding retention.json")
        target.add_argument("--active-project", default=f"{DISPOSABLE_PROJECT_PREFIX}active")
        target.add_argument("--home-host", required=True)
        target.add_argument("--projects-host", required=True)
        target.add_argument("--worktrees-host", required=True)
        target.add_argument("--uid", default="99")
        target.add_argument("--gid", default="100")
        target.add_argument("--wait-timeout", type=int, default=180)

    update = sub.add_parser("update", help="run the full staged-update transaction")
    common(update)
    update.add_argument("--record", default=None)
    update.add_argument("--builder", default="pi-unraid-paseo")
    update.add_argument("--buildx-state-dir",
                        default=str(Path.home() / ".local/share/pi-unraid/buildx"))
    update.add_argument("--cache-dir", default=None)
    update.add_argument("--retain", type=int, default=3)
    update.add_argument("--build-timeout", type=int, default=3600)
    update.add_argument("--smoke-timeout", type=int, default=600)

    init = sub.add_parser("init", help="seed disposable anchors from verified live state")
    common(init)
    init.add_argument("--force", action="store_true")

    readback = sub.add_parser("readback", help="idempotent live-versus-recorded readback")
    common(readback)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "update":
        return cmd_update(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "readback":
        return cmd_readback(args)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
