# Brainstorm — automated Paseo/Pi updates and Unraid distribution

Date: `2026-09-28`
Scope ID: `paseo-update-distribution`
Revision: `R1`
Status: `active`

## Problem / goal

Design an extensible, inventory-driven update and distribution system for the production Paseo/Pi environment on Unraid. The system should automatically discover updates for current and future managed components, build and test one coordinated immutable candidate, distribute accepted images cleanly to Unraid, and preserve safe rollback/recovery semantics.

This record is exploratory state only. It preserves user choices from Brainstorming; Definition must promote accepted choices before they become canonical requirements/decisions.

## Accepted exploratory choices

1. Detection, candidate creation, PR creation, build and automated testing should run automatically after an update is discovered. Production promotion policy remains under discussion.
2. Updates are coordinated as one complete environment candidate rather than independently mutating individual production components.
3. GHCR plus an Unraid Docker Template / Community Apps style UX is the preferred normal production distribution/management direction. Compose remains available for development, testing, recovery and fallback unless later evidence changes that decision.
4. Version discovery should run daily.
5. The update inventory must be extensible and data-driven rather than hard-coded to the initial component set. Adding a future supported tool/extension to inventory should enroll it in discovery/candidate lifecycle without creating a bespoke scheduler workflow.

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

Options currently under discussion:

- manual promotion: everything through GREEN is automatic, user clicks Update in Unraid;
- simple unattended promotion: Unraid automatically updates when a new accepted image/tag is published;
- guarded unattended promotion: accepted image is automatically deployed, post-deploy health/readback gates run, and the previous known-good image is automatically restored on failure.

Current recommendation pending user decision: guarded unattended promotion, provided Research confirms a clean Unraid-native or bounded host-side realization without weakening the existing rollback/recovery guarantees.

## Research trigger

After the remaining product choices are sufficiently bounded, route agent-findable implementation facts to formal Research. Candidate topics include Unraid DockerMan/Community Applications update semantics, CA Auto Update behavior, GHCR/tag strategy, health-gated rollback feasibility, extensible resolver/inventory design, and compatibility policy for coupled components.
