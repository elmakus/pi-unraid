# Workstream post-merge closure evidence

- Workstream: `issue-codex-lb-current-main-gpt6-image`
- Original source branch: `fix/codex-lb-current-main-gpt6-image`
- Integration target: `main`
- Final scope-completing PR: `#16`
- Exact merged source head: `c01af97b0ee4cc66d0adbf9f991a2711349d9c93`
- Target pre-merge head: `4fdeaedbe65aac20fbe7f32e1b7d4ef4adb5e08a`
- Merge commit/result: `8faba8e4fd866ffa29bbbc2247b363ad9d680eac`
- Closure publication: closure-only PR `#17` from `chore/codex-lb-current-main-gpt6-close`
- Result: **GREEN — current upstream main plus the bounded GPT-6 128K repair is integrated as the immutable production Codex-LB image**
- Runtime/deployment mutation during post-merge closure bookkeeping: **none**

## Immutable integration readback

GitHub reports PR #16 as merged with base `main`, exact source head `c01af97b0ee4cc66d0adbf9f991a2711349d9c93`, and merge commit `8faba8e4fd866ffa29bbbc2247b363ad9d680eac`.

Comparing the exact merged source head to the merge commit yields one merge commit and **no changed files**, proving that the accepted source tree was integrated without target-side content substitution.

The original source branch is absent on post-merge readback. This is normal automatic cleanup and must not be recreated.

## Target-side recovery package

The merge-result `main` contains the complete workstream package: original branch/base/target provenance, Intake authorization and exact prior-art binding, consumed Research result, stable M01-T01 Card, exact result locator, pre-production and production evidence, REQUIRED independent review `M01-T01-R01` GREEN, and Close pre-integration refresh evidence.

Target-side recovery therefore no longer depends on the deleted source ref. No GitHub tracker is durably linked to this workstream, so there is no tracker-close mutation to reconcile.

## Accepted final production state

- Codex-LB source: `elmakus/codex-lb@34511dd6e73e4dbc03dd54112e911fa9149f3440`.
- Exact accepted upstream ancestor: `Soju06/codex-lb@f8ffbac2099a113fba54dfd8d77774f5bca80ffa`.
- Immutable production image: `ghcr.io/elmakus/codex-lb:sha-34511dd`.
- OCI digest: `sha256:fff96614507c45cca70e980a5390eb36a67295ec74d0863a01ca065efe59e2bb`.
- Production and the Unraid template use that immutable image; production was independently read back running with restart count 0.
- Immediate rollback `v1.25.0-beta.9-private.1` remains preserved.
- Authenticated `/v1/models` exposes 9 models; GPT-6 Astra/Sol/Luna report context `272000` and max output `128000`; Pi/Paseo persisted state converges to `maxTokens=128000`.
- Independent exact-source targeted test rerun: `62 passed`.
- No real LLM inference was required or executed during independent review.

No mutable `:main` production pin, automatic upstream tracking, Pi/Paseo model-selection/failover change, or context-window override was introduced.
