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

## Second contribution validation — remaining incomplete boundaries

Inspected corrected implementation: `elmakus/pi-unraid@38d704ac78c40e88dbc4d81851d3bdad4b2337bf`.
Corrected report: `elmakus/pi-unraid@9c3141601b3dc80ef37165f0c809b1b344bb98ac:implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T04-baseline-implementation-2026-10-04.md@69c4655c1693cbf5228ed3835adc080579ebd73a`.

The contribution now invokes the actual launcher in synthetic negative fixtures, executes a provenance-gated pure upstream clamp readback and includes a reconciled target contract. Those are real improvements; source/state remain bounded. Main has not rerun the reported 44/549 counts or accepted a semantic result. The stable Card remains valid and `in_progress`; no review attempt exists.

### A. Reachable build/package enforcement is still missing

A production callsite search finds `verify_companion_binding` only as its definition and test calls. `prepare_context` declares the identity from `source_root` after copying, but never verifies the staged copy against that declaration. `paseo_buildx.verify_build_inputs`, `cmd_build` and `package_tested_image` do not consume the companion declaration. The build record/package output lacks companion identity and does not compare it with the prepared source/candidate/handoff binding. Therefore changed/missing/different staged companions can pass the actual existing build/package path; helper-only rejection tests do not demonstrate that path's enforcement.

Complete this already-requested narrow baseline binding in the existing preparation, build-input readback/record and package path. Verify the actual staged payload; retain and check its declared identity/provenance through the package evidence, failing before external actions when malformed/missing/mismatched. Add integration fixtures against those real entrypoints, not just direct helper tests: positive declared bundle, source/stage divergence, post-prepare content/file-set mutation, missing/malformed declaration, inconsistent source/candidate/handoff identity and build/package mismatch. Use only mocked/fake Docker and disposable filesystem roots. Do not broaden into final validator/promotion gates, trigger builds, alter topology or mutate production.

### B. Dispatch assertions occur after fixture deletion

Both corrected launcher-test helpers return a marker Path from inside `TemporaryDirectory`, then callers evaluate `marker.exists()` after the context manager deleted the directory. These assertions are always false, even if a dispatch occurred. Snapshot and return the marker existence/content/count before cleanup, and include a positive control proving that a valid fake dispatch is observed. For unavailable execution, do not depend on there never being a real Paseo binary in `/usr/bin` or `/bin`: guarantee a fake-only dispatch path or isolate executable resolution so this test cannot accidentally cause real inference on another host. Keep actual launcher behavior, fixed identity and no-fallback semantics unchanged.

### C. Remaining contradictory rollout wording

The reconciled product contract still says real acceptance is performed "if performed" and that "Failure after cutover restores" without the immediate transaction window. R2/P4 requires the bounded real gate before exposure; it is not optional. PUD-REQ-028 ends automatic rollback authority at immediate GREEN, so a later unrelated fault cannot trigger restoration. Qualify the preserved rollout paragraph with the actual guard/exposure/user-trigger/immediate-acceptance sequence and the bounded pre-GREEN rollback authority. This is documentation alignment to existing approved authority, not a new decision or change to frozen requirements/planning. Preserve the non-conflicting secret/upstream/catalog text.

These are incomplete implementation/evidence boundaries under common Execution, not a Research/profile-input/user blocker or independent RED verdict. Correct them within the unchanged Card, update exact implementation/evidence and honest test/readback accounting, then return to Main without finalizing state or pushing.

## Third contribution validation — only actual pipeline binding remains

Inspected implementation: `elmakus/pi-unraid@808c7a459cd99ba5d7f846a6a4a7bf39c45dcbba`.
Report: `elmakus/pi-unraid@c483c5fc674fb8a171a11c4ae37fe49370e856a3:implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T04-baseline-implementation-2026-10-04.md@404ba55d3988d14e9da96720a0c6e994413ee3a5`.

The fixture helpers now snapshot dispatch before cleanup and use test-owned executable resolution; the product contract now states mandatory validation, ordered exposure/user transaction and cessation of rollback at GREEN. Do not reopen those resolved boundaries without new contrary evidence. Main has not rerun or accepted the reported 48/553 counts. No semantic result or review attempt exists.

The package's `build_input_path=None` default explicitly preserves a bypass. The canonical `.github/workflows/paseo-candidate-build.yml` package step does not pass `--build-input`, so its actual output omits the companion entirely. `paseo_buildx` still neither verifies prepared bundle identity before build nor records the companion in its resolution/build evidence. When supplied to package, the new input checks only candidate ID, schema and key presence: it does not verify payload after prepare, declaration types/digest/modes, source/candidate/handoff provenance or matching build-readback identity. Optional shape checks are not fail-closed R2 pipeline binding. The post-prepare mutation fixture still exercises the helper rather than automatic build/package rejection.

Complete the original requested binding through the actual current R2 pipeline. Prepared inputs and the actual staged bundle must be verified before builder/external actions, retained in the build record and checked again against source/candidate/handoff/prepared identity before packaging. Current R2 omission/malformed/mismatched binding must reject, not silently preserve old behavior. Wire the existing workflow steps/arguments to this same required path and retain the bound evidence through its normal artifact handoff. Narrow argument/record wiring in existing jobs is included implementation, not a topology change or CI trigger; do not add jobs, trigger/run/build/publish anything, change default-branch/branch allowances or invent another pipeline. If an explicitly legacy helper remains, it must be non-R2/noneligible and mechanically inaccessible as the current R2 path; do not maintain a silent default bypass.

Use real entrypoint integration fixtures with fake/mocked Docker proving failure before external calls for omitted record, post-prepare mutation/add/remove, malformed fields or false digest, wrong source/candidate/handoff, build-record/prepared mismatch and attempted legacy bypass. Positive prepare/readback/package must carry the same frozen identity. Final M07-T05/T06 acceptance/promotion mechanics remain deferred; no real inference, credentials, live runtime/HOME/host/production or artifact build is authorized. Update the implementation report to the exact corrected subject and accurately distinguish shipped machine enforcement from future final gates. This is remediable incomplete Execution work, not a new Card, Review verdict, Planning change or user blocker.
