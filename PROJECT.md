# PROJECT

## Identity

- Project: `pi-unraid`
- Repository: `elmakus/pi-unraid`
- Lifecycle: `active`
- High-level goal: establish a reproducible Pi Coding Agent deployment on Unraid, beginning with a minimal base bootstrap before later Web UI/extension research.
- High-level status: **Project Definition Complete = GREEN** for `pi-unraid-bootstrap@R1`; next authorized role is Strategic Planning, to be authored by Codex/Astra Max.

## Execution policy

- execution_policy: `chatgpt_only`

Changing execution policy requires an explicit user decision.

The user has directed that the **Strategic Planning role** for this Phase 1 scope be authored by Codex/Astra Max. This does not change the project's `chatgpt_only` Task Card execution policy. Independent Plan Review and downstream Execution Prep, Execution, implementation review and Close remain routed through ChatGPT unless the user explicitly changes the project policy later.

## Canonical authority pointers

- Active workstream: `implementation/workstreams/feature-pi-unraid-bootstrap/WORKSTREAM.yaml`
- Approved requirements: `requirements/PI_UNRAID_BOOTSTRAP.md`
- Accepted decisions:
  - `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
  - `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
  - `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
  - `decisions/PIB_ADR_004_WORKFLOW_ROLES.md`
- Definition evidence: `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`
- Source exploratory record: `brainstorming/PI_UNRAID_BRAINSTORM.md`
- Approved plan: none; Planning has not yet been authored.

## Definition state

- Definition subject: `pi-unraid-bootstrap@R1`
- Requirements status: `approved`
- Definition Complete: `GREEN`
- Material unresolved user/product questions: none
- Planning scope: Phase 1 minimal Pi bootstrap only

## Workflow

- Workflow repository: `elmakus/chatgpt-codex-project-workflow`
- Workflow ref: `main`

## Context note

This file is a high-level integrated-project router/index, not live execution state.

The historical brainstorming record originally accumulated on `main` before the current branch-first managed-change contract was applied. The active managed continuation was recovered onto `feat/pi-unraid-bootstrap`; the historical `main` copy remains provenance and is not rewritten as if it had always been branch-isolated.

No Task Board exists yet. Planning must consume the approved requirements and accepted decisions above before Execution Prep creates implementation state.
