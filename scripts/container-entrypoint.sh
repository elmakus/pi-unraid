#!/bin/sh
set -eu

fail() {
  printf 'pi-unraid init error: %s\n' "$*" >&2
  exit 1
}

is_uint() {
  case "$1" in
    ''|*[!0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

PI_UID="${PI_UID:-1000}"
PI_GID="${PI_GID:-1000}"

is_uint "$PI_UID" || fail "PI_UID must be a non-negative integer"
is_uint "$PI_GID" || fail "PI_GID must be a non-negative integer"
[ "$(id -u)" -eq 0 ] || fail "entrypoint must start as root so it can reconcile the service account"

uid_owner="$(getent passwd "$PI_UID" | cut -d: -f1 || true)"
gid_owner="$(getent group "$PI_GID" | cut -d: -f1 || true)"

[ -z "$uid_owner" ] || [ "$uid_owner" = "pi" ] || fail "requested PI_UID=$PI_UID is already used by user $uid_owner"
[ -z "$gid_owner" ] || [ "$gid_owner" = "pi" ] || fail "requested PI_GID=$PI_GID is already used by group $gid_owner"

current_gid="$(id -g pi)"
if [ "$current_gid" != "$PI_GID" ]; then
  groupmod --gid "$PI_GID" pi
fi

current_uid="$(id -u pi)"
if [ "$current_uid" != "$PI_UID" ]; then
  usermod --home /nonexistent pi
  usermod --uid "$PI_UID" pi
  usermod --home /home/pi pi
fi
usermod --gid "$PI_GID" pi

for path in /home/pi /projects /worktrees; do
  [ -d "$path" ] || fail "required mount target $path is not a directory"
done

if [ -z "$(find /home/pi -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  chown "$PI_UID:$PI_GID" /home/pi
fi

gosu pi test -r /home/pi || fail "/home/pi is not readable by PI_UID=$PI_UID PI_GID=$PI_GID"
gosu pi test -w /home/pi || fail "/home/pi is not writable by PI_UID=$PI_UID PI_GID=$PI_GID; fix host ownership instead of recursive takeover"
gosu pi test -x /home/pi || fail "/home/pi is not searchable by PI_UID=$PI_UID PI_GID=$PI_GID"

gosu pi mkdir -p /home/pi/.pi/agent

for path in /home/pi/.pi /home/pi/.pi/agent; do
  gosu pi test -r "$path" || fail "$path is not readable by the service user"
  gosu pi test -w "$path" || fail "$path is not writable by the service user"
  gosu pi test -x "$path" || fail "$path is not searchable by the service user"
done

for path in /projects /worktrees; do
  gosu pi test -r "$path" || fail "$path is not readable by the service user"
  gosu pi test -x "$path" || fail "$path is not searchable by the service user"
done

printf 'pi-unraid init: uid=%s gid=%s home=/home/pi\n' "$PI_UID" "$PI_GID"
exec gosu pi "$@"
