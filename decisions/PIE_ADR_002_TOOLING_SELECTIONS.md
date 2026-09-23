# Decision — MCP, exclusions and Pi-wide capability feedback

- Decision ID: `PIE-ADR-002`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Related requirements: `requirements/PI_EXTENSION_TOOLING.md`
- Evidence:
  - `research/PI_EXTENSION_EVALUATION_R1.md`
  - `research/PI_BLACKHOLE_MEMORY_FACTS_R1.md`

## Decision

### MCP

Select `pi-mcp-adapter` as the primary MCP adapter for the clean Pi + Paseo stack.

The adapter selection remains subject to live validation of:
- Paseo agent-scoped MCP injection on Linux/Unraid;
- secret/OAuth behavior;
- interaction with `pi-permission-system`;
- MCP restrictions for future subagents.

### Explicit exclusions

Do not install/select as baseline:
- `rpiv-todo`; its dependency/cycle/progress ideas may still inform future workflow UX;
- Plannotator;
- `pi-github-pr`.

### Capability-gap / harness-improvement loop

The desired capability-gap mechanism belongs to the **whole Pi harness**, not inside Project Workflow.

SpecPi's existing wishlist/harness-improvement loop is useful prior art and a possible implementation candidate, but this decision does not yet select the whole SpecPi stack.

A Pi role may report a missing capability. Reporting the gap MUST NOT itself authorize changing the harness. Promotion to an actual harness change remains a separate controlled action.

### Future workflow research

Keep the following as future research, not current baseline deployment choices:
- deterministic external workflow-engine patterns such as Dagu;
- Pi-native subagent runtimes/frameworks;
- a separately authorized PWv3 redesign;
- refactoring/optimizing the separate `codex_workflow` runtime for Pi-native operation and bounded subagent context.

## Consequences

- MCP architecture can now be planned around one adapter rather than comparing multiple clients indefinitely.
- Context7 is not a blocker for the current stack; it can use the user's alternate delivery method later if needed.
- Pi-wide harness learning and Project Workflow authority remain separate concerns.
- PWv3/codex_workflow work must not be smuggled into this extension deployment workstream.
