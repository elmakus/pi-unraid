#!/usr/bin/env python3
"""M06-T01 integrated Pi RPC + project workspace flow harness.

readback: machine-readable static verification of the exact frozen candidate,
compose runtime shape, instruction-plane rules, RPC on-demand policy and
autostart config. No Docker, no network, no mutation.

flow: disposable Docker end-to-end of the integrated RPC workspace flow with
session-loss recovery. Requires --scope disposable and a fixture root under a
system temp directory; refuses production scope and production host paths.

Exit is M06 technical GREEN with HA outstanding only; this harness never
claims full GREEN.
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
import time
from pathlib import Path

CARD_ID = "M06-T01"
CANDIDATE_ID = "sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69"
BASE_DIGEST = "sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136"
PASEO_VERSION = "0.9.2"
PI_VERSION = "0.87.1"
RUNTIME_UID = 99
RUNTIME_GID = 100
SHM_BYTES = 1073741824

# HA wave owns every genuinely interactive proof (P4 section 4/M07).
HA_DEFERRED = (
    {"need": "secret_supply", "owner": "M07-T02"},
    {"need": "oauth_device_flow", "owner": "M07-T02"},
    {"need": "account_choice", "owner": "M07-T02"},
    {"need": "two_factor_approval", "owner": "M07-T02"},
    {"need": "manual_login_approval", "owner": "M07-T02"},
    {"need": "real_phone_pairing", "owner": "M07-T02"},
    {"need": "interactive_github_auth", "owner": "M07-T02"},
    {"need": "graphql_credential_materialization", "owner": "M07-T02"},
    {"need": "authenticated_graphql_mutation", "owner": "M07-T02"},
    {"need": "manual_ux_judgment", "owner": "M07-T02"},
    {"need": "production_confirmation", "owner": "M07-T03"},
)

TASK_BOARD_MARKERS = (
    "[[cards]]",
    "execution_status =",
    'status = "in_progress"',
    "review_attempts =",
)

SECRET_VALUE_PATTERN = re.compile(r"(?i)(password|token|api[_-]?key)\s*[:=]\s*[^\s]+")


def fail(message: str):
    raise SystemExit(f"paseo rpc-workspace error: {message}")


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
    if candidate.get("policy", {}).get("build_must_not_reresolve") is not True:
        violations.append("build_must_not_reresolve not enforced")
    dockerfile = (root / "Dockerfile").read_text()
    if f"FROM ghcr.io/getpaseo/paseo@{BASE_DIGEST}" not in dockerfile:
        violations.append("dockerfile base digest mismatch")
    for label, expected in (
        ('io.pi-unraid.candidate-id', CANDIDATE_ID),
        ('io.pi-unraid.paseo-version', PASEO_VERSION),
        ('io.pi-unraid.pi-version', PI_VERSION),
    ):
        if f'{label}="{expected}"' not in dockerfile:
            violations.append(f"dockerfile label {label} mismatch")
    identity = {
        "candidate_id": candidate.get("candidate_id"),
        "paseo_version": paseo.get("version"),
        "pi_version": components.get("pi", {}).get("version"),
        "base_digest": paseo.get("artifact", {}).get("digest"),
        "frozen": candidate.get("policy", {}).get("build_must_not_reresolve") is True,
    }
    return identity, violations


def parse_compose_shape(text: str) -> dict:
    targets = re.findall(r"(?m)^\s+target: (\S+)\s*$", text)
    return {
        "paseo_service": re.search(r"(?m)^  paseo:\s*$", text) is not None,
        "legacy_pi_service": re.search(r"(?m)^  pi:\s*$", text) is not None,
        "targets": targets,
        "create_host_path_false": text.count("create_host_path: false"),
        "user": 'user: "${PASEO_UID:-99}:${PASEO_GID:-100}"' in text,
        "shm_1gb": 'shm_size: "1gb"' in text,
        "restart_unless_stopped": "restart: unless-stopped" in text,
        "logging_json_file": "driver: json-file" in text,
        "log_max_size": 'max-size: "10m"' in text,
        "log_max_file": 'max-file: "3"' in text,
        "forbidden_present": sorted(
            key for key in (
                "cpus:", "mem_limit:", "mem_reservation:", "deploy:",
                "privileged:", "network_mode: host", "/var/run/docker.sock",
            ) if key in text
        ),
        "ports_block": re.search(r"(?m)^\s+ports:\s*$", text) is not None,
        "entrypoint_override": re.search(
            r"(?m)^\s+(entrypoint|command|healthcheck):\s*", text) is not None,
        "secrets_block": re.search(r"(?m)^\s+secrets:\s*$", text) is not None,
        "rpc_wiring": "rpc" in text.lower(),
    }


def check_compose_shape(shape: dict) -> list[str]:
    violations: list[str] = []
    if not shape["paseo_service"]:
        violations.append("paseo service missing")
    if shape["legacy_pi_service"]:
        violations.append("legacy pi service still present")
    if shape["targets"] != ["/home/paseo", "/projects", "/worktrees"]:
        violations.append(f"intended roots violated: {shape['targets']}")
    if shape["create_host_path_false"] != 3:
        violations.append("host-path creation must stay explicit on all binds")
    if not shape["user"]:
        violations.append("upstream user mapping missing")
    if not shape["shm_1gb"]:
        violations.append("1 GiB shared memory missing")
    if not shape["restart_unless_stopped"]:
        violations.append("autostart restart policy missing")
    if not (shape["logging_json_file"] and shape["log_max_size"] and shape["log_max_file"]):
        violations.append("bounded log rotation missing")
    if shape["forbidden_present"]:
        violations.append(f"forbidden runtime keys: {shape['forbidden_present']}")
    if shape["ports_block"] or shape["entrypoint_override"] or shape["secrets_block"]:
        violations.append("ports/entrypoint/secrets override present")
    if shape["rpc_wiring"]:
        violations.append("permanent RPC wiring must not exist in compose")
    return violations


def check_instruction_plane(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    source = root / "config" / "pi-agent"
    try:
        agents = (source / "AGENTS.md").read_text()
    except OSError as exc:
        return {}, [f"AGENTS.md unreadable: {exc}"]
    for required in (
        "Managed project selection is user-driven",
        "Do not infer or bind",
        "before any managed mutation",
        "Do not create a second Task Board",
    ):
        if required not in agents:
            violations.append(f"instruction rule missing: {required}")
    skills = {
        "project-recovery": source / "skills" / "project-recovery" / "SKILL.md",
        "recovery-bootstrap": source / "skills" / "project-recovery" / "references" / "bootstrap.md",
        "unraid-admin": source / "skills" / "unraid-admin" / "SKILL.md",
    }
    for name, path in skills.items():
        if not path.is_file():
            violations.append(f"skill missing: {name}")
    bootstrap = skills["recovery-bootstrap"].read_text() if skills["recovery-bootstrap"].is_file() else ""
    for required in ("current default branch", "Do not reconstruct missing workflow policy"):
        if required not in bootstrap:
            violations.append(f"recovery bootstrap rule missing: {required}")
    installer = (root / "scripts" / "pi_instruction_plane.py").read_text()
    if 'choices=("apply", "rollback", "status")' not in installer:
        violations.append("instruction installer actions missing")
    corpus = "\n".join(p.read_text() for p in source.rglob("*") if p.is_file())
    for marker in TASK_BOARD_MARKERS:
        if marker in corpus:
            violations.append(f"workflow-state duplication marker: {marker}")
    if SECRET_VALUE_PATTERN.search(corpus):
        violations.append("secret-valued assignment in instruction corpus")
    report = {
        "explicit_selection": "Managed project selection is user-driven" in agents,
        "no_inference": "Do not infer or bind" in agents,
        "recovery_before_mutation": "before any managed mutation" in agents,
        "no_second_board": all(m not in corpus for m in TASK_BOARD_MARKERS),
        "skills": sorted(name for name, path in skills.items() if path.is_file()),
    }
    return report, violations


def check_rpc_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    smoke = (root / "scripts" / "verify-pi-instruction-plane.sh").read_text()
    on_demand = "pi --mode rpc --no-session" in smoke
    if not on_demand:
        violations.append("on-demand RPC probe missing from smoke")
    compose = (root / "compose.yaml").read_text()
    if "rpc" in compose.lower():
        violations.append("compose must not wire a permanent RPC process")
    # Absence of an RPC process without a session is not a failure: nothing in
    # the runtime shape requires a long-lived RPC listener.
    report = {
        "on_demand_mechanism": "pi --mode rpc --no-session",
        "on_demand_proven_by_smoke": on_demand,
        "permanent_rpc_required": False,
        "absence_without_session_is_failure": False,
    }
    return report, violations


def check_autostart(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    compose = (root / "compose.yaml").read_text()
    configured = "restart: unless-stopped" in compose
    if not configured:
        violations.append("autostart restart policy missing from compose")
    # Validation is static and read-only: this harness provides no flag or
    # path that enables production autostart. M07 owns production cutover.
    report = {
        "restart_policy": "unless-stopped" if configured else None,
        "config_validated": configured,
        "production_autostart_enabled": False,
        "production_enablement_path": None,
    }
    return report, violations


def build_readback(root: Path) -> dict:
    candidate, candidate_violations = check_candidate_identity(root)
    compose_text = (root / "compose.yaml").read_text()
    shape = parse_compose_shape(compose_text)
    compose_violations = check_compose_shape(shape)
    instruction, instruction_violations = check_instruction_plane(root)
    rpc, rpc_violations = check_rpc_policy(root)
    autostart, autostart_violations = check_autostart(root)
    violations = (
        candidate_violations + compose_violations + instruction_violations
        + rpc_violations + autostart_violations
    )
    return {
        "card": CARD_ID,
        "candidate": candidate,
        "runtime": {
            "targets": shape["targets"],
            "explicit_host_paths": shape["create_host_path_false"] == 3,
            "upstream_user_mapping": shape["user"],
            "shm_1gb": shape["shm_1gb"],
            "no_cpu_ram_caps": not shape["forbidden_present"],
            "bounded_logs": shape["log_max_size"] and shape["log_max_file"],
            "no_ports_entrypoint_secrets": not (
                shape["ports_block"] or shape["entrypoint_override"] or shape["secrets_block"]
            ),
        },
        "instruction_plane": instruction,
        "rpc": rpc,
        "autostart": autostart,
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


def docker_available() -> bool:
    return shutil.which("docker") is not None


def docker_run(image: str, run_args: list[str], command: list[str],
             timeout: int = 180, input_text: str | None = None) -> str:
    return run_command(["docker", "run", "--rm", *run_args, image, *command],
                       timeout=timeout, input_text=input_text)


def chown_fixture(image: str, fixture: Path) -> str:
    # Recursive: host-created nested content (notably the fixture .git)
    # must transfer to the runtime identity, otherwise container git fails
    # with dubious ownership. No safe.directory workaround is used.
    return run_command(["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "chown",
                        "-v", f"{fixture}:/fixture", image, "-R",
                        f"{RUNTIME_UID}:{RUNTIME_GID}",
                        "/fixture/home", "/fixture/projects", "/fixture/worktrees"])


def nested_ownership_snippet() -> str:
    # Live guard: any nested path outside the runtime identity fails the
    # readback. Appended to the workspace readback probe script.
    return (
        f"printf 'foreign=%s\\n' \"$(find /home/paseo /projects /worktrees "
        f"\\( -not -user {RUNTIME_UID} -o -not -group {RUNTIME_GID} \\) -print "
        "2>/dev/null | head -5 | tr '\\n' ';')\"; "
    )


FIXTURE_PROJECT = "m06-t01-fixture-project"
FIXTURE_BOARD_PATH = "implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml"
FIXTURE_BOARD_REVISION = 96


def fixture_project_text() -> str:
    return (
        "# M06-T01 durable fixture project\n"
        "\n"
        f"project: {FIXTURE_PROJECT}\n"
        "selection: explicit-user-selection\n"
        "selection_rule: conversational inference alone never binds a project\n"
    )


def fixture_state_text() -> str:
    return json.dumps({
        "project": FIXTURE_PROJECT,
        "selection": {"method": "explicit", "source": "user"},
        "board": {"path": FIXTURE_BOARD_PATH, "revision": FIXTURE_BOARD_REVISION},
        "authority": [
            "requirements/PASEO_GUI_RUNTIME.md",
            "planning/PASEO_GUI_RUNTIME_P4.md",
        ],
    }, sort_keys=True, indent=2) + "\n"


def verify_recovered_state(*, head_before: str, head_after: str, status_porcelain: str,
                           state_json_text: str, project_text: str,
                           sessions_absent: bool) -> dict:
    # Recovery must re-derive canonical state from durable Git object content
    # after session loss. Anything else fails: live sessions present (could
    # leak session text into recovery), HEAD drift, dirty worktree, or
    # absent/corrupt/tampered canonical content.
    if not sessions_absent:
        fail("recovery observed live session state; session independence unproven")
    if not head_after or head_after != head_before:
        fail("durable git HEAD changed or unreadable across session loss")
    if status_porcelain.strip():
        fail(f"durable worktree not clean: {status_porcelain.strip()[:200]}")
    try:
        state = json.loads(state_json_text)
    except ValueError:
        fail("canonical state absent or corrupt (not valid JSON)")
    if not isinstance(state, dict) or state.get("project") != FIXTURE_PROJECT:
        fail("canonical project identity mismatch")
    if state.get("selection", {}).get("method") != "explicit":
        fail("canonical selection is not explicit")
    board = state.get("board", {})
    if board.get("path") != FIXTURE_BOARD_PATH or board.get("revision") != FIXTURE_BOARD_REVISION:
        fail("canonical board locator mismatch")
    if FIXTURE_PROJECT not in project_text or "explicit" not in project_text.lower():
        fail("canonical project file mismatch")
    return {
        "project": FIXTURE_PROJECT,
        "selection_method": "explicit",
        "board": {"path": FIXTURE_BOARD_PATH, "revision": FIXTURE_BOARD_REVISION},
        "sessions_absent": True,
    }


def write_failure_report(report_path: Path | None, scope: str, error: str) -> None:
    # Emit a machine-readable failure record without overwriting success.
    if report_path is None or report_path.exists():
        return
    report_path.write_text(json.dumps({
        "card": CARD_ID,
        "scope": scope,
        "outcome": "failed",
        "error": error,
        "full_green_claimed": False,
        "production_mutation": False,
    }, sort_keys=True, indent=2) + "\n")


def record(phases: list[dict], name: str, status: str, detail: dict) -> None:
    phases.append({"name": name, "status": status, "detail": detail})


def disposable_flow(root: Path, image: str, report_path: Path | None) -> dict:
    if not docker_available():
        fail("docker is not available; run the disposable flow on a Docker runner (CI)")
    phases: list[dict] = []
    fixture = Path(tempfile.mkdtemp(prefix="pi-unraid-m06-t01.")).resolve()
    guard_disposable_scope("disposable", fixture)
    try:
        home = fixture / "home"
        projects = fixture / "projects"
        worktrees = fixture / "worktrees"
        for path in (home, projects, worktrees):
            path.mkdir(parents=True)
        # Canonical durable state: a fixture git repository under /projects.
        # Recovery after session loss re-reads this durable state; session
        # content is never replayed.
        repo = projects / "m06-t01-fixture"
        run_command(["git", "init", "-b", "main", str(repo)])
        (repo / "PROJECT.md").write_text(fixture_project_text())
        (repo / "canonical-state.json").write_text(fixture_state_text())
        run_command(["git", "-C", str(repo), "add", "-A"])
        run_command(["git", "-C", str(repo), "-c", "user.name=m06-t01",
                     "-c", "user.email=m06-t01@example.invalid",
                     "commit", "-q", "-m", "durable fixture"])
        head_before = run_command(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
        status_before = run_command(["git", "-C", str(repo), "status", "--porcelain"]).strip()
        if status_before:
            fail(f"fixture worktree not clean after commit: {status_before[:200]}")
        record(phases, "fixture", "ok", {"root": str(fixture), "durable_head": head_before})
        chown_fixture(image, fixture)
        run_command(["bash", str(root / "scripts" / "configure-paseo-runtime.sh"),
                     image, str(home), str(worktrees), str(RUNTIME_UID), str(RUNTIME_GID)])
        apply_out = run_command(["bash", str(root / "scripts" / "configure-pi-instruction-plane.sh"),
                                 "apply", image, str(home), str(RUNTIME_UID), str(RUNTIME_GID)])
        apply = json.loads(apply_out)
        if not apply.get("in_sync"):
            fail(f"instruction-plane apply not in sync: {apply}")
        record(phases, "configure", "ok", {"instruction_in_sync": True})

        # On-demand RPC: two fresh provider-free processes across the
        # recreation boundary; each exits, none persists.
        rpc_flags = ["-i", "--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                     "-v", f"{home}:/home/paseo", "--shm-size=1gb"]
        rpc_cmd = ["pi", "--mode", "rpc", "--no-session"]
        first_raw = docker_run(
            image, rpc_flags, rpc_cmd,
            input_text=json.dumps({"id": "m06-t01-first", "type": "get_state"}) + "\n",
        )
        first = validate_rpc_response(first_raw, "m06-t01-first")
        second_raw = docker_run(
            image, rpc_flags, rpc_cmd,
            input_text=json.dumps({"id": "m06-t01-second", "type": "get_state"}) + "\n",
        )
        second = validate_rpc_response(second_raw, "m06-t01-second")
        lingering = run_command(["docker", "ps", "-q", "--filter", f"ancestor={image}"]).strip()
        if lingering:
            fail(f"permanent RPC container left running: {lingering}")
        record(phases, "rpc_on_demand", "ok",
               {"first_success": first, "second_success": second, "lingering_containers": []})

        before = workspace_readback(image, home, projects, worktrees)
        record(phases, "workspace_readback_before", "ok", before)

        # Session-loss simulation: representative session state is created,
        # then destroyed. Managed instructions must survive; recovery must
        # re-derive project state from durable Git, never from session text.
        home_flags = ["--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                      "-v", f"{home}:/home/paseo", "--shm-size=1gb"]
        docker_run(image, home_flags,
                   ["sh", "-c",
                    "set -eu; mkdir -p /home/paseo/.pi/agent/sessions/m06-t01-probe; "
                    "printf '%s' '{\"id\":\"m06-t01-probe\"}' > "
                    "/home/paseo/.pi/agent/sessions/m06-t01-probe/session.jsonl"])
        docker_run(image, home_flags,
                   ["sh", "-c", "set -eu; rm -rf /home/paseo/.pi/agent/sessions"])
        managed_ok = (
            (home / ".pi" / "agent" / "AGENTS.md").read_bytes()
            == (root / "config" / "pi-agent" / "AGENTS.md").read_bytes()
        )
        if not managed_ok:
            fail("managed instruction plane did not survive session loss")
        status_out = run_command(["bash", str(root / "scripts" / "configure-pi-instruction-plane.sh"),
                                  "status", image, str(home), str(RUNTIME_UID), str(RUNTIME_GID)])
        if not json.loads(status_out).get("in_sync"):
            fail("instruction-plane status not in sync after session loss")
        board_hits = []
        for path in sorted(home.rglob("*")):
            if path.is_file():
                try:
                    text = path.read_text()
                except (OSError, ValueError):
                    continue
                if any(marker in text for marker in TASK_BOARD_MARKERS):
                    board_hits.append(path.relative_to(home).as_posix())
        if board_hits:
            fail(f"second task-board markers in HOME: {board_hits}")
        record(phases, "session_loss", "ok",
               {"managed_instructions_intact": True, "instruction_in_sync": True,
                "second_board_markers": []})

        projects_ro = ["--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                       "-v", f"{projects}:/projects:ro", "--shm-size=1gb"]
        recovered_head = docker_run(
            image, projects_ro,
            ["git", "-C", "/projects/m06-t01-fixture", "rev-parse", "HEAD"]).strip()
        recovered_status = docker_run(
            image, projects_ro,
            ["git", "-C", "/projects/m06-t01-fixture", "status", "--porcelain"]).strip()
        # Read canonical content from the Git object store (HEAD), not from
        # the worktree, so recovery provably uses durable state.
        recovered_state = docker_run(
            image, projects_ro,
            ["git", "-C", "/projects/m06-t01-fixture", "show", "HEAD:canonical-state.json"])
        recovered_project = docker_run(
            image, projects_ro,
            ["git", "-C", "/projects/m06-t01-fixture", "show", "HEAD:PROJECT.md"])
        sessions_probe = docker_run(
            image, home_flags,
            ["sh", "-c", "if [ -e /home/paseo/.pi/agent/sessions ]; then "
                         "printf 'sessions=present'; else printf 'sessions=absent'; fi"])
        recovered = verify_recovered_state(
            head_before=head_before,
            head_after=recovered_head,
            status_porcelain=recovered_status,
            state_json_text=recovered_state,
            project_text=recovered_project,
            sessions_absent="sessions=absent" in sessions_probe,
        )
        after = workspace_readback(image, home, projects, worktrees)
        record(phases, "recovery", "ok",
               {"durable_head": recovered_head, "worktree_clean": True,
                "project": recovered["project"],
                "selection_method": recovered["selection_method"],
                "board": recovered["board"],
                "sessions_absent": True,
                "decision": "recovered_from_durable_git_no_replay"})
        record(phases, "workspace_readback_after", "ok", after)

        image_id = run_command(["docker", "inspect", "--format={{.Id}}", image]).strip()
        labels_out = run_command(
            ["docker", "inspect", "--format={{json .Config.Labels}}", image]).strip()
        labels = json.loads(labels_out or "{}")
        if labels.get("io.pi-unraid.candidate-id") != CANDIDATE_ID:
            fail("image candidate label mismatch")
        leftover = run_command(["docker", "ps", "-q", "--filter", f"ancestor={image}"]).strip()
        if leftover:
            fail(f"containers left running: {leftover}")
        report = {
            "card": CARD_ID,
            "scope": "disposable",
            "image": {"ref": image, "id": image_id, "candidate_id": labels.get("io.pi-unraid.candidate-id")},
            "phases": phases,
            "ha_deferred": list(HA_DEFERRED),
            "full_green_claimed": False,
            "production_mutation": False,
            "outcome": "integrated_flow_green",
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


def validate_rpc_response(raw: str, probe_id: str) -> bool:
    records = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    match = [r for r in records
             if r.get("id") == probe_id and r.get("type") == "response"
             and r.get("command") == "get_state"]
    if not match or match[0].get("success") is not True:
        fail(f"RPC probe {probe_id} unsuccessful: {raw.strip()[:400]}")
    return True


def check_nested_ownership(image: str, home: Path, projects: Path, worktrees: Path) -> None:
    out = docker_run(
        image, ["--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                "-v", f"{home}:/home/paseo", "-v", f"{projects}:/projects",
                "-v", f"{worktrees}:/worktrees", "--shm-size=1gb"],
        ["sh", "-c", "set -eu; " + nested_ownership_snippet()])
    for line in out.splitlines():
        if line.startswith("foreign=") and line[len("foreign="):]:
            fail(f"foreign-owned nested content: {line[len('foreign='):]!r}")


def workspace_readback(image: str, home: Path, projects: Path, worktrees: Path) -> dict:
    out = docker_run(
        image, ["--user", f"{RUNTIME_UID}:{RUNTIME_GID}",
                "-v", f"{home}:/home/paseo", "-v", f"{projects}:/projects",
                "-v", f"{worktrees}:/worktrees", "--shm-size=1gb"],
        ["sh", "-c",
         "set -eu; "
                "printf 'uid=%s\\n' \"$(id -u):$(id -g)\"; "
                "printf 'shm=%s\\n' \"$(df -B1 /dev/shm | awk 'NR==2{print $2}')\"; "
                "printf 'home=%s\\n' \"$(stat -c '%u:%g' /home/paseo)\"; "
                "printf 'projects=%s\\n' \"$(stat -c '%u:%g' /projects)\"; "
                "printf 'worktrees=%s\\n' \"$(stat -c '%u:%g' /worktrees)\"; "
                "printf 'worktrees_root=%s\\n' \"$(python3 -c 'import json;print(json.load(open(\"/home/paseo/.paseo/config.json\"))[\"worktrees\"][\"root\"])')\"; "
                "printf 'mounts=%s\\n' \"$(grep -c -e ' /projects ' -e ' /worktrees ' /proc/mounts || true)\""])
    values = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    uid = values.get("uid", "")
    if uid != f"{RUNTIME_UID}:{RUNTIME_GID}":
        fail(f"runtime identity mismatch: {uid}")
    if uid.startswith("0:"):
        fail("runtime must stay non-root")
    try:
        shm = int(values.get("shm", "0"))
    except ValueError:
        fail(f"unreadable shm size: {values.get('shm')}")
    if shm != SHM_BYTES:
        fail(f"shm size mismatch: {shm}")
    for key in ("home", "projects", "worktrees"):
        if values.get(key) != f"{RUNTIME_UID}:{RUNTIME_GID}":
            fail(f"ownership mismatch on {key}: {values.get(key)}")
    if values.get("worktrees_root") != "/worktrees":
        fail(f"worktrees root mismatch: {values.get('worktrees_root')}")
    try:
        mounts = int(values.get("mounts", "0"))
    except ValueError:
        fail(f"unreadable mount count: {values.get('mounts')}")
    if mounts < 2:
        fail(f"workspace mounts missing: {mounts}")
    host_stats = {
        key: f"{(fixture).stat().st_uid}:{(fixture).stat().st_gid}"
        for key, fixture in (("home", home), ("projects", projects), ("worktrees", worktrees))
    }
    for key, observed in host_stats.items():
        if observed != f"{RUNTIME_UID}:{RUNTIME_GID}":
            fail(f"host-visible ownership mismatch on {key}: {observed}")
    check_nested_ownership(image, home, projects, worktrees)
    return {
        "runtime_uid_gid": uid,
        "non_root": True,
        "shm_bytes": shm,
        "ownership": values["home"],
        "host_ownership": host_stats,
        "worktrees_root": values.get("worktrees_root"),
        "workspace_mounts": mounts,
        "nested_ownership_ok": True,
    }


SPAWN_BLOCK_PATTERNS = (
    ("relay_disabled", ("relay_disabled",)),
    ("onboarding", ("onboard",)),
    ("auth", ("unauthorized", "401", "403", "forbidden", "login", "credential",
              "api key", "apikey", "token", "password")),
)


def classify_spawn_blocker(text: str) -> str | None:
    lowered = text.lower()
    for gate, markers in SPAWN_BLOCK_PATTERNS:
        if any(marker in lowered for marker in markers):
            return gate
    return None


def check_pi_diagnostic(output: str) -> bool:
    return "pi" in output.lower() and PI_VERSION in output


def find_pi_child(ps_text: str) -> dict | None:
    for line in ps_text.splitlines():
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        pid, ppid, args = parts
        if "pi --mode rpc" in args and "[p]i --mode rpc" not in args:
            return {"pid": pid, "ppid": ppid, "args": args}
    return None


def paseo_spawn_probe(root: Path, image: str, report_path: Path | None) -> dict:
    # True Paseo-to-Pi integration: drive the frozen v0.9.2 daemon CLI
    # (provider diagnostic pi, then run --provider pi) and observe a pi
    # --mode rpc child spawned by the daemon worker. Secret-free and
    # disposable; any auth/onboarding gate fails loudly as PASEO_SPAWN_BLOCKED
    # instead of being inferred around.
    if not docker_available():
        fail("docker is not available; run the Paseo spawn probe on a Docker runner (CI)")
    phases: list[dict] = []
    fixture = Path(tempfile.mkdtemp(prefix="pi-unraid-m06-t01-spawn.")).resolve()
    guard_disposable_scope("disposable", fixture)
    project = f"piunraid-m06-t01-spawn-{os.getpid()}"
    home = fixture / "home"
    projects = fixture / "projects"
    worktrees = fixture / "worktrees"
    paseo_home = "/home/paseo/.paseo"
    saved_env = dict(os.environ)
    os.environ.update({
        "PASEO_UID": str(RUNTIME_UID),
        "PASEO_GID": str(RUNTIME_GID),
        "PASEO_HOME_HOST": str(home),
        "PASEO_PROJECTS_HOST": str(projects),
        "PASEO_WORKTREES_HOST": str(worktrees),
    })

    def dc(*args: str, timeout: int = 120) -> str:
        return run_command(
            ["docker", "compose", "-p", project, "-f", str(root / "compose.yaml"),
             "-f", str(fixture / "compose.fixture.yaml"), *args],
            timeout=timeout,
        )

    try:
        for path in (home, projects, worktrees):
            path.mkdir(parents=True)
        chown_fixture(image, fixture)
        run_command(["bash", str(root / "scripts" / "configure-paseo-runtime.sh"),
                     image, str(home), str(worktrees), str(RUNTIME_UID), str(RUNTIME_GID)])
        record(phases, "fixture", "ok", {"root": str(fixture)})
        (fixture / "compose.fixture.yaml").write_text(
            "services:\n  paseo:\n    image: " + image + "\n    build: null\n    restart: \"no\"\n"
        )
        dc("config")
        dc("up", "-d")
        cid = dc("ps", "-q", "paseo").strip()
        if not cid:
            fail("paseo service did not start")
        health_check = (
            "const http=require('http');"
            "const req=http.get({hostname:'127.0.0.1',port:6767,path:'/api/health'},"
            "r=>process.exit(r.statusCode===200?0:1));"
            "req.on('error',()=>process.exit(1));"
            "req.setTimeout(1500,()=>{req.destroy();process.exit(1)});"
        )
        deadline = time.monotonic() + 60
        healthy = False
        while time.monotonic() < deadline:
            try:
                run_command(["docker", "exec", cid, "node", "-e", health_check], timeout=10)
                healthy = True
                break
            except SystemExit:
                time.sleep(2)
        if not healthy:
            fail("paseo daemon /api/health did not become ready")
        record(phases, "daemon_up", "ok", {"container": cid[:12]})

        diagnostic = run_command(
            ["docker", "exec", "-u", f"{RUNTIME_UID}:{RUNTIME_GID}", cid,
             "paseo", "--home", paseo_home, "provider", "diagnostic", "pi", "--json"],
            timeout=120,
        )
        if not check_pi_diagnostic(diagnostic):
            fail(f"pi provider diagnostic did not resolve frozen pi: {diagnostic.strip()[:400]}")
        record(phases, "diagnostic", "ok", {"pi_version_resolved": PI_VERSION})

        try:
            run_out = run_command(
                ["docker", "exec", "-u", f"{RUNTIME_UID}:{RUNTIME_GID}", "-w", "/projects", cid,
                 "paseo", "--home", paseo_home,
                 "run", "--provider", "pi", "--background",
                 "Reply with exactly: M06-T01-SPAWN-PROBE"],
                timeout=180,
            )
        except SystemExit as exc:
            gate = classify_spawn_blocker(str(exc))
            if gate is not None:
                fail(f"PASEO_SPAWN_BLOCKED:{gate}: {str(exc)[:300]}")
            raise
        agent_id = parse_agent_id(run_out)
        spawn: dict | None = None
        poll_deadline = time.monotonic() + 90
        while time.monotonic() < poll_deadline:
            ps_out = run_command(
                ["docker", "exec", cid, "sh", "-c",
                 "ps -eo pid,ppid,args | grep '[p]i --mode rpc' || true"],
                timeout=30,
            )
            spawn = find_pi_child(ps_out)
            if spawn is not None:
                break
            time.sleep(1)
        if spawn is None:
            fail("no pi --mode rpc child spawned by the Paseo daemon within the poll window; "
                 "Paseo-driven launch unproven (direct pi CLI leg is separate evidence)")
        ppid_comm = run_command(
            ["docker", "exec", cid, "ps", "-o", "comm=", "-p", spawn["ppid"]],
            timeout=30,
        ).strip().lower()
        if "node" not in ppid_comm and "paseo" not in ppid_comm:
            fail(f"pi RPC parent is not the daemon worker: pid={spawn['pid']} "
                 f"ppid={spawn['ppid']} comm={ppid_comm!r}")
        record(phases, "spawn_observed", "ok",
               {"pid": spawn["pid"], "ppid": spawn["ppid"], "ppid_comm": ppid_comm,
                "agent_id": agent_id})
        if agent_id is not None:
            try:
                run_command(
                    ["docker", "exec", "-u", f"{RUNTIME_UID}:{RUNTIME_GID}", cid,
                     "paseo", "--home", paseo_home, "stop", agent_id],
                    timeout=60,
                )
            except SystemExit:
                pass
        dc("down", "-v")
        report = {
            "card": CARD_ID,
            "scope": "disposable",
            "image": {"ref": image},
            "phases": phases,
            "spawn": {"observed": True, "pid": spawn["pid"], "ppid": spawn["ppid"],
                      "ppid_comm": ppid_comm},
            "ha_deferred": list(HA_DEFERRED),
            "full_green_claimed": False,
            "production_mutation": False,
            "outcome": "paseo_spawn_green",
        }
    finally:
        try:
            run_command(
                ["docker", "compose", "-p", project, "-f", str(root / "compose.yaml"),
                 "-f", str(fixture / "compose.fixture.yaml"), "down", "-v"],
                timeout=120,
            )
        except SystemExit:
            pass
        os.environ.clear()
        os.environ.update(saved_env)
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


def parse_agent_id(run_output: str) -> str | None:
    stripped = run_output.strip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            for key in ("id", "agentId", "agent_id"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
    match = re.search(r'"id"\s*:\s*"([^"]+)"', run_output)
    if match:
        return match.group(1)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M06-T01 RPC + workspace flow harness")
    sub = parser.add_subparsers(dest="action", required=True)
    readback_cmd = sub.add_parser("readback", help="static machine-readable verification")
    readback_cmd.add_argument("--report", type=Path, default=None)
    flow_cmd = sub.add_parser("flow", help="disposable Docker end-to-end flow")
    flow_cmd.add_argument("--scope", required=True, help="must be 'disposable'")
    flow_cmd.add_argument("--image", required=True, help="frozen-candidate image ref")
    flow_cmd.add_argument("--report", type=Path, default=None)
    spawn_cmd = sub.add_parser("paseo-spawn", help="disposable Paseo-driven Pi spawn probe")
    spawn_cmd.add_argument("--scope", required=True, help="must be 'disposable'")
    spawn_cmd.add_argument("--image", required=True, help="frozen-candidate image ref")
    spawn_cmd.add_argument("--report", type=Path, default=None)
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
        if args.action == "paseo-spawn":
            report = paseo_spawn_probe(root, args.image, args.report)
        else:
            report = disposable_flow(root, args.image, args.report)
    except SystemExit as exc:
        write_failure_report(args.report, args.scope, str(exc) or "flow failed")
        raise
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
