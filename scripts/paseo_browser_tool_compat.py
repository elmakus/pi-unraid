#!/usr/bin/env python3
"""M06-T02 automatic browser/tool/extension compatibility harness.

readback: machine-readable static verification of the exact frozen candidate,
child-image browser/tool pins, automation-profile/download policy, SpecPi and
adapter delivery policy, and HA/M07-T05 deferrals. No Docker, no network,
no mutation.

flow: disposable Docker end-to-end of the browser/tool/extension
compatibility flow on the exact frozen candidate image. Requires --scope
disposable and a fixture root under a system temp directory; refuses
production scope and production host paths.

Exit is M06 technical GREEN with HA outstanding only; this harness never
claims full GREEN and never performs wishlist activation, interactive
authentication, or production mutation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CARD_ID = "M06-T02"
CANDIDATE_ID = "sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69"
BASE_DIGEST = "sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136"
PASEO_VERSION = "0.9.2"
PI_VERSION = "0.87.1"
PLAYWRIGHT_VERSION = "1.63.0"
CHROMIUM_VERSION = "153.0.8010.12"
CHROMIUM_REVISION = "1243"
SPECPI_VERSION = "0.34.0"
ADAPTER_VERSION = "2.37.0"
GH_VERSION = "2.101.0"
DOCKER_CLI_VERSION = "29.8.1"
DOCKER_COMPOSE_VERSION = "5.5.1"
NODE_VERSION = "22.23.3"
RUNTIME_UID = 99
RUNTIME_GID = 100

PLAYWRIGHT_MODULE = "/usr/local/lib/node_modules/playwright"
AUTOMATION_PROFILE_PATH = "/m06t02/profile"
AUTOMATION_DOWNLOADS_PATH = "/m06t02/downloads"

# Genuinely interactive or post-deploy proofs this Card must not claim.
# Authenticated gh/UX proof belongs to the HA wave (P4 section 4/M07);
# SpecPi wishlist activation belongs to conditional post-deploy M07-T05.
HA_DEFERRED = (
    {"need": "authenticated_github_workflow", "owner": "M07-T02"},
    {"need": "manual_headed_ux_judgment", "owner": "M07-T02"},
    {"need": "secret_supply", "owner": "M07-T02"},
    {"need": "oauth_device_flow", "owner": "M07-T02"},
    {"need": "account_choice", "owner": "M07-T02"},
    {"need": "two_factor_approval", "owner": "M07-T02"},
    {"need": "manual_login_approval", "owner": "M07-T02"},
    {"need": "real_phone_pairing", "owner": "M07-T02"},
    {"need": "graphql_credential_materialization", "owner": "M07-T02"},
    {"need": "authenticated_graphql_mutation", "owner": "M07-T02"},
    {"need": "specpi_wishlist_activation", "owner": "M07-T05"},
    {"need": "production_confirmation", "owner": "M07-T03"},
)

PERSONAL_PROFILE_PATHS = (
    ".config/google-chrome",
    ".config/chromium",
    ".mozilla",
    ".pki",
)

HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def fail(message: str):
    raise SystemExit(f"paseo browser-tool-compat error: {message}")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_candidate_identity(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    candidate_path = root / "config" / "paseo-candidate.json"
    try:
        candidate = json.loads(candidate_path.read_text())
    except (OSError, ValueError) as exc:
        return {}, [f"candidate file unreadable: {exc}"]
    if candidate.get("candidate_id") != CANDIDATE_ID:
        violations.append("candidate_id mismatch")
    components = candidate.get("components", {})
    paseo = components.get("paseo", {})
    if paseo.get("version") != PASEO_VERSION:
        violations.append("paseo version mismatch")
    if paseo.get("artifact", {}).get("digest") != BASE_DIGEST:
        violations.append("paseo base digest mismatch")
    if components.get("pi", {}).get("version") != PI_VERSION:
        violations.append("pi version mismatch")
    playwright = components.get("playwright", {})
    if playwright.get("version") != PLAYWRIGHT_VERSION:
        violations.append("playwright version mismatch")
    chromium = playwright.get("chromium", {})
    if chromium.get("browser_version") != CHROMIUM_VERSION:
        violations.append("chromium browser version mismatch")
    if chromium.get("revision") != CHROMIUM_REVISION:
        violations.append("chromium revision mismatch")
    if components.get("specpi", {}).get("version") != SPECPI_VERSION:
        violations.append("specpi version mismatch")
    if components.get("pi_mcp_adapter", {}).get("version") != ADAPTER_VERSION:
        violations.append("pi-mcp-adapter version mismatch")
    if components.get("github_cli", {}).get("version") != GH_VERSION:
        violations.append("github cli version mismatch")
    if components.get("docker_cli", {}).get("version") != DOCKER_CLI_VERSION:
        violations.append("docker cli version mismatch")
    if components.get("docker_compose", {}).get("version") != DOCKER_COMPOSE_VERSION:
        violations.append("docker compose version mismatch")
    if components.get("node", {}).get("version") != NODE_VERSION:
        violations.append("node version mismatch")
    if candidate.get("policy", {}).get("build_must_not_reresolve") is not True:
        violations.append("build_must_not_reresolve not enforced")
    try:
        dockerfile = (root / "Dockerfile").read_text()
    except OSError as exc:
        return {}, [f"dockerfile unreadable: {exc}"]
    if f"FROM ghcr.io/getpaseo/paseo@{BASE_DIGEST}" not in dockerfile:
        violations.append("dockerfile base digest mismatch")
    for label, expected in (
        ("io.pi-unraid.candidate-id", CANDIDATE_ID),
        ("io.pi-unraid.paseo-version", PASEO_VERSION),
        ("io.pi-unraid.pi-version", PI_VERSION),
        ("io.pi-unraid.specpi-version", SPECPI_VERSION),
        ("io.pi-unraid.pi-mcp-adapter-version", ADAPTER_VERSION),
        ("io.pi-unraid.playwright-version", PLAYWRIGHT_VERSION),
    ):
        if f'{label}="{expected}"' not in dockerfile:
            violations.append(f"dockerfile label {label} mismatch")
    identity = {
        "candidate_id": candidate.get("candidate_id"),
        "paseo_version": paseo.get("version"),
        "pi_version": components.get("pi", {}).get("version"),
        "playwright_version": playwright.get("version"),
        "chromium_version": chromium.get("browser_version"),
        "chromium_revision": chromium.get("revision"),
        "specpi_version": components.get("specpi", {}).get("version"),
        "pi_mcp_adapter_version": components.get("pi_mcp_adapter", {}).get("version"),
        "gh_version": components.get("github_cli", {}).get("version"),
        "docker_cli_version": components.get("docker_cli", {}).get("version"),
        "docker_compose_version": components.get("docker_compose", {}).get("version"),
        "node_version": components.get("node", {}).get("version"),
        "base_digest": paseo.get("artifact", {}).get("digest"),
        "frozen": candidate.get("policy", {}).get("build_must_not_reresolve") is True,
    }
    return identity, violations


def check_browser_tooling(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    try:
        dockerfile = (root / "Dockerfile").read_text()
        compose = (root / "compose.yaml").read_text()
    except OSError as exc:
        return {}, [f"runtime shape unreadable: {exc}"]
    playwright_global = '"playwright@${PI_UNRAID_PLAYWRIGHT_VERSION}"' in dockerfile
    chromium_install = "playwright install --with-deps chromium" in dockerfile
    browsers_path = 'PLAYWRIGHT_BROWSERS_PATH="/opt/ms-playwright"' in dockerfile
    xvfb_present = re.search(r"(?m)^\s+xvfb\s*\\?\s*$", dockerfile) is not None
    xvfb_check = "command -v Xvfb" in dockerfile
    gh_pinned = (
        '"https://github.com/cli/cli/releases/download/v${PI_UNRAID_GH_VERSION}/gh_${PI_UNRAID_GH_VERSION}_linux_amd64.tar.gz"'
        in dockerfile
        and "9bca2d1c16825f109907a23307628a2f0698fbf99662b73a5cf0b020293072b8" in dockerfile
    )
    docker_cli_pinned = "docker-${PI_UNRAID_DOCKER_CLI_VERSION}.tgz" in dockerfile
    compose_pinned = (
        "docker/compose/releases/download/v${PI_UNRAID_DOCKER_COMPOSE_VERSION}" in dockerfile
        and "db1889184726840f75c4f9c001048430d4f25b3be3cb084d3ddd762bc0aed576" in dockerfile
    )
    for name, ok in (
        ("playwright global install", playwright_global),
        ("chromium browser install", chromium_install),
        ("playwright browsers path", browsers_path),
        ("xvfb package", xvfb_present),
        ("xvfb presence check", xvfb_check),
        ("gh pinned install", gh_pinned),
        ("docker cli pinned install", docker_cli_pinned),
        ("docker compose pinned install", compose_pinned),
    ):
        if not ok:
            violations.append(f"{name} missing from Dockerfile")
    # Docker CLI/Compose are accepted tooling, never host control: the
    # runtime shape must not mount the host socket nor publish dev servers.
    socket_mounted = "/var/run/docker.sock" in compose or "/var/run/docker.sock" in dockerfile
    ports_published = re.search(r"(?m)^\s+ports:\s*$", compose) is not None
    if socket_mounted:
        violations.append("host docker socket must not be mounted")
    if ports_published:
        violations.append("no public dev-server ports allowed")
    report = {
        "playwright_module": PLAYWRIGHT_MODULE,
        "playwright_global_install": playwright_global,
        "chromium_install": chromium_install,
        "browsers_path": browsers_path,
        "xvfb": xvfb_present and xvfb_check,
        "gh_pinned": gh_pinned,
        "docker_cli_pinned": docker_cli_pinned,
        "docker_compose_pinned": compose_pinned,
        "socket_mounted": socket_mounted,
        "ports_published": ports_published,
        "automation_profile": AUTOMATION_PROFILE_PATH,
        "automation_downloads": AUTOMATION_DOWNLOADS_PATH,
        "personal_profiles_forbidden": list(PERSONAL_PROFILE_PATHS),
    }
    return report, violations


def check_extension_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    try:
        delivery = (root / "scripts" / "pi_global_capabilities.py").read_text()
        harness = Path(__file__).read_text()
    except OSError as exc:
        return {}, [f"extension policy unreadable: {exc}"]
    scope_policy = '"specpi_scope_policy": "inactive_in_fresh_session"' in delivery
    compat_schema = all(
        key in delivery
        for key in (
            '"specpi_scope_inactive": True',
            '"specpi_improvement_wishlist": True',
            '"mcp_command_surface": True',
        )
    )
    if not scope_policy:
        violations.append("specpi scope policy missing from delivery")
    if not compat_schema:
        violations.append("compatibility smoke schema missing from delivery")
    # This harness must document the M07-T05 wishlist owner and provide no
    # wishlist activation path of its own.
    wishlist_owner = '"need": "specpi_wishlist_activation", "owner": "M07-T05"' in harness
    activation_path = re.search(r"(?im)^.*wishlist.*activat\w*\s*\(", harness) is not None
    if not wishlist_owner:
        violations.append("wishlist M07-T05 deferral missing from harness")
    if activation_path:
        violations.append("harness must not provide a wishlist activation path")
    report = {
        "specpi_scope_policy": "inactive_in_fresh_session" if scope_policy else None,
        "compatibility_schema": compat_schema,
        "wishlist_owner": "M07-T05",
        "wishlist_activation_path": None,
    }
    return report, violations


def build_readback(root: Path) -> dict:
    candidate, candidate_violations = check_candidate_identity(root)
    tooling, tooling_violations = check_browser_tooling(root)
    extension, extension_violations = check_extension_policy(root)
    violations = candidate_violations + tooling_violations + extension_violations
    return {
        "card": CARD_ID,
        "candidate": candidate,
        "browser_tooling": tooling,
        "extension_policy": extension,
        "ha_deferred": list(HA_DEFERRED),
        "violations": violations,
        "full_green_claimed": False,
        "verdict": "technical_green_ha_outstanding" if not violations else "red",
    }


def allowed_fixture_roots() -> list[Path]:
    roots = [Path("/tmp"), Path("/var/tmp")]
    tmpdir = Path(tempfile.gettempdir()).resolve()
    if tmpdir not in roots:
        roots.append(tmpdir)
    return roots


def guard_disposable_scope(scope: str, fixture_root: Path) -> Path:
    if scope != "disposable":
        fail(f"refusing non-disposable scope: {scope}")
    resolved = fixture_root.resolve()
    if not any(
        resolved == base or base in resolved.parents for base in allowed_fixture_roots()
    ):
        fail(f"refusing fixture root outside system temp: {resolved}")
    return resolved


def run_command(argv: list[str], timeout: int = 120, input_text: str | None = None) -> str:
    try:
        completed = subprocess.run(
            argv, input=input_text, capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        fail(f"required command not found: {argv[0]}")
    except subprocess.TimeoutExpired:
        fail(f"command timed out: {' '.join(argv[:4])}")
    if completed.returncode != 0:
        fail(f"command failed ({completed.returncode}): {' '.join(argv[:6])}: {completed.stderr.strip()[:400]}")
    return completed.stdout


def run_command_unchecked(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        fail(f"required command not found: {argv[0]}")
    except subprocess.TimeoutExpired:
        fail(f"command timed out: {' '.join(argv[:4])}")


def docker_available() -> bool:
    return shutil.which("docker") is not None


def docker_run(image: str, run_args: list[str], command: list[str],
               timeout: int = 180, input_text: str | None = None) -> str:
    return run_command(["docker", "run", "--rm", *run_args, image, *command],
                       timeout=timeout, input_text=input_text)


def scan_secret_safe(text: str, context: str) -> None:
    for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"secret-like value leaked into {context}")


def record(phases: list[dict], name: str, status: str, detail: dict) -> None:
    phases.append({"name": name, "status": status, "detail": detail})


def write_failure_report(report_path: Path | None, scope: str, error: str,
                         extra: dict | None = None) -> str | None:
    # Emit a machine-readable failure record without overwriting success.
    # Returns the payload when newly written so callers can also log it.
    # A write failure must never mask the original error: fall back to stderr.
    if report_path is None or report_path.exists():
        return None
    payload = {
        "card": CARD_ID,
        "scope": scope,
        "outcome": "failed",
        "error": error,
        "full_green_claimed": False,
        "production_mutation": False,
    }
    if extra:
        payload.update(extra)
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    try:
        report_path.write_text(text)
    except OSError as exc:
        print(f"paseo browser-tool-compat error: failure report unwritable ({exc}); payload: {text}",
              file=sys.stderr)
        return None
    return text


HEADLESS_JS = (
    f"const {{ chromium }} = require('{PLAYWRIGHT_MODULE}');"
    "(async()=>{"
    "const b=await chromium.launch({headless:true});"
    "console.log('version='+(await b.version()));"
    "const ctx=await b.newContext({acceptDownloads:true});"
    "const p=await ctx.newPage();"
    "await p.setContent('<html><body><h1>m06-t02-headless</h1></body></html>');"
    f"await p.screenshot({{path:'{AUTOMATION_DOWNLOADS_PATH}/headless.png'}});"
    f"await p.pdf({{path:'{AUTOMATION_DOWNLOADS_PATH}/headless.pdf'}});"
    "await b.close();"
    "console.log('capture=ok');"
    "})().catch(e=>{console.error('BROWSER_ERROR:'+e.message);process.exit(1)});"
)

# Headed leg uses a dedicated persistent automation profile and a temp/task
# downloads directory. PDF is headless-only by upstream Playwright design, so
# the headed leg captures screenshot plus a real file download instead.
HEADED_JS = (
    f"const {{ chromium }} = require('{PLAYWRIGHT_MODULE}');"
    "(async()=>{"
    f"const ctx=await chromium.launchPersistentContext('{AUTOMATION_PROFILE_PATH}',"
    "{headless:false,acceptDownloads:true,"
    f"downloadsPath:'{AUTOMATION_DOWNLOADS_PATH}'}});"
    "console.log('version='+(await ctx.browser().version()));"
    "const p=await ctx.newPage();"
    "await p.setContent('<html><body>'"
    "+'<a href=\"data:text/plain,m06-t02-download-probe\" download=\"task-download.txt\">dl</a>'"
    "+'</body></html>');"
    "const [dl]=await Promise.all(["
    "p.waitForEvent('download',{timeout:15000}),p.click('a')]);"
    f"await dl.saveAs('{AUTOMATION_DOWNLOADS_PATH}/'+dl.suggestedFilename());"
    f"await p.screenshot({{path:'{AUTOMATION_DOWNLOADS_PATH}/headed.png'}});"
    "await ctx.close();"
    "console.log('capture=ok');"
    "})().catch(e=>{console.error('BROWSER_ERROR:'+e.message);process.exit(1)});"
)


def container_flags(*mounts: str) -> list[str]:
    flags = ["--user", f"{RUNTIME_UID}:{RUNTIME_GID}", "--shm-size=1gb"]
    for mount in mounts:
        flags.extend(["-v", mount])
    return flags


def chown_fixture(image: str, fixture: Path, *names: str) -> None:
    # Recursive: host-created nested content must transfer to the runtime
    # identity before the container legs run as non-root.
    targets = [f"/fixture/{name}" for name in names]
    run_command(["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "chown",
                 "-v", f"{fixture}:/fixture", image, "-R",
                 f"{RUNTIME_UID}:{RUNTIME_GID}", *targets])


def parse_version_line(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    fail(f"browser version line missing in output: {output.strip()[:300]}")
    raise AssertionError("unreachable")


def phase_image_labels(image: str) -> dict:
    image_id = run_command(["docker", "inspect", "--format={{.Id}}", image]).strip()
    labels_out = run_command(
        ["docker", "inspect", "--format={{json .Config.Labels}}", image]).strip()
    labels = json.loads(labels_out or "{}")
    expected = {
        "io.pi-unraid.candidate-id": CANDIDATE_ID,
        "io.pi-unraid.paseo-version": PASEO_VERSION,
        "io.pi-unraid.pi-version": PI_VERSION,
        "io.pi-unraid.specpi-version": SPECPI_VERSION,
        "io.pi-unraid.pi-mcp-adapter-version": ADAPTER_VERSION,
        "io.pi-unraid.playwright-version": PLAYWRIGHT_VERSION,
    }
    for label, want in expected.items():
        if labels.get(label) != want:
            fail(f"image label {label} mismatch: {labels.get(label)!r}")
    return {"id": image_id, "candidate_id": labels["io.pi-unraid.candidate-id"]}


def phase_browser_headless(image: str, downloads: Path) -> dict:
    out = docker_run(
        image,
        container_flags(f"{downloads}:{AUTOMATION_DOWNLOADS_PATH}"),
        ["node", "-e", HEADLESS_JS],
        timeout=180,
    )
    version = parse_version_line(out, "version=")
    if version != CHROMIUM_VERSION:
        fail(f"headless Chromium version mismatch: {version!r}")
    if "capture=ok" not in out:
        fail(f"headless capture incomplete: {out.strip()[:300]}")
    for name in ("headless.png", "headless.pdf"):
        path = downloads / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"headless artifact missing or empty: {name}")
    return {
        "chromium_version": version,
        "screenshot": "headless.png",
        "pdf": "headless.pdf",
        "pdf_supported": True,
    }


def phase_browser_headed_xvfb(image: str, profile: Path, downloads: Path) -> dict:
    out = docker_run(
        image,
        container_flags(f"{profile}:{AUTOMATION_PROFILE_PATH}",
                        f"{downloads}:{AUTOMATION_DOWNLOADS_PATH}"),
        ["xvfb-run", "-a", "node", "-e", HEADED_JS],
        timeout=240,
    )
    version = parse_version_line(out, "version=")
    if version != CHROMIUM_VERSION:
        fail(f"headed Chromium version mismatch: {version!r}")
    if "capture=ok" not in out:
        fail(f"headed capture incomplete: {out.strip()[:300]}")
    for name in ("headed.png", "task-download.txt"):
        path = downloads / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"headed artifact missing or empty: {name}")
    if (downloads / "task-download.txt").read_text() != "m06-t02-download-probe":
        fail("task download content mismatch")
    return {
        "chromium_version": version,
        "screenshot": "headed.png",
        "download": "task-download.txt",
        "pdf_supported": False,
        "pdf_reason": "upstream-headless-only",
    }


def phase_profile_isolation(image: str, home: Path, profile: Path, downloads: Path) -> dict:
    # The headed leg ran against the dedicated bind-mounted profile. Prove
    # the automation profile is populated, every download landed in the
    # temp/task directory, and no personal profile was touched.
    entries = sorted(path.name for path in profile.iterdir()) if profile.is_dir() else []
    if not entries:
        fail("automation profile directory is empty after headed run")
    if not (profile / "Preferences").is_file():
        fail("automation profile Preferences missing; persistent profile unproven")
    download_files = sorted(path.name for path in downloads.iterdir() if path.is_file())
    expected_downloads = ["headed.png", "headless.pdf", "headless.png", "task-download.txt"]
    if download_files != expected_downloads:
        fail(f"downloads directory mismatch: {download_files}")
    personal_hits = []
    for path in home.rglob("*"):
        rel = path.relative_to(home).as_posix()
        if any(rel == personal or rel.startswith(personal + "/") for personal in PERSONAL_PROFILE_PATHS):
            personal_hits.append(rel)
    if personal_hits:
        fail(f"personal profile paths touched: {personal_hits}")
    out = docker_run(
        image,
        container_flags(f"{home}:/home/paseo"),
        ["sh", "-c", "set -eu; "
         "for d in .config/google-chrome .config/chromium .mozilla .pki; do "
         "if [ -e \"/home/paseo/$d\" ]; then printf 'personal=%s\\n' \"$d\"; fi; done; "
         "printf 'profile_check=done\\n'"],
        timeout=60,
    )
    if "personal=" in out:
        fail(f"container-side personal profile present: {out.strip()[:200]}")
    if "profile_check=done" not in out:
        fail("container-side profile check incomplete")
    return {
        "automation_profile": AUTOMATION_PROFILE_PATH,
        "automation_profile_populated": True,
        "profile_entries": len(entries),
        "downloads": download_files,
        "downloads_path": AUTOMATION_DOWNLOADS_PATH,
        "personal_profiles_touched": [],
    }


def phase_dev_baseline(image: str) -> dict:
    out = docker_run(
        image,
        container_flags(),
        ["bash", "-lc", "set -eu; "
         "printf 'bash=%s\\n' \"$(bash --version | head -n1)\"; "
         "printf 'git=%s\\n' \"$(git --version)\"; "
         "printf 'gcc=%s\\n' \"$(gcc --version | head -n1)\"; "
         "printf 'make=%s\\n' \"$(make --version | head -n1)\"; "
         "printf 'python=%s\\n' \"$(python3 --version)\"; "
         "printf 'node=%s\\n' \"$(node --version)\"; "
         "printf 'network_tools=%s\\n' \"$(command -v dig; command -v getent; command -v nc; command -v ssh; true)\"; "],
        timeout=120,
    )
    values = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    for key in ("bash", "git", "gcc", "make", "python", "node"):
        if not values.get(key):
            fail(f"dev baseline tool missing: {key}")
    if values.get("node") != f"v{NODE_VERSION}":
        fail(f"node version mismatch: {values.get('node')!r}")
    network_tools = (values.get("network_tools") or "").split()
    if len(network_tools) < 4:
        fail(f"network baseline tools missing: {network_tools}")
    return {
        "shell": values["bash"][:80],
        "git": values["git"][:80],
        "build": [values["gcc"][:80], values["make"][:80]],
        "python": values["python"][:80],
        "node": values["node"],
        "network_tools": ["dig", "getent", "nc", "ssh"],
    }


def phase_gh_unauth(image: str) -> dict:
    version_out = docker_run(
        image, container_flags(),
        ["bash", "-lc", "gh --version | head -n1 | awk '{print $3}'"],
        timeout=60,
    ).strip()
    if version_out != GH_VERSION:
        fail(f"gh version mismatch: {version_out!r}")
    # Unauthenticated mechanics only: no login is attempted. `gh auth
    # status` must fail closed proving no credential is present.
    proc = run_command_unchecked(
        ["docker", "run", "--rm", *container_flags(), image,
         "bash", "-lc", "gh auth status 2>&1"],
        timeout=60,
    )
    combined = (proc.stdout + proc.stderr).strip()
    scan_secret_safe(combined, "gh auth status output")
    if proc.returncode == 0:
        fail("gh reports an authenticated session; unauthenticated mechanics unproven")
    if "not logged in" not in combined.lower():
        fail(f"gh fail-closed signal missing: {combined[:300]}")
    return {
        "gh_version": version_out,
        "auth_status_exit": proc.returncode,
        "fail_closed": True,
        "authenticated_workflow_claimed": False,
    }


def phase_docker_tooling(image: str) -> dict:
    out = docker_run(
        image, container_flags(),
        ["bash", "-lc", "set -eu; "
         "printf 'cli=%s\\n' \"$(docker --version)\"; "
         "printf 'compose=%s\\n' \"$(docker compose version --short)\"; "
         "if [ -e /var/run/docker.sock ]; then printf 'socket=present\\n'; "
         "else printf 'socket=absent\\n'; fi"],
        timeout=60,
    )
    values = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    if f"Docker version {DOCKER_CLI_VERSION}," not in values.get("cli", ""):
        fail(f"docker cli version mismatch: {values.get('cli')!r}")
    if values.get("compose") != DOCKER_COMPOSE_VERSION:
        fail(f"docker compose version mismatch: {values.get('compose')!r}")
    if values.get("socket") != "absent":
        fail("host docker socket is visible inside the container")
    # Presence only: with no socket there is no daemon to control. The
    # control call must fail closed.
    proc = run_command_unchecked(
        ["docker", "run", "--rm", *container_flags(), image,
         "bash", "-lc", "docker ps 2>&1"],
        timeout=60,
    )
    if proc.returncode == 0:
        fail("docker control call unexpectedly succeeded without a socket")
    return {
        "docker_cli": values["cli"][:80],
        "docker_compose": values["compose"],
        "socket": "absent",
        "control_fail_closed": True,
        "host_control_claimed": False,
    }


def capability_status(root: Path, image: str, home: Path) -> tuple[int, str]:
    proc = run_command_unchecked(
        ["bash", str(root / "scripts" / "configure-pi-global-capabilities.sh"),
         "status", image, str(home), str(RUNTIME_UID), str(RUNTIME_GID)],
        timeout=180,
    )
    return proc.returncode, proc.stdout


def phase_extension_compat(root: Path, image: str, home: Path) -> dict:
    # Exact-pair SpecPi-core/pi-mcp-adapter compatibility on the exact
    # Paseo/Pi candidate, reusing the proven M04 delivery wrapper. Scope
    # and wishlist stay inactive: installed and smoke-verified, never
    # activated. No live MCP server is configured.
    agent_home = home / ".pi" / "agent"
    agent_home.mkdir(parents=True)
    (agent_home / "settings.json").write_text(json.dumps({
        "theme": "dark",
        "packages": [{"source": "npm:unrelated-example@1.2.3", "autoload": False}],
        "customUnrelated": {"keep": "sentinel"},
    }) + "\n")
    (agent_home / "provider-state.json").write_text('{"providerState":"unchanged"}\n')
    chown_fixture_run = ["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "chown",
                         "-v", f"{home}:/home/paseo", image, "-R",
                         f"{RUNTIME_UID}:{RUNTIME_GID}", "/home/paseo"]
    run_command(chown_fixture_run, timeout=120)

    before_rc, before_out = capability_status(root, image, home)
    if before_rc == 0:
        fail("capability status unexpectedly GREEN before apply")
    before = json.loads(before_out)
    if before.get("state") != "RED" or before.get("compatibility", {}).get("verified") is not False:
        fail(f"pre-apply status not RED-with-missing-smoke: {before_out[:300]}")

    apply_out = run_command(
        ["bash", str(root / "scripts" / "configure-pi-global-capabilities.sh"),
         "apply", image, str(home), str(RUNTIME_UID), str(RUNTIME_GID)],
        timeout=600,
    )
    scan_secret_safe(apply_out, "capability apply output")
    applied = json.loads(apply_out)
    if not (applied.get("changed") is True and applied.get("in_sync") is True):
        fail(f"capability apply not in sync: {apply_out[:300]}")
    if applied.get("compatibility") != {"reason": "none", "state": "GREEN", "verified": True}:
        fail(f"compatibility marker not GREEN: {applied.get('compatibility')}")
    if applied["packages"]["specpi"]["desired_version"] != SPECPI_VERSION:
        fail("specpi desired version mismatch")
    if applied["packages"]["pi_mcp_adapter"]["desired_version"] != ADAPTER_VERSION:
        fail("adapter desired version mismatch")
    if applied.get("specpi_scope_policy") != "inactive_in_fresh_session":
        fail("specpi scope policy mismatch")

    # Wishlist inactive: the compatibility marker schema carries no
    # activation fields, settings hold exactly managed plus unrelated
    # declarations, and this flow performs zero activation mutations.
    marker = json.loads((home / ".pi-unraid" / "global-capabilities" / "compatibility.json").read_text())
    if set(marker) != {"schema_version", "candidate_id", "runtime_pi_version", "packages", "smoke"}:
        fail(f"compatibility marker schema drift: {sorted(marker)}")
    if set(marker["smoke"]) != {"provider_free_rpc", "specpi_scope_inactive",
                                "specpi_improvement_wishlist", "mcp_command_surface"}:
        fail(f"compatibility smoke schema drift: {sorted(marker['smoke'])}")
    settings = json.loads((agent_home / "settings.json").read_text())
    sources = sorted(
        entry.get("source") if isinstance(entry, dict) else entry
        for entry in settings.get("packages", [])
    )
    if sources != [f"npm:pi-mcp-adapter@{ADAPTER_VERSION}",
                   f"npm:specpi@{SPECPI_VERSION}",
                   "npm:unrelated-example@1.2.3"]:
        fail(f"managed settings declarations mismatch: {sources}")
    if settings.get("customUnrelated") != {"keep": "sentinel"}:
        fail("unrelated settings not preserved")

    # Status is read-only: repeated readback changes nothing.
    settings_before = (agent_home / "settings.json").read_bytes()
    after_rc, after_out = capability_status(root, image, home)
    if after_rc != 0:
        fail(f"capability status not GREEN after apply: {after_out[:300]}")
    if (agent_home / "settings.json").read_bytes() != settings_before:
        fail("capability status mutated settings")
    after = json.loads(after_out)
    scan_secret_safe(after_out, "capability status output")
    adapter_config = after.get("adapter_config", {})
    if adapter_config.get("contents_exposed") is not False:
        fail("adapter config readback exposes contents")

    # Adapter failure observability: a bounded missing-package failure
    # reports RED with a machine-readable reason, then restores GREEN.
    adapter = agent_home / "npm" / "node_modules" / "pi-mcp-adapter"
    run_command(["docker", "run", "--rm", "--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                 "--entrypoint", "mv", "-v", f"{home}:/home/paseo", image,
                 "/home/paseo/.pi/agent/npm/node_modules/pi-mcp-adapter",
                 "/home/paseo/.pi/agent/npm/node_modules/pi-mcp-adapter.hold"],
                timeout=120)
    try:
        if adapter.exists():
            fail("adapter hold move did not take effect")
        missing_rc, missing_out = capability_status(root, image, home)
        if missing_rc == 0:
            fail("capability status unexpectedly GREEN with adapter missing")
        scan_secret_safe(missing_out, "capability failure output")
        missing = json.loads(missing_out)
        if missing["packages"]["pi_mcp_adapter"]["state"] != "RED":
            fail("adapter failure not RED")
        failure_reason = missing["packages"]["pi_mcp_adapter"]["reason"]
        if failure_reason != "package_missing_or_invalid":
            fail(f"adapter failure reason mismatch: {failure_reason!r}")
        if (agent_home / "settings.json").read_bytes() != settings_before:
            fail("failure readback mutated settings")
    finally:
        run_command(["docker", "run", "--rm", "--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                     "--entrypoint", "mv", "-v", f"{home}:/home/paseo", image,
                     "/home/paseo/.pi/agent/npm/node_modules/pi-mcp-adapter.hold",
                     "/home/paseo/.pi/agent/npm/node_modules/pi-mcp-adapter"],
                    timeout=120)
    if not adapter.is_dir():
        fail("adapter restore did not take effect")
    restored_rc, restored_out = capability_status(root, image, home)
    if restored_rc != 0 or json.loads(restored_out).get("in_sync") is not True:
        fail(f"capability status not GREEN after restore: {restored_out[:300]}")
    return {
        "specpi_version": SPECPI_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "compatibility": "GREEN",
        "scope": "inactive_in_fresh_session",
        "wishlist_activation_performed": False,
        "wishlist_owner": "M07-T05",
        "adapter_config_state": adapter_config.get("state"),
        "adapter_config_contents_exposed": False,
        "failure_reason_observed": failure_reason,
        "failure_readback_secret_safe": True,
        "restored_green": True,
    }


def disposable_flow(root: Path, image: str, report_path: Path | None) -> dict:
    if not docker_available():
        fail("docker is not available; run the disposable flow on a Docker runner (CI)")
    phases: list[dict] = []
    fixture = Path(tempfile.mkdtemp(prefix="pi-unraid-m06-t02.")).resolve()
    guard_disposable_scope("disposable", fixture)
    try:
        home = fixture / "home"
        profile = fixture / "profile"
        downloads = fixture / "downloads"
        for path in (home, profile, downloads):
            path.mkdir(parents=True)
        record(phases, "fixture", "ok", {"root": str(fixture)})
        chown_fixture(image, fixture, "home", "profile", "downloads")

        image_detail = phase_image_labels(image)
        record(phases, "image_labels", "ok", image_detail)
        # Browser legs run before the extension leg so the profile-isolation
        # scan observes a HOME untouched by capability delivery.
        record(phases, "browser_headless", "ok", phase_browser_headless(image, downloads))
        record(phases, "browser_headed_xvfb", "ok",
               phase_browser_headed_xvfb(image, profile, downloads))
        record(phases, "profile_isolation", "ok",
               phase_profile_isolation(image, home, profile, downloads))
        record(phases, "dev_baseline", "ok", phase_dev_baseline(image))
        record(phases, "gh_unauth", "ok", phase_gh_unauth(image))
        record(phases, "docker_tooling", "ok", phase_docker_tooling(image))
        record(phases, "extension_compat", "ok", phase_extension_compat(root, image, home))

        leftover = run_command(["docker", "ps", "-q", "--filter", f"ancestor={image}"]).strip()
        if leftover:
            fail(f"containers left running: {leftover}")
        report = {
            "card": CARD_ID,
            "scope": "disposable",
            "image": {"ref": image, **image_detail},
            "phases": phases,
            "ha_deferred": list(HA_DEFERRED),
            "full_green_claimed": False,
            "production_mutation": False,
            "outcome": "browser_tool_compat_green",
        }
    finally:
        try:
            run_command(["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "chown",
                         "-v", f"{fixture}:/fixture", image, "-R",
                         f"{os.getuid()}:{os.getgid()}", "/fixture"], timeout=180)
        except SystemExit:
            pass
        shutil.rmtree(fixture, ignore_errors=True)
    if report_path is not None:
        report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M06-T02 browser/tool/extension compatibility harness")
    sub = parser.add_subparsers(dest="action", required=True)
    readback_cmd = sub.add_parser("readback", help="static machine-readable verification")
    readback_cmd.add_argument("--report", type=Path, default=None)
    flow_cmd = sub.add_parser("flow", help="disposable Docker end-to-end flow")
    flow_cmd.add_argument("--scope", required=True, help="must be 'disposable'")
    flow_cmd.add_argument("--image", required=True, help="frozen-candidate image ref")
    flow_cmd.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    if args.action == "readback":
        report = build_readback(root)
        text = json.dumps(report, sort_keys=True, indent=2)
        if args.report is not None:
            args.report.write_text(text + "\n")
        print(text)
        return 0 if report["verdict"] != "red" else 1
    guard_disposable_scope(args.scope, Path(tempfile.gettempdir()))
    try:
        report = disposable_flow(root, args.image, args.report)
    except BaseException as exc:
        written = write_failure_report(args.report, args.scope, str(exc) or "flow failed")
        if written is not None:
            print(written)
        raise
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
