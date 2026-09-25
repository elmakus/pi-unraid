#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
  echo "usage: $(basename "$0") IMAGE HOME_HOST WORKTREES_HOST [UID] [GID]" >&2
  exit 2
fi

image="$1"
home_host="$2"
worktrees_host="$3"
uid="${4:-99}"
gid="${5:-100}"

for path in "$home_host" "$worktrees_host"; do
  if [ ! -d "$path" ]; then
    echo "paseo runtime config error: required host directory does not exist: $path" >&2
    exit 1
  fi
done

docker run --rm --user "$uid:$gid" \
  -v "$home_host:/home/paseo" \
  -v "$worktrees_host:/worktrees" \
  "$image" paseo daemon config set worktrees.root /worktrees --home /home/paseo/.paseo >/dev/null

docker run --rm --user "$uid:$gid" \
  -v "$home_host:/home/paseo" \
  "$image" python3 -c '
import json
from pathlib import Path
cfg = json.loads(Path("/home/paseo/.paseo/config.json").read_text())
assert cfg["worktrees"]["root"] == "/worktrees", cfg
'
