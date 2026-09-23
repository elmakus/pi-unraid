# Decision — Skip disruptive restart as a Phase 1 acceptance exercise

- Decision ID: `PIB-ADR-007`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Supersedes: the R2 requirement that Docker-wide/host restart be executed before Phase 1 technical completion
- Related requirements: `PIB-REQ-013`
- Related milestone/card: `M03 / M03-T05`

## Context

M03-T05 completed the authorized non-disruptive production recovery checks and reached the separate gate for a Docker-wide or Unraid host restart. The user explicitly chose: **skip that restart**.

The production deployment already has the accepted `unless-stopped`-style restart policy and `Europe/Zurich` timezone configured/read back, but a Docker-wide or host restart has not been executed as part of this project.

## Decision

- Phase 1 does not require performing a Docker-wide restart, Unraid host restart, or similarly broad interruption as an acceptance exercise.
- Do not claim that broad restart recovery was tested.
- Retain the intended automatic restart configuration requirement: the Pi production service remains configured with `unless-stopped`-style behavior and `Europe/Zurich`.
- Accept the residual risk that the broad restart path is not live-verified in Phase 1.
- Preserve all already-completed M03-T05 update, runtime-fallback, rollback, graceful-stop/session-resume, Codex-LB outage/restart, logging/security and workstation-independence evidence.
- Remove the disruptive-restart authorization gate from the remaining Phase 1 completion path.
- Later real-world restart observation may be recorded opportunistically, but it is not a blocker for Phase 1 completion.

## Consequences

- Project Definition advances to R3 because an acceptance-level outcome and authorization boundary changed.
- Strategic Planning must revise the remaining M03 completion strategy and remove the mandatory disruptive-restart proof.
- Existing M03-T05 evidence remains historical/valid; downstream execution state must be reconciled rather than rewriting that evidence as if the restart occurred.
- Final technical handoff must state explicitly that Docker-wide/host restart recovery was not live-tested.

## Provenance

- Explicit user direction on 2026-09-23: `Pomijamy ten restart`.
