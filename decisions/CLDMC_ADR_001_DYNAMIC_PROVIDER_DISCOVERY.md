# Decision — Dynamic Codex-LB model discovery is a Pi provider-extension responsibility

- Decision ID: `CLDMC-ADR-001`
- Date: `2026-09-28`
- Status: `accepted`
- Authority: promoted Definition scope `codex-lb-dynamic-model-catalog@1`
- Related requirements: `CLDMC-REQ-001..012`

## Context

The production Pi/Paseo runtime currently exposes only the Codex-LB model IDs explicitly present in Pi configuration. Codex-LB already exposes an authenticated OpenAI-compatible `/v1/models` catalog, while Pi 0.87.1 supports dynamic provider discovery through provider extensions and `refreshModels`. Pi RPC model selection reads a runtime availability snapshot, so startup-only discovery is insufficient for long-lived Paseo sessions.

## Decision

- Dynamic Codex-LB model discovery is implemented as one small global Pi provider extension delivered by `pi-unraid`.
- The extension queries the existing authenticated Codex-LB `/v1/models` endpoint and maps validated returned IDs into the `codex-lb` Pi provider using the existing `openai-responses` transport.
- The extension uses Pi's supported model refresh/persistence mechanism for startup/last-known-good state and a bounded session-lifecycle refresh mechanism for long-lived RPC sessions.
- Catalog refreshes publish runtime changes only when the accepted catalog changes.
- Transient discovery failure preserves the current/last-known-good catalog.
- Model-specific capability metadata uses verified metadata when available and conservative defaults otherwise.
- This feature does not modify Codex-LB, does not move OAuth/account-routing ownership into Pi, and does not automatically change the user's selected model.

## Rationale

This keeps model-catalog ownership with Codex-LB, uses Pi's native extension/provider interfaces, avoids repository churn for each newly exposed model, and updates active Paseo sessions without coupling discovery to container restarts.

## Rejected alternatives

- Hardcoded model IDs in `models.json`: rejected because every Codex-LB catalog change would require configuration/repository maintenance.
- Startup-only dynamic discovery: rejected because existing long-lived RPC sessions read a runtime snapshot and would not reliably observe later catalog changes.
- Polling or modifying Codex-LB itself for Paseo-specific state: rejected because Codex-LB already exposes the required catalog and should remain an independent service.
- Automatic model failover/selection: rejected as outside this scope and contrary to explicit manual model selection.

## Consequences

Planning must define the minimal extension packaging, refresh cadence, metadata defaults, failure observability, deterministic tests, and staged production acceptance. The implementation must remain compatible with the existing Codex-LB secret and transport boundary.
