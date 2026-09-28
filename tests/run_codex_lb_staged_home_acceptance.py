#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import selectors
import secrets
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

DEFAULT_IMAGE = "pi-unraid:paseo-b4e0c1e7c276"
DEFAULT_PROD_HOME = "/mnt/user/appdata/pi-unraid/paseo-home"
DEFAULT_SECRET_ENV = "/mnt/user/appdata/pi-unraid/secrets/codex-lb.env"
PROVIDER_ID = "codex-lb"


def run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def run_json(*args: str, cwd: Path | None = None) -> dict[str, object]:
    return json.loads(run(*args, cwd=cwd))


def run_instruction(repo: Path, image: str, action: str, home: Path) -> dict[str, object]:
    return run_json(
        "bash", "scripts/configure-pi-instruction-plane.sh",
        action, image, str(home), "99", "100", cwd=repo,
    )


def run_reconciler(repo: Path, image: str, action: str, home: Path) -> dict[str, object]:
    script = repo / "scripts/reconcile-codex-lb-provider-config.py"
    output = run(
        "docker", "run", "--rm", "--user", "99:100",
        "-v", f"{home}:/home/paseo",
        "-v", f"{script}:/reconcile-codex-lb-provider-config.py:ro",
        image,
        "python3", "/reconcile-codex-lb-provider-config.py",
        action,
        "/home/paseo/.pi/agent/models.json",
        "/home/paseo/.pi-unraid/codex-lb-provider-config",
    )
    return json.loads(output)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise AssertionError(f"Expected object in {path}")
    return value


def managed_relpaths(source: Path, home: Path) -> list[Path]:
    rels = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    current = home / ".pi-unraid/instruction-plane/current.json"
    if current.is_file():
        value = load_json(current)
        files = value.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, str):
                    rels.add(Path(item))
    return sorted(rels, key=lambda p: p.as_posix())


def instruction_fingerprint(source: Path, home: Path) -> str:
    digest = hashlib.sha256()
    current = home / ".pi-unraid/instruction-plane/current.json"
    digest.update(b"current\0")
    digest.update(current.read_bytes() if current.is_file() else b"<absent>")
    digest.update(b"\0previous\0")
    digest.update(b"1" if (home / ".pi-unraid/instruction-plane/previous").exists() else b"0")
    agent = home / ".pi/agent"
    for rel in managed_relpaths(source, home):
        target = agent / rel
        digest.update(rel.as_posix().encode())
        digest.update(b"\0")
        if target.is_file() and not target.is_symlink():
            digest.update(b"present\0")
            digest.update(str(stat.S_IMODE(target.stat().st_mode)).encode())
            digest.update(b"\0")
            digest.update(target.read_bytes())
        else:
            digest.update(b"absent")
        digest.update(b"\0")
    return digest.hexdigest()


def provider_semantics_without_models(doc: dict[str, object]) -> dict[str, object]:
    cloned = json.loads(json.dumps(doc))
    providers = cloned.get("providers")
    if not isinstance(providers, dict):
        raise AssertionError("models.json providers is not an object")
    provider = providers.get(PROVIDER_ID)
    if not isinstance(provider, dict):
        raise AssertionError("codex-lb provider missing")
    provider.pop("models", None)
    return cloned


def provider_details(doc: dict[str, object]) -> dict[str, object]:
    providers = doc.get("providers")
    if not isinstance(providers, dict):
        raise AssertionError("models.json providers is not an object")
    provider = providers.get(PROVIDER_ID)
    if not isinstance(provider, dict):
        raise AssertionError("codex-lb provider missing")
    return {
        "baseUrl": provider.get("baseUrl"),
        "api": provider.get("api"),
        "apiKey_reference": provider.get("apiKey"),
        "models_present": "models" in provider,
        "unrelated_provider_ids": sorted(k for k in providers if k != PROVIDER_ID),
    }


def read_env_value(path: Path, key: str) -> str:
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == key:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if not value:
                break
            return value
    raise AssertionError(f"{key} is missing from the secret env file")


def host_catalog_url(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    host = parsed.hostname
    if not host:
        raise AssertionError("codex-lb baseUrl has no hostname")
    if host == "host.docker.internal":
        host = "127.0.0.1"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/") + "/models"
    return urllib.parse.urlunsplit((parsed.scheme, f"{host}{port}", path, "", ""))


def fetch_catalog_ids(base_url: str, api_key: str) -> list[str]:
    request = urllib.request.Request(
        host_catalog_url(base_url),
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.load(response)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise AssertionError("real Codex-LB catalog data is not a list")
    ids = sorted(
        {
            item["id"]
            for item in data
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item["id"]
            and item["id"].strip() == item["id"]
        }
    )
    if not ids:
        raise AssertionError("real Codex-LB catalog is empty")
    return ids


def stored_ids(path: Path) -> list[str]:
    value = json.loads(path.read_text())
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("provider") == PROVIDER_ID and isinstance(node.get("id"), str):
                found.add(node["id"])
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return sorted(found)


def leaked_paths(root: Path, secret: str) -> list[str]:
    needle = secret.encode()
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            if needle in path.read_bytes():
                hits.append(str(path.relative_to(root)))
        except OSError:
            pass
    return sorted(hits)


def production_state(home: Path, source: Path) -> dict[str, object]:
    raw = json.loads(run("docker", "inspect", "pi-unraid-paseo-1"))[0]
    state = raw.get("State", {})
    health = state.get("Health") if isinstance(state, dict) else None
    return {
        "container_id": raw.get("Id"),
        "running": state.get("Running") if isinstance(state, dict) else None,
        "health": health.get("Status") if isinstance(health, dict) else None,
        "started_at": state.get("StartedAt") if isinstance(state, dict) else None,
        "restart_count": raw.get("RestartCount"),
        "models_sha256": sha256_file(home / ".pi/agent/models.json"),
        "instruction_fingerprint": instruction_fingerprint(source, home),
    }


class RpcProcess:
    def __init__(self, image: str, home: Path, api_key: str) -> None:
        self.name = f"m02t01-{uuid.uuid4().hex[:10]}"
        env = os.environ.copy()
        env["CODEX_LB_API_KEY"] = api_key
        cmd = [
            "docker", "run", "--rm", "--name", self.name,
            "--user", "99:100",
            "--network", "host",
            "--add-host", "host.docker.internal:host-gateway",
            "-i",
            "-e", "HOME=/home/paseo",
            "-e", "CODEX_LB_API_KEY",
            "-e", "PI_CODEX_LB_MODEL_REFRESH_MS=1000",
            "-v", f"{home}:/home/paseo",
            image,
            "pi", "--mode", "rpc", "--no-session",
            "--no-context-files", "--no-skills", "--no-prompt-templates", "--no-themes",
        ]
        self.proc = subprocess.Popen(
            cmd,
            env=env,
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
        wire = dict(payload, id=request_id)
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(wire) + "\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ready = self.selector.select(timeout=max(0.05, deadline - time.monotonic()))
            if not ready:
                continue
            assert self.proc.stdout is not None
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError(f"Pi RPC exited before response: rc={self.proc.poll()}")
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
        try:
            if self.proc.stdin and not self.proc.stdin.closed:
                self.proc.stdin.close()
            self.proc.wait(timeout=8)
        except Exception:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
                self.proc.wait(timeout=5)
        finally:
            subprocess.run(
                ["docker", "rm", "-f", self.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def rpc_codex_ids(record: dict[str, object]) -> list[str]:
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


def wait_rpc_ids(rpc: RpcProcess, expected: list[str], timeout: float = 20.0) -> list[str]:
    deadline = time.monotonic() + timeout
    latest: list[str] = []
    while time.monotonic() < deadline:
        latest = rpc_codex_ids(rpc.request({"type": "get_available_models"}))
        if latest == expected:
            return latest
        time.sleep(0.25)
    raise AssertionError(f"RPC catalog mismatch: latest={latest}, expected={expected}")


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
    if not prod.is_dir() or not secret_file.is_file():
        raise SystemExit("required production HOME or secret env file is unavailable")

    pi_version = run("docker", "run", "--rm", args.image, "pi", "--version")
    image_id = run("docker", "image", "inspect", args.image, "--format", "{{.Id}}")
    before_prod = production_state(prod, source)
    if before_prod["running"] is not True or before_prod["health"] != "healthy":
        raise AssertionError(f"production Paseo is not healthy: {before_prod}")

    api_key = read_env_value(secret_file, "CODEX_LB_API_KEY")
    rpc: RpcProcess | None = None
    summary: dict[str, object] = {
        "verdict": "GREEN",
        "image": args.image,
        "image_id": image_id,
        "pi_version": pi_version,
        "production_before": before_prod,
    }

    with tempfile.TemporaryDirectory(prefix="m02-t01-staged-home-") as tmp_name:
        stage = Path(tmp_name) / "home"
        (stage / ".pi").mkdir(parents=True)
        (stage / ".pi-unraid").mkdir(parents=True)
        os.chown(stage, 99, 100)
        os.chmod(stage, 0o700)
        os.chown(stage / ".pi", 99, 100)
        os.chown(stage / ".pi-unraid", 99, 100)
        subprocess.check_call(["cp", "-a", str(prod / ".pi/agent"), str(stage / ".pi/agent")])
        prod_ip = prod / ".pi-unraid/instruction-plane"
        if prod_ip.is_dir():
            subprocess.check_call(["cp", "-a", str(prod_ip), str(stage / ".pi-unraid/instruction-plane")])

        models_file = stage / ".pi/agent/models.json"
        provider_state = stage / ".pi-unraid/codex-lb-provider-config"
        before_models_raw = models_file.read_bytes()
        before_doc = load_json(models_file)
        before_instruction = instruction_fingerprint(source, stage)
        if sha256_file(models_file) != before_prod["models_sha256"]:
            raise AssertionError("staged provider config is not an exact production clone")
        if before_instruction != before_prod["instruction_fingerprint"]:
            raise AssertionError("staged instruction surface is not an exact production clone")

        summary["staged_before"] = {
            "models_sha256": sha256_file(models_file),
            "instruction_fingerprint": before_instruction,
            "provider": provider_details(before_doc),
        }

        applied = False
        migrated = False
        try:
            summary["instruction_apply"] = run_instruction(repo, args.image, "apply", stage)
            applied = True
            summary["instruction_status"] = run_instruction(repo, args.image, "status", stage)
            if summary["instruction_status"].get("in_sync") is not True:
                raise AssertionError("staged instruction plane is not in sync after apply")

            bootstrap_details = provider_details(before_doc)
            base_url = bootstrap_details["baseUrl"]
            if not isinstance(base_url, str):
                raise AssertionError("staged Codex-LB baseUrl is invalid")
            direct_ids = fetch_catalog_ids(base_url, api_key)
            summary["real_codex_lb_ids_before_migration"] = direct_ids

            store = stage / ".pi/agent/models-store.json"
            summary["pre_seed_cached_ids"] = stored_ids(store) if store.is_file() else []

            # First prove the extension against the staged production clone while
            # the reversible static bootstrap still exists. This seeds Pi's
            # provider-scoped LKG before the static list is removed.
            rpc = RpcProcess(args.image, stage, api_key)
            summary["seed_rpc_codex_lb_ids"] = wait_rpc_ids(rpc, direct_ids)
            rpc.close()
            rpc = None
            if not store.is_file():
                raise AssertionError("provider-scoped models-store.json was not persisted during staged seed")
            summary["seeded_codex_lb_ids"] = stored_ids(store)
            if summary["seeded_codex_lb_ids"] != direct_ids:
                raise AssertionError("seeded Codex-LB catalog differs from the real catalog")

            summary["provider_migrate"] = run_reconciler(repo, args.image, "migrate", stage)
            migrated = True
            summary["provider_status"] = run_reconciler(repo, args.image, "status", stage)
            after_doc = load_json(models_file)
            if provider_semantics_without_models(before_doc) != after_doc:
                raise AssertionError("provider migration changed semantics beyond removing static models")
            details = provider_details(after_doc)
            if details["models_present"]:
                raise AssertionError("static Codex-LB models remain after migration")
            summary["staged_dynamic_provider"] = details

            direct_ids_after = fetch_catalog_ids(base_url, api_key)
            summary["real_codex_lb_ids_after_migration"] = direct_ids_after

            # A new Pi process now starts from the dynamic provider config with
            # no hardcoded model list; the provider-scoped LKG is the bootstrap
            # and the live refresh must converge to the current real catalog.
            rpc = RpcProcess(args.image, stage, api_key)
            summary["rpc_codex_lb_ids_after_migration"] = wait_rpc_ids(rpc, direct_ids_after)
            rpc.close()
            rpc = None

            summary["persisted_codex_lb_ids"] = stored_ids(store)
            if summary["persisted_codex_lb_ids"] != direct_ids_after:
                raise AssertionError("persisted Codex-LB catalog differs from the current real catalog")

            summary["secret_scan"] = leaked_paths(stage, api_key)
            if summary["secret_scan"]:
                raise AssertionError("raw Codex-LB credential leaked into staged HOME")
        finally:
            if rpc is not None:
                rpc.close()
            if migrated:
                summary["provider_rollback"] = run_reconciler(repo, args.image, "rollback", stage)
            if applied:
                summary["instruction_rollback"] = run_instruction(repo, args.image, "rollback", stage)

        after_instruction = instruction_fingerprint(source, stage)
        summary["staged_after_rollback"] = {
            "models_sha256": sha256_file(models_file),
            "instruction_fingerprint": after_instruction,
            "provider_rollback_state_exists": provider_state.exists(),
        }
        if models_file.read_bytes() != before_models_raw:
            raise AssertionError("provider rollback did not restore exact pre-change bytes")
        if after_instruction != before_instruction:
            raise AssertionError("instruction rollback did not restore exact pre-change surface")
        if provider_state.exists():
            raise AssertionError("provider rollback state remains after rollback")

    after_prod = production_state(prod, source)
    summary["production_after"] = after_prod
    if after_prod != before_prod:
        raise AssertionError("production HOME/runtime fingerprint changed during staged acceptance")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
