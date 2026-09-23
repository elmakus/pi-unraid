# Decision — Codex-LB is the Phase 1 ChatGPT/Codex access layer

- Decision ID: `PIB-ADR-005`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Supersedes: direct-Pi-OAuth requirement `PIB-REQ-004@R1` and the R1 Codex-LB/multi-account Phase 1 exclusion; narrows `PIB-ADR-001` only for this accepted access-layer dependency
- Related requirements: `PIB-REQ-004, PIB-REQ-019, PIB-REQ-022..024`
- Related milestone/card: remaining M03 work; old `M03-T01` is superseded

## Context

Before the first production Pi deployment, the user changed the Phase 1 architecture. R1 required Pi to authenticate directly with one ChatGPT Plus/Pro account and explicitly excluded Codex-LB/multi-account routing. The target now requires Codex-LB from the first real Pi model interaction.

Current research confirms that Pi can use Codex-LB through Pi's supported OpenAI Responses-compatible client path without embedding Codex-LB or exporting pooled ChatGPT OAuth tokens into Pi.

## Decision

- Codex-LB is the mandatory ChatGPT/Codex access, OAuth and account-routing layer for Phase 1 from the first real Pi model interaction.
- Direct Pi built-in ChatGPT/Codex OAuth is not a required, fallback or acceptance path for Phase 1 and must not be performed as part of bootstrap acceptance.
- ChatGPT/Codex OAuth login, encrypted token persistence, refresh and pooled-account eligibility/routing belong to Codex-LB.
- Pi uses an authenticated Codex-LB client credential and a supported OpenAI Responses-compatible endpoint. Phase 1 uses the generic Pi `openai-responses` compatibility seam to Codex-LB `/v1`; it does not feed an opaque Codex-LB API key into Pi's native `openai-codex-responses` OAuth/JWT path.
- Pi does not import, export, mount or manage pooled ChatGPT access/refresh tokens.
- Codex-LB remains an independently deployed/persistent service on Unraid with its own data/backup lifecycle. It is not embedded into the Pi image/container and its appdata is not mounted into Pi.
- The existing Tower Codex-LB deployment is the intended dependency after its fork/image freshness and Pi-client compatibility are reconciled and verified by the replanned M03 path.
- Multi-account selection/failover semantics are Codex-LB-owned. Phase 1 does not promise transparent migration of hard account-owned continuation state when Codex-LB cannot safely move it.
- M01 and M02 remain completed historical checkpoints. Their implementation/evidence is not reopened merely because the external model-access architecture changed before production deployment.

## Rationale

This centralizes ChatGPT OAuth/account state in the already-persistent multi-account service, keeps Pi's container focused on Pi/session/development state, avoids duplicate OAuth stores, and permits account pooling without teaching Pi about individual account tokens.

Using Pi's generic Responses-compatible client path matches the proxy contract. Pi's native Codex transport expects a real ChatGPT JWT and extracts a ChatGPT account id, so substituting an opaque Codex-LB client key there would be the wrong authentication boundary.

## Alternatives considered

- Direct Pi built-in ChatGPT OAuth: rejected by explicit user redefinition.
- Embed a second Codex-LB inside the Pi container/Compose lifecycle: rejected because it couples replaceable Pi lifecycle to independent OAuth/account persistence and duplicates the already-running service.
- Export one Codex-LB account's OAuth tokens into Pi and use Pi native Codex auth: rejected because it bypasses pooling, duplicates secret ownership and restores the direct-token architecture the user replaced.
- Build a custom Pi provider extension immediately: rejected because current Pi/Codex-LB APIs already provide a smaller supported `openai-responses` compatibility seam.

## Consequences

- Requirements move to Definition R2 and remove Codex-LB/multi-account routing from Phase 1 non-goals.
- Strategic Planning must replace the stale remaining R1/M03 strategy before any production deployment.
- M03 must first reconcile/verify the selected Codex-LB dependency and a dedicated Pi client credential, then configure/deploy Pi to use that dependency.
- Pi authentication acceptance becomes a routed model-call proof through Codex-LB rather than Pi `/login` against ChatGPT.
- Codex-LB unavailability is a real external dependency failure for model access; Pi terminal/session/Git state may remain available but model calls cannot be claimed healthy solely from Pi container health.
- Secret evidence must remain sanitized; no ChatGPT OAuth token or full Codex-LB client key belongs in Git.
- Existing M01/M02 checkpoint evidence remains historical authority for the behavior it already proved.

## Required authoritative updates

- Requirements: `requirements/PI_UNRAID_BOOTSTRAP.md` R2.
- Planning: new Master Plan revision covering the changed M03 dependency/order/acceptance.
- Execution Prep: discard/supersede the old R1 M03 deployment Card and materialize new Cards only after the new plan is approved.
- PROJECT/workstream pointers: include this decision and R2 Definition state.

## Provenance

- Explicit user redefinition in the active `feature-pi-unraid-bootstrap` workstream before production deployment.
- Evidence: `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`.
