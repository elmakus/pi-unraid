# Decision — LLM-backed test traffic uses GPT-6 Luna Low, never Astra

- Decision ID: `PIB-ADR-008`
- Date: `2026-09-28`
- Status: `accepted`
- Authority: `user`
- Scope: `pi-unraid` test, smoke, acceptance and verification activity that actually invokes an LLM through Pi/Paseo/Codex-LB

## Decision

- Every repository-managed test, smoke, acceptance, verification or diagnostic flow that sends a real inference request to an LLM MUST use provider `codex-lb`, model `gpt-6-luna`, with reasoning/thinking effort `low`.
- `gpt-6-astra` MUST NOT be used for LLM-backed test traffic. It is not an allowed fallback, substitute, smoke model or acceptance model.
- If `gpt-6-luna` with `low` reasoning is unavailable, an LLM-backed test MUST fail closed or report a blocked/unavailable prerequisite. It MUST NOT silently switch to Astra or another model.
- Tests that only enumerate a catalog, validate configuration, exercise a fake/local fixture, or otherwise do not send a real LLM inference request are not required to select an LLM model.
- This policy does not remove models from the user-facing model picker and does not constrain the user's normal interactive model choice outside test traffic.
- Any future change to this test-model policy requires a new explicit user decision; incidental upstream defaults or model availability MUST NOT override it.

## Rationale

The user explicitly requires predictable, lower-cost LLM-backed test execution on `gpt-6-luna` at `low` reasoning and explicitly forbids using `gpt-6-astra` for tests.

## Acceptance implications

Repository-managed LLM test harnesses and durable test instructions must encode or assert `codex-lb/gpt-6-luna` plus `low`, and contract tests must reject Astra as a test model.
