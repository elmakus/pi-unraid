# M03-T04 independent review

- Card: `M03-T04 — Authorized production bootstrap and live functional acceptance`
- Review type: `RECOMMENDED`
- Reviewer: fresh normal ChatGPT independent from implementation of the reviewed subject
- Reviewed subject: `a78ea7a7e749bd64c1012b47847680712fb1e3ab`
- Date: 2026-09-23
- Verdict: **GREEN**

## Authority reviewed

The review used the exact M03-T04 Card authority slice:
- approved Master Plan R2, M03 / M03-W3;
- `PIB-REQ-001..013`, `PIB-REQ-016`, `PIB-REQ-018`, `PIB-REQ-019`, `PIB-REQ-022..024`;
- accepted `PIB-ADR-001`, `PIB-ADR-002`, `PIB-ADR-003`, `PIB-ADR-005`;
- accepted M03-T03 OpenSpec provider/secret contract;
- terminal M03-T02/M03-T03 dependency results, historical M03 readiness and the explicit M03-T04 production authorization.

No chat narrative was used as authority.

## Exact-subject inspection

The predecessor-to-subject delta was inspected from `906ba4020905981be75c1b44e23d7f0ef6589535` to the exact reviewed subject. The implementation-affecting change is the bounded target-GID correction in `scripts/container-entrypoint.sh` plus its regression coverage in `scripts/verify-compose-foundation.sh`.

The correction preserves the existing target group when the requested GID is already occupied and moves the `pi` user to that GID instead of trying to take over the group. This is consistent with the accepted configurable UID/GID requirement and does not add ownership traversal or broaden privileges.

An independent run of:

`bash scripts/verify-compose-foundation.sh`

completed GREEN at the exact production checkout subject, including the existing-GID regression.

## Independent live readback

Read-only production inspection on Tower confirmed:

- production checkout is clean at the exact reviewed subject;
- production image is `sha256:ddb23ca173e47cbd77739e6177a5860190221bc9556eeff561e8b2c9c888f005`;
- container health and separate `provider-health` are GREEN;
- PID 1 runs as UID/GID `99:100`; host process mapping is the expected `nobody:users`;
- restart policy is `unless-stopped`, timezone configuration is `Europe/Zurich`, the container is not privileged and publishes no service ports;
- mounts are limited to persistent Pi home, canonical projects, canonical worktrees and the dedicated read-only Pi Codex-LB secret; no Docker socket, host-root or Codex-LB appdata mount is present;
- Pi is `0.87.1`;
- provider configuration is persistent `codex-lb` using `api: openai-responses`, the accepted host-gateway `/v1` endpoint, model `gpt-6-sol`, and only the literal environment reference `${CODEX_LB_API_KEY}`;
- Pi `auth.json` contains no direct provider/OAuth entries;
- the recorded native session ID is still present in persistent Pi state after the final recreation;
- the dedicated host secret is owned `99:100` with mode `0600`;
- the resolved client key has zero matches in the reviewed Git subject, zero matches in current Pi container logs, and is not present in the container's configured environment;
- required development-tool inventory is present and the Pi service user has read/write/search access to `/home/pi`, `/projects` and `/worktrees`;
- persistent Git identity is present, GitHub SSH uses strict host-key checking with a persistent GitHub known-host entry, and `gh auth status` is GREEN.

Dependency/independence readback confirmed:

- `codex-lb-clean` runs `ghcr.io/soju06/codex-lb:1.25.0-beta.9` at image ID `sha256:867eeb726bf3d8141ed18ac35a827d3a3d0f49e6a6cca285567adf1f98102f0f`;
- Codex-LB `/health` returns HTTP 200 and unauthenticated `/v1/models` returns HTTP 401;
- `chatgpt-ce-workstation` remains healthy on the same baseline image ID `sha256:9ede8f1f522a710707acac32d01fd8c4d7671b91912791e299d1c635d964b893`;
- Appdata Backup still includes `/mnt/user/appdata`, defaults verification to enabled, and has no `pi-unraid` override marking it skipped.

## Evidence assessment

The implementation evidence for the authorized first real Codex-LB model call, native TUI/session create-exit-resume flow, bounded external Git SSH and `gh api` write/readback/delete checks, cleanup, and final recreation is coherent with the independently observed persistent/runtime state. No client key, OAuth token or private transcript content is present in the reviewed evidence.

## Verdict

**GREEN.**

M03-T04 satisfies its Card acceptance and applicable authority at the exact reviewed subject. No corrective implementation or additional Research obligation is required.
