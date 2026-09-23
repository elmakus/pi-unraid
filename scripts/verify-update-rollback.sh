#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(mktemp -d "${TMPDIR:-/tmp}/pi-unraid-m02-t03.XXXXXX")"
project="piunraid-m02-t03-$$"
uid="${PI_TEST_UID:-21001}"
gid="${PI_TEST_GID:-21001}"
active="pi-unraid:m02-t03-active-$$"
candidate="pi-unraid:m02-t03-candidate-$$"
previous="pi-unraid:m02-t03-previous-$$"
baseline_image="${1:-pi-unraid:m02-t02-r2}"
remote="$root/remote.git"
work="$root/work"
author="$root/author"
state="$root/deployment-state"
override="$root/compose.fixture.yaml"
bad_override="$root/compose.bad-cutover.yaml"

cleanup() {
  docker compose -p "$project" -f "$work/compose.yaml" -f "$override" down -v >/dev/null 2>&1 || true
  docker image rm "$active" "$candidate" "$previous" >/dev/null 2>&1 || true
  rm -rf "$root"
}
trap cleanup EXIT

for tag in "$active" "$candidate" "$previous"; do
  docker image rm "$tag" >/dev/null 2>&1 || true
done
docker image inspect "$baseline_image" >/dev/null
docker image tag "$baseline_image" "$active"

git clone --bare "$repo_root" "$remote" >/dev/null
git clone "$remote" "$work" >/dev/null
git clone "$remote" "$author" >/dev/null
git -C "$work" checkout feat/pi-unraid-bootstrap >/dev/null
git -C "$author" checkout feat/pi-unraid-bootstrap >/dev/null
git -C "$work" branch --set-upstream-to=origin/feat/pi-unraid-bootstrap >/dev/null
git -C "$author" config user.name "M02 fixture"
git -C "$author" config user.email "m02@example.invalid"

mkdir -p "$root/home" "$root/projects" "$root/worktrees" "$state"
chown "$uid:$gid" "$root/home" "$root/projects" "$root/worktrees"

cat >"$override" <<EOF
services:
  pi:
    image: $active
    build: null
    restart: "no"
    environment:
      PI_UNRAID_LOOKUP_TIMEOUT_SECONDS: "1"
      npm_config_registry: "http://127.0.0.1:9"
      npm_config_fetch_retries: "0"
    healthcheck:
      interval: 1s
      timeout: 2s
      retries: 5
      start_period: 1s
    volumes:
      - type: bind
        source: $root/home
        target: /home/pi
        bind:
          create_host_path: false
      - type: bind
        source: $root/projects
        target: /projects
        bind:
          create_host_path: false
      - type: bind
        source: $root/worktrees
        target: /worktrees
        bind:
          create_host_path: false
networks:
  default:
    internal: true
EOF

cat >"$bad_override" <<'EOF'
services:
  pi:
    environment:
      PI_UNRAID_RUNTIME_STATE_ROOT: /tmp/m02-broken-state
      PI_UNRAID_RUNTIME_SHARE_ROOT: /tmp/m02-broken-share
      PI_UNRAID_SEED_CLI: /nonexistent
EOF

dc=(docker compose -p "$project" -f "$work/compose.yaml" -f "$override")
PI_UID="$uid" PI_GID="$gid" "${dc[@]}" up -d --no-build
for _ in $(seq 1 80); do
  cid="$("${dc[@]}" ps -q pi)"
  status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid")"
  [ "$status" = healthy ] && break
  sleep 0.25
done
[ "${status:-}" = healthy ]

docker exec -u pi "$cid" sh -ec '
  printf home-marker > /home/pi/m02-t03-home
  printf project-marker > /projects/m02-t03-project
  printf worktree-marker > /worktrees/m02-t03-worktree
'
docker exec -u pi \
  -e PI_UNRAID_TEST_LATEST_OVERRIDE=9.9.9 \
  -e PI_UNRAID_TEST_INSTALL_SPEC_OVERRIDE=file:/fixture-does-not-exist \
  "$cid" pi-unraid-runtime reconcile >/dev/null 2>&1 || true

hash_sources() {
  sha256sum "$root/home/m02-t03-home" "$root/projects/m02-t03-project" "$root/worktrees/m02-t03-worktree" |
    sha256sum | awk '{print $1}'
}
failed_candidate_marker() {
  jq -c '.failed_candidate' "$root/home/.local/state/pi-unraid/runtime.json"
}
ownership_sources() {
  stat -c '%u:%g' "$root/home/m02-t03-home" "$root/projects/m02-t03-project" "$root/worktrees/m02-t03-worktree"
}
before_hash="$(hash_sources)"
before_failed_candidate="$(failed_candidate_marker)"
[ "$before_failed_candidate" != "null" ]
before_owners="$(ownership_sources)"
old_id="$(docker image inspect "$active" --format '{{.Id}}')"

printf '%s\n' 'M02-T03: fast-forward source + verified candidate + healthy cutover'
python3 - "$author/Dockerfile" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
s=s.replace('Phase 1 Pi Coding Agent base for Unraid', 'Phase 1 Pi Coding Agent base for Unraid - M02 update fixture', 1)
p.write_text(s)
PY
git -C "$author" add Dockerfile
git -C "$author" commit -m 'test: advance disposable deployment image' >/dev/null
git -C "$author" push origin feat/pi-unraid-bootstrap >/dev/null
success_head="$(git -C "$author" rev-parse HEAD)"

env \
  PI_UID="$uid" PI_GID="$gid" \
  PI_UNRAID_DEPLOYMENT_STATE_ROOT="$state" \
  PI_UNRAID_ACTIVE_TAG="$active" PI_UNRAID_CANDIDATE_TAG="$candidate" PI_UNRAID_PREVIOUS_TAG="$previous" \
  PI_UNRAID_COMPOSE_PROJECT="$project" PI_UNRAID_COMPOSE_OVERRIDE="$override" \
  PI_UNRAID_UPDATE_HEALTH_TIMEOUT_SECONDS=20 \
  bash "$work/scripts/update.sh"

[ "$(git -C "$work" rev-parse HEAD)" = "$success_head" ]
new_id="$(docker image inspect "$active" --format '{{.Id}}')"
[ "$new_id" != "$old_id" ]
[ "$(docker image inspect "$previous" --format '{{.Id}}')" = "$old_id" ]
tx="$state/$(readlink "$state/latest")"
[ "$(cat "$tx/pre-image-id")" = "$old_id" ]
[ "$(cat "$tx/post-image-id")" = "$new_id" ]
[ "$(cat "$tx/pre-source-head")" != "$(cat "$tx/post-source-head")" ]
[ "$(cat "$tx/status")" = healthy ]
jq -e '.selected.version != null' "$tx/post-runtime.json" >/dev/null
[ "$(hash_sources)" = "$before_hash" ]
[ "$(failed_candidate_marker)" = "$before_failed_candidate" ]
[ "$(ownership_sources)" = "$before_owners" ]

printf '%s\n' 'M02-T03: explicit rollback uses retained artifacts while deployment network is internal/offline'
env \
  PI_UID="$uid" PI_GID="$gid" \
  PI_UNRAID_DEPLOYMENT_STATE_ROOT="$state" \
  PI_UNRAID_ACTIVE_TAG="$active" PI_UNRAID_CANDIDATE_TAG="$candidate" PI_UNRAID_PREVIOUS_TAG="$previous" \
  PI_UNRAID_COMPOSE_PROJECT="$project" PI_UNRAID_COMPOSE_OVERRIDE="$override" \
  PI_UNRAID_UPDATE_HEALTH_TIMEOUT_SECONDS=20 \
  bash "$work/scripts/update.sh" rollback "$tx"
[ "$(docker image inspect "$active" --format '{{.Id}}')" = "$old_id" ]
[ "$(cat "$tx/status")" = rolled_back ]
[ "$(hash_sources)" = "$before_hash" ]
[ "$(failed_candidate_marker)" = "$before_failed_candidate" ]
[ "$(ownership_sources)" = "$before_owners" ]

printf '%s\n' 'M02-T03: injected build failure is pre-cutover and leaves deployment unchanged'
pre_fail_image="$(docker image inspect "$active" --format '{{.Id}}')"
set +e
env \
  PI_UID="$uid" PI_GID="$gid" \
  PI_UNRAID_DEPLOYMENT_STATE_ROOT="$state" \
  PI_UNRAID_ACTIVE_TAG="$active" PI_UNRAID_CANDIDATE_TAG="$candidate" PI_UNRAID_PREVIOUS_TAG="$previous" \
  PI_UNRAID_COMPOSE_PROJECT="$project" PI_UNRAID_COMPOSE_OVERRIDE="$override" \
  PI_UNRAID_TEST_FAIL_BUILD=1 \
  bash "$work/scripts/update.sh"
rc=$?
set -e
[ "$rc" -ne 0 ]
[ "$(docker image inspect "$active" --format '{{.Id}}')" = "$pre_fail_image" ]

printf '%s\n' 'M02-T03: unhealthy post-cutover deployment automatically restores previous image/config'
# Advance source again so the candidate has a distinct source/image identity.
python3 - "$author/Dockerfile" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text().replace('M02 update fixture', 'M02 rollback fixture', 1)
p.write_text(s)
PY
git -C "$author" add Dockerfile
git -C "$author" commit -m 'test: create disposable unhealthy cutover candidate' >/dev/null
git -C "$author" push origin feat/pi-unraid-bootstrap >/dev/null
before_broken_image="$(docker image inspect "$active" --format '{{.Id}}')"

set +e
env \
  PI_UID="$uid" PI_GID="$gid" \
  PI_UNRAID_DEPLOYMENT_STATE_ROOT="$state" \
  PI_UNRAID_ACTIVE_TAG="$active" PI_UNRAID_CANDIDATE_TAG="$candidate" PI_UNRAID_PREVIOUS_TAG="$previous" \
  PI_UNRAID_COMPOSE_PROJECT="$project" PI_UNRAID_COMPOSE_OVERRIDE="$override" \
  PI_UNRAID_TEST_CUTOVER_OVERRIDE="$bad_override" \
  PI_UNRAID_TEST_VERIFY_COMMAND='docker image inspect "$PI_UNRAID_CANDIDATE_TAG" >/dev/null' \
  PI_UNRAID_UPDATE_HEALTH_TIMEOUT_SECONDS=8 \
  bash "$work/scripts/update.sh"
rc=$?
set -e
[ "$rc" -ne 0 ]
latest_tx="$state/$(readlink "$state/latest")"
[ "$(cat "$latest_tx/status")" = rolled_back ]
[ "$(docker image inspect "$active" --format '{{.Id}}')" = "$before_broken_image" ]
[ "$(hash_sources)" = "$before_hash" ]
[ "$(failed_candidate_marker)" = "$before_failed_candidate" ]
[ "$(ownership_sources)" = "$before_owners" ]

cid="$(docker compose -p "$project" -f "$latest_tx/pre-update.compose.yaml" ps -q pi)"
[ -n "$cid" ]
[ "$(docker inspect -f '{{.State.Health.Status}}' "$cid")" = healthy ]
[ "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-size"}}' "$cid")" = 10m ]
[ "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-file"}}' "$cid")" = 3 ]
tx_count="$(find "$state" -maxdepth 1 -mindepth 1 -type d -name 'tx-*' | wc -l | tr -d ' ')"
[ "$tx_count" -le 2 ]

printf 'M02-T03 update/rollback verification: GREEN old=%s new=%s tx_count=%s\n' "$old_id" "$new_id" "$tx_count"
