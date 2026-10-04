#!/bin/sh
# M07-T05 candidate-local Meta auth loader (test-owned, ephemeral).
# Shell builtins only (read/case/export/exec): no sed/awk/tr/head/cat
# dependency beyond the executable itself. Invoked via bash by the
# validator dispatch, like the canonical guard.
set -eu
ptr="${META_API_KEY_FILE:-/run/secrets/pi-unraid-meta}"
if [ ! -f "$ptr" ]; then echo 'M07-T05 loader: META_API_KEY_FILE unavailable' >&2; exit 42; fi
count=0
auth_name='META_API_KEY'
val=""
while read -r line || [ -n "$line" ]; do
  case "$line" in ""|\#*) continue ;; esac
  count=$((count+1))
  case "$line" in
    *=*)
      name="${line%%=*}"
      if [ "$name" != "$auth_name" ]; then echo 'M07-T05 loader: unexpected credential entry' >&2; exit 42; fi
      val="${line#*=}" ;;
    *) val="$line" ;;
  esac
done < "$ptr"
if [ "$count" -ne 1 ]; then echo 'M07-T05 loader: credential must hold exactly one entry' >&2; exit 42; fi
case "$val" in ""|*[[:space:]]*) echo 'M07-T05 loader: dedicated Muse credential is empty or invalid' >&2; exit 42 ;; esac
export "${auth_name}=${val}"
exec "$@"
