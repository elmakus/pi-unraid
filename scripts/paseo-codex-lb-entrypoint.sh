#!/bin/sh
set -eu

secret_file="${PI_CODEX_LB_SECRET_FILE:-/run/secrets/pi-unraid-codex-lb}"
upstream_entrypoint="${PI_UNRAID_PASEO_UPSTREAM_ENTRYPOINT:-/usr/local/libexec/pi-unraid/paseo-docker-entrypoint.upstream}"

fail() {
  printf 'pi-unraid Paseo init error: %s\n' "$*" >&2
  exit 1
}

read_secret() {
  python3 - "$secret_file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
try:
    text = path.read_text(encoding="utf-8")
except Exception:
    raise SystemExit(20)

lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
if len(lines) != 1:
    raise SystemExit(21)
line = lines[0]
if "=" in line:
    name, value = line.split("=", 1)
    if name != "CODEX_LB_API_KEY":
        raise SystemExit(21)
else:
    value = line
value = value.strip()
if not value or any(ch.isspace() for ch in value) or "\x00" in value:
    raise SystemExit(21)
sys.stdout.write(value)
PY
}

# Never inherit a stale credential from image/Compose configuration. The only
# accepted source is the dedicated runtime secret file.
unset CODEX_LB_API_KEY || true
if [ -s "$secret_file" ]; then
  if key="$(read_secret)"; then
    export CODEX_LB_API_KEY="$key"
  else
    fail "dedicated Codex-LB secret is non-empty but invalid"
  fi
fi

[ -x "$upstream_entrypoint" ] || fail "pinned upstream Paseo entrypoint is unavailable"
exec "$upstream_entrypoint" "$@"
