#!/usr/bin/env python3
"""M06-T03 automatic Relay/persistence/capability/doctor readiness harness.

readback: machine-readable static verification of the exact frozen candidate,
Relay default-disabled/consent/revocation policy, zero-port/secret-safe
runtime shape, inventory desired-state authority, reconcile/doctor semantics,
lightweight healthcheck wiring and bounded auth-health fingerprints. No
Docker, no network, no mutation.

flow: disposable Docker end-to-end of the integrated Relay/persistence/
capability/doctor readiness flow on the exact frozen candidate image.
Requires --scope disposable and a fixture root under a system temp
directory; refuses production scope and production host paths.

Exit is one M06 technical slice GREEN with M06-T04 and HA outstanding
only; this harness never claims full GREEN, never pairs a real phone,
never materializes live credentials and never performs wishlist
activation, authenticated mutation or production mutation.
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

CARD_ID = "M06-T03"
CANDIDATE_ID = "sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69"
BASE_DIGEST = "sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136"
PASEO_VERSION = "0.9.2"
PI_VERSION = "0.87.1"
RUNTIME_UID = 99
RUNTIME_GID = 100
SHM_BYTES = 1073741824
HEALTH_PORT = 6767
HEALTH_PATH = "/api/health"

# Genuinely interactive or post-deploy proofs this Card must not claim.
# Real phone pairing plus first credential/authenticated proof belongs to the
# HA wave (P4 section 4/M07); pairing-material transfer to production is
# witnessed in M07-T03; wishlist activation is conditional M07-T05.
HA_DEFERRED = (
    {"need": "real_phone_pairing", "owner": "M07-T02"},
    {"need": "pairing_transfer_ux", "owner": "M07-T03"},
    {"need": "secret_supply", "owner": "M07-T02"},
    {"need": "oauth_device_flow", "owner": "M07-T02"},
    {"need": "account_choice", "owner": "M07-T02"},
    {"need": "two_factor_approval", "owner": "M07-T02"},
    {"need": "manual_login_approval", "owner": "M07-T02"},
    {"need": "interactive_github_auth", "owner": "M07-T02"},
    {"need": "authenticated_github_workflow", "owner": "M07-T02"},
    {"need": "graphql_credential_materialization", "owner": "M07-T02"},
    {"need": "authenticated_graphql_mutation", "owner": "M07-T02"},
    {"need": "manual_ux_judgment", "owner": "M07-T02"},
    {"need": "specpi_wishlist_activation", "owner": "M07-T05"},
    {"need": "production_confirmation", "owner": "M07-T03"},
)

SECRET_ENV_TOKENS = (
    "PASEO_PASSWORD",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
    "MUSE_API_KEY",
    "CODEX_API_KEY",
)

HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def fail(message: str):
    raise SystemExit(f"paseo relay-doctor-readiness error: {message}")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_scripts():
    """Import the repo inventory/control modules without polluting sys.path."""
    import importlib.util

    scripts = repo_root() / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    inv_spec = importlib.util.spec_from_file_location(
        "m06t03_inventory", scripts / "environment_capability_inventory.py"
    )
    inv = importlib.util.module_from_spec(inv_spec)
    assert inv_spec.loader is not None
    inv_spec.loader.exec_module(inv)
    sys.modules["environment_capability_inventory"] = inv
    ctl_spec = importlib.util.spec_from_file_location(
        "m06t03_control", scripts / "environment_capability_control.py"
    )
    ctl = importlib.util.module_from_spec(ctl_spec)
    assert ctl_spec.loader is not None
    ctl_spec.loader.exec_module(ctl)
    return inv, ctl


def check_candidate_identity(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    try:
        candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
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


def check_relay_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    try:
        configure = (root / "scripts" / "configure-paseo-runtime.sh").read_text()
        access = (root / "scripts" / "paseo-relay-access.sh").read_text()
        smoke = (root / "scripts" / "verify-compose-foundation.sh").read_text()
        doc = (root / "docs" / "PASEO_RELAY_AUTH.md").read_text()
    except OSError as exc:
        return {}, [f"relay policy source unreadable: {exc}"]
    # Default-disabled at configure time.
    if "paseo daemon config set daemon.relay.enabled false --home /home/paseo/.paseo" not in configure:
        violations.append("relay default-disabled configure step missing")
    if 'cfg["daemon"]["relay"]["enabled"] is False' not in configure:
        violations.append("relay default-disabled assert missing")
    # Pairing-helper consent gate: interactive terminal plus explicit
    # default-negative human confirmation before native --relay.
    for marker in ("require_tty", "read -r answer", "[y/N]",
                   "paseo daemon pair --relay --home /home/paseo/.paseo",
                   "Pairing cancelled; Relay was not enabled by this helper."):
        if marker not in access:
            violations.append(f"pairing consent-gate marker missing: {marker}")
    # First-time auth stays explicit and HOME-backed.
    for marker in ("auth-shell", "exec -w /home/paseo paseo sh"):
        if marker not in access:
            violations.append(f"auth-shell marker missing: {marker}")
    if "First-time provider or account authentication is never part of normal container startup" not in doc:
        violations.append("first-auth HOME-backed rule missing from doc")
    # Status is metadata-only: enablement plus keypair presence/mode/
    # ownership, pairing gate flag and unsupported revocation marker. The
    # keypair contents and pairing offers must never be printed.
    for marker in ('"relay_enabled"', '"daemon_keypair"', '"pairing_requires_human_action"',
                   '"device_revocation_cli": "unsupported"'):
        if marker not in access:
            violations.append(f"status metadata marker missing: {marker}")
    if 'daemon-keypair.json").read_text' in access:
        violations.append("status must not read keypair contents")
    if "never prints the keypair" not in doc:
        violations.append("metadata-only guarantee missing from doc")
    # Revocation fails closed where upstream lacks support.
    for marker in ('"supported":false', "no-individual-device-revocation-cli"):
        if marker not in access:
            violations.append(f"revocation fail-closed marker missing: {marker}")
    if "no command for listing and individually revoking" not in doc:
        violations.append("revocation unsupported rationale missing from doc")
    # Live mechanics already proven by the M02 disposable smoke; this Card
    # re-exercises the same boundary on the exact candidate.
    for marker in ('"code":"RELAY_DISABLED"', "paseo daemon pair --relay --json",
                   'cfg["daemon"]["relay"]["enabled"] is True', "daemon-keypair.json",
                   "keypair_sha_before", "keypair_sha_after", '= "600"',
                   "{{len .HostConfig.PortBindings}}", '"relay_default_disabled":true',
                   '"relay_enabled_after_consent":true', '"relay_enabled_after_recreate":true',
                   '"daemon_identity_persisted":true'):
        if marker not in smoke:
            violations.append(f"M02 relay smoke marker missing: {marker}")
    report = {
        "default_disabled": "paseo daemon config set daemon.relay.enabled false" in configure,
        "consent_gate": "Pairing cancelled; Relay was not enabled by this helper." in access,
        "metadata_only_status": 'daemon-keypair.json").read_text' not in access,
        "revocation_supported": False,
        "revocation_reason": "no-individual-device-revocation-cli",
    }
    return report, violations


def check_runtime_network_shape(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    try:
        compose = (root / "compose.yaml").read_text()
    except OSError as exc:
        return {}, [f"compose unreadable: {exc}"]
    ports_block = re.search(r"(?m)^\s+ports:\s*$", compose) is not None
    if ports_block:
        violations.append("compose must not publish public ports")
    secrets_block = re.search(r"(?m)^\s+secrets:\s*$", compose) is not None
    dedicated_secret = all(marker in compose for marker in (
        "source: codex_lb_client",
        "target: pi-unraid-codex-lb",
        'file: "${PI_CODEX_LB_SECRET_SOURCE:-/mnt/user/appdata/pi-unraid/secrets/codex-lb.env}"',
        "PI_CODEX_LB_SECRET_FILE: /run/secrets/pi-unraid-codex-lb",
    ))
    if secrets_block and not dedicated_secret:
        violations.append("compose secrets must be limited to the dedicated Codex-LB file-backed secret")
    leaked_env = [token for token in SECRET_ENV_TOKENS if token in compose]
    if leaked_env:
        violations.append(f"secret environment wiring in compose: {leaked_env}")
    forbidden = sorted(
        key for key in ("cpus:", "mem_limit:", "mem_reservation:", "deploy:",
                        "privileged:", "network_mode: host", "/var/run/docker.sock")
        if key in compose
    )
    if forbidden:
        violations.append(f"forbidden runtime keys: {forbidden}")
    if 'user: "${PASEO_UID:-99}:${PASEO_GID:-100}"' not in compose:
        violations.append("upstream user mapping missing")
    if 'shm_size: "1gb"' not in compose:
        violations.append("1 GiB shared memory missing")
    if not ("driver: json-file" in compose and 'max-size: "10m"' in compose
            and 'max-file: "3"' in compose):
        violations.append("bounded log rotation missing")
    report = {
        "public_ports": 0 if not ports_block else None,
        "ports_published": ports_block,
        "secret_env_wiring": leaked_env,
        "dedicated_codex_lb_secret": dedicated_secret,
        "forbidden_keys": forbidden,
    }
    return report, violations


def check_inventory_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    inventory, _ = _load_scripts()
    try:
        definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
    except (OSError, ValueError) as exc:
        return {}, [f"inventory authority unreadable: {exc}"]
    try:
        inventory.validate_definition(definition)
    except Exception as exc:
        return {}, [f"inventory definition invalid: {exc}"]
    if definition.get("authority") != "environment_availability_only":
        violations.append("inventory authority must remain environment availability only")
    script_text = (root / "scripts" / "environment_capability_inventory.py").read_text()
    for token in ("import urllib", "import requests", "import subprocess"):
        if token in script_text:
            violations.append(f"inventory must not use network/process: {token}")
    # Desired state derives from the frozen candidate without duplicate
    # version literals in the definition.
    definition_text = (root / "config" / "environment-capabilities.json").read_text()
    for component in candidate.get("components", {}).values():
        version = component.get("version")
        if isinstance(version, str) and version in definition_text:
            violations.append(f"duplicate version literal in definition: {version}")
    try:
        bare = inventory.derive_inventory(definition, candidate, root)
    except Exception as exc:
        return {}, [f"inventory derivation failed: {exc}"]
    if bare.get("authority") != "environment_availability_only":
        violations.append("derived inventory authority drift")
    if bare.get("candidate_id") != CANDIDATE_ID:
        violations.append("derived inventory candidate mismatch")
    # Perfect observations prove desired/observed readback; drifted
    # observations prove classification without silent deletion.
    perfect = {
        item["id"]: {"present": True, "version": item["desired"]["version"],
                     "location": item["runtime_location"]["value"]}
        for item in bare["capabilities"]
    }
    try:
        green = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    except Exception as exc:
        return {}, [f"inventory green derivation failed: {exc}"]
    if green.get("state") != "GREEN":
        violations.append("perfect observations must derive GREEN")
    drifted = dict(perfect)
    drifted["pi"] = {"present": False}
    drifted["node"] = {"present": True, "version": "not-the-frozen-version",
                       "location": "not-the-runtime-location"}
    drifted["m06t03-unexpected-probe"] = {"present": True, "version": "anything"}
    try:
        drift = inventory.derive_inventory(definition, candidate, root, drifted)
    except Exception as exc:
        return {}, [f"inventory drift derivation failed: {exc}"]
    by_id = {item["id"]: item for item in drift["capabilities"]}
    if by_id.get("pi", {}).get("drift") != "missing":
        violations.append("missing drift not classified")
    if by_id.get("node", {}).get("drift") != "version_mismatch":
        violations.append("version_mismatch drift not classified")
    if len(drift.get("unexpected_observations", [])) != 1:
        violations.append("unexpected extra not reported")
    if "m06t03-unexpected-probe" in json.dumps(drift):
        violations.append("unexpected id leaked instead of fingerprint")
    report = {
        "authority": definition.get("authority"),
        "capabilities": len(bare["capabilities"]),
        "green_state": green.get("state"),
        "drift_state": drift.get("state"),
        "drift": {"pi": "missing", "node": "version_mismatch",
                  "unexpected": "reported_fingerprinted"},
    }
    return report, violations


def check_control_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    inventory, control = _load_scripts()
    try:
        definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
    except (OSError, ValueError) as exc:
        return {}, [f"control authority unreadable: {exc}"]
    bare = inventory.derive_inventory(definition, candidate, root)
    perfect = {
        item["id"]: {"present": True, "version": item["desired"]["version"],
                     "location": item["runtime_location"]["value"]}
        for item in bare["capabilities"]
    }
    payload = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    try:
        quick = control.doctor(payload, depth="quick")
        full = control.doctor(payload, depth="full")
    except Exception as exc:
        return {}, [f"doctor failed on green payload: {exc}"]
    for name, result in (("quick", quick), ("full", full)):
        if result.get("state") != "GREEN":
            violations.append(f"{name} doctor must be GREEN on perfect observations")
        if result.get("doctor") != "environment_capabilities":
            violations.append(f"{name} doctor identity drift")
        if not isinstance(result.get("summary"), str) or "GREEN:" not in result["summary"]:
            violations.append(f"{name} doctor summary missing GREEN")
        if result.get("depth") != name:
            violations.append(f"{name} doctor depth mismatch")
    if not quick.get("deferred_capabilities"):
        violations.append("quick doctor must defer non-quick probes")
    if full.get("deferred_capabilities") != []:
        violations.append("full doctor must cover every capability")
    if len(full.get("checks", [])) != len(definition["capabilities"]):
        violations.append("full doctor check count mismatch")
    if len(quick.get("checks", [])) >= len(full.get("checks", [])):
        violations.append("quick doctor must select fewer checks than full")
    try:
        plan = control.build_reconcile_plan(payload)
    except Exception as exc:
        return {}, [f"reconcile plan failed on green payload: {exc}"]
    if plan.get("plan_state") != "clean":
        violations.append("green payload must reconcile clean")
    if plan.get("unexpected_policy") != "report_only_never_delete":
        violations.append("reconcile must never silently delete unexpected extras")
    if plan.get("desired_state_mutation") is not False:
        violations.append("reconcile must not mutate desired state")
    # Drifted payload proves approved-only restore targeting.
    drifted_obs = dict(perfect)
    drifted_obs["pi"] = {"present": False}
    drifted = inventory.derive_inventory(definition, candidate, root, drifted_obs)
    drift_plan = control.build_reconcile_plan(drifted)
    action_ids = sorted(a["capability_id"] for a in drift_plan.get("actions", []))
    if action_ids != ["pi"]:
        violations.append(f"reconcile must target only drifted approved ids: {action_ids}")
    # Post-action readback proves restoration only on exact GREEN.
    readback = control.verify_reconcile_readback(drifted, payload, drift_plan)
    if readback.get("state") != "GREEN":
        violations.append("restored readback must be GREEN")
    unresolved = control.verify_reconcile_readback(drifted, drifted, drift_plan)
    if unresolved.get("state") != "RED":
        violations.append("unrestored readback must stay RED")
    raw = (root / "scripts" / "environment_capability_control.py").read_text()
    for token in ('add_parser("update")', '"operation": "delete', "shell=True",
                  "import subprocess", "import requests", "import urllib"):
        if token in raw:
            violations.append(f"control surface must not own update/delete/process: {token}")
    for token in ("role_ceiling", "assignment_eligibility", "task_scoped_grant",
                  "task_board", "workflow_state"):
        if token in raw:
            violations.append(f"control must not own OR/PW policy: {token}")
    report = {
        "quick_state": quick.get("state"),
        "full_state": full.get("state"),
        "quick_checks": len(quick.get("checks", [])),
        "full_checks": len(full.get("checks", [])),
        "reconcile_green_plan": plan.get("plan_state"),
        "reconcile_drift_actions": action_ids,
        "unexpected_policy": plan.get("unexpected_policy"),
    }
    return report, violations


def check_healthcheck_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    try:
        definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
        compose = (root / "compose.yaml").read_text()
        smoke = (root / "scripts" / "verify-compose-foundation.sh").read_text()
    except (OSError, ValueError) as exc:
        return {}, [f"healthcheck source unreadable: {exc}"]
    paseo = next((c for c in definition.get("capabilities", []) if c.get("id") == "paseo"), None)
    if paseo is None or paseo.get("probe", {}).get("kind") != "http_health":
        violations.append("paseo http_health probe missing from inventory")
    if paseo is not None and paseo.get("probe", {}).get("path") != HEALTH_PATH:
        violations.append("paseo health path mismatch")
    if HEALTH_PATH not in smoke or str(HEALTH_PORT) not in smoke:
        violations.append("lightweight health probe missing from M02 smoke")
    if re.search(r"(?m)^\s+healthcheck:\s*$", compose) is not None:
        violations.append("compose must inherit the parent healthcheck, not override it")
    report = {
        "probe": "http_health",
        "path": HEALTH_PATH,
        "port": HEALTH_PORT,
        "compose_override": False,
    }
    return report, violations


def check_auth_fingerprint_policy(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    inventory, control = _load_scripts()
    try:
        definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
        candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
    except (OSError, ValueError) as exc:
        return {}, [f"fingerprint authority unreadable: {exc}"]
    bare = inventory.derive_inventory(definition, candidate, root)
    perfect = {
        item["id"]: {"present": True, "version": item["desired"]["version"],
                     "location": item["runtime_location"]["value"]}
        for item in bare["capabilities"]
    }
    secret = "M06T03-RAW-CREDENTIAL-PROBE-MUST-NOT-APPEAR"
    tainted = dict(perfect)
    tainted["pi"] = {"present": True, "version": secret,
                     "location": f"https://user:{secret}@example.invalid",
                     "token": secret}
    tainted[f"unknown-{secret}"] = {"present": True, "token": secret}
    derived = inventory.derive_inventory(definition, candidate, root, tainted)
    text = json.dumps(derived, sort_keys=True, separators=(",", ":"))
    if secret in text or "token" in text:
        violations.append("credential material leaked into inventory readback")
    if "version_fingerprint" not in text or "location_fingerprint" not in text:
        violations.append("mismatched observations must carry fingerprints only")
    if "id_fingerprint" not in text:
        violations.append("unexpected ids must carry fingerprints only")
    payload = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    try:
        control.build_reconcile_plan(payload, requested_ids=[f"not-approved-{secret}"])
        violations.append("reconcile must refuse unapproved capability ids")
    except Exception as exc:
        if secret in str(exc):
            violations.append("credential material leaked into reconcile refusal")
        if "sha256:" not in str(exc):
            violations.append("reconcile refusal must fingerprint unknown ids")
    report = {
        "fingerprints_only": not violations,
        "surfaces": ["inventory_version", "inventory_location", "unexpected_id",
                     "reconcile_refusal"],
    }
    return report, violations


def check_no_activation_path(root: Path) -> tuple[dict, list[str]]:
    violations: list[str] = []
    harness = Path(__file__).read_text()
    if '"need": "specpi_wishlist_activation", "owner": "M07-T05"' not in harness:
        violations.append("wishlist M07-T05 deferral missing from harness")
    if re.search(r"(?im)^.*wishlist.*activat\w*\s*\(", harness) is not None:
        violations.append("harness must not provide a wishlist activation path")
    if "real_phone_pairing" not in harness or "pairing_transfer_ux" not in harness:
        violations.append("phone pairing/transfer deferrals missing from harness")
    report = {"wishlist_owner": "M07-T05", "wishlist_activation_path": None,
              "phone_pairing_claimed": False}
    return report, violations


def build_readback(root: Path) -> dict:
    candidate, candidate_violations = check_candidate_identity(root)
    relay, relay_violations = check_relay_policy(root)
    network, network_violations = check_runtime_network_shape(root)
    inv, inv_violations = check_inventory_policy(root)
    control, control_violations = check_control_policy(root)
    health, health_violations = check_healthcheck_policy(root)
    fingerprints, fingerprint_violations = check_auth_fingerprint_policy(root)
    activation, activation_violations = check_no_activation_path(root)
    violations = (candidate_violations + relay_violations + network_violations
                  + inv_violations + control_violations + health_violations
                  + fingerprint_violations + activation_violations)
    return {
        "card": CARD_ID,
        "candidate": candidate,
        "relay": relay,
        "runtime_network": network,
        "inventory": inv,
        "capability_control": control,
        "healthcheck": health,
        "auth_fingerprints": fingerprints,
        "activation_policy": activation,
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


def bounded_output(text: str, limit: int = 6000) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return "...[truncated]...\n" + text[-limit:]


def scan_secret_safe(text: str, context: str) -> None:
    for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"secret-like value leaked into {context}")


def record(phases: list[dict], name: str, status: str, detail: dict) -> None:
    phases.append({"name": name, "status": status, "detail": detail})


def write_failure_report(report_path: Path | None, scope: str, error: str,
                         extra: dict | None = None) -> str | None:
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
        print(f"paseo relay-doctor-readiness error: failure report unwritable ({exc}); payload: {text}",
              file=sys.stderr)
        return None
    return text


def container_flags(*mounts: str) -> list[str]:
    flags = ["--user", f"{RUNTIME_UID}:{RUNTIME_GID}", "--shm-size=1gb"]
    for mount in mounts:
        flags.extend(["-v", mount])
    return flags


def chown_fixture(image: str, fixture: Path, *names: str) -> None:
    targets = [f"/fixture/{name}" for name in names]
    run_command(["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "chown",
                 "-v", f"{fixture}:/fixture", image, "-R",
                 f"{RUNTIME_UID}:{RUNTIME_GID}", *targets])


def parse_kv_output(output: str) -> dict:
    # Single-line machine-readable probes: each line is exactly key=value
    # with the value space-joined on that one line.
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


HEALTH_JS = (
    "const http=require('http');"
    "const req=http.get({hostname:'127.0.0.1',port:6767,path:'/api/health'},"
    "r=>process.exit(r.statusCode===200?0:1));"
    "req.on('error',()=>process.exit(1));"
    "req.setTimeout(1500,()=>{req.destroy();process.exit(1)});"
)


def phase_image_labels(image: str) -> dict:
    image_id = run_command(["docker", "inspect", "--format={{.Id}}", image]).strip()
    labels_out = run_command(
        ["docker", "inspect", "--format={{json .Config.Labels}}", image]).strip()
    labels = json.loads(labels_out or "{}")
    expected = {
        "io.pi-unraid.candidate-id": CANDIDATE_ID,
        "io.pi-unraid.paseo-version": PASEO_VERSION,
        "io.pi-unraid.pi-version": PI_VERSION,
    }
    for label, want in expected.items():
        if labels.get(label) != want:
            fail(f"image label {label} mismatch: {labels.get(label)!r}")
    return {"id": image_id, "candidate_id": labels["io.pi-unraid.candidate-id"]}


def phase_relay_fail_closed(root: Path, image: str, home: Path, worktrees: Path) -> dict:
    # Configure persists relay=false; every enablement path without consent
    # then fails closed, and revocation reports unsupported.
    run_command(["bash", str(root / "scripts" / "configure-paseo-runtime.sh"),
                 image, str(home), str(worktrees), str(RUNTIME_UID), str(RUNTIME_GID)])
    flags = container_flags(f"{home}:/home/paseo")
    relay_out = docker_run(
        image, flags,
        ["python3", "-c", "import json;print(json.load(open('/home/paseo/.paseo/config.json'))"
         "['daemon']['relay']['enabled'])"],
        timeout=60,
    ).strip()
    if relay_out != "False":
        fail(f"relay default not disabled after configure: {relay_out!r}")
    proc = run_command_unchecked(
        ["docker", "run", "--rm", *flags, image,
         "paseo", "daemon", "pair", "--json", "--home", "/home/paseo/.paseo"],
        timeout=120,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    scan_secret_safe(combined, "non-consenting pair probe")
    if proc.returncode == 0:
        fail("non-consenting pair unexpectedly succeeded while Relay is disabled")
    if '"code":"RELAY_DISABLED"' not in combined:
        fail(f"RELAY_DISABLED fail-closed signal missing: {bounded_output(combined.strip() or '(no output)')}")
    access = (root / "scripts" / "paseo-relay-access.sh").read_text()
    for marker in ("require_tty", "read -r answer", "[y/N]",
                   "Pairing cancelled; Relay was not enabled by this helper."):
        if marker not in access:
            fail(f"pairing consent-gate marker missing in flow: {marker}")
    rev_out = run_command(
        ["bash", str(root / "scripts" / "paseo-relay-access.sh"), "revocation-capability"],
        timeout=30,
    )
    try:
        revocation = json.loads(rev_out)
    except ValueError:
        fail(f"revocation-capability is not JSON: {rev_out.strip()[:200]}")
    if revocation.get("supported") is not False:
        fail(f"revocation must report unsupported: {rev_out.strip()[:200]}")
    if revocation.get("reason") != "no-individual-device-revocation-cli":
        fail(f"revocation reason mismatch: {revocation}")
    return {
        "relay_default_disabled": True,
        "pair_fail_closed": True,
        "pair_code": "RELAY_DISABLED",
        "consent_gate": True,
        "revocation_supported": False,
        "revocation_reason": "no-individual-device-revocation-cli",
    }


def phase_synthetic_persistence(image: str, home: Path, projects: Path,
                                worktrees: Path) -> dict:
    # Synthetic identity: explicit --relay consent inside this disposable
    # fixture only. The pairing offer is captured and discarded without
    # logging; only relay state plus keypair sha/mode/ownership are kept.
    flags = container_flags(f"{home}:/home/paseo")
    offer = docker_run(
        image, flags,
        ["paseo", "daemon", "pair", "--relay", "--json", "--home", "/home/paseo/.paseo"],
        timeout=120,
    )
    if not offer.strip():
        fail("consent simulation produced no pairing offer")
    scan_secret_safe(offer, "synthetic pairing offer")
    del offer
    relay_out = docker_run(
        image, flags,
        ["python3", "-c", "import json;print(json.load(open('/home/paseo/.paseo/config.json'))"
         "['daemon']['relay']['enabled'])"],
        timeout=60,
    ).strip()
    if relay_out != "True":
        fail(f"relay not enabled after consent simulation: {relay_out!r}")
    identity_out = docker_run(
        image, flags,
        ["sh", "-c", "set -eu; "
         "printf 'sha=%s\\n' \"$(sha256sum /home/paseo/.paseo/daemon-keypair.json"
         " | awk '{print $1}')\"; "
         "printf 'mode=%s\\n' \"$(stat -c '%a:%u:%g'"
         " /home/paseo/.paseo/daemon-keypair.json)\"; "
         "printf 'identity_check=done\\n'"],
        timeout=60,
    )
    scan_secret_safe(identity_out, "keypair identity probe")
    values = parse_kv_output(identity_out)
    if values.get("identity_check") != "done":
        fail("container-side keypair identity check incomplete")
    sha = values.get("sha", "")
    if not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
        fail(f"keypair sha is not a hex digest: {sha!r}")
    if values.get("mode") != f"600:{RUNTIME_UID}:{RUNTIME_GID}":
        fail(f"keypair mode/ownership mismatch: {values.get('mode')!r}")
    docker_run(
        image, container_flags(f"{home}:/home/paseo", f"{projects}:/projects",
                               f"{worktrees}:/worktrees"),
        ["sh", "-c", "set -eu; printf home > /home/paseo/m06t03-home-marker; "
         "printf project > /projects/m06t03-project-marker; "
         "printf worktree > /worktrees/m06t03-worktree-marker; "],
        timeout=60,
    )
    return {
        "relay_enabled_after_consent": True,
        "synthetic_identity": True,
        "real_phone_claimed": False,
        "keypair_sha_before": sha,
        "keypair_mode": "600",
        "keypair_owner": f"{RUNTIME_UID}:{RUNTIME_GID}",
        "markers_written": ["home", "projects", "worktrees"],
    }


def _wait_daemon_health(cid: str, timeout_s: int = 60) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        proc = run_command_unchecked(
            ["docker", "exec", cid, "node", "-e", HEALTH_JS], timeout=15)
        if proc.returncode == 0:
            return
        time.sleep(2)
    fail("paseo daemon /api/health did not become ready")


def _inspect_mounts(cid: str) -> str:
    return run_command(
        ["docker", "inspect", "-f", "{{range .Mounts}}{{.Destination}};{{end}}", cid],
        timeout=30,
    )


def phase_daemon_health_ports(cid: str) -> dict:
    _wait_daemon_health(cid)
    user = run_command(["docker", "inspect", "-f", "{{.Config.User}}", cid],
                       timeout=30).strip()
    if user != f"{RUNTIME_UID}:{RUNTIME_GID}":
        fail(f"daemon user mismatch: {user!r}")
    for template, want, name in (
        ("{{len .HostConfig.PortBindings}}", "0", "public port bindings"),
        ("{{.HostConfig.ShmSize}}", str(SHM_BYTES), "shared memory"),
        ("{{.HostConfig.Memory}}", "0", "memory cap"),
        ("{{.HostConfig.NanoCpus}}", "0", "cpu cap"),
        ("{{.HostConfig.Privileged}}", "false", "privileged"),
        ("{{.HostConfig.LogConfig.Type}}", "json-file", "log driver"),
        ('{{index .HostConfig.LogConfig.Config "max-size"}}', "10m", "log max-size"),
        ('{{index .HostConfig.LogConfig.Config "max-file"}}', "3", "log max-file"),
    ):
        observed = run_command(["docker", "inspect", "-f", template, cid],
                               timeout=30).strip()
        if observed != want:
            fail(f"daemon {name} mismatch: {observed!r} != {want!r}")
    mounts = _inspect_mounts(cid)
    for target in ("/home/paseo", "/projects", "/worktrees"):
        if f"{target};" not in mounts:
            fail(f"missing expected Compose mount {target} in {mounts!r}")
    relay_out = run_command(
        ["docker", "exec", "-u", f"{RUNTIME_UID}:{RUNTIME_GID}", cid, "python3", "-c",
         "import json;print(json.load(open('/home/paseo/.paseo/config.json'))"
         "['daemon']['relay']['enabled'])"],
        timeout=60,
    ).strip()
    if relay_out != "True":
        fail(f"daemon lost relay enablement: {relay_out!r}")
    mode_out = run_command(
        ["docker", "exec", cid, "stat", "-c", "%a:%u:%g",
         "/home/paseo/.paseo/daemon-keypair.json"],
        timeout=30,
    ).strip()
    if mode_out != f"600:{RUNTIME_UID}:{RUNTIME_GID}":
        fail(f"daemon keypair mode/ownership mismatch: {mode_out!r}")
    return {
        "health": "GREEN",
        "health_path": HEALTH_PATH,
        "health_port": HEALTH_PORT,
        "public_ports": 0,
        "daemon_user": user,
        "shm_bytes": SHM_BYTES,
        "mounts": ["/home/paseo", "/projects", "/worktrees"],
        "relay_enabled": True,
        "keypair_mode": "600",
    }


def phase_recreate_markers(cid: str, sha_before: str) -> dict:
    markers = {}
    for container_path, want in (
        ("/home/paseo/m06t03-home-marker", "home"),
        ("/projects/m06t03-project-marker", "project"),
        ("/worktrees/m06t03-worktree-marker", "worktree"),
    ):
        observed = run_command(["docker", "exec", cid, "cat", container_path],
                               timeout=30).strip()
        if observed != want:
            fail(f"marker {container_path} mismatch after recreate: {observed!r}")
        markers[container_path] = observed
    relay_out = run_command(
        ["docker", "exec", "-u", f"{RUNTIME_UID}:{RUNTIME_GID}", cid, "python3", "-c",
         "import json;print(json.load(open('/home/paseo/.paseo/config.json'))"
         "['daemon']['relay']['enabled'])"],
        timeout=60,
    ).strip()
    if relay_out != "True":
        fail(f"relay not enabled after recreate: {relay_out!r}")
    sha_after = run_command(
        ["docker", "exec", cid, "sha256sum", "/home/paseo/.paseo/daemon-keypair.json"],
        timeout=30,
    ).split()[0]
    if sha_after != sha_before:
        fail("daemon keypair bytes changed across recreation")
    mode_out = run_command(
        ["docker", "exec", cid, "stat", "-c", "%a", "/home/paseo/.paseo/daemon-keypair.json"],
        timeout=30,
    ).strip()
    if mode_out != "600":
        fail(f"keypair mode changed across recreate: {mode_out!r}")
    _wait_daemon_health(cid)
    ports = run_command(["docker", "inspect", "-f", "{{len .HostConfig.PortBindings}}", cid],
                        timeout=30).strip()
    if ports != "0":
        fail(f"public ports appeared after recreate: {ports!r}")
    return {
        "markers_persisted": True,
        "relay_enabled_after_recreate": True,
        "daemon_identity_persisted": True,
        "keypair_sha_after": sha_after,
        "keypair_sha_match": True,
        "health_after_recreate": "GREEN",
        "public_ports_after_recreate": 0,
    }


def phase_secret_safe_home(root: Path, image: str, home: Path) -> dict:
    # All HOME content reads run container-side as the runtime identity:
    # the fixture HOME is 99:100-owned with 0600 daemon material that the
    # host user cannot read. Only metadata (never keypair contents or
    # pairing offers) is captured.
    out = docker_run(
        image, container_flags(f"{home}:/home/paseo"),
        ["python3", "-c",
         "import json,re;cfg=json.load(open('/home/paseo/.paseo/config.json'));"
         "text=json.dumps(cfg);"
         "forbidden=[t for t in ('PASEO_PASSWORD','OPENAI_API_KEY','ANTHROPIC_API_KEY',"
         "'GITHUB_TOKEN','MUSE_API_KEY','CODEX_API_KEY') if t in text];"
         "secret_pat=re.compile(r'(?i)(password|token|api[_-]?key)\\s*[:=]\\s*\\S+');"
         "print('forbidden_env='+','.join(forbidden));"
         "print('secret_assign='+str(bool(secret_pat.search(text))));"
         "print('has_daemon_keypair='+str(bool(__import__('pathlib').Path("
         "'/home/paseo/.paseo/daemon-keypair.json').is_file())));"
         "print('secret_scan=done')"],
        timeout=60,
    )
    scan_secret_safe(out, "HOME secret scan")
    values = parse_kv_output(out)
    if values.get("secret_scan") != "done":
        fail("container-side HOME secret scan incomplete")
    if values.get("forbidden_env"):
        fail(f"secret env material in HOME config: {values['forbidden_env']!r}")
    if values.get("secret_assign") != "False":
        fail("secret-valued assignment in HOME config")
    if values.get("has_daemon_keypair") != "True":
        fail("daemon keypair missing from HOME")
    compose = (root / "compose.yaml").read_text()
    leaked = [t for t in SECRET_ENV_TOKENS if t in compose]
    if leaked:
        fail(f"secret environment wiring in compose: {leaked}")
    return {
        "home_secret_free": True,
        "keypair_contents_captured": False,
        "pairing_offer_logged": False,
        "compose_secret_wiring": [],
    }


def phase_inventory_drift(root: Path) -> dict:
    inventory, _ = _load_scripts()
    definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
    candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
    bare = inventory.derive_inventory(definition, candidate, root)
    perfect = {
        item["id"]: {"present": True, "version": item["desired"]["version"],
                     "location": item["runtime_location"]["value"]}
        for item in bare["capabilities"]
    }
    green = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    if green.get("state") != "GREEN":
        fail("inventory perfect observations did not derive GREEN")
    drifted_obs = dict(perfect)
    drifted_obs["pi"] = {"present": False}
    drifted_obs["node"] = {"present": True, "version": "m06t03-drift-probe",
                           "location": "m06t03-drift-location"}
    drifted_obs["m06t03-unexpected-extra"] = {"present": True, "version": "anything"}
    drifted = inventory.derive_inventory(definition, candidate, root, drifted_obs)
    by_id = {item["id"]: item for item in drifted["capabilities"]}
    if drifted.get("state") != "RED":
        fail(f"drifted inventory must be RED: {drifted.get('state')}")
    if by_id["pi"]["drift"] != "missing":
        fail("pi missing drift not reported")
    if by_id["node"]["drift"] != "version_mismatch":
        fail("node mismatch drift not reported")
    unexpected = drifted.get("unexpected_observations", [])
    if len(unexpected) != 1 or unexpected[0].get("drift") != "unexpected":
        fail("unexpected extra not reported without deletion")
    text = json.dumps(drifted)
    if "m06t03-unexpected-extra" in text or "m06t03-drift-probe" in text:
        fail("drifted values leaked instead of fingerprints")
    scan_secret_safe(text, "inventory drift readback")
    return {
        "desired_observed_readback": True,
        "green_state": "GREEN",
        "drift_state": "RED",
        "pi_drift": "missing",
        "node_drift": "version_mismatch",
        "unexpected_reported": 1,
        "unexpected_deleted": 0,
        "machine_readable": True,
    }


def phase_reconcile_doctor(root: Path) -> dict:
    inventory, control = _load_scripts()
    definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
    candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
    bare = inventory.derive_inventory(definition, candidate, root)
    perfect = {
        item["id"]: {"present": True, "version": item["desired"]["version"],
                     "location": item["runtime_location"]["value"]}
        for item in bare["capabilities"]
    }
    green_payload = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    drifted_obs = dict(perfect)
    drifted_obs["pi"] = {"present": False}
    drifted_obs["node"] = {"present": True, "version": "m06t03-reconcile-probe",
                           "location": "m06t03-reconcile-location"}
    drifted_obs["m06t03-reconcile-unexpected"] = {"present": True, "version": "x"}
    drifted = inventory.derive_inventory(definition, candidate, root, drifted_obs)
    plan = control.build_reconcile_plan(drifted)
    action_ids = sorted(a["capability_id"] for a in plan.get("actions", []))
    if action_ids != ["node", "pi"]:
        fail(f"reconcile must target exactly the drifted approved ids: {action_ids}")
    for action in plan["actions"]:
        if action.get("operation") != "restore_desired_state":
            fail("reconcile operation must be restore_desired_state")
    if plan.get("unexpected_policy") != "report_only_never_delete":
        fail("reconcile must report unexpected extras without deleting")
    if plan.get("desired_state_mutation") is not False:
        fail("reconcile plan must not mutate desired state")
    # The restored readback keeps the same unexpected extra reported:
    # approved capabilities are restored while the extra is still
    # observed, proving reconcile never silently deletes it.
    restored_obs = dict(perfect)
    restored_obs["m06t03-reconcile-unexpected"] = {"present": True, "version": "x"}
    restored_payload = inventory.derive_inventory(definition, candidate, root, restored_obs)
    restored = control.verify_reconcile_readback(drifted, restored_payload, plan)
    if restored.get("state") != "WARN":
        fail(f"restored reconcile readback must be WARN with the extra still reported: {restored.get('state')}")
    if sorted(a["capability_id"] for a in restored["actions"]
              if a["status"] == "restored") != ["node", "pi"]:
        fail("restored actions mismatch")
    unresolved = control.verify_reconcile_readback(drifted, drifted, plan)
    if unresolved.get("state") != "RED":
        fail("unrestored reconcile readback must stay RED")
    clean_after = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    disappeared = control.verify_reconcile_readback(drifted, clean_after, plan)
    if disappeared.get("state") != "RED" or not disappeared.get("unexpected_disappeared"):
        fail("disappearing unexpected extra must fail RED, never silently vanish")
    quick_green = control.doctor(green_payload, depth="quick")
    full_green = control.doctor(green_payload, depth="full")
    full_red = control.doctor(drifted, depth="full")
    if quick_green.get("state") != "GREEN" or full_green.get("state") != "GREEN":
        fail("doctor must be GREEN on perfect observations")
    if full_red.get("state") != "RED":
        fail("doctor must be RED on drifted observations")
    for name, result in (("quick", quick_green), ("full", full_green), ("full_red", full_red)):
        if result.get("doctor") != "environment_capabilities":
            fail(f"{name} doctor identity drift")
        if not isinstance(result.get("summary"), str):
            fail(f"{name} doctor summary missing")
        if not isinstance(result.get("counts"), dict):
            fail(f"{name} doctor counts missing")
    if not quick_green.get("deferred_capabilities"):
        fail("quick doctor must defer non-quick probes")
    if full_green.get("deferred_capabilities") != []:
        fail("full doctor must cover every capability")
    scan_secret_safe(json.dumps(plan), "reconcile plan")
    scan_secret_safe(json.dumps(full_red), "drifted doctor")
    return {
        "reconcile_plan_state": plan.get("plan_state"),
        "reconcile_actions": action_ids,
        "reconcile_approved_only": True,
        "restored_state": "WARN",
        "restored_warn_reason": "unexpected_extra_still_reported",
        "unrestored_state": "RED",
        "unexpected_disappeared_fails_red": True,
        "quick_state": "GREEN",
        "full_state": "GREEN",
        "drifted_full_state": "RED",
        "machine_readable": True,
    }


def phase_auth_fingerprints(root: Path) -> dict:
    inventory, control = _load_scripts()
    definition = json.loads((root / "config" / "environment-capabilities.json").read_text())
    candidate = json.loads((root / "config" / "paseo-candidate.json").read_text())
    bare = inventory.derive_inventory(definition, candidate, root)
    perfect = {
        item["id"]: {"present": True, "version": item["desired"]["version"],
                     "location": item["runtime_location"]["value"]}
        for item in bare["capabilities"]
    }
    secret = "M06T03-LIVE-CREDENTIAL-PROBE-MUST-NOT-APPEAR"
    tainted = dict(perfect)
    tainted["pi"] = {"present": True, "version": secret,
                     "location": f"https://user:{secret}@example.invalid",
                     "token": secret}
    tainted[f"unknown-{secret}"] = {"present": True, "token": secret}
    derived = inventory.derive_inventory(definition, candidate, root, tainted)
    text = json.dumps(derived, sort_keys=True, separators=(",", ":"))
    if secret in text or "token" in text:
        fail("credential material leaked into live inventory readback")
    for marker in ("version_fingerprint", "location_fingerprint", "id_fingerprint"):
        if marker not in text:
            fail(f"live readback missing {marker}")
    payload = inventory.derive_inventory(definition, candidate, root, dict(perfect))
    try:
        control.build_reconcile_plan(payload, requested_ids=[f"not-approved-{secret}"])
        fail("live reconcile must refuse unapproved capability ids")
    except Exception as exc:
        message = str(exc)
        if secret in message:
            fail("credential material leaked into live reconcile refusal")
        if "sha256:" not in message:
            fail("live reconcile refusal must fingerprint unknown ids")
    return {
        "fingerprints_only": True,
        "credential_material_captured": False,
        "surfaces": ["inventory_version", "inventory_location", "unexpected_id",
                     "reconcile_refusal"],
    }


def disposable_flow(root: Path, image: str, report_path: Path | None) -> dict:
    if not docker_available():
        fail("docker is not available; run the disposable flow on a Docker runner (CI)")
    phases: list[dict] = []
    fixture = Path(tempfile.mkdtemp(prefix="pi-unraid-m06-t03.")).resolve()
    guard_disposable_scope("disposable", fixture)
    project = f"piunraid-m06-t03-{os.getpid()}"
    saved_env = dict(os.environ)
    home = fixture / "home"
    projects = fixture / "projects"
    worktrees = fixture / "worktrees"
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
        try:
            record(phases, "fixture", "ok", {"root": str(fixture)})
            chown_fixture(image, fixture, "home", "projects", "worktrees")
            image_detail = phase_image_labels(image)
            record(phases, "image_labels", "ok", image_detail)
            record(phases, "relay_fail_closed", "ok",
                   phase_relay_fail_closed(root, image, home, worktrees))
            synthetic = phase_synthetic_persistence(image, home, projects, worktrees)
            # The keypair sha is a one-way digest of synthetic disposable
            # identity; persisting the digest (never keypair contents or
            # pairing offers) is required for the recreate comparison.
            record(phases, "synthetic_persistence", "ok", synthetic)
            sha_before = synthetic["keypair_sha_before"]
            (fixture / "compose.fixture.yaml").write_text(
                "services:\n  paseo:\n    image: " + image + "\n    build: null\n    restart: \"no\"\n"
            )
            dc("config")
            dc("up", "-d")
            cid = dc("ps", "-q", "paseo").strip()
            if not cid:
                fail("paseo service did not start")
            try:
                record(phases, "daemon_health_ports", "ok",
                       phase_daemon_health_ports(cid))
                dc("down")
                dc("up", "-d")
                cid = dc("ps", "-q", "paseo").strip()
                if not cid:
                    fail("paseo service did not restart after recreate")
                record(phases, "recreate_survival", "ok",
                       phase_recreate_markers(cid, sha_before))
            finally:
                try:
                    dc("down", "-v")
                except SystemExit:
                    pass
            # The daemon is down; remaining HOME reads use one-shot
            # runtime-identity containers, never host-side reads of 0600
            # container-owned material.
            record(phases, "secret_safe_home", "ok",
                   phase_secret_safe_home(root, image, home))
            record(phases, "inventory_drift", "ok", phase_inventory_drift(root))
            record(phases, "reconcile_doctor", "ok", phase_reconcile_doctor(root))
            record(phases, "auth_fingerprints", "ok", phase_auth_fingerprints(root))
            # Secret-safety of the final report itself: no keypair
            # contents, offers or credential probes may be embedded.
            report_text = json.dumps(phases)
            scan_secret_safe(report_text, "flow phase details")
            if sha_before not in ("", None) and len(sha_before) != 64:
                fail("keypair sha length mismatch in report guard")
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
                "outcome": "relay_doctor_readiness_green",
            }
        except BaseException as exc:
            if report_path is not None and not report_path.exists():
                written = write_failure_report(
                    report_path, "disposable", str(exc) or "flow failed",
                    extra={"phases_completed": [p["name"] for p in phases]})
                if written is not None:
                    print(written)
            raise
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="M06-T03 Relay/persistence/capability/doctor readiness harness")
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
