#!/usr/bin/env python3
"""Authenticated non-inference Codex-LB checks (M07-T05).

Replaces the former direct /responses inference smoke. Only supported
authenticated catalog/metadata/auth/health readback plus structural
validation and deterministic protocol fixtures. Never sends a prompt,
never calls an inference endpoint, never selects another model as a
real test. Ordinary/catalog/fixture model IDs remain legitimate data.

Secret handling: credential values are read in-memory from a dedicated
private file, never placed on argv, never logged, never persisted.
Errors are sanitized to bounded messages without echoing tokens,
headers, stderr tails or response bodies.
"""
from __future__ import annotations

import json
import os
import re
import stat
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA_VERSION = 1

# Inference endpoints that must never be requested by this module.
INFERENCE_SUBSTRINGS = (
    "/responses",
    "/chat/completions",
    "/completions",
    "/embeddings",
    "/images/generations",
)

REQUIRED_BASE_SUFFIX = "/v1"
DEFAULT_TIMEOUT = 10

MODEL_ID_RE = re.compile(r"^[^\s\x00-\x1f\x7f]+$")


class CodexError(RuntimeError):
    """Fail-closed validation error (maps to FAIL)."""


class CodexBlocked(RuntimeError):
    """Unavailable/missing input (maps to BLOCKED)."""


class CodexAuthDenied(CodexError):
    """Authentication rejected (401/403)."""


def _fail(msg: str) -> CodexError:
    return CodexError(msg)


def validate_base_url(value) -> str:
    if not isinstance(value, str) or not value:
        raise CodexError("Codex-LB base URL must be a non-empty string")
    v = value.strip()
    if v != value or any(ch.isspace() for ch in value):
        raise CodexError("Codex-LB base URL must not contain whitespace")
    try:
        parsed = urlsplit(v)
    except ValueError as exc:
        raise CodexError("Codex-LB base URL is not a valid URL") from exc
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise CodexError("Codex-LB base URL must be http(s) with a host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise CodexError("Codex-LB base URL must not carry credentials/query/fragment")
    norm = v.rstrip("/")
    if not norm.endswith(REQUIRED_BASE_SUFFIX):
        raise CodexError("Codex-LB base URL must end in /v1")
    # Reject inference-shaped base URLs on the NORMALIZED form (must be a
    # catalog root, not an endpoint, encoded or not).
    low = _normalized_url(norm).lower()
    for sub in INFERENCE_SUBSTRINGS:
        if sub in low:
            raise CodexError("Codex-LB base URL must not point at an inference endpoint")
    return norm


def validate_model_id(value) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise CodexError("Codex-LB model must be one non-empty model id")
    if any(ch.isspace() for ch in value):
        raise CodexError("Codex-LB model must be one non-empty model id")
    if len(value) > 256:
        raise CodexError("Codex-LB model id is too long")
    return value


def _normalized_url(url: str) -> str:
    """Normalize a URL for safety checks: percent-decode, case-fold scheme/host.

    Percent-encoded inference destinations (e.g. ``/v1/%72esponses`` for
    ``/v1/responses``) must be rejected BEFORE any network effect, so every
    safety predicate below runs on the decoded form. Decoding is applied
    repeatedly (bounded) to defeat double-encoding. """
    try:
        from urllib.parse import unquote
    except ImportError:  # pragma: no cover
        return url
    norm = url
    for _ in range(3):
        nxt = unquote(norm)
        if nxt == norm:
            break
        norm = nxt
    return norm


def assert_no_inference_url(url: str) -> None:
    low = _normalized_url(url).lower()
    for sub in INFERENCE_SUBSTRINGS:
        if sub in low:
            raise CodexError(f"inference endpoint is forbidden for non-inference checks: {sub}")


def sanitize_message(msg: str, *, limit: int = 300) -> str:
    """Bounded secret-safe message: single line, truncated, no token shapes.

    Never echoes arbitrary dependency tails: labelled bearer/key shapes are
    redacted AND any unlabelled opaque token-looking value (>=20 chars of
    token alphabet) is replaced, so an echoed synthetic secret cannot be
    retained in ValidationError/Classification reasons.
    """
    if not isinstance(msg, str):
        msg = str(msg)
    # Strip bearer tokens and key-like assignments if a dependency echoed them.
    redacted = re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-~+/=]+", "Bearer [redacted]", msg)
    redacted = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s\"']+)", r"\1[redacted]", redacted)
    redacted = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[redacted]", redacted)
    redacted = re.sub(r"gh[pousr]_[A-Za-z0-9]{8,}", "gh_[redacted]", redacted)
    redacted = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "[redacted-key]", redacted)
    # Unlabelled opaque echoes: any 20+ char token-alphabet run is not safe
    # to retain (Main probe: subprocess echoes synthetic token verbatim).
    # Preserve common short words by requiring length >= 20.
    redacted = re.sub(r"[A-Za-z0-9._\-~+/=]{20,}", "[redacted-value]", redacted)
    single = " ".join(redacted.split())
    if len(single) > limit:
        single = single[:limit] + "…"
    return single or "check failed"


def read_dedicated_secret(secret_path) -> str:
    """Read the dedicated operator-controlled credential file (in-memory only).

    Validates: regular file, not a symlink, private mode (0600/0400),
    single non-empty line, optional CODEX_LB_API_KEY assignment prefix. Never logs
    the value. Missing file -> Blocked; malformed/insecure -> Error.
    """
    p = Path(secret_path)
    # Resolve without following beyond the file itself for symlink check.
    try:
        if p.is_symlink():
            raise CodexError("dedicated Codex-LB credential must not be a symlink")
        st = p.stat()
    except FileNotFoundError as exc:
        raise CodexBlocked("dedicated Codex-LB credential file unavailable") from exc
    except OSError as exc:
        raise CodexBlocked(f"dedicated Codex-LB credential unavailable: {sanitize_message(exc)}") from exc
    import stat as statmod

    if not statmod.S_ISREG(st.st_mode):
        raise CodexError("dedicated Codex-LB credential must be a regular file")
    mode = statmod.S_IMODE(st.st_mode)
    # Private: owner-only (0600/0400); group/other must have no permissions.
    if mode & 0o077:
        raise CodexError(f"dedicated Codex-LB credential must be private (0600/0400), got {mode:04o}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise CodexBlocked(f"dedicated Codex-LB credential unreadable: {sanitize_message(exc)}") from exc
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if len(lines) != 1:
        raise CodexError("dedicated Codex-LB credential must hold exactly one entry")
    line = lines[0]
    if "=" in line:
        name, _, value = line.partition("=")
        if name != "CODEX_LB_API_KEY":
            raise CodexError("dedicated Codex-LB credential entry must be CODEX_LB_API_KEY or a bare key")
    else:
        value = line
    value = value.strip()
    if not value or any(ch.isspace() for ch in value) or "\x00" in value:
        raise CodexError("dedicated Codex-LB credential value is invalid")
    if len(value) > 4096:
        raise CodexError("dedicated Codex-LB credential value is too long")
    return value


def _origin_tuple(url: str) -> tuple:
    """Normalized origin: (scheme, hostname, port) with default ports resolved.

    Source-qualified redirect boundary: only the identical origin may be
    followed. A cross-port localhost redirect is a different origin and
    fails closed (no credential forwarding, no request). """
    parsed = urlsplit(url)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        raise CodexError("Codex-LB redirect target is not a valid URL")
    if port is None:
        port = 443 if scheme == "https" else 80 if scheme == "http" else None
    return (scheme, host, port)


def assert_safe_redirect(from_url: str, to_url: str) -> None:
    """Fail closed on unsafe redirect targets.

    Redirects must stay http(s), must not point at an inference endpoint,
    and must not carry credentials/query/fragment. Auth is never forwarded
    cross-host by the transport below; any redirect to a different host
    drops Authorization. Inference-shaped or credentialed targets fail.
    """
    if not isinstance(to_url, str) or not to_url:
        raise CodexError("Codex-LB redirect target is invalid")
    try:
        parsed = urlsplit(to_url)
    except ValueError as exc:
        raise CodexError("Codex-LB redirect target is not a valid URL") from exc
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise CodexError("Codex-LB redirect target must be http(s) with a host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise CodexError("Codex-LB redirect target must not carry credentials/query/fragment")
    assert_no_inference_url(to_url)
    # Supported destinations only: the redirect target path must be a
    # non-inference API path under the same origin (catalog/health style),
    # matched on the NORMALIZED path. Anything else fails closed.
    try:
        target_path = _normalized_url(to_url).split("?", 1)[0].split("#", 1)[0]
        target_path = urlsplit(target_path).path or "/"
    except ValueError as exc:
        raise CodexError("Codex-LB redirect target is not a valid URL") from exc
    # Only the two implemented readbacks are admitted. A blacklist cannot
    # classify an arbitrary /v1/* route as non-inference.
    if target_path not in ("/v1/models", "/health"):
        raise CodexError("Codex-LB redirect target is not a supported non-inference destination")
    if target_path != urlsplit(_normalized_url(from_url)).path:
        raise CodexError("Codex-LB redirect changes the required check destination")
    # Same-origin only: scheme/host/port must match the request origin.
    # A cross-port (or scheme/host) redirect is a foreign origin and fails
    # closed before any network effect with credentials.
    try:
        from_origin = _origin_tuple(from_url)
        to_origin = _origin_tuple(to_url)
    except CodexError:
        raise
    except ValueError as exc:
        raise CodexError("Codex-LB redirect target is not a valid URL") from exc
    if from_origin != to_origin:
        raise CodexError(
            "Codex-LB redirect leaves the request origin; "
            "cross-origin redirects are rejected without credential forwarding"
        )


class _NoAuthForwardRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that enforces same-origin and never forwards auth off-origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Validate the redirect target before following (same-origin,
        # non-inference, no credentials/query/fragment). Cross-origin
        # (including cross-port) raises here: no request is issued and no
        # Authorization is forwarded.
        assert_safe_redirect(req.full_url, newurl)
        nxt = super().redirect_request(req, fp, code, msg, headers, newurl)
        if nxt is None:
            return None
        # Defense in depth: strip auth headers on ANY origin change
        # (scheme/host/port), even if the pre-check above is bypassed.
        try:
            orig = _origin_tuple(req.full_url)
            new = _origin_tuple(nxt.full_url)
        except ValueError:
            raise CodexError("Codex-LB redirect target is not a valid URL")
        if orig != new:
            for h in ("Authorization", "Proxy-Authorization", "Cookie"):
                try:
                    if nxt.has_header(h):
                        nxt.remove_header(h)
                except Exception:
                    pass
        # Re-assert the final URL is not an inference endpoint.
        assert_no_inference_url(nxt.full_url)
        return nxt


def _http_get(url: str, headers: dict, timeout: int):
    """Default transport: urllib GET with bounded timeout, no secret on argv.

    Uses a redirect-validating opener: inference-shaped, credentialed or
    off-scheme redirect targets fail closed; Authorization is never
    forwarded to a different host. Bodies are bounded (256KiB success,
    64KiB error) and never persisted; only status+body bytes are returned
    for structural parsing by the caller.
    """
    assert_no_inference_url(url)
    if urlsplit(url).path not in ("/v1/models", "/health"):
        raise CodexError("unsupported non-inference destination")
    opener = urllib.request.build_opener(_NoAuthForwardRedirectHandler)
    req = urllib.request.Request(url, headers=dict(headers), method="GET")
    try:
        with opener.open(req, timeout=timeout) as resp:
            # Final URL after redirects must still be a safe non-inference target.
            try:
                final_url = resp.geturl()
            except Exception:
                final_url = url
            assert_no_inference_url(final_url)
            assert_safe_redirect(url, final_url) if final_url != url else None
            status = getattr(resp, "status", 200) or 200
            body = resp.read(256 * 1024)
            return status, body
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(64 * 1024)
        except Exception:
            body = b""
        return exc.code, body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise CodexBlocked(f"Codex-LB endpoint unreachable: {sanitize_message(exc)}") from exc


def parse_catalog_body(body: bytes) -> list:
    """Structural validation of GET /v1/models payload. Returns sorted ids.

    Never persists the raw body; only ids/count are retained by callers.
    """
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CodexError("Codex-LB catalog is not valid UTF-8 JSON") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CodexError("Codex-LB catalog is not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise CodexError("Codex-LB catalog is not an OpenAI-compatible list")
    data = payload["data"]
    if not data:
        raise CodexError("Codex-LB catalog contains no models")
    if len(data) > 10000:
        raise CodexError("Codex-LB catalog is unexpectedly large")
    ids = set()
    for item in data:
        if not isinstance(item, dict):
            raise CodexError("Codex-LB catalog entry is invalid")
        mid = item.get("id")
        if not isinstance(mid, str) or not mid or mid.strip() != mid:
            raise CodexError("Codex-LB catalog contains an invalid model id")
        if any(ch.isspace() for ch in mid) or len(mid) > 256:
            raise CodexError("Codex-LB catalog contains an invalid model id")
        ids.add(mid)
    return sorted(ids)


def parse_health_body(body: bytes) -> dict:
    """Structural validation of GET /health payload. Returns sanitized fields."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexError("Codex-LB health is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise CodexError("Codex-LB health is not an object")
    status = payload.get("status")
    if not isinstance(status, str) or not status:
        raise CodexError("Codex-LB health status is missing")
    # Retain only the bounded status string, not the full body.
    return {"status": status[:64]}


def check_catalog(base_url: str, secret_value: str, *, timeout: int = DEFAULT_TIMEOUT, http_get=None) -> dict:
    """GET {base}/models with Bearer auth. Classifies auth/structural/unreachable."""
    base = validate_base_url(base_url)
    if not secret_value or any(ch.isspace() for ch in secret_value):
        raise CodexError("Codex-LB credential value is invalid")
    url = base.rstrip("/") + "/models"
    assert_no_inference_url(url)
    getter = http_get or _http_get
    try:
        status, body = getter(url, {"Authorization": "Bearer " + secret_value, "Accept": "application/json"}, timeout)
    except CodexBlocked:
        raise
    except CodexError:
        raise
    except Exception as exc:
        raise CodexBlocked(f"Codex-LB catalog unreachable: {sanitize_message(exc)}") from exc
    if status in (401, 403):
        raise CodexAuthDenied("Codex-LB catalog authentication rejected")
    if status == 404:
        raise CodexError("Codex-LB catalog endpoint not found")
    if status != 200:
        raise CodexError(f"Codex-LB catalog unexpected status {status}")
    ids = parse_catalog_body(body)
    return {"status": "PASS", "count": len(ids), "models": ids[:256]}


def check_health(base_url: str, *, timeout: int = DEFAULT_TIMEOUT, http_get=None) -> dict:
    """GET {root}/health without auth. Structural check only."""
    base = validate_base_url(base_url)
    root = base[: -len("/v1")].rstrip("/") or base
    url = root + "/health"
    assert_no_inference_url(url)
    getter = http_get or _http_get
    try:
        status, body = getter(url, {"Accept": "application/json"}, timeout)
    except CodexBlocked:
        raise
    except CodexError:
        raise
    except Exception as exc:
        raise CodexBlocked(f"Codex-LB health unreachable: {sanitize_message(exc)}") from exc
    if status in (401, 403):
        raise CodexAuthDenied("Codex-LB health authentication rejected")
    if status != 200:
        raise CodexError(f"Codex-LB health unexpected status {status}")
    parsed = parse_health_body(body)
    if parsed.get("status", "").lower() not in ("ok", "healthy", "ready", "up"):
        raise CodexError("Codex-LB health status is not ok")
    return {"status": "PASS", "health": parsed["status"]}


def run_all(*, base_url, secret_file=None, secret_value=None, timeout: int = DEFAULT_TIMEOUT, http_get=None) -> dict:
    """Run required non-inference checks. Returns per-check outcomes.

    If secret_file/secret_value is absent, catalog/auth are SKIP (missing
    credential leaves real validation unsatisfied; never silently PASS).
    Health is attempted without auth. Inference is never attempted.
    """
    outcomes: dict = {}
    # Health first (no credential needed).
    try:
        res = check_health(base_url, timeout=timeout, http_get=http_get)
        outcomes["codex_health"] = "PASS"
        outcomes["codex_health_detail"] = res
    except CodexBlocked as exc:
        outcomes["codex_health"] = "BLOCKED"
        outcomes["codex_health_reason"] = sanitize_message(exc)
    except CodexError as exc:
        outcomes["codex_health"] = "FAIL"
        outcomes["codex_health_reason"] = sanitize_message(exc)

    # Catalog/auth require a dedicated credential.
    cred = secret_value
    if cred is None and secret_file is not None:
        try:
            cred = read_dedicated_secret(secret_file)
        except CodexBlocked as exc:
            outcomes["codex_catalog"] = "BLOCKED"
            outcomes["codex_catalog_reason"] = sanitize_message(exc)
            outcomes["codex_auth"] = "BLOCKED"
            outcomes["codex_auth_reason"] = sanitize_message(exc)
            outcomes["codex_no_inference"] = "PASS"
            return outcomes
        except CodexError as exc:
            outcomes["codex_catalog"] = "FAIL"
            outcomes["codex_catalog_reason"] = sanitize_message(exc)
            outcomes["codex_auth"] = "FAIL"
            outcomes["codex_auth_reason"] = sanitize_message(exc)
            outcomes["codex_no_inference"] = "PASS"
            return outcomes
    if cred is None:
        outcomes["codex_catalog"] = "SKIP"
        outcomes["codex_catalog_reason"] = "dedicated credential not supplied; real gate unsatisfied"
        outcomes["codex_auth"] = "SKIP"
        outcomes["codex_auth_reason"] = "dedicated credential not supplied; real gate unsatisfied"
        outcomes["codex_no_inference"] = "PASS"
        return outcomes
    try:
        res = check_catalog(base_url, cred, timeout=timeout, http_get=http_get)
        outcomes["codex_catalog"] = "PASS"
        outcomes["codex_catalog_detail"] = {"count": res["count"]}
        # Retain ids only as non-secret catalog data when small; never bodies.
        if res["count"] <= 64:
            outcomes["codex_catalog_detail"]["models"] = res["models"]
        outcomes["codex_auth"] = "PASS"
    except CodexBlocked as exc:
        outcomes["codex_catalog"] = "BLOCKED"
        outcomes["codex_catalog_reason"] = sanitize_message(exc)
        outcomes["codex_auth"] = "BLOCKED"
        outcomes["codex_auth_reason"] = sanitize_message(exc)
    except CodexAuthDenied as exc:
        outcomes["codex_catalog"] = "FAIL"
        outcomes["codex_catalog_reason"] = sanitize_message(exc)
        outcomes["codex_auth"] = "FAIL"
        outcomes["codex_auth_reason"] = sanitize_message(exc)
    except CodexError as exc:
        outcomes["codex_catalog"] = "FAIL"
        outcomes["codex_catalog_reason"] = sanitize_message(exc)
        # Structural failure implies auth shape could not be proven.
        outcomes["codex_auth"] = "FAIL"
        outcomes["codex_auth_reason"] = sanitize_message(exc)
    finally:
        # Best-effort: drop the in-memory credential reference.
        cred = None
    outcomes["codex_no_inference"] = "PASS"
    return outcomes
