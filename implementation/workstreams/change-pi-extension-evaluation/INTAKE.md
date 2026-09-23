# Intake — Pi extension evaluation

- Workstream ID: `change-pi-extension-evaluation`
- Intake kind: `change`
- Intake state: `complete`
- Branch: `work/pi-extension-evaluation`
- Base ref: `feat/pi-unraid-bootstrap`
- Integration target: `main`
- Parent workstream: `feature-pi-unraid-bootstrap`
- Parent branch: `feat/pi-unraid-bootstrap`

## Authorized bounded scope

Research, compare and record the extension/tooling choices for a clean Pi Coding Agent deployment operated primarily through Paseo. Preserve the user's accepted/rejected candidates and investigate unresolved candidates, including possible lessons for a future Pi-oriented revision of Project Workflow (informally discussed as PWv3). Include MCP support because MCP usage is required.

This workstream is research/decision preparation only unless later authority explicitly promotes findings into Definition/Planning/implementation.

## Base/dependency classification

Classification: **stacked**.

Reason: the work explicitly assumes the clean-Pi deployment direction, Paseo as the intended UI/remote, and the current project repository/workstream structure. Those project facts are presently durable only on the unmerged parent branch `feat/pi-unraid-bootstrap`; `main` does not yet contain the current `PROJECT.md` or that accepted project state.

The final integration target remains `main`. The child must not integrate directly while its declared parent-only dependency is unsatisfied.

## User choices captured at intake

- 1 `rpiv-ask-user-question`: accepted.
- 2 `pi-permission-system`: accepted.
- 3 `@narumitw/pi-lsp`: rejected.
- 4 `pi-lens`: accepted.
- 5–6 `pi-web-access` vs Ketch: compare before choosing.
- 7 Context7 Pi: decide after 5–6 analysis.
- 8 `pi-blackhole`: deeper research requested.
- 9 loop detector / `pi-antiloop`: accepted.
- 10 `pi-fabric`: research requested, including possible PWv3 lessons.
- 11 Laya / System One: research requested, including possible PWv3 lessons.
- 12 `rpiv-todo`: research requested because moving from Codex/ChatGPT usage to Pi may justify PWv3 changes.
- 13 Plannotator: verify Paseo compatibility.
- 14 `pi-skill-gate`: accepted.
- 15 `pi-file-context`: rejected.
- 16 `pi-btw`: rejected.
- 17 `pi-github-pr`: determine whether it only helps the human UI or also the agent.
- 18 `pi-zentui`: rejected.
- 19 SpecPi/self-discovered extension/ability mechanism: locate the Reddit comment and identify the actual extension/mechanism referred to.
- 20 external workflow-engine prior art: research requested.
- 21 `pi-code`: rejected; use clean Pi.
- 22 subagent frameworks: research requested as prior art for Pi-native subagents/PWv3.
- 23 Pi Desktop: rejected; Paseo selected instead.
- MCP: research Pi extensions/approaches needed to use MCP cleanly.

## Downstream materialization

- Path: Research
- Next route: `research:pi-extension-evaluation-r1`
- Canonical research record: `research/PI_EXTENSION_EVALUATION_R1.md`
- Manifest routing locator: `routing.research_obligation = research/PI_EXTENSION_EVALUATION_R1.md`
