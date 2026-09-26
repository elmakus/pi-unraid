# Independent Plan Review — Paseo GUI Runtime P4 / R01

Plan revision: `P4`
Planning cycle: `4`
Workstream: `feature-paseo-gui-runtime`
Branch: `feat/paseo-gui-runtime`
Review state: `green`
Reviewed subject: `elmakus/pi-unraid@f87ec5df4215af06302765bad615a6be69a295ef:planning/PASEO_GUI_RUNTIME_P4.md@3c0949e50b41100630b8e57f7dc51472e183f49c`

## Independence

This review was performed in a fresh independent context reserved by `PLAN_REVIEW.toml` R01.
The reviewer did not materially author or repair the exact frozen P4 subject.
Planner audit (`planning/audits/PGR_P4.md`) and frozen plan were treated as evidence only;
no planner judgment was borrowed.

## Authority checked

- `requirements/PASEO_GUI_RUNTIME.md` revision R2 / Definition `paseo-gui-runtime@3`
- `decisions/ADR_PGR_001_RUNTIME_SUBSTRATE.md` through `ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md`
- Immutable prior plan P3 subject `elmakus/pi-unraid@b1c5d4c3f340afb96bfb2f3ae44f694069bd6a63:planning/PASEO_GUI_RUNTIME_P3.md@fb071b96e5e7b54187bfaa7040640f5f3eb59b89`
- Entry input `elmakus/pi-unraid@384676d5d25989dcba22f6a83f157dfb3bba62f3:planning/inputs/PASEO_GUI_RUNTIME_P4_USER_DECISION_2026-09-26.md@6a76439267dcdc4eeacd161145ac29da9ad50a3f` (direction only)
- `implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml` revision 94
- Current Project Workflow V2 Planning and Independent Plan Review contracts

## Independent findings

### Exact subject identity — GREEN

`git show f87ec5df4215af06302765bad615a6be69a295ef:planning/PASEO_GUI_RUNTIME_P4.md`
hashes to `3c0949e50b41100630b8e57f7dc51472e183f49c`; HEAD working-tree plan hashes
identically (frozen subject unmodified). `PLANNING.toml` cycle 4 / revision P4 /
`premium_a=satisfied` on the exact entry subject / `premium_b=satisfied` on the exact
frozen subject matches `PLAN_REVIEW.toml` R01 subject. Plan header cycle 4, revision P4,
Definition R2/`paseo-gui-runtime@3`, branch and date are consistent. Router obligation
before review is `plan_review` on this exact subject.

### Accepted authority and requirement coverage — GREEN

Section 6 assigns every R2 requirement a primary home with no waiver:
001–010, 011–020, 021–026, 027–035, 036–044, 045–054, 055–070, 071–080, 081–082,
083–084, 085, 086–087 (contiguous, no gap). Only R2-declared separate scope
(035/081/082 mechanics) is deferred. MUST/SHOULD stances preserved: one-container
Paseo/Pi shape, Git/PW canonical, Relay-first, GraphQL-primary/SSH-fallback with
explicit high-impact gates, staged immutable-candidate deployment, secret-safe
evidence, local-first Tower Buildx/cache/retention with GHCR/cache/runner optional,
Docker CLI/Compose retained per REQ-025.

### Terminal M01–M05 preservation — GREEN

Section 2.1 preserves exactly the 16 done Cards (M01-T01..M05-T03 incl. M05-T01 R02,
M05-T02A R02, M05-T02B, M05-T03 R02) per Board revision 94; no M06+ Card exists
(only `after-M05-T03-materialize-M06-T01` JIT trigger). M05-T03 R02 citation verified:
result commit `550c5f76…`, blob `b526cf47…`, implementation `900fb0fd…`, CI 36258902151
GREEN 243 tests with disposable-transaction semantics matching the durable result.
M05-T02B reuse figures verified against durable evidence (builder `pi-unraid-paseo`,
BuildKit v0.32.2, candidate `b4e0c1e7…`, base `d413ff36…`, cold 108143 ms/0 cached,
warm 7945 ms/8 cached, 4/4 smokes, cache 933087833 B under 8 GiB, protected image
`a8ea7f23…`). Frozen pins verified (Paseo 0.9.2, Pi 0.87.1, Playwright 1.63.0 /
Chromium 153.0.8010.12 rev 1243, Docker CLI 29.8.1, SpecPi 0.34.0,
pi-mcp-adapter 2.37.0, Unraid 7.2.4 / unraid-api 4.37.4+ad268301).

### M06/M07/M08 decomposition and dependency gates — GREEN

Strictly sequential one-active-Card order M06-T01→M08 with no parallel execution;
bounded preparation only outside the active mutation surface. M06 yields at most
"technical GREEN"; distinct HA-entry, staged-HA-GREEN, production-confirmation-GREEN,
base-final-GREEN and close-ready gates. P3 M06 early phone pairing + authenticated
mutation (P3 M06-T03/T04) is correctly replaced by automatic M06 plus late HA wave;
P3 M07 cold/warm repetition is replaced by invalidation-gated reuse plus bounded
production deltas. Execution Prep must supersede the satisfied P3-worded JIT condition
before any M06 Card; no verbatim P3 Card cut is permitted.

### Late HA consolidation and feasibility — GREEN

All entry-input interactive classes (secret/OAuth/account/2FA/login approval, phone
pairing, interactive gh auth, GraphQL credential/mutation proof, UX judgment) are owned
by one wave spanning exactly M07-T02 (staged presence) and the M07-T03 tail
(production confirmation), split by staged/production mutation-surface boundary.
M06 common rules fail closed on every such class. M07-T02 terminal GREEN including
independent review plus cutover preflight forms an explicit review/transition hold
(user on standby); wave breaks pause before cutover and resume via minimal re-entry
covering only the invalidated surface. M07-T01 staged readiness with isolated alias
and HOME shadow/equivalence plus rollback anchors makes staged-first technically
plausible on the proven M05-T03 transaction semantics.

### PGR-REQ-079 production phone proof — GREEN

The 079 matrix has explicit staged and/or production legs for Pi RPC, phone Relay,
browser, GitHub auth, doctor/capability, cold/warm, rollback/recovery and
session-loss recovery. Production acceptance requires an actual phone-to-production
Relay action against the production alias; automated reachability alone is
insufficient and staged proof is never inferred as production proof (invariants
12–13, sections 4.1/5/7.1, gates).

### Legacy Pi safety anchor — GREEN

Retirement is last (M07-T06) strictly after staged HA GREEN, production confirmation
GREEN including actual phone proof, M07-T04 recovery GREEN and terminal M07-T05
wishlist disposition. The standalone Pi stays live through first credentials, first
mutation and pairing, satisfying the entry-input final sequence and strengthening
REQ-085 as a hard P4 gate.

### M05-T02B/M06/HA reuse and invalidation — GREEN

Section 7.1 gates reuse on identity plus behavioral coverage and never waives a
requirement. M05-T02B cold/warm reuse requires unchanged candidate, build graph,
builder/config, cache/retention and smoke surfaces; drift forces bounded leg-only
re-run. M06 reuse requires unchanged candidate/config/HOME/capability/API/doctor
contracts; expected staged/production alias/HOME divergence is covered by M07-T03
confirmation, not full repeat. HA transfer requires upstream/secret-strategy support
without revocation/expiry/rotation and never substitutes for phone-to-production
proof. M05-T03 design is consumed but production cutover/rollback is still proven
live; wishlist scope isolation never re-opens base proofs.

### SpecPi core/wishlist order — GREEN

M06-T02 installs SpecPi core with scope monitoring and wishlist inactive and runs
exact-pair compatibility smoke before promotion. M07-T05 is conditional post-deploy
(only after M07-T03 production base, sequenced after M07-T04): activate → smoke on
the exact production pair → persist only on GREEN; dispositions are
activated-GREEN, explicitly deferred, or failed-safe/WARN with desired state
unchanged, never claiming wishlist GREEN nor invalidating base GREEN. This preserves
REQ-086 (MAY-enabled wishlist, exact-pair smoke before promotion) and the
must-not-block-first-startup constraint.

### Planner completeness and challenge audit — GREEN

Section 9 plus `planning/audits/PGR_P4.md` GREEN covers authority, preservation,
sequencing, HA consolidation, 079, gates, reuse, legacy anchor and SpecPi/wishlist.
Five strongest counterfactuals (HA-after-deploy, retained P3 early timing,
single-Card wave, inferred production Relay, re-resolve to drop Docker CLI/Compose)
are each rejected with dependency/safety/authority rationale. Remaining Execution
Prep/live-readback details (storage quantities, wave scheduling mechanics, exact
smoke commands, HOME shadow/equivalence binding) are bounded and do not hide a
product decision; genuine authority conflicts return to Definition.

## Verdict

**GREEN.**

The exact P4 subject is consistent with Definition R2 and ADR-PGR-001..004, preserves
terminal M01–M05 exactly, provides sufficient M06/M07/M08 decomposition with workable
late-HA timing and distinct gates, and contains no material strategy, scope,
authority, rollback, security or acceptance defect requiring another planning cycle.

This verdict establishes plan sufficiency only. It does not prove downstream live
behavior, production readiness or implementation correctness; those remain Planning
consumption, Execution Prep, Card execution and acceptance obligations.
