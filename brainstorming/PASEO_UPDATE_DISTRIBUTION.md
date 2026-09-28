# Brainstorm — automated Paseo/Pi updates and Unraid distribution

Date: `2026-09-28`
Scope ID: `paseo-update-distribution`
Revision: `R8`
Status: `active`

## Problem / goal

Design an extensible, inventory-driven update and distribution system for the production Paseo/Pi environment on Unraid. The system should automatically discover updates for current and future managed components, build and test one coordinated immutable candidate, distribute accepted images cleanly to Unraid, and preserve safe rollback/recovery semantics.

This record is exploratory state only. It preserves user choices from Brainstorming; Definition must promote accepted choices before they become canonical requirements/decisions.

## Accepted exploratory choices

1. Detection, candidate creation, PR creation, build and automated testing should run automatically after an update is discovered. Automation stops before production cutover: the user explicitly triggers the production update from the normal Unraid Docker UI when convenient.
2. Updates are coordinated as one complete environment candidate, but candidate resolution is compatibility-aware rather than all-or-nothing. The target is the newest compatible combination across all managed components. If one newly released component version is incompatible while another independent update is compatible, the compatible update may advance while the problematic component remains on its previous accepted version.
3. GHCR plus an Unraid Docker Template / Community Apps style UX is the preferred normal production distribution/management direction. Compose remains available for development, testing, recovery and fallback unless later evidence changes that decision.
4. Version discovery should run daily.
5. The update inventory must be extensible and data-driven rather than hard-coded to the initial component set. Adding a future supported tool/extension to inventory should enroll it in discovery/candidate lifecycle without creating a bespoke scheduler workflow.
6. Codex-LB end-to-end smoke uses a dedicated user-managed API key whose server-side policy forces a low-cost smoke model; normal agent credentials are not exposed to the update pipeline.
7. Production cutover must not be unattended because an automatic container restart could interrupt active Paseo/Pi agent work. Only a fully GREEN accepted image may become update-ready; the actual production restart/cutover is initiated by the user from the Unraid Docker UI.
8. Keep exactly two previous known-good production images available for rollback.
9. Do not add a separate candidate changelog/UX surface for now; keep the user-facing flow minimal.
10. If multiple accepted candidates accumulate before the user updates, expose only the newest accepted compatible candidate as the normal update target; intermediate accepted candidates do not need sequential installation.
11. Major versions do not receive a special product policy. They follow the same compatibility/build/test gates as any other version; avoid a separate major-version approval mechanism unless later evidence proves it necessary.
12. A user-triggered production update is one bounded transaction: if the newly started candidate fails its immediate post-update acceptance window, automatically roll back to the previous known-good image so Paseo is restored without requiring a second manual action. This automatic rollback applies only to the immediate update transaction; failures that appear after the candidate has already passed acceptance must not trigger an autonomous later rollback/restart.

## Current component set

- Paseo
- Pi
- SpecPi
- pi-mcp-adapter
- Playwright
- Chromium derived from Playwright
- GitHub CLI
- Docker CLI
- Docker Compose
- managed developer/base tooling

Future component classes may include npm packages/extensions, GitHub releases/binaries, OCI/container images, apt packages, pip/cargo packages and other explicitly supported resolvers.

## Open product decision

### Production promotion policy

Accepted exploratory direction: manual user-triggered production cutover from the normal Unraid Docker UI. Upstream release discovery, candidate resolution, CI build/tests, disposable validation and publication/update-readiness remain automated, but no automation may restart the production Paseo container merely because a new candidate became GREEN.

Preferred acceptance shape before the user sees an update-ready production image:

- GitHub/CI mechanical build and compatibility tests;
- a disposable candidate validation on Tower using the real production integration boundaries without mutating the active production container;
- one minimal real Codex-LB model round-trip using a separately configurable low-cost smoke-test model when available;
- only after those checks are GREEN, publish/promote the accepted image/tag that Unraid can detect as an available update;
- user chooses the safe moment and clicks Update in Unraid.

The Codex-LB smoke is an automated protocol/integration probe, not an LLM judgment. Use a dedicated smoke-test API credential created and managed by the user in Codex-LB. That credential should be constrained server-side to a low-cost smoke-test model (and, where supported, least-privilege limits such as bounded quota/rate/output). The update pipeline receives only this dedicated credential and does not get the user's normal agent credential. The test itself should use a tiny prompt/output budget. Research should verify the cleanest supported credential/model-binding mechanism and the exact Unraid update/readback/rollback realization.

### Compatibility-aware partial advancement

The resolver must maximize freshness subject to compatibility and acceptance constraints. A newly released version may be held back independently when it is incompatible or fails its required checks; unrelated compatible components should still be allowed to advance in the same coordinated candidate. Production still receives exactly one fully frozen, fully tested environment candidate.

### Post-update verification direction

After the user clicks Update, treat cutover plus immediate verification as one bounded transaction:

- start the new accepted image;
- run a short deterministic post-update acceptance window (health/readback and required runtime probes);
- GREEN -> commit the new runtime as the active known-good version;
- RED before acceptance -> automatically restore the immediately previous known-good image and verify that Paseo is healthy again.

This is recovery from the update the user explicitly initiated, not unattended update scheduling. Automatic rollback authority ends once the new candidate has passed its immediate acceptance window. A later unrelated runtime failure must not autonomously restart or roll back production, because agent work may already be active.

Research must determine the cleanest Unraid-native/bounded-host realization and how rollback status is exposed without adding a custom operational dashboard.

## Research trigger

After the remaining product choices are sufficiently bounded, route agent-findable implementation facts to formal Research. Candidate topics include Unraid DockerMan/Community Applications update semantics, CA Auto Update behavior, GHCR/tag strategy, health-gated rollback feasibility, extensible resolver/inventory design, and compatibility policy for coupled components.


## Formal Research reconciliation — R7

Integrated formal Research result:
`elmakus/project-research:projects/pi-unraid/production_updates/paseo_pi_update_distribution/FINAL_SYNTHESIS.md@f2b0bd9d1a9c4c0635ad73b80e5f87b71a5d12db`

The 12-lane Research wave found the selected direction feasible and refined the implementation boundary:

- DockerMan/Community Applications may remain the user-visible update-discovery surface and normal manual cutover gesture, but DockerMan is not itself a project transaction engine.
- Accepted production identity is the immutable OCI digest. One mutable GHCR channel such as `:accepted` signals only fully accepted updates to Unraid.
- The smallest architecture is hybrid: daily GitHub-hosted discovery/resolution/build/tests; exact-digest GHCR publication; narrow Tower-local disposable validation; then accepted-channel promotion.
- Tower validation includes production-shaped checks, exact direct state-transition proof and the real dedicated Codex-LB smoke. GitHub-hosted CI must not receive production secrets.
- A pre-armed durable Tower transaction guard must bind the user-triggered cutover to the exact candidate and exact previous known-good runtime, then commit GREEN or automatically rollback+verify on immediate RED.
- Automatic rollback authority ends after the immediate acceptance transaction reaches GREEN.
- Ordinary Update Ready requires a coherent disposable `A -> C -> A` proof against representative current persistent state. An irreversible migration that breaks rollback cannot use the ordinary update channel.
- Production rollback ledger is exactly: current + previous_1 + previous_2 immutable known-good digests. Registry/build retention may be broader.
- Direct skipping to the newest accepted candidate is allowed only when the actual current baseline -> newest candidate transition is explicitly proven.
- Resolver should use typed inventory/source adapters plus graph-aware newest-first bounded backtracking and narrowly scoped content-addressed known-bad facts. A universal SAT solver is not justified now.
- pi-mcp-adapter needs a deterministic local MCP fixture with an actual tool round-trip; command discovery alone is insufficient.
- Codex-LB server-side per-key model forcing/usage restrictions are verified by Research; the dedicated smoke key remains operator-managed.
- Existing resolver/build/smoke/HOME/staged-transaction assets are substantially reusable, while the legacy Git/Compose production updater should not remain the normal production path.

### Remaining owner decisions after Research

1. Freshness tie-break when multiple compatible environments are Pareto-maximal but incomparable.
2. Whether to allow one project/plugin `Update + Verify` action in Unraid if exact crash-safe binding to the stock DockerMan Update button cannot be proven on the installed version.
3. Operator settings for the dedicated Codex-LB smoke key: exact cheap model, quota/token/window limits and Tower-local secret placement.
4. Policy for a future desired release with an irreversible migration that cannot pass `A -> C -> A`.


## Owner decisions after Research — R8

Accepted:
- Freshness tie-break for incomparable Pareto-maximal candidates: minimize aggregate lag from newest available versions across managed independently versioned components, with equal component weight; use a deterministic technical tie-break only after equal aggregate lag.
- Preserve the stock Unraid Docker Update gesture when it can be bound safely to the pre-armed transaction guard; if target-version proof fails, allow one project/plugin `Update + Verify` action in Unraid rather than patching DockerMan or adding a dashboard.
- The user will provide a dedicated Codex-LB smoke API key. Key creation/model forcing/quota policy is operator-owned in Codex-LB; the update system only consumes the supplied dedicated secret.
- A desired future release that cannot pass rollback-safe `A -> C -> A` state proof is held out of the ordinary update channel and requires a separate explicit maintenance procedure.

### Compatibility complexity reduction — proposed classification

Do not put every versioned tool into combinatorial compatibility search. Use separate classes:

1. **Compatibility-search group** — solver may test alternate version combinations/backtrack:
   - Paseo + Pi + SpecPi + pi-mcp-adapter as the primary runtime/API/plugin compatibility group.
   - Node is not an independent choice; it is derived from the exact Paseo image and only checked against required runtime floors/constraints.

2. **Derived pair** — no independent combinatorial search:
   - Playwright + Chromium. Chromium is exactly derived from Playwright. Treat the pair as one version decision unit and run its browser smoke. If the newest Playwright pair fails, hold back that pair without recombining unrelated runtime components.

3. **Independent smoke-only components** — no cross-component combination search:
   - GitHub CLI;
   - Docker CLI;
   - Docker Compose.
   Resolve newest stable independently, install/build, run a small deterministic functional/version probe, and hold back only the failing component when necessary. Do not enumerate combinations with Paseo/Pi/SpecPi/MCP.

4. **Non-independent / repository-owned environment surfaces** — no upstream compatibility solver:
   - generic base tooling package graph;
   - Pi instruction plane / managed repository tree.
   These are validated as part of the image/runtime contract when repository/base-image changes occur, not independently version-searched by the update resolver.

Every final candidate still receives one whole-environment integration smoke. The classification controls only which components participate in compatibility backtracking/version-combination search; it does not remove basic verification from the final candidate.
