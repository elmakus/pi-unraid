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
- High-level status: **Phase 1 R3 and the Paseo/Pi GUI runtime scope are complete and integrated into `main`; the Paseo update-distribution workstream is currently active.** Phase 1 was integrated through PR #1; the Paseo/Pi workstream was integrated through PR #4 with all M01-M08 Cards terminal, M08-T01 REQUIRED independent review GREEN and M08-T02 close-readiness GREEN. Production Paseo is accepted on the frozen immutable image. Routine scheduled Appdata Backup remains explicitly degraded; bounded M07 rollback/migration archives remain verified.

## Workflow runtime policy

Current Project Workflow V2 routing is harness-neutral. Provider, model, product, session or worker identity does not select or gate Project Workflow roles.

Independent review is determined by exact-subject semantic independence under the canonical `workflow/REVIEW.md`: a context that materially produced or repaired the exact subject cannot issue its independent verdict; another qualifying context or harness may do so.

Historical Phase 1 ADRs, plans and evidence that contain runtime-specific role routing or earlier workflow package paths are retained as historical records only. They are not current routing authority for active Project Workflow V2 workstreams.

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

- Workflow repository: `elmakus/project_workflow_v2`
- Workflow ref: current default branch (`main`)
- Active managed workstream: `implementation/workstreams/feature-paseo-update-distribution/WORKSTREAM.toml`

## Context note

This file is a high-level integrated-project router/index, not live execution state.

The historical brainstorming record originally accumulated on `main` before the branch-first managed-change contract was applied. The managed Phase 1 continuation was recovered onto `feat/pi-unraid-bootstrap`, completed under the namespaced workstream package and merged back to `main` through PR #1; GitHub then automatically removed the source branch. Terminal recovery truth now lives in the target-side namespaced workstream package.

Master Plan R3 is approved after independent Plan Review GREEN. Phase 1 has no remaining implementation, review or Close obligation. The later Paseo/Pi GUI runtime scope was executed as its own V2 workstream, integrated through PR #4, and its target-side recovery package now lives under `implementation/workstreams/feature-paseo-gui-runtime/`. The original source branch was automatically removed after merge and must not be recreated for bookkeeping.
