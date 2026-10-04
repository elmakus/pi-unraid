# Brainstorm — automated Paseo/Pi updates and Unraid distribution

Date: `2026-10-04`
Scope ID: `paseo-update-distribution`
Revision: `R11`
Status: `promoted`

## Problem / goal

Design an extensible, inventory-driven update and distribution system for the production Paseo/Pi environment on Unraid. The system should automatically discover updates for current and future managed components, build and test one coordinated immutable candidate, distribute accepted images cleanly to Unraid, and preserve safe rollback/recovery semantics.

This record is exploratory state only. It preserves user choices from Brainstorming; Definition must promote accepted choices before they become canonical requirements/decisions.

## Accepted exploratory choices

1. Detection, candidate creation, PR creation, build and automated testing should run automatically after an update is discovered. Automation stops before production cutover: the user explicitly triggers the production update from the normal Unraid Docker UI when convenient.
2. Updates are coordinated as one complete environment candidate, but compatibility combination search is intentionally narrow: only the core Paseo↔Pi runtime pair participates in version backtracking, with Node derived from Paseo and checked only against Pi runtime constraints. Extensions and ordinary developer tools update independently; a failing newest version may remain on its previous accepted version without forcing unrelated components to roll back.
3. GHCR plus an Unraid Docker Template / Community Apps style UX is the preferred normal production distribution/management direction. Compose remains available for development, testing, recovery and fallback unless later evidence changes that decision.
4. Version discovery should run daily.
5. The update inventory must be extensible and data-driven rather than hard-coded to the initial component set. Adding a future supported tool/extension to inventory should enroll it in discovery/candidate lifecycle without creating a bespoke scheduler workflow.
6. Final validation uses a real Muse Spark 1.3 Contributor/max smoke through the mandatory guarded launcher and non-inference Codex-LB integration checks. Validation consumes only dedicated operator-controlled credentials in the disposable candidate boundary; normal agent credentials are not exposed to the update pipeline. R11 supersedes the earlier real Codex-LB/low-cost-model smoke requirement.
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
- one bounded real Muse smoke through the mandatory fixed-profile guarded launcher, plus authenticated Codex-LB metadata/auth/health checks without inference;
- only after those checks are GREEN, publish/promote the accepted image/tag that Unraid can detect as an available update;
- user chooses the safe moment and clicks Update in Unraid.

The real Muse smoke is a bounded protocol/runtime probe, not an LLM judgment. It must execute through the exact disposable candidate's Paseo/Pi path, with fixed provider/model/contribution and no fallback as required by the mandatory environment test policy. Codex-LB checks must not send inference requests. Dedicated validation credentials remain operator-controlled and available only to the disposable candidate boundary, never to GitHub CI, images, Git or evidence; ordinary agent credentials are not provided to the update pipeline. A missing credential, unavailable fixed profile or inability to bind the probe to the exact candidate blocks acceptance rather than weakening the gate.

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


## Owner decisions after Research — R8 (historical; smoke superseded by R11)

Accepted:
- Freshness tie-break for incomparable Pareto-maximal candidates: minimize aggregate lag from newest available versions across managed independently versioned components, with equal component weight; use a deterministic technical tie-break only after equal aggregate lag.
- Preserve the stock Unraid Docker Update gesture when it can be bound safely to the pre-armed transaction guard; if target-version proof fails, allow one project/plugin `Update + Verify` action in Unraid rather than patching DockerMan or adding a dashboard.
- The user will provide a dedicated Codex-LB smoke API key. Key creation/model forcing/quota policy is operator-owned in Codex-LB; the update system only consumes the supplied dedicated secret.
- A desired future release that cannot pass rollback-safe `A -> C -> A` state proof is held out of the ordinary update channel and requires a separate explicit maintenance procedure.

### Compatibility policy — accepted simplification

Compatibility combination search is intentionally narrow.

1. **Core compatibility gate**
   - Only Paseo and Pi participate in version-combination compatibility search.
   - Node is derived from the exact Paseo image and is checked only against the runtime/version constraints required by Pi.
   - The candidate must prove that the Paseo -> Pi RPC/provider path starts and works mechanically.

2. **Pi extensions are not compatibility-gating components**
   - SpecPi, pi-mcp-adapter and future ordinary Pi extensions do not participate in Paseo/Pi version backtracking.
   - Resolve/update each extension independently to its newest stable version.
   - If the newest extension cannot be fetched/installed/built at all, retain that extension's previous accepted version without blocking unrelated component updates.
   - If it installs but later exposes an extension-specific functional problem, that problem does not by itself block the core Paseo/Pi update channel.
   - Extension-specific failures may be diagnosed during normal use unless later evidence shows a particular extension can destabilize the core runtime strongly enough to justify promotion into the compatibility gate.

3. **Derived components**
   - Chromium remains derived from the selected Playwright version. Treat Playwright+Chromium as one update unit, not a combinatorial compatibility group.
   - Run only the browser/build smoke needed to prove that selected pair is usable.

4. **Independent tools**
   - GitHub CLI, Docker CLI, Docker Compose and future ordinary developer tools do not enter cross-component version search.
   - Update independently; require install/build success and only a small deterministic functional/version probe where justified.
   - A failing newest version may fall back to that tool's previous accepted version without causing unrelated components to roll back.

5. **Whole-image sanity**
   - Every final candidate still has one bounded whole-environment smoke for core startup/invariants.
   - This is not permission to turn optional extension/tool functionality into a blocking compatibility matrix.

### Managed component registry lifecycle

The update inventory/managed-component registry is the durable source of truth for what the image intentionally carries and what the update system must track.

- Adding a managed Pi extension must add its registry/inventory entry in the same managed change that adds the extension to the image/runtime declaration.
- Adding a managed developer tool must likewise add its registry/inventory entry in the same managed change.
- Removing a managed extension/tool from the image/runtime declaration must remove its registry/inventory entry in the same managed change.
- The add/remove workflow must be transactional at repository level: no accepted state may intentionally contain "installed but not registered" or "registered but no longer installed".
- Build/readback validation must detect registry/runtime drift and fail the managed change rather than silently adopting it.
- Future managed components default to the least complex update class:
  - ordinary Pi extension -> independent extension update, non-core compatibility gate;
  - ordinary developer tool -> independent tool update;
  - derived artifact -> follows its owning component;
  - only a component with demonstrated core startup/API coupling may be promoted into the Paseo/Pi compatibility-search group.
- Experimental or ad-hoc live changes inside a running container are not durable registration events. To keep a component, it must be adopted through the managed add path so the repo declaration and registry become authoritative together.

The intended operator/agent UX is a single managed add/remove operation rather than editing two unrelated files manually. The exact CLI/helper shape belongs to Definition/Planning, but it must update both installation intent and registry membership atomically and then rely on the normal candidate build/update pipeline.


### Agent-operated managed component lifecycle — R10

The human operator does not need to invoke component-management helpers directly.

- The normal user interaction is natural-language intent to the coding agent, e.g. "install this Pi extension", "add this developer tool", or "remove this component".
- The agent must route every durable managed install/remove through the project-owned managed-component helper/workflow.
- The helper is an implementation contract for agents, not a required user-facing CLI workflow.
- A durable add operation must atomically update installation intent plus registry/inventory membership and then enter the normal candidate build/test/update pipeline.
- A durable remove operation must atomically remove installation intent plus registry/inventory membership and then enter the same pipeline.
- Agents must not implement a durable managed change by directly editing only the image/Dockerfile/package install command while skipping registry lifecycle.
- Direct live-container installation is permitted only as explicitly temporary experimentation/diagnosis; it is not durable state and must not silently become managed inventory.
- Definition/Planning should provide machine-checkable guidance/tests so an agent can discover and use the correct helper automatically without the user needing to remember registry mechanics.


## Final challenge audit — R10 (historical)

Status: **GREEN**

The completion challenge found no remaining material product/strategy decision and no contradiction that requires owner input.

Reconciled points:
- the earlier broad phrase "newest compatible combination across all managed components" is superseded by the accepted R9/R10 rule that only Paseo<->Pi participates in compatibility combination search;
- SpecPi, pi-mcp-adapter, future ordinary Pi extensions and developer tools remain independently updated managed components, not core compatibility gates;
- optional extension/tool malfunction does not block core Update Ready merely because its feature later fails during normal use, provided the final candidate still satisfies core startup/invariant checks;
- durable add/remove operations are agent-operated through the managed-component lifecycle so installation intent and registry membership cannot intentionally drift;
- Research recommendations for stronger extension-specific compatibility probes are historical evidence and do not override the later explicit owner decision to keep those probes outside the blocking compatibility gate;
- Codex-LB smoke key provisioning remains an operator prerequisite at implementation/deployment time, not an unresolved Brainstorming choice;
- irreversible future persistent-state migration remains a separately handled maintenance class rather than weakening the ordinary rollback contract.

No additional adaptive-grilling round had material expected decision value at R10. Its promotion subject was `paseo-update-distribution@10`.

## Accepted validation correction and promotion — R11

On 2026-10-04 the user explicitly approved the bounded correction proposed at the M08-T01 authority stop: real inference validation through the mandatory Muse Spark/max guarded path, with Codex-LB validation restricted to non-inference checks. This approval applies to this exact R11 scope delta; it is not approval for production restart, cutover, inference-policy bypass, or later premium gates.

Unchanged: daily GitHub-hosted preparation; immutable build-once/GHCR identity; Tower disposable validation; no ordinary-agent credentials in the update pipeline; direct A -> C -> A state-transition proof; exact transaction-guard pre-arm before accepted-channel exposure; user-chosen Unraid cutover; bounded immediate RED rollback and cessation after GREEN; current plus exactly two previous known-good identities; narrow compatibility search and managed-component lifecycle.

Final challenge audit: **GREEN**. The earlier unresolved smoke-provider choice is now resolved. Credential admission, exact candidate-bound launcher realization, profile availability and actual test results are implementation/acceptance inputs, not waived gates or claims of success. The exact authorized promotion subject is `paseo-update-distribution@11`; Definition R2 owns conversion into requirements/decision authority.
