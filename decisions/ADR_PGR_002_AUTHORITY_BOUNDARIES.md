# Decision — PW, OR and pi-unraid have separate authority domains

- Decision ID: `ADR-PGR-002`
- Date: `2026-09-24`
- Status: `definition-active`
- Definition subject: `paseo-gui-runtime@2`

## Decision

- Project Workflow owns managed legality, canonical workflow state, review semantics and user stops.
- Orchestration Runtime owns concrete runtime scheduling, role/tool assignment, worker/session lifecycle and worker/worktree realization subject to PW legality.
- pi-unraid owns the execution environment, workspace substrate, installed capability availability, deployment and host administration.
- The pi-unraid **Environment Capability Inventory** records environment availability/provenance/version/delivery/health only. OR's Tool Registry owns runtime-use classification/bundles/assignment policy.
- pi-unraid may locally enforce no-write-on-main for direct Main/Pi ad-hoc mutation but does not claim universal semantic ownership of that cross-runtime rule.
- Pi-owned policy guards enforce environment/host safety only; PW/OR semantic rules are consumed from their owning contracts.

## Consequences

No private Paseo/OR state becomes a second workflow authority. Future PWv2.1 and OR Pi extensions remain separate products/interfaces; pi-unraid installs/configures released artifacts but does not take ownership of their semantics.
