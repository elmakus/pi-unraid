# Pi Codex-LB provider integration specification

## Compose secret and route

1. The repository-owned Compose definition MUST support a dedicated Pi Codex-LB client secret without embedding its value in Git, image layers, service environment declarations or rendered Compose output.
2. The default production secret source MUST be a Pi-owned host path under `/mnt/user/appdata/pi-unraid`; disposable verification MUST override it to a unique non-production path.
3. The secret MUST be mounted into the Pi container only as a dedicated read-only secret file; Pi MUST NOT mount Codex-LB's data directory.
4. The default container-to-host route MUST use `host.docker.internal:host-gateway` and the accepted host-published Codex-LB listener unless later target evidence requires an authorized change.
5. This integration MUST NOT add Docker socket, host-root, unrelated-appdata mounts, inbound SSH or a dependency on `chatgpt-ce-workstation`.

## Persistent models configuration

1. Provider initialization MUST target persistent `~/.pi/agent/models.json`.
2. A fresh compatible configuration MUST define a `codex-lb` provider using `api: openai-responses`, a Codex-LB `/v1` base URL, an environment reference for `CODEX_LB_API_KEY`, and at least one configured model.
3. The persisted JSON MUST NOT contain the resolved client-key value.
4. Initialization MUST be atomic and idempotent across repeated startup/recreation.
5. Existing unrelated valid provider/model configuration MUST be preserved.
6. An already-valid `codex-lb` provider MUST be preserved rather than destructively rewritten.
7. Conflicting or invalid existing provider configuration MUST fail the provider reconciliation clearly while preserving the original file.
8. Provider initialization failure MUST NOT be represented as loss of persistent home/session/Git/runtime state.

## Credential ownership and process exposure

1. The Pi client secret MUST be loaded only from the dedicated runtime secret file or an explicit disposable override.
2. The managed Pi process MAY receive the resolved client key through its process environment after secret-file validation.
3. Ordinary diagnostics, Compose rendering, service logs and committed evidence MUST NOT emit the resolved key.
4. ChatGPT/Codex pooled account OAuth/access/refresh tokens MUST NOT be copied, mounted or materialized into Pi.
5. Direct Pi built-in ChatGPT/Codex OAuth MUST NOT be introduced as a fallback.

## Provider diagnostics

1. Pi runtime/service readiness and Codex-LB provider readiness MUST be independently observable.
2. Runtime health MUST continue to represent M02 runtime readiness even when the provider secret is missing/invalid or Codex-LB is unreachable.
3. Provider health MUST validate persistent provider shape, secret availability, endpoint reachability and authenticated `/v1/models` access.
4. Missing/invalid credential, authentication rejection and endpoint unreachability MUST produce distinct actionable non-secret failures.
5. Provider diagnostics MUST NOT print response payloads or secret values on failure.

## Verification boundary

1. M03-T03 MUST verify provider behavior only with uniquely named disposable resources and non-production credentials/endpoints.
2. Verification MUST cover fresh and populated home, repeated initialization, recreation persistence, missing/invalid credential, unreachable endpoint, redaction and affected inherited M01/M02 behavior.
3. A disposable authenticated `/v1/models` success is sufficient for this Card; the first real production model interaction remains M03-T04.
