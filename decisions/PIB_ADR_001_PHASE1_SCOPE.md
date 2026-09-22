# Decision — Phase 1 is the minimal Pi bootstrap only

- Decision ID: `PIB-ADR-001`
- Date: `2026-09-22`
- Status: `accepted`
- Authority: `user`
- Supersedes: `none`
- Related requirements: `requirements/PI_UNRAID_BOOTSTRAP.md`
- Related milestone/card: `none`

## Context

Brainstorming explored a much broader desired end state: browser project/session UI, Android access, web research, subagents, MCP, browser automation, notifications, multiple providers/accounts and eventual Project Workflow-on-Pi use.

Implementing those before evaluating the base Pi harness would couple the bootstrap to unselected third-party extensions/frontends and make failures harder to attribute.

## Decision

The promoted Project Definition covers only **Phase 1: minimal Pi bootstrap on Unraid**.

Phase 1 proves the base Dockerized Pi runtime, persistent auth/session state, terminal/TUI access, Git/GitHub development environment and operational update/recovery behavior.

Web UI/mobile/extensions/provider expansion and Project Workflow-on-Pi integration are later Research/Definition scopes and are not part of the Phase 1 plan.

A prescribed coding benchmark is also not a Phase 1 workflow acceptance gate. After technical bootstrap acceptance, the user performs their own real-world Pi evaluation and decides whether follow-on scopes proceed.

## Rationale

- isolates evaluation of Pi itself from extension/frontend quality;
- prevents scope creep in the first implementation;
- preserves later optionality because overlapping Pi extensions still require bounded comparative research;
- matches the user's explicit G121/G124 choices.

## Alternatives considered

- Build the Web UI and core extensions in the first deployment: rejected for Phase 1 because it makes the evaluation dependent on still-unresearched components.
- Require a fixed Pi-vs-Codex benchmark before bootstrap acceptance: rejected by user authority; real-world evaluation remains user-owned after technical bootstrap.

## Consequences

- Planning MUST NOT add Web UI, Android, MCP, subagents, web search, browser automation or other later capability merely because it appears elsewhere in historical brainstorming.
- Phase 1 can complete with native terminal/TUI access.
- Follow-on component research begins only after the base bootstrap is available for the user's own evaluation.

## Required authoritative updates

- Requirements / Project Definition: captured in `requirements/PI_UNRAID_BOOTSTRAP.md`.
- Planning: must cover Phase 1 only.
- Task Card/OpenSpec: later, from approved plan.
- PROJECT.md: point to this accepted Definition and keep later scopes out of current plan.

## Provenance

- Source discussion/request: `brainstorming/PI_UNRAID_BRAINSTORM.md`, especially G86, G121, G124.
- Evidence/research: `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`.
- Strategic `request_id`: none.
- Exact `DECISION FOR CODEX:` marker: none.
- Persisting commit: recorded by Git history.
