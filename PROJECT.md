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
- High-level status: **Phase 1 R3, the Paseo/Pi GUI runtime scope, dynamic Codex-LB model discovery and the permanent Paseo-to-Pi Codex-LB credential repair are complete and integrated into `main`.** Phase 1 was integrated through PR #1; Paseo/Pi through PR #4; dynamic Codex-LB discovery through PR #8; the runtime credential propagation and Luna/low-only real-LLM test policy through PR #12 with REQUIRED independent review GREEN. Production Paseo is healthy on the accepted repaired image, exposes the live nine-model Codex-LB catalog without manual secret sourcing, and retains bounded rollback anchors. Routine scheduled Appdata Backup remains explicitly degraded; bounded M07 rollback/migration archives remain verified.

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
- Completed dynamic Codex-LB model catalog workstream: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/WORKSTREAM.toml`
- Dynamic catalog requirements: `requirements/CODEX_LB_DYNAMIC_MODEL_CATALOG.md`
- Dynamic catalog final scope reconciliation: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M03-T01.md`
- Dynamic catalog final independent review: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/reviews/M03-T01-R01.toml`
- Dynamic catalog post-merge closure evidence: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/evidence/WORKSTREAM_CLOSE.md`
- Completed Paseo Codex-LB environment repair workstream: `implementation/workstreams/issue-paseo-codex-lb-env-propagation/WORKSTREAM.toml`
- Paseo Codex-LB environment repair result: `implementation/workstreams/issue-paseo-codex-lb-env-propagation/results/M01-T01.md`
- Paseo Codex-LB environment repair independent review: `implementation/workstreams/issue-paseo-codex-lb-env-propagation/reviews/M01-T01-R01.toml`
- Real LLM test policy: `docs/LLM_TEST_POLICY.md`
- Paseo Codex-LB repair post-merge closure evidence: `implementation/workstreams/issue-paseo-codex-lb-env-propagation/evidence/WORKSTREAM_CLOSE.md`
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

## Codex-LB dynamic model catalog state

- Workstream: `feature-codex-lb-dynamic-model-catalog`
- Requirements: `requirements/CODEX_LB_DYNAMIC_MODEL_CATALOG.md`, approved Definition R1
- Accepted plan: `planning/CODEX_LB_DYNAMIC_MODEL_CATALOG_P1.md`
- Implementation state: all five Cards terminal; final M03-T01 scope reconciliation REQUIRED review `M03-T01-R01` GREEN
- Integrated source: PR #8, exact source head `e6efe241a95f97a2483748638d74532a55e30a57`, merge commit `0ac278a29ed2decf93f4bf71d4585d712b2ddf14`
- Production state: instruction plane remains in sync; Codex-LB provider configuration is dynamic; persisted Codex-LB auth shadow is absent; bounded instruction/provider/auth rollback anchors remain available
- Tracker state: Issue #7 is CLOSED / COMPLETED after explicit post-merge reconciliation; the merged PR body contained literal escaped newline characters, so GitHub did not register its intended automatic closing linkage
- Scope boundary: no automatic model selection/failover was introduced, and the separate `feature-paseo-update-distribution` workstream was not modified by this feature scope

## Paseo Codex-LB runtime environment and LLM-test policy state

- Workstream: `issue-paseo-codex-lb-env-propagation`
- Repair subject: `repair:paseo-codex-lb-runtime-env-and-llm-test-policy:v1`
- Implementation state: M01-T01 terminal; REQUIRED independent review `M01-T01-R01` GREEN
- Integrated source: PR #12, exact source head `ae0d580aa13aae8ee67064c0a12802d62de4c959`, merge commit `12fae1f7f444afb96e3da9bc56618be383432c86`
- Production state: healthy on repaired image `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`; Paseo enumerates all nine current Codex-LB models without manual secret sourcing; raw `CODEX_LB_API_KEY` is not persisted in Docker configured environment
- Real LLM test rule: all real inference tests use `codex-lb/gpt-6-luna` with thinking `low`; `gpt-6-astra` is forbidden and fallback is disabled
- Policy authority: `docs/LLM_TEST_POLICY.md`, `config/pi-agent/policies/LLM_TEST_POLICY.md`, `config/pi-agent/policies/llm-test-policy.json`, `config/pi-agent/AGENTS.md`, `config/pi-agent/bin/run-llm-test.sh`
- Tracker state: Issue #10 `CLOSED / COMPLETED` after PR #12 integration

## Workflow

- Workflow repository: `elmakus/project_workflow_v2`
- Workflow ref: current default branch (`main`)

## Context note

This file is a high-level integrated-project router/index, not live execution state.

The historical brainstorming record originally accumulated on `main` before the branch-first managed-change contract was applied. The managed Phase 1 continuation was recovered onto `feat/pi-unraid-bootstrap`, completed under the namespaced workstream package and merged back to `main` through PR #1; GitHub then automatically removed the source branch. Terminal recovery truth now lives in the target-side namespaced workstream package.

Master Plan R3 is approved after independent Plan Review GREEN. Phase 1 has no remaining implementation, review or Close obligation. The later Paseo/Pi GUI runtime scope was integrated through PR #4, dynamic Codex-LB model discovery through PR #8, and the permanent Paseo Codex-LB environment propagation repair plus Luna/low-only real-LLM test policy through PR #12. Their target-side recovery packages live under their respective namespaced workstreams on `main`; automatically removed source branches must not be recreated for bookkeeping.
