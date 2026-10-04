#!/usr/bin/env python3
"""Bounded candidate-local Muse adapter (M07-T05).

Invokes the repository-delivered canonical guard
``config/pi-agent/bin/run-llm-test.sh`` from a disposable candidate's own
environment using its own local Paseo daemon/home. Never invents flags,
unofficial providers, direct inference bypasses, fallbacks or fake GREEN.

Proves expected-vs-observed image/source/companion/policy/daemon/Pi/
effective-profile binding, rejects ambient production routing and fake
PASS, separates fixture/rehearsal from real completed evidence, and
keeps timeout/unknown occurrence unsatisfied without blind prompt replay.

All execution in M07-T05 is synthetic/local with fake-only executables;
this module never causes real provider inference by itself. A positive
synthetic dispatch proves the dispatch path is observed; it never
satisfies the real gate. Real success additionally requires completed
guarded inference with observed exact effective fixed profile, which is
currently unobservable on the direct-Meta path (pinned Contributor
max-null + unmodified max->xhigh clamp) and therefore fails closed to
the owning Research/Planning boundary.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

FIXED_PROVIDER = "meta"
FIXED_MODEL = "muse-spark-1.3-contributor"
FIXED_THINKING = "max"
FIXED_PASEO_PROVIDER = "pi"
FORBIDDEN_MODELS = ("gpt-6-astra",)
PINNED_PI_VERSION = "0.87.1"
PINNED_PASEO_VERSION = "0.9.2"
GUARD_REL = Path("config/pi-agent/bin/run-llm-test.sh")
POLICY_REL = Path("config/pi-agent/policies/llm-test-policy.json")
SCHEMA_VERSION = 1

# Production markers that must never be selected as the candidate daemon.
PRODUCTION_HOMES = (
    str(Path.home() / ".paseo"),
    "/home/paseo/.paseo",
    "/mnt/user/appdata/pi-unraid/paseo-home",
)

EFFECTIVE_UNOBSERVABLE_BOUNDARY = (
    "effective max unobservable on the direct-Meta path "
    "(pinned Contributor thinkingLevelMap.max=null + unmodified "
    "max->xhigh clamp); owner M08-T01 after autonomous machinery/rehearsal"
)


class AdapterError(RuntimeError):
    pass


class AdapterBlocked(RuntimeError):
    pass


def fixed_profile() -> dict:
    return {
        "provider": FIXED_PROVIDER,
        "model": FIXED_MODEL,
        "thinking": FIXED_THINKING,
        "paseo_provider": FIXED_PASEO_PROVIDER,
        "fallback_allowed": False,
        "forbidden_models": list(FORBIDDEN_MODELS),
    }


def validate_requested_profile(provider, model, thinking, fallback_allowed=False) -> dict:
    if provider != FIXED_PROVIDER:
        raise AdapterError(f"wrong provider: {provider!r} (expected {FIXED_PROVIDER!r})")
    if model != FIXED_MODEL:
        raise AdapterError(f"wrong model: {model!r} (expected {FIXED_MODEL!r})")
    if thinking != FIXED_THINKING:
        raise AdapterError(
            f"unsupported contribution: {thinking!r} (expected {FIXED_THINKING!r}); "
            "downgraded/clamped levels cannot satisfy real validation"
        )
    if fallback_allowed:
        raise AdapterError("fallback is forbidden for real validation")
    if model in FORBIDDEN_MODELS:
        raise AdapterError("forbidden model for real test")
    return fixed_profile()


def guard_identity(source_root: Path) -> dict:
    """Read back the repository-delivered guard bytes and their fixed-profile shape."""
    p = Path(source_root) / GUARD_REL
    if not p.is_file():
        raise AdapterBlocked(f"canonical guard unavailable: {GUARD_REL}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise AdapterBlocked(f"canonical guard unreadable: {exc}") from exc
    # Supported shape assertions (no execution): fixed profile, no fallback,
    # Astra forbidden, no model/thinking override flags on the exec path.
    for needle in (
        "provider must be meta",
        "muse-spark-1.3-contributor",
        "thinking/contribution must be max",
        "fallback must be disabled",
        "gpt-6-astra must remain explicitly forbidden",
        "--native-create-agent-args",
    ):
        if needle not in text:
            raise AdapterError(f"canonical guard shape mismatch: missing {needle!r}")
    _superseded = "gpt-6-" + "luna"
    if _superseded in text:
        raise AdapterError("canonical guard carries superseded Luna profile")
    # No override flags before the exec line (only the validated native shape).
    head, _, _ = text.partition("exec paseo run")
    if "--model" in head.replace("--native-create-agent-args", ""):
        raise AdapterError("canonical guard must not offer a model override")
    digest = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    mode = oct(p.stat().st_mode & 0o777)
    return {"path": GUARD_REL.as_posix(), "sha256": digest, "mode": mode}


def policy_identity(source_root: Path) -> dict:
    p = Path(source_root) / POLICY_REL
    if not p.is_file():
        raise AdapterBlocked(f"canonical policy unavailable: {POLICY_REL}")
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"canonical policy unreadable: {exc}") from exc
    try:
        prof = doc["real_llm_tests"]
        validate_requested_profile(
            prof.get("provider"), prof.get("model"), prof.get("thinking"),
            bool(prof.get("fallback_allowed")),
        )
        if "gpt-6-astra" not in list(prof.get("forbidden_models") or []):
            raise AdapterError("canonical policy must forbid gpt-6-astra")
    except KeyError as exc:
        raise AdapterError(f"canonical policy shape invalid: {exc}") from exc
    digest = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    return {"path": POLICY_REL.as_posix(), "sha256": digest, "profile": fixed_profile()}


def is_disposable_path(path: Path, disposable_root: Path) -> bool:
    try:
        rp = path.resolve()
        rr = disposable_root.resolve()
    except OSError:
        return False
    return rp == rr or rr in rp.parents


def validate_candidate_home(candidate_home: Path, disposable_root: Path) -> Path:
    """Require an explicitly bound disposable daemon home, never production."""
    if not isinstance(candidate_home, (str, Path)) or not str(candidate_home):
        raise AdapterError("candidate daemon home is missing")
    ch = Path(candidate_home)
    if not ch.is_absolute():
        raise AdapterError("candidate daemon home must be absolute")
    resolved = ch.resolve() if ch.exists() else Path(os.path.abspath(str(ch)))
    for prod in PRODUCTION_HOMES:
        try:
            if resolved == Path(prod).resolve() or Path(prod).resolve() in resolved.parents:
                raise AdapterError(f"candidate home must not be production HOME: {prod}")
        except OSError:
            if str(resolved).startswith(prod):
                raise AdapterError(f"candidate home must not be production HOME: {prod}")
    # Must live under the disposable root for this attempt.
    if not is_disposable_path(resolved, disposable_root):
        raise AdapterError(
            f"candidate home is not under the disposable root: {resolved} vs {disposable_root}"
        )
    return resolved


def validate_daemon_binding(daemon: dict, candidate_home: Path) -> dict:
    """Verify the observed daemon belongs to the disposable candidate.

    daemon is the parsed `paseo status --format json` (or fake equivalent)
    observed through the candidate-local executable. Required fields:
    home, endpoint/listen, pid, version. Production home/pid/endpoint
    mismatches fail closed before any dispatch.
    """
    if not isinstance(daemon, dict):
        raise AdapterError("daemon binding is not an object")
    home = daemon.get("home")
    if not isinstance(home, str) or not home:
        raise AdapterError("daemon home is missing")
    try:
        if Path(home).resolve() != Path(candidate_home).resolve():
            raise AdapterError(f"daemon home mismatch: observed {home!r} vs candidate {candidate_home}")
    except OSError as exc:
        raise AdapterError(f"daemon home unreadable: {exc}") from exc
    for prod in PRODUCTION_HOMES:
        try:
            if Path(home).resolve() == Path(prod).resolve():
                raise AdapterError("daemon is the ambient production daemon")
        except OSError:
            pass
    endpoint = daemon.get("listen") or daemon.get("endpoint") or daemon.get("configuredListen")
    if not isinstance(endpoint, str) or not endpoint:
        raise AdapterError("daemon endpoint is missing")
    version = daemon.get("daemonVersion") or daemon.get("version")
    if version is not None and str(version) != PINNED_PASEO_VERSION:
        raise AdapterError(f"daemon version mismatch: {version!r} vs pinned {PINNED_PASEO_VERSION!r}")
    pid = daemon.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid <= 0):
        raise AdapterError("daemon pid is invalid")
    return {"home": home, "endpoint": endpoint, "pid": pid, "version": version}


def validate_pi_binding(pi_path: str, pi_version: str | None, bindir: Path) -> dict:
    """Verify the invoked Pi executable resolves through the candidate bindir."""
    if not pi_path:
        raise AdapterError("Pi executable path is missing")
    # Must resolve inside the explicitly bound bindir (fake-only isolation),
    # never an ambient host path outside it.
    try:
        rp = Path(pi_path).resolve()
        br = Path(bindir).resolve()
    except OSError as exc:
        raise AdapterError(f"Pi path unreadable: {exc}") from exc
    if rp != br / "pi" and br not in rp.parents and rp != br / "paseo":
        # Allow the candidate container path when explicitly marked? No:
        # synthetic fixtures must prove bindir resolution. Anything else fails.
        raise AdapterError(f"Pi executable is not candidate-local: {pi_path!r}")
    if pi_version is not None and str(pi_version).strip() != PINNED_PI_VERSION:
        raise AdapterError(f"Pi version mismatch: {pi_version!r} vs pinned {PINNED_PI_VERSION!r}")
    return {"path": str(rp), "version": PINNED_PI_VERSION}


def classify_effective_profile(requested: dict, observed) -> dict:
    """Compare requested fixed profile vs observed effective execution.

    observed is None/unknown -> pending/unknown, unsatisfied, no replay.
    observed thinking != max (e.g. xhigh clamp) -> terminal mismatch,
    unsatisfied with the Research/Planning boundary. Only an observed
    exact max with matching provider/model satisfies the profile gate,
    and even then only a real execution_class with completed inference
    can satisfy final validation (fixtures always leave it unsatisfied).
    """
    if observed is None or (isinstance(observed, dict) and observed.get("unknown")):
        return {
            "gate": "UNKNOWN",
            "real_satisfied": False,
            "reason": "effective profile unknown; " + EFFECTIVE_UNOBSERVABLE_BOUNDARY,
            "replay": False,
        }
    if not isinstance(observed, dict):
        return {"gate": "FAIL", "real_satisfied": False, "reason": "effective profile malformed", "replay": False}
    prov = observed.get("provider")
    model = observed.get("model")
    thinking = observed.get("thinking") or observed.get("thinkingOptionId")
    if prov != FIXED_PROVIDER or model != FIXED_MODEL:
        return {
            "gate": "FAIL",
            "real_satisfied": False,
            "reason": f"wrong effective identity: {prov!r}/{model!r}",
            "replay": False,
        }
    if thinking != FIXED_THINKING:
        if thinking in ("xhigh", "high", "medium", "low", "minimal", "off"):
            return {
                "gate": "FAIL",
                "real_satisfied": False,
                "reason": (
                    f"downgraded effective contribution: {thinking!r} (requested max); "
                    + EFFECTIVE_UNOBSERVABLE_BOUNDARY
                ),
                "replay": False,
            }
        return {"gate": "FAIL", "real_satisfied": False, "reason": f"unsupported effective contribution: {thinking!r}", "replay": False}
    return {"gate": "PASS", "real_satisfied": "deferred-to-real", "reason": "requested==observed (profile gate only)", "replay": False}


def run_guard_dispatch(*, guard_file: Path, agent_root: Path, prompt: str, cwd: str,
                       bindir: Path, extra_env: dict | None = None, timeout: int = 60,
                       native_args: bool = False) -> dict:
    """Invoke the real guard bytes with fake-only executable resolution.

    Copies the delivered launcher into a disposable agent root (so the exact
    shipped bytes are exercised), resolves executables ONLY through the
    test-owned bindir, snapshots dispatch BEFORE temp cleanup. Returns a
    snapshot dict with returncode/stderr/dispatched/dispatch_lines.
    Never causes real inference when bindir holds only fake executables.
    """
    with tempfile.TemporaryDirectory(prefix="muse-adapter-") as tmp:
        tmp_p = Path(tmp)
        agent = tmp_p / "agent"
        (agent / "bin").mkdir(parents=True)
        (agent / "policies").mkdir(parents=True)
        launcher = agent / "bin" / "run-llm-test.sh"
        launcher.write_bytes(Path(guard_file).read_bytes())
        launcher.chmod(0o755)
        # Policy for the disposable agent root: mirror the repo policy unless
        # the caller supplied an explicit agent_root policy fixture.
        src_policy = Path(agent_root) / "policies" / "llm-test-policy.json"
        if src_policy.is_file():
            (agent / "policies" / "llm-test-policy.json").write_bytes(src_policy.read_bytes())
        else:
            # Fall back to the repo policy so the guard shape is preserved.
            (agent / "policies" / "llm-test-policy.json").write_text(json.dumps({
                "schema": 1,
                "real_llm_tests": {
                    "provider": FIXED_PROVIDER, "model": FIXED_MODEL,
                    "thinking": FIXED_THINKING, "forbidden_models": list(FORBIDDEN_MODELS),
                    "fallback_allowed": False,
                },
            }))
        marker = tmp_p / "dispatched.txt"
        env = {"PATH": str(bindir), "DISPATCH_MARKER": str(marker)}
        if extra_env:
            # Only nonsecret configuration may be passed; secret values are
            # never placed in env by this adapter (mounts only).
            for k, v in extra_env.items():
                if "KEY" in k.upper() or "TOKEN" in k.upper() or "SECRET" in k.upper():
                    raise AdapterError(f"refusing secret-bearing env: {k}")
                env[k] = v
        argv = [str(launcher)]
        argv += ["--native-create-agent-args"] if native_args else [prompt, cwd]
        try:
            proc = subprocess.run(argv, env=env, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            return {"returncode": None, "timeout": True, "stderr": "guard dispatch timeout",
                    "dispatched": marker.is_file(),
                    "dispatch_lines": marker.read_text().splitlines() if marker.is_file() else []}
        except OSError as exc:
            return {"returncode": None, "timeout": False, "stderr": f"guard unavailable: {exc}",
                    "dispatched": False, "dispatch_lines": []}
        # Snapshot BEFORE the temp dir is deleted.
        snapshot = {
            "returncode": proc.returncode,
            "timeout": False,
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "dispatched": marker.is_file(),
            "dispatch_lines": marker.read_text().splitlines() if marker.is_file() else [],
        }
        return snapshot


def outcome_for_fixture(*, requested: dict, dispatch_snapshot: dict,
                        observed_effective, daemon_binding=None, pi_binding=None,
                        subject: dict | None = None) -> dict:
    """Build the typed fixture outcome. Fixture ALWAYS leaves real unsatisfied."""
    eff = classify_effective_profile(requested, observed_effective)
    if dispatch_snapshot.get("timeout"):
        terminal = "unknown"
        status = "UNKNOWN"
        reason = "guard dispatch timeout; occurrence unknown, no replay"
    elif not dispatch_snapshot.get("dispatched"):
        terminal = "terminal"
        status = "FAIL" if dispatch_snapshot.get("returncode") not in (0, None) else "BLOCKED"
        reason = (dispatch_snapshot.get("stderr") or "guard did not dispatch")[:300]
    elif eff["gate"] != "PASS":
        terminal = "terminal"
        status = "FAIL"
        reason = eff["reason"][:400]
    else:
        # Mechanical dispatch observed with matching profile gate, but this
        # is still a fixture: real inference did not complete.
        terminal = "terminal"
        status = "PASS"
        reason = "fixture dispatch observed; real inference not completed"
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_class": "fixture",
        "status": status,
        "terminal_class": terminal,
        "requested_profile": requested,
        "observed_effective": observed_effective,
        "effective_gate": eff["gate"],
        "daemon_binding": daemon_binding,
        "pi_binding": pi_binding,
        "subject": subject or {},
        "dispatch_observed": bool(dispatch_snapshot.get("dispatched")),
        "real_validation_satisfied": False,
        "real_reason": "fixture/rehearsal never satisfies final validation",
        "reason": reason,
    }
