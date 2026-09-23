# Pi extension/tooling stack

Revision: `R1`
Status: `draft`
Updated: `2026-09-23`

Definition subject: `pi-extension-tooling-selection@R1`
Workstream: `change-pi-extension-evaluation`
Verified research: `research/PI_EXTENSION_EVALUATION_R1.md`

## Goal

Define the follow-on Pi capability stack for a **clean Pi Coding Agent** operated primarily through **Paseo**, while preserving Project Workflow as the workflow/authority layer and avoiding duplicate orchestration/state systems.

## Accepted requirements / constraints

| ID | Requirement | Status |
|---|---|---|
| PIE-REQ-001 | The target agent runtime MUST remain clean Pi; `pi-code` and OMP are not the baseline runtime. | accepted |
| PIE-REQ-002 | Paseo MUST be the primary GUI/remote surface for Pi, including Android use; terminal/TUI may remain a fallback. | accepted |
| PIE-REQ-003 | The stack MUST support MCP. The exact MCP client/adapter remains an unresolved implementation/architecture choice pending live validation. | accepted |
| PIE-REQ-004 | Project Workflow remains the canonical workflow/authority layer. Extensions MAY provide tools, UI, context management or bounded execution primitives but MUST NOT silently become a second source of workflow authority. | accepted |
| PIE-REQ-005 | `rpiv-ask-user-question` MUST be included in the candidate baseline for structured human-in-the-loop questions/choices. | accepted |
| PIE-REQ-006 | `pi-permission-system` MUST be included in the candidate baseline for enforceable allow/ask/deny policy. | accepted |
| PIE-REQ-007 | `pi-lens` MUST be included in the candidate baseline; `@narumitw/pi-lsp` is excluded from the baseline. | accepted |
| PIE-REQ-008 | A loop detector / `pi-antiloop` capability MUST be included in the candidate baseline, with conservative thresholds validated before hard abort behavior is enabled. | accepted |
| PIE-REQ-009 | `pi-skill-gate` MUST be included when the skill catalog is large enough for selective skill exposure to materially reduce context. | accepted |
| PIE-REQ-010 | `pi-file-context`, `pi-btw`, `pi-zentui`, `pi-code` and Pi Desktop MUST NOT be selected as baseline components in this scope. | accepted |
| PIE-REQ-011 | Session memory/compaction, todo/progress UI, subagent runtimes, code-mode tool composition and external workflow engines MUST NOT replace repository-backed durable Project Workflow state unless a future explicit workflow-definition decision changes that authority model. | accepted |
| PIE-REQ-012 | Any future PWv3 work derived from this research MUST be a separate authorized workflow workstream; this Pi extension workstream records prior art only. | accepted |

## Current selected baseline

Accepted candidates:
- `rpiv-ask-user-question`;
- `pi-permission-system`;
- `pi-lens`;
- loop detector / `pi-antiloop`;
- `pi-skill-gate`;
- Paseo.

Explicitly excluded:
- `@narumitw/pi-lsp`;
- `pi-file-context`;
- `pi-btw`;
- `pi-zentui`;
- `pi-code`;
- Pi Desktop.

## Non-goals / not yet accepted

The following are not yet selected merely because research found them promising:
- `pi-web-access`;
- Ketch;
- a dedicated Context7 Pi extension;
- `pi-blackhole`;
- `pi-fabric`;
- Laya/System One;
- `rpiv-todo`;
- Plannotator;
- `pi-github-pr`;
- Dagu or another external workflow engine;
- any third-party subagent framework;
- an exact MCP client/adapter;
- PWv3 implementation.

## Authority / memory invariant

Pi/Paseo/session-derived state may improve UX and continuity, but canonical Project Workflow state remains repository-backed. If Blackhole memory, rpiv-todo, Paseo session state or another extension disagrees with canonical workstream/Task Board/requirements/decision/evidence state, the repository authority wins.

## Definition completeness

Definition Complete: **RED / user decisions and live validation still required**.

See `brainstorming/PI_EXTENSION_OPEN_QUESTIONS.md`.
