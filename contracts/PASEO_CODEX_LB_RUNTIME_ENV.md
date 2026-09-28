# Technical contract — Paseo Codex-LB runtime environment repair

## Secret propagation

- Canonical repository deployment mounts the dedicated host secret source `${PI_CODEX_LB_SECRET_SOURCE:-/mnt/user/appdata/pi-unraid/secrets/codex-lb.env}` read-only as `/run/secrets/pi-unraid-codex-lb`.
- The image installs a project-owned wrapper at the exact upstream Paseo Docker entrypoint path while preserving the original pinned upstream entrypoint under a separate immutable path.
- At startup the wrapper reads only `PI_CODEX_LB_SECRET_FILE` (default `/run/secrets/pi-unraid-codex-lb`).
- Empty/absent secret means Codex-LB remains unavailable but Paseo may start; a non-empty malformed secret fails closed without printing secret material.
- A valid secret is exported as `CODEX_LB_API_KEY` only in the running process environment, then the wrapper `exec`s the original upstream Paseo entrypoint.
- `CODEX_LB_API_KEY` must not be written into Compose `environment`, Docker image `ENV`, Git, logs or evidence. Docker configured `Config.Env` must not contain the credential value.
- Canonical Compose also restores `host.docker.internal:host-gateway` because the accepted provider URL uses that hostname.

## Upstream compatibility

- The build must fail if the pinned upstream entrypoint is absent instead of silently installing an unusable wrapper.
- Paseo remains the owner of daemon startup/user-drop behavior; the wrapper may only inject the dedicated project credential then delegate.
- Pi children launched by Paseo inherit the daemon environment; no Paseo server source patch and no Pi source patch is permitted.

## Verified model capability metadata

- Dynamic catalog discovery may expose reasoning/thinking controls only from explicit Codex-LB `/v1/models` capability metadata; model IDs themselves are never used to infer capabilities.
- When `supported_reasoning_levels` is explicitly supplied, Pi `thinkingLevelMap` must represent exactly those known levels and mark omitted levels unsupported.
- Explicit positive context/output limits may be adopted; missing or unusable fields retain conservative defaults.
- Persisted last-known-good catalog entries must retain the sanitized verified capability metadata so offline/cache-only startup does not silently downgrade a previously verified reasoning model.
- If verified reasoning metadata is absent, the model remains conservative `reasoning=false`.

## Real LLM test policy

- Any test, smoke, acceptance probe or verification that intentionally causes a real LLM inference MUST use provider/model `codex-lb/gpt-6-luna` and thinking/reasoning effort `low`.
- `gpt-6-astra` MUST NEVER be used for real LLM test execution.
- The restriction does not prohibit Astra appearing as catalog/fixture text or being selected by a human for normal interactive work outside tests.
- The rule must exist in a dedicated human-readable document, the global Pi `AGENTS.md`, and a machine-readable policy consumed by the canonical LLM-test launcher/validator.
- Contract tests must fail if the policy ceases to resolve to exact model `gpt-6-luna`, exact effort `low`, or if Astra is accepted as a real-test model.

## Verification and rollout

- Static/unit contracts prove Compose mount/host-gateway, wrapper parsing/delegation, no configured secret leakage, and exact LLM-test policy.
- Disposable image/runtime verification proves a Paseo daemon started with the wrapper can enumerate the dynamic Pi catalog through `paseo provider models pi` without manually sourcing the secret.
- Production cutover uses a newly built immutable candidate, preserves the current image as rollback anchor, recreates only the Paseo service, and verifies health/runtime identity plus provider catalog after cutover.
- A real model-call acceptance, if performed, MUST go through the canonical LLM-test launcher using `gpt-6-luna` with `low`; no Astra call is permitted.
- Failure after cutover restores the previous accepted image/config without restoring or destructively rewriting persistent HOME.
