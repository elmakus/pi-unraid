# Independent Plan Review — Paseo/Pi Update Distribution P1 / R01

Plan revision: `P1`  
Planning cycle: `1`  
Workstream: `feature-paseo-update-distribution`  
Branch: `feat/paseo-update-distribution`  
Review state: `red`  
Reviewed subject: `elmakus/pi-unraid@077097ac2a0f5f3c01b42cf59f7536fecac69211:planning/PASEO_UPDATE_DISTRIBUTION_P1.md@b0441ddcd9b95e3d4b44ce7d81bd397953320e51`

## Independence

R01 was performed in the fresh independent review context entered for Premium B / independent Plan Review.
The reviewer did not materially author or repair the exact frozen P1 subject.

## Authority checked

- `requirements/PASEO_UPDATE_DISTRIBUTION.md` R1 / Definition `paseo-update-distribution@10`
- `decisions/ADR_PUD_001_DISTRIBUTION_AND_CUTOVER.md`
- `decisions/ADR_PUD_002_MANAGED_COMPONENT_LIFECYCLE.md`
- `decisions/ADR_PUD_003_ROLLBACK_SAFE_PROMOTION.md`
- inherited `requirements/PASEO_GUI_RUNTIME.md` where non-conflicting
- inherited `decisions/ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md` where non-conflicting
- current Project Workflow V2 Planning and Independent Plan Review contracts

## Findings

### Accepted-channel / transaction-guard ordering — RED

`PUD-REQ-026` requires the durable Tower transaction guard to bind the exact candidate digest,
the exact previous known-good deployment and rollback anchor **before exposing a candidate through
the accepted channel**.

P1 does not preserve that ordering:

- M05-T01 implements the accepted-channel promotion writer before M06-T01 implements the durable
  transaction-guard state machine.
- Gate G5 explicitly places accepted-channel/ledger/pre-arm work before the M06 transaction-guard
  production binding.
- Most importantly, M08-T02 orders the real production sequence as: rerun final gates -> move
  `:accepted` -> verify Unraid Update Ready -> arm the transaction guard before user cutover.
  That allows real accepted-channel exposure before the durable guard is armed, which is contrary
  to PUD-REQ-026.

This is not cured by M05-T03's "pre-arm contract": the binding requirement is a durable live guard
binding for the exact candidate/predecessor/rollback anchor before production accepted-channel
exposure, not merely a contract or ledger prepared for later M06 realization.

### Codex-LB / accepted-channel boundary — clarification required in the same correction

`PUD-REQ-020`, `PUD-REQ-021` and ADR-PUD-003 make the dedicated real Codex-LB smoke part of the
required Tower acceptance before a candidate becomes normally update-ready. P1 correctly defers the
real key/smoke to M08-T01 and has M08-T02 as the final real accepted-channel exposure. Therefore any
M05 accepted-channel movement must be explicitly non-production/simulated test evidence and must not
move the production `:accepted` tag. P1 currently says M05-T01 "moves `:accepted`" after
GitHub+Tower GREEN even though M04/M07 use fixture credentials, leaving the production-vs-test
boundary insufficiently fail-closed.

## Required correction class

Material planning/gate correction:

1. Make all M05 accepted-channel exercises explicitly disposable/non-production, or otherwise
   guarantee that the production `:accepted` tag cannot move there.
2. Before the first real production `:accepted` movement, durably arm/bind the transaction guard
   to exact candidate digest + previous known-good + rollback anchor.
3. Keep the real dedicated Codex-LB smoke and other required final Tower gates before that same real
   accepted-channel movement.
4. Update M05/M06/M08 ordering and G5/G8 wording so there is one unambiguous executable sequence.

Because the defect changes a safety gate ordering and the prior subject has no GREEN Plan Review,
this is not an editorial exemption and requires a new material planning cycle.

## Verdict

**RED.**

P1 has a material accepted-channel safety-ordering defect against PUD-REQ-026. The exact frozen P1
subject must remain immutable; Planning must create a new material cycle/revision rather than repair
P1 in place.
