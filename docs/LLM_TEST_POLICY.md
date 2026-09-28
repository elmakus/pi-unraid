# Real LLM test policy

This is the mandatory pi-unraid policy for any automated or manual verification whose purpose includes causing a real language-model inference.

## Required execution profile

- Provider: `codex-lb`
- Model: **`gpt-6-luna`**
- Thinking/reasoning effort: **`low`**
- Fallback: **forbidden**
- `gpt-6-astra`: **never permitted for real LLM test execution**

If `gpt-6-luna` is unavailable, the real-LLM test is blocked/failed. Do not substitute Astra, Sol, another model, or a different thinking level to make the test pass.

## What counts as a real LLM test

The rule applies to smoke tests, regression tests, acceptance checks, deployment verification, provider round-trip probes, UI/Relay checks and any other verification that intentionally sends a prompt which causes an actual model response.

The rule does not apply to non-inference checks such as catalog enumeration, `/v1/models` retrieval, auth/health probes, parser/unit tests, fake-model fixtures, static metadata checks, or ordinary human interactive work. Model names including `gpt-6-astra` may appear as fixture/catalog data; they must not be selected to execute a test inference.

## Canonical launcher

Real LLM tests in this repository must use `scripts/run-llm-test.sh`. The launcher reads `config/llm-test-policy.json`, verifies the exact fixed policy, and invokes Paseo with `codex-lb/gpt-6-luna` and `--thinking low`. It offers no model/effort override and no fallback path.

Do not bypass the launcher with direct `paseo run`, `pi --model`, or another real-inference command when the action is a test. If a new harness needs a different invocation shape, extend the canonical launcher/validator while preserving the same fixed model and effort.

## Evidence and secrets

Test evidence may record the fixed provider/model/effort and the pass/fail result. Do not persist provider credentials or unnecessary model response content. Credential handling remains governed by the existing Codex-LB secret boundary.
