# Paseo/Pi Runtime on Unraid — Strategic Plan P4

Plan revision: P4
Planning cycle: 4
Status: frozen (pending Premium B independent review)
Definition: R2 / paseo-gui-runtime@3
Workstream: feature-paseo-gui-runtime
Branch: feat/paseo-gui-runtime
Review mode: independent
Date: 2026-09-26
Supersedes: planning/PASEO_GUI_RUNTIME_P3.md for not-yet-materialized M06/M07/M08 only
Preserves: P3 for M01–M05 exactly; Definition R2, requirements, ADR-PGR-001..004 unchanged

## 1. Purpose and accepted authority

P4 is a strategic revision of P3 that consolidates all genuinely interactive
acceptance into one late Human Acceptance (HA) wave while completing every
technically independent automatic check first. Intended final order:

autonomous work → technically ready Paseo/Pi → one consolidated HA wave →
final production acceptance → legacy Pi retirement → Close.

Authority (unchanged, all binding):

- requirements/PASEO_GUI_RUNTIME.md revision R2 (PGR-REQ-001..087).
- decisions/ADR_PGR_001_RUNTIME_SUBSTRATE.md through
  decisions/ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md.
- Immutable prior plan P3 subject
  `elmakus/pi-unraid@b1c5d4c3f340afb96bfb2f3ae44f694069bd6a63:planning/PASEO_GUI_RUNTIME_P3.md@fb071b96e5e7b54187bfaa7040640f5f3eb59b89`.
- All terminal M01–M05 results and GREEN independent reviews (see 2.1).
- Planning entry input (direction only, not authority):
  `elmakus/pi-unraid@384676d5d25989dcba22f6a83f157dfb3bba62f3:planning/inputs/PASEO_GUI_RUNTIME_P4_USER_DECISION_2026-09-26.md@6a76439267dcdc4eeacd161145ac29da9ad50a3f`.

P4 changes milestone slices, dependency graph, gates, requirement/evidence
coverage and risks for M06/M07/M08. It does not revise product authority,
M01–M05 results, Task Board/Cards, PLANNING.toml, Plan Review or production.

Target and baseline are unchanged from P3: one production Paseo container as
the normal Android/PC GUI and Pi execution surface, Git/PW canonical, OR a
separate later layer, pi-unraid owning deployment, environment, workspace and
host administration. The standalone Phase-1 Pi remains a migration/rollback
baseline only.

## 2. Global planning invariants

P3 invariants 1–10 are carried forward unchanged:

1. No product/workflow authority moves into Paseo session/HOME convenience
   state, OR runtime state or the Environment Capability Inventory.
2. Production image derives from one exact resolved official stable
   ghcr.io/getpaseo/paseo base; Pi and approved capabilities install into that
   child or via deterministic Pi-native configuration.
3. Builds consume a frozen candidate; they never discover latest independently.
4. Full /home/paseo is persistent and sensitive; canonical repos/worktrees stay
   outside HOME under the accepted workspace root.
5. Relay is the initial remote-access path; port 6767 is not Internet-facing;
   no alternate LAN/tunnel path is introduced.
6. Server-side Chromium/Playwright exists in the Unraid execution environment
   independently of Paseo desktop Browser Tools.
7. GraphQL is the preferred structured Unraid control path; SSH is fallback for
   gaps/outage/recovery. High-impact operations remain explicit user gates.
8. Direct Main/Pi guards may enforce local no-write-on-main and host safety but
   must not invent universal PW/OR semantics.
9. OR deployment and future PWv2.1 Pi extension are excluded from initial
   bring-up; integration starts only after base GREEN under separate scope.
10. Legacy standalone Pi is retired only after Paseo production acceptance and
    rollback/recovery are proven (strengthened in P4: only after full final
    GREEN plus proven rollback/recovery, section 4/M07-T06).

P4 adds:

11. Technical GREEN is not full GREEN. M06 automatic acceptance yields at most
    "M06 technical GREEN"; "base final GREEN" additionally requires the HA
    wave (with actual phone-to-production proof) plus bounded production
    confirmation and recovery proof.
12. Exactly one consolidated HA wave owns all genuinely interactive proof,
    spanning a staged presence block (M07-T02) and a production-confirmation
    presence block (M07-T03 tail) within one scheduled wave. Automatic work
    never blocks on user presence except a demonstrated minimal technical
    dependency or an already-accepted authorization gate.
13. HA proves staged behavior on a non-production Tower runtime before final
    cutover, then proves production behavior with bounded actual
    phone-to-production Relay confirmation after cutover (decision,
    section 4.1). If the wave cannot finish because of invalidation or review
    delay, final GREEN stops on a minimal user re-entry; phone proof is never
    claimed by inference.
14. Prior exact evidence is reused only when its identity and behavioral
    coverage still apply; reuse never waives a requirement (section 7.1).
15. Docker CLI/Compose remain accepted candidate tooling; they are not the
    host-control architecture. Private project GHCR, registry cache and
    self-hosted runner remain optional, outside the required path.
16. SpecPi core with exact-pair compatibility smoke stays before promotion.
    Optional improvement/wishlist activation is post-deploy capability setup
    (M07-T05): only after production base deploy may it be activated, then
    compatibility smoke, then (and only then) desired-state persistence. It
    never blocks first base startup, and optional failure never claims GREEN
    nor installs into desired state.

## 2.1 P4 change boundary

Preserved exactly (no replanning, no replay, no rewrite):

- M01-T01/T02/T03, M02-T01/T02/T03, M03-T01/T02/T03, M04-T01/T02/T03,
  M05-T01(R02), M05-T02A(R02), M05-T02B, M05-T03(R02): all `done` with GREEN
  independent reviews per TASK_BOARD.toml revision 94.
- M05-T03 exact result/review in particular:
  result `implementation/workstreams/feature-paseo-gui-runtime/results/M05-T03-R02.md@550c5f76cca783e43eb44b0bdbf82c7fe889bff6:b526cf4717ea6d353fc6d23f082b1c726e7f55ed`,
  implementation `900fb0fdef62c21bbc3c484cc4627cd3a3e8b3ea`,
  exact-SHA CI 36258902151 GREEN (243 tests, disposable staged transaction:
  promotion after temp smoke, pre-smoke no_mutation, post-smoke rolled_back,
  runtime-identity HOME guard, protected retention, production-scope refusal).
- M05-T02B local-first evidence (reused under 7.1, not replayed):
  builder `pi-unraid-paseo` (docker-container, BuildKit v0.32.2),
  candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`,
  base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`,
  cold 108143 ms / 0 cached, final warm 7945 ms / 8 cached steps, 4/4 smokes
  GREEN, portable cache 933087833 bytes under 8 GiB cap, protected image
  `sha256:a8ea7f236b5167e4e02a3847b4af21db3b3a91be635be550c591f860d03f40b7`.
- Frozen accepted component pins consumed by P4: Paseo 0.9.2, Pi 0.87.1,
  Playwright 1.63.0 / Chromium 153.0.8010.12 rev 1243 + Xvfb, Docker CLI
  29.8.1, SpecPi 0.34.0, pi-mcp-adapter 2.37.0, Unraid 7.2.4 /
  unraid-api 4.37.4+ad268301 readback discipline.

Redesigned (M06/M07/M08 only):

- P3 M06-T01..T04 (which put real phone Relay pairing and authenticated
  GraphQL mutation before integrated GREEN) is replaced by P4 M06 automatic
  technical slices plus a single M07 HA wave spanning staged proof (M07-T02)
  and production confirmation (M07-T03 tail). P3 M07 cold/warm + full
  integration repetition is replaced by invalidation-gated reuse plus bounded
  production-specific checks. SpecPi wishlist activation moves to post-deploy
  conditional M07-T05, with legacy retirement last as M07-T06. M08 is
  re-bound to the new M06/M07 gates.
- Execution Prep must supersede the satisfied
  `after-M05-T03-materialize-M06-T01` JIT condition's P3 wording before
  materializing any M06 Card; no Card may be cut verbatim from P3 M06/M07.
- P3 remains the immutable record for M01–M05. Any genuine product-authority
  conflict found during P4 execution returns to Definition; it is never
  silently planned away.

## 3. Execution decomposition rule

P3 section 3 is preserved: each planned slice below is a separate Card
candidate; split further on independent mutation surfaces, rollback domains,
acceptance evidence or not-yet-knowable live facts; do not manufacture tiny
Cards for mechanical edits sharing one acceptance surface; express
cross-milestone dependencies through durable predecessor results.

P4 additions:

- Exactly one Card is active per workstream at any time. Cards launch
  deterministically and sequentially via the Board in slice order
  (M06-T01 → T02 → T03 → T04 → M07-T01 → T02 → T03 → T04 → T05 → T06 → M08).
  No Card executes in parallel with another. Bounded preparation and evidence
  research (read-only discovery, harness/script drafting, doc preparation)
  may overlap an active Card only outside that Card's mutation surface; no
  overlapping work may mutate state the active Card owns or pre-empt its
  acceptance evidence.
- The HA wave is one scheduled wave spanning exactly two sequential Cards:
  M07-T02 (staged interactive proof) and M07-T03 (automatic cutover followed
  by an interactive production-confirmation tail). The split is required
  because staged and production mutation surfaces and rollback domains are
  independent. Do not fragment user presence beyond these two presence
  blocks. All automatic preparation (staged runtime, anchors, scripts,
  readback harnesses, cutover preflight) is complete before each presence
  block begins.
- Critical security, HA, production-cutover, host-control and update/rollback
  slices require independent implementation review. M07-T02 must reach
  terminal GREEN (including its independent review) before M07-T03 launches;
  the wave schedule therefore contains a review/transition hold between the
  staged presence block and cutover. Mechanical evidence consolidation may
  use lighter review only when the Card contract justifies it.
- If a future Card depends on live behavior not yet known, leave it as a JIT
  trigger rather than guessing interfaces early.

## 4. Milestone strategy

### M01–M05 — Terminal, preserved (no P4 slices)

M01 (exact candidate + child-image foundation), M02 (persistence/workspace/
Relay/auth/instruction plane), M03 (GraphQL-primary/SSH-fallback/host-doctor
foundation), M04 (inventory/reconcile/doctor + SpecPi/MCP delivery) and M05
(coordinated resolver + Tower-local Buildx/cache/retention + staged
update/rollback transaction) are complete. Their results are consumed as exact
durable predecessors. P4 adds no M01–M05 work.

### M06 — Automatic integrated technical acceptance (no user presence)

Goal: prove the exact candidate as a real combined environment with every
check that does not need a human. Exit is **M06 technical GREEN**, explicitly
not full integrated GREEN.

Common M06 rules: disposable or staged non-production runtimes only; no
production alias/HOME mutation; no secret supply, OAuth/device flow, account
choice, 2FA, manual login approval, real phone pairing, interactive GitHub
auth, GraphQL credential materialization/authenticated mutation, or manual
UX judgment. Any Card needing one fails closed and defers it to the HA wave
(M07-T02/M07-T03).

- M06-T01 Automatic Pi RPC and project/workspace flow: Paseo launches Pi via
  RPC on demand (no permanent RPC required); project selection stays explicit
  with no conversational inference; session/history verified as convenience
  state; repository/PW durable recovery after losing Paseo/Pi session state;
  canonical workspaces/worktrees outside HOME under the accepted root with
  only intended roots exposed; Unraid-compatible ownership and 1 GiB shm
  behavior; no arbitrary CPU/RAM caps; bounded logs/rotation; autostart config
  validated without enabling production autostart.
- M06-T02 Automatic browser/tool/extension compatibility: server-side headless
  and headed/Xvfb Chromium/Playwright launch, screenshot/PDF, dedicated
  persistent automation profile (never a personal profile), temp/task download
  default; dev baseline (shell/Git/network/build/Python/Node), gh binary and
  unauthenticated contract mechanics, Docker CLI/Compose presence (accepted
  tooling, not host control); SpecPi core installed with scope monitoring
  inactive and improvement/wishlist inactive, exact Paseo/Pi/SpecPi-core/
  pi-mcp-adapter compatibility smoke, adapter config/readback/failure-state
  observability. No wishlist activation occurs in M06; it is post-deploy
  capability setup owned by M07-T05 and must not block base startup or
  promotion. Authenticated gh workflow proof and UX judgment move to HA.
- M06-T03 Automatic Relay/persistence/capability/doctor readiness: Relay
  default-disabled fail-closed without consent, pairing-helper consent gate,
  synthetic-identity persistence/recreate survival (proving mechanics, not a
  real phone), zero public ports, secret-bearing HOME handling without raw
  credentials in Git/evidence, revocation/readback fail-closed where upstream
  lacks support; capability inventory desired/observed readback, drift
  reporting without silent deletion, reconcile-restores-approved-only,
  quick/full doctor machine-readable plus GREEN/WARN/RED, lightweight
  healthcheck, bounded auth-health fingerprints only. Real phone pairing and
  pairing-transfer UX move to HA.
- M06-T04 Automatic noninteractive host-control integration: GraphQL-primary
  client, bounded least-practical INFO/DOCKER permission profile and mutation
  allowlist, fail-closed unauthenticated/transport/protocol behavior, exact
  live Unraid/API version/schema readback (non-secret), CI/static safety proof;
  noninteractive SSH reachability plus forced bounded fallback exercise for a
  safe gap/recovery case with pre-mutation readback and rollback/snapshot
  anchor where applicable; high-impact classification (reboot/engine
  restart/OS upgrade/format/broad-delete/broad-network) enforced gated;
  automatic rollback only where the rollback itself is ungated; host doctor
  distinct from PW Recovery/OR doctor; return-to-GraphQL behavior.
  Credential-backed authenticated GraphQL readback and any live mutation move
  to HA.

Exit: exact candidate is technically GREEN as an integrated base. Full GREEN
is impossible before M07-T02/M07-T03/M07-T04.

### 4.1 Human Acceptance (HA) substrate decision (binding)

**Decision: the consolidated HA wave proves staged behavior on a
non-production Tower runtime before final cutover (M07-T02), then cuts over
and proves production behavior with bounded actual phone-to-production Relay
confirmation (M07-T03 tail).**

Dependency rationale:

- Preserves staged safety (PGR-REQ-063/064): pre-deploy failure, including
  staged-HA failure, leaves production untouched; the M05-T03 transaction
  semantics (preflight → temp smoke → promote → post smoke, rollback to
  prior coherent set) stay valid.
- Keeps the legacy standalone Pi as a live rollback/safety anchor through the
  riskiest interactive proofs (credential materialization, first mutation,
  phone pairing) instead of mutating production first.
- Minimizes blast radius of first-time secrets/OAuth/pairing: staged alias
  and shadow/production-equivalent HOME strategy isolate HA mistakes; pairing
  material and approved sessions transfer to production only where upstream
  and PGR-REQ-019 permit reuse, and production Relay behavior is still
  proven by an actual phone action, never inferred from staged proof.
- Satisfies PGR-REQ-079 with a real production leg: staged phone pairing
  proves the Relay mechanism, but first production acceptance additionally
  requires the user's phone to reach the production alias after cutover.
  Automated reachability checks alone are insufficient evidence.
- Fits one-active-Card execution with a workable review boundary: M07-T02
  must be terminal GREEN (independent review included) before M07-T03
  launches, so the wave schedule contains a review/transition hold between
  the staged presence block and cutover. User presence stays grouped into
  two contiguous blocks (staged, then production confirmation) with all
  automatic work prepared beforehand. If the hold cannot complete (RED
  review, invalidation, undecidable transfer), the wave pauses and resumes
  via minimal user re-entry covering only the invalidated surface.
- Keeps invalidation local: staged-vs-production divergence is bounded to
  alias/HOME/anchor identity and covered by explicit M07-T03 confirmation
  checks rather than by repeating full integration.

Rejected alternative (HA after technical deployment to production) is retained
only as the challenge counterfactual in section 9.

### M07 — Consolidated Human Acceptance (HA) + staged production acceptance

Goal: group interactive cost into one wave (staged proof, then production
confirmation), then complete bounded recovery proof, optional post-deploy
capability setup, and legacy retirement last.

- M07-T01 Staged Tower HA readiness (automatic, read-only plus staged
  provisioning): refresh Unraid/API/appdata/workspace/backup/secret-strategy/
  builder-cache/retention/legacy-Pi readback; provision the staged
  non-production Tower runtime from the exact M06-technical-GREEN candidate
  with isolated alias and defined HOME shadow/equivalence; verify rollback
  anchors and backup coverage; establish HA entry gate (M06 technical GREEN +
  staged smoke GREEN + anchors/backups present + session scheduled). No
  production mutation. Private GHCR/runner readiness is not required. Any
  newly required high-impact operation stops for user authority before
  mutation (pre-existing gate, not a new early HA split).
- M07-T02 Staged HA interactive proof (staged runtime, first presence
  block): checklist, all on the staged runtime: secret supply/approval;
  first OAuth/device flow, account choice, 2FA, manual login approval;
  interactive `gh auth` plus GitHub workflow access proof; real phone Relay
  pairing, persistence across routine replacement/restart, bounded session
  reuse and individual revocation where upstream supports it; Unraid GraphQL
  credential materialization plus authenticated least-privilege INFO/DOCKER
  readback and exactly one safe reversible ordinary container mutation with
  pre/post/restoration readback and permission-sufficiency proof; forced
  bounded SSH-fallback confirmation only if M06-T04 left a gap requiring a
  credentialed fallback witness; manual UI/UX judgment (Paseo as normal
  entrypoint, native UI reuse, session labels, notification sanity, no
  second dashboard). Raw credentials stay outside Git/evidence; only bounded
  fingerprints persist. Exit: staged HA GREEN. Minimal earlier gate: none
  beyond already-accepted high-impact, compatibility-exception,
  new-capability and destructive-HOME gates; no ordinary earlier stop is
  planned.
- M07-T03 Production cutover + interactive production confirmation
  (automatic cutover, then second presence block): bind the exact terminal
  M07-T02 GREEN result; preserve prior coherent deployment as rollback
  anchor; promote the exact HA-proven candidate to the production alias;
  enable normal autostart; transfer pairing material and approved
  Relay/GitHub/GraphQL sessions only where upstream and PGR-REQ-019 permit
  reuse. Then, with the user present, run bounded production confirmation:
  Pi RPC, browser smoke without new UX judgment, capability/doctor readback,
  GraphQL authenticated readback reuse without a second mutation unless
  invalidated, and — required — actual phone-to-production Relay
  confirmation from the user's phone against the production alias (bounded
  session action proving the production path; automated reachability alone
  is not sufficient). Keep legacy Pi running and healthy. Exit: production
  confirmation GREEN. If the wave cannot finish here (invalidation, failed
  transfer, review-delayed launch), final GREEN stops and resumes via
  minimal user re-entry covering only the invalidated surface.
- M07-T04 Bounded recovery/update acceptance with reuse: reuse exact M05-T02B
  cold/warm, M06 technical and M07-T02 staged proofs per 7.1 unless an
  invalidation trigger fires; prove only production-specific deltas:
  failed-candidate/pre-deploy protection, safe post-deploy rollback to prior
  coherent set, runtime/container restart recovery, loss-of-session recovery
  from canonical Git/PW without blind replay, HOME preservation (destructive
  restore still user-gated). Whole-host reboot and engine restart are not
  invented as required tests; existing gates apply if a genuine later need
  arises. Exit: recovery GREEN.
- M07-T05 Post-deploy optional SpecPi improvement/wishlist activation
  (conditional, non-blocking): eligible only after M07-T03 production base
  deploy; sequenced after M07-T04 so base acceptance and recovery are
  evaluated on the pure base, and the legacy Pi stays available during any
  activation attempt. First base Paseo/Pi startup and cutover never wait
  for wishlist. Ordered path: activate wishlist → compatibility smoke on
  the exact production pair → desired-state persistence if and only if
  smoke is GREEN. Terminal dispositions: activated-GREEN, explicitly
  deferred, or failed-safe (wishlist left inactive, desired state unchanged,
  failure recorded). Optional failure is WARN and never claims wishlist
  GREEN, never installs into desired state, and never retroactively
  invalidates base final GREEN. Exit: terminal wishlist disposition.
- M07-T06 Legacy standalone Pi retirement: only after M07-T02 staged HA
  GREEN, M07-T03 production confirmation GREEN (including actual
  phone-to-production proof), M07-T04 rollback/recovery GREEN and M07-T05
  terminal wishlist disposition. Stop/remove the old runtime/appdata path
  to the safe extent while preserving required migration/backup evidence.
  Exit: no independent legacy production authority remains.

M07-T01..T04 exit is **base final GREEN** for the base scope. M07-T05 adds a
terminal optional disposition with the legacy anchor still in place. M07-T06
then retires the legacy anchor. All are required before M08.

### M08 — Final evidence, review and downstream unlock

Goal: close only the accepted Paseo/Pi base scope.

- M08-T01 Consolidate requirement/acceptance evidence, M06-technical vs
  staged-HA vs production ledger, wishlist disposition, capability inventory
  readback, production identity, backup boundary, residual risks and handoff.
  Critical final production subject receives required independent
  implementation review.
- M08-T02 Close only after all accepted Cards are terminal and the approved
  scope is durably complete. Record that OR live integration may resume under
  orchestration-runtime authority and future PWv2.1 Pi-extension work needs
  its own accepted scope.

Exit: durable end of approved scope; no OR/PW-extension work smuggled in.

## 5. Dependency and gate graph

Primary sequence (strictly sequential, one active Card at a time):

M01 → M02 → M03 → M04 → M05 (all terminal)
→ M06-T01 → M06-T02 → M06-T03 → M06-T04 (automatic; each binds the shared
frozen candidate and exact M01–M05 predecessors)
→ M06 technical GREEN gate
→ M07-T01 staged readiness
→ HA entry gate → M07-T02 staged presence block → staged HA GREEN gate
→ review/transition hold (M07-T02 independent review + M07-T03 cutover
preflight; no user action required)
→ M07-T03 automatic cutover + production-confirmation presence block
→ M07-T04 bounded recovery → base final GREEN gate
→ M07-T05 wishlist disposition → M07-T06 legacy retirement
→ close-ready gate → M08-T01/T02 → Close.

Gates:

- M06 technical GREEN: all four M06 Cards terminal GREEN in Board order with
  no user presence claimed; candidate/image identity bound; no full-GREEN
  language permitted.
- HA entry: M06 technical GREEN + staged runtime smoke + rollback anchors +
  backup coverage + scheduled wave; production untouched.
- Staged HA GREEN: M07-T02 checklist fully evidenced on staged runtime,
  secret-safe, terminal GREEN including independent review.
- Production confirmation GREEN: M07-T03 cutover on the exact HA-proven
  candidate plus bounded production confirmation GREEN, including actual
  phone-to-production Relay proof; transfer reuse elsewhere or justified
  bounded re-proof.
- Base final GREEN: staged HA GREEN + production confirmation GREEN +
  M07-T04 recovery GREEN.
- Close-ready: base final GREEN + M07-T05 terminal wishlist disposition +
  M07-T06 retirement. M07-T06 itself requires base final GREEN and the
  terminal wishlist disposition, keeping the legacy anchor available during
  any activation attempt. Only then may M08 close.

Sequencing rule: Cards launch deterministically via the Board in the order
above; no two Cards are ever active together. Bounded preparation for a later
slice (read-only discovery, harness drafting) may proceed only outside the
active Card's mutation surface and never substitutes for the gate decision.
No HA, production, wishlist or retirement work begins before its gate.

Wave/review timing: M07-T02 and M07-T03 form one scheduled wave with a
review/transition hold between the staged presence block and cutover. The
hold covers M07-T02 independent review and M07-T03 cutover preflight; the
user is on standby, not dismissed, and all automatic cutover work completes
before the production-confirmation presence block begins. If the hold cannot
complete (RED review, invalidation, undecidable transfer) or the
production-confirmation block fails, the wave pauses: repair or bounded
re-proof first, then resume via minimal user re-entry covering only the
invalidated surface. Phone-to-production proof is never inferred from staged
proof or automated reachability.

Real user stops inside execution remain only accepted gates: the HA wave
(including any minimal re-entry), high-impact Unraid operations, new durable
capability approval, compatibility exceptions from latest, destructive HOME
restore, or genuinely unresolved product authority. Ordinary bounded
host/container/service work does not stop per command.

## 6. Requirement coverage

Every R2 requirement keeps a primary home; no requirement is waived. "Auto"
means M06/M07-T01 automatic; "HA" means the HA wave (M07-T02 staged
interactive plus the M07-T03 interactive production-confirmation tail);
"Prod" means M07-T03/T04 bounded production confirmation and M07-T05
post-deploy disposition; M01–M05 foundations are cited as already GREEN.

- PGR-REQ-001–010 (runtime/UX): M02 foundation preserved; M06-T01/T03 auto
  (RPC on demand, explicit project selection, convenience-state proof,
  ownership/shm/caps, no-broad-mounts); HA judges entrypoint normality,
  native UI reuse, session labels; Prod confirms autostart and the actual
  phone-to-production path.
- PGR-REQ-011–020 (persistence/access/secrets): M02 foundation preserved;
  M06-T01/T03 auto (native HOME paths, workspace outside HOME, Relay
  fail-closed, zero public ports, metadata-only status, secret-safe doctor);
  HA proves first interactive auth, staged pairing persistence/recreate,
  revocation where supported, and actual phone-to-production confirmation;
  pairing material transfers only where upstream permits, and production
  Relay behavior is proven by a phone action, never inferred.
- PGR-REQ-021–026 (tooling/browser): M01 foundation preserved; M06-T02 auto
  (dev baseline, headless + headed/Xvfb, automation profile, temp downloads,
  gh/Docker CLI+Compose presence, no socket mount, no public dev servers);
  HA proves authenticated gh workflow access (staged) with a production
  reuse witness and headed UX judgment; Prod runs smoke-only browser/tool
  confirmation otherwise.
- PGR-REQ-027–035 (inventory/instruction plane): M04/M02 foundations
  preserved; M06-T02/T03 auto (inventory readback, drift without silent
  delete, reconcile/doctor semantics, compact AGENTS.md, Unraid skill,
  reproducible extensions with snapshot/rollback/smoke); HA needs no
  inventory-authority interaction; M07-T05 owns wishlist activation,
  compatibility smoke and persistence (only on GREEN smoke) after base
  deploy; PGR-REQ-035 stays deferred (M08 boundary).
- PGR-REQ-036–044 (PW/OR/Git boundaries): cross-cutting; M02/M03/M04
  foundations preserved; M06-T01/T03/T04 auto (worktree-capable substrate
  without freezing OR topology, recovery from Git/PW, no second Task Board,
  no-write-on-main local enforcement, host-safety-only guards); HA/Prod add
  no new authority; M08 reconfirms deferment of universal promotion.
- PGR-REQ-045–054 (host administration/safety): M03 foundation preserved
  (GraphQL-primary/SSH-fallback, bounded INFO/DOCKER profile, fail-closed,
  pre-readback, gated high-impact classes); M06-T04 auto proves the full
  noninteractive surface; staged HA (M07-T02) owns credential
  materialization, authenticated least-privilege readback, one reversible
  mutation/restoration and permission-sufficiency proof; Prod reuses the
  credential for readback-only confirmation without a second mutation unless
  invalidated; gates for reboot/engine-restart/upgrade/format/broad-delete/
  broad-network, rollback anchors and rotation/readback persist throughout.
- PGR-REQ-055–070 (update/build/cache/rollback): M05/M01 foundations
  preserved (coordinated resolver, frozen candidate, immutable provenance,
  staged transaction, Tower-local builder/cache, bounded retention,
  phase-timed builds); M07-T04 reuses exact M05-T02B cold/warm per 7.1 and
  proves only production deltas (pre-deploy protection, post-deploy rollback,
  HOME preservation with destructive restore gated). PGR-REQ-061/066/067 keep
  the local-first required path; GHCR/cache/runner stay optional.
- PGR-REQ-071–080 (health/observability/recovery/acceptance): M04 foundation
  preserved; M06-T03 auto (lightweight healthcheck, quick/full doctor,
  diagnose/reconcile/update separation, WARN/RED policy, bounded logs,
  structured-results default); HA judges notifications/UX sanity; Prod proves
  crash/restart recovery from Git/PW. PGR-REQ-079 matrix (all required in
  first production acceptance): Pi RPC (M06-T01 auto + M07-T03 Prod),
  phone Relay path (M07-T02 staged pairing + M07-T03 actual
  phone-to-production confirmation — automated reachability alone is not
  sufficient), browser (M06-T02 auto + M07-T03 smoke), GitHub auth/workflow
  (M07-T02 staged proof + M07-T03 reuse witness), doctor/capability
  (M06-T03 auto + M07-T03 Prod), cold/warm build (M05-T02B reuse + M07-T04
  invalidation gate), rollback/recovery (M05-T03 foundation + M07-T04 Prod),
  session-loss recovery (M06-T01 auto + M07-T04 Prod). PGR-REQ-080
  fast-path/wide-validation rule governs M07-T04 scope.
- PGR-REQ-081–082 (deferred boundaries): M08 enforces non-goals before base
  GREEN; no M06/M07 Card may deploy OR or PWv2.1 extension scope.
- PGR-REQ-083–084 (live-readback verification, bounded design freedom):
  M01–M06 exact-candidate/readback strategy preserved; HA/Prod verify secret
  materialization, candidate/Relay/SpecPi/adapter/browser/ownership/
  builder-cache behavior by readback/smoke, never by guess; Execution Prep
  may choose bounded schemas/commands/sizes/check-lists without changing
  authority.
- PGR-REQ-085 (legacy retirement): M07-T06 only, after base final GREEN plus
  terminal M07-T05 wishlist disposition;
  SHOULD-strength preserved as a hard P4 gate.
- PGR-REQ-086–087 (SpecPi/MCP): M04-T03 delivery preserved; M06-T02 auto
  owns exact-pair SpecPi-core compatibility smoke before promotion (scope
  and wishlist inactive); M07-T05 owns post-deploy wishlist activation,
  then compatibility smoke, then persistence only on GREEN; adapter
  config/readback/failure covered by full doctor/acceptance; HA adds no
  compatibility exception.

No requirement is intentionally deferred except R2-declared separate scope
(PGR-REQ-035/081/082 mechanics).

## 7. Evidence and review strategy

Each Card produces the smallest durable evidence proving its own acceptance
surface. Live evidence identifies the tested immutable candidate/production
image and avoids raw credentials (bounded fingerprints only).

Minimum per checkpoint:

- M01–M05: existing terminal evidence stands; later Cards cite exact
  result commit/blob, never re-prove foundations.
- M06: per-slice automatic matrix (RPC/workspace, browser headless+headed,
  SpecPi/adapter compatibility, inventory/doctor, noninteractive
  GraphQL/SSH/read-only/API-version evidence), all candidate-bound, all
  explicitly "technical GREEN, HA outstanding".
- M07-T01: staged readiness readback (Unraid/API/appdata/backup/secrets/
  builder/retention/legacy state) plus staged runtime identity and smoke.
- M07-T02: staged HA ledger (secret/OAuth/2FA/account handling without
  secret disclosure, gh workflow, staged phone pairing + recreate, GraphQL
  credential + readback + reversible mutation/restoration, UX judgment).
- M07-T03: promotion record (prior anchor, exact candidate, autostart,
  transfer disposition per surface) plus production-confirmation ledger
  including actual phone-to-production Relay proof and bounded production
  smoke.
- M07-T04: reuse ledger (which M05-T02B/M06/HA evidence reused, identity
  comparison, trigger evaluation) plus production-only delta proofs.
- M07-T05: wishlist disposition record (activated-GREEN with smoke +
  persistence refs, explicitly deferred, or failed-safe/WARN with desired
  state unchanged).
- M07-T06: retirement record with preserved migration/backup refs.
- M08: final requirement ledger mapping every PGR-REQ to
  technical/staged-HA/Prod evidence, wishlist disposition, production
  identity, backup boundary, residual risks, handoff; required independent
  review of the critical final production subject.

Execution Prep binds predecessor-dependent Cards to exact durable results.

### 7.1 Evidence reuse and invalidation (binding)

Reuse is an acceptance method only when identity and behavioral coverage
still apply; it never waives a requirement.

- M05-T02B cold/warm reuse in M07-T04: permitted when frozen candidate ID,
  Dockerfile/build graph, builder identity/config (pi-unraid-paseo,
  docker-container, BuildKit line), cache paths/policy/caps, retention
  policy/maximum and smoke surfaces are all unchanged. Any change, or Tower
  storage/permission drift affecting build behavior, invalidates the affected
  leg and requires a bounded re-run of that leg only (cold or representative
  warm), not a full strategy replay.
- M06 technical reuse in M07-T03/T04: permitted when candidate/image,
  compose/runtime config, HOME/secret strategy, capability set, Unraid/API
  readback line and doctor/inventory contracts are unchanged. Staged-vs-
  production alias/HOME divergence is expected and is covered by M07-T03
  confirmation checks, not by repeating full M06.
- HA staged reuse in M07-T03 production confirmation: pairing material, gh
  session and GraphQL credential transfer is permitted when upstream
  supports persistence/reuse, the secret strategy transfers the state
  intact, and no revocation/expiry/permission rotation occurred. Transfer
  never substitutes for the required actual phone-to-production Relay
  confirmation. If the wave cannot finish (invalidation, failed transfer,
  review delay), final GREEN stops and resumes via minimal user re-entry
  covering only the invalidated surface; phone proof is never inferred.
- M05-T03 transaction reuse: M07-T03/T04 consume its disposable proof as the
  transaction design; production cutover/rollback behavior is still proven
  live in M07-T03/T04 because scope (Tower production alias) differs.
- Wishlist scope isolation: M07-T05 activation, smoke or persistence affects
  only the wishlist disposition; it never re-opens base M06/M07-T01..T04
  proofs. A wishlist smoke failure invalidates only wishlist persistence,
  which must then not occur, and is recorded as WARN.

## 8. Risks and planned containment

- Staged-vs-production divergence: bound to alias/HOME/anchor identity;
  contained by M07-T01 equivalence definition plus M07-T03 confirmation.
- HA scheduling delay: M06 technical work never blocks on HA; staged runtime
  and anchors are refreshable; HA entry gate revalidates freshness.
- First-credential blast radius: staged-first containment, least-privilege
  profile, one reversible mutation, pre/post/restoration readback, no raw
  secrets in evidence.
- Pairing/session transfer failure: staged HA proves pairing; M07-T03 proves
  production behavior with an actual phone action; invalidation triggers
  force minimal re-entry re-proof, not silent carryover or inference.
- Wave-hold overrun (review delay, RED review, invalidated transfer): the
  wave pauses before cutover with production untouched; repair or bounded
  re-proof first, then resume via minimal re-entry. No cutover proceeds on
  an unreviewed or invalidated staged result.
- GraphQL permission insufficiency: M06-T04 static/profile proof precedes HA;
  HA proves sufficiency without a broader role; failure returns to bounded
  profile repair, not role escalation by inertia.
- Fast-moving Paseo/Pi/SpecPi/MCP: frozen candidate plus exact compatibility
  smoke; no silent lag; exceptions need explicit approval + re-evaluation.
- UID/GID mismatch: preserve upstream Paseo identity; prove host write live.
- Browser mismatch: freeze package/browser versions together; smoke headless
  and Xvfb; dedicated automation profile.
- Secret leakage: native mechanisms, sensitive-HOME handling, fingerprints
  only; M06 requires no interactive handoff.
- Capability-policy duplication: inventory stays availability-only.
- Build/cache regression: persistent Tower cache, bounded retention,
  post-success prune, rebuild-from-Git recovery on total loss.
- Session/runtime loss: recover from canonical Git/PW; never blindly replay.
- UX subjectivity: HA judgment is explicit and secret-safe; automatic Cards
  never claim UX GREEN.
- Mega-Card regression: preserve slices; the HA wave spans exactly M07-T02
  and the M07-T03 tail by PWv2 boundary, with all preparation outside the
  presence blocks; wishlist stays a separate conditional slice.

## 9. Planner audit and challenge

Planner audit: GREEN.

- Authority: P4 consumes Definition R2 + ADR-PGR-001..004 without weakening
  any MUST/SHOULD; Docker CLI/Compose retention, GraphQL-primary/SSH-fallback
  and local-first build stances match accepted authority.
- Preservation: M01–M05 terminal results untouched; M05-T03 exact
  result/review cited; plan changes only not-yet-materialized M06/M07/M08.
- Sequencing: exactly one active Card; strictly sequential Board order with
  no parallel execution; bounded preparation overlaps only outside the
  active Card's mutation surface.
- HA consolidation: every user-decision interactive class has its home in
  the HA wave (M07-T02 staged proof, M07-T03 production-confirmation tail);
  automatic M06 slices explicitly exclude them and fail closed; the wave
  spans two Cards by PWv2 boundary with a workable review/transition hold.
- PGR-REQ-079: each matrix element has staged and/or production legs with no
  silent waiver; the production leg includes actual phone-to-production
  Relay confirmation, never inferred; minimal re-entry covers wave breaks.
- Gates: technical vs staged-HA vs production vs base-final GREEN are
  distinct; high-impact/compatibility/new-capability/destructive-HOME gates
  persist; minimal earlier gate stated.
- Reuse: M05-T02B/M06/HA reuse is identity-gated with explicit triggers and
  bounded re-proof; unchanged behavior is not re-executed for ceremony.
- Legacy anchor: retirement (M07-T06, last) strictly after staged HA +
  production confirmation (with actual phone proof) + recovery GREEN +
  terminal M07-T05 wishlist disposition, keeping the anchor available
  during any activation attempt.
- SpecPi/wishlist: core-before-promotion with exact compatibility; wishlist
  is post-deploy M07-T05 (activate → smoke → persist only on GREEN),
  non-blocking, with failed-safe/WARN and deferred dispositions that never
  claim wishlist GREEN nor touch desired state.

Challenge pass (strongest counterfactuals considered):

1. HA after technical deployment to production: rejected — mutates production
   before first credential/pairing proof, weakens staged safety and the
   legacy anchor, and risks re-entry after rollback. Staged-first with an
   actual phone-to-production confirmation tail dominates on safety.
2. Keep P3 early interactive timing (Relay pairing + GraphQL mutation in
   M06): rejected — forces user presence before technical readiness,
   fragments HA across milestones, and repeats interactive cost. P4 proves
   all noninteractive prerequisites first.
3. Single-Card HA wave (staged + cutover + production confirmation in one
   Card): rejected — combines independent staged/production mutation
   surfaces and rollback domains. The M07-T02/M07-T03 split with a
   review/transition hold is required; presence still groups into one wave.
4. Infer production Relay from staged proof plus automated reachability:
   rejected — PGR-REQ-079's phone path requires an actual phone action
   against the production alias. Staged proof plus inference is insufficient
   evidence by definition.
5. Re-resolve the candidate to drop Docker CLI/Compose now: rejected —
   accepted cleanup-deferral direction; removal is later cleanup, not a
   current-path prerequisite, and must not disturb the frozen candidate.

No unresolved product decision remains hidden as an implementation
assumption. Tower storage/path/retention quantities, concrete wave-scheduling
mechanics and exact production smoke commands are bounded Execution Prep /
live-readback details, not new product authority.

## 10. Planning completion

P4 is complete when this exact plan has:

- full accepted-authority coverage;
- explicit milestone/dependency/gate strategy with one-active-Card
  sequential execution;
- HA-substrate decision with dependency rationale and workable
  review/transition timing;
- bounded execution decomposition suitable for later stable Task Cards;
- evidence-reuse/invalidation rules covering M05-T02B, M06, HA transfer and
  wishlist scope isolation;
- no unresolved product decision hidden as an implementation assumption;
- GREEN planner audit;
- immutable Git subject frozen for independent Plan Review.

After freeze, Premium B requires a fresh independent best-available review
context. The planning context that authored P4 must not perform that review.
