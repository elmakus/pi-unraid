# M04-T01 — Environment Capability Inventory foundation evidence

Date: 2026-09-25
Card: `M04-T01`
Implementation subject: `elmakus/pi-unraid@45a083482855378e6085e261a6181376d4c2fa2d`

## Exact predecessors

The implementation revalidated the Card-bound accepted predecessors:

- `implementation/workstreams/feature-paseo-gui-runtime/results/M01-T03.md@bbc862c37c0da81a08a91876499cfe865be958ab:3772f647f5a0c55e856d3ae8e3feb05c6fb3e1f5`
- `implementation/workstreams/feature-paseo-gui-runtime/results/M02-T03.md@cac4ac5e5a4b6c96ad71d9bbce12962388f7a4be:0d13d7fe5a6dd29fb68e700d13cc5c1251722c28`

The CI predecessor-binding step completed GREEN before the contract suite.

## Implemented inventory foundation

- `config/environment-capabilities.json@47bbea690b32b38d26d5aac6fc56c40e238e2d84` is the single declarative environment-availability inventory definition.
- The definition contains stable capability IDs, accepted delivery mode, runtime location and read-only probe metadata. It does not contain OR role/action/bundle/assignment policy or PW Task Board/workflow state.
- Desired versions for the frozen candidate components are referenced by selector and derived from `config/paseo-candidate.json`; the inventory definition does not duplicate those version literals.
- The nested Chromium identity is derived from the frozen Playwright candidate metadata, the generic base-tooling identity/membership is derived from the candidate policy record, and the Pi instruction plane is identified by a deterministic repository-tree SHA-256 over `config/pi-agent`.
- `scripts/environment_capability_inventory.py@e2da97e1c07750022a6b7415f03236a70ea2787c` performs deterministic read-only derivation using repository files plus explicit observation input. It performs no network calls, subprocess execution, installation, reconcile, deletion or version re-resolution.
- Observation input is reduced to bounded `present`, `version` and `location` fields. Exact versions become GREEN/no drift; missing or mismatched approved capabilities become RED drift; absent observations are WARN/unobserved; unexpected capability IDs are surfaced as WARN/unexpected without copying arbitrary observation values or mutating anything.
- Definition validation rejects fields reserved for OR runtime-use policy or PW state, including role ceilings, action classification, bundles, assignment eligibility/task grants, Task Board and workflow-state fields.
- SpecPi and pi-mcp-adapter appear as accepted desired capabilities from the frozen candidate, but M04-T01 does not claim they are installed. Their delivery/compatibility remains owned by M04-T03.

## Contract tests

`tests/test_environment_capability_inventory_contract.py@6ce1b55188bcd80ba9ff0c443a54f05232f95ffe` verifies:

- coverage of every independently versioned frozen candidate component plus Chromium, generic base tooling and the repository-managed Pi instruction plane;
- desired-state derivation from canonical candidate/repository inputs without duplicated version literals or network/subprocess resolution;
- exact, missing, mismatched and unexpected observation classification;
- deterministic output and filtering of arbitrary credential/token observation fields;
- rejection of OR/PW policy-state fields.

## CI / readback

GitHub Actions run `36194185759` on exact SHA `45a083482855378e6085e261a6181376d4c2fa2d` completed **success**.

Its single `contract-build-and-smoke` job completed GREEN for:

- exact predecessor-binding verification, now including M02-T03;
- the complete candidate/image/runtime/Relay/instruction-plane/GraphQL/host-safety/host-doctor contract suite;
- the new Environment Capability Inventory contract suite;
- frozen Paseo child-image build;
- disposable image/provenance smoke;
- disposable persistence/ownership smoke;
- disposable Pi instruction-plane smoke;
- immutable foundation metadata inspection.

## Scope boundary

No reconcile/update behavior, capability installation, production/Tower deployment, host mutation, credential materialization, M04-T02 doctor aggregation, M04-T03 SpecPi/MCP delivery, OR policy or PW workflow authority was introduced.

## Outcome

GREEN implementation return for the stable M04-T01 acceptance surface, ready for required independent implementation review.
