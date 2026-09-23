# PROJECT

## Identity

- Project: `pi-unraid`
- Repository: `elmakus/pi-unraid`
- Lifecycle: `active`
- High-level goal: establish a reproducible Pi Coding Agent deployment on Unraid, beginning with a minimal base bootstrap before later Web UI/extension research.
- High-level status: **Phase 1 R3 is technically complete and integrated into `main` through PR #1.** M01, M02 and M03 are terminal GREEN; final M03-T06 REQUIRED independent review and the workstream final-integration gate are GREEN. The Docker-wide/Unraid host restart exercise was intentionally not executed under PIB-ADR-007, and that residual risk remains explicitly accepted.

## Execution policy

- execution_policy: `chatgpt_only`

Changing execution policy requires an explicit user decision.

The latest user authority supersedes the former Codex/Astra Max planner assignment: the current normal ChatGPT session authored Strategic Planning R3 under `PIB-ADR-006` after the explicit R3 acceptance change in `PIB-ADR-007`. This does not change the project's `chatgpt_only` execution policy. Independent Plan Review must be performed by a fresh normal ChatGPT that did not author the exact R3 plan subject, and downstream Execution Prep, Execution, implementation review and Close remain routed through ChatGPT unless the user explicitly changes project authority later.

## Canonical authority pointers

- Completed Phase 1 workstream: `implementation/workstreams/feature-pi-unraid-bootstrap/WORKSTREAM.yaml`
- Approved requirements: `requirements/PI_UNRAID_BOOTSTRAP.md`
- Accepted decisions:
  - `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
  - `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
  - `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
  - `decisions/PIB_ADR_004_WORKFLOW_ROLES.md`
  - `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md`
  - `decisions/PIB_ADR_006_CHATGPT_STRATEGIC_PLANNER_OVERRIDE.md`
  - `decisions/PIB_ADR_007_SKIP_DISRUPTIVE_RESTART_ACCEPTANCE.md`
- Definition evidence:
  - `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`
  - `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`
- Source exploratory record: `brainstorming/PI_UNRAID_BRAINSTORM.md`
- Current Master Plan artifact: `planning/MASTER_PLAN.md`, revision `R3`, status `approved`
- Planner audit: `planning/audits/R3.md`, GREEN
- Plan Review record: `planning/reviews/R3.md`, GREEN

## Definition state

- Definition subject: `pi-unraid-bootstrap@R3`
- Requirements status: `approved`
- Definition Complete: `GREEN`
- Material unresolved user/product questions: none; the broad restart verification risk is explicitly accepted under `PIB-ADR-007`
- Planning scope: Phase 1 minimal Pi bootstrap with Codex-LB as the required ChatGPT/Codex OAuth/account-routing layer; no direct Pi ChatGPT OAuth bootstrap path

## Workflow

- Workflow repository: `elmakus/chatgpt-codex-project-workflow`
- Workflow ref: `main`

## Context note

This file is a high-level integrated-project router/index, not live execution state.

The historical brainstorming record originally accumulated on `main` before the branch-first managed-change contract was applied. The managed Phase 1 continuation was recovered onto `feat/pi-unraid-bootstrap`, completed under the namespaced workstream package and merged back to `main` through PR #1; GitHub then automatically removed the source branch. Terminal recovery truth now lives in the target-side namespaced workstream package.

Master Plan R3 is approved after independent Plan Review GREEN. Phase 1 has no remaining implementation, review or Close obligation. Any later Web UI/extensions/subagents/MCP/browser/research capability is outside this completed scope and must enter through a new accepted workflow route rather than extending the closed workstream implicitly.
