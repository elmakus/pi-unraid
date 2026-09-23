#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-pi-unraid:m02-t01}"
ROOT="$(mktemp -d /tmp/pi-unraid-m02-t01.XXXXXX)"
HOME_DIR="$ROOT/home"
EMPTY_HOME="$ROOT/empty-home"
FIXTURE_PACKAGE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/tests/fixtures/m02/pi-package"
UID_FIXTURE="${PI_TEST_UID:-21001}"
GID_FIXTURE="${PI_TEST_GID:-21001}"

cleanup() {
  rm -rf "$ROOT"
}
trap cleanup EXIT

mkdir -p "$HOME_DIR" "$EMPTY_HOME"

run_home() {
  docker run --rm     -e PI_UID="$UID_FIXTURE"     -e PI_GID="$GID_FIXTURE"     -v "$HOME_DIR:/home/pi"     "$IMAGE" "$@"
}

run_fixture() {
  docker run --rm     -e PI_UID="$UID_FIXTURE"     -e PI_GID="$GID_FIXTURE"     -e PI_UNRAID_TEST_LATEST_OVERRIDE="${PI_TEST_LATEST:?}"     -e PI_UNRAID_TEST_INSTALL_SPEC_OVERRIDE="file:/fixture/pi-package"     -e PI_TEST_VERSION="${PI_TEST_LATEST}"     -e PI_TEST_PROBE_FAIL="${PI_TEST_PROBE_FAIL:-0}"     -v "$HOME_DIR:/home/pi"     -v "$FIXTURE_PACKAGE:/fixture/pi-package:ro"     "$IMAGE" "$@"
}

printf '%s\n' 'M02-T01: real latest-stable staging and RPC readiness'
run_home pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
version="$(printf '%s\n' "$status" | jq -r '.selected.version')"
source="$(printf '%s\n' "$status" | jq -r '.selected.source')"
[ "$source" = persistent ]
[ -n "$version" ]
[ "$(printf '%s\n' "$status" | jq -r '.status')" = ready ]
run_home pi-unraid-runtime health
[ "$(run_home pi --version | tail -n 1)" = "$version" ]
run_home sh -lc 'printf "%s" t01-marker > ~/.pi/agent/m02-t01-marker'
marker_before="$(sha256sum "$HOME_DIR/.pi/agent/m02-t01-marker" | awk '{print $1}')"

printf '%s\n' 'M02-T01: persistent recreation, stale staging and serialized overlap'
mkdir -p "$HOME_DIR/.local/share/pi-unraid/runtimes/.staging-stale"
printf 'partial\n' > "$HOME_DIR/.local/share/pi-unraid/runtimes/.staging-stale/partial"
run_home sh -lc 'pi-unraid-runtime health && test "$(pi --version | tail -n 1)" = "$(jq -r .selected.version ~/.local/state/pi-unraid/runtime.json)"'
run_home sh -lc 'pi-unraid-runtime reconcile & a=$!; pi-unraid-runtime reconcile & b=$!; wait "$a"; wait "$b"; pi-unraid-runtime health'
[ -f "$HOME_DIR/.local/share/pi-unraid/runtimes/.staging-stale/partial" ]
[ "$(stat -c '%a' "$HOME_DIR/.local/state/pi-unraid/runtime.json")" = 600 ]

printf '%s\n' 'M02-T01: candidate probe failure preserves LKG'
export PI_TEST_LATEST=9.9.9
export PI_TEST_PROBE_FAIL=1
run_fixture pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.outcome')" = candidate_probe_failed ]
[ "$(printf '%s\n' "$status" | jq -r '.selected.version')" = "$version" ]
[ "$(printf '%s\n' "$status" | jq -r '.failed_candidate.version')" = 9.9.9 ]
run_home pi-unraid-runtime health

printf '%s\n' 'M02-T01: failed candidate cooldown avoids immediate reinstall'
run_fixture pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.outcome')" = candidate_cooldown ]

printf '%s\n' 'M02-T01: explicit retry bypasses cooldown but still preserves LKG on probe failure'
run_fixture pi-unraid-runtime retry
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.outcome')" = candidate_probe_failed ]
[ "$(printf '%s\n' "$status" | jq -r '.selected.version')" = "$version" ]

printf '%s\n' 'M02-T01: install failure preserves LKG'
export PI_TEST_LATEST=9.9.8
export PI_TEST_PROBE_FAIL=0
docker run --rm   -e PI_UID="$UID_FIXTURE" -e PI_GID="$GID_FIXTURE"   -e PI_UNRAID_TEST_LATEST_OVERRIDE="$PI_TEST_LATEST"   -e PI_UNRAID_TEST_INSTALL_SPEC_OVERRIDE="file:/fixture/does-not-exist"   -v "$HOME_DIR:/home/pi"   -v "$FIXTURE_PACKAGE:/fixture/pi-package:ro"   "$IMAGE" pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.outcome')" = candidate_install_failed ]
[ "$(printf '%s\n' "$status" | jq -r '.selected.version')" = "$version" ]

printf '%s\n' 'M02-T01: prerelease-shaped latest is rejected'
export PI_TEST_LATEST=9.9.10-beta.1
run_fixture pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.outcome')" = unstable_latest_rejected ]
[ "$(printf '%s\n' "$status" | jq -r '.selected.version')" = "$version" ]

printf '%s\n' 'M02-T01: registry-unavailable path falls back without losing LKG'
docker run --rm   -e PI_UID="$UID_FIXTURE" -e PI_GID="$GID_FIXTURE"   -e PI_UNRAID_LOOKUP_TIMEOUT_SECONDS=2   -e npm_config_registry=http://127.0.0.1:9   -e npm_config_fetch_retries=0   -v "$HOME_DIR:/home/pi"   "$IMAGE" pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.outcome')" = registry_unavailable ]
[ "$(printf '%s\n' "$status" | jq -r '.selected.version')" = "$version" ]
run_home pi-unraid-runtime health

printf '%s\n' 'M02-T01: missing persistent LKG falls back to immutable image seed'
rm -rf "$HOME_DIR/.local/share/pi-unraid/runtimes/$version"
docker run --rm   -e PI_UID="$UID_FIXTURE" -e PI_GID="$GID_FIXTURE"   -e PI_UNRAID_LOOKUP_TIMEOUT_SECONDS=2   -e npm_config_registry=http://127.0.0.1:9   -e npm_config_fetch_retries=0   -v "$HOME_DIR:/home/pi"   "$IMAGE" pi-unraid-runtime reconcile
status="$(run_home pi-unraid-runtime status)"
[ "$(printf '%s\n' "$status" | jq -r '.selected.source')" = seed ]
[ "$(printf '%s\n' "$status" | jq -r '.status')" = degraded ]
run_home pi-unraid-runtime health
[ "$(run_home pi --version | tail -n 1)" = "$(printf '%s\n' "$status" | jq -r '.image_seed_version')" ]

printf '%s\n' 'M02-T01: unavailable state never reports healthy'
if docker run --rm   -e PI_UID="$UID_FIXTURE" -e PI_GID="$GID_FIXTURE"   -e PI_UNRAID_SEED_CLI=/nonexistent   -e PI_UNRAID_LOOKUP_TIMEOUT_SECONDS=2   -e npm_config_registry=http://127.0.0.1:9   -e npm_config_fetch_retries=0   -v "$EMPTY_HOME:/home/pi"   "$IMAGE" pi-unraid-runtime reconcile; then
  printf '%s\n' 'expected unavailable reconcile to fail' >&2
  exit 1
fi
if docker run --rm   -e PI_UID="$UID_FIXTURE" -e PI_GID="$GID_FIXTURE"   -e PI_UNRAID_SEED_CLI=/nonexistent   -v "$EMPTY_HOME:/home/pi"   "$IMAGE" pi-unraid-runtime health; then
  printf '%s\n' 'expected unavailable health to fail' >&2
  exit 1
fi
[ "$(docker run --rm -e PI_UID="$UID_FIXTURE" -e PI_GID="$GID_FIXTURE" -e PI_UNRAID_SEED_CLI=/nonexistent -v "$EMPTY_HOME:/home/pi" "$IMAGE" pi-unraid-runtime status | jq -r '.status')" = unavailable ]

marker_after="$(sha256sum "$HOME_DIR/.pi/agent/m02-t01-marker" | awk '{print $1}')"
[ "$marker_before" = "$marker_after" ]

printf 'M02-T01 runtime selector verification: GREEN (real stable=%s)\n' "$version"
