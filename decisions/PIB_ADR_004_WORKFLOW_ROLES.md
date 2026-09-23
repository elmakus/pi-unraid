# Decision — ChatGPT-only workflow with Codex/Astra Max as Strategic Planner

- Decision ID: `PIB-ADR-004`
- Date: `2026-09-22`
- Status: `accepted`
- Authority: `user`
- Supersedes: `none`
- Related requirements: `requirements/PI_UNRAID_BOOTSTRAP.md`
- Related milestone/card: `none`

## Context

Project Workflow distinguishes authority roles from model identities. The user wants normal ChatGPT to own discovery/Definition and downstream execution/review lifecycle, but wants the Strategic Planning role for this Phase 1 Definition authored by Codex using Astra Max.

Selecting a planning runtime does not need to switch the entire project execution policy to `codex_only`.

## Decision

- Project execution policy remains `chatgpt_only`.
- ChatGPT owns Brainstorming, pre-Definition Research and Project Definition.
- **Codex/Astra Max** authors the Strategic Planning role for this Phase 1 subject.
- A fresh normal ChatGPT performs independent Plan Review.
- After an approved plan, Execution Prep, Task Card execution, implementation review and Close return to ChatGPT under `chatgpt_only`, unless the user later explicitly changes project execution policy.

## Rationale

This uses the user's preferred stronger planner while retaining the fixed ChatGPT execution/review workflow and its independent-review semantics. Project Workflow explicitly treats roles as authority roles rather than prescribed model identities.

## Alternatives considered

- Switch project to `codex_only`: rejected because the user wants Codex only for planning, not review/execution.
- Keep Strategic Planning in the current ChatGPT session: rejected by user preference for Astra Max planning.

## Consequences

- Definition must stop before authoring the Master Plan.
- The next planning handoff must clearly identify the approved Definition and selected workstream, while the planner reconstructs authority from repository state.
- The Codex planning chat cannot issue its own independent plan-review verdict.
- Independent Plan Review returns to a fresh normal ChatGPT session.

## Required authoritative updates

- Requirements / Project Definition: no product behavior change; governance preserved here and in `PROJECT.md`.
- Planning: Codex/Astra Max is the requested authoring runtime.
- Task Card/OpenSpec: execution remains ChatGPT-only unless explicitly changed later.
- PROJECT.md: preserve execution policy and planner assignment.

## Provenance

- Source discussion/request: G122 and user's explicit correction after completion audit.
- Evidence/research: Project Workflow common authority + `workflow/chatgpt_only/PLANNING.md` semantics.
- Strategic `request_id`: none.
- Exact `DECISION FOR CODEX:` marker: none.
- Persisting commit: recorded by Git history.
