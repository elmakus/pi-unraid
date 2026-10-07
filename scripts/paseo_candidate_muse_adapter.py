#!/usr/bin/env python3
"""Bounded candidate-local Muse adapter (M07-T05, coherent rewrite).

The future-authorized path invokes the repository-delivered canonical guard
``config/pi-agent/bin/run-llm-test.sh`` through its fixed-profile
candidate-only ``--candidate-owned`` extension from the disposable private
Paseo daemon/home, with
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
recorded). Provider and effective Pi thinking come from the supported
handler context (``ctx.model.provider`` and ``ctx.thinkingLevel``), never
from policy or a model-name inference. Actual context and wire effort must
both agree with the fixed profile. On mismatch or failed private observation,
``ctx.abort()`` aborts the run; throwing alone is not a transport barrier.
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
import re
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
MUSE_MAX_FRAGMENT_REL = Path("models.muse-max-override.json")
MUSE_MAX_MERGE_REL = Path("bin/paseo-muse-max-merge.py")
MUSE_MAX_EFFECTIVE_REL = Path("models.json")
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
    'pinned default Contributor max=null is a negative capability fact; '
    'preflight must block it before dispatch, with no override or fallback'
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


# ---------------------------------------------------------------------------
# M07-T05A muse-max delivery: secret-free minimal modelOverrides fragment +
# narrow merge-safe effective configuration (pinned Pi 0.87.1 documented
# semantics). Product path for the validator; unit-tested with fake-only
# boundaries. Preserves fixed meta/muse-spark-1.3-contributor/max +
# no-fallback; never installs a whole models.json and never relies on the
# mutable models-store overlay.
# ---------------------------------------------------------------------------

def muse_max_fragment_identity(source_root: Path) -> dict:
    """Read back the frozen secret-free fragment bytes, mode and digest."""
    p = Path(source_root) / "config" / "pi-agent" / MUSE_MAX_FRAGMENT_REL
    if p.is_symlink() or not p.is_file():
        raise AdapterBlocked(f"muse-max fragment unavailable: {MUSE_MAX_FRAGMENT_REL}")
    try:
        raw = p.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise AdapterError(f"muse-max fragment unreadable: {exc}") from exc
    validate_muse_max_fragment(doc)
    mode = p.stat().st_mode & 0o777
    if mode != 0o644:
        raise AdapterError(f"muse-max fragment mode is not 0644: {mode:04o}")
    return {
        "path": MUSE_MAX_FRAGMENT_REL.as_posix(),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "mode": f"{mode:04o}",
        "bytes": len(raw),
    }


def validate_muse_max_fragment(doc) -> dict:
    """Require EXACTLY the minimal documented override, nothing else."""
    if not isinstance(doc, dict):
        raise AdapterError("muse-max fragment root must be an object")
    if set(doc.keys()) != {"providers"}:
        raise AdapterError("muse-max fragment must contain only 'providers'")
    providers = doc.get("providers")
    if not isinstance(providers, dict) or set(providers.keys()) != {FIXED_PROVIDER}:
        raise AdapterError("muse-max fragment must contain only the 'meta' provider")
    meta = providers.get(FIXED_PROVIDER)
    if not isinstance(meta, dict) or set(meta.keys()) != {"modelOverrides"}:
        raise AdapterError("muse-max fragment meta must contain only 'modelOverrides'")
    overrides = meta.get("modelOverrides")
    if not isinstance(overrides, dict) or set(overrides.keys()) != {FIXED_MODEL}:
        raise AdapterError("muse-max fragment must override only the Contributor model")
    entry = overrides.get(FIXED_MODEL)
    if not isinstance(entry, dict) or set(entry.keys()) != {"thinkingLevelMap"}:
        raise AdapterError("muse-max fragment entry must contain only 'thinkingLevelMap'")
    tlm = entry.get("thinkingLevelMap")
    if not isinstance(tlm, dict) or set(tlm.keys()) != {FIXED_THINKING}:
        raise AdapterError("muse-max fragment thinkingLevelMap must contain only 'max'")
    if tlm.get(FIXED_THINKING) != "max":
        raise AdapterError("muse-max fragment thinkingLevelMap.max must be exactly \"max\"")
    text = json.dumps(doc)
    if "!" in text and "!command" in text:
        raise AdapterError("muse-max fragment must be secret-free")
    for banned in ("apiKey", "baseUrl", "models", "api", "oauth", "headers", "authHeader"):
        if banned in meta:
            raise AdapterError(f"muse-max fragment must not carry {banned}")
    if "$" in text:
        raise AdapterError("muse-max fragment must be secret-free (no interpolation)")
    return doc


def merge_muse_max_effective(existing, fragment) -> dict:
    """Narrow merge preserving unrelated providers (pinned shallow key-merge)."""
    validate_muse_max_fragment(fragment)
    if not isinstance(existing, dict):
        raise AdapterError("existing effective config root must be an object")
    providers = existing.get("providers", {})
    if "providers" in existing and not isinstance(providers, dict):
        raise AdapterError("existing providers must be an object")
    merged = json.loads(json.dumps(existing))
    mproviders = merged.setdefault("providers", {})
    if not isinstance(mproviders, dict):
        raise AdapterError("existing providers must be an object")
    meta = mproviders.setdefault(FIXED_PROVIDER, {})
    if not isinstance(meta, dict):
        raise AdapterError("existing meta entry is not an object")
    overrides = meta.setdefault("modelOverrides", {})
    if not isinstance(overrides, dict):
        raise AdapterError("existing meta modelOverrides is not an object")
    entry = overrides.setdefault(FIXED_MODEL, {})
    if not isinstance(entry, dict):
        raise AdapterError("existing Contributor entry is not an object")
    tlm = entry.setdefault("thinkingLevelMap", {})
    if not isinstance(tlm, dict):
        raise AdapterError("existing thinkingLevelMap is not an object")
    tlm[FIXED_THINKING] = "max"
    return merged


def verify_muse_max_effective(doc) -> dict:
    """Verify the effective merged file carries the required override."""
    if not isinstance(doc, dict):
        raise AdapterError("effective models config root must be an object")
    try:
        value = doc["providers"][FIXED_PROVIDER]["modelOverrides"][FIXED_MODEL]["thinkingLevelMap"][FIXED_THINKING]
    except (KeyError, TypeError):
        raise AdapterError("effective config lacks the required muse max override") from None
    if value != "max":
        raise AdapterError("effective muse max override is not exactly \"max\" (null/clamped)")
    return {"model": f"{FIXED_PROVIDER}/{FIXED_MODEL}", "thinking": FIXED_THINKING}


def muse_max_effective_identity(raw: bytes, mode: int) -> dict:
    if not isinstance(raw, bytes) or not raw:
        raise AdapterError("effective config bytes are missing")
    if mode != 0o600:
        raise AdapterError(f"effective config mode is not 0600: {mode:04o}")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise AdapterError(f"effective config unreadable: {exc}") from exc
    verify_muse_max_effective(doc)
    return {
        "path": MUSE_MAX_EFFECTIVE_REL.as_posix(),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "mode": f"{mode:04o}",
        "bytes": len(raw),
    }


def apply_muse_max_merge(home_agent: Path, source_root: Path) -> dict:
    """Host-side narrow merge for validator staging (no inference/auth).

    Reads the frozen fragment from ``source_root/config/pi-agent`` and the
    existing effective file from ``home_agent/models.json`` (when present),
    validates both, writes the merged effective file atomically with mode
    ``0600`` when changed, and returns fragment + effective identities.
    The existing file is preserved unchanged on any validation failure.
    Idempotent: identical inputs yield ``changed: False`` with the same
    effective digest.
    """
    frag_path = Path(source_root) / "config" / "pi-agent" / MUSE_MAX_FRAGMENT_REL
    eff_path = Path(home_agent) / MUSE_MAX_EFFECTIVE_REL
    if frag_path.is_symlink() or not frag_path.is_file():
        raise AdapterBlocked(f"muse-max fragment unavailable: {MUSE_MAX_FRAGMENT_REL}")
    try:
        frag_raw = frag_path.read_bytes()
        frag_doc = json.loads(frag_raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise AdapterError(f"muse-max fragment unreadable: {exc}") from exc
    validate_muse_max_fragment(frag_doc)
    if eff_path.is_symlink():
        raise AdapterError(f"refusing symlink effective target: {eff_path}")
    if eff_path.exists():
        if not eff_path.is_file():
            raise AdapterError(f"refusing non-file effective target: {eff_path}")
        try:
            eff_raw = eff_path.read_bytes()
            eff_doc = json.loads(eff_raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            raise AdapterError(f"effective models.json unreadable; preserved unchanged: {exc}") from exc
        if not isinstance(eff_doc, dict):
            raise AdapterError("effective models.json root must be an object; preserved unchanged")
    else:
        eff_doc = {"providers": {}}
        eff_raw = b""
    merged = merge_muse_max_effective(eff_doc, frag_doc)
    rendered = (json.dumps(merged, sort_keys=True, indent=2) + "\n").encode("utf-8")
    verify_muse_max_effective(merged)
    if eff_path.exists():
        cur = eff_path.read_bytes()
        mode = eff_path.stat().st_mode & 0o777
        if cur == rendered and mode == 0o600:
            return {
                "changed": False,
                "fragment": {"sha256": "sha256:" + hashlib.sha256(frag_raw).hexdigest(), "mode": f"{frag_path.stat().st_mode & 0o777:04o}"},
                "effective": muse_max_effective_identity(rendered, 0o600),
            }
    import tempfile as _tf
    eff_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = _tf.mkstemp(prefix=".models.json.", dir=eff_path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, eff_path)
    finally:
        tmp.unlink(missing_ok=True)
    return {
        "changed": True,
        "fragment": {"sha256": "sha256:" + hashlib.sha256(frag_raw).hexdigest(), "mode": f"{frag_path.stat().st_mode & 0o777:04o}"},
        "effective": muse_max_effective_identity(rendered, 0o600),
    }


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
            'stderr': 'guard dispatch failed' if proc.returncode else '',
            'stdout': '',
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


LOADER_REL = Path("bin/m07-t05-candidate-env.sh")


def stage_candidate_env(dest: Path) -> Path:
    """Stage the candidate-local env loader (test-owned, ephemeral).

    Supported mechanism: the Pi Meta provider authenticates via
    ``envApiKeyAuth("Meta Model API key", ["META_API_KEY"])`` (pinned
    ``pi-ai`` ``providers/meta.ts``), i.e. Pi reads ``META_API_KEY`` from
    its process environment. The Pi subprocess environment is
    ``{...daemon process env, ...createAgent.env}`` (pinned Paseo server
    ``createExternalProcessEnv(baseEnv=daemon env, overlay=launch.env)``
    via ``buildPiLaunch``/``JsonlRpcProcess``); ``createAgent.env`` carries
    ONLY parsed ``--env`` (pinned ``run.js`` ``parseRunEnv``), so a raw key
    value must NEVER travel ``--env``/argv. Instead the disposable
    candidate receives the ``META_API_KEY_FILE`` pointer (read-only mount
    at ``/run/secrets/pi-unraid-meta``); this loader reads the pointer
    INSIDE the candidate, exports ``META_API_KEY`` for the child process it
    execs (daemon bring-up or guard dispatch), and never logs the value.
    Missing/unreadable/non-single/empty pointer fails closed (exit 42)
    before any child runs. Only synthetic files in M07-T05.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "#!/bin/sh\n"
        "# M07-T05 candidate-local Meta auth loader (test-owned, ephemeral).\n"
        "# Shell builtins only (read/case/export/exec): no sed/awk/tr/head/cat\n"
        "# dependency beyond the executable itself. Invoked via bash by the\n"
        "# validator dispatch, like the canonical guard.\n"
        "set -eu\n"
        "ptr=\"${META_API_KEY_FILE:-" + MUSE_SECRET_TARGET + "}\"\n"
        "if [ ! -f \"$ptr\" ]; then echo 'M07-T05 loader: META_API_KEY_FILE unavailable' >&2; exit 42; fi\n"
        "count=0\n"
        "auth_name='META_API_KEY'\n"
        "val=\"\"\n"
        "while read -r line || [ -n \"$line\" ]; do\n"
        "  case \"$line\" in \"\"|\\#*) continue ;; esac\n"
        "  count=$((count+1))\n"
        "  case \"$line\" in\n"
        "    *=*)\n"
        "      name=\"${line%%=*}\"\n"
        "      if [ \"$name\" != \"$auth_name\" ]; then echo 'M07-T05 loader: unexpected credential entry' >&2; exit 42; fi\n"
        "      val=\"${line#*=}\" ;;\n"
        "    *) val=\"$line\" ;;\n"
        "  esac\n"
        "done < \"$ptr\"\n"
        "if [ \"$count\" -ne 1 ]; then echo 'M07-T05 loader: credential must hold exactly one entry' >&2; exit 42; fi\n"
        "case \"$val\" in \"\"|*[[:space:]]*) echo 'M07-T05 loader: dedicated Muse credential is empty or invalid' >&2; exit 42 ;; esac\n"
        "export \"${auth_name}=${val}\"\n"
        "exec \"$@\"\n",
        encoding="utf-8",
    )
    try:
        dest.chmod(0o755)
    except OSError:
        pass
    return dest


def stage_meta_loader(dest: Path, *, guard_path: str = "/home/paseo/.pi/agent/bin/run-llm-test.sh") -> Path:
    """Backwards-compatible loader staging.

    Stages :func:`stage_candidate_env` (generic ``exec "$@"`` form).
    Callers pass the guard path plus prompt args explicitly at exec time.
    The ``guard_path`` parameter is accepted and ignored. """
    _ = guard_path
    return stage_candidate_env(dest)


# ---------------------------------------------------------------------------
# Witness observer (actual pinned payload semantics, per-test aggregation)
# ---------------------------------------------------------------------------
#
# Pinned semantics: ``before_provider_request`` → ``{type, payload}`` where
# payload is openai-responses params (``model`` id string,
# ``reasoning: {effort, summary}``, ...). ``after_provider_response`` →
# ``{type, status, headers}`` (headers never recorded). The extension also
# reads ``M07_T05_TEST_ID`` so every event correlates to one owned test.
# Only nonsecret whitelisted test/model/context/effort/status/kind facts are recorded.

WITNESS_KINDS = ("request", "response", "terminal")
EFFECTIVE_WITNESS_ALLOWLIST = ("test_id", "provider", "thinking", "model", "effort", "status", "kind")


def stage_witness_extension(dest: Path) -> Path:
    """Stage the test-owned witness extension (actual payload fields).

    Records per event (JSONL): ``test_id`` (from ``M07_T05_TEST_ID``),
    ``model`` (qualified ``payload.model``), actual ``provider``/``thinking``
    (supported context), ``effort``
    (``payload.reasoning.effort`` fallback ``reasoningEffort``), ``status``
    (response ``status``, turn ``outcome``, or agent-end derived
    stopReason), ``kind`` (request/response/terminal). Nothing else.

    Pinned terminal semantics (pi 0.87.1 ``agent-session.js`` + extension
    docs): ``turn_end`` carries the qualified ``outcome``
    (``completed``|``aborted``|``error`` mapped from the assistant
    ``stopReason``); ``agent_end`` carries ``messages`` only (a low-level
    run end — recovery/queued work may follow), so the observer derives
    ``aborted``/``error`` by scanning message ``stopReason`` and records
    neutral ``ended`` otherwise; ``agent_settled`` is final but notification-only
    (no success outcome) and is recorded as neutral ``settled``. A later
    ``settled`` must never overwrite a known aborted/error terminal.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Stage the actual frozen delivery member, not an independently maintained
    # source generator that can diverge from what the candidate executes.
    source = Path(__file__).resolve().parents[1] / 'config/pi-agent/extensions/m07-t05-witness.js'
    dest.write_bytes(source.read_bytes())
    try:
        dest.chmod(0o644)
    except OSError:
        pass
    return dest


# Backwards-compatible alias (old tests import this name).
def write_effective_witness_extension(dest: Path) -> Path:
    return stage_witness_extension(dest)


def parse_witness_readback(text: str, test_id: str, runtime_binding: dict | None = None) -> list:
    """Validate the ENTIRE private readback before any aggregation/filtering.

    Malformed, mixed-subject and unknown-field rows invalidate the readback;
    never manufacture a clean event bag by discarding inconvenient evidence.
    Empty/unavailable readback remains uncertain, not successful.
    """
    if not isinstance(text, str) or len(text.encode('utf-8')) > 65536:
        raise AdapterError("witness readback is malformed or exceeds bound")
    out = []
    for line in text.splitlines():
        if not line.strip():
            raise AdapterError("witness readback contains an empty row")
        try:
            doc = json.loads(line)
        except (ValueError, TypeError):
            raise AdapterError("witness readback contains malformed JSON") from None
        if not isinstance(doc, dict) or doc.get('test_id') != test_id:
            raise AdapterError("witness readback contains a wrong subject")
        kind = doc.get('kind')
        fields = {'request': {'test_id', 'kind', 'provider', 'thinking', 'model', 'effort'},
                  'response': {'test_id', 'kind', 'status'},
                  'terminal': {'test_id', 'kind', 'status'}}.get(kind)
        if runtime_binding is not None:
            runtime_fields = {'pid', 'agent_id', 'workspace_id', 'server_id'}
            if fields is not None:
                fields = fields | runtime_fields
            if any(doc.get(key) != runtime_binding.get(key) for key in runtime_fields):
                raise AdapterError('witness process/agent/workspace/server binding mismatch')
            if not isinstance(doc.get('pid'), int) or isinstance(doc['pid'], bool) or doc['pid'] <= 0:
                raise AdapterError('witness process identity malformed')
        if fields is None or set(doc) != fields or any(
                not isinstance(v, str) or not v or len(v) > 128
                for k, v in doc.items() if k != 'pid'):
            raise AdapterError("witness readback contains malformed typed facts")
        out.append(doc)
        if len(out) > 16:
            raise AdapterError("witness event bound exceeded")
    return out


def load_witness_events(path: Path, test_id: str) -> list:
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return []
    return parse_witness_readback(text, test_id)


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
    missing → UNKNOWN; response non-numeric or non-2xx → FAIL (malformed
    status cannot prove successful HTTP/provider execution); any aborted/
    error terminal → FAIL and a later settled notification never overwrites
    it; settled-only (or otherwise non-success terminal) → UNKNOWN;
    terminal missing → UNKNOWN (occurrence uncertain, no resend);
    contradictory efforts across request events → FAIL (forged witness).
    """
    # This bounded smoke permits exactly one provider exchange. Retry/mixed
    # exchanges have no supported per-request identifier in these pinned hooks;
    # do not correlate an arbitrary successful response with another request.
    if not isinstance(events, list) or any(not isinstance(e, dict) or e.get("test_id") != test_id
                                          or e.get("kind") not in WITNESS_KINDS for e in events):
        return {"gate": "FAIL", "observed": None, "reason": "mixed or malformed witness", "replay": False}
    reqs = [e for e in events if e.get("kind") == "request" and e.get("test_id") == test_id]
    resps = [e for e in events if e.get("kind") == "response" and e.get("test_id") == test_id]
    terms = [e for e in events if e.get("kind") == "terminal" and e.get("test_id") == test_id]
    if not reqs:
        return {"gate": "UNKNOWN", "observed": None,
                "reason": "no witness request for owned test; " + EFFECTIVE_UNOBSERVABLE_BOUNDARY,
                "replay": False}
    if len(reqs) != 1 or len(resps) > 1:
        return {"gate": "FAIL", "observed": None, "reason": "ambiguous provider exchange", "replay": False}
    if resps and (events.index(resps[0]) < events.index(reqs[0]) or
                  any(events.index(t) < events.index(resps[0]) for t in terms)):
        return {"gate": "FAIL", "observed": None, "reason": "out-of-order provider exchange", "replay": False}
    efforts = {e.get("effort") for e in reqs if e.get("effort")}
    models = {e.get("model") for e in reqs if e.get("model")}
    if len(models) > 1:
        return {"gate": "FAIL", "observed": None, "reason": "contradictory witness models", "replay": False}
    model = next(iter(models)) if models else None
    if model != expected_model:
        return {"gate": "FAIL", "observed": None,
                'reason': 'wrong witnessed model identity', 'replay': False}
    if len(efforts) > 1:
        return {"gate": "FAIL", "observed": None, "reason": "contradictory witness efforts", "replay": False}
    effort = next(iter(efforts)) if efforts else None
    if effort is None:
        return {"gate": "UNKNOWN", "observed": None,
                "reason": "witness effort missing; " + EFFECTIVE_UNOBSERVABLE_BOUNDARY, "replay": False}
    request = reqs[0]
    observed = {"provider": request.get('provider'), "model": model,
                "thinking": request.get('thinking'), "effort": effort}
    if request.get('provider') != FIXED_PROVIDER or request.get('thinking') != FIXED_THINKING:
        return {"gate": "FAIL", "observed": observed,
                "reason": "actual Pi context has wrong provider or effective thinking", "replay": False}
    if effort != FIXED_THINKING:
        return {"gate": "FAIL", "observed": observed,
                'reason': 'wrong or downgraded on-wire effort (requested max); '
                + EFFECTIVE_UNOBSERVABLE_BOUNDARY, "replay": False}
    if not resps:
        return {"gate": "UNKNOWN", "observed": observed,
                "reason": "witness response missing; occurrence uncertain, no resend", "replay": False}
    try:
        statuses = [int(str(e.get("status", "")).strip()) for e in resps if str(e.get("status", "")).strip().isdigit()]
    except (ValueError, TypeError):
        statuses = []
    if not statuses:
        # Non-numeric statuses (e.g. 'garbage'/'ok') are recorded but can
        # never prove successful HTTP/provider execution: FAIL, not UNKNOWN.
        return {"gate": "FAIL", "observed": observed,
                "reason": "witness response status is not valid typed HTTP success", "replay": False}
    if not any(200 <= s < 300 for s in statuses):
        return {"gate": "FAIL", "observed": observed,
                "reason": f"witness response not successful: {statuses}", "replay": False}
    if not terms:
        return {"gate": "UNKNOWN", "observed": observed,
                "reason": "witness terminal missing; occurrence uncertain, no resend", "replay": False}
    term_statuses = [t.get("status", "") for t in terms]
    if any(s in ("aborted", "error") for s in term_statuses):
        # Pinned agent-session.js maps assistant stopReason aborted/error to
        # the turn_end outcome; a known negative completion is terminal and
        # a later agent_settled notification (status 'settled', no outcome)
        # never overwrites it.
        return {"gate": "FAIL", "observed": observed,
                "reason": "witness terminal reports aborted/error completion", "replay": False}
    if "completed" not in term_statuses or "settled" not in term_statuses:
        # Settled-only or other non-success terminals prove settlement at
        # most, never successful inference: occurrence stays UNKNOWN.
        return {"gate": "UNKNOWN", "observed": observed,
                "reason": "witness terminal is not qualified success; occurrence uncertain, no resend",
                "replay": False}
    if events[-1].get("kind") != "terminal" or events[-1].get("status") != "settled":
        return {"gate": "FAIL", "observed": observed,
                "reason": "events continue after claimed final settlement", "replay": False}
    if any(s not in ("completed", "ended", "settled") for s in term_statuses):
        return {"gate": "FAIL", "observed": observed,
                "reason": "contradictory or unsupported terminal facts", "replay": False}
    return {"gate": "PASS", "observed": observed,
            "reason": "ordered request+response+qualified completion+settlement for owned test", "replay": False}


def classify_aggregated_witness(events: list, *, test_id: str) -> dict:
    """Classify witness events for the fixed profile (validator entrypoint)."""
    return aggregate_witness(events, test_id=test_id, expected_model=FIXED_MODEL)


# ---------------------------------------------------------------------------
# Integrated product path: daemon/Pi observers + guarded dispatch (validator calls these)
# ---------------------------------------------------------------------------

def private_daemon_config() -> dict:
    """Pinned PersistedConfigSchema/provider command replacement, no profile override."""
    return {'version': 1, 'pluginsEnabled': False,
            'daemon': {'listen': '127.0.0.1:6767', 'relay': {'enabled': False},
                       'mcp': {'enabled': False, 'injectIntoAgents': False},
                       'browserTools': {'enabled': False}},
            'agents': {'providers': {'pi': {
                'command': ['/home/paseo/.pi/agent/bin/m07-t05-pi-owned.py']}}}}


def stage_private_runtime(home: Path, *, uid: int, gid: int) -> None:
    """Exclusive private configuration and acquisition directories, not live HOME."""
    for relative in ('.paseo', '.m07-t05', '.m07-t05/processes'):
        directory = home / relative
        directory.mkdir(mode=0o700)
        os.chown(directory, uid, gid)
    config = home / '.paseo/config.json'
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(private_daemon_config(), stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.chown(config, uid, gid)


APPLIED_REFERENCE = '/home/paseo/.m07-t05/applied.json'
APPLIED_MANIFEST = '/home/paseo/.m07-t05/applied-manifest.json'
APPLIED_PROGRAM = '/home/paseo/.pi/agent/bin/m07-t05-applied.py'


def stage_applied_interval(home: Path, source: Path, companion: dict, *, nonce: str,
                           uid: int, gid: int) -> str:
    """Frozen public source content; no credential values or caller success fields.

    M07-T05A: when the derived effective ``models.json`` has already been
    staged host-side via :func:`apply_muse_max_merge` into
    ``home/.pi/agent/models.json`` (mode ``0600``), its bytes/mode join the
    kernel-backed interval rows so continuous binding covers both the
    frozen fragment and the actual effective merged configuration Pi reads.
    Homes without a staged effective file keep exact M07-T05 behavior.
    """
    code = (source / 'bin/m07-t05-applied.py').read_text()
    doc = {'schema_version': 1, 'root': '/home/paseo/.pi/agent', 'nonce': nonce,
           'files': {rel: {'content': (source / rel).read_text(), 'mode': companion['modes'][rel]}
                     for rel in companion['files']}}
    # Derived effective file (NOT a companion member): bind it when staged.
    eff_home = Path(home) / '.pi' / 'agent' / MUSE_MAX_EFFECTIVE_REL.as_posix()
    if eff_home.exists() and not eff_home.is_symlink() and eff_home.is_file():
        try:
            eff_raw = eff_home.read_bytes()
            eff_doc = json.loads(eff_raw.decode('utf-8'))
        except (OSError, ValueError) as exc:
            raise AdapterError(f"staged effective config unreadable: {exc}") from exc
        verify_muse_max_effective(eff_doc)
        import stat as _st
        eff_mode = eff_home.stat().st_mode & 0o777
        if eff_mode != 0o600:
            raise AdapterError(f"staged effective config mode is not 0600: {eff_mode:04o}")
        if MUSE_MAX_EFFECTIVE_REL.as_posix() in doc['files']:
            raise AdapterError("effective config collides with companion member")
        doc['files'][MUSE_MAX_EFFECTIVE_REL.as_posix()] = {
            'content': eff_raw.decode('utf-8'), 'mode': '0600'}
    file = home / '.m07-t05/applied-manifest.json'
    fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(doc, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
    os.chown(file, uid, gid)
    # Retained in the trusted host invocation, never recovered from candidate
    # writable inputs or the process under verification. Only public data.
    return {'code': code, 'manifest': doc, 'config': private_daemon_config()}


def start_applied_interval(exec_run, authority: dict, *, nonce: str | None = None):
    # Freeze instructions AND expectations into the actual child's -c input.
    # No applied file/import/__file__ supplies startup behavior. The start
    # wrapper also executes source-frozen code and checks its acquired child.
    code = authority['code'].split("if __name__ == '__main__':", 1)[0]
    digest = hashlib.sha256(json.dumps(authority['manifest'], sort_keys=True).encode()).hexdigest()
    server = code + '\nserve(' + repr(APPLIED_MANIFEST) + ', ' + repr(APPLIED_REFERENCE) + ', ' + repr(authority['manifest']) + ', ' + repr(authority['config']) + ', ' + repr(digest) + ')\n'
    # Bound exec argv size independently of public companion text/quoting.
    # Compression is only transport encoding, not a writable code artifact.
    import base64
    import zlib
    encoded = base64.b64encode(zlib.compress(server.encode())).decode('ascii')
    frozen_server = 'import base64, zlib; exec(zlib.decompress(base64.b64decode(' + repr(encoded) + ')))'
    launcher = code + '\nprocess = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-c", ' + repr(frozen_server) + '], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)\n' + (
        'if not select.select([process.stdout], [], [], 5)[0]:\n'
        '    process.terminate(); raise ValueError("interval startup unknown")\n'
        'line = process.stdout.readline()\n'
        'if not line: raise ValueError("interval startup unavailable")\n'
        'info = json.loads(line)\n'
        'assert info["pid"] == process.pid and info["start"] == stamp(process.pid)\n'
        'print(json.dumps(info))\n')
    result = exec_run(['python3', '-I', '-S', '-B', '-c', launcher])
    if result.returncode != 0:
        raise AdapterError('applied interval startup unavailable')
    try:
        info = json.loads(result.stdout)
        if (set(info) != {'schema_version', 'pid', 'start', 'nonce', 'socket', 'manifest_sha256'}
                or type(info.get('schema_version')) is not int or info['schema_version'] != 1
                or type(info.get('pid')) is not int or info['pid'] <= 0
                or not isinstance(info.get('start'), str) or not info['start'].isdigit()
                or info.get('socket') != APPLIED_REFERENCE + '.sock'
                or not isinstance(info.get('nonce'), str) or not info['nonce']
                or (nonce is not None and info['nonce'] != nonce)
                or not isinstance(info.get('manifest_sha256'), str)
                or info['manifest_sha256'] != hashlib.sha256(
                    json.dumps(authority['manifest'], sort_keys=True).encode()).hexdigest()):
            raise ValueError()
        return info
    except (ValueError, TypeError, AttributeError):
        raise AdapterError('applied interval startup identity unavailable') from None


def check_applied_interval(exec_run, authority: dict, expected: dict):
    # Execute SOURCE-frozen client code, not the now-applied helper. SO_PEERCRED
    # and /proc start identity bind the original independent interval observer.
    pinned_client = authority['code'].split("if __name__ == '__main__':", 1)[0] + '\n' + (
        'expected = ' + repr(expected) + '\n'
        'assert private(' + repr(APPLIED_REFERENCE) + ') == expected\n'
        'print(json.dumps(observe(' + repr(APPLIED_REFERENCE) + ')))\n')
    result = exec_run(['python3', '-I', '-S', '-B', '-c', pinned_client])
    if result.returncode != 0:
        raise AdapterError('applied interval changed or unavailable')
    try:
        info = json.loads(result.stdout)
        if info.get('bound') is not True or type(info.get('pid')) is not int:
            raise ValueError()
        return info
    except (ValueError, TypeError, AttributeError):
        raise AdapterError('applied interval readback unavailable') from None


def controlled_candidate_argv(argv: list) -> list:
    """Whitelist only nonsecret selectors. No image/CLI ambient env inheritance."""
    return ['env', '-i', 'HOME=/home/paseo', 'PASEO_HOME=/home/paseo/.paseo',
            'PATH=/usr/local/bin:/usr/bin:/bin', 'TMPDIR=/tmp', 'PYTHONDONTWRITEBYTECODE=1', *argv]


def dispatch_owned_runtime(exec_run, *, daemon: dict, pi: dict, test_id: str,
                           witness: str, applied_peer: dict | None = None) -> dict:
    """Use the fixed guard native shape, acquire IDs, inspect, then bounded send.

    Bridge refs live on the private mounted candidate HOME, usable even when
    dispatch/inspection times out. No title lookup or automatic resend.
    """
    config = {'test_id': test_id, 'daemon': daemon, 'pi': pi, 'cwd': '/tmp',
              'daemon_config': private_daemon_config(), 'applied_reference': APPLIED_REFERENCE,
              'applied_peer': applied_peer,
              'guard': '/home/paseo/.pi/agent/bin/run-llm-test.sh',
              'reference': '/home/paseo/.m07-t05/owned.json',
              'binding': '/home/paseo/.m07-t05/binding.json',
              'process_dir': '/home/paseo/.m07-t05/processes', 'witness': witness}
    # Data passes stdin-equivalent via quoted shell literal; no secret values.
    import shlex
    text = json.dumps(config, sort_keys=True)
    script = ('# guarded-dispatch (owned-runtime)\numask 077; set -C; printf %s ' + shlex.quote(text)
              + ' > /home/paseo/.m07-t05/launch.json; '
              + 'bash /home/paseo/.pi/agent/bin/run-llm-test.sh --candidate-owned '
              + '/home/paseo/.m07-t05/launch.json')
    proc = exec_run(['sh', '-ec', script], timeout=120)
    try:
        result = json.loads(proc.stdout or '')
    except (ValueError, AttributeError):
        raise AdapterBlocked('owned runtime occurrence unknown; retain candidate readback') from None
    if not isinstance(result, dict) or result.get('status') != 'PASS':
        raise AdapterBlocked('owned runtime occurrence unknown; retain candidate readback')
    if result.get('test_id') != test_id or result.get('daemon') != daemon or result.get('dispatch') != 'settled':
        raise AdapterError('owned runtime subject mismatch')
    return result


def _require_candidate_local_endpoint(endpoint: str) -> str:
    """Require a candidate-local daemon endpoint (loopback IP, never remote).

    The candidate daemon runs inside the disposable candidate namespace.
    Only IP-literal loopback (127.0.0.0/8, ::1), the name ``localhost``, or
    a wildcard bind (0.0.0.0/::) inside the candidate netns is accepted.
    Any other DNS name or address — including strings that merely START
    with ``127.`` but are not IP literals (e.g. ``127.attacker.invalid``,
    which DNS-resolves elsewhere) — fails closed. No DNS/network lookup is
    performed; non-literal names other than localhost are rejected. """
    import ipaddress as _ip
    host = endpoint.strip()
    # Strip scheme if present, then take host before ':' or '/'.
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].split(":", 1)[0].strip().lower().strip("[]")
    if not host:
        raise AdapterError("daemon endpoint host is missing")
    if host == "localhost":
        return endpoint
    try:
        addr = _ip.ip_address(host)
    except ValueError:
        raise AdapterError('daemon endpoint host is not a loopback IP literal') from None
    if not (addr.is_loopback or str(addr) in ("0.0.0.0", "::")):
        raise AdapterError('daemon endpoint is not candidate-local')
    return endpoint


def _require_candidate_local_pi_path(path: str) -> str:
    """Require a plausible candidate-local Pi executable path.

    This legacy predicate alone is NOT executable provenance: it rejects malformed
    or keyword-shaped pseudo-paths (``..`` escapes, non-absolute paths,
    names that merely contain ``pi`` such as ``/operator/providers/pi``
    without any binding to the observed daemon), but a well-formed path
    proves nothing by itself. Real binding comes from the bring-up Plus
    observation chain: the daemon is started inside the candidate from a
    controlled environment, ``command -v pi`` resolves through the
    candidate ``PATH``, ``pi --version`` matches the frozen candidate, and
    ``paseo agent inspect`` confirms provider/model/effective profile for
    the owned child. """
    if not path.startswith("/"):
        raise AdapterError(f"candidate Pi path is not absolute: {path!r}")
    parts = [p for p in path.split("/") if p]
    if not parts or ".." in parts or "." in parts:
        raise AdapterError(f"candidate Pi path escapes its root: {path!r}")
    low = path.lower()
    if "foreign" in low:
        raise AdapterError(f"candidate Pi path is not candidate-local: {path!r}")
    base = parts[-1].lower()
    if base not in ("pi", "pi.exe") and not base.startswith("pi-"):
        raise AdapterError(f"candidate Pi path is not a Pi executable: {path!r}")
    return path


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
        # applied across the namespace boundary). Production protection here
        # is exec scoping (docker exec into the candidate) plus the host-side
        # validate_candidate_home disposable-root binding; the string
        # "/home/paseo/.paseo" is the candidate's own home inside its mount
        # namespace, not the host production HOME.
        raise AdapterError("daemon home is not the candidate home")
    endpoint = doc.get("listen") or doc.get("endpoint") or doc.get("configuredListen")
    if not isinstance(endpoint, str) or not endpoint:
        raise AdapterError("daemon endpoint is missing")
    _require_candidate_local_endpoint(endpoint)
    version = doc.get("daemonVersion") or doc.get("version")
    if version is None or str(version) != str(expected_version):
        raise AdapterError('daemon version mismatch vs frozen candidate')
    pid = doc.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise AdapterError("daemon pid is missing or invalid; process identity unverified")
    local_state = doc.get("localDaemon")
    if local_state != "running":
        raise AdapterError('candidate daemon is not running')
    connected = doc.get("connectedDaemon")
    if connected != "reachable":
        raise AdapterError('candidate daemon is not reachable')
    worker_pid = doc.get("workerPid")
    if not isinstance(worker_pid, int) or isinstance(worker_pid, bool) or worker_pid <= 0:
        raise AdapterError("daemon worker process identity is missing")
    if not isinstance(doc.get("serverId"), str) or not doc["serverId"]:
        raise AdapterError("connected daemon server identity is missing")
    if not isinstance(doc.get("daemonNode"), str) or not doc["daemonNode"].startswith("/"):
        raise AdapterError("daemon Node executable identity is missing")
    providers = doc.get('providers')
    if not isinstance(providers, (list, dict)) or not providers:
        raise AdapterError('daemon provider details are unavailable')
    pi_available = ('pi' in providers if isinstance(providers, dict) else
                    any(p == 'pi' or isinstance(p, dict) and p.get('provider') == 'pi'
                        and p.get('available') is True for p in providers))
    if not pi_available:
        raise AdapterError('connected daemon does not advertise the selected Pi provider')
    return {"home": home, "endpoint": endpoint, "pid": pid, "version": str(version),
            "worker_pid": worker_pid, "server_id": doc["serverId"], "node": doc["daemonNode"]}


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
    if path != '/usr/local/bin/pi':
        raise AdapterError('Pi resolution does not match the controlled image executable')
    ver = exec_run(["pi", "--version"], timeout=30)
    if getattr(ver, "returncode", 1) != 0:
        raise AdapterBlocked("candidate Pi version unavailable")
    out = (getattr(ver, "stdout", "") or "").strip().splitlines()
    out = out[-1].strip() if out else ""
    if out != str(expected_version):
        raise AdapterError('Pi version mismatch vs frozen candidate')
    hashed = exec_run(['sha256sum', path], timeout=30)
    digest = (getattr(hashed, 'stdout', '') or '').split()
    import re
    if getattr(hashed, 'returncode', 1) != 0 or not digest or not re.fullmatch('[0-9a-f]{64}', digest[0]):
        raise AdapterBlocked('candidate Pi executable bytes unavailable')
    return {"path": path, "version": out, 'sha256': 'sha256:' + digest[0]}


def ensure_candidate_daemon(exec_run, *, candidate_home: str, expected_version: str,
                            env_loader: str | None = None,
                            meta_pointer: str | None = None) -> dict:
    """Bring up the candidate-local daemon (idempotent) and observe it.

    Source-qualified bring-up (pinned Paseo 0.9.2
    ``dist/commands/daemon/start.js``): ``paseo daemon start --home
    <candidate-home>`` starts the local daemon from persistent
    configuration, returning ``started`` or ``already_running`` with
    ``pid``/``listen``. When ``env_loader``/``meta_pointer`` are supplied,
    the start runs under the staged candidate-env loader, so the daemon
    process inherits ``META_API_KEY`` (read in-candidate from the private
    pointer file) plus the controlled container environment — the
    supported route by which the actual daemon-selected Pi subprocess
    receives Meta auth (pinned server ``createExternalProcessEnv(daemon
    env, launch.env)``; ``META_API_KEY`` is not a runtime-control key).
    The raw value never travels argv/``--env``/evidence. Afterwards the
    daemon is observed via :func:`observe_daemon_status` (same strict
    binding); a start that leaves the daemon unobservable fails closed.
    """
    start_argv = ["paseo", "daemon", "start", "--json", "--home", candidate_home]
    if env_loader and meta_pointer:
        start_argv = ["bash", "-c",
                      f"# daemon-bringup\nMETA_API_KEY_FILE={meta_pointer} "
                      f"bash {env_loader} paseo daemon start --json --home {candidate_home}"]
    proc = exec_run(start_argv, timeout=120)
    if getattr(proc, "returncode", 1) != 0:
        raise AdapterBlocked("candidate daemon startup failed; auth inheritance unverified")
    try:
        started = json.loads(getattr(proc, "stdout", "") or "")
    except (ValueError, TypeError):
        raise AdapterError("candidate daemon startup result malformed") from None
    if not isinstance(started, dict) or started.get("action") != "started" or started.get("home") != candidate_home:
        raise AdapterError("candidate daemon was not newly started under the private loader")
    observed = observe_daemon_status(exec_run, candidate_home=candidate_home,
                                    expected_version=expected_version)
    if started.get("pid") != observed["pid"] or started.get("listen") != observed["endpoint"]:
        raise AdapterError("candidate daemon changed during startup")
    return observed


def preflight_candidate_profile(exec_run, *, candidate_home: str) -> dict:
    """Non-inference catalog of the selected candidate daemon, before prompt.

    Paseo 0.9.2 provider/models.js exposes id + thinkingOptionIds from Pi's
    get_available_models RPC. agent.js resolvePiThinkingConfig excludes a
    null max mapping, including the pinned Contributor catalog. No override,
    fallback or prompt is attempted when that required option is absent.
    This is a necessary capability gate, not proof of effective inference.
    """
    proc = exec_run(["paseo", "provider", "models", "pi", "--thinking", "--json",
                     "--home", candidate_home], timeout=30)
    if getattr(proc, "returncode", 1) != 0:
        raise AdapterBlocked("candidate model catalog unavailable before dispatch")
    try:
        models = json.loads(getattr(proc, "stdout", "") or "")
    except (ValueError, TypeError):
        raise AdapterError("candidate model catalog malformed") from None
    if not isinstance(models, list) or any(not isinstance(m, dict) for m in models):
        raise AdapterError("candidate model catalog malformed")
    matches = [m for m in models if m.get("id") == f"{FIXED_PROVIDER}/{FIXED_MODEL}"]
    if len(matches) != 1:
        raise AdapterBlocked("fixed candidate model is absent or ambiguous before dispatch")
    options = matches[0].get("thinkingOptionIds")
    if not isinstance(options, list) or any(not isinstance(o, str) for o in options):
        raise AdapterError("candidate thinking options malformed")
    if FIXED_THINKING not in options:
        raise AdapterBlocked("fixed max is unavailable; guarded inference dispatch prohibited")
    return {"model": f"{FIXED_PROVIDER}/{FIXED_MODEL}", "thinking": FIXED_THINKING,
            "source": "candidate-daemon provider models (non-inference)"}


def inspect_owned_agent(exec_run, *, candidate_home: str, expected_title: str,
                        expected_model: str = FIXED_MODEL,
                        expected_thinking: str = FIXED_THINKING) -> dict:
    """Legacy helper-level CLI inspection; NOT product ownership/provenance proof.

    Product execution uses actual supported creation IDs and snapshot workspaceId
    through the private bridge, never title/idle/usage inference.

    Inspect the dispatched child via supported agent commands.

    Source-qualified inspection (pinned Paseo 0.9.2): ``paseo agent ls
    --json --home`` lists ``{id, name(title), provider, thinking(effective),
    status, ...}``; ``paseo agent inspect <id> --json --home`` returns the
    full snapshot including ``Model`` (runtime model), ``Thinking``
    (``effectiveThinkingOptionId`` — the EFFECTIVE profile observation),
    ``Status``, ``Cwd``, ``ParentAgentId`` and ``LastUsage`` token/cost
    proof. The owned child is the exactly-one agent whose title equals the
    dispatched correlation title; zero or multiple matches fail closed
    (missing/ambiguous child is never borrowed). Model must contain the
    fixed model, effective thinking must equal ``max`` (a clamp/downgrade
    observed here fails even when the witness agreed), and usage must show
    consumed tokens (a smoke that consumed nothing proves no inference).
    """
    proc = exec_run(["paseo", "agent", "ls", "--json", "--home", candidate_home],
                    timeout=30)
    if getattr(proc, "returncode", 1) != 0:
        raise AdapterBlocked("candidate agent list unavailable")
    try:
        agents = json.loads((getattr(proc, "stdout", "") or "").strip())
    except (json.JSONDecodeError, ValueError) as exc:
        raise AdapterError("candidate agent list malformed") from exc
    if isinstance(agents, dict):
        agents = agents.get("agents") or agents.get("data") or []
    if not isinstance(agents, list):
        raise AdapterError("candidate agent list malformed")
    owned = [a for a in agents
             if isinstance(a, dict) and (a.get("name") or a.get("title")) == expected_title]
    if len(owned) != 1:
        raise AdapterError(
            f"owned dispatched child not uniquely observable: {len(owned)} matches")
    agent_id = owned[0].get("id")
    if not agent_id:
        raise AdapterError("owned dispatched child lacks an identity")
    iproc = exec_run(["paseo", "agent", "inspect", str(agent_id),
                      "--json", "--home", candidate_home], timeout=30)
    if getattr(iproc, "returncode", 1) != 0:
        raise AdapterBlocked("owned dispatched child inspection unavailable")
    try:
        doc = json.loads((getattr(iproc, "stdout", "") or "").strip())
    except (json.JSONDecodeError, ValueError) as exc:
        raise AdapterError("owned child inspection malformed") from exc
    if isinstance(doc, list):
        doc = doc[0] if doc else {}
    if not isinstance(doc, dict):
        raise AdapterError("owned child inspection malformed")
    if str(doc.get("Id") or doc.get("id") or "") != str(agent_id):
        raise AdapterError("owned child identity mismatch on inspection")
    if str(doc.get("Provider") or doc.get("provider") or "") != "pi":
        raise AdapterError("owned child is not a Pi agent")
    model = str(doc.get("Model") or doc.get("model") or "")
    if model != f"{FIXED_PROVIDER}/{expected_model}":
        raise AdapterError(f"owned child model mismatch: {model!r}")
    thinking = str(doc.get("Thinking") or doc.get("thinking") or "")
    if thinking != expected_thinking:
        raise AdapterError(f"owned child effective thinking is not max: {thinking!r}")
    status = str(doc.get("Status") or doc.get("status") or "")
    if status.lower() not in ("completed", "idle", "done", "success"):
        raise AdapterError(f"owned child status is not successful: {status!r}")
    usage = doc.get("LastUsage") or doc.get("lastUsage") or {}
    try:
        consumed = int(usage.get("InputTokens", 0)) + int(usage.get("OutputTokens", 0))
    except (ValueError, TypeError, AttributeError):
        consumed = 0
    if consumed <= 0:
        raise AdapterError("owned child consumed no tokens; inference unproven")
    return {"id": str(agent_id), "provider": "pi", "model": model,
            "thinking": thinking, "status": status, "tokens": consumed}


def dispatch_guarded_test(*, guard_file: Path, agent_root: Path, prompt: str, cwd: str,
                          bindir: Path, test_id: str, witness_file: Path,
                          meta_secret_file: Path | None = None, timeout: int = 120) -> dict:
    """Run the canonical guard PROMPT form with per-test witness correlation.

    Copies the exact guard bytes into a disposable agent root, executes the
    PROMPT form (``guard PROMPT [CWD]`` — the future-authorized smoke shape,
    NOT ``--native-create-agent-args`` export) with ``PATH`` isolated to the
    test-owned ``bindir`` (fake ``paseo`` records dispatch + witness, never
    real inference), ``M07_T05_TEST_ID``/``M07_T05_WITNESS_FILE`` correlation,
    and ``META_API_KEY_FILE`` pointer (never the secret value). The staged
    :func:`stage_candidate_env` loader reads the pointer and exports
    ``META_API_KEY`` for the guard/Pi process — the same loader bytes the
    validator stages into the candidate. Snapshots dispatch + witness events
    BEFORE temp cleanup. Timeout → UNKNOWN snapshot with ``replay: False``
    (never resend blindly).

    Local helper-level dispatch for direct unit coverage; the validator's
    candidate path performs the equivalent loader→guard sequence via
    ``docker exec`` into the disposable candidate (see the Tower validator).
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
        loader = stage_candidate_env(agent / "bin" / "m07-t05-candidate-env.sh")
        # Local dispatch-argv capture: the shell fake records its argv here
        # (no Pi/daemon exists locally, so no witness events occur; dispatch
        # means the guard executed `paseo run` with the transmitted contract).
        argv_marker = tmp_p / "dispatch-argv.txt"
        env = {
            "PATH": str(bindir),
            "M07_T05_TEST_ID": test_id,
            "M07_T05_WITNESS_FILE": str(witness_file),
            "DISPATCH_MARKER": str(argv_marker),
        }
        if meta_secret_file is not None:
            # Pointer only; the staged loader reads the value inside the
            # (here local-simulated) candidate boundary and exports it.
            env[MUSE_SECRET_POINTER_ENV] = str(meta_secret_file)
        try:
            proc = subprocess.run(["bash", str(loader), str(launcher), prompt, cwd], env=env, text=True,
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
        try:
            recorded = argv_marker.read_text(encoding="utf-8").splitlines()
        except OSError:
            recorded = []
        # Local dispatch = guard exit 0 AND the shell fake recorded a `run`
        # invocation (it parses --env and enforces loader auth itself).
        dispatched = proc.returncode == 0 and bool(recorded) and recorded[0] == "run"
        return {
            "returncode": proc.returncode,
            "timeout": False,
            'stderr': 'guard dispatch failed' if proc.returncode else '',
            'stdout': '',
            "dispatched": dispatched,
            "dispatch_argv": recorded,
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
