# Research — Pi → Codex-LB Phase 1 integration facts

Research ID: `pi-unraid-codex-lb-integration-r1`
Status: `active`
Origin role: `project_definition`
Origin subject: `pi-unraid-bootstrap@R2`
Return target: `project_definition:pi-unraid-bootstrap@R2`
Research question: `Determine the current, source-grounded Pi → Codex-LB integration contract needed for Phase 1: provider/protocol compatibility, OAuth persistence and refresh ownership, multi-account behavior, failure/fallback semantics, and the correct Unraid deployment topology from the first real production start, including whether/how the existing Tower Codex-LB deployment can be used without violating Pi persistence/security/workstation-independence invariants.`
Return reconciliation: `pending`
Return reconciliation result: `none`

## Trigger / authority

The user explicitly changed Phase 1 product/system authority before the first production deployment:

- Phase 1 must use Codex-LB as the ChatGPT/Codex OAuth access layer from the first real Pi run.
- Direct Pi → built-in ChatGPT OAuth is no longer the required or intended bootstrap path.
- Codex-LB is no longer a Phase 1 non-goal.
- Existing completed M01/M02 checkpoints and evidence remain historical truth and must not be rewritten.
- No production deployment may proceed under the old M03-T01 authority.

## Evidence needed

Research must establish, using current upstream/primary sources and read-only target facts where material:

1. the exact Pi provider/API shape that can target Codex-LB;
2. which component performs ChatGPT/Codex OAuth login, token storage and refresh;
3. where Codex-LB persists credentials/account state and what Pi itself must persist;
4. actual multi-account selection/pooling/failover behavior and any user-visible constraints;
5. required network endpoint/model/provider configuration between Pi and Codex-LB;
6. startup/readiness/failure semantics relevant to Phase 1 acceptance;
7. the correct target topology on Tower, including the already-running Codex-LB instance if reusable;
8. security/isolation implications, backup surface and workstation-independence;
9. which old R1 requirements/acceptance outcomes/plan statements become invalid and what exact authority needs R2 replacement.

Research is evidence only. Product/system acceptance remains owned by Project Definition R2.
