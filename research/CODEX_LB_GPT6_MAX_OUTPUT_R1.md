# Codex-LB GPT-6 max-output diagnosis — R1

Date: 2026-09-28
Repair subject: `repair:codex-lb-gpt6-max-output-128k:v1`

## Finding

OpenAI's current official model catalog documents **128,000 max output tokens** for all three current GPT-6 family members relevant here:

- `gpt-6-astra`: 128,000 max output tokens;
- `gpt-6-sol`: 128,000 max output tokens;
- `gpt-6-luna`: 128,000 max output tokens.

Official references checked on 2026-09-28:
- `https://developers.openai.com/api/docs/models/gpt-6-astra`
- `https://developers.openai.com/api/docs/models/gpt-6-luna`
- `https://developers.openai.com/api/docs/models` (current catalog includes `gpt-6-sol` with 128K max output)

## Codex-LB behavior

Production currently runs `ghcr.io/soju06/codex-lb:1.25.0-beta.9`.

Both `Soju06/codex-lb@v1.25.0-beta.9` and current upstream `main` implement `_v1_max_output_tokens(model)` as:

1. use `model.raw["max_output_tokens"]` when the upstream model catalog supplies an integer;
2. otherwise consult `_V1_MAX_OUTPUT_TOKEN_OVERRIDES`;
3. otherwise return `None`.

The override table currently contains 128,000 for older GPT slugs including `gpt-5.5`, but not `gpt-6-astra`, `gpt-6-sol` or `gpt-6-luna`.

The live Codex-LB persisted upstream model-registry snapshot confirms that GPT-6 Astra/Sol/Luna raw metadata contains `context_window`/`max_context_window` but **does not contain `max_output_tokens`**. Consequently live `/v1/models` returns `max_output_tokens: null` for those GPT-6 models.

Pi's dynamic Codex-LB catalog correctly trusts a positive `max_output_tokens` value when present; when absent it uses its conservative generic fallback of 16,384. Thus the displayed/stored 16,384 is not an upstream GPT-6 capability limit; it is a downstream fallback caused by missing Codex-LB capability metadata.

## Prior-art / conflict check

- Official upstream evidence: checked; OpenAI documents 128K max output for Astra/Sol/Luna.
- Actual project/runtime evidence: checked directly against the running Codex-LB image, live `/v1/models`, persisted model registry and Pi production model store.
- Tracker/discussion evidence: searched current `Soju06/codex-lb` Issues and PRs for the GPT-6 `max_output_tokens` omission; no exact existing repair was found. Unrelated probe issues that mention `max_output_tokens` do not repair `/v1/models` capability metadata.
- Practitioner/community evidence: not required for this exact capability value because first-party OpenAI documentation and direct runtime evidence are stronger and non-conflicting.

No material source conflict was found.

## Minimal repair

Add these three entries to Codex-LB's existing `_V1_MAX_OUTPUT_TOKEN_OVERRIDES` fallback table:

```python
"gpt-6-astra": 128_000,
"gpt-6-sol": 128_000,
"gpt-6-luna": 128_000,
```

Do not change `_v1_max_output_tokens()` precedence: a future integer supplied by upstream raw model metadata must continue to win over the fallback table automatically.

The production dependency should return to upstream as soon as an upstream release contains the accepted equivalent fix. Any temporary downstream artifact must retain exact upstream lineage and rollback evidence.

## Explicit non-scope

This repair does not alter context-window selection. OpenAI's public API documentation currently advertises a larger API context window than the default Codex registry value seen by Codex-LB; that is a separate capability/behavior question and is intentionally not bundled into this max-output repair.
