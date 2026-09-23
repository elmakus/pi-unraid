# Decision — Current ChatGPT authors Strategic Planning for Definition R2

- Decision ID: `PIB-ADR-006`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Supersedes: the Strategic Planner runtime assignment in `PIB-ADR-004` only
- Related requirements: `requirements/PI_UNRAID_BOOTSTRAP.md`
- Related milestone/card: remaining `M03` planning only

## Context

`PIB-ADR-004` assigned the Strategic Planning role for Phase 1 to Codex/Astra Max while keeping the project execution policy `chatgpt_only`.

Before the Definition R2 replan was authored, the user explicitly replaced that runtime assignment and directed the current normal ChatGPT session to perform the Strategic Planning work itself.

Project Workflow treats Strategic Planning as an authority role rather than a model-bound capability. The planner identity can therefore change without changing the accepted Phase 1 product/system target or the project execution policy.

## Decision

- Project execution policy remains `chatgpt_only`.
- Approved Project Definition remains `pi-unraid-bootstrap@R2`; no product/system requirement changes are introduced by this governance decision.
- The current normal ChatGPT session is authorized to author the new Strategic Planning revision for Definition R2.
- The prior requirement that this plan be authored by Codex/Astra Max is superseded.
- Independent Plan Review remains a fresh-session boundary: a fresh normal ChatGPT that did not author the exact reviewed plan subject performs that review.
- After plan approval, Execution Prep, Task Card execution, implementation review and Close continue under `chatgpt_only` unless the user later changes project authority again.

## Rationale

The user's latest explicit authority controls the planner assignment. Keeping the remainder of `PIB-ADR-004` intact preserves the established `chatgpt_only` lifecycle and independent-review separation without reopening the accepted product/system Definition.

## Alternatives considered

- Continue requiring Codex/Astra Max despite the explicit override: rejected because it conflicts with the user's latest authority.
- Change the entire project to `codex_only`: rejected because no such policy change was requested.
- Remove independent Plan Review: rejected because the user requested the replan to proceed to the required fresh independent Plan Review boundary.

## Consequences

- Strategic Planning may proceed immediately from Definition R2 in this session.
- `PIB-ADR-004` remains historical authority for the overall role/lifecycle split except for its superseded planner-runtime assignment.
- `PROJECT.md` and the selected workstream authority list must include this decision.
- The new Master Plan must identify ChatGPT as the strategic author and remain `draft` until independent Plan Review is GREEN and Planning consumes that verdict.
- This decision authorizes planning only; it does not authorize production deployment or any Tower live-write.

## Required authoritative updates

- Requirements: none; Definition R2 remains approved and GREEN.
- Decisions: add this record as the controlling planner-assignment override.
- PROJECT/workstream pointers: include this accepted decision and remove stale wording that requires Codex/Astra Max.
- Planning: author a new Definition-R2 Master Plan revision and required planner audit, then freeze it for fresh independent Plan Review.
- Task Cards: none from this Definition reconciliation.

## Provenance

- Source authority: user's explicit 2026-09-23 instruction that the current ChatGPT must perform the plan and that this overrides the earlier Codex/Astra Max decision.
- Persisting commit: recorded by Git history.
