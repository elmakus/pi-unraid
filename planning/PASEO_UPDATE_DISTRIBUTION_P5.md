# Paseo/Pi Update Distribution — Strategic Plan P5

Plan revision: P5
Planning cycle: 5
Status: frozen for Premium B / independent Plan Review; not approved for execution
Definition: R3 / paseo-update-distribution@12
Workstream: feature-paseo-update-distribution
Branch: feat/paseo-update-distribution
Review mode: independent
Date: 2026-10-08
Entry subject: `elmakus/pi-unraid@6912aee2231386123d05b14d7e3b8a9608abee32:implementation/workstreams/feature-paseo-update-distribution/evidence/DEFINITION_R3_METADATA_POLICY_2026-10-08.md@f31c9fa8f463bf8fa865bb0579e6b01195487863`

## 1. Authority, objective and scope

Complete the existing updater with proportionate metadata validation, not a Paseo fork: metadata notification/ctime change alone is not a rejection when protected observed file identity, content, owner and private mode remain valid. Explicitly accept that transient metadata mutation-and-restore between observations may escape detection. Never claim equivalence to the old blanket metadata tripwire.

Authority is Requirements R3, ADR-PUD-001..005, especially ADR-PUD-005 for this amendment and ADR-PUD-004 for unchanged guarded Muse/max and non-inference Codex-LB validation. Inherited non-conflicting GUI-runtime authority remains applicable. P5 materially replaces the remaining P4 strategy; it is not an editorial exemption. Cycle-5 premium A is satisfied by the user's explicit instruction to continue planning here after the R3 gate. Cycle-4 review/gates do not authorize this subject.

The exact historical P4 plan remains available at `6912aee2231386123d05b14d7e3b8a9608abee32:planning/PASEO_UPDATE_DISTRIBUTION_P4.md`. P5 retains its unaffected discovery, managed inventory, narrow compatibility search, distribution, ledger, transaction, credential admission and Close strategy as restated below. Its metadata assumption and autonomous readiness are superseded. No historical DONE Card/result/review is rewritten.

Sequence: approved P5 and C -> Main Execution Prep refresh of blocked M07-T07 -> local fake-only R3 interval implementation and independent-ready regressions -> one fresh frozen GitHub build/test/preserved-image publication -> exact disposable Tower rehearsal and full readiness -> required independent implementation review -> M08 dedicated inputs/real final validation -> guard -> accepted-channel exposure -> user-triggered Update + Verify -> operationalization/Close.

## 2. Recovered state and evidence limits

Task Board revision 135 preserves DONE M01-T01 through M07-T06 including M07-T05A; M07-T07 is blocked without a semantic result, M08-T01 is planned. Human policy choice is now resolved by R3, but its Card remains non-executable until approved replacement Planning and Prep reconcile the blocker and acceptance. Do not treat the old blocker as permission to resume P4.

Old tested/published candidate f5f52337 / OCI aa7425c8 / local aa4c522e and PR25/run37684609105 are historical exact R2 evidence, not R3 eligibility. Evidence ev2..ev6 identifies repeated unconditional upstream chmod of config.json, failed blanket interval, existing observer limitations, no supported compatible release/option and no suitable arbitrary holdback. Another same-source retry cannot fix it. 50131ab and 8144bda had identical tracked trees; full737 positive and one witness-control failure plus focused reruns remain classified historical tests, not proof of R3 behavior.

Current component versions, source/target, production predecessor, legacy archive/config anchors, guard/channel and full digests must be freshly read before affected operations. Short historical hashes are explanatory only, never mutable pins. No live production change or new test inference has been authorized by planning.

## 3. R3 implementation strategy inside refreshed M07-T07

### 3.1 Main-owned preparation and bounded correction

After exact independent Plan Review GREEN is consumed and premium C satisfied, Main refreshes the active M07-T07 Card under R3/P5, keeping its identity and historical evidence. Explicitly include applied-interval correction, contract/documentation reconciliation, consumer regression and fresh exact artifact/rehearsal; exclude forks/upstream patches, credential/inference/production effects, arbitrary version pin and new privileged monitoring. Resolve the existing human-authority blocker in the same canonical transition; do not launch the stale Card. Preserve original blocker history through Git.

Consume exact reviewed DONE dependency subjects and the ev2..ev6 diagnosis. Existing DONE semantics are historical mechanism inputs; changed behavior needs new evidence. Update the selective validation contract to cite R3/ADR-PUD-005 during execution, not by silently editing old results. Do not create a parallel approval/queue store. Execution Prep owns exact dependency locators and any necessary JIT refinement; this plan creates no Task Cards.

### 3.2 Semantic identity, event handling and bounded observation

Use the existing Linux inotify + private Unix-peer interval mechanism. No fanotify/audit/eBPF, PID-based trust, public caller flags or polling-only replacement is introduced.

Separate notification metadata from protected semantic identity. At acquisition, metadata event processing, existing preflight/dispatch/completion checkpoints and terminal verification, verify the expected file set, regular-file/non-symlink topology, retained device/inode identity, content and relevant owner/group/mode constraints. Credentials/manifest/config remain private and owned; derived models.json retains existing 0600 and source/effective identity binding. Frozen companion declared content/mode must still match actual bytes. Extend any missing required owner/group observations coherently rather than claiming they already exist.

ctime alone is no longer a semantic mismatch. An attributable-to-watched-path IN_ATTRIB notification requests synchronous revalidation of the protected observed properties, not proof of a benign syscall or actor. Tolerate metadata notifications only when revalidation succeeds; mixed events containing a disallowed content/identity event remain terminal. Event counts or cookies cannot prove that a notification was a same-mode chmod; no such claim is made.

Content writes, including writes that restore original bytes, replacement/deletion/move/unmount, lost watch, malformed event stream and overflow remain irreversibly invalidating for relevant protected paths. Keep parent-watch path filtering precise: unrelated sibling activity is not a mutation of the protected input; protected parent/root identity and required watches must remain valid. No blanket clearing of event masks or exception suppression.

Stable-read checks must use semantic before/after identity plus actual content validation and pending event accounting. A metadata-only race may use a bounded revalidation strategy consistent with the accepted limitation; exhaustion/ambiguous read/failure remains unsatisfied. Do not simply delete ctime checks everywhere and call safety proven. Retain exact source-frozen bootstrap expectations, private input rules, peer/process/reference binding and all interval boundary call sites. Observed meaningful delta is terminal even if a later read sees restored state. The accepted blind spot is only a metadata change-and-restore entirely between observations, not observed changes or content events.

### 3.3 Tests before external build effects

Run focused fake-only reachable interval/adapter/validator tests on an immutable legal worktree with isolated HOME/cache/bytecode controls. Positive controls: same-mode config chmod at daemon bring-up and repeatedly between checkpoints; metadata notifications with unchanged protected properties; exact companion/derived-file binding through final observation; no inference and fixture never real eligibility.

Negative controls: actual observed mode, owner/group or identity delta; content mutation-and-restore; replacement/symlink/unlink; companion add/remove and mode/content drift; manifest/config modification; mixed ATTRIB+MODIFY; watcher loss/overflow/read failure; initial/read-boundary races and terminal callback mutations. Exercise all existing interval checkpoints, not only helper snapshots. Explicitly document indistinguishable metadata-ABA as accepted limitation rather than fabricate a negative-test guarantee. Retain guard/profile/source/daemon/Pi/secret and detached-forgery negatives.

Refresh affected delivery/build-binding, effective config, owned runtime, genuine validator/assembler/writer, first-channel404 versus auth/network, typed legacy/OCI/local, ledger and trigger/restore regressions. Use direct exit codes, full logs, executed/skipped accounting, Node/syntax/diff and secret scans. Run full synthetic discovery once meaningful focused checks pass on fixed immutable source outside system temp where repo-location tests require it. Any residual failure needs concrete attribution and a reachable control; targeted rerun alone is not blanket permission to ignore it. No commits/source mutation inside a running test's source tree, duplicate suites, blind external retries or sleep/poll loops.

Exit: locally demonstrated R3 behavior and classified full synthetic evidence, not independent acceptance or permission for live inference.

## 4. Fresh artifact, autonomous rehearsal and independent readiness

Changing config/pi-agent/bin/m07-t05-applied.py changes the managed companion itself, and adapter/validator changes affect validation_sources. Recompute the installer-derived file set/modes/content, effective models config, policy/launcher, relevant validation-source hashes and candidate/build/source identity; never attach R3 validation to aa7425c8 or any older artifact. Refresh stable components using the existing resolver without arbitrary pins/new gates.

Use normal GitHub-hosted build/package/publish: one frozen build, exact-image mechanical smokes, preserved tested bytes and publication of those bytes to GHCR, then immutable OCI and local/platform identity readback. Require positive terminal exact-source CI/artifact evidence, full hashes/IDs and secret-free durable logs; queued/skipped/cancelled/failed is not accepted.

Where default-branch automation is not yet reachable, retain only the previously approved exact bootstrap pair `automation/paseo-update-candidate-p4-bootstrap -> feat/paseo-update-distribution`, one frozen source parent/ref and exactly two standard handoff files under candidates/paseo-update. Its historical p4 name does not authorize broader behavior. Temporary allowances reuse the existing pipeline, not a second updater. Read exact remote PR/ref/history before effects, capture artifact/digest before close-without-merge/ref deletion, restore default-branch-only topology and verify cleanup. Compare ALL frozen build and validation inputs after cleanup; any changed input invalidates reuse and requires appropriate new build/evidence. Do not waive binding because image bytes appear unchanged.

Rehearse on owned disposable Tower with fake dedicated inputs only, correct CLI and all frozen evidence/companion wiring. Prove semantic interval survives actual unmodified Paseo repeated normalization while its content/identity/owner/mode negative controls still reject. A generic structural FAIL or 18/19 count is not readiness. All applicable synthetic structural/source/runtime/isolation/config/non-inference fixture gates must complete successfully; real_validation_satisfied remains false. Do not exercise real provider endpoints or claim real eligibility.

Prove actual-baseline sanitized isolated clone -> exact new candidate -> modified representative state -> actual predecessor reopen; no ordinary credentials/live HOME reach candidate. Nonproduction promotion must move actual candidate bytes and read back their typed digest. Execute selected shipped Update + Verify on disposable deployment/anchors: immediate GREEN, actual bound predecessor restore+verification on RED, interruption/unknown readback/no reissue and post-GREEN denial. Retain source/harness/commands, full outputs, guard/anchor and cleanup ownership evidence, not narrative-only image-inspect substitutes. Candidate never receives host administration key or production Docker socket.

Required independent implementation Review covers the complete refreshed M07-T07 result, R3 changes, exact new artifact, synthetic regressions, rehearsal and cleanup. Fresh reviewer must not be its producer/repairer. Main reconciles result and review and continues until a real boundary; child idle is not completion. Production image/config/guard/channel remain unchanged throughout. Only independently GREEN DONE readiness can unlock M08-T01.

## 5. Retained downstream M08/M09 and Close

M08-T01: refresh exact candidate/bundle/baseline; ask only for genuinely missing dedicated operator-controlled validation inputs using private approved provisioning, never tokens in chat or ordinary agent credential copies. Run candidate-local guarded meta/muse-spark-1.3-contributor/max with effective daemon/Pi/profile/child provenance and no fallback; authenticated Codex-LB catalog/auth/health without inference. All real LLM tests use the mandatory launcher or its unchanged validated native args; candidate health/catalog/synthetic controls are not inference. Timeout/unknown occurrence uses owned-object readback before retry. Required independent review; no production effects yet.

M08-T02: refresh eligibility, relevant state/config, typed production predecessor, current-plus-two-previous ledger and independently recoverable rollback anchors. Changed candidate/bundle/baseline invalidates affected evidence. Arm/read back exact durable transaction guard only after real final validation/review. No trigger.

M08-T03: trusted acquisition-owned single writer, same lock, verified404 absence or exact expected prior accepted alias, refreshed baseline and armed guard; publish/read back accepted OCI and Unraid readiness without recreating production. Auth/network failure is not absence. No fixture or caller-composed gate eligibility.

M08-T04: user chooses cutover and explicitly invokes fixed single Update + Verify. Read current eligibility/guard/channel immediately before action; immediate deterministic GREEN commits ledger, RED restores exact predecessor and verifies recovery. Unknown trigger/restore readback before any reissue. No extra production LLM smoke, unattended restart or destructive HOME restore. Required independent transaction review.

M08-T05: bounded non-inference committed image/config/state/ledger/ordinary operation readback; later unrelated failures cannot roll back after GREEN. Clean only verified owned temporary objects.

M09-T01..T03: document daily default-branch discovery, registry/install-intent managed add/remove, exact frozen/preserved-artifact flow, R3 metadata limitation, dedicated-secret procedure, first/subsequent exposure, rollback ledger and irreversible migration exception. Prove no-change no-op, independent component holdback, safe enrollment and default-branch repeatability; bootstrap absent. Reconcile all requirements against exact unchanged/revalidated/new results.

Close owns final target refresh, integration PR/merge readback, target-side durable recovery, post-merge default-branch schedule proof and Issue6 closure only after approved scope completion. Pre-integration tests cannot manufacture post-merge schedule proof. Do not recreate deleted source branches. Preserve unrelated repairs/backup degradation; Orchestration Runtime, notifyOnFinish runtime repair, dashboards, DockerMan patches and other host changes remain out of scope.

## 6. Coverage and gates

| Authority | Retained mechanism | P5 evidence owner |
|---|---|---|
| PUD-REQ-001..003 | M01/M02 registry/discovery | M07-T07 compatibility, M09 repeatability, Close schedule |
| PUD-REQ-004..010 | frozen narrow Paseo/Pi resolver and independent tools | M07-T07 refreshed candidate/regression, M09 |
| PUD-REQ-011..016 | managed registry/install atomic membership | affected delivery/drift regression, M09 lifecycle |
| PUD-REQ-017..018 | normal GitHub preserved-image publication | fresh M07-T07 exact artifact and cleanup |
| PUD-REQ-019 | acquisition-owned serialized writer | M07-T07 negatives/disposable promotion, M08-T03 |
| PUD-REQ-020..021 + ADR004 | dedicated exact-candidate guarded Muse/non-inference Codex | M07-T07 machinery only; M08-T01 real evidence/review |
| PUD-REQ-022..023 | core smoke/stable-major policy | M07-T07 exact image and full regressions |
| PUD-REQ-024..025 | user timing/selected Update + Verify | M07-T07 disposable action, M08-T03/T04 |
| PUD-REQ-026..029 | typed guard/ledger/immediate recovery | M07-T07 controls, M08-T02..T05 |
| PUD-REQ-030..032 | sanitized direct A-C-A/skip/irreversible exclusion | new M07-T07 actual-baseline proof, M08 refresh, M09 docs |
| PUD-REQ-033 | minimal existing Unraid UX | unchanged, M09 coverage |
| R3 + ADR005 | explicit proportionate metadata semantics and limitation | refreshed M07-T07 implementation/tests/review, M08 effective validation, M09 docs |

Gate chain: G5-1 P5 independent approval+C -> G5-2 refreshed Card/local R3 regression -> G5-3 fresh exact artifact+complete autonomous rehearsal+independent M07-T07 GREEN -> G5-4 reviewed exact real validation -> G5-5 refreshed armed guard -> G5-6 serialized accepted exposure -> G5-7 explicit user transaction and independent verification -> G5-8 operationalization, integration/post-merge proof and completed scope. No gate is satisfied merely by this plan or its audit.

## 7. Planner challenge and continuation

Planner audit is GREEN in planning/audits/PASEO_UPDATE_DISTRIBUTION_P5.md. Challenges cover benign repeated normalization, honest metadata-ABA limitation, retained harmful event detection, stable reads/owner/group consistency, source/bundle/consumer propagation, fake versus real, exact artifact/bootstrap cleanup, actual rollback, residual test classification and all33 requirement groups.

No task/technical contract mutation, implementation, real test, production change or Plan Review verdict is performed during planning. Missing facts route proportional Research; R3 ambiguity returns Definition; strategy/order changes return Planning; actual operator gates remain user stops. P5 freezes one exact immutable blob and stops at premium B for a fresh independent Main context; planning Main must not review its own plan or spawn a child reviewer. After GREEN review consumption/C, Main owns Prep/reconciliation and continues deterministic obligations. Runtime scheduling/subscription labels are never workflow authority.
