# Research — M02 runtime lifecycle facts

Date: `2026-09-23`

## Durable continuation metadata

Research ID: `pi-unraid-m02-lifecycle-facts-r1`
Status: `active`
Origin role: `execution_prep`
Origin subject: `M02`
Return target: `execution_resolution:M02`
Return reconciliation: `pending`
Return reconciliation result: `none`

## Research question

Refresh the exact current Pi/Docker lifecycle facts needed to contract `M02 — Recoverable runtime and deployment lifecycle` without reopening accepted product intent.

Establish, from current upstream/official sources and disposable runtime evidence as needed:

- current stable Pi package/version discovery and Node engine compatibility needed for stable-only admission;
- Pi process/TUI signal and exit behavior relevant to bounded graceful stop of exec-launched active processes;
- native session persistence/resume facts relevant to preserving persisted state across planned stop/restart;
- package/runtime installation and activation seams that can support staged candidate validation, last-known-good retention and fallback without overwriting the only working runtime;
- Docker/Compose stop/timeout behavior relevant to explicit graceful-stop deadlines and escalation;
- Docker image/deployment retention and rollback/update mechanics needed for a host-operated previous-candidate path while preserving the existing home/projects/worktrees binds;
- exact fixture probes/failure-injection boundaries that are safe to run before M03, and which checks still require live credentials or target authorization.

The output must distinguish verified upstream facts, repository/runtime observations, implementation choices still delegated by the approved plan, and any finding that would require Planning/Definition rather than L1/L2 Execution Prep.

## Authority / predecessor inputs

- `planning/MASTER_PLAN.md#M02 — Recoverable runtime and deployment lifecycle`
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-014/015/017/020/021 and integrated M01 invariants
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `implementation/workstreams/feature-pi-unraid-bootstrap/handoffs/M01_HANDOFF.md`
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-acceptance.md`

## Findings

Pending.

## Sources / evidence

Pending.

## Assumptions / uncertainties

Pending.

Research is evidence, not accepted requirement/decision/plan authority.
