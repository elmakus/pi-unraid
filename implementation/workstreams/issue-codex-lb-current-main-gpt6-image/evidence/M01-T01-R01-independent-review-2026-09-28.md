# M01-T01-R01 independent review evidence

Date: 2026-09-28
Workstream: `issue-codex-lb-current-main-gpt6-image`
Card: `M01-T01`
Review attempt: `R01`
Verdict: **GREEN**

## Exact review binding

- Reviewed result subject: `elmakus/pi-unraid@64572cc44629c696790df0d6738705efa41db16a:implementation/workstreams/issue-codex-lb-current-main-gpt6-image/results/M01-T01.md`.
- Reviewed result blob: `d538b0cf1c176e9b2dfc82db3e12b4cee4abc44b`.
- Acceptance surface: `implementation/workstreams/issue-codex-lb-current-main-gpt6-image/cards/M01-T01.md`.
- The reviewer context did not materially produce or repair the exact reviewed result subject.

## Independent verification

1. **Exact upstream ancestry and bounded fork diff**
   - `elmakus/codex-lb@34511dd6e73e4dbc03dd54112e911fa9149f3440` compares as ahead by 8 / behind by 0 from exact accepted upstream `f8ffbac2099a113fba54dfd8d77774f5bca80ffa`; the merge base is that exact upstream commit.
   - GPT-6 repair head `d64c94338305315d28d1e5899a3aee9c5cb53771` is also an ancestor of final source; final is ahead by 5 / behind by 0 from that repair head.
   - The upstream-to-final diff contains exactly the two intended fork publisher workflows plus `app/modules/proxy/api.py`, `tests/integration/test_v1_models.py`, and the three GPT-6 OpenSpec files. No unrelated source file appeared.

2. **Exact-source targeted tests**
   - A fresh temporary checkout of exact final source `34511dd6e73e4dbc03dd54112e911fa9149f3440` was created on Tower for review only.
   - `uv run pytest -q tests/integration/test_v1_models.py` completed **62 passed, 1 warning**.
   - The warning is a Starlette/AnyIO deprecation warning and does not affect the acceptance behavior.

3. **GHCR build provenance**
   - GitHub Actions run `36462879195`, job `Build and push main image`, is completed with conclusion `success`.
   - The publishing workflow emits both `main` and immutable `sha-<short-sha>` tags from the checked-out source.

4. **Independent live production readback**
   - `codex-lb-clean` is running with restart count 0 on `ghcr.io/elmakus/codex-lb:sha-34511dd`.
   - Local image ID is `sha256:f311d34deb4c1859ad7b4e1bfefef0e64b4e3646a9704dc4d56d9c277cb79742`.
   - OCI source revision is exact `34511dd6e73e4dbc03dd54112e911fa9149f3440`.
   - Repo digest is `sha256:fff96614507c45cca70e980a5390eb36a67295ec74d0863a01ca065efe59e2bb`.
   - Unraid template points to the same immutable `sha-34511dd` image.
   - Immediate rollback container `codex-lb-clean-rollback-pre-main-gpt6-20260928` remains preserved, stopped, on `v1.25.0-beta.9-private.1`, restart count 0.

5. **Authenticated catalog and Pi/Paseo state**
   - Authenticated live `/v1/models` returns 9 models.
   - `gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna` each report `context_length=272000` and `128000` for `max_output_tokens`, `maxOutputTokens`, `metadata.max_output_tokens`, and `capabilities.max_output_tokens`.
   - Persisted Pi definitions for Astra/Sol/Luna each report `contextWindow=272000`, `maxTokens=128000`, and `reasoning=true`.
   - Paseo provider discovery exposes 9 Codex-LB models and includes all three GPT-6 models.

## Safety/scope check

- No real LLM inference was executed during review.
- Review activity was read-only against production. The only local write was a disposable temporary source checkout used to rerun tests; it did not modify production state.
- No excluded Pi/Paseo routing, context-window, automatic failover, or unrelated Codex-LB change was observed.

## Verdict

**GREEN.** The frozen M01-T01 result is supported by independent source, test, artifact-provenance, rollback, live-service, and Pi/Paseo readback evidence. No blocking or corrective finding was identified.
