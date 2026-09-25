#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_ENTRYPOINT = ["/usr/bin/tini", "--", "/usr/local/bin/paseo-docker-entrypoint"]
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)
SECRET_ENV_KEY = re.compile(r"(?:^|_)(?:PASSWORD|TOKEN|SECRET|API_KEY|PRIVATE_KEY)(?:$|_)", re.I)


def run(
    args: list[str],
    *,
    input_text: str | None = None,
    timeout: int = 60,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def docker_run(image: str, *command: str, timeout: int = 60, input_text: str | None = None) -> str:
    proc = run(
        ["docker", "run", "--rm", "-i", image, *command],
        input_text=input_text,
        timeout=timeout,
    )
    return proc.stdout.strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def inspect_image(image: str) -> dict:
    return json.loads(run(["docker", "image", "inspect", image], timeout=30).stdout)[0]


def smoke_rpc(image: str) -> dict:
    rpc_input = json.dumps({"id": "m01-t03-state", "type": "get_state"}) + "\n"
    proc = run(
        ["docker", "run", "--rm", "-i", image, "pi", "--mode", "rpc", "--no-session"],
        input_text=rpc_input,
        timeout=30,
    )
    records: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Pi RPC emitted non-JSON stdout record: {line!r}") from exc

    response = next(
        (
            record
            for record in records
            if record.get("id") == "m01-t03-state"
            and record.get("type") == "response"
            and record.get("command") == "get_state"
        ),
        None,
    )
    require(response is not None, f"Pi RPC get_state response missing; records={records!r}")
    require(response.get("success") is True, f"Pi RPC get_state failed: {response!r}")
    return response


def smoke_browser(image: str, *, headed: bool) -> str:
    js = (
        "const { chromium } = require('/usr/local/lib/node_modules/playwright');"
        "(async()=>{"
        f"const b=await chromium.launch({{headless:{str(not headed).lower()}}});"
        "console.log(await b.version());"
        "await b.close();"
        "})().catch(e=>{console.error(e);process.exit(1)});"
    )
    command = ["node", "-e", js]
    if headed:
        command = ["xvfb-run", "-a", *command]
    return docker_run(image, *command, timeout=45)


def smoke_paseo_health(image: str) -> None:
    name = f"pi-unraid-m01-t03-{int(time.time())}"
    run(["docker", "run", "-d", "--name", name, image], timeout=30)
    try:
        check = (
            "const http=require('http');"
            "const req=http.get({hostname:'127.0.0.1',port:6767,path:'/api/health'},"
            "r=>process.exit(r.statusCode===200?0:1));"
            "req.on('error',()=>process.exit(1));"
            "req.setTimeout(1500,()=>{req.destroy();process.exit(1)});"
        )
        deadline = time.monotonic() + 30
        last = ""
        while time.monotonic() < deadline:
            proc = run(
                ["docker", "exec", name, "node", "-e", check],
                timeout=5,
                check=False,
            )
            if proc.returncode == 0:
                return
            last = f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
            time.sleep(1)
        logs = run(["docker", "logs", name], timeout=10, check=False)
        raise RuntimeError(
            "Paseo /api/health did not become GREEN in disposable container; "
            f"last={last}; logs={logs.stdout[-4000:]} {logs.stderr[-2000:]}"
        )
    finally:
        run(["docker", "rm", "-f", name], timeout=15, check=False)


def scan_secrets(image: str, inspect: dict) -> None:
    for entry in inspect.get("Config", {}).get("Env") or []:
        key, sep, value = entry.partition("=")
        if sep and value and SECRET_ENV_KEY.search(key):
            raise RuntimeError(f"secret-like environment variable persisted in image config: {key}")

    history = run(
        ["docker", "history", "--no-trunc", "--format", "{{.CreatedBy}}", image],
        timeout=30,
    ).stdout
    config_text = json.dumps(inspect.get("Config", {}), sort_keys=True)
    for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
        require(not pattern.search(history), f"high-confidence secret pattern found in image history: {pattern.pattern}")
        require(not pattern.search(config_text), f"high-confidence secret pattern found in image config: {pattern.pattern}")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} IMAGE CANDIDATE_JSON", file=sys.stderr)
        return 2

    image = sys.argv[1]
    candidate = json.loads(Path(sys.argv[2]).read_text())
    inspect = inspect_image(image)
    config = inspect["Config"]
    labels = config.get("Labels") or {}
    env = dict(entry.split("=", 1) for entry in (config.get("Env") or []) if "=" in entry)

    expected = {
        "candidate_id": candidate["candidate_id"],
        "paseo_version": candidate["components"]["paseo"]["version"],
        "pi_version": candidate["components"]["pi"]["version"],
        "playwright_version": candidate["components"]["playwright"]["version"],
    }

    require(labels.get("io.pi-unraid.candidate-id") == expected["candidate_id"], "candidate label mismatch")
    require(labels.get("io.pi-unraid.paseo-version") == expected["paseo_version"], "Paseo label mismatch")
    require(labels.get("io.pi-unraid.pi-version") == expected["pi_version"], "Pi label mismatch")
    require(
        labels.get("io.pi-unraid.playwright-version") == expected["playwright_version"],
        "Playwright label mismatch",
    )
    require(config.get("WorkingDir") == "/workspace", "native Paseo WORKDIR was not preserved")
    require(config.get("Entrypoint") == EXPECTED_ENTRYPOINT, f"unexpected inherited entrypoint: {config.get('Entrypoint')!r}")
    require(config.get("Healthcheck") is not None, "Paseo healthcheck is missing")
    require(env.get("HOME") == "/home/paseo", "native Paseo HOME was not preserved")
    require(env.get("PLAYWRIGHT_BROWSERS_PATH") == "/opt/ms-playwright", "image-owned browser path missing")

    pi_version = docker_run(image, "pi", "--version", timeout=20)
    require(pi_version == expected["pi_version"], f"Pi version mismatch: {pi_version!r}")
    rpc_response = smoke_rpc(image)

    tool_readback = docker_run(
        image,
        "bash",
        "-lc",
        (
            "set -e; "
            "git --version; python3 --version; gh --version | head -n1; "
            "docker --version; docker compose version --short; "
            "playwright --version; ssh -V 2>&1; command -v Xvfb; command -v xvfb-run"
        ),
        timeout=30,
    )

    browser_headless = smoke_browser(image, headed=False)
    browser_headed = smoke_browser(image, headed=True)
    expected_browser = candidate["components"]["playwright"]["chromium"]["browser_version"]
    require(browser_headless == expected_browser, f"headless Chromium mismatch: {browser_headless!r}")
    require(browser_headed == expected_browser, f"headed Chromium mismatch: {browser_headed!r}")

    smoke_paseo_health(image)
    scan_secrets(image, inspect)

    summary = {
        "candidate_id": expected["candidate_id"],
        "image_id": inspect["Id"],
        "paseo_version": expected["paseo_version"],
        "pi_version": pi_version,
        "pi_rpc_get_state": bool(rpc_response.get("success")),
        "playwright_version": expected["playwright_version"],
        "chromium_headless": browser_headless,
        "chromium_headed_xvfb": browser_headed,
        "paseo_health": "GREEN",
        "secret_scan": "GREEN",
        "tool_readback": tool_readback.splitlines(),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
