#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$repo_root/config/llm-test-policy.json"

[ "$#" -ge 1 ] && [ "$#" -le 2 ] || {
  echo "usage: $(basename "$0") PROMPT [CWD]" >&2
  exit 2
}
prompt="$1"
cwd="${2:-$PWD}"

provider="$(jq -er '.real_llm_tests.provider' "$policy")"
model="$(jq -er '.real_llm_tests.model' "$policy")"
thinking="$(jq -er '.real_llm_tests.thinking' "$policy")"
fallback="$(jq -r '.real_llm_tests.fallback_allowed | tostring' "$policy")"

[ "$provider" = "codex-lb" ] || { echo "LLM test policy error: provider must be codex-lb" >&2; exit 3; }
[ "$model" = "gpt-6-luna" ] || { echo "LLM test policy error: model must be gpt-6-luna" >&2; exit 3; }
[ "$thinking" = "low" ] || { echo "LLM test policy error: thinking must be low" >&2; exit 3; }
[ "$fallback" = "false" ] || { echo "LLM test policy error: fallback must be disabled" >&2; exit 3; }
if jq -e '.real_llm_tests.forbidden_models | index("gpt-6-astra") != null' "$policy" >/dev/null; then :; else
  echo "LLM test policy error: gpt-6-astra must remain explicitly forbidden" >&2
  exit 3
fi

exec paseo run \
  --provider pi \
  --model "$provider/$model" \
  --thinking "$thinking" \
  --cwd "$cwd" \
  --title "LLM-TEST:$model:$thinking" \
  "$prompt"
