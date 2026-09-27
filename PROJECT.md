+++
project_workflow = "v2"
project_id = "pi-unraid"
repository = "elmakus/pi-unraid"
workstream_root = "implementation/workstreams"
+++
# PROJECT

## Identity

- Project: `pi-unraid`
- Repository: `elmakus/pi-unraid`
- Lifecycle: `active`
- High-level goal: operate a reproducible Pi Coding Agent environment on Unraid with Paseo as the production GUI/runtime, durable project/worktree storage, bounded host control, reproducible global capabilities and rollback/recovery evidence.
- High-level status: **Phase 1 R3 and the Paseo/Pi GUI runtime scope are complete and integrated into `main`.** Phase 1 was integrated through PR #1; the Paseo/Pi workstream was integrated through PR #4 with all M01-M08 Cards terminal, M08-T01 REQUIRED independent review GREEN and M08-T02 close-readiness GREEN. Production Paseo is accepted on the frozen immutable image. Routine scheduled Appdata Backup remains explicitly degraded; bounded M07 rollback/migration archives remain verified.

## Execution policy

- execution_policy: `chatgpt_only`

Changing execution policy requires an explicit user decision.

The latest user authority supersedes the former Codex/Astra Max planner assignment: the current normal ChatGPT session authored Strategic Planning R3 under `PIB-ADR-006` after the explicit R3 acceptance change in `PIB-ADR-007`. This does not change the project's `chatgpt_only` execution policy. Independent Plan Review must be performed by a fresh normal ChatGPT that did not author the exact R3 plan subject, and downstream Execution Prep, Execution, implementation review and Close remain routed through ChatGPT unless the user explicitly changes project authority later.

## Canonical authority pointers

- Completed Phase 1 workstream: `implementation/workstreams/feature-pi-unraid-bootstrap/WORKSTREAM.yaml`
- Completed Paseo/Pi GUI runtime workstream: `implementation/workstreams/feature-paseo-gui-runtime/WORKSTREAM.toml`
- Paseo/Pi final production evidence: `implementation/workstreams/feature-paseo-gui-runtime/results/M08-T01.md`
- Paseo/Pi final independent review: `implementation/workstreams/feature-paseo-gui-runtime/reviews/M08-T01-R01.toml`
- Paseo/Pi close-readiness result: `implementation/workstreams/feature-paseo-gui-runtime/results/M08-T02.md`
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

## Paseo/Pi GUI runtime state

- Workstream: `feature-paseo-gui-runtime`
- Requirements: `requirements/PASEO_GUI_RUNTIME.md`, approved Definition R2
- Accepted plan: `planning/PASEO_GUI_RUNTIME_P4.md`
- Implementation state: all M01-M08 Cards terminal; final M08-T01 production evidence REQUIRED review GREEN; M08-T02 close-readiness GREEN
- Integrated source: PR #4, exact source head `c3ea146ffd083fb4b93e7c6c8cb30d8743828976`, merge commit `cfe5bc64bac0d89ae209fe99d86412dc1dafda3a`
- Residual risk: scheduled Appdata Backup is degraded through the 2026-09-27 failed run; bounded production and legacy-retirement archives remain verified
- Downstream boundary: Orchestration Runtime live integration and future PWv2.1 Pi-extension packaging/bootstrap are separate scopes and are not authorized by this completed workstream

## Workflow

- Workflow repository: `elmakus/chatgpt-codex-project-workflow`
- Workflow ref: `main`

## Context note

This file is a high-level integrated-project router/index, not live execution state.

The historical brainstorming record originally accumulated on `main` before the branch-first managed-change contract was applied. The managed Phase 1 continuation was recovered onto `feat/pi-unraid-bootstrap`, completed under the namespaced workstream package and merged back to `main` through PR #1; GitHub then automatically removed the source branch. Terminal recovery truth now lives in the target-side namespaced workstream package.

Master Plan R3 is approved after independent Plan Review GREEN. Phase 1 has no remaining implementation, review or Close obligation. The later Paseo/Pi GUI runtime scope was executed as its own V2 workstream, integrated through PR #4, and its target-side recovery package now lives under `implementation/workstreams/feature-paseo-gui-runtime/`. The original source branch was automatically removed after merge and must not be recreated for bookkeeping.
