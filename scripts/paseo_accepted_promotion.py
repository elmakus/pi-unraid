#!/usr/bin/env python3
"""Serialized exact-digest promotion writer for Paseo update channels."""
from __future__ import annotations
import argparse, fcntl, hashlib, json, re, socket, subprocess, sys, tempfile
from pathlib import Path
from scripts.paseo_transaction_guard import GuardError, validate as validate_guard_readback

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SCHEMA_VERSION = 1
PRODUCTION_WRITER_HOST = "Tower"
PRODUCTION_LOCK_ROOT = Path("/mnt/user/appdata/pi-unraid/update-state")

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

def validate_production_gate(candidate: str, expected: str, final_gate: dict | None, guard: dict | None) -> None:
    try:
        guard = validate_guard_readback(guard)
    except (GuardError, OSError, TypeError, ValueError) as exc:
        raise PromotionError("production accepted promotion requires validated transaction guard readback") from exc
    if not final_gate or final_gate.get("status") != "GREEN":
        raise PromotionError("production accepted promotion requires exact GREEN final-gate evidence")
    if final_gate.get("candidate_digest") != candidate:
        raise PromotionError("final-gate candidate digest mismatch")
    if not guard or guard.get("state") != "armed" or guard.get("candidate_digest") != candidate:
        raise PromotionError("production accepted promotion requires matching armed transaction guard readback")
    for key in ("previous_digest", "rollback_digest"):
        require_digest(str(guard.get(key) or ""), f"guard {key}")
    if guard.get("previous_digest") != expected or guard.get("rollback_digest") != expected:
        raise PromotionError("armed guard predecessor/rollback identity mismatch")
    config_digest = str(guard.get("config_digest") or "")
    require_digest(config_digest, "guard config_digest")
    if final_gate.get("guard_binding_digest") != guard.get("binding_digest"):
        raise PromotionError("final-gate/guard binding mismatch")

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

def promote(*, repository: str, alias: str, candidate_digest: str,
            expected_current_digest: str, output_path: Path,
            final_gate: dict | None = None, guard: dict | None = None,
            lock_path: Path | None = None) -> dict:
    candidate = require_digest(candidate_digest, "candidate digest")
    expected = require_digest(expected_current_digest, "expected current digest")
    production = alias == "accepted"
    if production:
        validate_production_gate(candidate, expected, final_gate, guard)
    elif alias == "accepted" or alias.endswith("/accepted"):
        raise PromotionError("reserved production accepted alias")
    ref = f"{repository}:{alias}"
    immutable = f"{repository}@{candidate}"
    domain_lock = validate_writer_domain(production=production, lock_path=lock_path)
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
              "candidate_digest": candidate, "readback_digest": readback,
              "rollback_digest": validate_rollback_identity(expected)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest="command",required=True)
    q=s.add_parser("promote"); q.add_argument("--repository",required=True); q.add_argument("--alias",required=True)
    q.add_argument("--candidate-digest",required=True); q.add_argument("--expected-current-digest",required=True)
    q.add_argument("--output",type=Path,required=True); q.add_argument("--final-gate",type=Path); q.add_argument("--guard",type=Path)
    a=p.parse_args()
    try:
        result=promote(repository=a.repository,alias=a.alias,candidate_digest=a.candidate_digest,
            expected_current_digest=a.expected_current_digest,output_path=a.output,
            final_gate=load_json(a.final_gate) if a.final_gate else None,
            guard=load_json(a.guard) if a.guard else None)
        print(json.dumps(result,sort_keys=True)); return 0
    except (PromotionError,GuardError,OSError,TypeError,ValueError) as exc:
        print(f"promotion failed: {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())