#!/usr/bin/env bash
set -euo pipefail

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$agent_root/policies/llm-test-policy.json"

native_args=false
if [ "$#" -eq 1 ] && [ "$1" = "--native-create-agent-args" ]; then
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

if [ "$native_args" = true ]; then
  jq -n --arg provider "pi/$provider/$model" --arg thinking "$thinking" \
    '{provider: $provider, settings: {thinkingOptionId: $thinking}, notifyOnFinish: true}'
  exit 0
fi

exec paseo run \
  --provider pi \
  --model "$provider/$model" \
  --thinking "$thinking" \
  --cwd "$cwd" \
  --title "LLM-TEST:$model:$thinking" \
  "$prompt"
