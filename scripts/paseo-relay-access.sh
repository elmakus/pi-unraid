#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
compose=(docker compose -f "$repo_root/compose.yaml")
action="${1:-}"

require_running() {
  local cid
  cid="$("${compose[@]}" ps -q paseo)"
  if [ -z "$cid" ]; then
    echo "paseo access error: paseo service is not running" >&2
    exit 1
  fi
}

require_tty() {
  if [ ! -t 0 ] || [ ! -t 1 ]; then
    echo "paseo access error: this action requires an interactive terminal" >&2
    exit 1
  fi
}

case "$action" in
  status)
    require_running
    "${compose[@]}" exec -T paseo python3 -c '
import json
import os
import stat
from pathlib import Path

home = Path("/home/paseo/.paseo")
cfg = json.loads((home / "config.json").read_text())
key = home / "daemon-keypair.json"
result = {
    "relay_enabled": bool(cfg.get("daemon", {}).get("relay", {}).get("enabled", False)),
    "daemon_keypair": {
        "present": key.is_file(),
        "mode": format(stat.S_IMODE(key.stat().st_mode), "03o") if key.exists() else None,
        "uid": key.stat().st_uid if key.exists() else None,
        "gid": key.stat().st_gid if key.exists() else None,
    },
    "pairing_requires_human_action": True,
    "device_revocation_cli": "unsupported",
}
print(json.dumps(result, sort_keys=True))
'
    ;;

  pair)
    require_running
    require_tty
    echo "Pairing offer/QR is a trust anchor. Keep this terminal private." >&2
    echo "Paseo will ask before enabling Relay; the default answer is no." >&2
    exec "${compose[@]}" exec paseo paseo daemon pair --home /home/paseo/.paseo
    ;;

  auth-shell)
    require_running
    require_tty
    echo "Use native provider/account authentication only inside this interactive HOME-backed shell." >&2
    echo "Do not pass credentials as command-line arguments or commit them to Git." >&2
    exec "${compose[@]}" exec -w /home/paseo paseo sh
    ;;

  revocation-capability)
    # Paseo v0.9.2 exposes pairing offers but no CLI surface for listing or
    # individually revoking paired device credentials. Fail closed instead of
    # pretending that deleting daemon identity is equivalent to device revoke.
    printf '%s\n' '{"supported":false,"candidate":"paseo-0.9.2","reason":"no-individual-device-revocation-cli"}'
    ;;

  *)
    echo "usage: $(basename "$0") {status|pair|auth-shell|revocation-capability}" >&2
    exit 2
    ;;
esac
