#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
image="${1:-pi-unraid:paseo-foundation}"
tmpbase="${TMPDIR:-/tmp}"
fixture="$(mktemp -d "$tmpbase/pi-unraid-m02-t03.XXXXXX")"
uid="${PASEO_TEST_UID:-99}"
gid="${PASEO_TEST_GID:-100}"

cleanup() {
  docker run --rm --user 0:0 --entrypoint chown \
    -v "$fixture:/fixture" \
    "$image" -R "$(id -u):$(id -g)" /fixture >/dev/null 2>&1 || true
  rm -rf "$fixture"
}
trap cleanup EXIT

mkdir -p "$fixture/home"
docker run --rm --user 0:0 --entrypoint chown \
  -v "$fixture:/fixture" \
  "$image" "$uid:$gid" /fixture/home

# Prove bounded rollback does not silently destroy a pre-existing global
# instruction file on first adoption.
docker run --rm --user "$uid:$gid" \
  -v "$fixture/home:/home/paseo" \
  "$image" sh -ec 'mkdir -p /home/paseo/.pi/agent; printf "%s\n" preexisting-local-instructions > /home/paseo/.pi/agent/AGENTS.md'

apply_json="$(bash "$repo_root/scripts/configure-pi-instruction-plane.sh" apply "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$apply_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["action"]=="apply" and d["changed"] and d["in_sync"]'

docker run --rm --user "$uid:$gid" \
  -v "$fixture/home:/home/paseo:ro" \
  "$image" python3 -c '
from pathlib import Path
root=Path("/home/paseo/.pi/agent")
assert (root/"AGENTS.md").is_file()
assert (root/"skills/project-recovery/SKILL.md").is_file()
assert (root/"skills/project-recovery/references/bootstrap.md").is_file()
assert (root/"skills/unraid-admin/SKILL.md").is_file()
assert (root/"skills/unraid-admin/references/safety-boundary.md").is_file()
assert not (root/"auth.json").exists()
'

test "$(docker run --rm --user 0:0 --entrypoint stat -v "$fixture/home:/home/paseo:ro" "$image" -c '%u:%g' /home/paseo/.pi/agent/AGENTS.md)" = "$uid:$gid"
test "$(docker run --rm --user 0:0 --entrypoint stat -v "$fixture/home:/home/paseo:ro" "$image" -c '%a' /home/paseo/.pi/agent/AGENTS.md)" = "644"

rollback_json="$(bash "$repo_root/scripts/configure-pi-instruction-plane.sh" rollback "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$rollback_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["action"]=="rollback" and d["restored_prior_state"]'
test "$(docker run --rm --user "$uid:$gid" -v "$fixture/home:/home/paseo:ro" "$image" cat /home/paseo/.pi/agent/AGENTS.md)" = "preexisting-local-instructions"
test ! -e "$fixture/home/.pi/agent/skills/project-recovery/SKILL.md"
test ! -e "$fixture/home/.pi/agent/skills/unraid-admin/SKILL.md"

bash "$repo_root/scripts/configure-pi-instruction-plane.sh" apply "$image" "$fixture/home" "$uid" "$gid" >/dev/null

tree_hash() {
  docker run --rm --user "$uid:$gid" \
    -v "$fixture/home:/home/paseo:ro" \
    "$image" sh -ec 'cd /home/paseo/.pi/agent && find AGENTS.md skills -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum' | awk '{print $1}'
}

fresh_rpc() {
  printf '%s\n' '{"id":"m02-t03-state","type":"get_state"}' | \
    docker run --rm -i --user "$uid:$gid" \
      -v "$fixture/home:/home/paseo" \
      "$image" pi --mode rpc --no-session
}

validate_rpc() {
  python3 -c '
import json,sys
records=[json.loads(line) for line in sys.stdin if line.strip()]
match=[r for r in records if r.get("id")=="m02-t03-state" and r.get("type")=="response" and r.get("command")=="get_state"]
assert match and match[0].get("success") is True, records
'
}

hash_before="$(tree_hash)"
rpc_first="$(fresh_rpc)"
printf '%s\n' "$rpc_first" | validate_rpc

# A second fresh container/process using the same persisted HOME is the
# recreation boundary for this non-production acceptance.
rpc_second="$(fresh_rpc)"
printf '%s\n' "$rpc_second" | validate_rpc
hash_after="$(tree_hash)"
test "$hash_after" = "$hash_before"

noop_json="$(bash "$repo_root/scripts/configure-pi-instruction-plane.sh" apply "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$noop_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["action"]=="apply" and d["changed"] is False and d["in_sync"]'

status_json="$(bash "$repo_root/scripts/configure-pi-instruction-plane.sh" status "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$status_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["action"]=="status" and d["in_sync"]'

printf '{"card":"M02-T03","agent_dir":"/home/paseo/.pi/agent","global_agents":true,"progressive_skills":2,"snapshot_rollback":true,"fresh_rpc_first":true,"fresh_rpc_recreated":true,"byte_stable_after_recreate":true,"runtime_uid":%s,"runtime_gid":%s,"result":"GREEN"}\n' "$uid" "$gid"
