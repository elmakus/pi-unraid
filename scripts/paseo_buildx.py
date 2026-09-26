#!/usr/bin/env python3
"""Repeatable local Buildx/BuildKit build path for the frozen Paseo child image (M05-T02A).

Builds only the frozen accepted candidate (``config/paseo-candidate.json``) or an
explicitly staged candidate file. Never resolves versions from the network: the
candidate is validated read-only with the M05-T01 resolver and the build context
Dockerfile must match its immutable identities, otherwise the run fails closed
before any Docker invocation.

The build uses a dedicated named ``docker-container`` Buildx builder that is
separate from the Workstation builder namespace and from the ``paseo`` runtime
container/service. Builder state lives under a configurable persistent
directory (used as ``DOCKER_CONFIG`` for buildx state); an optional local
cache directory adds a portable ``type=local`` cache backend. No registry
push/pull, no registry cache and no login happen here; those surfaces belong
to M05-T02B.

Every ``build`` run writes one machine-readable record with the immutable
image identity, structured provenance and per-phase timings for the
resolution/readback, build, test and prune phases, so cold and warm runs can
be compared. The acceptance flow is ``build`` then ``test`` then ``prune``
against that same record: ``test`` runs the complete disposable smoke suite
and measures the test phase, and ``prune`` is gated on that exact record
showing a successful build and test before it runs the bounded cleanup and
measures the prune phase. There is no unconditional cleanup path:
``build --with-prune`` requires ``--with-smoke`` in the same invocation, and
standalone ``prune`` requires ``--record`` pointing at a successfully tested
build record for the same builder. A failed smoke prevents prune and leaves
the prior coherent cache and images untouched. Cache cleanup is bounded
(``--keep-storage`` only, no age filter, never before the build) and runs
only after successful work.

Portability note: on an ephemeral CI host the named builder persists across
steps within one job, so the cold/warm cache-reuse proof there is within-job
across separate invocations. On a persistent host the same builder/state dir
survives across jobs and reboots.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "config" / "paseo-candidate.json"
SMOKE_SCRIPT = ROOT / "scripts" / "smoke_paseo_image.py"
COMPOSE_SMOKE = ROOT / "scripts" / "verify-compose-foundation.sh"
INSTRUCTION_SMOKE = ROOT / "scripts" / "verify-pi-instruction-plane.sh"
CAPABILITY_SMOKE = ROOT / "scripts" / "verify-pi-global-capabilities.sh"

BUILDER_NAME_DEFAULT = "pi-unraid-paseo"
RUNTIME_SERVICE_NAME = "paseo"
STATE_DIR_DEFAULT = Path.home() / ".local/share" / "pi-unraid" / "buildx"
KEEP_STORAGE_DEFAULT = "8GB"
IMAGE_REPO_DEFAULT = "pi-unraid"
RECORD_SCHEMA_VERSION = 1

ENV_BUILDER = "PI_UNRAID_BUILDX_BUILDER"
ENV_STATE_DIR = "PI_UNRAID_BUILDX_STATE_DIR"
ENV_CACHE_DIR = "PI_UNRAID_BUILDX_CACHE_DIR"
ENV_KEEP_STORAGE = "PI_UNRAID_BUILDX_KEEP_STORAGE"

# Tokens that would mean the build re-resolves a floating channel.
FLOATING_CHANNEL_TOKENS = ("releases/latest", ":latest", "/latest/", "@latest")
# Legacy standalone-Pi lifecycle that must never be carried into this path.
LEGACY_TOKENS = (
    "node:24-bookworm-slim",
    "NODE_IMAGE",
    "/home/pi",
    "NOPASSWD",
    "pi-unraid-entrypoint",
    "pi-unraid-service",
    "groupmod --new-name pi",
    "usermod --login pi",
)
TAG_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*:[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$")
CANDIDATE_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FROM_RE = re.compile(r"^FROM\s+(.*)$", re.IGNORECASE)
RESERVED_BUILDER_NAMES = frozenset({"default"})
EXIT_VALIDATION = 2
EXIT_BUILD = 1


class BuildxError(RuntimeError):
    """Fail-closed build-path error."""


def _load_resolver():
    spec = importlib.util.spec_from_file_location(
        "paseo_candidate_resolver", ROOT / "scripts" / "resolve-paseo-candidate.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def validate_builder_name(builder: str) -> str:
    """Reject shared/reserved builder namespaces; return the validated name."""
    name = (builder or "").strip()
    if (
        not name
        or name == RUNTIME_SERVICE_NAME
        or "workstation" in name.lower()
        or name.lower() in RESERVED_BUILDER_NAMES
    ):
        raise BuildxError(f"builder name is not an isolated namespace: {builder!r}")
    return name


def effective_from_images(dockerfile_text: str) -> list[str]:
    """Return effective FROM image references, ignoring comments/directives.

    Only real Dockerfile instructions count: full-line comments (including
    parser directives such as ``# syntax=...``) and blank lines are skipped,
    line continuations are joined, and the match is case-insensitive with
    optional leading whitespace. ``--platform``-style flags and an optional
    ``AS <stage>`` suffix are stripped so only the image token is returned.
    """
    logical: list[str] = []
    pending = ""
    for raw in (dockerfile_text or "").splitlines():
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            pending += stripped[:-1] + " "
            continue
        pending += raw
        logical.append(pending)
        pending = ""
    if pending.strip():
        logical.append(pending)
    images: list[str] = []
    for line in logical:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        match = FROM_RE.match(text)
        if not match:
            continue
        image = None
        for token in match.group(1).split():
            if token.startswith("--"):
                continue
            image = token
            break
        if image:
            images.append(image)
    return images


def image_tag(candidate_id: str, repo: str = IMAGE_REPO_DEFAULT) -> str:
    """Derive the deterministic immutable image tag from a candidate id."""
    if not CANDIDATE_RE.fullmatch(candidate_id or ""):
        raise BuildxError("candidate_id is not an immutable sha256 identity")
    tag = f"{repo}:paseo-{candidate_id.removeprefix('sha256:')[:12]}"
    if not TAG_RE.fullmatch(tag):
        raise BuildxError(f"derived image tag is not docker-safe: {tag}")
    return tag


def verify_build_inputs(candidate: dict, dockerfile_text: str, context_dir: Path) -> dict:
    """Fail closed unless the context Dockerfile matches the frozen candidate.

    Returns a small readback dict for the record. Pure: performs no network
    or Docker calls; candidate schema/identity validation is delegated to the
    M05-T01 resolver (read-only ``validate``).
    """
    if not isinstance(candidate, dict):
        raise BuildxError("candidate must be an object")
    resolver = _load_resolver()
    try:
        resolver.validate(candidate)
    except resolver.ResolutionError as exc:
        raise BuildxError(f"candidate failed validation: {exc}") from exc

    if not context_dir.is_dir():
        raise BuildxError(f"build context is missing: {context_dir}")
    dockerfile = context_dir / "Dockerfile"
    if not dockerfile.is_file():
        raise BuildxError(f"build context has no Dockerfile: {context_dir}")

    candidate_id = candidate["candidate_id"]
    paseo = candidate["components"]["paseo"]
    reference = paseo["artifact"]["reference"]
    from_images = effective_from_images(dockerfile_text)
    if not from_images:
        raise BuildxError("Dockerfile has no effective FROM instruction")
    for image in from_images:
        if image != reference:
            raise BuildxError("Dockerfile FROM does not match the frozen Paseo reference")

    expected_env = {
        "PI_UNRAID_CANDIDATE_ID": candidate_id,
        "PI_UNRAID_PI_VERSION": candidate["components"]["pi"]["version"],
        "PI_UNRAID_SPECPI_VERSION": candidate["components"]["specpi"]["version"],
        "PI_UNRAID_PI_MCP_ADAPTER_VERSION": candidate["components"]["pi_mcp_adapter"]["version"],
        "PI_UNRAID_PLAYWRIGHT_VERSION": candidate["components"]["playwright"]["version"],
        "PI_UNRAID_GH_VERSION": candidate["components"]["github_cli"]["version"],
        "PI_UNRAID_DOCKER_CLI_VERSION": candidate["components"]["docker_cli"]["version"],
        "PI_UNRAID_DOCKER_COMPOSE_VERSION": candidate["components"]["docker_compose"]["version"],
    }
    for name, value in expected_env.items():
        if f'{name}="{value}"' not in dockerfile_text:
            raise BuildxError(f"Dockerfile {name} does not match the frozen candidate")

    for component in ("github_cli", "docker_compose"):
        digest = candidate["components"][component]["artifact"]["digest"].removeprefix("sha256:")
        if digest not in dockerfile_text:
            raise BuildxError(f"Dockerfile lacks the frozen {component} artifact digest")

    if f'io.pi-unraid.candidate-id="{candidate_id}"' not in dockerfile_text:
        raise BuildxError("Dockerfile lacks the frozen candidate-id label")

    lowered = dockerfile_text.lower()
    for token in FLOATING_CHANNEL_TOKENS:
        if token in lowered:
            raise BuildxError(f"Dockerfile carries a floating channel token: {token}")
    for token in LEGACY_TOKENS:
        if token in dockerfile_text:
            raise BuildxError(f"Dockerfile carries a legacy standalone-Pi token: {token}")

    return {
        "candidate_id": candidate_id,
        "paseo_reference": reference,
        "paseo_version": paseo["version"],
        "pi_version": candidate["components"]["pi"]["version"],
    }


def load_candidate(path: Path) -> dict:
    try:
        raw = path.read_text()
    except FileNotFoundError as exc:
        raise BuildxError(f"candidate file is missing: {path}") from exc
    except OSError as exc:
        raise BuildxError(f"candidate file is unreadable: {path}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuildxError(f"candidate file is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise BuildxError("candidate must be a JSON object")
    return data


def _run(argv: list[str], env: dict[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, text=True, capture_output=True, timeout=timeout, env=env)
    except OSError as exc:
        return subprocess.CompletedProcess(argv, 127, "", f"cannot execute {argv[0]}: {exc}")


def _tail(text: str, limit: int = 2000) -> str:
    text = text or ""
    return text[-limit:] if len(text) > limit else text


def count_cached_steps(progress_text: str) -> int:
    """Count BuildKit plain-progress cached steps (``#N CACHED`` lines)."""
    return len(re.findall(r"(?m)^#\d+ CACHED\b", progress_text or ""))


def print_build_output(proc) -> None:
    """Echo buildx output so the tee'd log keeps the BuildKit progress.

    Plain progress (including ``#N CACHED`` lines) is written to stderr;
    printing stdout alone would silently drop the cache evidence.
    """
    sys.stdout.write("--- buildx stdout (tail) ---\n")
    sys.stdout.write(_tail(proc.stdout or "(empty)\n", 4000))
    if not (proc.stdout or "").endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.write("--- buildx stderr (progress) ---\n")
    sys.stdout.write(proc.stderr or "(empty)\n")
    sys.stdout.flush()


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Recorder:
    def __init__(self) -> None:
        self.phases: dict[str, dict] = {}

    def record(self, name: str, status: str, duration_ms: int, detail: dict) -> None:
        self.phases[name] = {"status": status, "duration_ms": duration_ms, "detail": detail}

    def skip_rest(self, names: list[str], reason: str) -> None:
        for name in names:
            if name not in self.phases:
                self.record(name, "skipped", 0, {"reason": reason})


def ensure_builder(
    run_fn, builder: str, state_dir: Path, env: dict[str, str]
) -> dict:
    """Create-or-reuse the dedicated named builder; never mutates the default."""
    builder = validate_builder_name(builder)
    state_dir.mkdir(parents=True, exist_ok=True)
    probe = run_fn(["docker", "buildx", "inspect", builder], env, 60)
    if probe.returncode == 0:
        return {"name": builder, "driver": "docker-container", "reused": True}
    create = run_fn(
        ["docker", "buildx", "create", "--name", builder, "--driver", "docker-container"],
        env,
        120,
    )
    if create.returncode != 0:
        raise BuildxError(
            "builder creation failed "
            f"(rc={create.returncode}): {_tail(create.stderr or create.stdout)}"
        )
    return {"name": builder, "driver": "docker-container", "reused": False}


def read_image_identity(run_fn, tag: str, env: dict[str, str]) -> dict:
    proc = run_fn(["docker", "image", "inspect", tag], env, 60)
    if proc.returncode != 0:
        raise BuildxError(
            f"image inspect failed (rc={proc.returncode}): {_tail(proc.stderr or proc.stdout)}"
        )
    try:
        entry = json.loads(proc.stdout)[0]
    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        raise BuildxError("image inspect returned unreadable JSON") from exc
    labels = (entry.get("Config", {}) or {}).get("Labels") or {}
    return {
        "id": entry.get("Id"),
        "digests": entry.get("RepoDigests") or [],
        "candidate_label": labels.get("io.pi-unraid.candidate-id"),
    }


def check_keep_storage(keep_storage: str) -> str:
    bound = (keep_storage or "").strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?\s*(?:B|KB|MB|GB|TB)", bound, re.I):
        raise BuildxError(f"keep-storage bound is invalid: {keep_storage!r}")
    return bound


def run_prune(
    run_fn, builder: str, keep_storage: str, env: dict[str, str]
) -> dict:
    """Bounded post-success prune: size bound only, never before the build."""
    bound = check_keep_storage(keep_storage)
    proc = run_fn(
        ["docker", "buildx", "prune", "--builder", builder,
         "--keep-storage", bound, "--force"],
        env,
        300,
    )
    if proc.returncode != 0:
        raise BuildxError(
            f"bounded prune failed (rc={proc.returncode}): {_tail(proc.stderr or proc.stdout)}"
        )
    return {"builder": builder, "keep_storage": bound, "reclaimed": _tail(proc.stdout, 500)}


def read_metadata_digest(metadata_file: Path | None) -> str | None:
    if metadata_file is None or not metadata_file.is_file():
        return None
    try:
        data = json.loads(metadata_file.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    digest = data.get("containerimage.digest")
    return digest if isinstance(digest, str) and digest else None


def docker_env(state_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["DOCKER_CONFIG"] = str(state_dir)
    return env


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(data, sort_keys=True, indent=2) + "\n"
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(rendered)
    os.replace(tmp, path)


def load_build_record(path: Path) -> dict:
    try:
        raw = path.read_text()
    except FileNotFoundError as exc:
        raise BuildxError(f"build record is missing: {path}") from exc
    except OSError as exc:
        raise BuildxError(f"build record is unreadable: {path}") from exc
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuildxError(f"build record is not valid JSON: {path}") from exc
    if not isinstance(record, dict):
        raise BuildxError("build record must be a JSON object")
    if record.get("schema_version") != RECORD_SCHEMA_VERSION:
        raise BuildxError("build record uses an unsupported schema")
    if record.get("command") != "build":
        raise BuildxError("record is not a build record")
    if not isinstance(record.get("phases"), dict):
        raise BuildxError("build record has no phases")
    return record


def smoke_suite(tag: str, candidate_path: str) -> list[tuple[str, list[str]]]:
    """The complete disposable smoke suite for one built tag, in order."""
    return [
        ("image_provenance", [sys.executable, str(SMOKE_SCRIPT), tag, candidate_path]),
        ("persistence_ownership", ["bash", str(COMPOSE_SMOKE), tag]),
        ("instruction_plane", ["bash", str(INSTRUCTION_SMOKE), tag]),
        ("global_capabilities", ["bash", str(CAPABILITY_SMOKE), tag]),
    ]


def run_smoke_suite(tag: str, candidate_path: str, per_smoke_timeout: int) -> dict:
    """Run the complete suite fail-fast; returns the test-phase detail."""
    smokes: list[dict] = []
    for name, argv in smoke_suite(tag, candidate_path):
        print(f"--- smoke: {name} ---", flush=True)
        begin = time.monotonic()
        try:
            proc = _run(argv, dict(os.environ), per_smoke_timeout)
        except subprocess.TimeoutExpired as exc:
            raise BuildxError(f"smoke timed out: {name}") from exc
        duration_ms = int((time.monotonic() - begin) * 1000)
        if proc.returncode != 0:
            raise BuildxError(
                f"smoke failed: {name} (rc={proc.returncode}): "
                f"{_tail(proc.stderr or proc.stdout)}"
            )
        if proc.stdout:
            sys.stdout.write(_tail(proc.stdout, 2000))
            if not proc.stdout.endswith("\n"):
                sys.stdout.write("\n")
        smokes.append({"name": name, "status": "ok", "duration_ms": duration_ms})
    return {"smokes": smokes}


def cmd_build(args: argparse.Namespace) -> int:
    if args.with_prune and not args.with_smoke:
        print("build refused: --with-prune requires --with-smoke "
              "(cleanup only after successful build/smoke)", file=sys.stderr)
        return EXIT_VALIDATION
    recorder = Recorder()
    started = _utcnow()
    builder = args.builder or os.environ.get(ENV_BUILDER, BUILDER_NAME_DEFAULT)
    state_dir = Path(args.state_dir or os.environ.get(ENV_STATE_DIR, str(STATE_DIR_DEFAULT)))
    cache_dir = args.cache_dir or os.environ.get(ENV_CACHE_DIR)
    keep_storage = args.keep_storage or os.environ.get(ENV_KEEP_STORAGE, KEEP_STORAGE_DEFAULT)
    candidate_path = Path(args.candidate)
    context_dir = Path(args.context)
    record_path = Path(args.record)
    metadata_file = Path(args.metadata) if args.metadata else None

    candidate_id = ""
    tag = args.tag or ""
    image: dict = {"id": None, "digests": [], "candidate_label": None}
    builder_info: dict = {"name": builder, "driver": "docker-container", "reused": None}
    cache_info: dict = {"local_dir": str(cache_dir) if cache_dir else None}
    readback: dict = {}
    exit_code = 0

    def finish() -> int:
        record = {
            "schema_version": RECORD_SCHEMA_VERSION,
            "command": "build",
            "builder": {**builder_info, "state_dir": str(state_dir)},
            "candidate": {"path": str(candidate_path), "candidate_id": candidate_id},
            "context": str(context_dir),
            "tag": tag,
            "image": image,
            "cache": cache_info,
            "started_at": started,
            "finished_at": _utcnow(),
            "phases": recorder.phases,
        }
        atomic_write_json(record_path, record)
        print(json.dumps({"tag": tag, "record": str(record_path)}, sort_keys=True))
        return exit_code

    # Phase 1: resolution/readback (no Docker, no network).
    begin = time.monotonic()
    try:
        candidate = load_candidate(candidate_path)
        dockerfile_text = (context_dir / "Dockerfile").read_text()
        readback = verify_build_inputs(candidate, dockerfile_text, context_dir)
        candidate_id = readback["candidate_id"]
        if not tag:
            tag = image_tag(candidate_id)
        elif not TAG_RE.fullmatch(tag):
            raise BuildxError(f"override tag is not docker-safe: {tag}")
        if args.with_prune:
            check_keep_storage(keep_storage)
        recorder.record(
            "resolution_readback",
            "ok",
            int((time.monotonic() - begin) * 1000),
            {**readback, "candidate_path": str(candidate_path)},
        )
    except (BuildxError, OSError) as exc:
        recorder.record("resolution_readback", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["builder_ensure", "build", "test", "prune"], "prior phase failed")
        exit_code = EXIT_VALIDATION
        return finish()

    env = docker_env(state_dir)
    run_fn = lambda argv, env_arg, timeout: _run(argv, env_arg, timeout)  # noqa: E731

    # Phase 2: builder ensure.
    begin = time.monotonic()
    try:
        builder_info = ensure_builder(run_fn, builder, state_dir, env)
        builder = builder_info["name"]
        recorder.record("builder_ensure", "ok", int((time.monotonic() - begin) * 1000), builder_info)
    except (BuildxError, subprocess.TimeoutExpired) as exc:
        recorder.record("builder_ensure", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["build", "test", "prune"], "prior phase failed")
        exit_code = EXIT_BUILD
        return finish()

    # Phase 3: build.
    begin = time.monotonic()
    build_argv = [
        "docker", "buildx", "build", "--builder", builder, "--load",
        "--progress", args.progress, "-t", tag,
    ]
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        build_argv += [
            "--cache-from", f"type=local,src={cache_dir}",
            "--cache-to", f"type=local,mode=max,dest={cache_dir}",
        ]
    for label in args.build_label or []:
        if "=" not in label:
            recorder.record("build", "failed", int((time.monotonic() - begin) * 1000),
                            {"error": f"build label is not KEY=VALUE: {label}"})
            recorder.skip_rest(["test", "prune"], "prior phase failed")
            exit_code = EXIT_VALIDATION
            return finish()
        build_argv += ["--label", label]
    if metadata_file:
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        build_argv += ["--metadata-file", str(metadata_file)]
    build_argv.append(str(context_dir))
    try:
        proc = run_fn(build_argv, env, args.build_timeout)
        print_build_output(proc)
        if proc.returncode != 0:
            raise BuildxError(
                f"build failed (rc={proc.returncode}): {_tail(proc.stderr or proc.stdout)}"
            )
        image = read_image_identity(run_fn, tag, env)
        if not image.get("id"):
            raise BuildxError("built image has no immutable Id")
        if image.get("candidate_label") != candidate_id:
            raise BuildxError("built image candidate label does not match the frozen candidate")
        recorder.record("build", "ok", int((time.monotonic() - begin) * 1000), {
            "tag": tag,
            "image_id": image["id"],
            "image_digests": image["digests"],
            "metadata_digest": read_metadata_digest(metadata_file),
            "cached_steps": count_cached_steps(proc.stderr),
        })
    except (BuildxError, subprocess.TimeoutExpired) as exc:
        recorder.record("build", "failed", int((time.monotonic() - begin) * 1000),
                        {"error": str(exc)})
        recorder.skip_rest(["test", "prune"], "prior phase failed")
        exit_code = EXIT_BUILD
        return finish()

    # Phase 4: test (complete disposable smoke suite when requested).
    if args.with_smoke:
        begin = time.monotonic()
        try:
            detail = run_smoke_suite(tag, str(candidate_path), args.smoke_timeout)
            recorder.record("test", "ok", int((time.monotonic() - begin) * 1000), detail)
        except (BuildxError, subprocess.TimeoutExpired) as exc:
            recorder.record("test", "failed", int((time.monotonic() - begin) * 1000),
                            {"error": str(exc)})
            recorder.skip_rest(["prune"], "prior phase failed")
            exit_code = EXIT_BUILD
            return finish()
    else:
        recorder.record("test", "skipped", 0, {"reason": "--with-smoke was not requested"})

    # Phase 5: prune (bounded, only after successful work).
    if args.with_prune:
        begin = time.monotonic()
        try:
            detail = run_prune(run_fn, builder, keep_storage, env)
            recorder.record("prune", "ok", int((time.monotonic() - begin) * 1000), detail)
        except (BuildxError, subprocess.TimeoutExpired) as exc:
            recorder.record("prune", "failed", int((time.monotonic() - begin) * 1000),
                            {"error": str(exc)})
            exit_code = EXIT_BUILD
            return finish()
    else:
        recorder.record("prune", "skipped", 0, {"reason": "--with-prune was not requested"})

    return finish()


def _phase_status(record: dict, phase: str) -> str:
    phases = record.get("phases") or {}
    entry = phases.get(phase) or {}
    status = entry.get("status")
    return status if isinstance(status, str) else ""


def cmd_test(args: argparse.Namespace) -> int:
    record_path = Path(args.record)
    try:
        record = load_build_record(record_path)
    except BuildxError as exc:
        print(f"test refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    if _phase_status(record, "build") != "ok":
        print("test refused: record has no successful build phase", file=sys.stderr)
        return EXIT_VALIDATION
    tag = record.get("tag") or ""
    candidate_path = (record.get("candidate") or {}).get("path") or ""
    if not tag or not candidate_path:
        print("test refused: record lacks tag/candidate identity", file=sys.stderr)
        return EXIT_VALIDATION
    begin = time.monotonic()
    try:
        detail = run_smoke_suite(tag, candidate_path, args.smoke_timeout)
    except (BuildxError, subprocess.TimeoutExpired) as exc:
        record["phases"]["test"] = {
            "status": "failed",
            "duration_ms": int((time.monotonic() - begin) * 1000),
            "detail": {"error": str(exc)},
        }
        record["finished_at"] = _utcnow()
        atomic_write_json(record_path, record)
        print(f"test failed: {exc}", file=sys.stderr)
        return EXIT_BUILD
    record["phases"]["test"] = {
        "status": "ok",
        "duration_ms": int((time.monotonic() - begin) * 1000),
        "detail": detail,
    }
    record["finished_at"] = _utcnow()
    atomic_write_json(record_path, record)
    print(json.dumps({"tag": tag, "record": str(record_path), "test": "ok"}, sort_keys=True))
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    builder = args.builder or os.environ.get(ENV_BUILDER, BUILDER_NAME_DEFAULT)
    state_dir = Path(args.state_dir or os.environ.get(ENV_STATE_DIR, str(STATE_DIR_DEFAULT)))
    keep_storage = args.keep_storage or os.environ.get(ENV_KEEP_STORAGE, KEEP_STORAGE_DEFAULT)
    try:
        builder = validate_builder_name(builder)
    except BuildxError as exc:
        print(f"bounded prune refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    try:
        check_keep_storage(keep_storage)
    except BuildxError as exc:
        print(f"bounded prune refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    record_path = Path(args.record)
    try:
        record = load_build_record(record_path)
    except BuildxError as exc:
        print(f"bounded prune refused: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    if _phase_status(record, "build") != "ok" or _phase_status(record, "test") != "ok":
        print("bounded prune refused: record lacks a successful build and test; "
              "cleanup runs only after successful build/smoke", file=sys.stderr)
        return EXIT_VALIDATION
    if (record.get("builder") or {}).get("name") != builder:
        print(f"bounded prune refused: record builder "
              f"{(record.get('builder') or {}).get('name')!r} does not match {builder!r}",
              file=sys.stderr)
        return EXIT_VALIDATION
    begin = time.monotonic()
    try:
        detail = run_prune(
            lambda argv, env_arg, timeout: _run(argv, env_arg, timeout),
            builder,
            keep_storage,
            docker_env(state_dir),
        )
    except (BuildxError, subprocess.TimeoutExpired) as exc:
        record["phases"]["prune"] = {
            "status": "failed",
            "duration_ms": int((time.monotonic() - begin) * 1000),
            "detail": {"error": str(exc)},
        }
        record["finished_at"] = _utcnow()
        atomic_write_json(record_path, record)
        print(f"prune failed: {exc}", file=sys.stderr)
        return EXIT_BUILD
    record["phases"]["prune"] = {
        "status": "ok",
        "duration_ms": int((time.monotonic() - begin) * 1000),
        "detail": detail,
    }
    record["finished_at"] = _utcnow()
    atomic_write_json(record_path, record)
    summary = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "command": "prune",
        "duration_ms": int((time.monotonic() - begin) * 1000),
        **detail,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local credential-free Buildx/BuildKit path for the frozen Paseo child image."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="validate, build and record one frozen-candidate image")
    build.add_argument("--candidate", default=str(DEFAULT_CANDIDATE),
                       help="frozen accepted or explicitly staged candidate JSON")
    build.add_argument("--context", default=str(ROOT), help="build context directory")
    build.add_argument("--tag", default=None, help="override the derived immutable tag")
    build.add_argument("--record", default="paseo-buildx-record.json",
                       help="machine-readable identity/provenance/timings record to write")
    build.add_argument("--metadata", default=None, help="buildx --metadata-file path")
    build.add_argument("--builder", default=None, help="dedicated builder name")
    build.add_argument("--state-dir", default=None, help="persistent buildx state directory")
    build.add_argument("--cache-dir", default=None, help="optional portable type=local cache dir")
    build.add_argument("--keep-storage", default=None, help="bounded prune keep-storage")
    build.add_argument("--build-label", action="append", default=[],
                       help="extra --label KEY=VALUE for warm-probe rebuilds")
    build.add_argument("--progress", default="plain", choices=("plain", "auto", "tty"))
    build.add_argument("--build-timeout", type=int, default=3600)
    build.add_argument("--smoke-timeout", type=int, default=600)
    build.add_argument("--with-smoke", action="store_true",
                       help="run the complete disposable smoke suite as the test phase")
    build.add_argument("--with-prune", action="store_true",
                       help="run the bounded prune after successful build/smoke (requires --with-smoke)")

    test = sub.add_parser("test", help="run the complete smoke suite and record the test phase")
    test.add_argument("--record", required=True, help="build record to test and update")
    test.add_argument("--smoke-timeout", type=int, default=600,
                      help="per-smoke timeout in seconds")

    prune = sub.add_parser("prune", help="bounded post-success cache prune only")
    prune.add_argument("--record", required=True,
                       help="successfully tested build record gating this prune")
    prune.add_argument("--builder", default=None)
    prune.add_argument("--state-dir", default=None)
    prune.add_argument("--keep-storage", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "build":
        return cmd_build(args)
    if args.command == "test":
        return cmd_test(args)
    if args.command == "prune":
        return cmd_prune(args)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
