# M01-T01 production acceptance evidence

Verdict: GREEN.

Final implementation source subject:
- `elmakus/pi-unraid@00f567ddd3dc27210407bc88da2e8452558d3eb7`
- workstream: `issue-paseo-codex-lb-env-propagation`
- production candidate image: `pi-unraid:paseo-codex-lb-env-bc87a92`
- candidate image ID: `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`

The earlier production cutover had already reached the expected candidate image when this final reconciliation resumed. It was not replayed. Subsequent writes were bounded instruction-plane updates plus supported Paseo daemon-worker reloads required to activate the final managed extension/policy files; the Docker container itself was not recreated again.

## Permanent Paseo -> Pi credential propagation

The repository-managed child image installs `scripts/paseo-codex-lb-entrypoint.sh` as the Paseo entrypoint bridge. Canonical Compose supplies only `PI_CODEX_LB_SECRET_FILE=/run/secrets/pi-unraid-codex-lb`, mounts the dedicated file-backed `codex_lb_client` secret, and preserves `host.docker.internal:host-gateway`.

The wrapper clears stale raw-key state, reads and validates the dedicated secret file, exports `CODEX_LB_API_KEY` only into the runtime process environment, and then execs the pinned upstream Paseo entrypoint. No Paseo upstream source patch and no Pi upstream source patch is used.

Current production readback:
- container `pi-unraid-paseo-1` ID `9477662964b187f85b3f9e1a59e0ecd7143f4069e646472d7872a3cebef981af`;
- image ID `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`, exactly matching the accepted candidate image;
- start time `2026-09-28T11:33:26.512043639Z`;
- Docker restart count `0`;
- health `healthy`;
- Docker configured environment contains `PI_CODEX_LB_SECRET_FILE` but does not contain `CODEX_LB_API_KEY`;
- current Paseo daemon and terminal worker process environments contain `CODEX_LB_API_KEY`, proving the dedicated secret is propagated at runtime rather than persisted in Docker `Config.Env`.

The current daemon provider diagnostic is ready and Pi 0.87.1 is resolved from `/usr/local/bin/pi`.

## Dynamic catalog and verified capability metadata

The final repository-managed Codex-LB extension keeps conservative defaults when capability metadata is absent, but now preserves explicit capability metadata returned by authenticated Codex-LB `/v1/models`. It never infers capability from a model ID.

For `gpt-6-luna`, Codex-LB explicitly reports reasoning support, a 272000-token context window, and supported reasoning efforts `low`, `medium`, `high`, `xhigh`, and `max`. The Pi RPC readback on the final source reports:
- provider/model `codex-lb/gpt-6-luna`;
- `reasoning=true`;
- `contextWindow=272000`;
- `thinkingLevelMap` with `low/medium/high/xhigh/max` mapped and `off/minimal` unsupported.

After a supported `paseo restart` of only the daemon worker (supervisor launch retained), Paseo's own provider snapshot reports exactly nine Codex-LB models and exposes the same Luna thinking options. The Docker container ID, start time and restart count remained unchanged by the worker reload.

The final network refresh intentionally fetches the small Codex-LB catalog body instead of relying on conditional ETag reuse, so capability metadata changes cannot remain hidden behind an older last-known-good body. Offline/cache-only startup still retains the sanitized last-known-good catalog.

## Durable LLM-test policy — Luna low only

The policy is durable and machine-enforced in the managed Pi instruction plane:
- `config/pi-agent/policies/LLM_TEST_POLICY.md`;
- `config/pi-agent/policies/llm-test-policy.json`;
- `config/pi-agent/AGENTS.md`;
- `config/pi-agent/bin/run-llm-test.sh`;
- `docs/LLM_TEST_POLICY.md`.

For every real LLM inference test:
- provider is fixed to `codex-lb`;
- model is fixed to `gpt-6-luna`;
- thinking is fixed to `low`;
- `gpt-6-astra` is explicitly forbidden;
- fallback is disabled;
- if Luna or low reasoning is unavailable, the test must fail/block rather than substitute another model or thinking level.

The canonical launcher is deployed as executable mode `0755`. The instruction-plane installer now owns mode semantics: managed `bin/` tools are `0755`, other managed instruction/policy files are `0644`, mode participates in status validation, and an incorrect mode is repaired by bounded apply. Current production instruction-plane status is `in_sync=true` with source digest `sha256:af297c012fa0bd0efeea8b485eb941e732a74bc2c37c6e75084b2f1d2cf53811`.

## Real LLM acceptance

The final real inference acceptance was executed only through the canonical launcher after the exact final source had been deployed and the Paseo daemon worker reloaded.

Agent readback:
- agent ID `509f472c-3bac-43de-b10a-0e4f579fcc18`;
- name `LLM-TEST:gpt-6-luna:low`;
- provider `pi`;
- model `codex-lb/gpt-6-luna`;
- thinking `low`;
- completion status successful/idle;
- prompt requested exactly `TEST_OK`;
- assistant output was exactly `TEST_OK`.

No Astra inference was used for the accepted test. Earlier diagnostic attempts that did not read back `Thinking: low` are not accepted as LLM-test evidence.

## Test and security verification

Final source verification:
- full Python suite: `403/403` GREEN;
- dynamic Codex-LB Node core suite: GREEN;
- `git diff --check`: GREEN;
- direct Pi RPC: nine Codex-LB models, Luna verified reasoning metadata present;
- Paseo provider snapshot: nine Codex-LB models, Luna thinking options `low, medium, high, xhigh, max`;
- tracked repository exact dedicated-secret scan: zero hits;
- production HOME exact dedicated-secret scan: zero hits;
- Docker configured environment: raw `CODEX_LB_API_KEY` absent.

The tests cover the entrypoint fail-closed/degraded behavior, Compose secret/host wiring, secret-safe logging/configuration, dynamic catalog parsing and LKG semantics, verified reasoning metadata, no automatic `setModel`, exact LLM-test policy, and managed executable-mode enforcement.

## Rollback readiness

The pre-repair runtime image remains available as `pi-unraid:paseo-rollback-pre-codex-lb-env-fix` with image ID `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`.

A non-empty rollback Compose file remains at `/mnt/user/appdata/pi-unraid/codex-lb-env-fix/compose.rollback.yaml`. It pins the rollback image while retaining the accepted production ancillary mounts. No rollback was executed because the final production state is healthy and GREEN.

M01-T01 is ready for its REQUIRED fresh independent review.
