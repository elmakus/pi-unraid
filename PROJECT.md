# PROJECT

## Identity

- Project: `pi-unraid`
- Repository: `elmakus/pi-unraid`
- Lifecycle: `active`
- High-level goal: establish a reproducible Pi Coding Agent deployment on Unraid, beginning with a minimal base bootstrap before later Web UI/extension research.
- High-level status: **Project Definition R2 GREEN; Master Plan R2 independently reviewed GREEN and approved; M03 is ready for JIT Execution Prep.** M01/M02 remain completed historical checkpoints; no production M03 deployment has occurred.

## Execution policy

- execution_policy: `chatgpt_only`

Changing execution policy requires an explicit user decision.

The latest user authority supersedes the former Codex/Astra Max planner assignment: the current normal ChatGPT session authored Strategic Planning R2 under `PIB-ADR-006`. This does not change the project's `chatgpt_only` execution policy. Independent Plan Review must be performed by a fresh normal ChatGPT that did not author the exact R2 plan subject, and downstream Execution Prep, Execution, implementation review and Close remain routed through ChatGPT unless the user explicitly changes project authority later.

## Canonical authority pointers

- Active workstream: `implementation/workstreams/feature-pi-unraid-bootstrap/WORKSTREAM.yaml`
- Approved requirements: `requirements/PI_UNRAID_BOOTSTRAP.md`
- Accepted decisions:
  - `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
  - `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
  - `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
  - `decisions/PIB_ADR_004_WORKFLOW_ROLES.md`
  - `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md`
  - `decisions/PIB_ADR_006_CHATGPT_STRATEGIC_PLANNER_OVERRIDE.md`
- Definition evidence:
  - `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`
  - `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`
- Source exploratory record: `brainstorming/PI_UNRAID_BRAINSTORM.md`
- Current Master Plan artifact: `planning/MASTER_PLAN.md`, revision `R2`, status `approved`
- Planner audit: `planning/audits/R2.md`, GREEN
- Plan Review record: `planning/reviews/R2.md`, GREEN

## Definition state

- Definition subject: `pi-unraid-bootstrap@R2`
- Requirements status: `approved`
- Definition Complete: `GREEN`
- Material unresolved user/product questions: none
- Planning scope: Phase 1 minimal Pi bootstrap with Codex-LB as the required ChatGPT/Codex OAuth/account-routing layer; no direct Pi ChatGPT OAuth bootstrap path

## Workflow

- Workflow repository: `elmakus/chatgpt-codex-project-workflow`
- Workflow ref: `main`

## Context note

This file is a high-level integrated-project router/index, not live execution state.

The historical brainstorming record originally accumulated on `main` before the current branch-first managed-change contract was applied. The active managed continuation was recovered onto `feat/pi-unraid-bootstrap`; the historical `main` copy remains provenance and is not rewritten as if it had always been branch-isolated.

The current R2 plan is not approved until the required independent Plan Review is GREEN and Planning consumes that verdict. Live implementation/review state remains owned only by the selected branch-isolated workstream manifest and its manifest-bound Task Board.
