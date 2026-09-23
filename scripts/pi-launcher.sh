#!/bin/sh
set -eu

manager="${PI_UNRAID_RUNTIME_MANAGER:-/usr/local/bin/pi-unraid-runtime}"
cli="$("$manager" select)" || {
  printf 'pi-unraid: no compatible Pi runtime is available; run pi-unraid-runtime status/retry\n' >&2
  exit 1
}

exec "$cli" "$@"
