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
    echo "pi global-capabilities error: unsupported action: $action" >&2
    exit 2
    ;;
esac

if [ ! -d "$home_host" ]; then
  echo "pi global-capabilities error: required HOME directory does not exist: $home_host" >&2
  exit 1
fi

docker run --rm --user "$uid:$gid" \
  -v "$home_host:/home/paseo" \
  -v "$repo_root/config/paseo-candidate.json:/candidate.json:ro" \
  -v "$repo_root/scripts/pi_global_capabilities.py:/global-capabilities.py:ro" \
  "$image" python3 /global-capabilities.py \
    "$action" --candidate /candidate.json --home /home/paseo
