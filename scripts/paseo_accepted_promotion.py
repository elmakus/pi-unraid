#!/usr/bin/env python3
"""Serialized exact-digest promotion writer for Paseo update channels.

M07-T06 trusted path: production exposure requires the strict trusted
final-gate assembler record (real validator + state round-trip +
source/companion/policy/launcher/guard bindings), an armed guard whose
predecessor equals the actually running predecessor, and — for first
creation — verified HTTP 404 channel absence under the same writer
lock. Channel predecessor observation (registry alias state) stays
distinct from the running production predecessor (guard/ledger
identity). Auth/network/permission failures are never absence.
"""
from __future__ import annotations
import argparse, fcntl, hashlib, json, re, socket, subprocess, sys, tempfile
from pathlib import Path
from scripts.paseo_transaction_guard import GuardError, validate as validate_guard_readback

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SCHEMA_VERSION = 1
PRODUCTION_WRITER_HOST = "Tower"
PRODUCTION_LOCK_ROOT = Path("/mnt/user/appdata/pi-unraid/update-state")

# Exact full required set the shipped assembler emits: 20 producer checks
# + 6 source/isolation checks + 4 state checks. The writer requires every
# name present with PASS. Iterating only the keys a caller record happens
# to carry would let an omitted check disappear silently, so omission of
# any name below fails closed here.
FULL_REQUIRED_GATES = (
    "registry_digest", "image_mapping", "image_config",
    "frozen_chain", "companion_binding", "policy_binding",
    "daemon_binding", "pi_binding", "codex_catalog",
    "codex_auth", "codex_health", "muse_guard_readback",
    "muse_policy_readback", "muse_dispatch",
    "muse_effective_profile", "muse_owned_child",
    "muse_profile_preflight", "applied_payload_interval",
    "muse_effective_config", "muse_effective_readback",
    "immutable_source_configuration", "runtime", "uid_gid",
    "mount_isolation", "network_isolation", "secret_isolation",
    "state.baseline_clone_isolated",
    "state.candidate_state_mutation",
    "state.previous_runtime_reopen",
    "state.direct_skip_path",
)

class PromotionError(RuntimeError):
    pass

def require_digest(value: str, label: str = "digest") -> str:
    if not DIGEST.fullmatch(str(value or "")):
        raise PromotionError(f"{label} must be an immutable sha256 digest")
    return str(value)

def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromotionError(f"unreadable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PromotionError(f"JSON object required: {path}")
    return value

def run_checked(argv: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PromotionError(f"command failed to execute: {argv[0]}") from exc
    if proc.returncode != 0:
        raise PromotionError(f"command failed ({proc.returncode}): {' '.join(argv)}: {(proc.stderr or proc.stdout)[-1000:]}")
    return proc

def parse_registry_digest(output: str) -> str:
    for line in output.splitlines():
        fields = line.strip().split()
        if len(fields) == 2 and fields[0] == "Digest:" and DIGEST.fullmatch(fields[1]):
            return fields[1]
    raise PromotionError("registry readback did not expose one OCI digest")

def inspect_digest(ref: str) -> str:
    out = run_checked(["docker", "buildx", "imagetools", "inspect", ref]).stdout
    return parse_registry_digest(out)

def validate_rollback_identity(value: str) -> str:
    return require_digest(value, "rollback identity")


def classify_channel_status(status: int | None, *, error: str | None = None) -> str:
    """Classify a registry channel read as absent/present/auth/uncertain.

    Only an explicit HTTP 404 is verified absence. 401/403 are auth
    failures, timeouts/network errors are uncertain, and any other
    state (including 200/present) is not absence. Ambiguity never
    becomes absence and is never silently retried.
    """
    if error is not None:
        kind = str(error).strip().lower()
        if kind in ("timeout", "network", "connection", "dns", "tls"):
            raise PromotionError("channel absence uncertain: network/timeout is not verified 404")
        raise PromotionError("channel absence uncertain: transport failure is not verified 404")
    if status == 404:
        return "absent"
    if status in (401, 403):
        raise PromotionError("channel auth failure is not verified absence")
    if status == 200:
        return "present"
    raise PromotionError("channel absence uncertain: ambiguous registry state")


def verify_channel_absence(*, status: int | None = None, error: str | None = None) -> None:
    """Require verified HTTP 404 absence; auth/network/timeout always fail."""
    if classify_channel_status(status, error=error) != "absent":
        raise PromotionError("channel is present; first-create requires verified absence")


def validate_trusted_final_gate(candidate: str, repository: str,
                                final_gate: dict | None, guard: dict,
                                *, predecessor_mapping: dict | None = None) -> dict:
    """Strict M07-T06 production gate: every required terminal check plus bindings.

    Rejects generic GREEN/PASS, fixture-as-real, missing/forged gates,
    wrong-digest reports, stale baselines, absent effective max and
    wrong source/bundle/configuration before any registry access. The
    running predecessor resolves per typed kind (``oci`` → manifest
    digest, ``local``/``legacy`` → image ID); OCI vs local namespaces
    stay distinct, and OCI mappings must name this repository.

    Trust boundary (R01 RED): this function checks VALUE consistency of a
    gate-shaped dict only — content alone can never prove provenance, so a
    direct call with a fully populated forged dict confers NOTHING. Actual
    production eligibility is conferred solely by the production writer
    paths, which refuse caller-supplied gate records and run the shipped
    acquisition boundary in-process (see ``_acquire_production_gate``).
    """
    if not isinstance(final_gate, dict):
        raise PromotionError(
            "production accepted promotion requires trusted final-gate assembler "
            "evidence (generic GREEN is not evidence)")
    if final_gate.get("schema_version") != 2:
        raise PromotionError("final-gate record uses an unsupported schema")
    if final_gate.get("status") != "GREEN":
        raise PromotionError("production accepted promotion requires exact GREEN final-gate evidence")
    if final_gate.get("execution_class") != "real":
        raise PromotionError("fixture/rehearsal never satisfies the final real gate")
    if final_gate.get("real_validation_satisfied") is not True:
        raise PromotionError("real validation is not satisfied")
    if final_gate.get("candidate_digest") != candidate:
        raise PromotionError("final-gate candidate digest mismatch")
    local = str(final_gate.get("candidate_local_image_id") or "")
    require_digest(local, "final-gate local image identity")
    if local == candidate:
        raise PromotionError("OCI manifest and local image identities must remain distinct")
    required = final_gate.get("required_gates")
    if not isinstance(required, dict):
        raise PromotionError("final-gate required checks are missing")
    for name, outcome in required.items():
        if outcome != "PASS":
            raise PromotionError(f"final gate requires {name} PASS")
    # Explicit full set: the 20 producer checks, the six source/isolation
    # checks AND the four state checks. A record that omits any of them —
    # even with every carried check PASS — fails closed here.
    for name in FULL_REQUIRED_GATES:
        if required.get(name) != "PASS":
            raise PromotionError(f"final gate requires {name} PASS")
    for key in ("source_head", "companion_digest", "policy_digest",
                "launcher_digest", "baseline_oci", "baseline_local_image_id"):
        value = final_gate.get(key)
        if key == "source_head":
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
                raise PromotionError("final-gate source/bundle binding is missing")
        else:
            require_digest(str(value or ""), f"final-gate {key}")
    if final_gate.get("baseline_local_image_id") == candidate:
        raise PromotionError("stale baseline: previous local equals candidate")
    if final_gate.get("baseline_oci") == candidate:
        raise PromotionError("stale baseline: previous OCI equals candidate")
    # Typed predecessor: kind determines which namespace the guard's
    # running identity lives in; divergent OCI vs local values pass.
    typed = final_gate.get("predecessor")
    if not isinstance(typed, dict) or typed.get("kind") not in ("oci", "local", "legacy"):
        raise PromotionError("final-gate predecessor mapping is missing")
    if typed["kind"] == "oci":
        running = require_digest(str(typed.get("digest") or ""), "predecessor OCI digest")
        if str(typed.get("repository") or "").strip().lower() != repository.strip().lower():
            raise PromotionError("predecessor repository mismatch")
    else:
        running = require_digest(str(typed.get("image_id") or ""), "predecessor image identity")
        if typed["kind"] == "legacy":
            for key in ("archive_sha256", "config_digest"):
                require_digest(str(typed.get(key) or ""), f"predecessor {key}")
            if not typed.get("archive_path") or not typed.get("state_identity"):
                raise PromotionError("predecessor legacy anchor/state is missing")
    if final_gate.get("baseline_oci") != running:
        raise PromotionError("stale baseline: final-gate baseline mismatch vs running predecessor")
    if predecessor_mapping is not None:
        if not isinstance(predecessor_mapping, dict):
            raise PromotionError("predecessor mapping must be an object")
        kind = predecessor_mapping.get("kind")
        if kind != typed["kind"]:
            raise PromotionError("predecessor mapping kind mismatch vs final gate")
        if kind == "oci":
            if require_digest(str(predecessor_mapping.get("digest") or ""), "mapping OCI digest") != running:
                raise PromotionError("predecessor mapping mismatch vs running predecessor")
            if str(predecessor_mapping.get("repository") or "").strip().lower() != repository.strip().lower():
                raise PromotionError("predecessor repository mismatch")
        else:
            if require_digest(str(predecessor_mapping.get("image_id") or ""), "mapping image identity") != running:
                raise PromotionError("predecessor mapping mismatch vs running predecessor")
    if final_gate.get("guard_binding_digest") != guard.get("binding_digest"):
        raise PromotionError("final-gate/guard binding mismatch")
    return final_gate

def validate_production_gate(candidate: str, repository: str, final_gate: dict | None, guard: dict | None, *, predecessor_mapping: dict | None = None) -> str:
    try:
        guard = validate_guard_readback(guard)
    except (GuardError, OSError, TypeError, ValueError) as exc:
        raise PromotionError("production accepted promotion requires validated transaction guard readback") from exc
    # Strict trusted path first: generic GREEN without the assembler
    # bindings never authorizes a production write. The running
    # predecessor resolves per typed kind inside the trusted gate.
    trusted = validate_trusted_final_gate(candidate, repository, final_gate, guard,
                                          predecessor_mapping=predecessor_mapping)
    typed = trusted["predecessor"]
    running = trusted["baseline_oci"]
    if not guard or guard.get("state") != "armed" or guard.get("candidate_digest") != candidate:
        raise PromotionError("production accepted promotion requires matching armed transaction guard readback")
    for key in ("previous_digest", "rollback_digest"):
        require_digest(str(guard.get(key) or ""), f"guard {key}")
    if guard.get("previous_digest") != running or guard.get("rollback_digest") != running:
        raise PromotionError("armed guard predecessor/rollback identity mismatch vs running predecessor")
    config_digest = str(guard.get("config_digest") or "")
    require_digest(config_digest, "guard config_digest")
    return running

def promotion_lock_path(repository: str, alias: str, *, production: bool = False) -> Path:
    key = hashlib.sha256(f"{repository}:{alias}".encode("utf-8")).hexdigest()
    root = PRODUCTION_LOCK_ROOT if production else Path(tempfile.gettempdir())
    return root / f"paseo-accepted-promotion-{key}.lock"

def validate_writer_domain(*, production: bool, lock_path: Path | None) -> Path:
    if not production:
        return lock_path if lock_path is not None else Path()
    if socket.gethostname() != PRODUCTION_WRITER_HOST:
        raise PromotionError("production accepted promotion is restricted to the Tower writer domain")
    expected_root = PRODUCTION_LOCK_ROOT.resolve()
    selected = (lock_path or promotion_lock_path("", "accepted", production=True)).resolve()
    try:
        selected.relative_to(expected_root)
    except ValueError as exc:
        raise PromotionError("production promotion lock must remain inside the Tower writer domain") from exc
    return selected

def _check_predecessor_mapping(running: str, mapping: dict | None) -> None:
    """Bind the typed predecessor mapping to the running value.

    OCI mappings carry the registry digest; local/legacy mappings carry
    the platform image-ID value. The kind distinguishes the namespaces
    even though both use sha256 syntax; a mapping whose value differs
    from the running predecessor, or that carries multiple/ambiguous
    identities, fails closed.
    """
    if mapping is None:
        return
    if not isinstance(mapping, dict):
        raise PromotionError("predecessor mapping must be an object")
    kind = mapping.get("kind")
    if kind not in ("oci", "local", "legacy"):
        raise PromotionError("unsupported predecessor kind")
    if kind == "oci":
        value = require_digest(str(mapping.get("digest") or ""), "OCI predecessor digest")
        if value != running:
            raise PromotionError("predecessor mapping mismatch vs running predecessor")
    else:
        value = require_digest(str(mapping.get("image_id") or ""), "local predecessor image-ID")
        if value != running:
            raise PromotionError("predecessor mapping mismatch vs running predecessor")
        if kind == "legacy":
            for key in ("archive_sha256", "config_digest"):
                require_digest(str(mapping.get(key) or ""), f"legacy {key}")
            if not mapping.get("archive_path") or not mapping.get("state_identity"):
                raise PromotionError("legacy predecessor anchor/state is missing")

def _running_from_mapping(repository: str, mapping: dict | None) -> str:
    """Resolve the running value from a REQUIRED typed mapping."""
    if not isinstance(mapping, dict):
        raise PromotionError("typed predecessor mapping is required")
    kind = mapping.get("kind")
    if kind == "oci":
        value = require_digest(str(mapping.get("digest") or ""), "OCI predecessor digest")
        if str(mapping.get("repository") or "").strip().lower() != repository.strip().lower():
            raise PromotionError("predecessor repository mismatch")
        return value
    if kind in ("local", "legacy"):
        return require_digest(str(mapping.get("image_id") or ""), "local predecessor image-ID")
    raise PromotionError("unsupported predecessor kind")

# Production eligibility is conferred ONLY by in-process acquisition: the
# writer invokes the shipped assembler acquisition boundary itself (shipped
# validator + state-prove + guard readback, recomputed source bindings).
# Caller-supplied gate dicts/JSON — however fully populated, internally
# consistent or genuinely valued — are detached records. Detached records
# may exercise disposable diagnostics but can never authorize a production
# write. No label, hash, flag or binding on a detached record changes that:
# the production paths below never read such markers, they refuse the
# record categorically and acquire the gate themselves.
DETACHED_GATE_ERROR = (
    "detached gate records are diagnostic-only and cannot confer production "
    "promotion eligibility; production promotion requires in-process trusted "
    "acquisition via the acquisition bundle")

# Locator-only bundle for in-process acquisition. Values are file paths and
# transport locators owned by the caller layers (plus the ledger-owned typed
# predecessor observation); the producer/validator/state objects themselves
# are NEVER caller-supplied — the writer imports the shipped acquisition
# owner itself (see _acquire_production_gate).
_ACQUISITION_KEYS = (
    "candidate_file", "handoff_file", "build_input_file",
    "tested_image_file", "build_record", "publication_file",
    "source_root", "codex_secret", "codex_base_url", "codex_model",
    "muse_secret", "validator_state_root", "validator_output",
    "baseline_path", "baseline_local_image_id", "state_root",
    "state_output", "predecessor", "guard_path",
)

def _acquire_production_gate(repository: str, candidate: str,
                             acquisition: dict | None) -> tuple[dict, dict]:
    """Run trusted acquisition in-process; return (gate, live guard).

    The shipped ``paseo_final_gate.assemble_from_acquisition`` boundary is
    invoked HERE, inside the writer, on caller locator data only. A forged
    or replayed gate dict presented by any caller path is refused by the
    callers of this helper before it is reached; this helper never accepts
    a gate/validator/state record from the caller at all.
    """
    from scripts import paseo_final_gate as _final_gate  # noqa: E402  shipped acquisition owner
    if not isinstance(acquisition, dict):
        raise PromotionError(
            "production promotion requires an acquisition bundle of "
            "file/secret locators (caller gate records are diagnostic-only)")
    missing = [key for key in _ACQUISITION_KEYS if acquisition.get(key) in (None, "")]
    if missing:
        raise PromotionError(f"acquisition bundle is missing: {', '.join(missing)}")
    if not isinstance(acquisition.get("predecessor"), dict):
        raise PromotionError("acquisition bundle predecessor mapping must be an object")
    try:
        gate, ctx = _final_gate.assemble_from_acquisition(
            repository=repository, candidate_digest=candidate,
            candidate_file=acquisition["candidate_file"],
            handoff_file=acquisition["handoff_file"],
            build_input_file=acquisition["build_input_file"],
            tested_image_file=acquisition["tested_image_file"],
            build_record=acquisition["build_record"],
            publication_file=acquisition["publication_file"],
            source_root=acquisition["source_root"],
            companion_bundle=acquisition.get("companion_bundle"),
            codex_secret=acquisition["codex_secret"],
            codex_base_url=acquisition["codex_base_url"],
            codex_model=acquisition["codex_model"],
            muse_secret=acquisition["muse_secret"],
            validator_state_root=acquisition["validator_state_root"],
            validator_output=acquisition["validator_output"],
            baseline_path=acquisition["baseline_path"],
            baseline_local_image_id=acquisition["baseline_local_image_id"],
            state_root=acquisition["state_root"],
            state_output=acquisition["state_output"],
            predecessor=acquisition["predecessor"],
            guard_path=acquisition["guard_path"])
    except _final_gate.FinalGateError as exc:
        raise PromotionError(f"production trusted acquisition failed: {exc}") from exc
    live_guard = ctx.get("guard_record")
    if not isinstance(live_guard, dict):
        raise PromotionError("production trusted acquisition did not bind a live guard")
    return gate, live_guard

def promote(*, repository: str, alias: str, candidate_digest: str,
            expected_current_digest: str, output_path: Path,
            final_gate: dict | None = None, guard: dict | None = None,
            lock_path: Path | None = None,
            running_predecessor: str | None = None,
            predecessor_mapping: dict | None = None,
            acquisition: dict | None = None) -> dict:
    candidate = require_digest(candidate_digest, "candidate digest")
    expected = require_digest(expected_current_digest, "expected current digest")
    production = alias == "accepted"
    if production:
        # Guard classification first (forged/stale guard fails before any
        # registry access with the guard-readback error), then Tower
        # domain (out-of-domain fails with the domain error), then the
        # strict trusted gates. This preserves both negative
        # classifications while keeping all failures before mutation.
        # The running predecessor resolves per typed kind from the
        # trusted gate; an explicit mapping is cross-checked when given.
        try:
            validate_guard_readback(guard)
        except (GuardError, OSError, TypeError, ValueError) as exc:
            raise PromotionError("production accepted promotion requires validated transaction guard readback") from exc
        domain_lock = validate_writer_domain(production=True, lock_path=lock_path)
        if predecessor_mapping is not None:
            _check_predecessor_mapping(
                _running_from_mapping(repository, predecessor_mapping), predecessor_mapping)
        # Detached-caller bypass close: a caller-supplied gate — genuine,
        # replayed or forged — is refused BEFORE any acquisition or registry
        # access. The eligible gate is acquired in-process below.
        if final_gate is not None:
            raise PromotionError(DETACHED_GATE_ERROR)
        gate, live_guard = _acquire_production_gate(repository, candidate, acquisition)
        running = validate_production_gate(candidate, repository, gate, live_guard,
                                           predecessor_mapping=predecessor_mapping)
    elif alias == "accepted" or alias.endswith("/accepted"):
        raise PromotionError("reserved production accepted alias")
    else:
        running = require_digest(running_predecessor or expected_current_digest,
                                 "running predecessor digest")
        _check_predecessor_mapping(running, predecessor_mapping)
        domain_lock = validate_writer_domain(production=False, lock_path=lock_path)
    ref = f"{repository}:{alias}"
    immutable = f"{repository}@{candidate}"
    lock_file = domain_lock if production else (lock_path or promotion_lock_path(repository, alias))
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        first = inspect_digest(ref)
        if first != expected:
            raise PromotionError("stale/superseded promotion attempt: current alias digest changed")
        second = inspect_digest(ref)
        if second != expected:
            raise PromotionError("promotion race detected before write")
        run_checked(["docker", "buildx", "imagetools", "create", "--prefer-index=false", "-t", ref, immutable])
        readback = inspect_digest(ref)
        if readback != candidate:
            raise PromotionError("registry digest mismatch after promotion")
    result = {"schema_version": SCHEMA_VERSION, "status": "promoted", "alias": alias,
              "production": production, "previous_digest": expected,
              "running_predecessor": running,
              "candidate_digest": candidate, "readback_digest": readback,
              "rollback_digest": validate_rollback_identity(expected if production else running)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def promote_first_channel(*, repository: str, alias: str, candidate_digest: str,
                          output_path: Path,
                          final_gate: dict | None = None, guard: dict | None = None,
                          lock_path: Path | None = None,
                          predecessor_mapping: dict | None = None,
                          acquisition: dict | None = None,
                          channel_status: int | None = None,
                          channel_error: str | None = None,
                          channel_status_fn=None) -> dict:
    """Create a channel only after verified HTTP 404 absence under one lock.

    ``channel_status``/``channel_error`` carry the fake-able registry
    read (404 = absent; 401/403/network/timeout = never absence).
    ``channel_status_fn`` optionally supplies a fresh read inside the lock
    for race detection: when it reports present/uncertain before the
    write, creation fails closed. Both create and update paths enforce
    the trusted final gates plus the armed guard before the write and
    read back the OCI digest afterward.
    """
    candidate = require_digest(candidate_digest, "candidate digest")
    # First creation always carries the typed running predecessor; the
    # writer cross-checks it against the trusted gate's typed binding.
    running = _running_from_mapping(repository, predecessor_mapping)
    _check_predecessor_mapping(running, predecessor_mapping)
    production = alias == "accepted"
    if not production and (alias == "accepted" or alias.endswith("/accepted")):
        raise PromotionError("reserved production accepted alias")
    domain_lock = validate_writer_domain(production=production, lock_path=lock_path)
    # Both create and update enforce the trusted final gates plus the
    # exact armed guard before the write, even for disposable aliases.
    # Guard classification first so forged guards fail with the guard
    # error before gate classification; all failures precede mutation.
    try:
        validate_guard_readback(guard)
    except (GuardError, OSError, TypeError, ValueError) as exc:
        raise PromotionError("production accepted promotion requires validated transaction guard readback") from exc
    # Detached-caller bypass close (production only): disposable aliases
    # keep validating caller records by value for diagnostics, but the
    # accepted channel is only ever written from an in-process acquisition.
    if production and final_gate is not None:
        raise PromotionError(DETACHED_GATE_ERROR)
    if production:
        final_gate, guard = _acquire_production_gate(repository, candidate, acquisition)
    gate_running = validate_production_gate(candidate, repository, final_gate, guard,
                                            predecessor_mapping=predecessor_mapping)
    if gate_running != running:
        raise PromotionError("predecessor mapping mismatch vs trusted running predecessor")
    ref = f"{repository}:{alias}"
    immutable = f"{repository}@{candidate}"
    lock_file = domain_lock if production else (lock_path or promotion_lock_path(repository, alias))
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        # Verified absence under the same lock; auth/network ambiguity
        # can never be interpreted as absence or silently retried.
        verify_channel_absence(status=channel_status, error=channel_error)
        if channel_status_fn is not None:
            try:
                race = channel_status_fn()
            except PromotionError:
                raise
            except Exception as exc:
                raise PromotionError("channel absence uncertain: transport failure is not verified 404") from exc
            if isinstance(race, dict):
                verify_channel_absence(status=race.get("status"),
                                       error=race.get("error"))
            elif race != 404:
                verify_channel_absence(status=race)
        # Any appearance before the write invalidates the attempt.
        try:
            appeared = inspect_digest(ref)
        except PromotionError as exc:
            message = str(exc).lower()
            if "404" in message or "not found" in message or "no such" in message:
                appeared = None
            else:
                raise PromotionError("channel absence uncertain: transport failure is not verified 404") from exc
        if appeared is not None:
            raise PromotionError("first-create race: channel appeared before write")
        run_checked(["docker", "buildx", "imagetools", "create", "--prefer-index=false", "-t", ref, immutable])
        readback = inspect_digest(ref)
        if readback != candidate:
            raise PromotionError("registry digest mismatch after promotion")
    result = {"schema_version": SCHEMA_VERSION, "status": "promoted", "alias": alias,
              "production": production, "first_create": True,
              "previous_digest": running,
              "running_predecessor": running,
              "candidate_digest": candidate, "readback_digest": readback,
              "rollback_digest": validate_rollback_identity(running)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest="command",required=True)
    q=s.add_parser("promote"); q.add_argument("--repository",required=True); q.add_argument("--alias",required=True)
    q.add_argument("--candidate-digest",required=True); q.add_argument("--expected-current-digest",required=True)
    q.add_argument("--output",type=Path,required=True); q.add_argument("--final-gate",type=Path); q.add_argument("--guard",type=Path); q.add_argument("--acquisition",type=Path)
    a=p.parse_args()
    try:
        cli_production = a.alias == "accepted"
        if cli_production and a.final_gate:
            raise PromotionError(DETACHED_GATE_ERROR + " (CLI --final-gate files are diagnostic-only)")
        acquisition = load_json(a.acquisition) if a.acquisition else None
        if cli_production and acquisition is None:
            raise PromotionError("production promotion requires an --acquisition bundle of file/secret locators")
        result=promote(repository=a.repository,alias=a.alias,candidate_digest=a.candidate_digest,
            expected_current_digest=a.expected_current_digest,output_path=a.output,
            final_gate=load_json(a.final_gate) if (a.final_gate and not cli_production) else None,
            guard=load_json(a.guard) if a.guard else None,
            acquisition=acquisition)
        print(json.dumps(result,sort_keys=True)); return 0
    except (PromotionError,GuardError,OSError,TypeError,ValueError) as exc:
        print(f"promotion failed: {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())