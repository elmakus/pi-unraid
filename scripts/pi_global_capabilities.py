#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

AGENT_REL = Path(".pi/agent")
SETTINGS_REL = AGENT_REL / "settings.json"
NPM_REL = AGENT_REL / "npm"
STATE_REL = Path(".pi-unraid/global-capabilities")
SNAPSHOT_NAME = "snapshot.json"
COMPATIBILITY_NAME = "compatibility.json"
ALLOWED_PACKAGE_KEYS = {"source", "autoload", "extensions", "skills", "prompts", "themes"}
PINNED_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

MANAGED = {
    "specpi": {
        "package": "specpi",
        "component": "specpi",
        "version_env": "PI_UNRAID_SPECPI_VERSION",
        "location": "specpi",
    },
    "pi_mcp_adapter": {
        "package": "pi-mcp-adapter",
        "component": "pi_mcp_adapter",
        "version_env": "PI_UNRAID_PI_MCP_ADAPTER_VERSION",
        "location": "pi-mcp-adapter",
    },
}


class CapabilityDeliveryError(RuntimeError):
    pass


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()[:16]


def _load_json(path: Path, *, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return deepcopy(default)
        raise CapabilityDeliveryError(f"required JSON file is missing: {path.name}")
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityDeliveryError(f"invalid JSON file: {path.name}") from exc


def _atomic_json(path: Path, payload: Any, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is None:
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
            handle.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
        os.chmod(path, mode)
    finally:
        if tmp.exists():
            tmp.unlink()


def _package_source(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict) and isinstance(entry.get("source"), str):
        return entry["source"]
    return None


def _validate_package_entry(entry: Any) -> None:
    if isinstance(entry, str):
        return
    if not isinstance(entry, dict) or not isinstance(entry.get("source"), str):
        raise CapabilityDeliveryError("Pi package declaration is malformed")
    if not set(entry).issubset(ALLOWED_PACKAGE_KEYS):
        raise CapabilityDeliveryError("Pi package declaration has unsupported fields")
    if "autoload" in entry and not isinstance(entry["autoload"], bool):
        raise CapabilityDeliveryError("Pi package autoload must be boolean")
    for key in ("extensions", "skills", "prompts", "themes"):
        if key in entry and (
            not isinstance(entry[key], list)
            or not all(isinstance(item, str) for item in entry[key])
        ):
            raise CapabilityDeliveryError(f"Pi package {key} filter is malformed")


def _managed_key(source: str) -> str | None:
    for key, spec in MANAGED.items():
        base = f"npm:{spec['package']}"
        if source == base or source.startswith(base + "@"):
            return key
    return None


def _source_version(source: str, package: str) -> str | None:
    prefix = f"npm:{package}@"
    if not source.startswith(prefix):
        return None
    value = source[len(prefix):]
    return value if PINNED_VERSION_RE.fullmatch(value) else None


def _settings(home: Path) -> dict:
    payload = _load_json(home / SETTINGS_REL, default={})
    if not isinstance(payload, dict):
        raise CapabilityDeliveryError("Pi settings must be a JSON object")
    packages = payload.get("packages", [])
    if not isinstance(packages, list):
        raise CapabilityDeliveryError("Pi settings packages must be an array")
    for entry in packages:
        _validate_package_entry(entry)
    return payload


def _managed_entries(settings: dict, *, rollback_safe: bool = False) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    for index, entry in enumerate(settings.get("packages", [])):
        source = _package_source(entry)
        if source is None:
            continue
        key = _managed_key(source)
        if key is None:
            continue
        if key in seen:
            raise CapabilityDeliveryError(f"duplicate managed Pi package declaration: {key}")
        seen.add(key)
        if rollback_safe and _source_version(source, MANAGED[key]["package"]) is None:
            raise CapabilityDeliveryError(
                f"managed Pi package rollback source is not pinned: {key}"
            )
        found.append({"key": key, "index": index, "entry": deepcopy(entry)})
    return found


def validate_candidate(candidate: dict, env: dict[str, str]) -> dict[str, dict]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != 1:
        raise CapabilityDeliveryError("unsupported candidate schema")
    expected_id = env.get("PI_UNRAID_CANDIDATE_ID")
    expected_pi = env.get("PI_UNRAID_PI_VERSION")
    if not expected_id or not expected_pi:
        raise CapabilityDeliveryError("exact child-image candidate identity is unavailable")
    if candidate.get("candidate_id") != expected_id:
        raise CapabilityDeliveryError("candidate identity does not match the exact child image")
    components = candidate.get("components")
    if not isinstance(components, dict):
        raise CapabilityDeliveryError("candidate components are missing")
    pi = components.get("pi")
    if (
        not isinstance(pi, dict)
        or pi.get("version") != expected_pi
        or not isinstance(pi.get("npm"), dict)
        or pi["npm"].get("package") != "@earendil-works/pi-coding-agent"
    ):
        raise CapabilityDeliveryError("candidate Pi identity does not match the exact child image")

    desired: dict[str, dict] = {}
    for key, spec in MANAGED.items():
        component = components.get(spec["component"])
        expected_version = env.get(spec["version_env"])
        if not expected_version:
            raise CapabilityDeliveryError(f"exact child-image version is unavailable: {key}")
        if not isinstance(component, dict) or component.get("version") != expected_version:
            raise CapabilityDeliveryError(f"candidate version mismatch: {key}")
        npm = component.get("npm")
        if (
            not isinstance(npm, dict)
            or npm.get("package") != spec["package"]
            or not isinstance(npm.get("integrity"), str)
            or not npm["integrity"]
        ):
            raise CapabilityDeliveryError(f"candidate npm provenance is invalid: {key}")
        if component.get("live_compatibility_smoke_required") is not True:
            raise CapabilityDeliveryError(f"candidate compatibility gate is missing: {key}")
        desired[key] = {
            "package": spec["package"],
            "version": expected_version,
            "integrity": npm["integrity"],
            "source": f"npm:{spec['package']}@{expected_version}",
            "location": spec["location"],
        }
    return desired


def _installed_readback(home: Path, package: str) -> dict:
    package_root = home / NPM_REL / "node_modules" / package
    manifest_path = package_root / "package.json"
    manifest_version: str | None = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
            if isinstance(manifest, dict) and isinstance(manifest.get("version"), str):
                manifest_version = manifest["version"]
        except (OSError, json.JSONDecodeError):
            pass

    lock_version: str | None = None
    lock_integrity: str | None = None
    lock_path = home / NPM_REL / "package-lock.json"
    if lock_path.is_file():
        try:
            lock = json.loads(lock_path.read_text())
            record = lock.get("packages", {}).get(f"node_modules/{package}")
            if isinstance(record, dict):
                if isinstance(record.get("version"), str):
                    lock_version = record["version"]
                if isinstance(record.get("integrity"), str):
                    lock_integrity = record["integrity"]
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
    return {
        "manifest_present": manifest_path.is_file(),
        "manifest_version": manifest_version,
        "lock_version": lock_version,
        "lock_integrity": lock_integrity,
    }


def _declaration_state(settings: dict, key: str, expected_source: str) -> dict:
    entries = [item for item in _managed_entries(settings) if item["key"] == key]
    if not entries:
        return {"state": "missing"}
    source = _package_source(entries[0]["entry"])
    if source == expected_source:
        return {"state": "exact"}
    return {"state": "mismatch", "source_fingerprint": _fingerprint(source or "")}


def _compatibility_path(home: Path) -> Path:
    return home / STATE_REL / COMPATIBILITY_NAME


def _compatibility_payload(
    candidate_id: str,
    desired: dict[str, dict],
    runtime_pi_version: str,
) -> dict:
    return {
        "schema_version": 1,
        "candidate_id": candidate_id,
        "runtime_pi_version": runtime_pi_version,
        "packages": {
            key: {
                "version": desired[key]["version"],
                "source": desired[key]["source"],
            }
            for key in sorted(MANAGED)
        },
        "smoke": {
            "provider_free_rpc": True,
            "specpi_scope_inactive": True,
            "specpi_improvement_wishlist": True,
            "mcp_command_surface": True,
        },
    }


def _compatibility_readback(
    home: Path,
    candidate_id: str,
    desired: dict[str, dict],
    runtime_pi_version: str,
) -> dict:
    path = _compatibility_path(home)
    if not path.is_file():
        return {"state": "RED", "verified": False, "reason": "compatibility_smoke_missing"}
    try:
        payload = _load_json(path)
    except CapabilityDeliveryError:
        return {"state": "RED", "verified": False, "reason": "compatibility_marker_invalid"}
    expected = _compatibility_payload(candidate_id, desired, runtime_pi_version)
    if payload != expected:
        return {"state": "RED", "verified": False, "reason": "compatibility_marker_stale"}
    return {"state": "GREEN", "verified": True, "reason": "none"}


def build_status(
    home: Path,
    candidate_id: str,
    desired: dict[str, dict],
    *,
    runtime_pi_version: str,
    expected_pi_version: str,
) -> dict:
    settings = _settings(home)
    packages: dict[str, dict] = {}
    observations: dict[str, dict] = {}
    states: list[str] = []
    pi_exact = runtime_pi_version == expected_pi_version
    compatibility = _compatibility_readback(
        home, candidate_id, desired, runtime_pi_version
    )

    for key in sorted(MANAGED):
        want = desired[key]
        declaration = _declaration_state(settings, key, want["source"])
        installed = _installed_readback(home, want["package"])
        version_exact = (
            installed["manifest_version"] == want["version"]
            and installed["lock_version"] == want["version"]
        )
        integrity_exact = installed["lock_integrity"] == want["integrity"]
        installed_exact = declaration["state"] == "exact" and version_exact and integrity_exact
        accepted = installed_exact and compatibility["state"] == "GREEN"
        state = "GREEN" if accepted else "RED"
        reason = "none"
        if declaration["state"] != "exact":
            reason = f"declaration_{declaration['state']}"
        elif not installed["manifest_present"] or installed["manifest_version"] is None:
            reason = "package_missing_or_invalid"
        elif not version_exact:
            reason = "version_mismatch"
        elif not integrity_exact:
            reason = "integrity_mismatch"
        elif compatibility["state"] != "GREEN":
            reason = compatibility["reason"]

        item = {
            "state": state,
            "installed_exact": installed_exact,
            "reason": reason,
            "desired_version": want["version"],
            "declaration": declaration,
            "manifest_present": installed["manifest_present"],
            "integrity_verified": integrity_exact,
        }
        if installed["manifest_version"] and installed["manifest_version"] != want["version"]:
            item["observed_version_fingerprint"] = _fingerprint(installed["manifest_version"])
        if installed["lock_integrity"] and not integrity_exact:
            item["observed_integrity_fingerprint"] = _fingerprint(installed["lock_integrity"])
        packages[key] = item
        states.append(state)
        observations[key] = (
            {"present": True, "version": want["version"], "location": want["location"]}
            if accepted
            else {"present": False}
        )

    known_config_paths = [
        home / ".config/mcp/mcp.json",
        home / ".agents/mcp.json",
        home / ".agents/mcp/mcp.json",
        home / AGENT_REL / "mcp.json",
    ]
    config_count = sum(1 for path in known_config_paths if path.is_file())
    overall = "GREEN" if pi_exact and all(state == "GREEN" for state in states) else "RED"
    snapshot_path = home / STATE_REL / SNAPSHOT_NAME
    return {
        "schema_version": 1,
        "delivery": "pi_global_capabilities",
        "candidate_id": candidate_id,
        "state": overall,
        "in_sync": overall == "GREEN",
        "runtime_pi": {
            "state": "GREEN" if pi_exact else "RED",
            "desired_version": expected_pi_version,
            **(
                {"version": expected_pi_version}
                if pi_exact
                else {"observed_version_fingerprint": _fingerprint(runtime_pi_version)}
            ),
        },
        "packages": packages,
        "inventory_observations": observations,
        "adapter_config": {
            "state": "configured" if config_count else "unconfigured",
            "recognized_source_count": config_count,
            "contents_exposed": False,
        },
        "specpi_scope_policy": "inactive_in_fresh_session",
        "snapshot_available": snapshot_path.is_file(),
        "compatibility": compatibility,
        "summary": f"{overall}: pi_global_capabilities managed={len(packages)}",
    }


def _snapshot_path(home: Path) -> Path:
    return home / STATE_REL / SNAPSHOT_NAME


def write_snapshot(home: Path, candidate_id: str) -> bool:
    path = _snapshot_path(home)
    if path.exists():
        return False
    settings = _settings(home)
    prior = _managed_entries(settings, rollback_safe=True)
    payload = {
        "schema_version": 1,
        "candidate_id": candidate_id,
        "packages_field_present": "packages" in settings,
        "prior_managed_packages": prior,
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    _atomic_json(path, payload, mode=0o600)
    return True


def _load_snapshot(home: Path, candidate_id: str) -> dict:
    payload = _load_json(_snapshot_path(home))
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or payload.get("candidate_id") != candidate_id
        or not isinstance(payload.get("prior_managed_packages"), list)
        or not isinstance(payload.get("packages_field_present"), bool)
    ):
        raise CapabilityDeliveryError("global capability snapshot is invalid or stale")
    seen: set[str] = set()
    for item in payload["prior_managed_packages"]:
        if (
            not isinstance(item, dict)
            or item.get("key") not in MANAGED
            or not isinstance(item.get("index"), int)
            or item["index"] < 0
        ):
            raise CapabilityDeliveryError("global capability snapshot entry is invalid")
        _validate_package_entry(item.get("entry"))
        source = _package_source(item["entry"])
        key = item["key"]
        if key in seen or _managed_key(source or "") != key:
            raise CapabilityDeliveryError("global capability snapshot identity is invalid")
        if _source_version(source or "", MANAGED[key]["package"]) is None:
            raise CapabilityDeliveryError("global capability snapshot source is not pinned")
        seen.add(key)
    return payload


def _pi_env(home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("PI_CODING_AGENT_DIR", None)
    return env


def _run_pi(home: Path, *args: str) -> None:
    proc = subprocess.run(
        ["pi", *args],
        cwd=str(home),
        env=_pi_env(home),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise CapabilityDeliveryError(
            f"Pi package operation failed: {args[0] if args else 'unknown'}"
        )


def _runtime_pi_version(home: Path) -> str:
    proc = subprocess.run(
        ["pi", "--version"],
        cwd=str(home),
        env=_pi_env(home),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise CapabilityDeliveryError("Pi version readback failed")
    return proc.stdout.strip()


def run_compatibility_smoke(
    home: Path,
    candidate_id: str,
    desired: dict[str, dict],
    expected_pi: str,
) -> None:
    env = _pi_env(home)
    env["PI_OFFLINE"] = "1"
    request_id = "pi-unraid-global-capabilities"
    try:
        proc = subprocess.run(
            ["pi", "--mode", "rpc", "--no-session", "--offline"],
            cwd=str(home),
            env=env,
            input=json.dumps({"id": request_id, "type": "get_commands"}) + "\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise CapabilityDeliveryError("Pi compatibility smoke timed out") from exc
    if proc.returncode != 0:
        raise CapabilityDeliveryError("Pi compatibility smoke failed")

    events = []
    try:
        events = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise CapabilityDeliveryError("Pi compatibility smoke returned invalid RPC output") from exc
    if any(item.get("type") == "extension_error" for item in events if isinstance(item, dict)):
        raise CapabilityDeliveryError("Pi compatibility smoke reported an extension error")

    responses = [
        item
        for item in events
        if isinstance(item, dict)
        and item.get("id") == request_id
        and item.get("type") == "response"
        and item.get("command") == "get_commands"
        and item.get("success") is True
    ]
    if len(responses) != 1:
        raise CapabilityDeliveryError("Pi compatibility smoke did not return command discovery")
    commands = responses[0].get("data", {}).get("commands", [])
    if not isinstance(commands, list):
        raise CapabilityDeliveryError("Pi compatibility smoke command discovery is malformed")

    expected_sources = {
        "scope": desired["specpi"]["source"],
        "wishlist": desired["specpi"]["source"],
        "harness-improvement": desired["specpi"]["source"],
        "mcp": desired["pi_mcp_adapter"]["source"],
        "pi-mcp": desired["pi_mcp_adapter"]["source"],
        "mcp-auth": desired["pi_mcp_adapter"]["source"],
    }
    discovered = {
        item.get("name"): item.get("sourceInfo", {}).get("source")
        for item in commands
        if isinstance(item, dict)
    }
    if any(discovered.get(name) != source for name, source in expected_sources.items()):
        raise CapabilityDeliveryError("Pi compatibility smoke command surface mismatch")

    scope_events = [
        item
        for item in events
        if isinstance(item, dict)
        and item.get("type") == "extension_ui_request"
        and item.get("method") == "setStatus"
        and item.get("statusKey") == "specpi-scope"
    ]
    if not scope_events or any(item.get("statusText") for item in scope_events):
        raise CapabilityDeliveryError("SpecPi scope is not inactive in the fresh compatibility session")

    runtime_pi = _runtime_pi_version(home)
    if runtime_pi != expected_pi:
        raise CapabilityDeliveryError("Pi runtime changed during compatibility smoke")
    payload = _compatibility_payload(candidate_id, desired, runtime_pi)
    path = _compatibility_path(home)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    _atomic_json(path, payload, mode=0o600)


def apply(home: Path, candidate_id: str, desired: dict[str, dict], expected_pi: str) -> dict:
    runtime_pi = _runtime_pi_version(home)
    before = build_status(
        home,
        candidate_id,
        desired,
        runtime_pi_version=runtime_pi,
        expected_pi_version=expected_pi,
    )
    if before["runtime_pi"]["state"] != "GREEN":
        raise CapabilityDeliveryError("Pi runtime version does not match the exact candidate")
    if before["in_sync"]:
        return {"action": "apply", "changed": False, **before}

    write_snapshot(home, candidate_id)
    _compatibility_path(home).unlink(missing_ok=True)
    try:
        for key in sorted(MANAGED):
            if not before["packages"][key]["installed_exact"]:
                _run_pi(home, "install", desired[key]["source"])
        run_compatibility_smoke(home, candidate_id, desired, expected_pi)
    except CapabilityDeliveryError as exc:
        try:
            rollback(home, candidate_id, desired, expected_pi)
        except CapabilityDeliveryError as rollback_exc:
            raise CapabilityDeliveryError(
                "Pi global capability apply failed and rollback did not complete"
            ) from rollback_exc
        raise CapabilityDeliveryError(
            "Pi global capability apply failed; prior managed state restored"
        ) from exc

    after = build_status(
        home,
        candidate_id,
        desired,
        runtime_pi_version=_runtime_pi_version(home),
        expected_pi_version=expected_pi,
    )
    if not after["in_sync"]:
        raise CapabilityDeliveryError("Pi global capability apply did not reach exact desired state")
    return {"action": "apply", "changed": True, **after}


def _merge_prior_managed(settings: dict, snapshot: dict) -> dict:
    current_packages = settings.get("packages", [])
    if not isinstance(current_packages, list):
        raise CapabilityDeliveryError("Pi settings packages must be an array")
    unrelated = []
    for entry in current_packages:
        source = _package_source(entry)
        if source is None or _managed_key(source) is None:
            unrelated.append(deepcopy(entry))
    merged = unrelated
    for item in sorted(snapshot["prior_managed_packages"], key=lambda value: value["index"]):
        index = min(item["index"], len(merged))
        merged.insert(index, deepcopy(item["entry"]))
    result = deepcopy(settings)
    if merged or snapshot["packages_field_present"]:
        result["packages"] = merged
    else:
        result.pop("packages", None)
    return result


def rollback(home: Path, candidate_id: str, desired: dict[str, dict], expected_pi: str) -> dict:
    snapshot = _load_snapshot(home, candidate_id)
    _compatibility_path(home).unlink(missing_ok=True)
    current = _settings(home)
    declared = {item["key"]: item for item in _managed_entries(current)}
    for key in sorted(MANAGED):
        installed = _installed_readback(home, MANAGED[key]["package"])
        if key in declared or installed["manifest_present"]:
            _run_pi(home, "remove", desired[key]["source"])

    for item in sorted(snapshot["prior_managed_packages"], key=lambda value: value["index"]):
        source = _package_source(item["entry"])
        assert source is not None
        _run_pi(home, "install", source)

    settings_after_ops = _settings(home)
    restored = _merge_prior_managed(settings_after_ops, snapshot)
    _atomic_json(home / SETTINGS_REL, restored)
    _snapshot_path(home).unlink()
    state_dir = home / STATE_REL
    try:
        state_dir.rmdir()
    except OSError:
        pass

    status = build_status(
        home,
        candidate_id,
        desired,
        runtime_pi_version=_runtime_pi_version(home),
        expected_pi_version=expected_pi,
    )
    return {
        "action": "rollback",
        "restored_prior_state": True,
        "desired_in_sync": status["in_sync"],
        **status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("apply", "status", "rollback"))
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--home", default=os.environ.get("HOME", ""))
    args = parser.parse_args()
    try:
        home = Path(args.home).resolve()
        if not home.is_dir():
            raise CapabilityDeliveryError("required HOME directory does not exist")
        candidate = _load_json(Path(args.candidate))
        desired = validate_candidate(candidate, dict(os.environ))
        candidate_id = candidate["candidate_id"]
        expected_pi = os.environ["PI_UNRAID_PI_VERSION"]
        if args.action == "apply":
            result = apply(home, candidate_id, desired, expected_pi)
        elif args.action == "rollback":
            result = rollback(home, candidate_id, desired, expected_pi)
        else:
            result = {
                "action": "status",
                **build_status(
                    home,
                    candidate_id,
                    desired,
                    runtime_pi_version=_runtime_pi_version(home),
                    expected_pi_version=expected_pi,
                ),
            }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        if args.action == "status" and not result["in_sync"]:
            return 1
        return 0
    except CapabilityDeliveryError as exc:
        print(
            json.dumps(
                {"ok": False, "error": "pi_global_capabilities", "message": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
