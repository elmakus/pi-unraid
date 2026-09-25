#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$#" -ge 1 ]; then image="$1"; else image="pi-unraid:paseo-foundation"; fi
tmpbase="/tmp"
if printenv TMPDIR >/dev/null 2>&1; then tmpbase="$TMPDIR"; fi
fixture="$(mktemp -d "$tmpbase/pi-unraid-m02-t01.XXXXXX")"
project="piunraid-m02-t01-$$"
uid="$(printenv PASEO_TEST_UID || true)"
gid="$(printenv PASEO_TEST_GID || true)"
[ -n "$uid" ] || uid=99
[ -n "$gid" ] || gid=100

export PASEO_UID="$uid"
export PASEO_GID="$gid"
export PASEO_HOME_HOST="$fixture/home"
export PASEO_PROJECTS_HOST="$fixture/projects"
export PASEO_WORKTREES_HOST="$fixture/worktrees"

dc() {
  docker compose -p "$project" -f "$repo_root/compose.yaml" -f "$fixture/compose.fixture.yaml" "$@"
}

cleanup() {
  dc down -v >/dev/null 2>&1 || true
  docker run --rm --user 0:0 --entrypoint chown \
    -v "$fixture:/fixture" \
    "$image" -R "$(id -u):$(id -g)" /fixture >/dev/null 2>&1 || true
  rm -rf "$fixture"
}
trap cleanup EXIT

mkdir -p "$fixture/home" "$fixture/projects" "$fixture/worktrees"

docker run --rm --user 0:0 --entrypoint chown \
  -v "$fixture:/fixture" \
  "$image" "$uid:$gid" /fixture/home /fixture/projects /fixture/worktrees

bash "$repo_root/scripts/configure-paseo-runtime.sh" \
  "$image" "$fixture/home" "$fixture/worktrees" "$uid" "$gid"

cat > "$fixture/compose.fixture.yaml" <<EOF
services:
  paseo:
    image: $image
    build: null
    restart: "no"
EOF

dc config >/dev/null
dc up -d

cid="$(dc ps -q paseo)"
test -n "$cid"

deadline=$((SECONDS + 30))
while (( SECONDS < deadline )); do
  if docker exec "$cid" node -e '
    const http=require("http");
    const req=http.get({hostname:"127.0.0.1",port:6767,path:"/api/health"},
      r=>process.exit(r.statusCode===200?0:1));
    req.on("error",()=>process.exit(1));
    req.setTimeout(1500,()=>{req.destroy();process.exit(1)});
  ' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$cid" node -e '
  const http=require("http");
  const req=http.get({hostname:"127.0.0.1",port:6767,path:"/api/health"},
    r=>process.exit(r.statusCode===200?0:1));
  req.on("error",()=>process.exit(1));
  req.setTimeout(1500,()=>{req.destroy();process.exit(1)});
' >/dev/null

test "$(docker inspect -f '{{.Config.User}}' "$cid")" = "$uid:$gid"
test "$(docker exec "$cid" id -u)" = "$uid"
test "$(docker exec "$cid" id -g)" = "$gid"
test "$uid" != "0"

docker exec "$cid" python3 -c '
import json
from pathlib import Path
cfg=json.loads(Path("/home/paseo/.paseo/config.json").read_text())
assert cfg["worktrees"]["root"] == "/worktrees", cfg
'

docker exec "$cid" sh -ec '
  printf home > /home/paseo/m02-home-marker
  printf project > /projects/m02-project-marker
  printf worktree > /worktrees/m02-worktree-marker
'

for marker in \
  "$fixture/home/m02-home-marker" \
  "$fixture/projects/m02-project-marker" \
  "$fixture/worktrees/m02-worktree-marker" \
  "$fixture/home/.paseo/config.json"; do
  test "$(stat -c '%u:%g' "$marker")" = "$uid:$gid"
done

mounts="$(docker inspect -f '{{range .Mounts}}{{.Destination}};{{end}}' "$cid")"
for target in /home/paseo /projects /worktrees; do
  case "$mounts" in
    *"$target;"*) ;;
    *) printf 'missing expected Compose mount %s in %s\n' "$target" "$mounts" >&2; exit 1 ;;
  esac
done
test "$(printf '%s' "$mounts" | tr ';' '\n' | sed '/^$/d' | wc -l | tr -d ' ')" = "3"
test "$(docker inspect -f '{{.HostConfig.Privileged}}' "$cid")" = "false"
test "$(docker inspect -f '{{.HostConfig.ShmSize}}' "$cid")" = "1073741824"
test "$(docker inspect -f '{{.HostConfig.Memory}}' "$cid")" = "0"
test "$(docker inspect -f '{{.HostConfig.NanoCpus}}' "$cid")" = "0"
test "$(docker inspect -f '{{.HostConfig.LogConfig.Type}}' "$cid")" = "json-file"
test "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-size"}}' "$cid")" = "10m"
test "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-file"}}' "$cid")" = "3"

dc down >/dev/null
dc up -d
cid="$(dc ps -q paseo)"

test "$(docker exec "$cid" cat /home/paseo/m02-home-marker)" = "home"
test "$(docker exec "$cid" cat /projects/m02-project-marker)" = "project"
test "$(docker exec "$cid" cat /worktrees/m02-worktree-marker)" = "worktree"
test "$(stat -c '%u:%g' "$fixture/home/m02-home-marker")" = "$uid:$gid"
test "$(stat -c '%u:%g' "$fixture/projects/m02-project-marker")" = "$uid:$gid"
test "$(stat -c '%u:%g' "$fixture/worktrees/m02-worktree-marker")" = "$uid:$gid"

printf '{"card":"M02-T01","home_persisted":true,"projects_persisted":true,"worktrees_persisted":true,"worktrees_root":"/worktrees","runtime_uid":%s,"runtime_gid":%s,"shm_bytes":1073741824,"resource_caps":"none","result":"GREEN"}\n' "$uid" "$gid"
