#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import selectors
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_IMAGE = "pi-unraid:paseo-b4e0c1e7c276"
DEFAULT_SUBJECT = "2c38c280f1f7a78045ead22b4aa70f21a6992680"


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def production_status() -> str:
    try:
        return run("docker", "ps", "--filter", "name=^/pi-unraid-paseo-1$", "--format", "{{.Names}} {{.Status}}")
    except subprocess.CalledProcessError:
        return "unavailable"


class Fixture:
    def __init__(self) -> None:
        self.key = secrets.token_urlsafe(24)
        self.models = ["keep-model", "remove-me"]
        self.fail = False
        self.requests = 0
        self.failures = 0
        self.lock = threading.Lock()
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                with fixture.lock:
                    fixture.requests += 1
                    fail = fixture.fail
                    models = list(fixture.models)
                    expected = f"Bearer {fixture.key}"
                if self.path != "/v1/models":
                    self.send_response(404)
                    self.end_headers()
                    return
                if self.headers.get("Authorization") != expected:
                    self.send_response(401)
                    self.end_headers()
                    return
                if fail:
                    with fixture.lock:
                        fixture.failures += 1
                    self.send_response(503)
                    self.end_headers()
                    return
                body = json.dumps({"object": "list", "data": [{"id": model, "object": "model"} for model in models]}).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return int(self.server.server_address[1])

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class RpcProcess:
    def __init__(self, image: str, home: Path, key: str, name: str) -> None:
        self.name = name
        cmd = [
            "docker", "run", "--rm", "--name", name, "--network", "host", "-i",
            "-e", "HOME=/home/paseo",
            "-e", f"CODEX_LB_API_KEY={key}",
            "-e", "PI_CODEX_LB_MODEL_REFRESH_MS=1000",
            "-v", f"{home}:/home/paseo",
            image, "pi", "--mode", "rpc", "--no-session",
            "--no-context-files", "--no-skills", "--no-prompt-templates", "--no-themes",
        ]
        self.proc = subprocess.Popen(
            cmd,
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
        request_id = f"accept-{uuid.uuid4().hex[:8]}"
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
                    raise RuntimeError(f"RPC {payload.get('type')} failed: {record.get('error')}")
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
            subprocess.run(["docker", "rm", "-f", self.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def codex_ids(record: dict[str, object]) -> list[str]:
    data = record.get("data")
    if not isinstance(data, dict):
        return []
    models = data.get("models")
    if not isinstance(models, list):
        return []
    return sorted(
        str(model["id"])
        for model in models
        if isinstance(model, dict) and model.get("provider") == "codex-lb" and isinstance(model.get("id"), str)
    )


def wait_ids(rpc: RpcProcess, expected: set[str], absent: set[str] | None = None, timeout: float = 15.0) -> list[str]:
    absent = absent or set()
    deadline = time.monotonic() + timeout
    latest: list[str] = []
    while time.monotonic() < deadline:
        latest = codex_ids(rpc.request({"type": "get_available_models"}))
        if expected.issubset(latest) and absent.isdisjoint(latest):
            return latest
        time.sleep(0.25)
    raise AssertionError(f"Catalog did not converge: latest={latest}, expected={sorted(expected)}, absent={sorted(absent)}")


def model_identity(state_record: dict[str, object]) -> str:
    data = state_record.get("data")
    model = data.get("model") if isinstance(data, dict) else None
    if not isinstance(model, dict):
        return ""
    return f"{model.get('provider')}/{model.get('id')}"


def stored_ids(store_path: Path) -> list[str]:
    value = json.loads(store_path.read_text())
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("provider") == "codex-lb" and isinstance(node.get("id"), str):
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--m01-t01-subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    subprocess.check_call(["git", "diff", "--quiet", args.m01_t01_subject, "--", "config/pi-agent"], cwd=repo)
    pi_version = run("docker", "run", "--rm", args.image, "pi", "--version")
    image_id = run("docker", "image", "inspect", args.image, "--format", "{{.Id}}")
    before = production_status()

    summary: dict[str, object] = {
        "verdict": "GREEN",
        "m01_t01_subject": args.m01_t01_subject,
        "managed_instruction_plane_exact_match": True,
        "image": args.image,
        "image_id": image_id,
        "pi_version": pi_version,
        "production_before": before,
    }

    fixture = Fixture()
    fixture.start()
    first: RpcProcess | None = None
    second: RpcProcess | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="m01-t02-live-rpc-") as tmp_name:
            root = Path(tmp_name)
            home = root / "home"
            agent = home / ".pi" / "agent"
            shutil.copytree(repo / "config" / "pi-agent", agent)
            models_file = agent / "models.json"
            models_file.write_text(json.dumps({
                "providers": {
                    "codex-lb": {
                        "baseUrl": f"http://127.0.0.1:{fixture.port}/v1",
                        "api": "openai-responses",
                        "apiKey": "${CODEX_LB_API_KEY}",
                        "models": [{"id": "static-fallback"}],
                    }
                }
            }, indent=2) + "\n")

            first = RpcProcess(args.image, home, fixture.key, f"m01t02-a-{uuid.uuid4().hex[:8]}")
            summary["initial_ids"] = wait_ids(first, {"keep-model", "remove-me"}, {"static-fallback"})

            with fixture.lock:
                fixture.models = ["keep-model", "remove-me", "added-model"]
            summary["after_add_ids"] = wait_ids(first, {"keep-model", "remove-me", "added-model"})

            first.request({"type": "set_model", "provider": "codex-lb", "modelId": "remove-me"})
            summary["selected_before_remove"] = model_identity(first.request({"type": "get_state"}))

            with fixture.lock:
                fixture.models = ["keep-model", "added-model"]
            summary["after_remove_ids"] = wait_ids(first, {"keep-model", "added-model"}, {"remove-me"})
            summary["selected_after_remove"] = model_identity(first.request({"type": "get_state"}))
            if summary["selected_after_remove"] != "codex-lb/remove-me":
                raise AssertionError(f"Selected model changed unexpectedly: {summary['selected_after_remove']}")

            with fixture.lock:
                fixture.fail = True
                failures_before = fixture.failures
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with fixture.lock:
                    if fixture.failures > failures_before:
                        break
                time.sleep(0.2)
            else:
                raise AssertionError("No forced HTTP 503 refresh was observed")
            summary["after_503_ids"] = wait_ids(first, {"keep-model", "added-model"}, {"remove-me"})

            store = agent / "models-store.json"
            if not store.is_file():
                raise AssertionError("models-store.json was not persisted")
            summary["persisted_ids"] = stored_ids(store)
            if set(summary["persisted_ids"]) != {"keep-model", "added-model"}:
                raise AssertionError(f"Unexpected persisted IDs: {summary['persisted_ids']}")
            summary["secret_scan_before_restart"] = leaked_paths(home, fixture.key)
            if summary["secret_scan_before_restart"]:
                raise AssertionError(f"Fixture credential leaked before restart: {summary['secret_scan_before_restart']}")

            first.close()
            first = None
            fixture.stop()

            second = RpcProcess(args.image, home, fixture.key, f"m01t02-b-{uuid.uuid4().hex[:8]}")
            summary["restart_offline_ids"] = wait_ids(second, {"keep-model", "added-model"}, {"remove-me"})
            summary["secret_scan_after_restart"] = leaked_paths(home, fixture.key)
            if summary["secret_scan_after_restart"]:
                raise AssertionError(f"Fixture credential leaked after restart: {summary['secret_scan_after_restart']}")
            summary["fixture_requests"] = fixture.requests
            summary["fixture_503_responses"] = fixture.failures
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        if fixture.thread.is_alive():
            fixture.stop()

    after = production_status()
    summary["production_after"] = after
    if before != after:
        raise AssertionError(f"Production container status changed: before={before!r} after={after!r}")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
