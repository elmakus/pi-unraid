# Pi extension/tooling stack

Revision: `R4`
Status: `draft`
Updated: `2026-09-23`

Definition subject: `pi-extension-tooling-selection@R4`
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
| PIE-REQ-013 | The stack MUST include SpecPi's Pi-wide capability-gap / harness-improvement loop. It MUST remain outside Project Workflow authority: observing/logging a gap does not authorize a harness change. | accepted |
| PIE-REQ-014 | Future Pi-oriented PWv3 research MUST also consider refactoring/optimizing the separate `codex_workflow` runtime for Pi-native subagents and bounded context rather than assuming the current Codex-specific design remains optimal. | accepted |
| PIE-REQ-015 | SpecPi MUST initially be installed in core-only mode (`--skip-package-install`) so its bundled package set does not silently decide unresolved choices such as web tooling, delegation, goals or other extension policy. | accepted |
| PIE-REQ-016 | `pi-blackhole` MUST be included as the context-compaction/memory extension. Its observational memory MAY be enabled, but all Blackhole summaries/observations/reflections remain non-authoritative convenience context. | accepted |
| PIE-REQ-017 | Independent review MUST use a fresh Pi session/process and MUST NOT inherit executor-session Blackhole memory or exported cross-session memory unless the exact review contract explicitly permits that evidence. | accepted |

## Current selected baseline

Accepted:
- Paseo;
- SpecPi core: scope + Harness Improvement Loop, installed initially with `--skip-package-install`;
- `pi-blackhole`;
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

## Blackhole authority/configuration boundary

Blackhole is selected, including the option to use observational memory.

Its worker models are configurable independently (`observerModel`, `reflectorModel`, `dropperModel`, fallbacks and thinking level). Exact model/provider choices are runtime configuration and may be optimized later without changing the product/system authority in this Definition.

Repository-backed Project Workflow state always wins over Blackhole memory. A remembered completion, verdict, route or decision can never advance workflow state by itself.

## Definition completeness

Definition Complete: **RED / live web-research A/B validation still remains**.

See `brainstorming/PI_EXTENSION_OPEN_QUESTIONS.md`.
