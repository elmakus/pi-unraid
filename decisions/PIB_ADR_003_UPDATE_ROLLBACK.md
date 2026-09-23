# Decision — Latest-stable-on-start with safe runtime and image rollback

- Decision ID: `PIB-ADR-003`
- Date: `2026-09-22`
- Status: `accepted`
- Authority: `user`
- Supersedes: `none`
- Related requirements: `PIB-REQ-013..017, PIB-REQ-020`
- Related milestone/card: `none`

## Context

The user prefers Pi freshness rather than a permanently pinned runtime, including checking for the newest stable Pi on normal service startup. That preference must not make a bad upstream release or broken image render the service unavailable or destroy persistent state.

## Decision

- On service/container startup, target the latest **stable** Pi release.
- Do not automatically consume beta/nightly/prerelease channels.
- If the newly selected Pi runtime cannot be installed or started successfully, fall back to the last known working Pi runtime.
- Separately preserve a previous known-working Docker image/deployment candidate for rollback of Dockerfile/dependency/startup failures.
- Runtime/image rollback must preserve persistent Pi home, repositories and worktrees.
- Provide one normal user-facing update operation for repository/image/deployment maintenance.
- Bound log growth through rotation/retention.

## Rationale

This preserves the user's explicit freshness preference while separating durable state from replaceable runtime/image layers and keeping ordinary restart/update failures recoverable.

## Alternatives considered

- Update only when rebuilding the image: explicitly rejected by the user in favor of update-on-start.
- Fail closed when newest Pi is broken: rejected; availability/fallback is required.
- Track prerelease/nightly automatically: rejected.
- Let logs grow indefinitely: rejected.

## Consequences

- Strategic Planning must design an actual last-known-good mechanism rather than merely running an unconditional package update in the startup command.
- Runtime fallback and Docker-image rollback are distinct mechanisms.
- Tests/evidence must prove persistence survives rollback paths.
- Exact retention/update mechanics are planning/implementation choices, not reopened product decisions.

## Required authoritative updates

- Requirements / Project Definition: captured in `requirements/PI_UNRAID_BOOTSTRAP.md`.
- Planning: must define runtime-version activation/fallback, image rollback and update workflow.
- Task Card/OpenSpec: later.
- PROJECT.md: point to this decision.

## Provenance

- Source discussion/request: G16/G46/G53/G96/G98/G105/G119.
- Evidence/research: current Pi runtime facts in `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`.
- Strategic `request_id`: none.
- Exact `DECISION FOR CODEX:` marker: none.
- Persisting commit: recorded by Git history.
