# M03-T05 disruptive restart authorization blocker

- Card: `M03-T05 — Production recovery, restart and final technical handoff`
- Date: 2026-09-23
- Status: **RESOLVED BY USER AUTHORITY CHANGE — restart not executed**
- Origin: M03-T05 execution after all currently authorized non-disruptive recovery checks passed

## Completed before this gate

The bounded M03-T05 production-recovery scope authorized on 2026-09-23 is GREEN. Canonical partial evidence:
`implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T05-partial.md`.

Production is currently healthy on the current M03-T05 source/image, Codex-LB provider health is GREEN, the native session remains resumable, and the workstation remains unchanged.

## Authorization required

The Card and approved M03 plan require one separate disruptive restart window to verify automatic recovery.

Authorize **one of the Card-permitted broad restart checks**:
- Docker-wide restart; or
- Unraid host restart.

The operation will include exact pre-restart state capture and post-restart readback for:
- Pi restart-policy recovery and runtime/provider health;
- persisted native Pi session;
- Codex-LB recovery/persistence;
- `chatgpt-ce-workstation` observation/independence;
- final M03 requirement/acceptance coverage.

No disruptive restart is performed until this explicit authorization is received.

## Resolution

On 2026-09-23 the user explicitly chose to skip the disruptive restart. No Docker-wide or Unraid host restart was executed. The change is captured by `PIB-ADR-007` and Definition R3; downstream plan/execution state must be reconciled under that new authority rather than treating this gate as passed.
