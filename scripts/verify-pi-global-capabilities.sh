#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
image="${1:-pi-unraid:paseo-foundation}"
tmpbase="${TMPDIR:-/tmp}"
fixture="$(mktemp -d "$tmpbase/pi-unraid-m04-t03.XXXXXX")"
uid="${PASEO_TEST_UID:-99}"
gid="${PASEO_TEST_GID:-100}"

cleanup() {
  docker run --rm --user 0:0 --entrypoint chown \
    -v "$fixture:/fixture" \
    "$image" -R "$(id -u):$(id -g)" /fixture >/dev/null 2>&1 || true
  rm -rf "$fixture"
}
trap cleanup EXIT

mkdir -p "$fixture/home/.pi/agent"
cat >"$fixture/home/.pi/agent/settings.json" <<'JSON'
{
  "theme": "dark",
  "packages": [{"source":"npm:unrelated-example@1.2.3","autoload":false}],
  "customUnrelated": {"keep":"sentinel"}
}
JSON
printf '%s\n' '{"providerState":"unchanged"}' >"$fixture/home/.pi/agent/provider-state.json"
chown -R "$uid:$gid" "$fixture/home"

bash "$repo_root/scripts/configure-pi-instruction-plane.sh" \
  apply "$image" "$fixture/home" "$uid" "$gid" >/dev/null
instruction_hash="$(sha256sum "$fixture/home/.pi/agent/AGENTS.md" | awk '{print $1}')"
provider_hash="$(sha256sum "$fixture/home/.pi/agent/provider-state.json" | awk '{print $1}')"

set +e
before_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  status "$image" "$fixture/home" "$uid" "$gid" 2>/dev/null)"
before_rc=$?
set -e
test "$before_rc" -eq 1
printf '%s\n' "$before_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["state"]=="RED"
assert d["compatibility"]["verified"] is False
'

apply_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  apply "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$apply_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["action"]=="apply" and d["changed"] and d["in_sync"]
assert d["compatibility"]=={"reason":"none","state":"GREEN","verified":True}
assert d["packages"]["specpi"]["desired_version"]=="0.34.0"
assert d["packages"]["pi_mcp_adapter"]["desired_version"]=="2.37.0"
assert d["inventory_observations"]["specpi"]["present"] is True
assert d["inventory_observations"]["pi_mcp_adapter"]["present"] is True
'

python3 - "$fixture/home/.pi/agent/settings.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d["theme"]=="dark"
assert d["customUnrelated"]=={"keep":"sentinel"}
unrelated={"source":"npm:unrelated-example@1.2.3","autoload":False}
assert unrelated in d["packages"]
assert "npm:specpi@0.34.0" in d["packages"]
assert "npm:pi-mcp-adapter@2.37.0" in d["packages"]
PY
test "$(sha256sum "$fixture/home/.pi/agent/AGENTS.md" | awk '{print $1}')" = "$instruction_hash"
test "$(sha256sum "$fixture/home/.pi/agent/provider-state.json" | awk '{print $1}')" = "$provider_hash"
python3 - "$fixture/home/.pi-unraid/global-capabilities/snapshot.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d["packages_field_present"] is True
assert d["prior_managed_packages"]==[]
PY
test "$(stat -c '%a' "$fixture/home/.pi-unraid/global-capabilities/snapshot.json")" = "600"
test "$(stat -c '%a' "$fixture/home/.pi-unraid/global-capabilities/compatibility.json")" = "600"

noop_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  apply "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$noop_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["action"]=="apply" and d["changed"] is False and d["in_sync"]
'

adapter="$fixture/home/.pi/agent/npm/node_modules/pi-mcp-adapter"
mv "$adapter" "$adapter.hold"
settings_hash="$(sha256sum "$fixture/home/.pi/agent/settings.json" | awk '{print $1}')"
set +e
missing_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  status "$image" "$fixture/home" "$uid" "$gid" 2>/dev/null)"
missing_rc=$?
set -e
test "$missing_rc" -eq 1
test ! -e "$adapter"
test "$(sha256sum "$fixture/home/.pi/agent/settings.json" | awk '{print $1}')" = "$settings_hash"
printf '%s\n' "$missing_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["packages"]["pi_mcp_adapter"]["state"]=="RED"
assert d["packages"]["pi_mcp_adapter"]["reason"]=="package_missing_or_invalid"
'
mv "$adapter.hold" "$adapter"

rollback_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  rollback "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$rollback_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["action"]=="rollback" and d["restored_prior_state"] is True
'
python3 - "$fixture/home/.pi/agent/settings.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d["theme"]=="dark"
assert d["customUnrelated"]=={"keep":"sentinel"}
assert d["packages"]==[{"source":"npm:unrelated-example@1.2.3","autoload":False}]
PY
test ! -e "$fixture/home/.pi-unraid/global-capabilities/snapshot.json"
test ! -e "$fixture/home/.pi-unraid/global-capabilities/compatibility.json"
test "$(sha256sum "$fixture/home/.pi/agent/AGENTS.md" | awk '{print $1}')" = "$instruction_hash"
test "$(sha256sum "$fixture/home/.pi/agent/provider-state.json" | awk '{print $1}')" = "$provider_hash"

reapply_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  apply "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$reapply_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["in_sync"] and d["compatibility"]["verified"]
'

status_json="$(bash "$repo_root/scripts/configure-pi-global-capabilities.sh" \
  status "$image" "$fixture/home" "$uid" "$gid")"
printf '%s\n' "$status_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["action"]=="status" and d["in_sync"]
assert d["specpi_scope_policy"]=="inactive_in_fresh_session"
'

printf '{"card":"M04-T03","global_packages":2,"compatibility_smoke":true,"scope_inactive":true,"mcp_surface":true,"status_read_only":true,"rollback_reapply":true,"runtime_uid":%s,"runtime_gid":%s,"result":"GREEN"}\n' "$uid" "$gid"
