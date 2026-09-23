#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${1:-pi-unraid:m02-t02}"
root="$(mktemp -d "${TMPDIR:-/tmp}/pi-unraid-m02-t02.XXXXXX")"
project="piunraid-m02-t02-$$"
uid="${PI_TEST_UID:-21001}"
gid="${PI_TEST_GID:-21001}"
grace="${PI_TEST_GRACE_SECONDS:-3}"
fixture="$root/fixture"

cleanup() {
  PI_UID="$uid" PI_GID="$gid" PI_TEST_SEED_CLI=/usr/local/bin/pi-seed \
    docker compose -p "$project" -f "$repo_root/compose.yaml" -f "$root/compose.fixture.yaml" down -v >/dev/null 2>&1 || true
  rm -rf "$root"
}
trap cleanup EXIT

mkdir -p "$root/home" "$root/projects" "$root/worktrees" "$fixture"
chown "$uid:$gid" "$root/home" "$root/projects" "$root/worktrees"

cat > "$fixture/select-manager" <<'EOF'
#!/bin/sh
set -eu
[ "${1:-}" = select ] || exit 2
printf '%s\n' "${PI_TEST_FAKE_CLI:?}"
EOF

cat > "$fixture/cooperative" <<'EOF'
#!/bin/sh
set -eu
trap 'exit 0' TERM INT
printf '%s\n' "$$" > "${PI_TEST_PID_FILE:?}"
while :; do sleep 1; done
EOF

cat > "$fixture/stubborn" <<'EOF'
#!/bin/sh
set -eu
trap '' TERM INT
printf '%s\n' "$$" > "${PI_TEST_PID_FILE:?}"
while :; do sleep 1; done
EOF

cat > "$fixture/run-tty.py" <<'EOF'
import os
import pty
import sys

cid = sys.argv[1]
pid, fd = pty.fork()
if pid == 0:
    os.execvp("docker", ["docker", "exec", "-it", "-u", "pi", cid, "pi", "--no-session"])

try:
    while True:
        data = os.read(fd, 4096)
        if not data:
            break
        os.write(sys.stdout.fileno(), data)
except OSError:
    pass

_, status = os.waitpid(pid, 0)
raise SystemExit(os.waitstatus_to_exitcode(status))
EOF

chmod 0755 "$fixture/select-manager" "$fixture/cooperative" "$fixture/stubborn"

cat > "$root/compose.fixture.yaml" <<EOF
services:
  pi:
    image: $image
    build: null
    restart: "no"
    environment:
      PI_UNRAID_MANAGED_GRACE_SECONDS: "$grace"
      PI_UNRAID_LOOKUP_TIMEOUT_SECONDS: "1"
      PI_UNRAID_SEED_CLI: "${PI_TEST_SEED_CLI:-/usr/local/bin/pi-seed}"
      npm_config_registry: "http://127.0.0.1:9"
      npm_config_fetch_retries: "0"
    healthcheck:
      interval: 1s
      timeout: 2s
      retries: 2
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
      - type: bind
        source: $fixture
        target: /fixture
        read_only: true
EOF

dc=(docker compose -p "$project" -f "$repo_root/compose.yaml" -f "$root/compose.fixture.yaml")

wait_health() {
  local expected="$1" cid status
  for _ in $(seq 1 80); do
    cid="$("${dc[@]}" ps -q pi 2>/dev/null || true)"
    if [ -n "$cid" ]; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || true)"
      [ "$status" = "$expected" ] && return 0
    fi
    sleep 0.25
  done
  printf 'expected health=%s, got=%s\n' "$expected" "${status:-missing}" >&2
  return 1
}

active_pids() {
  local cid="$1"
  docker exec -u pi "$cid" bash -lc '
    shopt -s nullglob
    for f in /tmp/pi-unraid/managed-pi/*.reg; do
      read -r p s u extra < "$f" || continue
      [ -z "${extra:-}" ] || continue
      [ -r "/proc/$p/stat" ] || continue
      [ "$(awk "{print \$22}" "/proc/$p/stat")" = "$s" ] || continue
      [ "$(awk "/^Uid:/ {print \$2; exit}" "/proc/$p/status")" = "$u" ] || continue
      printf "%s\n" "$p"
    done
  '
}

printf '%s\n' 'M02-T02: service readiness, non-root PID1 and real packaged Pi planned SIGTERM'
PI_UID="$uid" PI_GID="$gid" "${dc[@]}" up -d
wait_health healthy
cid="$("${dc[@]}" ps -q pi)"
host_pid="$(docker inspect -f '{{.State.Pid}}' "$cid")"
test "$(ps -o uid= -p "$host_pid" | tr -d ' ')" = "$uid"
test "$(ps -o gid= -p "$host_pid" | tr -d ' ')" = "$gid"
grep -F 'stop_grace_period: 20s' "$repo_root/compose.yaml" >/dev/null
docker inspect -f '{{json .Config.Healthcheck.Test}}' "$cid" | grep -F 'pi-unraid-service' >/dev/null

mkdir -p "$root/home/.pi/agent/sessions/m02-fixture"
printf '%s\n' '{"fixture":"persisted-before-stop"}' > "$root/home/.pi/agent/sessions/m02-fixture/state.json"
chown -R "$uid:$gid" "$root/home/.pi"
state_before="$(sha256sum "$root/home/.pi/agent/sessions/m02-fixture/state.json" | awk '{print $1}')"

python3 "$fixture/run-tty.py" "$cid" >"$root/real-pi-tty.log" 2>&1 &
tty_job=$!
real_pid=""
for _ in $(seq 1 80); do
  real_pid="$(active_pids "$cid" | head -n 1 || true)"
  [ -n "$real_pid" ] && break
  sleep 0.25
done
[ -n "$real_pid" ]

"${dc[@]}" stop pi >/dev/null
wait "$tty_job" || true
logs="$("${dc[@]}" logs --no-color pi 2>&1)"
printf '%s\n' "$logs" | grep -F "sent SIGTERM to managed Pi pid=$real_pid" >/dev/null
if printf '%s\n' "$logs" | grep -F "sent SIGKILL to managed Pi pid=$real_pid" >/dev/null; then
  printf 'real packaged Pi required SIGKILL unexpectedly\n' >&2
  exit 1
fi

PI_UID="$uid" PI_GID="$gid" "${dc[@]}" down >/dev/null
PI_UID="$uid" PI_GID="$gid" "${dc[@]}" up -d
wait_health healthy
state_after="$(sha256sum "$root/home/.pi/agent/sessions/m02-fixture/state.json" | awk '{print $1}')"
[ "$state_before" = "$state_after" ]

printf '%s\n' 'M02-T02: concurrent registrations, stale PID defense and bounded escalation'
cid="$("${dc[@]}" ps -q pi)"
docker exec -d -u pi \
  -e PI_UNRAID_RUNTIME_MANAGER=/fixture/select-manager \
  -e PI_TEST_FAKE_CLI=/fixture/cooperative \
  -e PI_TEST_PID_FILE=/tmp/cooperative-a.pid \
  "$cid" pi
docker exec -d -u pi \
  -e PI_UNRAID_RUNTIME_MANAGER=/fixture/select-manager \
  -e PI_TEST_FAKE_CLI=/fixture/cooperative \
  -e PI_TEST_PID_FILE=/tmp/cooperative-b.pid \
  "$cid" pi
docker exec -d -u pi \
  -e PI_UNRAID_RUNTIME_MANAGER=/fixture/select-manager \
  -e PI_TEST_FAKE_CLI=/fixture/stubborn \
  -e PI_TEST_PID_FILE=/tmp/stubborn.pid \
  "$cid" pi

for _ in $(seq 1 80); do
  count="$(active_pids "$cid" | wc -l | tr -d ' ')"
  [ "$count" -ge 3 ] && break
  sleep 0.1
done
[ "${count:-0}" -ge 3 ]
coop_a="$(docker exec "$cid" cat /tmp/cooperative-a.pid)"
coop_b="$(docker exec "$cid" cat /tmp/cooperative-b.pid)"
stubborn="$(docker exec "$cid" cat /tmp/stubborn.pid)"

docker exec -u pi "$cid" sh -ec 'printf "1 1 %s\n" "$(id -u)" > /tmp/pi-unraid/managed-pi/stale.reg'

start_ms="$(date +%s%3N)"
"${dc[@]}" stop pi >/dev/null
elapsed_ms=$(( $(date +%s%3N) - start_ms ))
logs="$("${dc[@]}" logs --no-color pi 2>&1)"

for pid in "$coop_a" "$coop_b" "$stubborn"; do
  printf '%s\n' "$logs" | grep -F "sent SIGTERM to managed Pi pid=$pid" >/dev/null
done
printf '%s\n' "$logs" | grep -F 'pruned stale managed-Pi registration stale.reg' >/dev/null
printf '%s\n' "$logs" | grep -F "sent SIGKILL to managed Pi pid=$stubborn" >/dev/null
for pid in "$coop_a" "$coop_b"; do
  if printf '%s\n' "$logs" | grep -F "sent SIGKILL to managed Pi pid=$pid" >/dev/null; then
    printf 'cooperative fixture pid=%s was SIGKILLed unexpectedly\n' "$pid" >&2
    exit 1
  fi
done
[ "$elapsed_ms" -ge $(( grace * 1000 - 500 )) ]
[ "$elapsed_ms" -lt 10000 ]

printf '%s\n' 'M02-T02: stale persistent readiness cannot make an unavailable startup healthy'
PI_UID="$uid" PI_GID="$gid" "${dc[@]}" down >/dev/null
PI_UID="$uid" PI_GID="$gid" PI_TEST_SEED_CLI=/nonexistent "${dc[@]}" up -d
wait_health unhealthy
cid="$("${dc[@]}" ps -q pi)"
if docker exec -u pi "$cid" pi-unraid-service health; then
  printf '%s\n' 'expected service health to fail while runtime is unavailable' >&2
  exit 1
fi

printf 'M02-T02 managed lifecycle verification: GREEN (grace=%ss elapsed_escalation_ms=%s)\n' "$grace" "$elapsed_ms"
