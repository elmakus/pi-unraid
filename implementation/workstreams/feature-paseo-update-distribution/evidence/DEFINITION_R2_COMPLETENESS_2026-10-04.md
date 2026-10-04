# Definition R2 completeness audit

Date: 2026-10-04
Workstream: `feature-paseo-update-distribution`
Promoted subject: `paseo-update-distribution@11`
Definition: `R2`
Outcome: **GREEN — product/acceptance authority complete; premium A due**

## Exact bounded authority

The R11 user-authorized correction is durably reconciled at commit `2dc251e08d2a6e01374351a9afb4ce77e8a20d2f`; the exact re-entry evidence blob is `98baf4c422e779d603ec9e53af51fbf905a6dbdd`.

Requirements R2 retain PUD-REQ-001..033. Only PUD-REQ-020/021 are substantively amended: exact-candidate guarded real Muse validation plus authenticated non-inference Codex-LB checks, with dedicated validation credential isolation. ADR-PUD-004 explicitly supersedes the prior conflicting smoke-provider/model provisions; ADR-PUD-003 R2 updates only its validation clause. The distribution/cutover, managed lifecycle, compatibility, immutable artifact and rollback decisions otherwise remain unchanged.

The accepted test invariant consumes the mandatory environment policy: `meta/muse-spark-1.3-contributor`, thinking/contribution `max`, guarded launcher, no fallback. This is not workflow role selection or interactive model policy. The CLI and validated native argument shapes are allowed mechanisms, not evidence that a particular candidate has been tested.

## Completeness challenge

- **Exact candidate:** inference must exercise the immutable disposable candidate's own Paseo/Pi/provider path. Production-runtime or unrelated child inference, launcher metadata and fixture-only evidence cannot satisfy it.
- **Policy delivery:** candidate policy and guard must be reproducible and must not regress to an older profile/bypass. Changed candidate content requires a new immutable build identity and appropriate exact-gate verification.
- **Credentials:** dedicated operator-controlled validation credentials only; no ordinary-agent credentials supplied to the update pipeline; no credentials in CI, images, Git, logs or evidence. Missing inputs remain blockers.
- **Codex-LB:** authenticated catalog/metadata/auth/health readback and deterministic fixtures only. No prompt or inference endpoint is used. Invalid/unreachable required observations are not GREEN.
- **Production:** validation GREEN precedes exact guard arm/readback, which precedes accepted-channel exposure, which precedes user-selected cutover. Scope approval is not permission to restart.
- **Rollback:** representative direct A -> C -> A proof, predecessor/configuration/anchor binding, current plus two previous known-good identities, immediate RED recovery and post-GREEN cessation remain required.
- **No invented success:** historical P3/M01-M07 GREEN subjects remain unchanged. The changed real-smoke acceptance is not covered by them and M08-T01 has no implementation result.

No unresolved product choice remains inside this bounded amendment. Candidate-bound guarded invocation realization, dedicated credential admission, fixed-profile runtime availability, selective revalidation and actual smoke evidence are downstream implementation/technical inputs, not waived obligations. They must be researched/refined proportionally if missing, and fail closed if unavailable.

## Planning and history reconciliation

This is material acceptance/strategy change, not an editorial correction. Cycle 4 / P4 is materialized only as gate metadata: draft, audit pending, exact re-entry subject above, premium A due, B/C not due and no frozen subject. No P4 strategy or plan artifact has been authored before A.

The original approved P3 planning state is recoverable at `21e586101bf6cb096c6024e64c9f16efa91fb4e2:implementation/workstreams/feature-paseo-update-distribution/PLANNING.toml`. The frozen P3 plan and its GREEN Stage-6 subject remain at commit `88feb2ba8d9f2b18ac58b9c57a465759277efa60`, blob `043ad95bf300dee7c0289f44fc6547684f82b664`. The existing P3 `PLAN_REVIEW.toml` and review evidence remain unchanged as historical records; the manifest no longer selects that attempt as review authority for P4. A fresh exact P4 review attempt can be materialized only after its own freeze and premium B boundary.

The prior human-authority question is resolved, so the unstarted M08-T01 Card is returned to `planned` and its blocker locator is removed. The original valid blocker file is retained unselected as historical evidence, byte-identical to its state at `21e586101bf6cb096c6024e64c9f16efa91fb4e2`. Planning/Definition execution-resolution classes are not valid durable blocker classes; no new blocker type or workflow schema is introduced. The Card is not READY and its old P3-bound contract must be refined only after approved replacement planning authority and premium C.

The next canonical real stop is premium A for R2 / the cycle-4 planning entry. Staying in the current best-available planning context is allowed, but old A/B/C satisfaction and the R11 scope approval do not satisfy the new gates.

## Verification / mutation boundary

The mandatory launcher argument validation was performed without inference and returned the fixed native profile/contribution with completion notification. No real LLM test, worker invocation, smoke implementation, secret admission, host mutation, candidate deployment, production guard arm, accepted-channel write, restart, cutover or rollback was performed by this Definition amendment.

Verification is PASS for Definition/Planning/Board and retained blocker schemas, exact R11 and immutable re-entry binding, existence of authority locators, all 33 stable requirement IDs with exactly PUD-REQ-020/021 amended, unchanged historical P3 plan/review/blocker, and canonical `stop / premium_A / R2` with optional handoff. A synthetic in-memory gate-satisfaction check routes to Planning, without changing durable A states or authoring P4. `git diff --check` is GREEN. This audit does not claim implementation or production acceptance.
