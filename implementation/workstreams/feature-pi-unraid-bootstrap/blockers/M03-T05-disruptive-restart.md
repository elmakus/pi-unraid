# M03-T05 disruptive restart authorization blocker

- Card: `M03-T05 — Production recovery, restart and final technical handoff`
- Date: 2026-09-23
- Status: **WAITING_USER_AUTHORIZATION**
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
