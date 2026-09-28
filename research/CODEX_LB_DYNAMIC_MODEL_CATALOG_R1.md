# Research — dynamic Codex-LB model catalog for Pi/Paseo

Research ID: `codex-lb-dynamic-model-catalog-r1`
Status: `consumed`
Origin role: `brainstorming`
Origin subject: `codex-lb-dynamic-model-catalog@1`
Return target: `brainstorming`
Return reconciliation: `applied`

## Question

Determine the smallest safe integration that makes Pi/Paseo expose the live Codex-LB model catalog without hardcoded model IDs, including how active RPC sessions learn about models added later and how transient catalog failures behave.

## Evidence checked

- Installed Pi Coding Agent 0.87.1 documentation and runtime source on production Tower:
  - `docs/models.md`
  - `docs/custom-provider.md`
  - extension provider API types
  - `ModelRuntime.refresh()`
  - RPC `get_available_models` handling.
- Production Pi/Paseo state on Tower:
  - `~/.pi/agent/models.json` currently defines only `gpt-6-sol` for provider `codex-lb`;
  - the authenticated Codex-LB `GET /v1/models` currently returns nine model IDs:
    `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`, `gpt-reserve`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, and `codex-auto-review`.
- Existing project authority and prior research:
  - `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md`
  - `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`.

Tracker/discussion and practitioner/community evidence are not material to this narrow runtime contract; the installed upstream API and live production behavior are stronger evidence.

## Findings

1. Static `models.json` cannot satisfy the requirement. Pi treats its `models` array as an explicit catalog, so new Codex-LB IDs do not appear automatically.

2. Pi 0.87.1 explicitly supports dynamic provider discovery through a provider extension with `refreshModels`. This is the intended upstream mechanism when a model catalog comes from a live service.

3. Pi RPC's `get_available_models` returns `ModelRuntime.getAvailableSnapshot()`; it does not itself perform a network refresh. Therefore merely defining `refreshModels` is sufficient for startup/background refreshes initiated by Pi, but is not by itself a guarantee that a long-lived Paseo session immediately sees a model added later.

4. Pi's extension API allows `pi.registerProvider()` after initial load and states that later registrations take effect immediately. A provider extension can therefore keep a bounded timer for live discovery: fetch the authenticated Codex-LB catalog, compare IDs with the last accepted catalog, and re-register/publish the provider only when the catalog changes. This updates the runtime model snapshot without editing `models.json` or restarting the Pi/Paseo container.

5. The timer can be lifecycle-bounded using Pi's `session_start` and `session_shutdown` extension events. No external daemon or Codex-LB change is required.

6. Startup should use Pi's normal `refreshModels`/models-store persistence path so a last-known-good catalog can survive a transient Codex-LB outage. A failed live refresh must not replace the current catalog with an empty list.

7. Model traffic remains on the existing generic `openai-responses` path through Codex-LB. Dynamic discovery does not move ChatGPT OAuth ownership into Pi and does not require Pi to understand Codex-LB account routing.

## Recommended scope

Implement one small global Pi provider extension for `codex-lb` that:
- authenticates to the existing `/v1/models` endpoint with the existing `CODEX_LB_API_KEY`;
- translates every returned model ID into the Pi provider catalog using the existing OpenAI Responses transport defaults;
- persists a last-known-good catalog through the supported model-store refresh path;
- refreshes the catalog in active sessions on a bounded interval and publishes only actual catalog changes;
- never hardcodes model IDs;
- keeps the last-known-good catalog on fetch/parse/auth failure;
- is installed reproducibly by `pi-unraid`, not manually edited in production home state.

Acceptance should prove: current nine IDs appear in Paseo, a synthetic/new catalog ID becomes visible in an already-running production-like RPC session without editing `models.json` or restarting the container, removal is reflected after refresh, and a temporary catalog failure preserves the previous list.

## Limitations

The exact polling interval is an implementation tuning parameter rather than a product-level requirement. The smallest reasonable default is a few minutes; tests should avoid waiting for wall-clock production intervals by exposing the refresh function directly or using an injectable timer.

The Codex-LB `/v1/models` payload primarily supplies IDs. Model-specific context/cost/reasoning metadata may need conservative shared defaults unless Codex-LB later exposes richer metadata. This does not block catalog discovery but must not invent unsupported capabilities.

## Conflict summary

None. Existing project authority deliberately deferred live model discovery in Phase 1; this new workstream is the later scope that activates it.
