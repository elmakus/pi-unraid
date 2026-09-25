#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path

import unraid_graphql_host_control as graphql_control
import unraid_ssh_fallback as ssh_fallback
from unraid_host_safety_guard import GuardError, load_policy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / "config" / "unraid-host-control" / "host-safety-policy.json"

GRAPHQL_OPERATIONS = {
    "graphql_container_start",
    "graphql_container_stop",
    "graphql_container_restart",
    "graphql_container_pause",
    "graphql_container_unpause",
}
GATED_SSH_OPERATIONS = {
    "ssh_admin_command",
    "host_reboot",
    "docker_engine_restart",
    "unraid_os_upgrade",
    "disk_format",
    "broad_share_delete",
    "broad_appdata_delete",
    "broad_network_change",
}
REQUIRED_FALLBACK_REASONS = {
    "api_gap",
    "api_outage",
    "os_plugin_filesystem_recovery",
    "forced_test",
}


def emit(payload: dict, *, stream=sys.stdout) -> None:
    print(json.dumps(payload, sort_keys=True), file=stream)


def _credential_metadata(path_value: str | None, key: str) -> dict:
    raw_path = path_value or __import__("os").environ.get("UNRAID_API_KEY_FILE", "")
    path = Path(raw_path)
    mode = stat.S_IMODE(path.stat().st_mode)
    return {
        "mode": format(mode, "03o"),
        "fingerprint": "sha256:" + hashlib.sha256(key.encode()).hexdigest()[:16],
    }


def policy_check(policy: dict) -> dict:
    try:
        if policy.get("primary_transport") != "graphql":
            raise GuardError("policy", "primary transport is not graphql")
        reasons = set(policy.get("allowed_fallback_reasons", []))
        if not REQUIRED_FALLBACK_REASONS.issubset(reasons):
            raise GuardError("policy", "required fallback reasons are missing")
        ordinary = policy.get("ordinary_operations", {})
        gated = policy.get("gated_operations", {})
        for operation in GRAPHQL_OPERATIONS:
            rule = ordinary.get(operation)
            if not isinstance(rule, dict):
                raise GuardError("policy", "required GraphQL operation is missing", operation=operation)
            if (
                rule.get("transport") != "graphql"
                or rule.get("mutating") is not True
                or rule.get("pre_readback") != "transport_internal"
                or rule.get("user_gate") != "none"
                or rule.get("rollback_anchor") != "pre_state"
            ):
                raise GuardError("policy", "GraphQL safety rule drift detected", operation=operation)
        for operation in GATED_SSH_OPERATIONS:
            rule = gated.get(operation)
            if not isinstance(rule, dict):
                raise GuardError("policy", "required gated SSH operation is missing", operation=operation)
            if (
                rule.get("transport") != "ssh"
                or rule.get("mutating") is not True
                or rule.get("pre_readback") != "evidence_file"
                or rule.get("user_gate") != "external_user_authorization"
                or rule.get("rollback_anchor") != "required"
            ):
                raise GuardError("policy", "gated SSH safety rule drift detected", operation=operation)
        if policy.get("unknown_operation_policy") != "deny":
            raise GuardError("policy", "unknown operations do not fail closed")
        return {
            "state": "GREEN",
            "primary_transport": "graphql",
            "ordinary_graphql_operations": len(GRAPHQL_OPERATIONS),
            "gated_ssh_operations": len(GATED_SSH_OPERATIONS),
            "unknown_operation_policy": "deny",
        }
    except GuardError as exc:
        return {
            "state": "RED",
            "error": exc.kind,
            "message": exc.message,
            **exc.details,
        }


def graphql_check(endpoint: str | None, api_key_file: str | None) -> dict:
    try:
        endpoint_value = graphql_control.endpoint_from_args(endpoint)
        key = graphql_control.load_api_key(api_key_file)
        credential = _credential_metadata(api_key_file, key)
        data = graphql_control.graphql(
            endpoint_value,
            key,
            graphql_control.READBACK_QUERY,
        )
        info = data.get("info")
        docker = data.get("docker")
        containers = docker.get("containers") if isinstance(docker, dict) else None
        if not isinstance(info, dict) or not isinstance(containers, list):
            raise graphql_control.HostControlError(
                "protocol",
                "GraphQL doctor readback is missing INFO or DOCKER data",
            )
        return {
            "state": "GREEN",
            "transport": "graphql",
            "endpoint": endpoint_value,
            "credential": credential,
            "capabilities": {
                "info_readback": True,
                "docker_readback": True,
                "container_count": len(containers),
            },
        }
    except (graphql_control.HostControlError, OSError) as exc:
        kind = getattr(exc, "kind", "credential")
        message = getattr(exc, "message", "GraphQL credential metadata is unavailable")
        details = getattr(exc, "details", {})
        http_status = details.get("status") if isinstance(details, dict) else None
        if kind == "http" and http_status in {401, 403}:
            kind = "auth"
        result = {
            "state": "RED",
            "transport": "graphql",
            "error": kind,
            "message": message,
        }
        if isinstance(http_status, int):
            result["http_status"] = http_status
        return result


def ssh_check(
    *,
    host: str | None,
    user: str | None,
    identity_file: str | None,
    known_hosts_file: str | None,
    depth: str,
    policy: dict,
) -> dict:
    values = (host, user, identity_file, known_hosts_file)
    if not any(values):
        return {
            "state": "WARN",
            "transport": "ssh",
            "configured": False,
            "message": "SSH fallback is not configured in this doctor invocation",
        }
    if not all(values):
        return {
            "state": "WARN",
            "transport": "ssh",
            "configured": False,
            "message": "SSH fallback configuration is incomplete",
        }
    try:
        config = ssh_fallback.validate_config(host, user, identity_file, known_hosts_file)
        result = {
            "state": "GREEN",
            "transport": "ssh",
            "configured": True,
            "host": config["host"],
            "user": config["user"],
            "identity_mode": config["identity_mode"],
            "known_hosts_mode": config["known_hosts_mode"],
            "identity_fingerprint": config["identity_fingerprint"],
            "reachability": "not_checked",
        }
        if depth == "full":
            probe = ssh_fallback.probe(config, reason="forced_test", policy=policy)
            result["reachability"] = probe.get("probe", "GREEN")
        return result
    except ssh_fallback.SshFallbackError as exc:
        return {
            "state": "WARN",
            "transport": "ssh",
            "configured": True,
            "error": exc.kind,
            "message": exc.message,
        }


def aggregate_state(graphql: dict, ssh: dict, policy: dict) -> str:
    if graphql.get("state") == "RED" or policy.get("state") == "RED":
        return "RED"
    if ssh.get("state") != "GREEN":
        return "WARN"
    return "GREEN"


def doctor(
    *,
    endpoint: str | None,
    api_key_file: str | None,
    ssh_host: str | None,
    ssh_user: str | None,
    ssh_identity_file: str | None,
    ssh_known_hosts_file: str | None,
    depth: str,
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> dict:
    try:
        policy = load_policy(policy_path)
        policy_status = policy_check(policy)
    except GuardError as exc:
        policy = {}
        policy_status = {
            "state": "RED",
            "error": exc.kind,
            "message": exc.message,
        }

    graphql_status = graphql_check(endpoint, api_key_file)
    ssh_status = ssh_check(
        host=ssh_host,
        user=ssh_user,
        identity_file=ssh_identity_file,
        known_hosts_file=ssh_known_hosts_file,
        depth=depth,
        policy=policy,
    )
    state = aggregate_state(graphql_status, ssh_status, policy_status)
    summary = (
        f"{state}: GraphQL={graphql_status.get('state')} "
        f"SSH={ssh_status.get('state')} policy={policy_status.get('state')} depth={depth}"
    )
    return {
        "ok": state != "RED",
        "state": state,
        "doctor": "unraid_host_control",
        "depth": depth,
        "primary_transport": "graphql",
        "checks": {
            "graphql": graphql_status,
            "ssh": ssh_status,
            "safety_policy": policy_status,
        },
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint")
    parser.add_argument("--api-key-file")
    parser.add_argument("--ssh-host")
    parser.add_argument("--ssh-user")
    parser.add_argument("--ssh-identity-file")
    parser.add_argument("--ssh-known-hosts-file")
    parser.add_argument("--depth", choices=("quick", "full"), default="quick")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY_PATH))
    args = parser.parse_args()

    result = doctor(
        endpoint=args.endpoint,
        api_key_file=args.api_key_file,
        ssh_host=args.ssh_host,
        ssh_user=args.ssh_user,
        ssh_identity_file=args.ssh_identity_file,
        ssh_known_hosts_file=args.ssh_known_hosts_file,
        depth=args.depth,
        policy_path=Path(args.policy),
    )
    emit(result)
    print(result["summary"], file=sys.stderr)
    return 1 if result["state"] == "RED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
