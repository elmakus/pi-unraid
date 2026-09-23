#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_ROOT="${PI_UNRAID_DEPLOYMENT_STATE_ROOT:-/mnt/user/appdata/pi-unraid/deployment-state}"
ACTIVE_TAG="${PI_UNRAID_ACTIVE_TAG:-pi-unraid:local}"
CANDIDATE_TAG="${PI_UNRAID_CANDIDATE_TAG:-pi-unraid:candidate}"
PREVIOUS_TAG="${PI_UNRAID_PREVIOUS_TAG:-pi-unraid:previous}"
COMPOSE_PROJECT="${PI_UNRAID_COMPOSE_PROJECT:-pi-unraid}"
COMPOSE_OVERRIDE="${PI_UNRAID_COMPOSE_OVERRIDE:-}"
HEALTH_TIMEOUT="${PI_UNRAID_UPDATE_HEALTH_TIMEOUT_SECONDS:-60}"
LOCK_TIMEOUT="${PI_UNRAID_UPDATE_LOCK_TIMEOUT_SECONDS:-30}"
KEEP_TRANSACTIONS="${PI_UNRAID_UPDATE_KEEP_TRANSACTIONS:-2}"

log() { printf 'pi-unraid update: %s\n' "$*" >&2; }
die() { log "$*"; exit 1; }

is_uint() { [[ "${1:-}" =~ ^[0-9]+$ ]]; }

compose_args() {
  COMPOSE_ARGS=(docker compose -p "$COMPOSE_PROJECT" -f "$REPO_ROOT/compose.yaml")
  if [ -n "$COMPOSE_OVERRIDE" ]; then
    COMPOSE_ARGS+=(-f "$COMPOSE_OVERRIDE")
  fi
}

acquire_lock() {
  mkdir -p "$STATE_ROOT"
  if [ "${PI_UNRAID_UPDATE_LOCK_HELD:-0}" = 1 ]; then
    : >&9 2>/dev/null || die "inherited update lock fd is unavailable"
    return
  fi
  exec 9>"$STATE_ROOT/update.lock"
  flock -w "$LOCK_TIMEOUT" 9 || die "timed out waiting for update lock"
  export PI_UNRAID_UPDATE_LOCK_HELD=1
}

wait_healthy() {
  local mode="$1" deadline cid status
  shift
  local -a dc=("$@")
  deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    cid="$("${dc[@]}" ps -q pi 2>/dev/null || true)"
    if [ -n "$cid" ]; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || true)"
      if [ "$status" = healthy ]; then
        printf '%s\n' "$cid"
        return 0
      fi
      if [ "$mode" = cutover ] && [ "${PI_UNRAID_TEST_FORCE_CUTOVER_UNHEALTHY:-0}" = 1 ]; then
        break
      fi
    fi
    sleep 1
  done
  return 1
}

render_config() {
  local output="$1"
  compose_args
  "${COMPOSE_ARGS[@]}" config >"$output"
}

checkout_upstream() {
  local branch upstream
  [ -z "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=normal)" ] ||
    die "working tree is not clean; refusing repository/deployment mutation"
  branch="$(git -C "$REPO_ROOT" symbolic-ref --quiet --short HEAD)" ||
    die "update requires a checked-out branch"
  upstream="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)" ||
    die "current branch has no upstream"
  printf '%s\n' "$upstream"
}

snapshot_pre_update() {
  local tx="$1" current_id
  mkdir -p "$tx"
  git -C "$REPO_ROOT" rev-parse HEAD >"$tx/pre-source-head"
  current_id="$(docker image inspect "$ACTIVE_TAG" --format '{{.Id}}' 2>/dev/null)" ||
    die "active image $ACTIVE_TAG does not exist"
  printf '%s\n' "$current_id" >"$tx/pre-image-id"
  render_config "$tx/pre-update.compose.yaml"
  printf '%s\n' prepared >"$tx/status"
  ln -sfn "$(basename "$tx")" "$STATE_ROOT/latest"
}

run_candidate_verification() {
  if [ -n "${PI_UNRAID_TEST_VERIFY_COMMAND:-}" ]; then
    PI_UNRAID_CANDIDATE_TAG="$CANDIDATE_TAG" bash -c "$PI_UNRAID_TEST_VERIFY_COMMAND"
    return
  fi
  bash "$REPO_ROOT/scripts/verify-base-image.sh" "$CANDIDATE_TAG"
  bash "$REPO_ROOT/scripts/verify-compose-foundation.sh" "$CANDIDATE_TAG"
  bash "$REPO_ROOT/scripts/verify-git-worktree-foundation.sh" "$CANDIDATE_TAG"
  bash "$REPO_ROOT/scripts/verify-runtime-selector.sh" "$CANDIDATE_TAG"
  bash "$REPO_ROOT/scripts/verify-managed-lifecycle.sh" "$CANDIDATE_TAG"
}

record_runtime() {
  local cid="$1" output="$2"
  docker exec -u pi "$cid" pi-unraid-runtime status | sed -n '/^{/,$p' >"$output"
  jq -e '.selected.version != null and (.status == "ready" or .status == "degraded")' "$output" >/dev/null
}

cleanup_transactions() {
  local keep="$KEEP_TRANSACTIONS" dir
  is_uint "$keep" || die "PI_UNRAID_UPDATE_KEEP_TRANSACTIONS must be an integer"
  mapfile -t dirs < <(find "$STATE_ROOT" -maxdepth 1 -mindepth 1 -type d -name 'tx-*' -printf '%T@ %p\n' |
    sort -nr | awk '{print $2}')
  for ((i=keep; i<${#dirs[@]}; i++)); do
    dir="${dirs[$i]}"
    rm -rf "$dir"
  done
}

rollback_transaction() {
  local tx="$1" old_id cid
  [ -d "$tx" ] || die "rollback transaction does not exist: $tx"
  [ -s "$tx/pre-image-id" ] || die "rollback transaction lacks pre-image-id"
  [ -s "$tx/pre-update.compose.yaml" ] || die "rollback transaction lacks rendered config"
  old_id="$(cat "$tx/pre-image-id")"
  docker image inspect "$old_id" >/dev/null 2>&1 ||
    die "retained rollback image $old_id is unavailable"
  docker image tag "$old_id" "$PREVIOUS_TAG"
  docker image tag "$old_id" "$ACTIVE_TAG"
  local -a rollback_dc=(docker compose -p "$COMPOSE_PROJECT" -f "$tx/pre-update.compose.yaml")
  "${rollback_dc[@]}" up -d --no-build --force-recreate
  cid="$(wait_healthy rollback "${rollback_dc[@]}")" ||
    die "restored previous deployment did not become healthy"
  printf '%s\n' "$old_id" >"$tx/rollback-image-id"
  printf '%s\n' rolled_back >"$tx/status"
  log "rollback healthy with image $old_id container $cid; Git source was not rewritten"
}

continue_update() {
  local tx="$1" old_id candidate_id cid
  [ -d "$tx" ] || die "transaction directory is missing"
  printf '%s\n' "$(git -C "$REPO_ROOT" rev-parse HEAD)" >"$tx/post-source-head"

  if [ "${PI_UNRAID_TEST_FAIL_BUILD:-0}" = 1 ]; then
    printf '%s\n' build_failed >"$tx/status"
    cleanup_transactions
    die "injected candidate build failure"
  fi

  if ! docker build -t "$CANDIDATE_TAG" "$REPO_ROOT"; then
    printf '%s\n' build_failed >"$tx/status"
    docker image rm "$CANDIDATE_TAG" >/dev/null 2>&1 || true
    cleanup_transactions
    die "candidate build failed before cutover"
  fi
  candidate_id="$(docker image inspect "$CANDIDATE_TAG" --format '{{.Id}}')"
  printf '%s\n' "$candidate_id" >"$tx/candidate-image-id"

  if ! run_candidate_verification; then
    printf '%s\n' verification_failed >"$tx/status"
    docker image rm "$CANDIDATE_TAG" >/dev/null 2>&1 || true
    cleanup_transactions
    die "candidate verification failed before cutover"
  fi
  printf '%s\n' verified >"$tx/status"

  old_id="$(cat "$tx/pre-image-id")"
  docker image tag "$old_id" "$PREVIOUS_TAG"
  docker image tag "$candidate_id" "$ACTIVE_TAG"

  compose_args
  local -a cutover_dc=("${COMPOSE_ARGS[@]}")
  if [ -n "${PI_UNRAID_TEST_CUTOVER_OVERRIDE:-}" ]; then
    cutover_dc+=(-f "$PI_UNRAID_TEST_CUTOVER_OVERRIDE")
  fi
  "${cutover_dc[@]}" up -d --no-build --force-recreate
  if ! cid="$(wait_healthy cutover "${cutover_dc[@]}")"; then
    log "candidate deployment unhealthy; restoring retained previous deployment"
    rollback_transaction "$tx"
    docker image rm "$CANDIDATE_TAG" >/dev/null 2>&1 || true
    return 1
  fi

  printf '%s\n' "$candidate_id" >"$tx/post-image-id"
  record_runtime "$cid" "$tx/post-runtime.json"
  printf '%s\n' healthy >"$tx/status"
  docker image rm "$CANDIDATE_TAG" >/dev/null 2>&1 || true
  cleanup_transactions
  log "update healthy: source $(cat "$tx/post-source-head"), image $candidate_id, container $cid"
}

start_update() {
  local upstream tx
  acquire_lock
  compose_args
  upstream="$(checkout_upstream)"
  tx="$STATE_ROOT/tx-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  snapshot_pre_update "$tx"
  cleanup_transactions
  printf '%s\n' "$upstream" >"$tx/upstream-ref"
  git -C "$REPO_ROOT" fetch --prune
  git -C "$REPO_ROOT" merge-base --is-ancestor HEAD "$upstream" ||
    die "current HEAD cannot fast-forward to $upstream"
  git -C "$REPO_ROOT" merge --ff-only "$upstream"
  export PI_UNRAID_UPDATE_LOCK_HELD=1
  exec "$REPO_ROOT/scripts/update.sh" --continue "$tx"
}

manual_rollback() {
  local tx="${1:-}"
  acquire_lock
  if [ -z "$tx" ]; then
    [ -L "$STATE_ROOT/latest" ] || die "no latest deployment transaction is available"
    tx="$STATE_ROOT/$(readlink "$STATE_ROOT/latest")"
  fi
  rollback_transaction "$tx"
}

case "${1:-update}" in
  update)
    start_update
    ;;
  --continue)
    [ "$#" -eq 2 ] || die "usage: update.sh --continue <transaction-directory>"
    acquire_lock
    continue_update "$2"
    ;;
  rollback)
    manual_rollback "${2:-}"
    ;;
  *)
    die "usage: update.sh [update|rollback [transaction-directory]]"
    ;;
esac
