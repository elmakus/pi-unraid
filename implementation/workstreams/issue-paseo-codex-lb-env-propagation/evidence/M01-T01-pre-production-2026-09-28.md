# M01-T01 pre-production evidence

Implementation source subject: `elmakus/pi-unraid@bc87a92fe0e13bda5061111edb2ea17e6de9a4a5`.

## Static and deterministic verification

- Targeted repair contracts: GREEN.
- Full Python suite: `402/402` GREEN.
- Dynamic Codex-LB Node core suite: GREEN.
- `git diff --check`: GREEN.
- Canonical Compose renders with the dedicated file-backed Codex-LB secret and no raw credential environment value.
- Real LLM-test policy is durable in `docs/LLM_TEST_POLICY.md`, `config/llm-test-policy.json`, `config/pi-agent/AGENTS.md` and the canonical launcher `scripts/run-llm-test.sh`.
- Machine policy fixes every real LLM test to provider `codex-lb`, model `gpt-6-luna`, thinking `low`, with fallback disabled and `gpt-6-astra` explicitly forbidden.

No real LLM inference was executed during these tests; catalog enumeration and provider metadata checks are non-inference operations.

## Candidate image

- Final tag: `pi-unraid:paseo-codex-lb-env-bc87a92`.
- Image ID: `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`.
- Docker ENTRYPOINT remains inherited as `/usr/bin/tini -- /usr/local/bin/paseo-docker-entrypoint`.
- `/usr/local/bin/paseo-docker-entrypoint` is a symlink to the project-owned bounded wrapper; the exact pinned upstream entrypoint is retained at `/usr/local/libexec/pi-unraid/paseo-docker-entrypoint.upstream`.
- Disposable Compose start/recreate acceptance without a usable Codex-LB secret is GREEN, proving degraded startup remains available.

## Staged cold-catalog acceptance

A disposable staged HOME copied the production Pi instruction/config surface but removed `models-store.json` before daemon start. The final candidate image plus the updated instruction plane then started a fresh Paseo daemon with the real dedicated secret mounted read-only.

`paseo provider models pi --no-headers` returned exactly the live nine-model Codex-LB catalog:

`codex-auto-review, gpt-5.5, gpt-5.6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-6-astra, gpt-6-luna, gpt-6-sol, gpt-reserve`.

A new provider-scoped `models-store.json` was created from the cold state and its IDs matched a same-window authenticated `/v1/models` readback exactly. This proves the result did not come from a copied LKG cache.

The staged Paseo worker process had the dedicated credential in its runtime process environment, while Docker `Config.Env` did not contain `CODEX_LB_API_KEY`. Installed Paseo 0.9.2 spawn code was independently inspected: external Pi child processes derive from daemon `process.env` and remove only Paseo/Electron runtime-control keys, so the dedicated credential is inherited by Pi without a Paseo source patch.

## Production pre-state

- Container: `pi-unraid-paseo-1`.
- Exact container ID prefix: `fb0722489b57`.
- Exact image ID: `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`.
- Configured image ref: `pi-unraid:paseo-b4e0c1e7c276`.
- Start time: `2026-09-28T09:16:28.292365808Z`; restart count `0`; health `healthy`.
- Current Compose files: `/mnt/user/appdata/pi-unraid/m07-t03/compose.base.yaml` and `/mnt/user/appdata/pi-unraid/m07-t03/compose.override.yaml`.
- Pre-state Compose SHA-256: base `60f8584911561dd7e9d5bc240845865aa1dc1f56df867dfca8f3e074b73ae70f`; override `fe07ab558452dd70422d13beca39a1abe3337399d153aecdd06cd3d27d2381f5`.
- Existing dedicated Codex-LB mount is read-only and host-gateway is present.
- Provider config is already dynamic; auth shadow is absent; both provider/auth rollback anchors remain available.
- Instruction plane is intentionally not yet in sync with this repair branch because production has not received the immediate-refresh and LLM-test-policy update.

Production mutation has not yet occurred at this evidence checkpoint.
