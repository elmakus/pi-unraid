#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import unraid_graphql_host_control as graphql_control
import unraid_ssh_fallback as ssh_fallback
from unraid_host_safety_guard import GuardError, load_policy

EXPLICIT_FALLBACK_REASONS = {"api_gap", "os_plugin_filesystem_recovery", "forced_test"}
OUTAGE_HTTP_STATUSES = {502, 503, 504}


class RouterError(RuntimeError):
    def __init__(self, kind: str, message: str, **details: object):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.details = details


def emit(payload: dict, *, stream=sys.stdout) -> None:
    print(json.dumps(payload, sort_keys=True), file=stream)


def graphql_readback(endpoint: str, api_key_file: str) -> dict:
    endpoint_value = graphql_control.endpoint_from_args(endpoint)
    key = graphql_control.load_api_key(api_key_file)
    return graphql_control.graphql(endpoint_value, key, graphql_control.READBACK_QUERY)


def should_fallback(exc: graphql_control.HostControlError) -> bool:
    if exc.kind == "transport":
        return True
    if exc.kind == "http" and exc.details.get("status") in OUTAGE_HTTP_STATUSES:
        return True
    return False


def routed_readback(
    *,
    endpoint: str,
    api_key_file: str,
    ssh_config: dict,
    explicit_reason: str | None,
    policy: dict,
) -> dict:
    if explicit_reason is not None:
        if explicit_reason not in EXPLICIT_FALLBACK_REASONS:
            raise RouterError("policy", "explicit fallback reason is not permitted", reason=explicit_reason)
        result = ssh_fallback.readback(ssh_config, reason=explicit_reason, policy=policy)
        return {**result, "primary_transport": "graphql", "primary_attempted": False}
    try:
        data = graphql_readback(endpoint, api_key_file)
        return {
            "ok": True,
            "transport": "graphql",
            "primary_transport": "graphql",
            "primary_attempted": True,
            "fallback_reason": None,
            "data": data,
        }
    except graphql_control.HostControlError as exc:
        if not should_fallback(exc):
            raise RouterError(
                "primary_failed_closed",
                "GraphQL primary failed with a non-fallback error",
                primary_error=exc.kind,
            ) from exc
        result = ssh_fallback.readback(ssh_config, reason="api_outage", policy=policy)
        return {**result, "primary_transport": "graphql", "primary_attempted": True, "primary_error": exc.kind}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--api-key-file", required=True)
    parser.add_argument("--ssh-host", required=True)
    parser.add_argument("--ssh-user", required=True)
    parser.add_argument("--ssh-identity-file", required=True)
    parser.add_argument("--ssh-known-hosts-file", required=True)
    parser.add_argument(
        "--policy",
        default=str(Path(__file__).resolve().parents[1] / "config" / "unraid-host-control" / "host-safety-policy.json"),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    readback = sub.add_parser("readback")
    readback.add_argument("--fallback-reason", choices=sorted(EXPLICIT_FALLBACK_REASONS))
    args = parser.parse_args()
    try:
        policy = load_policy(Path(args.policy))
        ssh_config = ssh_fallback.validate_config(
            args.ssh_host, args.ssh_user, args.ssh_identity_file, args.ssh_known_hosts_file
        )
        emit(routed_readback(
            endpoint=args.endpoint,
            api_key_file=args.api_key_file,
            ssh_config=ssh_config,
            explicit_reason=args.fallback_reason,
            policy=policy,
        ))
        return 0
    except (RouterError, ssh_fallback.SshFallbackError, GuardError) as exc:
        emit({"ok": False, "error": exc.kind, "message": exc.message, **exc.details}, stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
