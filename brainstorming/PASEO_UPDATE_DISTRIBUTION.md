# Brainstorm — automated Paseo/Pi updates and Unraid distribution

Date: `2026-09-28`
Scope ID: `paseo-update-distribution`
Revision: `R2`
Status: `active`

## Problem / goal

Design an extensible, inventory-driven update and distribution system for the production Paseo/Pi environment on Unraid. The system should automatically discover updates for current and future managed components, build and test one coordinated immutable candidate, distribute accepted images cleanly to Unraid, and preserve safe rollback/recovery semantics.

This record is exploratory state only. It preserves user choices from Brainstorming; Definition must promote accepted choices before they become canonical requirements/decisions.

## Accepted exploratory choices

1. Detection, candidate creation, PR creation, build and automated testing should run automatically after an update is discovered. Production promotion policy remains under discussion.
2. Updates are coordinated as one complete environment candidate, but candidate resolution is compatibility-aware rather than all-or-nothing. The target is the newest compatible combination across all managed components. If one newly released component version is incompatible while another independent update is compatible, the compatible update may advance while the problematic component remains on its previous accepted version.
3. GHCR plus an Unraid Docker Template / Community Apps style UX is the preferred normal production distribution/management direction. Compose remains available for development, testing, recovery and fallback unless later evidence changes that decision.
4. Version discovery should run daily.
5. The update inventory must be extensible and data-driven rather than hard-coded to the initial component set. Adding a future supported tool/extension to inventory should enroll it in discovery/candidate lifecycle without creating a bespoke scheduler workflow.
6. Production promotion should be guarded and unattended: only an accepted fully GREEN image may be promoted automatically; Tower then performs bounded post-deploy health/readback checks and automatically restores the previous known-good image if production acceptance fails.

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

Accepted exploratory direction: guarded unattended promotion. The update path must not deploy merely because an upstream release or a mutable image tag changed. It may deploy only a coordinated candidate that completed the required build/test/acceptance path. Production promotion then performs bounded post-deploy health/readback checks and automatically restores the previous known-good image if acceptance fails.

Research must determine the cleanest realization on Unraid (native DockerMan/CA mechanism versus a bounded host-side updater or hybrid) without weakening the existing rollback/recovery guarantees.

### Compatibility-aware partial advancement

The resolver must maximize freshness subject to compatibility and acceptance constraints. A newly released version may be held back independently when it is incompatible or fails its required checks; unrelated compatible components should still be allowed to advance in the same coordinated candidate. Production still receives exactly one fully frozen, fully tested environment candidate.

## Research trigger

After the remaining product choices are sufficiently bounded, route agent-findable implementation facts to formal Research. Candidate topics include Unraid DockerMan/Community Applications update semantics, CA Auto Update behavior, GHCR/tag strategy, health-gated rollback feasibility, extensible resolver/inventory design, and compatibility policy for coupled components.
