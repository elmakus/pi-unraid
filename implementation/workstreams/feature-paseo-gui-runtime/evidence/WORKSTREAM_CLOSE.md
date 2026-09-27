# Workstream post-merge closure evidence

- Workstream: `feature-paseo-gui-runtime`
- Original source branch: `feat/paseo-gui-runtime`
- Integration target: `main`
- Final scope-completing PR: `#4`
- Exact merged source head: `c3ea146ffd083fb4b93e7c6c8cb30d8743828976`
- Target pre-merge head: `ca196378bc38d87f5267b870de2c5545905279d4`
- Merge commit/result: `cfe5bc64bac0d89ae209fe99d86412dc1dafda3a`
- Closure publication: closure-only PR `#5` from `chore/paseo-gui-runtime-close`
- Result: **GREEN — final target integration succeeded; remaining reconciliation is target-side bookkeeping only**
- Runtime/deployment mutation during closure: **none**

## Immutable integration readback

GitHub reports PR #4 as merged on 2026-09-27 with base `main`, exact source head `c3ea146ffd083fb4b93e7c6c8cb30d8743828976`, and merge commit `cfe5bc64bac0d89ae209fe99d86412dc1dafda3a`.

The `main` branch was read back at that exact merge commit immediately after integration.

The original source branch `feat/paseo-gui-runtime` was absent on post-merge readback. This is normal automatic cleanup under the V2 Close contract. The source branch is not recreated.

## Target-side recovery package

The merge-result `main` contains the V2 workstream package and the unique recovery artifacts required before integration, including:

- `WORKSTREAM.toml` with original branch/base/target provenance;
- `TASK_BOARD.toml` with all materialized Cards terminal;
- stable M01-M08 Task Cards and exact results;
- REQUIRED independent review records and evidence, including M08-T01-R01 GREEN;
- M08-T01 final production evidence ledger;
- M08-T02 close-readiness result/evidence;
- Close pre-integration target refresh and 382/382 affected-compatibility verification evidence;
- approved requirements, ADR-PGR-001..004 and P4 planning authority.

Target-side recovery therefore no longer depends on the deleted source ref.

## Accepted final state

M08-T01 final production evidence is GREEN under REQUIRED independent review. M08-T02 is close-ready GREEN and all approved P4 Card-level obligations are complete.

Production acceptance established before Close remains unchanged: Paseo is the authoritative Pi GUI/runtime on the accepted immutable image; the legacy standalone Pi runtime is retired while migration/rollback material is retained; SpecPi wishlist is enabled and project-scope monitoring remains inactive.

Routine scheduled Appdata Backup remains explicitly degraded through the 2026-09-27 failed run. This residual risk is not reclassified as GREEN. The bounded M07 production and legacy-retirement archives remain verified.

## Downstream boundary

This completed workstream does not authorize Orchestration Runtime live integration or future PWv2.1 Pi-extension packaging/bootstrap. Those remain separate scopes under their own authority.

No implementation, acceptance condition, production configuration, runtime behavior, host state, secret, backup or network state is changed by the closure publication.
