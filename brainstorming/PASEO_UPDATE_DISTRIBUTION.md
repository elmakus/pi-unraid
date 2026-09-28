# Brainstorm — automated Paseo/Pi updates and Unraid distribution

Date: `2026-09-28`
Scope ID: `paseo-update-distribution`
Revision: `R5`
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

After the user clicks Update and the new container starts, perform a bounded mechanical health/readback check. Do not automatically trigger another production restart merely because that post-update check fails. The exact user-visible failure/rollback mechanism remains open for Research because it depends on what Unraid DockerMan can expose cleanly without adding a custom operational UI.

## Research trigger

After the remaining product choices are sufficiently bounded, route agent-findable implementation facts to formal Research. Candidate topics include Unraid DockerMan/Community Applications update semantics, CA Auto Update behavior, GHCR/tag strategy, health-gated rollback feasibility, extensible resolver/inventory design, and compatibility policy for coupled components.
