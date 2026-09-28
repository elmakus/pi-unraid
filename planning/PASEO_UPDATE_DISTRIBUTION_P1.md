# Paseo/Pi Update Distribution — Strategic Plan P1

Plan revision: P1  
Planning cycle: 1  
Status: frozen (pending Premium B independent review)  
Definition: R1 / paseo-update-distribution@10  
Workstream: feature-paseo-update-distribution  
Branch: feat/paseo-update-distribution  
Review mode: independent  
Date: 2026-09-28  
Entry subject: `elmakus/pi-unraid@a69c20d093f255a1fb4335175631c3bd1da8587a:implementation/workstreams/feature-paseo-update-distribution/DEFINITION.toml@84c80268d4900cf8c3d3b9bfc22031a2a1736956`

## 1. Planning objective

Implement the approved update-distribution system without reopening product decisions:

daily discovery -> frozen candidate -> bounded resolution -> GitHub-hosted build/test -> immutable GHCR digest -> Tower-specific validation -> serialized accepted channel -> user-triggered Unraid cutover -> immediate acceptance or automatic rollback.

Human presence is intentionally deferred to the final production-acceptance wave. All infrastructure, failure injection, disposable state-transition proof, DockerMan integration proof and secret plumbing must be complete before asking the user to provide the dedicated Codex-LB key or click Update.

Binding authority:
- `requirements/PASEO_UPDATE_DISTRIBUTION.md` R1, PUD-REQ-001..033;
- `decisions/ADR_PUD_001_DISTRIBUTION_AND_CUTOVER.md`;
- `decisions/ADR_PUD_002_MANAGED_COMPONENT_LIFECYCLE.md`;
- `decisions/ADR_PUD_003_ROLLBACK_SAFE_PROMOTION.md`;
- inherited non-conflicting Paseo/Pi runtime authority from `requirements/PASEO_GUI_RUNTIME.md` and ADR-PGR-001..004.

## 2. Global planning invariants

1. OCI digest is deployment/rollback identity; tags are signaling aliases only.
2. Build once. GitHub tests, GHCR publication, Tower validation, production promotion and rollback all bind to the same digest.
3. Only Paseo<->Pi participates in compatibility combination search. Node is derived from Paseo.
4. Pi extensions and ordinary developer tools update independently; extension feature failure is not a core compatibility gate.
5. Playwright+Chromium is one derived update unit.
6. Registry membership and durable installation intent change atomically through the agent-operated managed-component helper.
7. GitHub-hosted CI receives no production credentials.
8. Tower validation is narrow, disposable and exact-digest; unaccepted candidate code does not receive production Docker/host authority.
9. No candidate reaches `:accepted` until direct A->C->A state-transition proof passes against a representative clone of the actual current baseline.
10. Production cutover is never triggered merely by update availability.
11. Immediate post-click RED may auto-rollback exactly once; post-GREEN failures never trigger autonomous rollback.
12. Production ledger is current + previous_1 + previous_2. Build/registry retention is a separate concern.
13. Stock DockerMan Update is preferred only if exact installed-version binding is proven. Otherwise use the already-authorized single `Update + Verify` Unraid action.
14. No custom dashboard, universal SAT solver, persistent privileged GitHub runner on Tower or extension compatibility matrix.
15. User-required secret/account interaction and actual production cutover occur only after all technically independent work is GREEN.

## 3. Milestone strategy

### M01 — Managed component registry and agent lifecycle

Goal: make registry membership and installation intent one durable operation.

- **M01-T01 Registry schema/generalization**
  - evolve the existing environment capability/update inventory into explicit managed update membership;
  - preserve capability/readback concerns separately from update metadata where appropriate;
  - represent source kind, stable channel, immutable identity, install class, update class, derived owner and basic probe references;
  - encode current managed components without adding unused apt/pip/cargo adapters.

- **M01-T02 Agent-operated add/remove helper**
  - add one project-owned managed-component add/remove interface for agents;
  - atomic repo mutation of installation intent + registry membership;
  - classes: Pi extension, developer tool, derived component;
  - live-container direct installs remain explicitly temporary.

- **M01-T03 Drift/readback enforcement**
  - tests fail installed-but-unregistered and registered-but-not-installed managed states;
  - prove add/remove round-trip and deterministic registry readback;
  - document agent instruction-plane discovery of the helper.

Exit: PUD-REQ-002..003 and 011..016 GREEN without user presence.

### M02 — Narrow resolver and independent fallback policy

Goal: generalize current resolver while shrinking compatibility combinatorics.

- **M02-T01 Typed discovery/freeze adapters**
  - preserve current provenance checks;
  - implement only current needed source classes: npm, GitHub release/assets, OCI and derived identity;
  - discovery returns normalized stable versions; freeze produces immutable install records.

- **M02-T02 Paseo<->Pi compatibility search**
  - newest-first bounded backtracking only for Paseo/Pi;
  - Node derived from exact Paseo image with Pi floor/range checks;
  - deterministic failure/nogood cache scoped only to proven failing identities/gate fingerprints;
  - infrastructure/transient errors classify BLOCKED, not incompatible.

- **M02-T03 Independent component fallback**
  - SpecPi, pi-mcp-adapter and future ordinary extensions resolve independently;
  - gh/Docker CLI/Compose likewise independent;
  - Playwright+Chromium is one derived unit;
  - implement equal-weight aggregate-lag tie-break for incomparable complete candidates;
  - unchanged candidate is a no-op.

Exit: PUD-REQ-001, 004..010, 016 and 023 GREEN.

### M03 — Default-branch CI, exact build and GHCR publication

Goal: move routine update preparation from historical feature-card workflows to operational default-branch automation.

- **M03-T01 Operational workflow topology**
  - daily schedule plus manual dispatch on default branch;
  - remove stale closed-feature branch triggers from active operational workflows;
  - discovery -> candidate artifact/PR/evidence only on material change;
  - concurrency/serialization prevents stale candidate promotion races.

- **M03-T02 Build-once candidate pipeline**
  - reuse/generalize existing child-image/buildx/smoke assets;
  - deterministic core whole-image smoke;
  - extension/tool install failures can hold back only that component;
  - optional extension feature behavior does not become a blocking matrix.

- **M03-T03 GHCR exact-digest publish**
  - publish the exact tested image, never rebuild for publication;
  - capture/read back OCI digest;
  - candidate-readable immutable alias may exist but digest is authority;
  - publisher has only required GHCR write scope; third-party Actions pinned as appropriate.

Exit: PUD-REQ-017..019, 022..023 GREEN. No production tag movement yet.

### M04 — Tower disposable validator and rollback-state proof

Goal: prove all Tower-specific facts without touching active production.

- **M04-T01 Narrow Tower validator boundary**
  - fixed project-owned validator/dispatcher on Tower rather than persistent privileged public-repo runner;
  - exact-digest pull, UID:GID/mount/network/runtime checks, structured PASS/FAIL/BLOCKED evidence;
  - candidate container receives no production Docker socket/host-control secret.

- **M04-T02 Codex-LB smoke plumbing**
  - implement dedicated secret mount/read path and bounded one-call protocol smoke;
  - tests use a disposable/fake credential fixture until final HA;
  - no normal agent credential enters CI or candidate image;
  - real user-supplied smoke key is deliberately deferred to M07.

- **M04-T03 A->C->A state clone**
  - reuse/extend staged HOME evidence to clone representative current persistent state;
  - prove actual-baseline -> candidate -> candidate-modified state -> previous runtime;
  - direct skip path must be tested against actual current baseline, not only adjacent candidates;
  - irreversible transition is BLOCKED from ordinary channel.

Exit: PUD-REQ-020..021, 030..032 technically implemented with fixture secret and disposable state.

### M05 — Accepted channel, Unraid template and production ledger

Goal: implement update signaling and pre-arm data without performing a real production cutover.

- **M05-T01 Accepted-channel promotion**
  - serialized single writer moves `:accepted` only after exact GitHub+Tower GREEN;
  - immediate registry digest readback;
  - stale/newer-candidate race protection;
  - rollback never resolves the mutable tag.

- **M05-T02 Unraid production template/update-ready path**
  - add/normalize Unraid Docker Template / CA-style configuration following `:accepted`;
  - verify exact installed Unraid/DockerMan version and update-ready digest behavior;
  - no custom dashboard.

- **M05-T03 Known-good ledger and pre-arm contract**
  - durable current/previous_1/previous_2 digest ledger;
  - preserve independently retrievable rollback anchor before candidate visibility/cutover;
  - distinguish production-known-good retention from broader registry/build retention.

Exit: PUD-REQ-019, 024, 026, 029 and 033 infrastructure GREEN.

### M06 — Production transaction guard and DockerMan binding

Goal: prove cutover/rollback mechanics without asking the user to perform the real update.

- **M06-T01 Transaction guard state machine**
  - durable states for armed/observed/validating/committed/rolling-back/recovered;
  - exact candidate/predecessor/config binding;
  - idempotent recovery after helper restart/interruption;
  - events may wake the helper but inspect/readback is authority.

- **M06-T02 Immediate acceptance + failure injection**
  - local core probes only: exact digest, container health, Paseo/Pi RPC/provider path, mounts/ownership and required core invariants;
  - injected RED restores predecessor and verifies recovery;
  - prove rollback authority is disabled after GREEN;
  - transient remote service outages do not become automatic image incompatibility unless explicitly required by candidate contract.

- **M06-T03 Stock DockerMan Update binding spike**
  - against exact installed target version, prove that pre-armed state can bind unambiguously and crash-safely to the stock Update gesture despite DockerMan cleanup/status-cache behavior;
  - if proof fails, implement/test the authorized single `Update + Verify` action instead;
  - do not patch DockerMan core merely to preserve wording.

Exit: PUD-REQ-025..028 GREEN mechanically, with selected production gesture durably determined.

### M07 — Full autonomous pre-production rehearsal

Goal: prove the complete pipeline except the two genuinely human inputs.

- **M07-T01 End-to-end candidate rehearsal**
  - synthetic/new version discovery -> resolver -> frozen candidate -> GitHub build/tests -> GHCR digest -> Tower disposable validator -> A->C->A proof;
  - use fixture Codex-LB secret path, not the user's real key.

- **M07-T02 Failure and race matrix**
  - tag changes/races;
  - unauthorized/wrong digest;
  - same immutable bad candidate does not loop daily;
  - changed relevant fingerprint invalidates stale failure cache;
  - missing GHCR/network recovery behavior follows the explicitly implemented local rollback-anchor contract;
  - helper restart during acceptance;
  - stale DockerMan status cannot masquerade as success.

- **M07-T03 Release readiness**
  - all automatic evidence GREEN;
  - exact production predecessor and rollback anchor available;
  - exact next candidate ready for real Codex-LB smoke;
  - no production restart/tag exposure requiring user action occurs yet.

Exit: technically ready for final human acceptance; all avoidable user interaction has been deferred.

### M08 — Consolidated human acceptance and production proof

Goal: perform only the genuinely human/operator-dependent final steps.

- **M08-T01 Dedicated Codex-LB key admission**
  - user supplies the dedicated API key;
  - store only in approved Tower-local secret location;
  - run one bounded real smoke using server-side operator policy;
  - no key value enters Git/evidence/logs.

- **M08-T02 Final accepted-channel exposure**
  - rerun invalidated final gates only;
  - move `:accepted` to the exact proven digest;
  - verify Unraid shows the update for the exact digest;
  - transaction guard is armed before user cutover.

- **M08-T03 User-triggered production update**
  - user chooses the moment and invokes the proven stock Update path or the previously-selected `Update + Verify` fallback;
  - GREEN path commits new current and rotates current/previous_1/previous_2;
  - if immediate RED occurs, automatic rollback+recovery evidence must complete without requiring a second manual rescue action.

- **M08-T04 Post-acceptance operational proof**
  - confirm Paseo/Pi normal operation after GREEN;
  - prove no automatic rollback remains armed after acceptance;
  - remove temporary HA fixtures/secrets only as appropriate while retaining the user-managed smoke secret for future automated candidate validation if that is the approved operational setup.

Exit: production path operational and ordinary future updates require no user action except choosing when to click Update.

### M09 — Operationalization and close readiness

Goal: leave one maintainable update system, not a mix of historical and current paths.

- retire/mark legacy `scripts/update.sh` and feature-card-only workflow triggers from normal operations while preserving historical evidence;
- keep Compose/staged tooling for development/recovery where useful;
- finalize operational docs for managed add/remove, resolver classes, Tower validator, accepted channel, ledger, rollback and irreversible-migration maintenance exception;
- prove daily no-change is a clean no-op;
- prove a newly managed extension/tool enrolled by the helper automatically enters discovery/update lifecycle;
- perform integrated requirement coverage/readback and prepare Close evidence.

Exit: PUD-REQ-001..033 all covered by durable evidence and no redundant normal production updater remains.

## 4. Requirement coverage

| Requirements | Primary milestone(s) |
|---|---|
| PUD-REQ-001..010 | M01-M02 |
| PUD-REQ-011..016 | M01, M09 |
| PUD-REQ-017..019 | M03, M05 |
| PUD-REQ-020..023 | M03-M04 |
| PUD-REQ-024..029 | M05-M08 |
| PUD-REQ-030..032 | M04, M07-M08 |
| PUD-REQ-033 | M05-M09 |

Inherited non-conflicting PGR security/persistence requirements are regression-checked proportionally where their surfaces are touched rather than replaying the completed Paseo GUI Runtime acceptance suite wholesale.

## 5. Gate strategy

- **G1 Registry integrity:** M01 GREEN before resolver generalization.
- **G2 Resolver correctness:** M02 GREEN before operational candidate automation.
- **G3 Exact artifact:** M03 must produce one tested immutable digest before Tower work can trust a candidate.
- **G4 Tower safety:** M04 validator and state-transition proof GREEN before production signaling exists.
- **G5 Promotion safety:** M05 accepted channel/ledger/pre-arm GREEN before transaction guard production binding.
- **G6 Transaction safety:** M06 injected success/failure/restart cases GREEN before end-to-end rehearsal.
- **G7 Autonomous readiness:** M07 GREEN before any user secret or real production cutover is requested.
- **G8 Human acceptance:** M08 owns the only planned user-presence wave.
- **G9 Close:** M09 proves ordinary repeatability and removes obsolete operational paths.

Critical production mutation, secret handling, GHCR promotion, transaction-guard, rollback and final acceptance Cards require independent implementation review. Pure schema/docs/mechanical test refactors may use proportional review classification at Execution Prep.

## 6. JIT boundaries

Do not guess these details early; Execution Prep resolves them only when their predecessor evidence exists:
- exact installed Unraid/DockerMan integration surface for stock-button observation;
- exact narrow Tower dispatcher transport/forced-command shape;
- exact GHCR package visibility/read credential if the package is private;
- exact real smoke model/quota selected by the user's Codex-LB key policy;
- irreversible future migration procedure, which is outside ordinary update flow until such a release exists.

A JIT discovery that changes product intent returns to Definition. A bounded technical choice stays in Execution Prep.

## 7. Risk controls

- **Mutable tag race:** serialized promotion + immediate digest readback + candidate eligibility recheck.
- **State rollback mismatch:** mandatory A->C->A proof blocks ordinary promotion.
- **DockerMan destructive old-image cleanup:** predecessor digest/artifact is secured before accepted-channel exposure.
- **Status-cache staleness:** actual docker inspect/digest readback is authority; private cache files are not architecture authority.
- **Public-repo runner compromise:** GitHub-hosted CI only; Tower uses a narrow local validator boundary.
- **Extension regression:** non-core by policy; install/build failures hold back only the extension, runtime feature failure is diagnosed later unless evidence promotes it into core compatibility.
- **User choreography:** no user-required steps until M08.
- **Legacy-path confusion:** M09 removes old scripts/workflows from normal operational guidance.

## 8. Planner challenge audit

Status: **GREEN**

Challenge results:
- every PUD MUST requirement has a milestone owner and evidence gate;
- later R9/R10 compatibility simplification is preserved and no Research-era extension matrix has been reintroduced;
- GHCR/default-branch automation cleanly supersedes the earlier Tower-local normal update path;
- stock DockerMan behavior is treated as an implementation fact to prove, not assumed;
- automatic rollback remains bounded to the user-triggered immediate acceptance transaction;
- user-managed component additions/removals are agent-operated and machine-checkable;
- all technically independent work precedes user-secret and production-click dependencies;
- no unresolved product decision remains inside the approved Definition scope.

The plan is complete and ready for independent Plan Review.
