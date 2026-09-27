# Independent Plan Review — Paseo GUI Runtime P2 / R01

Plan revision: `P2`
Planning cycle: `2`
Workstream: `feature-paseo-gui-runtime`
Branch: `feat/paseo-gui-runtime`
Review state: `green`
Reviewed subject: `elmakus/pi-unraid@c774f02de78dfba78d2888b54a11059c7f897304:planning/PASEO_GUI_RUNTIME_P2.md@5a16489e0f0618264f93ec0f260d89914a615ec1`

## Independence

This review was performed in the fresh Premium-B context reserved by `PLAN_REVIEW.toml`. The reviewer did not materially author or repair the exact frozen P2 subject.

## Authority checked

- `requirements/PASEO_GUI_RUNTIME.md` revision R1 / Definition `paseo-gui-runtime@2`
- `decisions/ADR_PGR_001_RUNTIME_SUBSTRATE.md`
- `decisions/ADR_PGR_002_AUTHORITY_BOUNDARIES.md`
- `decisions/ADR_PGR_003_UNRAID_ADMIN_SAFETY.md`
- `decisions/ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md`
- current Project Workflow V2 Planning and Independent Plan Review contracts

The workflow-adoption binding was treated as bootstrap/migration authority only, not product Definition authority.

## Independent findings

### Definition and decision consistency — GREEN

P2 preserves the accepted one-container Paseo/Pi runtime shape, Git/PW authority, OR separation, Relay-first access, non-root application runtime, GraphQL-primary/SSH-fallback host administration, explicit high-impact gates, immutable latest-stable candidate resolution, staged cutover and rollback-first update semantics.

### P2 timing change — GREEN

The material P2 change is bounded to evidence timing. Credential-backed authenticated GraphQL readback and live reversible mutation proof are deferred from M03-T01 to M06-T04. The plan does not waive PGR-REQ-045–054, does not relax least privilege or pre/post-readback, and does not allow production cutover when the deferred smoke is absent or RED.

M03 remains an implementation/safety-foundation milestone: client contract, permission profile, structured control surface, live API/schema/version readback, fail-closed behavior and static/CI safety evidence. M06-T04 is the integrated credential-backed acceptance point and must prove authenticated structured readback, one safe reversible ordinary GraphQL mutation, exact pre/post/restoration state, sufficiency of the bounded permission profile, SSH fallback, host doctor and return to GraphQL.

This sequencing is compatible with the accepted Definition because the requirements mandate the capability and acceptance behavior but do not require the credential-bearing mutation to be proven specifically inside M03-T01.

### Requirement coverage — GREEN

Mechanical coverage of the P2 requirement-mapping section accounts for all canonical `PGR-REQ-001` through `PGR-REQ-087`: 87/87 mapped, 0 missing.

The milestone decomposition also preserves the main cross-cutting authority boundaries:
- runtime/UX, persistence, Relay and secret handling: M02 with M06/M07 acceptance;
- browser/tool baseline: M01 with M06 acceptance;
- environment capability inventory and doctor/reconcile: M04;
- host-control implementation and safety: M03 with mandatory integrated credential-backed acceptance in M06-T04;
- coordinated update/cache/rollback: M05 with M07 production acceptance;
- OR and future PW extension integration remain outside the initial base bring-up.

### Sequencing and rollback — GREEN

The M01→M08 dependency graph is coherent. M06 consumes the implementation foundations from M01–M05; M07 consumes only the GREEN integrated candidate from M06; M08 closes only after production acceptance. Failed pre-deploy validation leaves production untouched and failed post-deploy validation preserves a rollback path to the prior coherent known-good set.

### Security and authority — GREEN

No raw credentials are made Git/evidence authority. High-impact Unraid actions remain explicit user gates. Paseo session/HOME convenience state, OR runtime state and the Environment Capability Inventory do not become workflow authority. The plan does not introduce Docker-socket or broad host-mount authority by default.

### Execution decomposition — GREEN

The planned slices are sufficiently bounded for later Card materialization and explicitly require further splitting on independent mutation surfaces, rollback domains, evidence surfaces or unresolved live-fact dependencies. The plan does not force premature concrete schemas/commands where R1 leaves them to implementation readback.

## Non-blocking Execution Prep observations

1. When M03/M06 Cards are materialized, carry the full PGR-REQ-045–054 authority into their acceptance, including PGR-REQ-050 pre-mutation readback and PGR-REQ-052 credential persistence/controlled rotation/readback; the P2 timing change must not narrow those obligations to only the reversible mutation smoke.
2. Bind M06-T04 to the exact accepted M03 host-control result so a later live incompatibility cannot be treated as evidence against a moving implementation subject.
3. Preserve PGR-REQ-023's dedicated persistent browser-automation profile and PGR-REQ-032's instruction-plane snapshot/rollback/fresh-session smoke when the relevant M01/M02/M06 Cards are refined.

## Verdict

**GREEN.**

No material strategic, scope, sequencing, authority, rollback, security or acceptance defect requires a P3 revision. P2 is suitable for Planning approval consumption.

This verdict proves plan sufficiency only. It does not prove the GraphQL credential, live mutation, Relay path, browser runtime, update pipeline or production deployment; those remain downstream execution and acceptance obligations.
