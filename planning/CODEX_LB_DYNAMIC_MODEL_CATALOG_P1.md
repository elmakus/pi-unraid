# Strategic Plan P1 — Dynamic Codex-LB model catalog

Status: frozen
Cycle: 1
Entry subject: `elmakus/pi-unraid@b44938e6ca8c33ecebfba15b7a0ebd4752c1cdff:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/DEFINITION.toml@42e918b2af4e42af40aa4b313af1477b2cc1c7eb`
Definition: `codex-lb-dynamic-model-catalog@1`
Requirements: `requirements/CODEX_LB_DYNAMIC_MODEL_CATALOG.md`
Decision: `decisions/CLDMC_ADR_001_DYNAMIC_PROVIDER_DISCOVERY.md`

## Planning objective

Replace the production behavior in which Pi/Paseo effectively exposes a static Codex-LB model list with a repository-managed Pi provider extension that discovers the authenticated Codex-LB `/v1/models` catalog, persists a last-known-good catalog, and refreshes long-lived RPC sessions without container restart or repository edits when Codex-LB changes its exposed model IDs.

This plan does not change Codex-LB OAuth/account routing, the generic `openai-responses` request path, or automatic model-selection policy.

## Current implementation facts

- Production Pi is Pi 0.87.1 inside the accepted Paseo runtime.
- The live persistent Pi provider config currently contains provider `codex-lb` with only one configured model ID, while live Codex-LB exposes multiple IDs.
- Pi 0.87.1 supports extension `ProviderConfig.refreshModels`, persisted provider-scoped `models-store.json`, and `ModelRegistry.refresh({providers:[...]})`.
- RPC `get_available_models` reads the current runtime availability snapshot; therefore a session-lifecycle refresh is required for a long-running Paseo agent to see later catalog changes.
- The existing accepted production secret mount and provider-auth boundary remain authoritative. The extension consumes the credential resolved by Pi; it does not read or persist ChatGPT/Codex OAuth material.
- `config/pi-agent` is already the repository-managed Pi instruction-plane source and is deployed transactionally to `/home/paseo/.pi/agent` with rollback support. A direct TypeScript extension under its `extensions/` subtree is therefore the smallest reproducible delivery mechanism.
- The completed Paseo runtime has already accepted the provider-secret mount, persistent HOME and staged/rollback deployment mechanisms. This scope reuses those mechanisms instead of reopening the image/update architecture.

## Technical strategy

### Provider extension

Add one repository-managed global extension, nominally:

`config/pi-agent/extensions/codex-lb-dynamic-model-catalog.ts`

The extension registers/overlays provider `codex-lb` without changing the accepted request transport. Its `refreshModels` implementation shall:

1. consume the provider credential supplied by Pi's resolved auth path;
2. obtain the accepted Codex-LB base URL from the existing provider/environment contract;
3. on cache-only/offline initialization, publish or return the stored provider catalog when one exists;
4. on network refresh, perform one bounded authenticated `GET <baseUrl>/models`;
5. require an OpenAI-compatible catalog shape and non-empty string model IDs, normalize/deduplicate deterministically, and reject malformed responses without replacing good state;
6. map IDs to Pi model definitions using `openai-responses` and only verified metadata; unspecified capabilities use conservative Pi defaults;
7. persist the accepted model list through Pi's provider-scoped models store with `checkedAt` and available HTTP validators where useful;
8. leave the current/last-known-good catalog untouched on timeout, abort, auth rejection, invalid JSON, invalid catalog shape, or other transient discovery failure.

The extension must not log credentials or response headers that may contain sensitive data.

### Long-lived session refresh

On `session_start`, install one session-scoped bounded timer. The timer calls:

`ctx.modelRegistry.refresh({ providers: ["codex-lb"] })`

rather than reimplementing model-registry internals. Refresh overlap is suppressed: at most one Codex-LB refresh may be in flight per extension runtime. The timer is cleared idempotently on `session_shutdown`.

The default interval shall be modest (Planning target: 5 minutes) and configurable through a non-secret environment variable for deterministic tests. A short test-only interval is permitted in disposable fixtures. Refresh errors are observable but do not terminate the session or erase the accepted catalog.

The timer updates availability only; it never calls `setModel`. A catalog change therefore cannot automatically switch the user's selected model.

### Static-config migration

The production `codex-lb` provider config must remain the transport/auth bootstrap, but the accepted end state must not depend on a hardcoded `models` array.

Add a bounded repository-managed reconciliation helper for the Codex-LB provider entry. It shall:

- preserve unrelated providers and unrelated user config;
- preserve the accepted `baseUrl`, `api: openai-responses` and API-key reference/auth contract;
- remove the managed static model list only after the dynamic extension has passed disposable/staged acceptance;
- snapshot the exact prior provider config for rollback;
- fail closed on invalid/conflicting config rather than replacing the whole file.

The retired standalone-Pi path is not reopened as a production authority. Any legacy helper touched only for consistency must remain backward-safe and must not drive the Paseo production deployment.

## Milestones and Cards

### M01 — Dynamic provider implementation and deterministic proof

**M01-T01 — Extension + provider-config contract**

Implement the global Pi extension and the bounded provider-config reconciler. Add focused contract/unit tests covering catalog parsing, ID validation/deduplication, conservative metadata mapping, cache-only startup, persistence, timeout/auth/JSON failure behavior, overlap suppression, lifecycle cleanup, no automatic model switch, and secret-safe diagnostics.

Acceptance:
- no hardcoded Codex-LB model IDs in the new dynamic source;
- supported Pi 0.87.1 extension/provider APIs only;
- existing provider auth/transport contract preserved;
- static catalog migration is reversible and unrelated config is byte/semantically preserved as appropriate.

Review: REQUIRED independent implementation review.

**M01-T02 — Disposable live-RPC catalog acceptance**

Use a disposable temporary HOME and a local authenticated fake Codex-LB fixture. Install the exact managed instruction plane, start real Pi 0.87.1 in RPC mode, and prove through RPC `get_available_models`:

- initial fixture IDs appear;
- adding a synthetic ID becomes visible in the same running RPC process after bounded refresh;
- removing an ID disappears after refresh;
- a selected model is not automatically changed by catalog refresh;
- a forced catalog failure preserves the previous valid list;
- after shutdown/restart with network unavailable, the persisted last-known-good catalog is restored;
- no raw fixture key is written to managed config/evidence.

Use an injectable/short test interval; do not wait for the production cadence.

Review: REQUIRED independent implementation review.

### M02 — Staged and production rollout

**M02-T01 — Staged-HOME migration and rollback proof**

Apply the changed `config/pi-agent` tree to a disposable/staged clone of the production HOME using the existing instruction-plane transaction. Reconcile the Codex-LB provider config to the dynamic end state, preserving auth/base URL and unrelated config.

Acceptance:
- instruction-plane apply/status is GREEN;
- extension is auto-loaded by a fresh Pi RPC process;
- provider-config migration has exact pre-change snapshot and rollback proof;
- current real Codex-LB catalog can be read from the staged runtime without exposing the key;
- rollback restores the prior instruction-plane/provider-config state;
- no production HOME mutation yet.

Review: REQUIRED independent implementation review.

**M02-T02 — Production activation and live-catalog acceptance**

Perform bounded production HOME mutation only after M02-T01 GREEN. Capture pre-change instruction-plane/provider-config identities, apply the extension through the existing instruction-plane mechanism, migrate the provider config away from the static model list, and start a fresh production Pi/Paseo agent process/session so the extension loads. A Paseo container/image rebuild or restart is not required merely to activate model discovery unless implementation readback proves the upstream runtime requires it.

Acceptance:
- production runtime remains healthy;
- `get_available_models`/Paseo model picker exposes the current authenticated Codex-LB catalog rather than one hardcoded ID;
- the current catalog includes every model ID returned by the live Codex-LB endpoint at the same acceptance readback;
- request transport remains `openai-responses` through `codex-lb`;
- provider secret values are absent from Git/evidence/logs;
- last-known-good store is populated;
- full instruction-plane/environment health remains GREEN or any unrelated pre-existing degradation is explicitly unchanged;
- if activation fails, restore the exact pre-change provider/instruction-plane snapshot without destructive HOME rollback.

The add/remove/failure behavior itself is accepted from M01-T02/M02-T01 production-like real-Pi RPC evidence; production Codex-LB is not mutated merely to manufacture synthetic model IDs.

Review: REQUIRED independent implementation review.

### M03 — Final evidence and integration readiness

**M03-T01 — Scope reconciliation**

Reconcile CLDMC-REQ-001..012 against exact implementation/review evidence, verify no automatic routing/model-switch behavior was introduced, verify the separate Paseo update/distribution workstream was not modified, and record final integration/rollback readiness.

Review: REQUIRED independent final review before Close/integration.

## Requirement coverage

| Requirement | Primary proof |
|---|---|
| CLDMC-REQ-001 | M01-T01 source/contract + M01-T02 RPC |
| CLDMC-REQ-002 | M01-T02 same-process add-ID proof |
| CLDMC-REQ-003 | M01-T02 same-process remove-ID proof |
| CLDMC-REQ-004 | M01-T01 lifecycle timer + M01-T02 live RPC |
| CLDMC-REQ-005 | M01-T01 failure semantics + M01-T02 restart/offline LKG proof |
| CLDMC-REQ-006 | M01-T01 provider contract + M02-T02 production readback |
| CLDMC-REQ-007 | M01-T01 secret/auth boundary + M02-T02 sanitized evidence |
| CLDMC-REQ-008 | M01-T01 repository-managed extension + M02 instruction-plane deployment |
| CLDMC-REQ-009 | M01-T01 parser/metadata tests |
| CLDMC-REQ-010 | M01-T01 bounded configurable timer + M01-T02 accelerated fixture |
| CLDMC-REQ-011 | M01-T02/M02-T01 production-like acceptance + M02-T02 current live catalog |
| CLDMC-REQ-012 | M01-T01 no-setModel contract + M01-T02 selected-model stability |

## Gates and safety

- No Codex-LB service mutation is needed for this feature.
- No ChatGPT/Codex OAuth token may enter Pi config, Git or evidence.
- Production HOME mutation waits for disposable/staged GREEN evidence and has an exact bounded rollback anchor.
- Failure to fetch a catalog is degraded discovery, not permission to erase the last-known-good catalog.
- Invalid/empty catalog payloads fail closed and do not become accepted state.
- No automatic selection/failover is introduced.
- Existing unrelated user provider configuration must not be overwritten.
- The separate `feature-paseo-update-distribution` scope is not modified by this plan.

## Planner audit

GREEN.

The plan covers every accepted requirement and the Definition decision without adding a new product choice. It uses the existing Pi extension, model-registry, instruction-plane, secret and production rollback mechanisms; separates deterministic synthetic catalog-change proof from live production readback; and avoids requiring a container rebuild/restart for ordinary future Codex-LB catalog changes.
