#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / "config" / "unraid-host-control" / "host-safety-policy.json"


class GuardError(RuntimeError):
    def __init__(self, kind: str, message: str, **details: object):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.details = details


def emit(payload: dict, *, stream=sys.stdout) -> None:
    print(json.dumps(payload, sort_keys=True), file=stream)


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> dict:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise GuardError("policy", "host-safety policy is unreadable or invalid") from exc
    if payload.get("schema_version") != 1:
        raise GuardError("policy", "unsupported host-safety policy schema")
    return payload


def operation_rule(policy: dict, operation: str) -> tuple[str, dict]:
    ordinary = policy.get("ordinary_operations", {})
    gated = policy.get("gated_operations", {})
    if operation in ordinary:
        return "ordinary", ordinary[operation]
    if operation in gated:
        return "gated", gated[operation]
    raise GuardError("policy", "operation is not classified and is denied", operation=operation)


def _validated_argv(argv: list[str]) -> list[str]:
    if not argv or any(not isinstance(item, str) or not item for item in argv):
        raise GuardError("configuration", "command argv must contain non-empty strings")
    return argv


def command_scope(argv: list[str]) -> str:
    canonical = json.dumps(_validated_argv(argv), separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def operation_scope(operation: str, argv: list[str]) -> str:
    if not isinstance(operation, str) or not operation:
        raise GuardError("configuration", "operation class is required")
    canonical = json.dumps(
        {"operation": operation, "argv": _validated_argv(argv)},
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode()
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _load_evidence(path_value: str | None, *, private: bool, kind: str, scope: str) -> dict:
    if not path_value:
        raise GuardError("gate", f"{kind} evidence is required")
    path = Path(path_value)
    if path.is_symlink():
        raise GuardError("gate", f"{kind} evidence must not be a symlink")
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise GuardError("gate", f"{kind} evidence does not exist") from exc
    if not stat.S_ISREG(st.st_mode):
        raise GuardError("gate", f"{kind} evidence must be a regular file")
    mode = stat.S_IMODE(st.st_mode)
    if private and mode & 0o077:
        raise GuardError("gate", f"{kind} evidence must be private", mode=format(mode, "03o"))
    if not private and mode & 0o022:
        raise GuardError("gate", f"{kind} evidence must not be group/other writable", mode=format(mode, "03o"))
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise GuardError("gate", f"{kind} evidence is invalid") from exc
    if payload.get("schema_version") != 1 or payload.get("kind") != kind or payload.get("scope") != scope:
        raise GuardError("gate", f"{kind} evidence does not bind the exact operation scope")
    if payload.get("ok") is not True:
        raise GuardError("gate", f"{kind} evidence is not GREEN")
    return payload


def evaluate(
    operation: str,
    *,
    scope: str,
    pre_readback_file: str | None = None,
    authorization_file: str | None = None,
    rollback_anchor_file: str | None = None,
    policy: dict | None = None,
) -> dict:
    policy = policy or load_policy()
    classification, rule = operation_rule(policy, operation)
    transport = rule.get("transport")
    mutating = bool(rule.get("mutating"))
    pre_readback = rule.get("pre_readback", "none")
    gate = rule.get("user_gate", "none")
    rollback = rule.get("rollback_anchor", "none")

    if mutating and pre_readback == "evidence_file":
        _load_evidence(pre_readback_file, private=False, kind="pre_mutation_readback", scope=scope)
    if gate == "external_user_authorization":
        _load_evidence(authorization_file, private=True, kind="external_user_authorization", scope=scope)
    if rollback == "required":
        _load_evidence(rollback_anchor_file, private=False, kind="rollback_anchor", scope=scope)
    elif rollback not in {"none", "pre_state", "automatic_cleanup"}:
        raise GuardError("policy", "unsupported rollback-anchor policy", operation=operation, rollback_anchor=rollback)

    return {
        "ok": True,
        "operation": operation,
        "classification": classification,
        "transport": transport,
        "mutating": mutating,
        "scope": scope,
        "pre_readback": pre_readback,
        "user_gate": gate,
        "rollback_anchor": rollback,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default=str(DEFAULT_POLICY_PATH))
    sub = parser.add_subparsers(dest="command", required=True)
    classify = sub.add_parser("classify")
    classify.add_argument("--operation", required=True)
    check = sub.add_parser("check")
    check.add_argument("--operation", required=True)
    check.add_argument("--scope", required=True)
    check.add_argument("--pre-readback-file")
    check.add_argument("--authorization-file")
    check.add_argument("--rollback-anchor-file")
    args = parser.parse_args()
    try:
        policy = load_policy(Path(args.policy))
        if args.command == "classify":
            classification, rule = operation_rule(policy, args.operation)
            emit({"ok": True, "operation": args.operation, "classification": classification, "rule": rule})
            return 0
        emit(evaluate(
            args.operation,
            scope=args.scope,
            pre_readback_file=args.pre_readback_file,
            authorization_file=args.authorization_file,
            rollback_anchor_file=args.rollback_anchor_file,
            policy=policy,
        ))
        return 0
    except GuardError as exc:
        emit({"ok": False, "error": exc.kind, "message": exc.message, **exc.details}, stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
