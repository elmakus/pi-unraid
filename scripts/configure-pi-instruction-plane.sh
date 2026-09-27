#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
  echo "usage: $(basename "$0") {apply|status|rollback} IMAGE HOME_HOST [UID] [GID]" >&2
  exit 2
fi

action="$1"
image="$2"
home_host="$3"
uid="${4:-99}"
gid="${5:-100}"

case "$action" in
  apply|status|rollback) ;;
  *)
    echo "pi instruction-plane error: unsupported action: $action" >&2
    exit 2
    ;;
esac

if [ ! -d "$home_host" ]; then
  echo "pi instruction-plane error: required HOME directory does not exist: $home_host" >&2
  exit 1
fi

docker run --rm --user "$uid:$gid" \
  -v "$home_host:/home/paseo" \
  -v "$repo_root/config/pi-agent:/instruction-source:ro" \
  -v "$repo_root/scripts/pi_instruction_plane.py:/instruction-installer.py:ro" \
  "$image" python3 /instruction-installer.py "$action" /instruction-source /home/paseo
