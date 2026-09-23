#!/usr/bin/env bash
set -euo pipefail

export PI_CODEX_LB_SECRET_SOURCE="${PI_CODEX_LB_SECRET_SOURCE:-/dev/null}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${1:-pi-unraid:local}"
fixture="$(mktemp -d "${TMPDIR:-/tmp}/pi-unraid-m01-t02.XXXXXX")"
project="piunraid-m01-t02-$$"
uid_a="${PI_TEST_UID_A:-21001}"
gid_a="${PI_TEST_GID_A:-21001}"
uid_b="${PI_TEST_UID_B:-21002}"
gid_b="${PI_TEST_GID_B:-21002}"

cleanup() {
  PI_UID="$uid_a" PI_GID="$gid_a" docker compose -p "$project"     -f "$repo_root/compose.yaml" -f "$fixture/compose.fixture.yaml" down -v >/dev/null 2>&1 || true
  rm -rf "$fixture"
}
trap cleanup EXIT

mkdir -p "$fixture/home" "$fixture/projects" "$fixture/worktrees"
cat > "$fixture/compose.fixture.yaml" <<EOF
services:
  pi:
    image: $image
    build: null
    restart: "no"
    volumes:
      - type: bind
        source: $fixture/home
        target: /home/pi
        bind:
          create_host_path: false
      - type: bind
        source: $fixture/projects
        target: /projects
        bind:
          create_host_path: false
      - type: bind
        source: $fixture/worktrees
        target: /worktrees
        bind:
          create_host_path: false
EOF

dc=(docker compose -p "$project" -f "$repo_root/compose.yaml" -f "$fixture/compose.fixture.yaml")

PI_UID="$uid_a" PI_GID="$gid_a" "${dc[@]}" up -d
sleep 1
cid="$("${dc[@]}" ps -q pi)"
host_pid="$(docker inspect -f '{{.State.Pid}}' "$cid")"

test "$(ps -o uid= -p "$host_pid" | tr -d ' ')" = "$uid_a"
test "$(ps -o gid= -p "$host_pid" | tr -d ' ')" = "$gid_a"
docker exec -u pi "$cid" sh -ec 'test "$(id -u)" = "$PI_UID"; test "$(id -g)" = "$PI_GID"; test "$HOME" = /home/pi; pi --version'
test "$(docker exec -u pi "$cid" sudo -n id -u)" = "0"
docker exec -u pi "$cid" sh -ec 'printf keep > /home/pi/.pi/agent/persist-marker'

PI_UID="$uid_a" PI_GID="$gid_a" "${dc[@]}" restart pi >/dev/null
sleep 1
cid="$("${dc[@]}" ps -q pi)"
test "$(docker exec -u pi "$cid" cat /home/pi/.pi/agent/persist-marker)" = "keep"
test "$(stat -c '%u:%g' "$fixture/home/.pi/agent/persist-marker")" = "$uid_a:$gid_a"

mounts="$(docker inspect -f '{{range .Mounts}}{{.Destination}};{{end}}' "$cid")"
case "$mounts" in
  *"/home/pi;"*"/projects;"*"/worktrees;"*"/run/secrets/pi-unraid-codex-lb;"*|*"/run/secrets/pi-unraid-codex-lb;"*"/home/pi;"*"/projects;"*"/worktrees;"*) ;;
  *) printf 'unexpected Compose mount set: %s\n' "$mounts" >&2; exit 1 ;;
esac
test "$(docker inspect -f '{{.HostConfig.Privileged}}' "$cid")" = "false"
test "$(docker inspect -f '{{.HostConfig.LogConfig.Type}}' "$cid")" = "json-file"
test "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-size"}}' "$cid")" = "10m"
test "$(docker inspect -f '{{index .HostConfig.LogConfig.Config "max-file"}}' "$cid")" = "3"
! docker exec "$cid" sh -ec 'command -v sshd >/dev/null'

PI_UID="$uid_a" PI_GID="$gid_a" "${dc[@]}" down >/dev/null
PI_UID="$uid_b" PI_GID="$gid_b" "${dc[@]}" up -d >/dev/null || true
sleep 1
cid="$("${dc[@]}" ps -aq pi)"
test "$(docker inspect -f '{{.State.Status}}' "$cid")" = "exited"
test "$(docker inspect -f '{{.State.ExitCode}}' "$cid")" = "1"
"${dc[@]}" logs --no-color pi 2>&1 | grep -F 'pi-unraid init error:' >/dev/null
test "$(stat -c '%u:%g' "$fixture/home/.pi/agent/persist-marker")" = "$uid_a:$gid_a"

echo "M01-T02 fixture verification: GREEN"
