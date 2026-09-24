# Paseo/Pi Runtime on Unraid — Strategic Plan P1

Plan revision: P1
Planning cycle: 1
Status: frozen
Definition: R1 / paseo-gui-runtime@2
Workstream: feature-paseo-gui-runtime
Branch: feat/paseo-gui-runtime
Review mode: independent
Date: 2026-09-24

## 1. Purpose and accepted authority

P1 turns the GREEN Paseo/Pi Definition into an executable strategy without changing product authority. It is governed by requirements/PASEO_GUI_RUNTIME.md and ADR-PGR-001 through ADR-PGR-004. Definition Research R1 is factual support for implementation choices but does not replace those authorities.

The target is one production Paseo container on Unraid that is the normal Android/PC GUI and Pi execution surface, with Git/PW remaining canonical, OR remaining a separate later runtime-orchestration layer, and pi-unraid owning deployment, environment capabilities, workspace substrate and host administration.

The existing standalone Phase-1 Pi image, compose shape and scripts are a migration baseline only. They may be reused where their behavior still satisfies R1, but their Node-base image, /home/pi identity, sudo-oriented bootstrap and standalone-Pi lifecycle must not be carried forward by inertia.

## 2. Global planning invariants

1. No product or workflow authority moves into Paseo session state, HOME convenience state, OR runtime state or the Environment Capability Inventory.
2. The production image derives from one exact resolved official stable ghcr.io/getpaseo/paseo base. Pi and approved global capabilities are installed into that child image or reproduced through deterministic Pi-native configuration.
3. Builds consume a frozen candidate resolution. They never discover latest independently.
4. The full /home/paseo state is persistent and sensitive; canonical repositories/worktrees stay outside HOME under the accepted workspace root.
5. Relay is the initial remote-access path. Port 6767 is not published as an Internet-facing path and no alternate LAN/tunnel path is introduced in this scope.
6. Server-side Chromium/Playwright exists inside the Unraid execution environment independently of Paseo desktop Browser Tools.
7. GraphQL is the preferred structured Unraid control path; SSH is fallback for gaps, outage and recovery. High-impact operations remain explicit user gates.
8. Direct Main/Pi environment guards may enforce local no-write-on-main and host safety, but must not invent universal PW/OR semantics.
9. OR deployment and the future PWv2.1 Pi extension are excluded from the initial Paseo+Pi bring-up. Their integration starts only after the base environment is GREEN under separate accepted scope.
10. The legacy standalone Pi deployment is retired only after Paseo production acceptance and rollback/recovery are proven.

## 3. Execution decomposition rule

Execution Prep must preserve the plan decomposition below. A milestone is not permission to create one mega-Card.

Each planned slice below is a separate Card candidate unless bounded refinement makes it smaller. Execution Prep must split a slice further when it would combine independent mutation surfaces, independent rollback domains, materially different acceptance evidence, or a live-fact dependency that is not yet knowable.

Conversely, it must not manufacture tiny Cards for purely mechanical edits that share one acceptance surface. Cross-milestone dependencies are expressed through durable predecessor results, not chat narrative.

Critical security, production-cutover, host-control and update/rollback slices require independent implementation review. Pure documentation or mechanical evidence consolidation may use a lighter review requirement when the stable Card contract justifies it.

## 4. Milestone strategy

### M01 — Exact candidate and Paseo child-image foundation

Goal: establish a reproducible, immutable candidate that can be built and tested without touching production.

Planned slices:

- M01-T01 Candidate resolver and frozen resolution record: resolve accepted latest-stable lines for Paseo, Pi, Node/runtime prerequisites, Playwright/Chromium, SpecPi, pi-mcp-adapter and other approved global baseline tools; record exact versions plus digest/SHA/integrity where available. Compatibility exceptions fail closed and return to explicit user authority.
- M01-T02 Child image and development/browser baseline: replace the standalone Node image foundation with the exact official Paseo base; install Pi, shell/Git/network/build/Python/Node tooling, gh, Docker CLI/Compose, server-side Playwright/Chromium and headed Xvfb support while preserving the upstream non-root Paseo contract.
- M01-T03 Image provenance and disposable smoke: prove Pi binary/RPC availability, browser launch, baseline tools, lightweight healthcheck, image labels/provenance and secret-free build output before any live deployment.

Exit: one exact non-production candidate image is reproducibly buildable and passes fast image-level smoke.

### M02 — Persistence, workspace, Relay, authentication and instruction plane

Goal: make the runtime usable without making convenience state authoritative.

Planned slices:

- M02-T01 Compose/runtime persistence and ownership: /home/paseo persistence, external project/worktree roots, configurable Paseo worktree root, 1 GiB shared memory target, bounded logs, Unraid-compatible host ownership, no arbitrary CPU/RAM caps, and live read/write ownership smoke without blindly forcing the old Pi UID model.
- M02-T02 Relay, pairing, auth and secret materialization: Relay opt-in/pairing persistence, no raw external Paseo port publication, deliberate first-time human authentication, reusable approved sessions, revocation/readback where upstream supports it, and secret-bearing HOME/credential handling outside Git.
- M02-T03 Pi-native instruction/config plane: compact global AGENTS.md, progressively loaded global skills/references, dedicated Unraid administration knowledge, reproducible approved extensions/config, project selection remaining user-driven, and canonical PW/Git recovery before managed mutation after a project is selected.

Exit: a disposable/recreated runtime preserves required HOME/Relay state, keeps code/worktrees outside HOME, and exposes no alternate authority or raw credential surface.

### M03 — Unraid host-control and safety plane

Goal: give Main full accepted host administration while preserving explicit high-impact gates.

Planned slices:

- M03-T01 GraphQL-primary control: dedicated Unraid API credential materialization, least-practical role/permission set compatible with accepted administration, structured readback and bounded ordinary mutations.
- M03-T02 SSH fallback and mutation guard: non-interactive SSH for API gaps/outage/recovery, bounded pre-mutation readback, rollback/snapshot anchors where applicable, explicit classification of reboot/Docker-engine restart/OS upgrade/format/broad-delete/broad-network operations as user-gated, and automatic safe rollback only where the rollback itself is not gated.
- M03-T03 Host-control doctor: read-only GraphQL health/capability checks, SSH fallback reachability, credential-health fingerprints without secret disclosure, and a host doctor kept distinct from PW Recovery and OR doctor semantics.

Exit: accepted bounded host actions are automatable and the high-impact gate boundary is mechanically testable.

### M04 — Environment Capability Inventory, reconcile and doctor

Goal: make the global environment reproducible and observable without duplicating OR policy.

Planned slices:

- M04-T01 Capability inventory and desired-state derivation: one declarative inventory for approved global capability identity, provenance, delivery mode, desired/observed version, runtime location and health/drift; no OR role ceilings, action classification, bundles or assignment eligibility.
- M04-T02 Reconcile/doctor surfaces: doctor remains read-only, reconcile restores already-approved desired state, update changes accepted version lines; unexpected extras are reported rather than silently deleted; quick/full doctor produce machine-readable output plus concise GREEN/WARN/RED summaries.
- M04-T03 SpecPi/MCP/global capability delivery: install SpecPi with scope monitoring inactive, retain improvement/wishlist capability, install pi-mcp-adapter only if the exact candidate passes compatibility smoke, and make config/readback/failure state observable without leaking secrets.

Exit: desired environment state is reproducible, drift is visible, and environment ownership stays separate from OR runtime-use policy.

### M05 — Coordinated update, build cache and rollback pipeline

Goal: make routine global maintenance fast, immutable and fail-closed.

Planned slices:

- M05-T01 Coordinated latest resolver: resolve all approved global components together to accepted stable lines, freeze the exact candidate, retain durable rationale for any explicitly approved compatibility exception, and ensure project-local locked dependencies remain outside blanket updates.
- M05-T02 Buildx/GHCR/cache path: dedicated persistent Buildx/BuildKit builder, private GHCR child image, secondary registry cache, bounded post-success pruning, cache-friendly Dockerfile stages/cache mounts/rebase techniques where measured useful, immutable image identity and material phase timing.
- M05-T03 Staged update/cutover/rollback: build → fast checks → temporary runtime smoke → promote/cutover → post-deploy smoke, production untouched on pre-deploy failure, safe rollback to prior coherent known-good set on post-deploy failure, and HOME restore only for proven state corruption with destructive restore user-gated.

Exit: update/reconcile/doctor semantics are distinct and a candidate can be promoted or rolled back without ambiguous partial state.

### M06 — Integrated non-production Paseo+Pi capability acceptance

Goal: prove the exact candidate as a real combined environment before production cutover.

Planned slices:

- M06-T01 Pi provider/RPC and project/workspace flow: Paseo launches Pi through RPC on demand, project selection remains explicit, session/history remain convenience state, and repository/PW durable state is sufficient to recover after losing Paseo/Pi session state.
- M06-T02 Tool/browser/extension compatibility: server-side headless and Xvfb Chromium/Playwright, gh/Git workflow access, SpecPi with scope inactive, pi-mcp-adapter config/readback, and the exact resolved Paseo/Pi/SpecPi/MCP combination.
- M06-T03 Relay/mobile and persistence smoke: real phone Relay path, pairing persistence across routine container replacement/restart, bounded auth/session reuse and individual revocation behavior where upstream supports it.
- M06-T04 Host-control integration smoke: GraphQL-primary ordinary operation, forced bounded SSH-fallback exercise for a safe gap/recovery case, host doctor and return-to-GraphQL behavior.

Exit: the exact candidate is GREEN as an integrated base environment. OR is still not deployed.

### M07 — Production cutover, recovery and first-acceptance matrix

Goal: deploy the proven candidate to Tower with rollback safety and retire the transitional standalone Pi only after acceptance.

Planned slices:

- M07-T01 Read-only Tower readiness: refresh Unraid version/API state, appdata/workspace ownership, current Paseo absence/presence, backup coverage, secrets, GHCR/build runner/cache readiness and legacy Pi state. Any newly required high-impact operation stops for user authority before mutation.
- M07-T02 Staged production deploy: preserve prior coherent deployment as rollback anchor, deploy the immutable candidate, enable normal autostart, complete post-deploy Pi RPC/Relay/browser/GitHub/doctor/capability smoke, and keep old Pi available until the new path is accepted.
- M07-T03 Recovery/update acceptance: cold build, representative warm update with real cache reuse, failed-candidate/pre-deploy protection, safe post-deploy rollback, runtime/container restart recovery, loss-of-Paseo/Pi-session recovery from canonical Git/PW state, and secret-safe evidence. Whole-host reboot or Docker-engine restart is not invented as a required test; if a later accepted acceptance need genuinely requires one, the existing user gate applies.
- M07-T04 Legacy standalone Pi retirement: only after M07-T02/T03 are GREEN and rollback is proven, stop/remove the old standalone Pi runtime/appdata path to the extent safe while preserving any still-required migration/backup evidence.

Exit: Paseo is the normal production GUI/runtime surface and the transitional standalone Pi is no longer an independent production authority.

### M08 — Final evidence, review and downstream unlock

Goal: close only the accepted Paseo+Pi base scope.

Planned slices:

- M08-T01 Consolidate requirement/acceptance evidence, capability inventory readback, production identity, backup boundary, known residual risks and final handoff. Critical final production subject receives required independent implementation review.
- M08-T02 Close the workstream only after all accepted Cards are terminal and the approved scope is durably complete. Record that OR live integration may now resume under orchestration-runtime authority and that future PWv2.1 Pi-extension packaging/bootstrap requires its own separately accepted scope after that contract stabilizes.

Exit: durable end of approved scope. No OR or future PW extension work is smuggled into this workstream.

## 5. Dependency and gate graph

Primary sequence:

M01 → M02 → M03 → M04 → M05 → M06 → M07 → M08

Bounded parallelism is allowed only where exact dependencies make it safe:

- M03 implementation can be prepared in parallel with late M02 work after secret/persistence interfaces are stable, but live integrated acceptance waits for both.
- M04 inventory/doctor schema can begin once M01 candidate identifiers and M02 config locations are stable.
- M05 cache/build mechanics may start after M01 exact-candidate semantics are stable, but cutover/update acceptance waits for M02–M04.
- M06 consumes GREEN results from M01–M05.
- M07 consumes the exact GREEN integrated candidate from M06.
- M08 consumes terminal production acceptance from M07.

Real user stops inside execution are only those already authorized by Definition/PW semantics: high-impact Unraid operations, new durable global capability approval, compatibility exceptions from latest, destructive HOME restore, or genuinely unresolved product authority. Ordinary bounded host/container/service work does not stop per command.

## 6. Requirement coverage

The milestone coverage is intentionally overlapping because acceptance validates cross-cutting behavior, but every R1 requirement has a primary home:

- PGR-REQ-001–010: M02 primary; M06/M07 acceptance.
- PGR-REQ-011–020: M02 primary; M06/M07 persistence, Relay and secret acceptance.
- PGR-REQ-021–026: M01 primary; M06 tool/browser acceptance.
- PGR-REQ-027–035: M04 primary; M02 instruction-plane implementation; M06/M07 readback.
- PGR-REQ-036–044: cross-cutting invariants in M02/M03/M04; M06 recovery acceptance; M08 boundary confirmation.
- PGR-REQ-045–054: M03 primary; M06/M07 live acceptance.
- PGR-REQ-055–070: M05 primary; M01 candidate foundation; M07 cold/warm/update/rollback acceptance.
- PGR-REQ-071–080: M04 doctor/observability primary; M06/M07 integrated and production acceptance.
- PGR-REQ-081–082: M08 enforces deferment; they are explicit non-goals before base GREEN.
- PGR-REQ-083–084: M01–M06 exact-candidate/live-readback strategy; Execution Prep may choose bounded schemas/commands without changing authority.
- PGR-REQ-085: M07-T04.
- PGR-REQ-086–087: M04-T03 delivery plus M06 exact compatibility acceptance.

No requirement is intentionally deferred except the integrations that R1 itself declares separate later scope.

## 7. Evidence and review strategy

Each implementation Card must produce the smallest durable evidence that proves its own acceptance surface. Live evidence must identify the tested immutable candidate or production image and avoid raw credentials.

Milestone checkpoints should consolidate, not replace, Card evidence. At minimum:

- M01: frozen candidate + reproducible image/build smoke.
- M02: persistence/ownership/Relay/auth/instruction readback.
- M03: GraphQL/SSH/gate/host-doctor evidence.
- M04: inventory/drift/reconcile/doctor and SpecPi/MCP readback.
- M05: cold/warm build timing, cache reuse, staged update and rollback evidence.
- M06: integrated Pi RPC/Relay/browser/GitHub/extensions/host-control matrix.
- M07: production identity, post-deploy smoke, recovery/update matrix and legacy retirement evidence.
- M08: final requirement coverage and independent final review.

Execution Prep must bind predecessor-dependent Cards to exact durable results. If a future Card depends on live behavior not yet known, leave it as a JIT trigger until its stable contract becomes knowable rather than guessing the interface early.

## 8. Risks and planned containment

- Fast-moving Paseo/Pi/SpecPi/MCP versions: exact candidate resolution plus compatibility smoke; no silent lag.
- UID/GID mismatch with official Paseo image: preserve upstream identity and prove host write semantics live instead of hard-coding the legacy Pi model.
- Relay or pairing state loss: persistent HOME plus rebuild/restart smoke before production.
- Browser dependency/version mismatch: freeze package/browser versions together and smoke both headless and Xvfb modes.
- Host-control overreach: structured readback, explicit high-impact gate classification, no broad arbitrary host mounts by default.
- Secret leakage: native secret mechanisms, sensitive HOME handling, bounded fingerprints only in doctor/evidence.
- Capability-policy duplication: inventory stores availability only; OR policy remains external.
- Build regressions: measured phase timing, persistent local cache, registry recovery cache and treated-as-defect unnecessary rebuilds.
- Session/runtime loss: recover from canonical Git/PW state and never blindly replay uncertain side effects.
- Mega-Card regression: preserve planned slices and split on independent mutation/rollback/evidence surfaces during Execution Prep.

## 9. Planning completion

P1 is complete when this exact plan has:

- full accepted-authority coverage;
- explicit milestone/dependency/gate strategy;
- bounded execution decomposition suitable for later stable Task Cards;
- no unresolved product decision hidden as an implementation assumption;
- GREEN planner audit;
- immutable Git subject frozen for independent Plan Review.

After freeze, Premium B requires a fresh independent best-available review context. The planning context that authored P1 must not perform that review.
