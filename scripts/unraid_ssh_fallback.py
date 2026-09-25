#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import stat
import subprocess
import sys
from pathlib import Path

from unraid_host_safety_guard import GuardError, command_scope, evaluate, load_policy

HOST_PATTERN = re.compile(r"^[A-Za-z0-9.-]+$")
USER_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
SMOKE_MARKER = "/tmp/pi-unraid-host-control-smoke"


class SshFallbackError(RuntimeError):
    def __init__(self, kind: str, message: str, **details: object):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.details = details


def emit(payload: dict, *, stream=sys.stdout) -> None:
    print(json.dumps(payload, sort_keys=True), file=stream)


def _regular_file(path_value: str, *, private: bool, label: str) -> tuple[Path, int]:
    path = Path(path_value)
    if path.is_symlink():
        raise SshFallbackError("credential", f"{label} must not be a symlink")
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise SshFallbackError("credential", f"{label} does not exist") from exc
    if not stat.S_ISREG(st.st_mode):
        raise SshFallbackError("credential", f"{label} must be a regular file")
    mode = stat.S_IMODE(st.st_mode)
    if private and mode & 0o077:
        raise SshFallbackError("credential", f"{label} must be private", mode=format(mode, "03o"))
    if not private and mode & 0o022:
        raise SshFallbackError("credential", f"{label} must not be group/other writable", mode=format(mode, "03o"))
    return path, mode


def validate_config(host: str, user: str, identity_file: str, known_hosts_file: str) -> dict:
    if not HOST_PATTERN.fullmatch(host) or host.startswith("-"):
        raise SshFallbackError("configuration", "SSH host has an invalid format")
    if not USER_PATTERN.fullmatch(user) or user.startswith("-"):
        raise SshFallbackError("configuration", "SSH user has an invalid format")
    identity, identity_mode = _regular_file(identity_file, private=True, label="SSH identity file")
    known_hosts, known_hosts_mode = _regular_file(known_hosts_file, private=False, label="SSH known_hosts file")
    fingerprint = "sha256:" + hashlib.sha256(identity.read_bytes()).hexdigest()[:16]
    return {
        "host": host,
        "user": user,
        "identity_file": str(identity),
        "known_hosts_file": str(known_hosts),
        "identity_mode": format(identity_mode, "03o"),
        "known_hosts_mode": format(known_hosts_mode, "03o"),
        "identity_fingerprint": fingerprint,
    }


def ssh_argv(config: dict, remote_command: str) -> list[str]:
    return [
        "ssh", "-F", "/dev/null",
        "-o", "BatchMode=yes",
        "-o", "PasswordAuthentication=no",
        "-o", "KbdInteractiveAuthentication=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", f"UserKnownHostsFile={config['known_hosts_file']}",
        "-o", "ConnectTimeout=10",
        "-i", config["identity_file"],
        "--", f"{config['user']}@{config['host']}", remote_command,
    ]


def run_remote(config: dict, remote_command: str, *, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(
            ssh_argv(config, remote_command),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SshFallbackError("transport", "SSH fallback transport failed") from exc
    if proc.returncode != 0:
        raise SshFallbackError(
            "remote",
            "SSH fallback command failed",
            returncode=proc.returncode,
            stderr_sha256="sha256:" + hashlib.sha256(proc.stderr.encode()).hexdigest()[:16],
        )
    return proc


def ensure_reason(reason: str, policy: dict) -> None:
    if reason not in policy.get("allowed_fallback_reasons", []):
        raise SshFallbackError("policy", "SSH fallback reason is not allowlisted", reason=reason)


def status(config: dict) -> dict:
    return {
        "ok": True,
        "transport": "ssh",
        "host": config["host"],
        "user": config["user"],
        "identity_mode": config["identity_mode"],
        "known_hosts_mode": config["known_hosts_mode"],
        "identity_fingerprint": config["identity_fingerprint"],
    }


def probe(config: dict, *, reason: str, policy: dict) -> dict:
    ensure_reason(reason, policy)
    proc = run_remote(config, "printf '%s\\n' __PI_UNRAID_SSH_GREEN__")
    if proc.stdout.strip() != "__PI_UNRAID_SSH_GREEN__":
        raise SshFallbackError("protocol", "SSH fallback probe returned unexpected output")
    return {"ok": True, "transport": "ssh", "fallback_reason": reason, "probe": "GREEN"}


def readback(config: dict, *, reason: str, policy: dict) -> dict:
    ensure_reason(reason, policy)
    command = "printf 'kernel='; uname -srm; printf 'hostname='; hostname; printf 'uid='; id -u"
    proc = run_remote(config, command)
    fields: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in {"kernel", "hostname", "uid"}:
            fields[key] = value
    if set(fields) != {"kernel", "hostname", "uid"}:
        raise SshFallbackError("protocol", "SSH fallback readback was incomplete")
    return {"ok": True, "transport": "ssh", "fallback_reason": reason, "data": fields}


def smoke_marker(config: dict, *, reason: str, policy: dict) -> dict:
    ensure_reason(reason, policy)
    if reason != "forced_test":
        raise SshFallbackError("policy", "smoke-marker mutation is restricted to forced_test")
    pre = run_remote(
        config,
        f"if test -e {shlex.quote(SMOKE_MARKER)}; then printf present; else printf absent; fi",
    ).stdout.strip()
    if pre != "absent":
        raise SshFallbackError("pre_readback", "smoke marker already exists; refusing to mutate")
    created = False
    try:
        run_remote(config, f"touch -- {shlex.quote(SMOKE_MARKER)}")
        created = True
        post = run_remote(
            config,
            f"if test -f {shlex.quote(SMOKE_MARKER)}; then printf present; else printf absent; fi",
        ).stdout.strip()
        if post != "present":
            raise SshFallbackError("post_readback", "smoke marker post-readback failed")
    finally:
        if created:
            run_remote(config, f"rm -f -- {shlex.quote(SMOKE_MARKER)}")
            restored = run_remote(
                config,
                f"if test -e {shlex.quote(SMOKE_MARKER)}; then printf present; else printf absent; fi",
            ).stdout.strip()
            if restored != "absent":
                raise SshFallbackError("rollback", "smoke marker cleanup did not restore pre-state")
    return {
        "ok": True,
        "transport": "ssh",
        "fallback_reason": reason,
        "operation": "ssh_forced_smoke_marker",
        "pre_state": "absent",
        "post_state": "present",
        "restored_state": "absent",
        "rollback": "automatic_cleanup",
    }


def _load_command_file(path_value: str) -> dict:
    path, _ = _regular_file(path_value, private=False, label="SSH command file")
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SshFallbackError("configuration", "SSH command file is invalid") from exc
    argv = payload.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        raise SshFallbackError("configuration", "SSH command file must contain non-empty argv strings")
    if payload.get("schema_version") != 1:
        raise SshFallbackError("configuration", "unsupported SSH command-file schema")
    return payload


def gated_exec(
    config: dict,
    *,
    reason: str,
    command_file: str,
    authorization_file: str,
    pre_readback_file: str,
    rollback_anchor_file: str | None,
    policy: dict,
) -> dict:
    ensure_reason(reason, policy)
    payload = _load_command_file(command_file)
    argv = payload["argv"]
    scope = command_scope(argv)
    rollback_applicable = bool(payload.get("rollback_applicable", False))
    try:
        decision = evaluate(
            "ssh_admin_command",
            scope=scope,
            pre_readback_file=pre_readback_file,
            authorization_file=authorization_file,
            rollback_anchor_file=rollback_anchor_file,
            rollback_applicable=rollback_applicable,
            policy=policy,
        )
    except GuardError as exc:
        raise SshFallbackError(exc.kind, exc.message, **exc.details) from exc
    remote_command = " ".join(shlex.quote(item) for item in argv)
    proc = run_remote(config, remote_command, timeout=60)
    return {
        "ok": True,
        "transport": "ssh",
        "fallback_reason": reason,
        "operation": "ssh_admin_command",
        "scope": scope,
        "returncode": proc.returncode,
        "stdout_bytes": len(proc.stdout.encode()),
        "stderr_bytes": len(proc.stderr.encode()),
        "stdout_sha256": "sha256:" + hashlib.sha256(proc.stdout.encode()).hexdigest()[:16],
        "stderr_sha256": "sha256:" + hashlib.sha256(proc.stderr.encode()).hexdigest()[:16],
        "guard": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--identity-file", required=True)
    parser.add_argument("--known-hosts-file", required=True)
    parser.add_argument(
        "--policy",
        default=str(Path(__file__).resolve().parents[1] / "config" / "unraid-host-control" / "host-safety-policy.json"),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    for name in ("probe", "readback", "smoke-marker"):
        item = sub.add_parser(name)
        item.add_argument("--reason", required=True)
    gated = sub.add_parser("exec-gated")
    gated.add_argument("--reason", required=True)
    gated.add_argument("--command-file", required=True)
    gated.add_argument("--authorization-file", required=True)
    gated.add_argument("--pre-readback-file", required=True)
    gated.add_argument("--rollback-anchor-file")
    args = parser.parse_args()
    try:
        policy = load_policy(Path(args.policy))
        config = validate_config(args.host, args.user, args.identity_file, args.known_hosts_file)
        if args.command == "status":
            emit(status(config))
        elif args.command == "probe":
            emit(probe(config, reason=args.reason, policy=policy))
        elif args.command == "readback":
            emit(readback(config, reason=args.reason, policy=policy))
        elif args.command == "smoke-marker":
            emit(smoke_marker(config, reason=args.reason, policy=policy))
        else:
            emit(gated_exec(
                config,
                reason=args.reason,
                command_file=args.command_file,
                authorization_file=args.authorization_file,
                pre_readback_file=args.pre_readback_file,
                rollback_anchor_file=args.rollback_anchor_file,
                policy=policy,
            ))
        return 0
    except (SshFallbackError, GuardError) as exc:
        kind = getattr(exc, "kind", "policy")
        message = getattr(exc, "message", str(exc))
        details = getattr(exc, "details", {})
        emit({"ok": False, "error": kind, "message": message, **details}, stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
