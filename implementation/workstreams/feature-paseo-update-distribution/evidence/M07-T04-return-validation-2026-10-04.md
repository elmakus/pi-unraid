# M07-T04 — Main return validation before semantic result acceptance

Date: 2026-10-04
Owner: common Execution result reconciliation for M07-T04
Classification: stable contract remains valid; initial return is incomplete/incorrect and requires bounded correction. This is not an independent review verdict, accepted Card result or user stop.

## Exact inspected contribution

- Implementation: `elmakus/pi-unraid@1991306705f894839529ff619bad4f2b0e6f2755`.
- Evidence: `elmakus/pi-unraid@bae5214980f6f0ea21fe41fa07ce4a4096147370:implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T04-baseline-implementation-2026-10-04.md@d8b89110c53fb09c252610eafa9bdefd5a13fca6`.
- Stable acceptance: `implementation/workstreams/feature-paseo-update-distribution/cards/M07-T04.md` under approved P4/cycle 4 and R2/ADR-PUD-004.
- Target readback: `main@e9476b4987290767a195a9de2ecd655de5f09605`.
- Canonical router/Execution contract: default branch `elmakus/project_workflow_v2@d3ab917f02e4de91b7dbb17915c2287c2387333e`.

Contribution changes are product/source plus the single implementation report. Main worktree remains clean. Selected workflow state, frozen plan, stable Card, historical results/reviews and the exact DONE dependency were not rewritten. The reported tests are synthetic/no-inference; Main has not independently rerun those counts or claimed final validation.

## Concrete correction boundaries

### 1. Behavioral rejection/readback evidence

`tests/test_llm_test_policy_contract.py:test_runner_rejects_wrong_profile_without_fallback` writes a bad temp policy but never copies/invokes the launcher against it. Its assertions only compare the constructed bad value with `max`. Likewise `test_m07_t04_policy_delivery.py:test_unsupported_or_downgraded_profile_cannot_report_acceptance` only compares literal strings. These are not evidence that the delivered guard rejected a bad profile, unavailable execution or fallback.

Exercise the actual repo-delivered launcher through a disposable symlink-free agent-root copy and fake Paseo executable. Cover invalid provider/model/contribution/fallback/forbidden policy and unavailable execution; prove nonzero failure and that no forbidden dispatch/fallback occurred. All such calls must remain fake/non-inference. Preserve the fixed canonical profile and invocation semantics.

The max-null/clamp test currently reads an absolute installed package path, may skip, and executes a hand-written Python mirror rather than Pi's actual selection function. Use portable pinned-source fixtures and/or an explicitly version/provenance-checked pure upstream-function readback, with honest executed/skipped accounting. Preserve the direct-Meta metadata-versus-endpoint distinction. Any effective-profile acceptance boundary not implemented until M07-T05 must be named as deferred, not represented by a tautological passed rejection test. No real inference or final-validator scope is admitted here.

### 2. Explicit frozen companion-bundle binding

The report and `test_candidate_build_context_binds_companion_bundle` infer eligibility binding from `shutil.copytree` and staged candidate-path strings. At the inspected subject, Dockerfile copies only the entrypoint wrapper and does not carry the instruction bundle; `paseo_buildx.verify_build_inputs` returns candidate/Paseo/Pi fields only. The existing prepare/build/package records do not declare the bundle digest or enforce its identity. Merely placing unused files in build context does not prove image delivery or an immutable image-plus-companion eligibility identity.

Within this baseline's included scope, provide a narrow explicit secret-free companion declaration/source/mode identity through the existing candidate/build/package evidence path and meaningful positive/negative synthetic tests. Account for actual payload delivery or an intentionally separate frozen companion. Changed/missing/wrong bundle or unverifiable provenance must not silently preserve the same declared binding. Do not mutate live HOME, make an older digest eligible, create another resolver/topology/ledger, build an image or implement final M07-T05/T06 gates. Update the report to describe what is actually bound, not just copied.

### 3. Preserve non-conflicting target contract intent

The target `contracts/PASEO_CODEX_LB_RUNTIME_ENV.md` includes secret propagation, upstream entrypoint ownership and verified dynamic capability metadata as well as superseded test/rollout text. Its absence from the branch does not demonstrate compatibility-contract preservation merely because one section uses the old test profile. Reconcile the necessary non-conflicting product contract/documentation under the stable baseline's target-preservation scope, replacing or explicitly qualifying only superseded test/rollout provisions by current R2/ADR-PUD-004/P4. This does not require a new optional Card technical contract, new product decision or modification of frozen planning/requirements. Do not claim scope-authority reentry simply because a technical document needs bounded correction; return any actual contradiction with exact evidence for Main classification.

## Return discipline

Keep the same active Card and restrictions. Commit bounded corrections and updated implementation evidence, retaining the initial bytes in Git history. Record the exact corrected implementation subject and precise test/readback scope. No push, inference, credential admission, installed runtime/HOME/host/production mutation, Board/Card/result/review/plan finalization or further delegation. Remove only verified generated Python cache artifacts, or prevent their regeneration; do not clean unknown/untracked source files indiscriminately.

Main will revalidate the corrected contribution before accepting one semantic result. A future REQUIRED review uses a fresh independent context that did not implement or repair the resulting subject. The current initial return has no semantic result or review-attempt acceptance.
