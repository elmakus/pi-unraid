# Real LLM test policy

This is the mandatory pi-unraid policy for any automated or manual verification whose purpose includes causing a real language-model inference.

## Required execution profile

- Provider: `meta` (Paseo runtime provider: `pi`)
- Model: **`muse-spark-1.3-contributor`** — Muse Code 1.3 Spark / catalog label Muse Spark 1.3 Contributor
- Thinking/contribution: **`max`**
- Fallback: **forbidden**
- `gpt-6-astra`: **never permitted for real LLM test execution**

If `meta/muse-spark-1.3-contributor` with `max` is unavailable, the real-LLM test is blocked/failed. Do not substitute another model or a different contribution level to make the test pass.

## What counts as a real LLM test

The rule applies to smoke tests, regression tests, acceptance checks, deployment verification, provider round-trip probes, UI/Relay checks and any other verification that intentionally sends a prompt which causes an actual model response.

The rule does not apply to non-inference checks such as catalog enumeration, `/v1/models` retrieval, auth/health probes, parser/unit tests, fake-model fixtures, static metadata checks, or ordinary human interactive work. Model names including `gpt-6-astra` may appear as fixture/catalog data; they must not be selected to execute a test inference.

## Canonical launcher

Real LLM tests in this environment must use `~/.pi/agent/bin/run-llm-test.sh`. The launcher reads `~/.pi/agent/policies/llm-test-policy.json`, verifies the exact fixed policy, and invokes Paseo with `--provider pi --model meta/muse-spark-1.3-contributor --thinking max`. It offers no model/contribution override and no fallback path.

For a native caller-scoped Paseo child-agent test, first run the launcher with `--native-create-agent-args`. This validates the same fixed policy without inference and emits the required `create_agent` fields: `provider`, `settings.thinkingOptionId`, and `notifyOnFinish`. Use those values unchanged with Paseo's native caller-scoped `create_agent`, adding only the test title and initial prompt; omit `workspaceId` so the child inherits the caller workspace. Read back the child's model, contribution setting, and parent relationship through normal Paseo lifecycle tools; fail the test on any mismatch. This is an allowed diagnostic invocation shape, not a PWv2 delegation fallback or a change to Project Workflow semantics.

Do not bypass these guarded paths with direct `paseo run`, `pi --model`, or another real-inference command when the action is a test. If a new harness needs a different invocation shape, extend the canonical launcher/validator while preserving the same fixed model and contribution.

## Evidence and secrets

Test evidence may record the fixed provider/model/contribution and the pass/fail result. Do not persist provider credentials or unnecessary model response content. Credential handling remains governed by the environment's existing secret boundary.
