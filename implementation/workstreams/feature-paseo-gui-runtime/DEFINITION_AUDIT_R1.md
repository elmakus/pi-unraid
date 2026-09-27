# Paseo GUI Runtime — Definition R1 Completeness Audit

Date: 2026-09-24
Workstream: `feature-paseo-gui-runtime`
Promoted source: `paseo-gui-runtime@2`
Definition revision: `R1`
Verdict: **GREEN**

## Subject integrity

- Exact promoted Brainstorming subject: `paseo-gui-runtime@2`.
- Brainstorming challenge/completion audit: GREEN.
- Cross-project authority corrections CP-01…CP-04 are incorporated before Definition.
- Definition Research `current-runtime-integration-facts` is complete, applied and consumed.
- Requirements contain 87 unique contiguous IDs: `PGR-REQ-001` through `PGR-REQ-087`.
- Accepted decisions:
  - `ADR-PGR-001` runtime/UI substrate;
  - `ADR-PGR-002` PW/OR/pi-unraid authority boundaries;
  - `ADR-PGR-003` Unraid administration/safety;
  - `ADR-PGR-004` update/build/rollback architecture.

## Promoted-scope coverage

| Brainstorm area | Definition coverage |
|---|---|
| A — UX / primary entry | PGR-REQ-001…003, 008…010 |
| B — container/runtime | PGR-REQ-004…007, 085; ADR-PGR-001 |
| C — filesystem/persistence | PGR-REQ-011…013, 038 |
| D — Relay/network access | PGR-REQ-014…016 |
| E — health/backup/recovery | PGR-REQ-065, 071…080, 085 |
| F — tooling/browser | PGR-REQ-021…026; ADR-PGR-001 |
| G — extensions/skills/MCP | PGR-REQ-027…035, 086…087 |
| H — sessions/agents/OR boundary | PGR-REQ-036…040, 076…081; ADR-PGR-002 |
| I/K — Git/worktree safety | PGR-REQ-038, 041…044 |
| J — conversation reconciliation | incorporated into the owning requirement groups rather than duplicated |
| L/M/N — update/full Unraid administration/safety | PGR-REQ-045…070; ADR-PGR-003/004 |
| O — project onboarding/dependencies/caches/temp services | PGR-REQ-013, 025…031, 055, 067…070, 084 |
| P — instruction plane/PWv2.1 integration | PGR-REQ-032…035, 036…044, 082 |
| Q — capability inventory/doctor/reconcile | PGR-REQ-027…031, 071…074 |
| R — secrets/auth/browser/Relay | PGR-REQ-014…020, 022…024 |
| S/T/U/V — image/update/latest/cache | PGR-REQ-055…070; ADR-PGR-004 |
| W — observability/recovery UX | PGR-REQ-071…080 |
| X — deterministic resolution/final acceptance | PGR-REQ-057…070, 078…085 |

## Cross-project authority audit

GREEN after correction:

- PW owns managed legality, durable workflow state, review semantics and user stops.
- OR owns runtime scheduling, worker/session/tool assignment and concrete worktree realization.
- pi-unraid owns environment availability, deployment, workspace substrate and host administration.
- Environment Capability Inventory and OR Tool Registry are explicitly non-duplicative.
- Pi-owned guards are restricted to environment/host safety.
- Future PWv2.1 workflow-extension semantics remain PW-owned.
- The generic cross-runtime ad-hoc Git rule still lacks a universal owner, but this is not an unresolved product choice inside this Definition: direct Main/Pi behavior is fully specified locally, while universal ownership is explicitly outside current scope.

## Research reconciliation

Definition Research produced no new user/product decision. It narrowed implementation facts only:

- official Paseo stable GHCR base + Pi installed in the child image;
- GraphQL-primary / SSH-fallback Unraid administration;
- configurable Paseo worktree root outside protected HOME;
- effective Unraid-compatible host ownership without overriding the official internal-user contract blindly;
- server-side Chromium/Playwright remains required because current Paseo Browser Tools are desktop-hosted;
- SpecPi and pi-mcp-adapter require exact-candidate compatibility smoke;
- GHCR and BuildKit local/registry cache are valid implementation substrates.

Live runtime facts that cannot exist until deployment (Relay persistence, exact permissions, browser/MCP execution, host-control failover, volume ownership) are acceptance/readback obligations, not unresolved Definition choices.

## Completeness result

- Material unresolved user/product questions inside the accepted scope: **none**.
- Missing authority needed for Strategic Planning: **none**.
- Known deferred work is explicitly scoped:
  - OR integration starts only after base Paseo/Pi is GREEN;
  - future PWv2.1 Pi-extension packaging starts after PWv2.1's final contract stabilizes;
  - universal cross-runtime ownership of the generic ad-hoc Git invariant is outside this Definition.
- Definition R1 is complete and may transition to GREEN with Premium stop A due.
