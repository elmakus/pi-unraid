#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import selectors
import stat
import subprocess
import time
import uuid
from pathlib import Path

from run_codex_lb_staged_home_acceptance import (
    DEFAULT_IMAGE,
    DEFAULT_PROD_HOME,
    DEFAULT_SECRET_ENV,
    fetch_catalog_ids,
    instruction_fingerprint,
    leaked_paths,
    load_json,
    production_state,
    provider_details,
    provider_semantics_without_models,
    read_env_value,
    run_auth_reconciler,
    run_instruction,
    run_reconciler,
    sha256_file,
    stored_ids,
)

PROVIDER_ID = "codex-lb"
CONTAINER = "pi-unraid-paseo-1"
class ProductionRpc:
    def __init__(self) -> None:
        self.marker = f"m02t02-{uuid.uuid4().hex[:10]}"
        shell = (
            "set -a; . /run/secrets/pi-unraid-codex-lb; "
            "export PI_CODEX_LB_MODEL_REFRESH_MS=1000; "
            "exec pi --mode rpc --no-session --no-context-files --no-skills "
            "--no-prompt-templates --no-themes"
        )
        self.proc = subprocess.Popen(
            [
                "docker", "exec", "--user", "99:100", "-i",
                "-e", f"PI_M02_T02_MARKER={self.marker}",
                CONTAINER, "sh", "-lc", shell,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)

    def request(self, payload: dict[str, object], timeout: float = 15.0) -> dict[str, object]:
        request_id = f"m02-{uuid.uuid4().hex[:8]}"
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(dict(payload, id=request_id)) + "\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ready = self.selector.select(timeout=max(0.05, deadline - time.monotonic()))
            if not ready:
                continue
            assert self.proc.stdout is not None
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError(f"production Pi RPC exited before response: rc={self.proc.poll()}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") == "response" and record.get("id") == request_id:
                if record.get("success") is not True:
                    raise RuntimeError(f"RPC {payload.get('type')} failed")
                return record
        raise TimeoutError(f"Timed out waiting for RPC {payload.get('type')}")

    def close(self) -> None:
        if self.proc.stdin and not self.proc.stdin.closed:
            self.proc.stdin.close()
        try:
            self.proc.wait(timeout=8)
        except subprocess.TimeoutExpired as exc:
            self.proc.terminate()
            raise RuntimeError("production Pi RPC did not exit on EOF") from exc


def rpc_ids(record: dict[str, object]) -> list[str]:
    data = record.get("data")
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list):
        return []
    return sorted(
        str(item["id"])
        for item in models
        if isinstance(item, dict)
        and item.get("provider") == PROVIDER_ID
        and isinstance(item.get("id"), str)
    )


def wait_ids(rpc: ProductionRpc, expected: list[str], timeout: float = 20.0) -> list[str]:
    deadline = time.monotonic() + timeout
    latest: list[str] = []
    while time.monotonic() < deadline:
        latest = rpc_ids(rpc.request({"type": "get_available_models"}))
        if latest == expected:
            return latest
        time.sleep(0.25)
    raise AssertionError(f"production RPC catalog mismatch: latest={latest}, expected={expected}")


def runtime_identity(state: dict[str, object]) -> dict[str, object]:
    return {
        key: state[key]
        for key in ("container_id", "running", "health", "started_at", "restart_count")
    }


def restore_store(store: Path, existed: bool, raw: bytes | None, mode: int | None) -> None:
    if existed:
        assert raw is not None and mode is not None
        store.write_bytes(raw)
        os.chmod(store, mode)
    else:
        store.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--prod-home", default=DEFAULT_PROD_HOME)
    parser.add_argument("--secret-env", default=DEFAULT_SECRET_ENV)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    source = repo / "config/pi-agent"
    prod = Path(args.prod_home).resolve()
    secret_file = Path(args.secret_env).resolve()
    models_file = prod / ".pi/agent/models.json"
    auth_file = prod / ".pi/agent/auth.json"
    store = prod / ".pi/agent/models-store.json"
    provider_state = prod / ".pi-unraid/codex-lb-provider-config"
    auth_state = prod / ".pi-unraid/codex-lb-auth-shadow"
    instruction_previous = prod / ".pi-unraid/instruction-plane/previous"

    if not prod.is_dir() or not secret_file.is_file():
        raise SystemExit("required production HOME or secret env file is unavailable")
    if provider_state.exists() or auth_state.exists():
        raise AssertionError("pre-existing Codex-LB rollback state requires reconciliation before activation")

    before = production_state(prod, source)
    if before["running"] is not True or before["health"] != "healthy":
        raise AssertionError(f"production Paseo is not healthy before activation: {before}")

    before_models = models_file.read_bytes()
    before_auth = auth_file.read_bytes() if auth_file.is_file() else None
    before_store_exists = store.is_file()
    before_store = store.read_bytes() if before_store_exists else None
    before_store_mode = stat.S_IMODE(store.stat().st_mode) if before_store_exists else None
    before_doc = load_json(models_file)
    before_instruction = instruction_fingerprint(source, prod)
    api_key = read_env_value(secret_file, "CODEX_LB_API_KEY")

    summary: dict[str, object] = {"verdict": "GREEN", "production_before": before}
    rpc: ProductionRpc | None = None
    applied = False
    auth_migrated = False
    provider_migrated = False
    try:
        summary["instruction_apply"] = run_instruction(repo, args.image, "apply", prod)
        applied = True
        summary["instruction_status"] = run_instruction(repo, args.image, "status", prod)
        if summary["instruction_status"].get("in_sync") is not True:
            raise AssertionError("production instruction plane is not in sync")

        summary["auth_shadow_migrate"] = run_auth_reconciler(repo, args.image, "migrate", prod)
        auth_migrated = bool(summary["auth_shadow_migrate"].get("changed"))
        summary["auth_shadow_status"] = run_auth_reconciler(repo, args.image, "status", prod)
        if summary["auth_shadow_status"].get("shadow_present") is not False:
            raise AssertionError("production codex-lb auth shadow remains")

        base_url = provider_details(before_doc).get("baseUrl")
        if not isinstance(base_url, str):
            raise AssertionError("production Codex-LB baseUrl is invalid")
        live_before = fetch_catalog_ids(base_url, api_key)
        summary["live_ids_before_provider_migration"] = live_before

        rpc = ProductionRpc()
        summary["seed_rpc_ids"] = wait_ids(rpc, live_before)
        rpc.close()
        rpc = None
        if not store.is_file() or stored_ids(store) != live_before:
            raise AssertionError("production provider-scoped LKG was not seeded exactly")
        summary["seeded_lkg_ids"] = stored_ids(store)

        summary["provider_migrate"] = run_reconciler(repo, args.image, "migrate", prod)
        provider_migrated = bool(summary["provider_migrate"].get("changed"))
        summary["provider_status"] = run_reconciler(repo, args.image, "status", prod)
        after_doc = load_json(models_file)
        if provider_semantics_without_models(before_doc) != after_doc:
            raise AssertionError("production provider migration changed unrelated semantics")
        if provider_details(after_doc)["models_present"]:
            raise AssertionError("production static Codex-LB models remain")

        live_after = fetch_catalog_ids(base_url, api_key)
        summary["live_ids_after_provider_migration"] = live_after
        rpc = ProductionRpc()
        summary["production_rpc_ids"] = wait_ids(rpc, live_after)
        rpc.close()
        rpc = None

        if stored_ids(store) != live_after:
            raise AssertionError("production LKG differs from current live catalog")
        summary["persisted_lkg_ids"] = stored_ids(store)
        summary["secret_scan"] = leaked_paths(prod, api_key)
        if summary["secret_scan"]:
            raise AssertionError("current dedicated Codex-LB secret leaked into production HOME")

        after = production_state(prod, source)
        summary["production_after"] = after
        if runtime_identity(after) != runtime_identity(before):
            raise AssertionError("production Paseo runtime identity/health changed during activation")
        if after["health"] != "healthy":
            raise AssertionError("production Paseo is not healthy after activation")
        if run_instruction(repo, args.image, "status", prod).get("in_sync") is not True:
            raise AssertionError("production instruction plane lost sync")
        if run_reconciler(repo, args.image, "status", prod).get("dynamic") is not True:
            raise AssertionError("production provider config is not dynamic")
        if run_auth_reconciler(repo, args.image, "status", prod).get("shadow_present") is not False:
            raise AssertionError("production auth shadow returned")
        if not provider_state.is_dir() or not auth_state.is_dir() or not instruction_previous.is_dir():
            raise AssertionError("required bounded rollback anchors are not all present")
    except Exception:
        if rpc is not None:
            try:
                rpc.close()
            except Exception:
                pass
        if provider_state.exists():
            run_reconciler(repo, args.image, "rollback", prod)
        if auth_state.exists():
            run_auth_reconciler(repo, args.image, "rollback", prod)
        if instruction_previous.exists():
            run_instruction(repo, args.image, "rollback", prod)
        restore_store(store, before_store_exists, before_store, before_store_mode)

        if models_file.read_bytes() != before_models:
            raise AssertionError("failure rollback did not restore provider config")
        if before_auth is None:
            if auth_file.exists():
                raise AssertionError("failure rollback created auth.json")
        elif auth_file.read_bytes() != before_auth:
            raise AssertionError("failure rollback did not restore auth.json")
        if instruction_fingerprint(source, prod) != before_instruction:
            raise AssertionError("failure rollback did not restore instruction plane")
        rolled = production_state(prod, source)
        if runtime_identity(rolled) != runtime_identity(before):
            raise AssertionError("failure rollback changed production runtime identity/health")
        raise

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
