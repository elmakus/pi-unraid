# M01 handoff — Reproducible non-root development environment

- Workstream: `feature-pi-unraid-bootstrap`
- Milestone: `M01`
- Status: **GREEN / complete**
- Final implementation head: `d016731a276e33f09b9a23df682951e89b21c8dc`
- Integrated acceptance: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-acceptance.md`

## Achieved state

The branch now carries the accepted M01 foundation:

- reproducible Node 24 / Pi 0.87.1 base image with required development tooling;
- non-root Compose runtime with persistent `/home/pi`, canonical `/projects` and `/worktrees` mounts, configurable UID/GID, sudo, timezone/restart/logging safeguards and safe existing-home behavior;
- native Pi/TUI operator path with explicit cwd;
- persistent Git identity plus strict GitHub.com host trust from tracked official keys;
- disposable repository + linked-worktree fixtures proving metadata, cwd and ownership behavior.

All three M01 Cards are terminal and independently GREEN. The original M01-T03 RED SSH-config finding is preserved in history and corrected by the reviewed subject.

## Authority in force

- `requirements/PI_UNRAID_BOOTSTRAP.md` R1
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `decisions/PIB_ADR_004_WORKFLOW_ROLES.md`
- `planning/MASTER_PLAN.md` R1

## Material boundaries / deferred work

M01 uses disposable fixtures only. It does not claim:

- live ChatGPT OAuth or persisted authenticated Pi session acceptance;
- authenticated Git/gh operations on a live authorized remote;
- actual Unraid/Docker host-restart acceptance;
- latest-stable runtime update/fallback, graceful active-Pi shutdown or external image/deployment rollback.

Those are intentionally owned by M02/M03.

## Next durable starting point

Return to the policy router. The next approved milestone is `M02 — Recoverable runtime and deployment lifecycle`.

Execution Prep must use this M01 handoff plus exact M01 evidence as predecessor truth, refresh current Pi/runtime facts, and create only the deterministic M02 Cards that can now be contracted. No live deployment or credentials are authorized by this handoff.
