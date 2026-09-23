# Decision — Adopt SpecPi core as the Pi-wide harness improvement layer

- Decision ID: `PIE-ADR-003`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Related requirements: `requirements/PI_EXTENSION_TOOLING.md`
- Evidence: `research/PI_EXTENSION_EVALUATION_R1.md`

## Context

The desired capability-gap mechanism must apply to the whole Pi harness rather than being embedded inside Project Workflow.

Current SpecPi provides an opt-in/local Harness Improvement Loop where Pi may record recurring capability gaps and the user later selects one for a bounded harness-improvement workflow. Observation alone does not authorize a change.

Current SpecPi also offers a default base that installs eight pinned supporting packages, including web access, delegation, goals and permissions. Several of those overlap with choices still being evaluated independently in this project.

## Decision

Adopt **SpecPi core** as the Pi-wide capability-gap / harness-improvement layer.

Initial installation MUST use SpecPi's supported `--skip-package-install` mode so that only SpecPi's own core scope/improvement-loop behavior is adopted without automatically installing its eight-package base.

SpecPi is not the Project Workflow authority. It may:
- observe and record Pi-wide harness friction/capability gaps;
- present those gaps for later human selection;
- execute a separately authorized bounded harness improvement.

It MUST NOT:
- treat a reported gap as authorization to self-modify;
- change Project Workflow durable state merely because a gap was observed;
- silently install or select overlapping extensions that remain under separate project decisions.

## Consequences

- capability learning belongs to the whole Pi environment rather than PWv2/PWv3;
- the project's explicit extension choices remain authoritative;
- SpecPi's bundled packages remain useful prior art and may be selected individually later;
- future PWv3 may consume promoted harness findings, but it does not own the collection loop.
