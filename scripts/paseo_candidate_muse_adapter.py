#!/usr/bin/env python3
"""Bounded candidate-local Muse adapter (M07-T05, coherent rewrite).

The future-authorized path invokes the repository-delivered canonical guard
``config/pi-agent/bin/run-llm-test.sh`` in its PROMPT form from the
disposable candidate's own environment (own local Paseo daemon/home), with
candidate-local daemon/Pi lifecycle observation, staged witness extension,
per-owned-test request/response/terminal aggregation, and strict
``meta/muse-spark-1.3-contributor/max`` no-fallback profile. The Tower
validator CALLS this module (dispatch, daemon/Pi observers, witness
stage/load/aggregate, dedicated Muse reader); those callsites are the
product path, not declarations.

Source-qualified credential: official Meta provider source
(``pi-ai`` ``providers/meta.ts`` → ``envApiKeyAuth("Meta Model API key",
["META_API_KEY"])`` + ``lazyOAuth`` native subscription) identifies
``META_API_KEY`` env API-key auth and native OAuth device flow. The
dedicated validation credential is therefore a private ``META_API_KEY=...``
(or bare-key) file, mounted read-only at ``/run/secrets/pi-unraid-meta``
and provisioned inside the candidate via the ``META_API_KEY_FILE`` pointer
(never the value on argv/env). Ordinary-agent auth is never read/copied;
no real admission occurs in M07-T05 (synthetic files only). Native OAuth
remains a manual operator step (M08-T01).

Source-qualified payload semantics (pinned pi 0.87.1 / pi-ai 0.87.1):
``before_provider_request`` event carries ONLY ``{type, payload}`` where
``payload`` is the provider params (openai-responses ``buildParams``:
``model`` id string, ``reasoning: {effort, summary}``, ``input``,
``max_output_tokens``, ...). There is NO generic ``payload.provider`` or
``payload.thinking`` field; the extension records ``payload.model``,
``payload.reasoning.effort`` (fallback ``reasoningEffort``), plus the
``M07_T05_TEST_ID`` correlation env and response ``status`` from
``after_provider_response`` (``{type, status, headers}`` — headers never
recorded). Provider is the fixed ``meta`` from guard policy, mapped from
the observed model id; it is never taken from an invented payload field.
Only whitelisted nonsecret facts are recorded; raw headers/body/prompt/
tokens are never recorded.

Effective max: pinned ``meta.json`` maps
``muse-spark-1.3-contributor`` ``max→null`` (unsupported) while
``muse-spark-1.3`` maps ``max→max``; ``clampThinkingLevel(max)`` on the
contributor therefore yields ``xhigh``. Requested ``max`` vs observed
``xhigh`` is a terminal FAIL (clamp proven), not a pass. Unknown/absent
witness is UNKNOWN, never replayed, failing closed to M08-T01/Research.

All execution in M07-T05 is synthetic/local with fake-only executables;
this module never causes real provider inference by itself. Fixture/
rehearsal ALWAYS leaves real satisfaction false; the real-mode path exists
structurally (completed dispatch + aggregated witness + all bindings PASS)
and is testable under fakes, not hardcoded false.
"""
from __future__ import annotations

import hashlib
import json
import os
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

# Dedicated Muse validation credential, source-qualified to official Meta
# provider auth (META_API_KEY env + native OAuth). Private file on the host,
# read-only mount inside the candidate at MUSE_SECRET_TARGET. The value is
# never placed on argv/env, never logged, never persisted in evidence.
# Provisioning uses the META_API_KEY_FILE pointer (nonsecret path) read
# inside the candidate wrapper; only synthetic files in M07-T05.
MUSE_SECRET_TARGET = "/run/secrets/pi-unraid-meta"
MUSE_SECRET_ENV_NAME = "META_API_KEY"
MUSE_SECRET_POINTER_ENV = "META_API_KEY_FILE"

# Production daemon homes that must never be selected as the candidate.
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
    """Read back the repository-delivered guard bytes and fixed-profile shape."""
    p = Path(source_root) / GUARD_REL
    if not p.is_file():
        raise AdapterBlocked(f"canonical guard unavailable: {GUARD_REL}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise AdapterBlocked(f"canonical guard unreadable: {exc}") from exc
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
    if not is_disposable_path(resolved, disposable_root):
        raise AdapterError(
            f"candidate home is not under the disposable root: {resolved} vs {disposable_root}"
        )
    return resolved


def validate_daemon_binding(daemon: dict, candidate_home: Path) -> dict:
    """Verify observed daemon dict belongs to the disposable candidate.

    ``daemon`` is the parsed ``paseo status --format json`` observed through
    the candidate-local executable (validator passes the exec-observed dict,
    never host paths). Required: home == candidate_home, endpoint present,
    pid positive when present. Version is checked by the validator against
    the frozen-candidate expectation (not a pinned constant here).
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
    pid = daemon.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid <= 0):
        raise AdapterError("daemon pid is invalid")
    version = daemon.get("daemonVersion") or daemon.get("version")
    return {"home": home, "endpoint": endpoint, "pid": pid, "version": version}


def validate_pi_binding(pi_path: str, pi_version: str | None, bindir: Path) -> dict:
    """Verify the invoked Pi executable resolves through the candidate bindir."""
    if not pi_path:
        raise AdapterError("Pi executable path is missing")
    try:
        rp = Path(pi_path).resolve()
        br = Path(bindir).resolve()
    except OSError as exc:
        raise AdapterError(f"Pi path unreadable: {exc}") from exc
    if rp != br / "pi" and br not in rp.parents and rp != br / "paseo":
        raise AdapterError(f"Pi executable is not candidate-local: {pi_path!r}")
    if pi_version is not None and str(pi_version).strip() != PINNED_PI_VERSION:
        raise AdapterError(f"Pi version mismatch: {pi_version!r} vs pinned {PINNED_PI_VERSION!r}")
    return {"path": str(rp), "version": PINNED_PI_VERSION}


def classify_effective_profile(requested: dict, observed) -> dict:
    """Compare requested fixed profile vs observed effective execution.

    Kept for helper-level unit coverage; the validator uses
    :func:`classify_aggregated_witness` on per-test aggregated events.
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
    thinking = observed.get("thinking") or observed.get("thinkingOptionId") or observed.get("effort")
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
    """Legacy helper-level guard invocation (unit coverage only).

    The validator's product path is :func:`dispatch_guarded_test` (prompt
    form with witness + test-ID correlation). This helper is retained for
    direct unit tests; it still fails closed on missing exact policy and
    never fabricates a substitute.
    """
    with tempfile.TemporaryDirectory(prefix="muse-adapter-") as tmp:
        tmp_p = Path(tmp)
        agent = tmp_p / "agent"
        (agent / "bin").mkdir(parents=True)
        (agent / "policies").mkdir(parents=True)
        launcher = agent / "bin" / "run-llm-test.sh"
        launcher.write_bytes(Path(guard_file).read_bytes())
        launcher.chmod(0o755)
        src_policy = Path(agent_root) / "policies" / "llm-test-policy.json"
        if not src_policy.is_file():
            raise AdapterBlocked(
                "canonical policy unavailable for dispatch: "
                f"{src_policy} (missing exact delivered policy fails closed)"
            )
        (agent / "policies" / "llm-test-policy.json").write_bytes(src_policy.read_bytes())
        marker = tmp_p / "dispatched.txt"
        env = {"PATH": str(bindir), "DISPATCH_MARKER": str(marker)}
        if extra_env:
            for k, v in extra_env.items():
                if "KEY" in k.upper() or "TOKEN" in k.upper() or "SECRET" in k.upper():
                    raise AdapterError(f"refusing secret-bearing env: {k}")
                env[k] = v
        argv = [str(launcher)]
        argv += ["--native-create-agent-args"] if native_args else [prompt, cwd]
        try:
            proc = subprocess.run(argv, env=env, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {"returncode": None, "timeout": True, "stderr": "guard dispatch timeout",
                    "dispatched": marker.is_file(),
                    "dispatch_lines": marker.read_text().splitlines() if marker.is_file() else []}
        except OSError as exc:
            return {"returncode": None, "timeout": False, "stderr": f"guard unavailable: {exc}",
                    "dispatched": False, "dispatch_lines": []}
        return {
            "returncode": proc.returncode,
            "timeout": False,
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "dispatched": marker.is_file(),
            "dispatch_lines": marker.read_text().splitlines() if marker.is_file() else [],
        }


# ---------------------------------------------------------------------------
# Dedicated Muse credential (source-qualified META_API_KEY)
# ---------------------------------------------------------------------------

def read_dedicated_muse_secret(secret_path) -> str:
    """Read the dedicated META_API_KEY validation credential (strict).

    Validates: regular file, not a symlink, private mode (0600/0400),
    exactly one non-empty entry, ``META_API_KEY=<value>`` or bare key with
    NON-EMPTY value (empty values fail closed — closes the Tower-parser
    empty-value hole). Never logs the value. Missing → Blocked;
    malformed/insecure → Error. Only synthetic files in M07-T05.
    """
    pth = Path(secret_path)
    try:
        if pth.is_symlink():
            raise AdapterError("dedicated Muse credential must not be a symlink")
        st = pth.stat()
    except FileNotFoundError as exc:
        raise AdapterBlocked("dedicated Muse credential file unavailable") from exc
    except OSError as exc:
        raise AdapterBlocked("dedicated Muse credential unavailable") from exc
    import stat as _sm
    if not _sm.S_ISREG(st.st_mode):
        raise AdapterError("dedicated Muse credential must be a regular file")
    mode = _sm.S_IMODE(st.st_mode)
    if mode & 0o077:
        raise AdapterError(f"dedicated Muse credential must be private (0600/0400), got {mode:04o}")
    try:
        text = pth.read_text(encoding="utf-8")
    except OSError as exc:
        raise AdapterBlocked("dedicated Muse credential unreadable") from exc
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if len(lines) != 1:
        raise AdapterError("dedicated Muse credential must hold exactly one entry")
    line = lines[0]
    if "=" in line:
        name, _, value = line.partition("=")
        if name != MUSE_SECRET_ENV_NAME:
            raise AdapterError(
                f"dedicated Muse credential entry must be {MUSE_SECRET_ENV_NAME} or a bare key"
            )
        value = value.strip()
    else:
        value = line.strip()
    if not value or any(ch.isspace() for ch in value) or "\x00" in value:
        raise AdapterError("dedicated Muse credential value is invalid")
    if len(value) > 4096:
        raise AdapterError("dedicated Muse credential value is too long")
    return value


def muse_secret_mount_args(secret_resolved) -> list:
    """Read-only mount args for the dedicated META_API_KEY credential."""
    return ["-v", f"{secret_resolved}:{MUSE_SECRET_TARGET}:ro"]


# ---------------------------------------------------------------------------
# Witness observer (actual pinned payload semantics, per-test aggregation)
# ---------------------------------------------------------------------------
#
# Pinned semantics: ``before_provider_request`` → ``{type, payload}`` where
# payload is openai-responses params (``model`` id string,
# ``reasoning: {effort, summary}``, ...). ``after_provider_response`` →
# ``{type, status, headers}`` (headers never recorded). The extension also
# reads ``M07_T05_TEST_ID`` so every event correlates to one owned test.
# Only nonsecret ``test_id/model/effort/status/kind`` are recorded.

WITNESS_KINDS = ("request", "response", "terminal")
EFFECTIVE_WITNESS_ALLOWLIST = ("test_id", "model", "effort", "status", "kind")


def stage_witness_extension(dest: Path) -> Path:
    """Stage the test-owned witness extension (actual payload fields).

    Records per event (JSONL): ``test_id`` (from ``M07_T05_TEST_ID``),
    ``model`` (``payload.model`` string), ``effort``
    (``payload.reasoning.effort`` fallback ``reasoningEffort``), ``status``
    (response ``status`` or terminal ``stopReason``), ``kind``
    (request/response/terminal). Nothing else is recorded.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "// M07-T05 witness (test-owned, secret-free, actual payload fields).\n"
        "export default function (ctx) {\n"
        "  const fs = require('node:fs');\n"
        "  const witness = process.env.M07_T05_WITNESS_FILE || '/tmp/m07-t05-witness.jsonl';\n"
        "  const testId = process.env.M07_T05_TEST_ID || '';\n"
        "  function emit(obj) {\n"
        "    const allow = { test_id: String(testId).slice(0,64) };\n"
        "    for (const k of ['model','effort','status','kind']) {\n"
        "      if (obj[k] !== undefined) allow[k] = String(obj[k]).slice(0,128);\n"
        "    }\n"
        "    try { fs.appendFileSync(witness, JSON.stringify(allow)+'\\n', {mode: 0o600}); } catch {}\n"
        "  }\n"
        "  ctx.on('before_provider_request', (ev) => {\n"
        "    try {\n"
        "      const p = ev.payload || {};\n"
        "      const r = p.reasoning || {};\n"
        "      emit({kind:'request', model: p.model, effort: (r.effort || p.reasoningEffort)});\n"
        "    } catch {}\n"
        "    return ev.payload;\n"
        "  });\n"
        "  ctx.on('after_provider_response', (ev) => {\n"
        "    try { emit({kind:'response', status: ev.status}); } catch {}\n"
        "  });\n"
        "}\n",
        encoding="utf-8",
    )
    try:
        dest.chmod(0o644)
    except OSError:
        pass
    return dest


# Backwards-compatible alias (old tests import this name).
def write_effective_witness_extension(dest: Path) -> Path:
    return stage_witness_extension(dest)


def load_witness_events(path: Path, test_id: str) -> list:
    """Load and filter witness events for one owned test.

    Returns only events whose ``test_id`` equals the owned test id.
    Stale (other test), caller (missing/mismatched id), and malformed lines
    are dropped. Empty → caller must treat as UNKNOWN (no replay).
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            doc = json.loads(ln)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        if doc.get("test_id") != test_id:
            continue
        filt = {"test_id": test_id}
        for k in ("model", "effort", "status", "kind"):
            v = doc.get(k)
            if isinstance(v, str) and v:
                filt[k] = v[:128]
        if filt.get("kind") not in WITNESS_KINDS:
            continue
        out.append(filt)
    return out


def parse_effective_witness_file(path: Path):
    """Legacy single-dict parse (kept for unit coverage).

    NOTE: retaining only the last event loses request fields when a
    response-status event follows — the validator therefore uses
    :func:`load_witness_events` + :func:`aggregate_witness` instead.
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    obs = None
    for ln in lines[-20:]:
        ln = ln.strip()
        if not ln:
            continue
        try:
            doc = json.loads(ln)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        filt = {k: doc[k] for k in EFFECTIVE_WITNESS_ALLOWLIST if isinstance(doc.get(k), str)}
        if filt:
            obs = filt
    if obs is None:
        return None
    return {
        "provider": obs.get("provider"),
        "model": obs.get("model"),
        "thinking": obs.get("thinking"),
        "unknown": False,
    }


def aggregate_witness(events: list, *, test_id: str, expected_model: str) -> dict:
    """Aggregate one owned test's request+response+terminal events.

    Returns ``{gate, observed, reason, replay}`` where observed is
    ``{provider, model, thinking}`` with thinking = on-wire effort.
    Rules: no request event → UNKNOWN; model mismatch vs expected →
    FAIL (wrong subject); effort != max → FAIL (clamp proven); response
    status missing/non-2xx → FAIL/UNKNOWN (no success); terminal event
    missing → UNKNOWN (occurrence uncertain, no resend); contradictory
    efforts across request events → FAIL (forged witness).
    """
    reqs = [e for e in events if e.get("kind") == "request" and e.get("test_id") == test_id]
    resps = [e for e in events if e.get("kind") == "response" and e.get("test_id") == test_id]
    terms = [e for e in events if e.get("kind") == "terminal" and e.get("test_id") == test_id]
    if not reqs:
        return {"gate": "UNKNOWN", "observed": None,
                "reason": "no witness request for owned test; " + EFFECTIVE_UNOBSERVABLE_BOUNDARY,
                "replay": False}
    efforts = {e.get("effort") for e in reqs if e.get("effort")}
    models = {e.get("model") for e in reqs if e.get("model")}
    if len(models) > 1:
        return {"gate": "FAIL", "observed": None, "reason": "contradictory witness models", "replay": False}
    model = next(iter(models)) if models else None
    if model != expected_model:
        return {"gate": "FAIL", "observed": None,
                "reason": f"wrong witness model: {model!r} vs {expected_model!r}", "replay": False}
    if len(efforts) > 1:
        return {"gate": "FAIL", "observed": None, "reason": "contradictory witness efforts", "replay": False}
    effort = next(iter(efforts)) if efforts else None
    if effort is None:
        return {"gate": "UNKNOWN", "observed": None,
                "reason": "witness effort missing; " + EFFECTIVE_UNOBSERVABLE_BOUNDARY, "replay": False}
    observed = {"provider": FIXED_PROVIDER, "model": model, "thinking": effort}
    if effort != FIXED_THINKING:
        return {"gate": "FAIL", "observed": observed,
                "reason": f"downgraded on-wire effort: {effort!r} (requested max); "
                + EFFECTIVE_UNOBSERVABLE_BOUNDARY, "replay": False}
    if not resps:
        return {"gate": "UNKNOWN", "observed": observed,
                "reason": "witness response missing; occurrence uncertain, no resend", "replay": False}
    try:
        statuses = [int(str(e.get("status", "")).strip()) for e in resps if str(e.get("status", "")).strip().isdigit()]
    except (ValueError, TypeError):
        statuses = []
    if statuses and not any(200 <= s < 300 for s in statuses):
        return {"gate": "FAIL", "observed": observed,
                "reason": f"witness response not successful: {statuses}", "replay": False}
    if not statuses:
        # Non-numeric statuses (e.g. 'ok') are recorded but cannot prove HTTP
        # success; require the terminal event for completion.
        pass
    if not terms:
        return {"gate": "UNKNOWN", "observed": observed,
                "reason": "witness terminal missing; occurrence uncertain, no resend", "replay": False}
    last_term = terms[-1].get("status", "")
    if last_term not in ("done", "completed", "success", "idle", "0"):
        return {"gate": "FAIL", "observed": observed,
                "reason": f"witness terminal not successful: {last_term!r}", "replay": False}
    return {"gate": "PASS", "observed": observed,
            "reason": "request+response+terminal aggregated for owned test", "replay": False}


def classify_aggregated_witness(events: list, *, test_id: str) -> dict:
    """Classify witness events for the fixed profile (validator entrypoint)."""
    return aggregate_witness(events, test_id=test_id, expected_model=FIXED_MODEL)


# ---------------------------------------------------------------------------
# Integrated product path: daemon/Pi observers + guarded dispatch (validator calls these)
# ---------------------------------------------------------------------------

def observe_daemon_status(exec_run, *, candidate_home: str, expected_version: str) -> dict:
    """Observe the candidate-local daemon via exec (validator callsite).

    ``exec_run`` is ``fn(argv, timeout) -> CompletedProcess``-like running
    ``paseo status --format json --home <candidate_home>`` INSIDE the
    candidate namespace. The returned dict is parsed and validated against
    the candidate home + frozen-candidate expected version (never host
    paths or caller labels). Production homes fail closed.
    """
    proc = exec_run(
        ["paseo", "status", "--format", "json", "--home", candidate_home], timeout=30
    )
    if getattr(proc, "returncode", 1) != 0:
        raise AdapterBlocked("candidate daemon status unavailable")
    try:
        doc = json.loads((getattr(proc, "stdout", "") or "").strip())
    except (json.JSONDecodeError, ValueError) as exc:
        raise AdapterError("candidate daemon status malformed") from exc
    if isinstance(doc, list):
        doc = doc[0] if doc else {}
    if not isinstance(doc, dict):
        raise AdapterError("candidate daemon status malformed")
    home = doc.get("home")
    if not isinstance(home, str) or home != candidate_home:
        # Candidate-namespace comparison (both sides are in-candidate paths
        # observed via exec inside the candidate; host resolve() must NOT be
        # applied across the namespace boundary).
        raise AdapterError("daemon home is not the candidate home")
    endpoint = doc.get("listen") or doc.get("endpoint") or doc.get("configuredListen")
    if not isinstance(endpoint, str) or not endpoint:
        raise AdapterError("daemon endpoint is missing")
    version = doc.get("daemonVersion") or doc.get("version")
    if version is None or str(version) != str(expected_version):
        raise AdapterError(f"daemon version mismatch vs frozen candidate: {version!r}")
    pid = doc.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid <= 0):
        raise AdapterError("daemon pid is invalid")
    return {"home": home, "endpoint": endpoint, "pid": pid, "version": str(version)}


def observe_pi_version(exec_run, *, expected_version: str) -> dict:
    """Observe the candidate-local Pi via exec (validator callsite).

    Runs ``command -v pi`` + ``pi --version`` INSIDE the candidate and
    requires the version to equal the frozen-candidate expectation.
    """
    which = exec_run(["sh", "-c", "command -v pi"], timeout=30)
    if getattr(which, "returncode", 1) != 0:
        raise AdapterBlocked("candidate Pi executable unavailable")
    path = (getattr(which, "stdout", "") or "").strip().splitlines()
    path = path[-1].strip() if path else ""
    if not path:
        raise AdapterError("candidate Pi path missing")
    ver = exec_run(["pi", "--version"], timeout=30)
    if getattr(ver, "returncode", 1) != 0:
        raise AdapterBlocked("candidate Pi version unavailable")
    out = (getattr(ver, "stdout", "") or "").strip().splitlines()
    out = out[-1].strip() if out else ""
    if out != str(expected_version):
        raise AdapterError(f"Pi version mismatch vs frozen candidate: {out!r}")
    return {"path": path, "version": out}


def dispatch_guarded_test(*, guard_file: Path, agent_root: Path, prompt: str, cwd: str,
                          bindir: Path, test_id: str, witness_file: Path,
                          meta_secret_file: Path | None = None, timeout: int = 120) -> dict:
    """Run the canonical guard PROMPT form with per-test witness correlation.

    Copies the exact guard bytes into a disposable agent root, executes the
    PROMPT form (``guard PROMPT [CWD]`` — the future-authorized smoke shape,
    NOT ``--native-create-agent-args`` export) with ``PATH`` isolated to the
    test-owned ``bindir`` (fake ``paseo`` records dispatch + witness, never
    real inference), ``M07_T05_TEST_ID``/``M07_T05_WITNESS_FILE`` correlation,
    and ``META_API_KEY_FILE`` pointer (never the secret value). Snapshots
    dispatch + witness events BEFORE temp cleanup. Timeout → UNKNOWN snapshot
    with ``replay: False`` (never resend blindly).

    The validator CALLS this function; the fake candidate exec in tests runs
    the actual guard script locally with the fake bindir, exercising real
    guard bytes (profile gates, fallback refusal, exec line).
    """
    if not test_id or not isinstance(test_id, str):
        raise AdapterError("test_id is required for guarded dispatch")
    with tempfile.TemporaryDirectory(prefix="muse-dispatched-") as tmp:
        tmp_p = Path(tmp)
        agent = tmp_p / "agent"
        (agent / "bin").mkdir(parents=True)
        (agent / "policies").mkdir(parents=True)
        launcher = agent / "bin" / "run-llm-test.sh"
        launcher.write_bytes(Path(guard_file).read_bytes())
        launcher.chmod(0o755)
        src_policy = Path(agent_root) / "policies" / "llm-test-policy.json"
        if not src_policy.is_file():
            raise AdapterBlocked(
                "canonical policy unavailable for dispatch "
                "(missing exact delivered policy fails closed)"
            )
        (agent / "policies" / "llm-test-policy.json").write_bytes(src_policy.read_bytes())
        witness_file = Path(witness_file)
        witness_file.parent.mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": str(bindir),
            "M07_T05_TEST_ID": test_id,
            "M07_T05_WITNESS_FILE": str(witness_file),
        }
        if meta_secret_file is not None:
            # Pointer only; the value is read inside the candidate wrapper.
            env[MUSE_SECRET_POINTER_ENV] = str(meta_secret_file)
        try:
            proc = subprocess.run([str(launcher), prompt, cwd], env=env, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            events = load_witness_events(witness_file, test_id)
            return {"returncode": None, "timeout": True, "dispatched": bool(events),
                    "events": events, "replay": False,
                    "stderr": "guard dispatch timeout; occurrence unknown, no replay"}
        except OSError as exc:
            return {"returncode": None, "timeout": False, "dispatched": False,
                    "events": [], "replay": False, "stderr": f"guard unavailable: {exc}"}
        events = load_witness_events(witness_file, test_id)
        dispatched = proc.returncode == 0 and bool([e for e in events if e.get("kind") == "request"])
        return {
            "returncode": proc.returncode,
            "timeout": False,
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "dispatched": dispatched,
            "events": events,
            "replay": False,
        }


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
        rc = dispatch_snapshot.get("returncode")
        if rc not in (0, None):
            status = "FAIL"
            reason = f"guard did not dispatch (exit {rc}); no replay"
        else:
            status = "BLOCKED"
            reason = "guard did not dispatch; input unavailable"
    elif eff["gate"] != "PASS":
        terminal = "terminal"
        status = "FAIL"
        reason = eff["reason"][:400]
    else:
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
