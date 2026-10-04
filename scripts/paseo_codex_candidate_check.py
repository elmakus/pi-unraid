#!/usr/bin/env python3
"""Candidate-local Codex-LB non-inference check (M07-T05, ONE shared path).

This is the exact program the Tower validator stages into the disposable
candidate and executes via ``docker exec`` (``python3 <staged>/... --mode
catalog|health``). It shares ALL validation/parsing/transport with
``scripts/paseo_codex_noninference.py`` via direct import (same directory),
so there is exactly one executable/parseable implementation — no inline
``python3 -c`` duplicates, no marker-to-returncode mocks.

Secret handling: the dedicated credential file is read in-memory via the
shared strict reader; the value never appears on argv, in stdout/stderr,
or in persisted evidence. Only a fixed JSON summary (mode/status/count or
health, no bodies/secrets) is printed.

Exit codes (validator contract):
  0  pass (structural check succeeded)
  20 unavailable/transport (BLOCKED)
  21 auth denied 401/403 (FAIL)
  22 missing credential inside candidate (BLOCKED)
  23 protocol/shape/validation failure (FAIL)

Redirect safety (shared transport): the opener validates every redirect
target BEFORE following (allowed http(s) origin/scheme/port, no inference
substring, no credentials/query/fragment) and never forwards Authorization
cross-host. Inference endpoints are never requested.

No real provider auth is performed in M07-T05 tests: the fake candidate
exec runs THIS file locally with a synthetic secret file and a local
``http.server`` fixture (127.0.0.1) or injected failure. A real test
inference can NEVER occur because this program only issues GET
``/v1/models`` and ``/health`` and asserts absence of inference substrings.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_shared():
    import importlib.util as _ilu

    here = Path(__file__).resolve().parent / "paseo_codex_noninference.py"
    spec = _ilu.spec_from_file_location("paseo_codex_noninference_shared", here)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError("shared non-inference helper unavailable")
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Candidate-local Codex non-inference check")
    ap.add_argument("--mode", required=True, choices=("catalog", "health"))
    ap.add_argument("--secret-file", default="/run/secrets/pi-unraid-codex-lb")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--model", default="fixture-model")
    args = ap.parse_args(argv)

    C = _load_shared()
    import os as _os

    base = args.base_url or _os.environ.get("PI_CODEX_LB_BASE_URL", "")
    try:
        base = C.validate_base_url(base)
    except C.CodexError as exc:
        print(json.dumps({"mode": args.mode, "status": "FAIL", "reason": C.sanitize_message(exc)}))
        return 23
    if args.mode == "health":
        try:
            res = C.check_health(base, timeout=args.timeout)
        except C.CodexBlocked as exc:
            print(json.dumps({"mode": "health", "status": "BLOCKED", "reason": C.sanitize_message(exc)}))
            return 20
        except C.CodexAuthDenied as exc:
            print(json.dumps({"mode": "health", "status": "FAIL", "reason": C.sanitize_message(exc)}))
            return 21
        except C.CodexError as exc:
            print(json.dumps({"mode": "health", "status": "FAIL", "reason": C.sanitize_message(exc)}))
            return 23
        print(json.dumps({"mode": "health", "status": "PASS", "health": res.get("health")}))
        return 0
    # catalog: secret required inside the candidate.
    try:
        secret_value = C.read_dedicated_secret(args.secret_file)
    except C.CodexBlocked:
        print(json.dumps({"mode": "catalog", "status": "BLOCKED", "reason": "credential missing inside candidate"}))
        return 22
    except C.CodexError as exc:
        print(json.dumps({"mode": "catalog", "status": "FAIL", "reason": C.sanitize_message(exc)}))
        return 23
    try:
        C.validate_model_id(args.model)
    except C.CodexError as exc:
        print(json.dumps({"mode": "catalog", "status": "FAIL", "reason": C.sanitize_message(exc)}))
        return 23
    try:
        res = C.check_catalog(base, secret_value, timeout=args.timeout)
    except C.CodexBlocked as exc:
        print(json.dumps({"mode": "catalog", "status": "BLOCKED", "reason": C.sanitize_message(exc)}))
        return 20
    except C.CodexAuthDenied as exc:
        print(json.dumps({"mode": "catalog", "status": "FAIL", "reason": C.sanitize_message(exc)}))
        return 21
    except C.CodexError as exc:
        print(json.dumps({"mode": "catalog", "status": "FAIL", "reason": C.sanitize_message(exc)}))
        return 23
    finally:
        secret_value = None  # type: ignore[assignment]
    print(json.dumps({"mode": "catalog", "status": "PASS", "count": res.get("count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
