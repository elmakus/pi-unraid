# Pi extension/tooling stack

Revision: `R2`
Status: `draft`
Updated: `2026-09-23`

Definition subject: `pi-extension-tooling-selection@R2`
Workstream: `change-pi-extension-evaluation`
Verified research:
- `research/PI_EXTENSION_EVALUATION_R1.md`
- `research/PI_BLACKHOLE_MEMORY_FACTS_R1.md`

## Goal

Define the follow-on Pi capability stack for a **clean Pi Coding Agent** operated primarily through **Paseo**, while preserving Project Workflow as the workflow/authority layer and avoiding duplicate orchestration/state systems.

## Accepted requirements / constraints

| ID | Requirement | Status |
|---|---|---|
| PIE-REQ-001 | The target agent runtime MUST remain clean Pi; `pi-code` and OMP are not the baseline runtime. | accepted |
| PIE-REQ-002 | Paseo MUST be the primary GUI/remote surface for Pi, including Android use; terminal/TUI may remain a fallback. | accepted |
| PIE-REQ-003 | The stack MUST support MCP through `pi-mcp-adapter` as the selected primary adapter. Live Pi + Paseo + Linux/Unraid validation remains required before deployment is treated as accepted operationally. | accepted |
| PIE-REQ-004 | Project Workflow remains the canonical workflow/authority layer. Extensions MAY provide tools, UI, context management or bounded execution primitives but MUST NOT silently become a second source of workflow authority. | accepted |
| PIE-REQ-005 | `rpiv-ask-user-question` MUST be included in the candidate baseline for structured human-in-the-loop questions/choices. | accepted |
| PIE-REQ-006 | `pi-permission-system` MUST be included in the candidate baseline for enforceable allow/ask/deny policy. | accepted |
| PIE-REQ-007 | `pi-lens` MUST be included in the candidate baseline; `@narumitw/pi-lsp` is excluded from the baseline. | accepted |
| PIE-REQ-008 | A loop detector / `pi-antiloop` capability MUST be included in the candidate baseline, with conservative thresholds validated before hard abort behavior is enabled. | accepted |
| PIE-REQ-009 | `pi-skill-gate` MUST be included when the skill catalog is large enough for selective skill exposure to materially reduce context. | accepted |
| PIE-REQ-010 | `pi-file-context`, `pi-btw`, `pi-zentui`, `pi-code`, Pi Desktop, `rpiv-todo`, Plannotator and `pi-github-pr` MUST NOT be selected as baseline components in this scope. | accepted |
| PIE-REQ-011 | Session memory/compaction, todo/progress UI, subagent runtimes, code-mode tool composition and external workflow engines MUST NOT replace repository-backed durable Project Workflow state unless a future explicit workflow-definition decision changes that authority model. | accepted |
| PIE-REQ-012 | Any future PWv3 work derived from this research MUST be a separate authorized workflow workstream; this Pi extension workstream records prior art only. | accepted |
| PIE-REQ-013 | If a capability-gap / harness-improvement reporting loop is adopted, it MUST be a Pi-wide harness capability rather than a feature embedded inside Project Workflow. Project Workflow may consume promoted work items later, but it does not own gap collection. | accepted |
| PIE-REQ-014 | Future Pi-oriented PWv3 research MUST also consider refactoring/optimizing the separate `codex_workflow` runtime for Pi-native subagents and bounded context rather than assuming the current Codex-specific design remains optimal. | accepted |

## Current selected baseline

Accepted candidates:
- Paseo;
- `rpiv-ask-user-question`;
- `pi-permission-system`;
- `pi-lens`;
- loop detector / `pi-antiloop`;
- `pi-skill-gate`;
- `pi-mcp-adapter`.

Explicitly excluded from the baseline:
- `@narumitw/pi-lsp`;
- `pi-file-context`;
- `pi-btw`;
- `pi-zentui`;
- `pi-code`;
- Pi Desktop;
- `rpiv-todo` (ideas may still be reused);
- Plannotator;
- `pi-github-pr`.

## Deferred / research-only prior art

Not selected as current deployment components merely because they are interesting:
- `pi-fabric`;
- Laya/System One;
- Dagu or another external workflow engine;
- third-party subagent frameworks;
- PWv3 implementation;
- `codex_workflow` refactor.

Context7 is not selected as a separate extension here. If it proves necessary after web/research testing, the user has another intended delivery path and it can be evaluated then.

## Authority / memory invariant

Pi/Paseo/session-derived state may improve UX and continuity, but canonical Project Workflow state remains repository-backed. If Blackhole memory, Paseo session state or another extension disagrees with canonical workstream/Task Board/requirements/decision/evidence state, the repository authority wins.

## Definition completeness

Definition Complete: **RED / bounded live validation and the Blackhole selection still remain**.

See `brainstorming/PI_EXTENSION_OPEN_QUESTIONS.md`.
