#!/usr/bin/env bash
set -euo pipefail

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$agent_root/policies/llm-test-policy.json"

native_args=false
candidate_owned=false
if [ "$#" -eq 2 ] && [ "$1" = "--candidate-owned" ]; then
  candidate_owned=true
  candidate_config="$2"
elif [ "$#" -eq 1 ] && [ "$1" = "--native-create-agent-args" ]; then
  native_args=true
elif [ "$#" -ge 1 ] && [ "$#" -le 2 ] && [[ "$1" != --* ]]; then
  prompt="$1"
  cwd="${2:-$PWD}"
else
  echo "usage: $(basename "$0") PROMPT [CWD] | --native-create-agent-args" >&2
  exit 2
fi

provider="$(jq -er '.real_llm_tests.provider' "$policy")"
model="$(jq -er '.real_llm_tests.model' "$policy")"
thinking="$(jq -er '.real_llm_tests.thinking' "$policy")"
fallback="$(jq -r '.real_llm_tests.fallback_allowed | tostring' "$policy")"

[ "$provider" = "meta" ] || { echo "LLM test policy error: provider must be meta" >&2; exit 3; }
[ "$model" = "muse-spark-1.3-contributor" ] || { echo "LLM test policy error: model must be muse-spark-1.3-contributor" >&2; exit 3; }
[ "$thinking" = "max" ] || { echo "LLM test policy error: thinking/contribution must be max" >&2; exit 3; }
[ "$fallback" = "false" ] || { echo "LLM test policy error: fallback must be disabled" >&2; exit 3; }
if jq -e '.real_llm_tests.forbidden_models | index("gpt-6-astra") != null' "$policy" >/dev/null; then :; else
  echo "LLM test policy error: gpt-6-astra must remain explicitly forbidden" >&2
  exit 3
fi

# Narrow candidate-only guard extension. The fixed-profile checks above are
# mandatory; the private bridge proves supported daemon/process/API identities,
# acquires without initialPrompt, and persists IDs before its only bounded send.
# No caller/model/thinking override is accepted by this mode.
if [ "$candidate_owned" = true ]; then
  unset PASEO_AGENT_ID PASEO_WORKSPACE_ID PASEO_HOST PASEO_SERVER PASEO_PASSWORD NODE_OPTIONS
  exec node "$agent_root/bin/m07-t05-owned-runtime.mjs" "$candidate_config"
fi

if [ "$native_args" = true ]; then
  jq -n --arg provider "pi/$provider/$model" --arg thinking "$thinking" \
    '{provider: $provider, settings: {thinkingOptionId: $thinking}, notifyOnFinish: true}'
  exit 0
fi

# M07-T05 candidate-correlation forwarding (nonsecret scoped env only).
# Pinned Paseo 0.9.2 dist/commands/agent/run.js forwards ONLY parsed --env
# (first-`=` split via parseKeyValueFlags) into createAgent.env; the CLI
# process environment is NOT copied to the daemon/Pi agent process
# (server createOptions.env -> agent-manager buildLaunchContext -> Pi
# provider createSession -> buildPiLaunch argv/env -> Pi subprocess env).
# Forward exactly these nonsecret correlation/pointer vars when present:
#   M07_T05_TEST_ID / M07_T05_WITNESS_FILE (owned-test witness correlation),
#   META_API_KEY_FILE (private-file pointer; NEVER the secret value).
# Raw secret values are never forwarded. Ambient caller selectors are
# scrubbed and an explicit local workspace is minted so a test never claims
# a caller agent or foreign workspace.
unset PASEO_AGENT_ID PASEO_WORKSPACE_ID
validator_env=()
for _m07_var in M07_T05_TEST_ID M07_T05_WITNESS_FILE META_API_KEY_FILE; do
  _m07_val="${!_m07_var:-}"
  [ -n "$_m07_val" ] || continue
  case "$_m07_val" in
    *$'\n'*|*"="*|*"--"*) echo "LLM test policy error: invalid validator env: $_m07_var" >&2; exit 3 ;;
  esac
  case "$_m07_val" in
    /*|[A-Za-z0-9_][A-Za-z0-9_.-]*) ;;
    *) echo "LLM test policy error: invalid validator env: $_m07_var" >&2; exit 3 ;;
  esac
  validator_env+=(--env "$_m07_var=$_m07_val")
done
# Correlate the owned agent by title when a test ID is present; the fixed
# LLM-TEST:model:thinking title is otherwise unchanged.
run_title="LLM-TEST:$model:$thinking"
if [ -n "${M07_T05_TEST_ID:-}" ]; then
  run_title="$run_title:${M07_T05_TEST_ID}"
fi

exec paseo run \
  --provider pi \
  --model "$provider/$model" \
  --thinking "$thinking" \
  --cwd "$cwd" \
  --new-workspace local \
  --title "$run_title" \
  ${validator_env[@]+"${validator_env[@]}"} \
  "$prompt"
