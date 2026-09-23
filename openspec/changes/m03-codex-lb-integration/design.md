# M03 Pi → Codex-LB integration design

## Compose and network boundary

The Pi service keeps the accepted M01/M02 container layout. It gains:
- `host.docker.internal:host-gateway` as the deliberate default route to the host-published Codex-LB listener;
- non-secret endpoint/model settings;
- one Compose secret whose default host source is the dedicated Pi secret path `/mnt/user/appdata/pi-unraid/secrets/codex-lb.env`;
- the secret mounted read-only at `/run/secrets/pi-unraid-codex-lb`.

The secret host source path is configurable through `PI_CODEX_LB_SECRET_SOURCE` for disposable tests/recovery. Because local Docker Compose implements file-backed secrets as bind-backed files and does not apply Swarm-style uid/gid/mode controls, the host source itself must be owned/readable by the configured Pi service UID/GID and remain non-world-readable (production target: mode `0600`). The secret value is not placed in Compose environment, image layers, Git or rendered Compose snapshots.

The container does not join Codex-LB's Docker network and does not mount Codex-LB appdata.

## Persistent provider configuration

Repository-owned helper `pi-unraid-provider` reconciles `~/.pi/agent/models.json`.

For a fresh home it creates provider `codex-lb` with:
- `baseUrl` from `PI_CODEX_LB_BASE_URL` (default `http://host.docker.internal:2455/v1`);
- `api: openai-responses`;
- `apiKey: ${CODEX_LB_API_KEY}` as a reference, never the secret value;
- one bootstrap model from `PI_CODEX_LB_MODEL` (default `gpt-5.6-sol`).

The helper atomically writes mode-0600 JSON. Existing unrelated provider/model settings are preserved. If a `codex-lb` entry already exists and is structurally compatible, it is preserved rather than rewritten. A conflicting/invalid existing entry fails provider reconciliation without replacing the user's file.

## Secret loading

The runtime secret file may contain either one raw key or one `CODEX_LB_API_KEY=<value>` assignment. The provider helper validates it without logging its value.

The managed `pi` launcher executes the selected Pi runtime through the provider helper. The helper exports `CODEX_LB_API_KEY` only into that Pi process, then execs it. Pooled account OAuth/access/refresh tokens never enter Pi.

## Health and failure domains

`pi-unraid-service health` remains the M02 Pi runtime/service readiness contract and does not become unhealthy solely because Codex-LB is unavailable.

A separate `pi-unraid-service provider-health` check verifies:
1. compatible persistent provider configuration;
2. readable/valid dedicated client secret;
3. Codex-LB health endpoint reachability;
4. authenticated `/v1/models` access.

Its failures are classified as configuration, credential missing/invalid, authentication rejected, or endpoint unreachable, without printing the key or response body.

## Disposable verification

A uniquely named fixture uses temporary home/projects/worktrees, a temporary fake client secret and a local fake OpenAI-compatible HTTP endpoint reachable through host-gateway. It verifies fresh-home initialization, preservation of populated config, repeated initialization, force recreation, redacted Compose output, authenticated provider health, missing/invalid key, endpoint loss, runtime-health independence, secret-log/source scans and inherited affected M01/M02 regressions.

No production Pi path/service or real Pi client key is used by M03-T03.
