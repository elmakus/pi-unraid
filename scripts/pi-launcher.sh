#!/bin/sh
set -eu

manager="${PI_UNRAID_RUNTIME_MANAGER:-/usr/local/bin/pi-unraid-runtime}"
registry_root="${PI_UNRAID_MANAGED_ROOT:-/tmp/pi-unraid/managed-pi}"
stop_marker="$registry_root/stopping"
lock_file="$registry_root/.lock"

cli="$("$manager" select)" || {
  printf 'pi-unraid: no compatible Pi runtime is available; run pi-unraid-runtime status/retry\n' >&2
  exit 1
}

mkdir -p "$registry_root"
chmod 0700 "$registry_root"
umask 077

exec 9>"$lock_file"
flock -x 9
if [ -e "$stop_marker" ]; then
  flock -u 9
  exec 9>&-
  printf 'pi-unraid: service shutdown is in progress; refusing a new managed Pi launch\n' >&2
  exit 1
fi

start_time="$(awk '{print $22}' "/proc/$$/stat")"
uid="$(id -u)"
tmp="$(mktemp "$registry_root/.registration.$$.XXXXXX")"
printf '%s %s %s\n' "$$" "$start_time" "$uid" > "$tmp"
mv -f "$tmp" "$registry_root/$$.reg"
flock -u 9
exec 9>&-

provider="${PI_UNRAID_PROVIDER_HELPER:-/usr/local/bin/pi-unraid-provider}"
if [ -x "$provider" ]; then
  exec "$provider" exec "$cli" "$@"
fi
exec "$cli" "$@"
