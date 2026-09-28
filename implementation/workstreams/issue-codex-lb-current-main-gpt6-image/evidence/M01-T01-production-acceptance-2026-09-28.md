# M01-T01 production acceptance evidence

Date: 2026-09-28
Repair subject: `repair:codex-lb-current-main-plus-gpt6-128k:v1`

## Exact source composition

- Accepted upstream source: `Soju06/codex-lb@main` commit `f8ffbac2099a113fba54dfd8d77774f5bca80ffa`.
- Final fork source: `elmakus/codex-lb@34511dd6e73e4dbc03dd54112e911fa9149f3440`.
- Final fork source ancestry proves both exact upstream main `f8ffbac2099a113fba54dfd8d77774f5bca80ffa` and the complete GPT-6 contribution head `d64c94338305315d28d1e5899a3aee9c5cb53771` are ancestors.
- Upstream main was re-fetched immediately after production cutover and remained exactly `f8ffbac2099a113fba54dfd8d77774f5bca80ffa`; no upstream movement occurred during build/cutover.
- Diff against exact upstream main contains only the two fork-local GHCR publisher workflows plus the GPT-6 repair implementation/tests/OpenSpec files: `.github/workflows/publish-main-image.yml`, `.github/workflows/publish-private-image.yml`, `app/modules/proxy/api.py`, `tests/integration/test_v1_models.py`, and the three `openspec/changes/advertise-gpt6-max-output-tokens/*` files.
- `git diff --check upstream/main..34511dd6...` is GREEN.
- Exact final fork source `tests/integration/test_v1_models.py`: **62/62 GREEN**.

## GHCR artifact

GitHub Actions run `36462879195` built final source `34511dd6e73e4dbc03dd54112e911fa9149f3440` successfully and published both mutable `main` and immutable `sha-34511dd` tags.

- Production tag: `ghcr.io/elmakus/codex-lb:sha-34511dd`.
- OCI index digest: `sha256:fff96614507c45cca70e980a5390eb36a67295ec74d0863a01ca065efe59e2bb`.
- linux/amd64 manifest digest: `sha256:d38a6f2dd5a37119b7cad3a290c96016b94f1b7202dfe2b2c963751fa304eb5a`.
- Pulled local image ID: `sha256:f311d34deb4c1859ad7b4e1bfefef0e64b4e3646a9704dc4d56d9c277cb79742`.
- Image OCI source revision label: `34511dd6e73e4dbc03dd54112e911fa9149f3440`.
- `ghcr.io/elmakus/codex-lb:main` and `ghcr.io/elmakus/codex-lb:sha-34511dd` resolve to the same OCI index digest above at acceptance time.
- Image `/app/app/modules/proxy/api.py` SHA-256 equals exact final source file SHA-256: `905e2539d426f2a05f5b7558116b64f984546378c21b6111d3947e5dd02bfa76`.
- Image source contains GPT-6 Astra/Sol/Luna entries at `128_000` in `_V1_MAX_OUTPUT_TOKEN_OVERRIDES`.

## Production cutover

Production `codex-lb-clean` was cut over to the immutable SHA tag while preserving the existing network, ports, appdata bind, encryption-key-file pointer, timezone and restart policy.

Post-cutover:
- `codex-lb-clean` image reference: `ghcr.io/elmakus/codex-lb:sha-34511dd`;
- image ID: `sha256:f311d34deb4c1859ad7b4e1bfefef0e64b4e3646a9704dc4d56d9c277cb79742`;
- state: running; restart count: 0;
- startup SQLite quick_check passed; schema reported current; application startup completed; nine-model registry snapshot loaded and refreshed; authenticated `/v1/models` returned HTTP 200.

Immediate rollback anchor:
- container: `codex-lb-clean-rollback-pre-main-gpt6-20260928`;
- image: `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1`;
- image ID: `sha256:d4a6d8ddbaff85d9091a18a2b25b1d5df6d60648fc41ed17c5bd2848d6d7b270`;
- state: stopped/exited; restart count: 0.

The older official beta.9 rollback container from the prior repair remains separately preserved as historical rollback depth.

## Unraid persistence

The Unraid template `/boot/config/plugins/dockerMan/templates-user/my-codex-lb-clean.xml` now references the same immutable production image `ghcr.io/elmakus/codex-lb:sha-34511dd`. The previous template was backed up before mutation as `my-codex-lb-clean.xml.bak-20260928-current-main-gpt6`.

## Live model readback

Authenticated production `/v1/models` returns 9 models. For each of `gpt-6-astra`, `gpt-6-sol`, and `gpt-6-luna`:
- `context_length = 272000`;
- `max_output_tokens = 128000`;
- `maxOutputTokens = 128000`;
- `metadata.max_output_tokens = 128000`;
- `capabilities.max_output_tokens = 128000`.

Pi/Paseo dynamic state converged after refresh:
- Paseo lists all 9 Codex-LB models;
- Pi persisted definitions contain `contextWindow=272000`, `maxTokens=128000`, `reasoning=true` for Astra, Sol and Luna.

No real LLM inference was executed. Existing real-LLM test policy remains unchanged: only `codex-lb/gpt-6-luna` with thinking `low`, never Astra, with no fallback.

## Acceptance

GREEN against the M01-T01 implementation contract: production now runs an immutable image whose source contains the complete exact current upstream main plus the bounded GPT-6 repair and fork publisher workflows, GHCR/source provenance is verified, the Unraid template is pinned to the same immutable image, rollback to the prior private beta.9 deployment is retained, the service is healthy, and Codex-LB/Pi/Paseo continue to expose 128000 max output for all three GPT-6 models.
