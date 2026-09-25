#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$#" -ge 1 ]; then image="$1"; else image="pi-unraid:paseo-foundation"; fi
tmpbase="/tmp"
if printenv TMPDIR >/dev/null 2>&1; then tmpbase="$TMPDIR"; fi
fixture="$(mktemp -d "$tmpbase/pi-unraid-m02-t02.XXXXXX")"
project="piunraid-m02-t02-$$"
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

# Non-interactive pairing must fail closed while Relay is disabled.
set +e
pair_disabled="$(docker run --rm --user "$uid:$gid" \
  -v "$fixture/home:/home/paseo" \
  "$image" paseo daemon pair --json --home /home/paseo/.paseo 2>&1)"
pair_rc=$?
set -e
test "$pair_rc" -ne 0
case "$pair_disabled" in
  *'"code":"RELAY_DISABLED"'*) ;;
  *) printf 'expected RELAY_DISABLED from non-consenting pair probe; got: %s\n' "$pair_disabled" >&2; exit 1 ;;
esac

# Simulate explicit human consent only inside this disposable fixture. The
# pairing offer is captured and never printed. Keep relay=true through both
# container starts so recreation proves persisted Relay state as well as the
# private daemon identity.
pair_offer="$(docker run --rm --user "$uid:$gid" \
  -v "$fixture/home:/home/paseo" \
  "$image" paseo daemon pair --relay --json --home /home/paseo/.paseo 2>/dev/null)"
test -n "$pair_offer"
unset pair_offer

docker run --rm --user "$uid:$gid" \
  -v "$fixture/home:/home/paseo:ro" \
  "$image" python3 -c '
import json
from pathlib import Path
cfg=json.loads(Path("/home/paseo/.paseo/config.json").read_text())
assert cfg["daemon"]["relay"]["enabled"] is True, cfg
assert Path("/home/paseo/.paseo/daemon-keypair.json").is_file()
'

keypair_sha_before="$(docker run --rm --user "$uid:$gid" --entrypoint sha256sum \
  -v "$fixture/home:/home/paseo:ro" \
  "$image" /home/paseo/.paseo/daemon-keypair.json | awk '{print $1}')"
test -n "$keypair_sha_before"

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
assert cfg["daemon"]["relay"]["enabled"] is True, cfg
'

docker exec "$cid" sh -ec '
  printf home > /home/paseo/m02-home-marker
  printf project > /projects/m02-project-marker
  printf worktree > /worktrees/m02-worktree-marker
'

assert_fixture_owner() {
  local rel="$1"
  test "$(docker run --rm --user 0:0 --entrypoint stat \
    -v "$fixture:/fixture:ro" \
    "$image" -c '%u:%g' "/fixture/$rel")" = "$uid:$gid"
}

assert_fixture_owner home/m02-home-marker
assert_fixture_owner projects/m02-project-marker
assert_fixture_owner worktrees/m02-worktree-marker
assert_fixture_owner home/.paseo/config.json
assert_fixture_owner home/.paseo/daemon-keypair.json

test "$(docker run --rm --user 0:0 --entrypoint stat \
  -v "$fixture:/fixture:ro" \
  "$image" -c '%a' /fixture/home/.paseo/daemon-keypair.json)" = "600"

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
test "$(docker inspect -f '{{len .HostConfig.PortBindings}}' "$cid")" = "0"
test "$(docker inspect -f '{{.HostConfig.LogConfig.Type}}' "$cid")" = "json-file"
test "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-size"}}' "$cid")" = "10m"
test "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-file"}}' "$cid")" = "3"

dc down >/dev/null
dc up -d
cid="$(dc ps -q paseo)"

test "$(docker exec "$cid" cat /home/paseo/m02-home-marker)" = "home"
test "$(docker exec "$cid" cat /projects/m02-project-marker)" = "project"
test "$(docker exec "$cid" cat /worktrees/m02-worktree-marker)" = "worktree"
assert_fixture_owner home/m02-home-marker
assert_fixture_owner projects/m02-project-marker
assert_fixture_owner worktrees/m02-worktree-marker
assert_fixture_owner home/.paseo/daemon-keypair.json

docker exec "$cid" python3 -c '
import json
from pathlib import Path
cfg=json.loads(Path("/home/paseo/.paseo/config.json").read_text())
assert cfg["daemon"]["relay"]["enabled"] is True, cfg
'

keypair_sha_after="$(docker exec "$cid" sha256sum /home/paseo/.paseo/daemon-keypair.json | awk '{print $1}')"
test "$keypair_sha_after" = "$keypair_sha_before"
test "$(docker exec "$cid" stat -c '%a' /home/paseo/.paseo/daemon-keypair.json)" = "600"

printf '{"card":"M02-T02","home_persisted":true,"projects_persisted":true,"worktrees_persisted":true,"worktrees_root":"/worktrees","relay_default_disabled":true,"relay_enabled_after_consent":true,"relay_enabled_after_recreate":true,"daemon_identity_persisted":true,"raw_host_ports":0,"revocation_cli":"unsupported","runtime_uid":%s,"runtime_gid":%s,"shm_bytes":1073741824,"resource_caps":"none","result":"GREEN"}\n' "$uid" "$gid"
