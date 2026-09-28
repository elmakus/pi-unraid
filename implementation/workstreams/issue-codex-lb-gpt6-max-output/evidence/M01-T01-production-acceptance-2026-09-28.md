# M01-T01 production acceptance evidence

Date: 2026-09-28
Repair subject: `repair:codex-lb-gpt6-max-output-128k:v1`

## Contribution and source verification

- Upstream contribution PR: `Soju06/codex-lb#2528`, OPEN at head `d64c94338305315d28d1e5899a3aee9c5cb53771`.
- Behavior patch commit on current upstream-main lineage: `641b4f30eee138eefad06e014f2087c30f61e4d5`.
- Contribution branch full `tests/integration/test_v1_models.py`: **62/62 GREEN**.
- Targeted GPT-6 fallback plus raw-upstream-precedence tests: **2/2 GREEN**.
- OpenSpec change `advertise-gpt6-max-output-tokens`: strict validation GREEN; repository spec validation GREEN.
- Upstream CI readback after OpenSpec push shows OpenSpec validation, Ruff, type check, migration checks, package build, Docker build, browser smoke and other completed checks GREEN; remaining pytest matrix jobs were still running at this acceptance snapshot. Upstream merge is not claimed.

## Canonical downstream artifact

The production artifact is intentionally based on the already accepted production release rather than unrelated current upstream-main changes:

- upstream tag `v1.25.0-beta.9` peels to `69f128afcbc616d9f8e924ca6583f7031d75cf82`;
- private patch commit `43afbc34b003da3be2485299092bbcf871b492a1` has that exact commit as its only parent;
- private tag `v1.25.0-beta.9-private.1` peels to the private patch commit;
- published image `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1` has OCI index digest `sha256:6202eb5867a87028e7ac9b4c2a29131f2f275fe610d6a556beaf695f8b360ded` and linux/amd64 manifest digest `sha256:215819235c53c8a17bd7fca68bdaf2d1caa9ac4e5bd492ba41aa5f8c641c0957`;
- pulled amd64 image ID is `sha256:d4a6d8ddbaff85d9091a18a2b25b1d5df6d60648fc41ed17c5bd2848d6d7b270`;
- image `/app/app/modules/proxy/api.py` SHA-256 exactly matches the private source file: `905e2539d426f2a05f5b7558116b64f984546378c21b6111d3947e5dd02bfa76`;
- the exact private source `tests/integration/test_v1_models.py` is **62/62 GREEN**.

## Production cutover and rollback

`codex-lb-clean` was cut over by preserving the complete previous container as a stopped rollback anchor and recreating the production name with the versioned private image while retaining the existing network, ports, appdata bind, encryption-key-file locator, timezone and restart policy.

Post-cutover production:
- container: `codex-lb-clean`;
- image reference: `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1`;
- image ID: `sha256:d4a6d8ddbaff85d9091a18a2b25b1d5df6d60648fc41ed17c5bd2848d6d7b270`;
- state: running; restart count: 0;
- application startup completed normally, database schema reported current, persisted nine-model registry snapshot applied, live registry refresh completed, and authenticated `/v1/models` returned HTTP 200.

Rollback anchor:
- container: `codex-lb-clean-rollback-gpt6-output-20260928`;
- exact old image reference: `ghcr.io/soju06/codex-lb:1.25.0-beta.9`;
- exact old image ID: `sha256:867eeb726bf3d8141ed18ac35a827d3a3d0f49e6a6cca285567adf1f98102f0f`;
- state: stopped/exited; restart count: 0.

Rollback requires no data migration: remove the new container, rename the retained old container back to `codex-lb-clean`, and start it.

## Live capability readback

Authenticated production `GET /v1/models` returns 9 models. For each of `gpt-6-astra`, `gpt-6-sol` and `gpt-6-luna`:
- `context_length = 272000`;
- `metadata.context_window = 272000`;
- `max_output_tokens = 128000`;
- `maxOutputTokens = 128000`;
- `metadata.max_output_tokens = 128000`;
- `capabilities.max_output_tokens = 128000`.

Therefore this repair changes only the missing output-capability advertisement; the existing context-window value remains unchanged.

Pi/Paseo convergence was then read back after dynamic refresh:
- Paseo lists the same 9 Codex-LB models;
- Pi persisted dynamic definitions contain `contextWindow=272000`, `maxTokens=128000`, `reasoning=true` for Astra, Sol and Luna.

No real LLM inference was required or executed. The existing real-LLM test policy remains unchanged: if any future real inference test is needed, it must use `codex-lb/gpt-6-luna` with thinking `low`, never Astra, with no fallback.

## Acceptance

GREEN against the M01-T01 implementation acceptance: documented GPT-6 output capability is advertised at 128000 across the OpenAI-compatible model fields, explicit upstream integer precedence has regression coverage, the equivalent upstream contribution exists, the production image is traceable to exact accepted upstream release lineage plus the bounded patch, production is healthy/running with a verified exact rollback anchor, Pi/Paseo converged to `maxTokens=128000`, and context/auth/routing/model-selection behavior is not changed by the repair.
