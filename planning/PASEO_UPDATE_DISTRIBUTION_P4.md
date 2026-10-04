# Paseo/Pi Update Distribution — Strategic Plan P4

Plan revision: P4
Planning cycle: 4
Status: frozen for Premium B / independent Plan Review; not approved for execution
Definition: R2 / paseo-update-distribution@11
Workstream: feature-paseo-update-distribution
Branch: feat/paseo-update-distribution
Review mode: independent
Date: 2026-10-04
Entry subject: `elmakus/pi-unraid@2dc251e08d2a6e01374351a9afb4ce77e8a20d2f:implementation/workstreams/feature-paseo-update-distribution/evidence/M08-T01-definition-reentry-2026-10-04.md@98baf4c422e779d603ec9e53af51fbf905a6dbdd`

## 1. Objective and authority

Complete the existing update-distribution scope under the user-authorized validation correction, without repeating completed work merely because its context disappeared:

current-target/source reconciliation -> reproducible fixed test policy -> guarded exact-candidate Muse validation machinery and non-inference Codex-LB checks -> strengthened final-gate/bootstrap transaction mechanics -> fresh GitHub build-once/GHCR candidate -> disposable autonomous rehearsal -> dedicated credential admission and final real validation -> exact guard arm/readback -> accepted-channel exposure -> user-triggered Update + Verify -> immediate acceptance/recovery -> operationalization and Close.

Binding authority:
- `requirements/PASEO_UPDATE_DISTRIBUTION.md`, R2, PUD-REQ-001..033;
- `decisions/ADR_PUD_001_DISTRIBUTION_AND_CUTOVER.md`;
- `decisions/ADR_PUD_002_MANAGED_COMPONENT_LIFECYCLE.md`;
- `decisions/ADR_PUD_003_ROLLBACK_SAFE_PROMOTION.md`, R2;
- `decisions/ADR_PUD_004_POLICY_COMPLIANT_VALIDATION.md`;
- inherited non-conflicting `requirements/PASEO_GUI_RUNTIME.md` and `decisions/ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md`.

R2/ADR-PUD-004 override prior real Codex-LB and configurable cheap-model smoke provisions. P4 replaces P3's remaining validation/acceptance strategy, not the exact historical implementation/review subjects. Premium A is satisfied for R2 and the exact cycle-4 entry; P3 A/B/C satisfaction is not reused. P4 requires its own independent B review, approval consumption and C before Execution Prep.

## 2. Recovered baseline and material findings

Planning recovery source was `320e4d0a491d756cac9f0bc74209499bc07b24da`; integration target readback is `main@e9476b4987290767a195a9de2ecd655de5f09605`. These are observations to refresh before implementation/integration, not permanent runtime pins.

The selected Task Board preserves 21 DONE Cards M01-T01..M07-T03 and one unstarted M08-T01 in `planned`. No new Task Cards are materialized by this plan. P3's exact frozen plan/review and all terminal results remain historical evidence. The M07 candidate `sha256:77e29f0d8fe8b1975725ba8b430ed7f2225dcc55c2074b397d153fcea3da4cf7` is not accepted under R2 merely because its earlier fixture rehearsal was GREEN.

Repository/contract inspection establishes four concrete remaining risks:
1. The update branch lacks later target-side dynamic Codex-LB catalog/auth-shadow handling, permanent credential entrypoint/Compose repair and test-policy delivery. Blind integration could regress accepted production repairs. Main's older test profile itself must be reconciled to the current mandatory policy, not copied as current test authority.
2. The current Tower validator performs direct Codex-LB `/responses` inference and can report PASS without a real smoke when no credential is supplied. Neither path can establish R2 final acceptance.
3. The promotion writer validates generic GREEN plus guard binding, but does not yet prove all R2 component gates. It also assumes an existing channel digest; recorded preflight found production `:accepted` absent. First exposure needs an explicit verified-absence path.
4. Existing ledger/guard helpers use identical SHA-shaped strings for identity, while the legacy production predecessor is recorded as a Docker image ID and the candidate as an OCI manifest digest. The Update + Verify adapter requires one RepoDigest. First-cutover identity/rollback must therefore be proven, not inferred from matching string syntax.

The completed M06-T03 correction selected the already-authorized single `Update + Verify` fallback after stock-gesture lifecycle binding was not proven. P4 preserves that selection. It does not reopen stock-button research, patch DockerMan core or add a dashboard.

No fresh host acceptance or inference is claimed by planning. The 2026-10-04 preflight's healthy production/digest/channel observations must be reread for later gates.

## 3. Global invariants

1. Normal discovery/resolution/build/mechanical tests are GitHub-hosted; production/provider test secrets never enter CI or image content.
2. Freeze managed component identities and source/policy delivery inputs before build. Build once; preserve and publish the same tested image, then bind Tower and promotion evidence to its immutable OCI digest.
3. Only Paseo/Pi participates in core compatibility backtracking; Node derives from Paseo. Extensions/tools remain independently updated; Playwright/Chromium is one derived unit. No new blocking extension matrix.
4. Preserve the existing managed add/remove helper and atomic registry/install-intent membership. Adoption of already-approved provider support must be reproducible; genuinely new unapproved capabilities return to Definition.
5. Every actual test inference uses the canonical guarded launcher, fixed `meta/muse-spark-1.3-contributor` / `max`, no fallback. All Codex-LB validation is non-inference. Test profile constraints do not select workflow roles or alter interactive model selection.
6. Candidate-bound inference requires inspection of the disposable daemon/Pi path and effective profile, not merely a model label, CLI exit code, working directory or unrelated native child.
7. Use only dedicated operator-controlled validation credentials, admitted to the disposable boundary after all independent machinery is GREEN. Do not copy ordinary agent auth/provider tokens from production HOME into candidate validation.
8. Candidate containers receive no production Docker socket, Unraid administration key, ordinary provider secret or live production HOME. Representative state clones must remove ordinary credentials before candidate code runs.
9. Keep production untouched through autonomous rehearsal. Production guard arm and `:accepted` movement remain M08 operations, after real final validation.
10. Distinguish OCI manifest digest, platform/local image ID, configuration hash, registry alias observation and legacy rollback identity. Never relabel one as another because all begin with `sha256:`.
11. One trusted Tower writer owns accepted-channel serialization and gate evidence. Fixture reports, stale/different-digest reports and caller-provided generic GREEN are insufficient.
12. Production order: exact final validation GREEN -> exact guard arm/readback -> accepted-channel write/readback -> user-chosen Update + Verify -> bounded immediate acceptance/recovery. Availability alone never restarts production.
13. Immediate RED may restore exactly the bound predecessor and verify recovery; GREEN ends automatic rollback authority. Preserve current plus exactly two previous known-good identities and independent rollback anchors.
14. No destructive production HOME restore, whole-host/engine restart, broad network/storage change or secret rotation is authorized by this plan. Separately gated recovery remains gated.
15. Refresh target, production baseline, relevant configuration/state and eligibility immediately before racing mutations. Uncertain external effects require exact readback before retry; no blind create/publish/trigger/inference replay.

## 4. Historical M01-M07 coverage and selective refresh

M01 registry/lifecycle, M02 narrow resolution, M03 exact build/publication, M04 isolation/state proof, M05 promotion/ledger, M06 transaction/fallback and M07 rehearsal remain their original DONE subjects. Do not rewrite those Cards/results to make changed behavior appear reviewed.

Reuse unaffected content/results only after exact-subject/acceptance comparison and affected compatibility verification. R2 invalidates the old real-smoke assumption and any final eligibility depending on it. Target integration, policy delivery, validator/gate/identity repairs and a rebuilt candidate need new exact implementation/result/review evidence. Old 503/503 and 53/53 results do not test new code.

Bounded additional M07 work below precedes M08. These are strategy/decomposition boundaries; Execution Prep creates stable Cards with exact DONE-result dependencies and current authority only after P4 approval/C.

### M07-T04 — Current-target preservation and reproducible policy baseline

- Refresh the target and reconcile its accepted catalog/auth-shadow/credential/Compose/image repairs into the legal source workstream, preserving the update-system changes and unrelated target-side recovery packages.
- Reconcile repository-managed human/machine test policy, guarded launcher and instruction-plane delivery to R2. Preserve ordinary interactive model behavior; remove stale test-only Luna/low or arbitrary-model execution paths without erasing historical evidence/fixture model data.
- Identify the existing approved Muse/provider delivery and pinned dependencies without reading/copying credential values. If the source/install mechanism is agent-findably missing, perform proportional Research before preparation; do not invent an unofficial provider implementation or borrow the active agent's credential.
- Prove that image plus any intentionally staged instruction/provider/policy bundle has frozen, reproducible source/provenance. Any companion bundle is declared in existing candidate/build/validation evidence and must participate in eligibility identity; a mutable live-HOME fix cannot make an older digest R2-compliant.
- Inventory affected test entrypoints before running them. CI/local regression uses only synthetic/local fixtures; actual inference paths remain guarded and disabled until M08.
- Required verification: target/source compatibility, dynamic catalog/auth/entrypoint/Compose contracts, instruction-plane rollback/readback, fixed-policy rejection/no-fallback fixtures, registry/install drift and secret-safe artifact scan. Record what target content was preserved and what was materially changed.

Exit: preserved baseline and reproducible R2 delivery are independently GREEN. No final candidate eligibility, credential admission or production mutation is claimed.

### M07-T05 — Exact-candidate guarded validator and non-inference Codex-LB path

- Replace the direct Codex-LB inference path with authenticated catalog/metadata/auth/health readback and structural response checks. Do not call inference endpoints, silently skip a required failed check or persist provider response bodies.
- Implement a bounded real-Muse test adapter that invokes the canonical guard from the disposable candidate environment. Preferred realization is the guarded CLI using the candidate's own local Paseo home/daemon; explicitly prove endpoint/process/container/Pi provenance and effective profile. Ambient production caller/host/workspace settings must not redirect the test.
- The validated native argument shape is an allowed alternative only if its caller-scoped daemon and child execution are independently proven to belong to the same disposable candidate. A child of the active production daemon is not candidate smoke. A necessary guard extension preserves the same fixed profile and no fallback; unsupported realization routes Research/Planning, never a direct provider call.
- Separate fixture/rehearsal results from real final results. Final eligibility requires completed real inference, verified profile/policy/candidate binding and successful required non-inference checks. Missing inputs, pending/uncertain inference, timeout, negative terminal result or identity mismatch cannot become GREEN.
- Design dedicated secret admission with approved local file/mount/OAuth mechanisms, private permissions and restricted provider-specific scope. No raw `--env KEY=value`, token-bearing argv, auth export, CI secret, image credential or production-auth clone.
- Keep cleanup bounded to verified owned disposable objects; no unconditional removal of an existing same-name object or global cache/HOME deletion.
- Required fixtures: wrong model/contribution, fallback/bypass, wrong daemon/image/bundle, missing credential, fake PASS, malformed/auth-denied/unreachable Codex metadata, inference endpoint rejection, timeout/uncertain return, leaked-token output and cleanup collision. No real inference is run in this Card.

Exit: validator/secret plumbing and host-verifiable evidence semantics are independently GREEN using fixtures; the real-smoke gate stays unsatisfied.

### M07-T06 — Final eligibility, first-channel exposure and legacy transaction compatibility

- Strengthen the trusted Tower final-gate assembler/writer to require explicit exact-candidate build/publication, runtime/isolation, current-baseline state round-trip, fixed-policy real Muse and non-inference Codex evidence. Bind relevant policy/bundle/configuration/guard inputs. Reject generic GREEN, fixture mode, absent checks, stale baseline and reports for another digest.
- Separate expected registry channel state from running production predecessor identity. Existing-channel update uses exact prior alias observation; first-channel creation requires verified HTTP 404/absence under the same writer lock. Auth/network/permission errors are not absence, and any channel appearance/change before the write invalidates the attempt.
- Both create and update paths enforce final real gates and exact armed guard before write and read back the resulting OCI digest afterward. Test against disposable aliases only before M08.
- Normalize first-cutover identity using explicit bounded representation/mapping in the existing guard/ledger/adapter surfaces: new accepted candidates are OCI identities; the original legacy predecessor may be represented as a verified local image-ID plus independently recoverable archive/configuration anchor. Never use that ID as a registry manifest digest. Verify imported/recovered image identity and representative state before relying on it. Do not publish a legacy image merely to manufacture a registry identity.
- Prove current plus two previous known-good retention and coherent migration of existing records without a second ledger. Unknown/multiple/wrong repository/manifest-to-image mappings fail closed.
- Package/read back the selected single Unraid Update + Verify action with fixed bounded target, probes and restore configuration. It validates the guard before triggering and owns observation/acceptance. Prove crash-safe trigger intent/readback so helper restart cannot blindly reissue an uncertain update; a narrow guard-local effect record is sufficient, not a universal action ledger.
- Required fixtures/disposable tests: absent-channel positive case; channel race; missing real/profile/round-trip gate; wrong config/bundle; legacy predecessor observation/restore; candidate OCI/local mapping; missing-container window; ambiguous third identity; helper interruption before/after trigger; immediate RED recovery; terminal GREEN disables rollback. Never restart the production container or Docker engine for a test.

Exit: final gate, first-exposure and transaction compatibility are independently GREEN mechanically; no production arm/tag/cutover occurs.

### M07-T07 — Fresh exact artifact, autonomous rehearsal and R2 release readiness

- Freeze the repaired source, component resolution and delivery bundle; create a new GitHub-hosted tested image and publish the exact preserved artifact once. Read back the immutable digest and retain exact positive terminal Actions/artifact/source evidence. Queued/skipped/cancelled/failed runs are not success.
- If ordinary default-branch automation is not yet available before scope completion, use one bounded secret-free P4 bootstrap: exact `automation/paseo-update-candidate-p4-bootstrap -> feat/paseo-update-distribution` pair, parent bound to one frozen source SHA/ref, and only the two standard handoff files under `candidates/paseo-update/`. Reuse the normal build/package/publish implementation; temporary allowances cannot accept arbitrary heads/bases or change production permissions.
- Capture the tested-image/artifact/digest before removing the temporary bootstrap allowance and read back bootstrap PR/ref cleanup. Return durable workflows to default-branch-only operation before M08. Reverify cleanup-affected topology; if cleanup changes image/bundle build inputs, rebuild/test/publish a new exact artifact instead of reusing the old digest. This exception is not a new routine updater.
- Rehearse the refreshed source's pipeline against disposable Tower state and fake provider credentials only: core runtime, ownership/mount/network isolation, guarded launch/profile rejection, non-inference Codex fixtures, actual-baseline -> candidate -> candidate-modified state -> predecessor, gate/guard simulation and non-production promotion/Update + Verify.
- Re-run the affected failure/race matrix and full synthetic suite with explicit no-inference classification. Verify the new candidate/predecessor/configuration/rollback anchor and required policy/bundle identities. Real credentials, real inference, production guard arm and production accepted-channel writes remain deferred.
- Old draft PR #19/artifacts may be reconciled as obsolete candidate bookkeeping only after their exact identity/effect/history is read back; they cannot supply P4's new source evidence. Do not merge it blindly or close Issue #6 before scope completion.

Exit: fresh R2 autonomous readiness is independently GREEN, all independent mechanics complete, exact artifact/anchors available, production unchanged. Only now request missing dedicated operator credential/account inputs.

## 5. M08 — Final human inputs and exact production proof

### M08-T01 — Dedicated credential admission and final Tower validation

Refine the existing unstarted Card under approved P4 rather than launching its stale P3/Codex-inference contract. Require M07-T07's exact DONE result and all dependent readiness evidence.

- Reread current candidate/bundle and baseline eligibility. Ask only for genuinely missing dedicated test credential/account input through an approved private local procedure; never request raw credentials in chat or repurpose normal agent credentials.
- Admit credentials only into the isolated disposable candidate. Run one bounded real test through the guarded fixed Muse path with verified daemon/Pi/profile provenance; perform the required authenticated Codex-LB checks without inference against that same validation context.
- Preserve only secret-safe exact-digest/policy/profile/binding/outcome evidence. On timeout/unknown occurrence, read back the exact test object before considering retry; do not resend prompts blindly.
- Fixture-only, missing, failed, wrong-profile or wrong-candidate observations leave the gate unsatisfied and production unchanged. Profile unavailability is blocked, not a model-selection problem to solve by fallback.

Exit: PUD-REQ-020/021 final validation evidence and REQUIRED independent review are GREEN. No production arm or channel movement yet.

### M08-T02 — Final revalidation and transaction-guard pre-arm

- Refresh target compatibility and exact running predecessor, relevant persistent-state/configuration/secret-reference bindings, ledger and independently retrievable rollback anchor.
- Re-run only gates invalidated since M07/M08-T01; a changed candidate or relevant bundle/baseline invalidates mismatched evidence and requires fresh artifact/affected verification, not a tag-based substitution.
- Arm/read back the durable guard for the exact eligible candidate, explicitly typed predecessor, configuration and rollback anchor. Verify actual restore inputs and installed Update + Verify/probe surface without triggering it.

Exit: eligibility plus exact armed guard are independently GREEN. Any missing/mismatch keeps production `:accepted` unchanged.

### M08-T03 — First or subsequent accepted-channel exposure

- Under the trusted Tower single-writer lock, require exact M08-T01 final validation and M08-T02 guard evidence; reread both production baseline and expected alias state immediately before write.
- Create `:accepted` only after verified absence, or update only from the exact expected existing digest. Read back candidate OCI digest and verify Unraid's update-ready/configuration surface selects this same artifact.
- Expose the selected Update + Verify action; do not change production template/entrypoint/HOME in a way that triggers immediate recreation merely to signal readiness. Record any necessary transactional configuration change for the later user-chosen cutover.

Exit: exact candidate is update-ready; production remains on its predecessor and guard remains armed while the user chooses the cutover time.

### M08-T04 — User-triggered Update + Verify transaction

- Immediately before the user action, reread eligibility, accepted-channel digest and exact guard/baseline/configuration/anchor binding. A superseding candidate or mismatch blocks the action.
- The user deliberately chooses the time and invokes the selected single Unraid action. Its fixed trigger and local deterministic core checks own one bounded transaction; do not invent another real inference on the production acceptance path.
- GREEN commits/rotates the coherent known-good set. Immediate RED restores only the protected exact predecessor and verifies recovery with the local probes. Unknown trigger/restore occurrence requires exact readback, not a second blind action.
- Preserve valid user/session/pairing state; destructive HOME restore or separately gated recovery cannot be authorized by the automatic rollback path.

Exit: candidate immediate acceptance or verified predecessor recovery is durable; no claim of successful rollout on RED. REQUIRED independent review covers the exact transaction result.

### M08-T05 — Post-acceptance readback

Prove ordinary Paseo/Pi operation through bounded non-inference/local readback, exact committed image/configuration/ledger and inactive automatic rollback authority. Clean only verified temporary validation fixtures/objects; retain approved private test-secret provisioning for future automated validation. Unexpected rollback on a later unrelated fault must be rejected. No new dashboard or unattended restart.

Exit: production proof under R2 is independently GREEN; later runtime faults cannot autonomously undo accepted work.

## 6. M09 — Operationalization and Close readiness

- **M09-T01 Operational docs and obsolete-path retirement:** finalize daily discovery, managed add/remove, fixed policy delivery, dedicated credential procedures, exact candidate/Tower validation, first/subsequent accepted exposure, selected Update + Verify, ledger/rollback and irreversible-migration exception. Retire legacy Git/Compose/feature-card paths from normal operations without deleting recovery tooling/evidence. Explain fixture versus real gates and uncertainty readback.
- **M09-T02 Ordinary repeatability:** prove default-branch scheduled/manual workflow reachability, no-change no-op, independently failing component holdback, and transactional managed-component add/remove enrollment with a bounded fixture/non-production example. No unnecessary real inference or new capability adoption. Bootstrap exceptions must be absent; preserve only appropriate artifacts/rollback history.
- **M09-T03 Integrated requirement coverage and Close refresh:** reconcile all PUD-REQ-001..033 with exact original/revalidated/new results; review covered behavior against the latest target and run affected compatibility verification. Preserve every recovery artifact and immutable review/result before final integration.

Close owns the final default-branch scope-completing PR, racing target reread, merge/effect readback, target-side recovery package and Issue #6 lifecycle. Default-branch schedule proof that can only occur after integration is an explicitly remaining Close obligation: preserve its pre-integration contract/test evidence, perform exact post-merge readback/verification, and do not claim end of scope until it is durable. Issue closing linkage belongs only to accepted scope completion; if post-merge proof is not yet complete, keep linkage reference-only and reconcile closure afterward. Source cleanup never recreates a branch GitHub already removed.

Unrelated open issues/repair branches, scheduled Appdata Backup repair, Orchestration Runtime integration and future PW extension release/bootstrap remain outside P4. The existing backup degradation is not relabeled GREEN.

## 7. Requirement coverage and gates

| Requirements | Retained owner/evidence | P4 refresh/final owner |
|---|---|---|
| PUD-REQ-001..003 | M01 registry, M02 discovery, M03 topology | M07-T04/T07; M09-T02/T03; post-merge schedule proof |
| PUD-REQ-004..010 | M02 frozen resolution/narrow search/holdback | M07-T04/T07 affected regression; M09-T02 |
| PUD-REQ-011..016 | M01 transactional lifecycle, M02 default classes | M07-T04 delivery/drift; M09-T01/T02/T03 |
| PUD-REQ-017..018 | M03 build-once/publication | M07-T07 exact new artifact and bootstrap cleanup |
| PUD-REQ-019 | M05 promotion writer | M07-T06; M08-T02/T03 |
| PUD-REQ-020..021 | M04 isolation/fixtures only; R2 authority | M07-T04/T05/T07 machinery; M08-T01 exact real/non-inference evidence |
| PUD-REQ-022..023 | M02 major-version policy, M03 core smoke | M07-T04/T07 exact candidate regression |
| PUD-REQ-024..025 | M05 signaling, M06 selected fallback | M07-T06; M08-T03/T04; M09-T01 |
| PUD-REQ-026..029 | M05 ledger, M06 guard/acceptance | M07-T06/T07; M08-T02..T05 |
| PUD-REQ-030..032 | M04 state clone, M07 rehearsal | M07-T07 actual-baseline proof; M08-T02 refresh; M09-T01 exception docs |
| PUD-REQ-033 | Existing minimal Unraid surface | M07-T06; M09-T01/T03 |

Inherited non-conflicting security/ownership/persistence/Relay/instruction/control-plane requirements receive selective compatibility verification where touched. Preserve accepted target repairs and their packages; do not replay completed bootstrap/Paseo bring-up or adopt PGR's superseded Tower-build/all-component-search policy.

Gates:
- **G-P4-1 Baseline:** M07-T04 exact target preservation/reproducible policy GREEN.
- **G-P4-2 Mechanics:** M07-T05/T06 guarded validation, final-gate/first-exposure/identity/action fixtures GREEN; no real credentials/inference or production mutation.
- **G-P4-3 Autonomous readiness:** M07-T07 new tested/published OCI artifact, fixture rehearsal, representative round trip and cleanup GREEN; production unchanged.
- **G-P4-4 Real validation:** M08-T01 dedicated-credential candidate-bound Muse and non-inference Codex checks GREEN under required review.
- **G-P4-5 Pre-arm:** M08-T02 refreshed eligibility and exact durable guard GREEN before channel visibility.
- **G-P4-6 Exposure:** M08-T03 serialized alias create/update/readback GREEN; no cutover.
- **G-P4-7 User transaction:** M08-T04 user action with immediate GREEN or verified RED recovery; M08-T05 proves committed operation and cessation of rollback.
- **G-P4-8 Close:** M09 and post-integration obligations durably covered; no false completion from an empty Card queue.

All security/credential/provenance, exact artifact, promotion/guard/rollback, live acceptance and final coverage Cards require independent implementation review. Planner completeness GREEN is not that review or Stage-6 verdict.

## 8. Execution Prep / JIT and failure classification

After P4 review approval and C, deterministic next useful preparation is M07-T04, using current target authority and the exact DONE M07-T03 dependency. Keep M08-T01 `planned` and non-executable until its revised contract and prerequisite evidence exist; preserve all existing DONE Cards. Add successor Cards only when exact predecessor results make them knowable, with waiting JIT triggers otherwise. No new Cards or technical contracts are authored during Planning.

JIT may settle supported provider secret shape, approved-source pin, candidate-local daemon routing/inspection, companion-bundle representation, narrow evidence/schema binding, typed legacy mapping, fixed Unraid action transport, and local fixture/probe commands. A separate selective technical contract is justified only for genuine cross-component validation/gate/security detail, not a universal schema/framework.

Missing agent-findable facts route proportional Research. Missing dedicated credential/profile/access is a concrete input/runtime blocker, not approval to use ordinary credentials or another model. Milestone/outcome/order/topology changes return to Planning; accepted product/global intent changes return to Definition. Unsupported fixed-bootstrap provenance or an unrepresentable safe rollback path cannot be repaired by inventing another publication/deployment mechanism.

No plan/code cleanup may silently waive a gate, rewrite an in-progress Card, mutate failed review history, create a second Task Board/approval store or move workflow authority into runtime labels/session metadata.

## 9. Planner challenge audit

Planner completeness/challenge: **GREEN**, recorded separately in `planning/audits/PASEO_UPDATE_DISTRIBUTION_P4.md`.

The audit challenges exact-candidate/profile/secret isolation, stale-main regression, fake final GREEN, absent first channel, OCI/local identity ambiguity, selected fallback and crash uncertainty, build-once/bootstrap cleanup, state/rollback proof, user timing and all 33 requirement owners. It establishes strategy completeness only. P4 is frozen for fresh independent Stage-6 review; no implementation, real test, production eligibility or deployment completion is claimed.
