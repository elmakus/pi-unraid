# Workstream post-merge closure evidence

- Workstream: `issue-paseo-codex-lb-env-propagation`
- Original source branch: `fix/paseo-codex-lb-runtime-env`
- Integration target: `main`
- Final scope-completing PR: `#12`
- Exact merged source head: `ae0d580aa13aae8ee67064c0a12802d62de4c959`
- Target pre-merge head: `1eaffc98660da3d89a6f2d473570db931c9dc38f`
- Merge commit/result: `12fae1f7f444afb96e3da9bc56618be383432c86`
- Closure publication: closure-only PR `#13` from `chore/paseo-codex-lb-env-close`
- Result: **GREEN — permanent Paseo-to-Pi Codex-LB credential propagation repair and Luna/low-only real-LLM test policy are integrated into `main`**
- Runtime/deployment mutation during post-merge closure bookkeeping: **none**

## Immutable integration readback

GitHub reports PR #12 as MERGED on 2026-09-28 with base `main`, exact source head `ae0d580aa13aae8ee67064c0a12802d62de4c959`, and merge commit `12fae1f7f444afb96e3da9bc56618be383432c86`.

The merge commit has parents `1eaffc98660da3d89a6f2d473570db931c9dc38f` and `ae0d580aa13aae8ee67064c0a12802d62de4c959`. Its tree is identical to the exact merged source head, proving that the accepted repair package was integrated without target-side content substitution.

The original source branch is absent on post-merge readback. This is normal automatic cleanup and it must not be recreated.

## Target-side recovery package

The merge-result `main` contains the complete workstream package, including original branch/base/target provenance, Intake diagnosis and exact prior-art binding, linked tracker Issue #10, stable M01-T01 Card, exact result, pre-production and production evidence, REQUIRED independent review `M01-T01-R01` GREEN, and Close pre-integration refresh evidence.

Target-side recovery therefore no longer depends on the deleted source ref.

## Tracker closure readback

Issue #10 was read back `CLOSED` with reason `COMPLETED` immediately after accepted integration. GitHub had already recognized PR #12 closing linkage through `closingIssuesReferences`, so no explicit close retry was needed.

## Accepted final state

The repair is repository-managed rather than a production-only hotfix:
- canonical Compose mounts the dedicated Codex-LB secret file read-only and restores `host.docker.internal:host-gateway`;
- the child image installs a bounded project-owned Paseo entrypoint bridge that exports `CODEX_LB_API_KEY` only into the runtime process environment before execing the pinned upstream entrypoint;
- raw `CODEX_LB_API_KEY` remains absent from Docker configured environment, Git and accepted evidence;
- production remains healthy on image `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de` with rollback material retained;
- Paseo independently enumerates all nine current Codex-LB models without manual secret sourcing.

The real-LLM test policy is durable and machine-enforced:
- every real inference test must use `codex-lb/gpt-6-luna` with thinking `low`;
- `gpt-6-astra` is explicitly forbidden for real LLM tests;
- fallback is disabled; unavailable Luna/low means the test blocks/fails rather than substituting another model;
- the rule is present in global Pi instructions, dedicated human-readable policy, machine-readable policy and canonical launcher.

No ordinary interactive user model-selection policy was changed.
