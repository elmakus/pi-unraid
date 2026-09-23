# Decision — Clean Pi + Paseo baseline and initial extension choices

- Decision ID: `PIE-ADR-001`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Related requirements: `requirements/PI_EXTENSION_TOOLING.md`
- Evidence: `research/PI_EXTENSION_EVALUATION_R1.md`

## Context

The project is moving from the Phase 1 minimal Pi bootstrap toward a later extension/tooling stack. The user explicitly chose clean Pi rather than a pre-bundled `pi-code`/OMP environment and selected Paseo as the primary GUI/Android remote.

The extension catalog contains overlapping workflow, memory, tool, MCP and subagent systems. Installing all of them would create duplicate authorities and unnecessary context/tool surfaces.

## Decision

Use **clean Pi + Paseo** as the baseline.

Include as accepted baseline candidates:
- `rpiv-ask-user-question`;
- `pi-permission-system`;
- `pi-lens`;
- loop detector / `pi-antiloop`;
- `pi-skill-gate`.

Do not select:
- `@narumitw/pi-lsp`;
- `pi-file-context`;
- `pi-btw`;
- `pi-zentui`;
- `pi-code`;
- Pi Desktop.

MCP capability is required, but the exact MCP adapter/client remains unresolved pending the current research/live validation boundary.

PWv2 remains current workflow authority. Findings about Fabric, Laya/System One, rpiv-todo, SpecPi, Dagu and subagent frameworks are prior art for a possible separately authorized PWv3 workstream; they do not modify PWv2 here.

## Rationale

- preserves Pi's small composable core;
- keeps Paseo as UI/remote rather than a competing workflow authority;
- avoids redundant LSP/context/TUI layers;
- preserves explicit user control over workflow evolution;
- allows later extensions to be added from evidence rather than bundle defaults.

## Consequences

- unresolved extension choices remain explicit rather than silently selected;
- future PWv3 work must preserve or explicitly redefine durable authority;
- live compatibility tests on the real Pi + Linux/Unraid + Paseo deployment remain required before finalizing some components.
