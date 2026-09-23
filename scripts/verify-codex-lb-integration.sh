#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${1:-pi-unraid:m03-t03}"
root="$(mktemp -d "${TMPDIR:-/tmp}/pi-unraid-m03-t03.XXXXXX")"
project="piunraid-m03-t03-$$"
uid="${PI_TEST_UID:-21001}"
gid="${PI_TEST_GID:-21001}"
fixture_key="fixture-m03-key-$$-not-real"
server_pid=""
secret_source=""
base_url=""
model_id="fixture-model"

cleanup() {
  if [ -n "$server_pid" ] && kill -0 "$server_pid" 2>/dev/null; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  PI_UID="$uid" PI_GID="$gid"     PI_CODEX_LB_SECRET_SOURCE="${secret_source:-/dev/null}"     PI_CODEX_LB_BASE_URL="${base_url:-http://host.docker.internal:9/v1}"     PI_CODEX_LB_MODEL="$model_id"     docker compose -p "$project" -f "$repo_root/compose.yaml" -f "$root/compose.fixture.yaml" down -v >/dev/null 2>&1 || true
  rm -rf "$root"
}
trap cleanup EXIT

mkdir -p "$root/home" "$root/projects" "$root/worktrees"
chown "$uid:$gid" "$root/home" "$root/projects" "$root/worktrees"

cat >"$root/fake-codex-lb.py" <<'PY'
import http.server
import json
import os
import sys

expected = os.environ["FIXTURE_KEY"]
port = int(sys.argv[1])

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, status, payload=None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok"})
            return
        if self.path == "/v1/models":
            if self.headers.get("Authorization") != "Bearer " + expected:
                self._send(401)
                return
            self._send(200, {"object": "list", "data": [{"id": "fixture-model", "object": "model"}]})
            return
        self._send(404)

server = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
server.serve_forever()
PY

port="$(python3 - <<'PY'
import socket
s=socket.socket()
s.bind(("0.0.0.0", 0))
print(s.getsockname()[1])
s.close()
PY
)"
FIXTURE_KEY="$fixture_key" python3 "$root/fake-codex-lb.py" "$port" >"$root/server.log" 2>&1 &
server_pid=$!
base_url="http://host.docker.internal:$port/v1"
secret_source="$root/codex-lb.env"
printf 'CODEX_LB_API_KEY=%s\n' "$fixture_key" >"$secret_source"
chown "$uid:$gid" "$secret_source"
chmod 0600 "$secret_source"

cat >"$root/compose.fixture.yaml" <<EOF
services:
  pi:
    image: $image
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
EOF

dc() {
  PI_UID="$uid" PI_GID="$gid"     PI_CODEX_LB_SECRET_SOURCE="$secret_source"     PI_CODEX_LB_BASE_URL="$base_url"     PI_CODEX_LB_MODEL="$model_id"     docker compose -p "$project" -f "$repo_root/compose.yaml" -f "$root/compose.fixture.yaml" "$@"
}

wait_health() {
  local expected="$1" cid status=""
  for _ in $(seq 1 80); do
    cid="$(dc ps -q pi 2>/dev/null || true)"
    if [ -n "$cid" ]; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || true)"
      [ "$status" = "$expected" ] && return 0
    fi
    sleep 0.25
  done
  printf 'expected health=%s, got=%s\n' "$expected" "${status:-missing}" >&2
  return 1
}

printf '%s\n' 'M03-T03: fresh-home provider initialization and authenticated disposable route'
dc up -d
wait_health healthy
cid="$(dc ps -q pi)"
docker exec -u pi "$cid" pi-unraid-service provider-health >"$root/provider-ready.log" 2>&1
grep -F 'pi-unraid provider: ready base_url=' "$root/provider-ready.log" >/dev/null
docker exec -u pi "$cid" getent hosts host.docker.internal >/dev/null

models="$root/home/.pi/agent/models.json"
test -s "$models"
test "$(stat -c '%a' "$secret_source")" = "600"
test "$(stat -c '%u:%g' "$secret_source")" = "$uid:$gid"
test "$(stat -c '%a' "$models")" = "600"
test "$(stat -c '%u:%g' "$models")" = "$uid:$gid"
python3 - "$models" "$base_url" "$model_id" <<'PY'
import json
import sys
p, expected_base, expected_model = sys.argv[1:4]
doc=json.load(open(p))
provider=doc["providers"]["codex-lb"]
assert provider["baseUrl"] == expected_base
assert provider["api"] == "openai-responses"
assert provider["apiKey"] == "${CODEX_LB_API_KEY}"
assert provider["models"] == [{"id": expected_model}]
PY
! grep -F "$fixture_key" "$models" >/dev/null

rendered="$(dc config)"
! printf '%s\n' "$rendered" | grep -F "$fixture_key" >/dev/null
printf '%s\n' "$rendered" | grep -F 'source: codex_lb_client' >/dev/null
printf '%s\n' "$rendered" | grep -F 'target: pi-unraid-codex-lb' >/dev/null

mounts_json="$(docker inspect -f '{{json .Mounts}}' "$cid")"
python3 - "$mounts_json" <<'PY'
import json,sys
mounts=json.loads(sys.argv[1])
secret=[m for m in mounts if m.get("Destination")=="/run/secrets/pi-unraid-codex-lb"]
assert len(secret)==1
assert secret[0].get("RW") is False
for prohibited in ("/var/run/docker.sock", "/", "/mnt/user/appdata/codex-lb-clean"):
    assert all(m.get("Source") != prohibited for m in mounts)
PY

printf '%s\n' 'M03-T03: idempotent init and recreation persistence'
hash_before="$(sha256sum "$models" | awk '{print $1}')"
docker exec -u pi "$cid" pi-unraid-provider init >/dev/null
docker exec -u pi "$cid" pi-unraid-provider init >/dev/null
hash_after_init="$(sha256sum "$models" | awk '{print $1}')"
test "$hash_before" = "$hash_after_init"
printf persist-provider >"$root/home/.pi/agent/m03-provider-marker"
chown "$uid:$gid" "$root/home/.pi/agent/m03-provider-marker"
dc up -d --force-recreate >/dev/null
wait_health healthy
cid="$(dc ps -q pi)"
test "$(cat "$root/home/.pi/agent/m03-provider-marker")" = "persist-provider"
test "$(sha256sum "$models" | awk '{print $1}')" = "$hash_before"
docker exec -u pi "$cid" pi-unraid-service provider-health >/dev/null
docker exec -u pi "$cid" pi --list-models 2>/dev/null | grep -F "$model_id" >/dev/null

printf '%s\n' 'M03-T03: populated-home preservation'
dc down >/dev/null
rm -rf "$root/home"
mkdir -p "$root/home/.pi/agent"
cat >"$root/home/.pi/agent/models.json" <<'JSON'
{
  "customMarker": "preserve-me",
  "providers": {
    "keep-me": {
      "api": "openai-completions",
      "apiKey": "dummy-placeholder",
      "baseUrl": "http://example.invalid/v1",
      "models": [{"id": "preserve-model"}]
    }
  }
}
JSON
chown -R "$uid:$gid" "$root/home"
dc up -d
wait_health healthy
cid="$(dc ps -q pi)"
docker exec -u pi "$cid" pi-unraid-service provider-health >/dev/null
python3 - "$root/home/.pi/agent/models.json" <<'PY'
import json,sys
doc=json.load(open(sys.argv[1]))
assert doc["customMarker"] == "preserve-me"
assert doc["providers"]["keep-me"]["models"][0]["id"] == "preserve-model"
assert doc["providers"]["codex-lb"]["api"] == "openai-responses"
assert doc["providers"]["codex-lb"]["apiKey"] == "${CODEX_LB_API_KEY}"
PY
pop_hash="$(sha256sum "$root/home/.pi/agent/models.json" | awk '{print $1}')"
docker exec -u pi "$cid" pi-unraid-provider init >/dev/null
test "$(sha256sum "$root/home/.pi/agent/models.json" | awk '{print $1}')" = "$pop_hash"

printf '%s\n' 'M03-T03: missing secret remains a provider failure, not runtime-state loss'
secret_source="/dev/null"
dc up -d --force-recreate >/dev/null
wait_health healthy
cid="$(dc ps -q pi)"
if docker exec -u pi "$cid" pi-unraid-service provider-health >"$root/missing.log" 2>&1; then
  printf '%s\n' 'provider-health unexpectedly succeeded without a credential' >&2
  exit 1
fi
grep -F 'credential unavailable from dedicated runtime secret' "$root/missing.log" >/dev/null
docker exec -u pi "$cid" pi-unraid-service health
test -s "$root/home/.pi/agent/models.json"

printf '%s\n' 'M03-T03: invalid secret is classified without leakage'
invalid_key="invalid-m03-key-$$-not-real"
secret_source="$root/invalid.env"
printf 'CODEX_LB_API_KEY=%s\n' "$invalid_key" >"$secret_source"
chown "$uid:$gid" "$secret_source"
chmod 0600 "$secret_source"
dc up -d --force-recreate >/dev/null
wait_health healthy
cid="$(dc ps -q pi)"
if docker exec -u pi "$cid" pi-unraid-service provider-health >"$root/invalid.log" 2>&1; then
  printf '%s\n' 'provider-health unexpectedly accepted an invalid credential' >&2
  exit 1
fi
grep -F 'Codex-LB authentication rejected' "$root/invalid.log" >/dev/null
! grep -F "$invalid_key" "$root/invalid.log" >/dev/null
docker exec -u pi "$cid" pi-unraid-service health

printf '%s\n' 'M03-T03: unreachable endpoint is distinct and runtime health remains GREEN'
secret_source="$root/codex-lb.env"
if kill -0 "$server_pid" 2>/dev/null; then
  kill "$server_pid"
  wait "$server_pid" 2>/dev/null || true
fi
server_pid=""
dc up -d --force-recreate >/dev/null
wait_health healthy
cid="$(dc ps -q pi)"
if docker exec -u pi "$cid" pi-unraid-service provider-health >"$root/unreachable.log" 2>&1; then
  printf '%s\n' 'provider-health unexpectedly succeeded with endpoint offline' >&2
  exit 1
fi
grep -F 'Codex-LB endpoint unreachable' "$root/unreachable.log" >/dev/null
docker exec -u pi "$cid" pi-unraid-service health

printf '%s\n' 'M03-T03: redaction and source safety'
logs="$(dc logs --no-color pi 2>&1 || true)"
! printf '%s\n' "$logs" | grep -F "$fixture_key" >/dev/null
! printf '%s\n' "$logs" | grep -F "$invalid_key" >/dev/null
! git -C "$repo_root" grep -nE 'sk-clb-[A-Za-z0-9_-]{8,}' -- . >/dev/null
! grep -R -F "$fixture_key" "$repo_root" >/dev/null

printf '%s\n' 'M03-T03: inherited affected regressions'
PI_CODEX_LB_SECRET_SOURCE=/dev/null bash "$repo_root/scripts/verify-base-image.sh" "$image"
PI_CODEX_LB_SECRET_SOURCE=/dev/null bash "$repo_root/scripts/verify-compose-foundation.sh" "$image"
PI_CODEX_LB_SECRET_SOURCE=/dev/null bash "$repo_root/scripts/verify-git-worktree-foundation.sh" "$image"
PI_CODEX_LB_SECRET_SOURCE=/dev/null bash "$repo_root/scripts/verify-runtime-selector.sh" "$image"
PI_CODEX_LB_SECRET_SOURCE=/dev/null bash "$repo_root/scripts/verify-managed-lifecycle.sh" "$image"

printf '%s\n' 'M03-T03 Codex-LB integration verification: GREEN'
