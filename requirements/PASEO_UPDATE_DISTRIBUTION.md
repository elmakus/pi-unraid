# Paseo/Pi Update Distribution — Requirements

Revision: `R2`
Status: `approved`
Updated: `2026-10-04`
Definition subject: `paseo-update-distribution@11`
Source Brainstorming: `brainstorming/PASEO_UPDATE_DISTRIBUTION.md`, R11
Base architecture Research: `elmakus/project-research:projects/pi-unraid/production_updates/paseo_pi_update_distribution/FINAL_SYNTHESIS.md@f2b0bd9d1a9c4c0635ad73b80e5f87b71a5d12db`
Amendment evidence: `implementation/workstreams/feature-paseo-update-distribution/evidence/M08-T01-definition-reentry-2026-10-04.md` and `implementation/workstreams/feature-paseo-update-distribution/evidence/DEFINITION_R2_COMPLETENESS_2026-10-04.md`

## Scope and precedence

These requirements define the update/distribution lifecycle for the production Paseo/Pi environment. For this workstream they supersede conflicting update-path provisions in `requirements/PASEO_GUI_RUNTIME.md`, especially PGR-REQ-055, PGR-REQ-061 and the extension-specific blocking implications of PGR-REQ-083. Unrelated runtime/security/persistence requirements from the earlier Paseo GUI Runtime Definition remain inherited.

## R2 validation correction and unchanged boundaries

R2 changes only final validation authority: a guarded real Muse smoke plus Codex-LB checks without inference replace R1's real Codex-LB smoke. ADR-PUD-004 owns this bounded correction and supersedes conflicting smoke-provider/model provisions in earlier PUD/PGR authority; historical plans, Research and GREEN evidence remain records of their original exact subjects.

Every real inference test MUST consume the mandatory environment test policy and use `~/.pi/agent/bin/run-llm-test.sh`: either its guarded CLI launch or its validated `--native-create-agent-args` shape for caller-scoped Paseo native creation. The fixed permitted test profile is `meta/muse-spark-1.3-contributor` with thinking/contribution `max`, with no fallback. This is a test execution constraint, not Project Workflow role-routing authority or a change to ordinary interactive model selection.

Final real-smoke evidence MUST prove that the exact immutable disposable candidate's Paseo/Pi/provider path performed the inference with the required effective profile. A valid launcher configuration, a test against the active production runtime, a test against another image, or an unrelated Muse child is insufficient. Candidate policy/launcher delivery and execution binding must be verified; missing profile, credential, launcher or binding fails closed. A harness extension may preserve the mandatory guard but cannot introduce a bypass, profile override or fallback.

Codex-LB validation is limited to authenticated non-inference catalog/metadata/auth/health integration readback and deterministic protocol fixtures. It MUST NOT send a prompt or invoke an inference endpoint to turn this check into an additional real LLM test. Negative, malformed, unauthorized, missing or unreachable required readback is not GREEN and must be classified proportionally rather than silently skipped.

Credential isolation, GitHub/Tower separation, exact build-once identity, direct state-transition proof, transaction-guard pre-arm, user-triggered cutover and bounded rollback are unchanged. Scope approval does not itself provide a credential, satisfy a smoke gate or authorize a production restart. The old M07 candidate and its fixture-only evidence do not establish the new real-smoke acceptance; any candidate changed to deliver R2 must receive a new immutable build identity and exact affected-gate evidence before promotion.

## Discovery, registry and candidate resolution

| ID | Requirement | Priority |
|---|---|---|
| PUD-REQ-001 | The system MUST discover updates for managed components automatically on a daily cadence. | MUST |
| PUD-REQ-002 | One declarative managed-component registry/inventory MUST be the durable source of truth for components intentionally carried by the environment and tracked for updates. | MUST |
| PUD-REQ-003 | The registry MUST be extensible through typed source/install classes; initial support SHOULD cover only source classes required by current components, while future classes may be added without creating component-specific scheduler workflows. | MUST |
| PUD-REQ-004 | Every candidate MUST freeze exact selected component identities before build; build/test stages MUST NOT independently re-resolve newer versions. | MUST |
| PUD-REQ-005 | Candidate resolution MUST allow an independently failing component to remain on its previous accepted version while unrelated components advance. | MUST |
| PUD-REQ-006 | Compatibility combination search MUST be limited to the core Paseo↔Pi runtime pair. Node MUST be derived from the exact Paseo image and checked only against Pi runtime/version constraints. | MUST |
| PUD-REQ-007 | SpecPi, pi-mcp-adapter and future ordinary Pi extensions MUST NOT participate in Paseo/Pi compatibility backtracking by default. If a newest extension cannot be fetched/installed/built, only that extension MAY remain on its previous accepted version. Extension-specific runtime malfunction after successful installation MUST NOT by itself block the core Update Ready channel unless later evidence promotes that extension into the core compatibility gate. | MUST |
| PUD-REQ-008 | Playwright and its derived Chromium version MUST be treated as one update unit, not a cross-component compatibility search group. | MUST |
| PUD-REQ-009 | GitHub CLI, Docker CLI, Docker Compose and future ordinary developer tools MUST update independently without cross-component version search; a failing newest version MAY fall back independently to its previous accepted version. | MUST |
| PUD-REQ-010 | If multiple complete compatible candidates are Pareto-maximal and incomparable, the resolver MUST select the candidate with the smallest aggregate version lag from current newest available versions using equal component weight, followed only by a deterministic technical tie-break. | MUST |

## Managed add/remove lifecycle

| ID | Requirement | Priority |
|---|---|---|
| PUD-REQ-011 | A durable add of a Pi extension or developer tool MUST atomically update both installation intent and managed-component registry membership. | MUST |
| PUD-REQ-012 | A durable remove MUST atomically remove both installation intent and registry membership. | MUST |
| PUD-REQ-013 | Build/readback validation MUST fail a managed change that intentionally leaves an installed-but-unregistered or registered-but-not-installed component. | MUST |
| PUD-REQ-014 | The normal user UX is natural-language instruction to the coding agent. The agent MUST use the project-owned managed-component helper/workflow for durable add/remove operations; the human operator MUST NOT be required to maintain registry entries manually. | MUST |
| PUD-REQ-015 | Direct live-container installation MAY be used for explicitly temporary experimentation/diagnosis but MUST NOT become durable managed state unless adopted through the managed add path. | MUST |
| PUD-REQ-016 | Future managed components MUST default to the least-complex class: ordinary extension or developer tool is independently updated; derived artifacts follow their owner; promotion into core compatibility search requires demonstrated core startup/API coupling. | MUST |

## Build, validation and publication

| ID | Requirement | Priority |
|---|---|---|
| PUD-REQ-017 | GitHub-hosted CI MUST own normal discovery, candidate resolution, exact build and deterministic mechanical validation; production secrets MUST NOT be exposed to GitHub-hosted candidate jobs. | MUST |
| PUD-REQ-018 | The exact tested image MUST be published to GHCR by immutable OCI digest; no rebuild is permitted between accepted build evidence and publication/promotion. | MUST |
| PUD-REQ-019 | Production update signaling MUST use one serialized mutable accepted channel/tag that points only to a fully accepted immutable digest. Moving the accepted tag MUST be followed by registry digest readback. | MUST |
| PUD-REQ-020 | Tower MUST perform only Tower-specific disposable validation against the exact GHCR digest, including production-shaped runtime/state checks, a bounded policy-compliant real Muse smoke through that exact candidate's Paseo/Pi/provider path, and authenticated Codex-LB integration checks without inference, without mutating the active production container. | MUST |
| PUD-REQ-021 | Validation MUST consume only dedicated operator-provisioned test credentials inside the approved disposable candidate boundary. Normal agent credentials MUST NOT be provided to the update pipeline; no credential may enter GitHub CI, images, Git, logs or evidence. Real inference MUST use the mandatory guarded launcher and fixed Muse Spark/max profile without fallback; Codex-LB credentials MUST be used only for non-inference checks. Credential provisioning/restrictions remain operator-managed; missing or incompatible input blocks acceptance. | MUST |
| PUD-REQ-022 | Every final candidate MUST pass a bounded whole-environment core startup/invariant smoke, but optional extension/tool feature functionality MUST NOT be expanded into a blocking combinatorial compatibility matrix. | MUST |
| PUD-REQ-023 | Major versions MUST follow the same discovery/build/validation policy as other stable versions; no separate major-version approval framework is required. | MUST |

## Production update and rollback

| ID | Requirement | Priority |
|---|---|---|
| PUD-REQ-024 | Production MUST NOT update merely because a candidate becomes accepted. The user MUST choose the cutover time and explicitly initiate the update from the Unraid surface. | MUST |
| PUD-REQ-025 | The preferred user gesture is the stock DockerMan Update action. Before relying on it, implementation MUST prove crash-safe binding to a pre-armed transaction guard on the exact installed Unraid version. If that cannot be proven, one project/plugin `Update + Verify` action in Unraid is the accepted minimal fallback; a separate dashboard and core DockerMan patch are out of scope. | MUST |
| PUD-REQ-026 | Before exposing a candidate through the accepted channel, a durable Tower transaction guard MUST bind the exact candidate digest, exact previous known-good deployment and rollback anchor. | MUST |
| PUD-REQ-027 | The user-triggered cutover plus immediate verification MUST be one bounded transaction: start the candidate, run deterministic acceptance checks, commit it as current known-good on GREEN, or automatically restore the immediately previous known-good image and verify recovery on RED. | MUST |
| PUD-REQ-028 | Automatic rollback authority MUST end once the immediate acceptance transaction reaches GREEN. Later unrelated runtime failures MUST NOT autonomously restart or roll back production. | MUST |
| PUD-REQ-029 | Production MUST maintain exactly two previous production-known-good rollback identities in addition to current. Registry/build evidence retention MAY be broader. | MUST |
| PUD-REQ-030 | An ordinary Update Ready candidate MUST prove the exact direct transition from the actually running known-good state to the candidate and back to the previous runtime on a coherent representative disposable state clone (`A -> C -> A`). | MUST |
| PUD-REQ-031 | Skipping intermediate accepted candidates is allowed only when the actual current production baseline -> newest accepted candidate direct transition is proven. | MUST |
| PUD-REQ-032 | A release that performs an irreversible persistent-state migration and cannot pass the ordinary rollback-safe transition proof MUST be held out of the normal accepted channel and requires a separate explicit maintenance procedure. | MUST |
| PUD-REQ-033 | The system MUST NOT add a separate candidate changelog/dashboard UX as part of this scope. Unraid Update Ready plus durable technical evidence is sufficient. | MUST |

## Acceptance boundary

Definition acceptance requires downstream Planning to preserve all MUST requirements above and to identify tests/evidence for:
- core Paseo↔Pi compatibility selection;
- managed registry/install drift prevention;
- exact-digest build/publish/promote identity;
- exact-candidate Tower disposable runtime/state-transition validation;
- guarded real Muse smoke with verified effective profile and authenticated non-inference Codex-LB integration checks;
- dedicated validation credential isolation and fail-closed behavior for missing policy/profile/launcher/candidate binding;
- stock-button transaction binding or the accepted Update+Verify fallback;
- current/previous_1/previous_2 known-good ledger;
- immediate RED rollback and post-GREEN cessation of rollback authority.
