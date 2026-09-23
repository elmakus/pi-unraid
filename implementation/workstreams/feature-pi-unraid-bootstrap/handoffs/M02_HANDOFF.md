# M02 handoff — Recoverable runtime and deployment lifecycle

- Workstream: `feature-pi-unraid-bootstrap`
- Milestone: `M02`
- Status: **GREEN / complete**
- Final implementation head: `340121090f4b78ef3d2a3c1377d8bf5477026835`
- Integrated acceptance: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M02-acceptance.md`

## Achieved state

M02 now provides stable-only Pi runtime reconciliation with persistent LKG and image-seed fallback, managed native Pi shutdown with bounded escalation, and one host-operated update/rollback transaction. The update path uses fast-forward-only source movement, separate candidate verification, actual running healthy deployment identity, rendered-config retention, post-cutover health/runtime readback, and rollback without restoring persistent home/projects/worktrees.

All three M02 Cards are terminal and independently GREEN. Historical RED findings remain preserved in their review evidence and are closed by the terminal reviewed subjects.

## Authority in force

- `requirements/PI_UNRAID_BOOTSTRAP.md` R1
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `decisions/PIB_ADR_004_WORKFLOW_ROLES.md`
- `planning/MASTER_PLAN.md` R1
- `openspec/changes/m02-runtime-lifecycle/`

## Acceptance/readback

Close-time detached verification at the exact final implementation head passed the full disposable update/rollback verifier plus inherited M01 and M02-T01/T02 regression gates. Exact results are in `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M02-acceptance.md`.

## Deferred to M03

M02 does not claim live ChatGPT authentication persistence, authenticated Git/GitHub operations, production deployment/update/rollback, actual Unraid/Docker host restart, post-restart live session proof, or final workstation-independence acceptance. Those remain within approved M03.

## Next durable starting point

Return to the policy router for approved `M03 — On-target technical acceptance and handoff`. Execution Prep begins with read-only target readiness and derives the concrete deployment/test parameters from current target facts. Live deployment, authentication actions and restart operations remain behind the M03 authorization/readiness gates.
