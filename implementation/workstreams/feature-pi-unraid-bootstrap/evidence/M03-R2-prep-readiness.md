# M03 R2 JIT preparation readiness — refreshed baseline

- Workstream: `feature-pi-unraid-bootstrap`
- Milestone: `M03 — Codex-LB-integrated on-Unraid acceptance and recoverable handoff`
- Date: 2026-09-23
- Mode: read-only target/dependency refresh plus repository planning-state reconciliation only
- Result: **READY FOR CONTRACTING; EXECUTION BLOCKED AT DEPENDENCY LIVE-WRITE GATE**

## Exact project/source state

- Approved plan: `planning/MASTER_PLAN.md` R2, independently reviewed GREEN.
- Durable project branch head observed after plan-review consumption: `b9484ba734ba668a56a320da7f2120ce69627c87`.
- Tower checkout: `/mnt/cachedl/projects/pi-unraid`.
- Tower checkout branch: `feat/pi-unraid-bootstrap`.
- Tower checkout HEAD: `21cee93349dc1b0e432d0ca844234a36494a76ba`.
- Tower checkout worktree: clean.
- Tower local upstream ref observed at the same stale HEAD.
- Therefore eventual production bootstrap still requires an explicit clean fast-forward to the exact then-approved workstream source.

No checkout mutation was performed.

## Tower Pi target state

- No production `pi-unraid` container exists.
- `/mnt/user/appdata/pi-unraid`: missing.
- `/mnt/user/appdata/pi-unraid/home`: missing.
- `/mnt/user/pi-worktrees`: missing.
- `/mnt/user/projects`: present, ownership/mode `99:100 2777`.
- Existing R1 readiness derivation of production Pi UID/GID `99:100` remains consistent with the refreshed projects-root ownership, but must be re-read immediately before production mutation.

No canonical Pi path was created and no Docker Pi deployment was started.

## Codex-LB dependency state

Current Tower deployment:
- container: `codex-lb-clean`;
- state: running;
- restart policy: `unless-stopped`;
- image: `ghcr.io/elmakus/codex-lb:main`;
- image ID: `sha256:914ba5dae9307da43dfb2eaf66566115d865ca027156af599b7433b4eebb166c`;
- image revision label: `0b673d84316c33dd166e6bffbe6b66444379a895`;
- persistent bind: `/mnt/user/appdata/codex-lb-clean -> /var/lib/codex-lb`;
- network: `ibraproxy`;
- `GET /health`: HTTP 200 with `{"status":"ok"}`;
- unauthenticated `GET /v1/models`: HTTP 401, consistent with proxy-key enforcement.

Current source baseline:
- `elmakus/codex-lb@main`: `0b673d84316c33dd166e6bffbe6b66444379a895`;
- that fork commit is based on upstream `0f6a31c56ac30804ca1c0fac27ca02c6f59bf2b0` plus the fork-specific GHCR publishing delta;
- current `Soju06/codex-lb@main`: `3d23d53f89dbbaa2353040a30451cf90ca48ee92`;
- GitHub compare from `0f6a31c...` to `3d23d53...`: upstream ahead by **92 commits**.

The running dependency is healthy but still uses the same materially stale fork baseline identified by Definition research. It therefore does **not** yet satisfy the R2 requirement for a current-enough reviewed dependency baseline. Reconciliation/update/validation must occur under Codex-LB's own authority/workflow before Pi production model acceptance.

No Codex-LB source, image, configuration, network, account, API key or persistent data was mutated.

## Workstation independence baseline

`chatgpt-ce-workstation` remains:
- running and healthy;
- container ID `ba960b239bd29c1908e314ea64b9d44c8883f238feaa4367e6d889227713d5a7`;
- image ID `sha256:9ede8f1f522a710707acac32d01fd8c4d7671b91912791e299d1c635d964b893`;
- restart policy `unless-stopped`.

No workstation mutation was performed.

## Execution-prep conclusion

The approved M03 packages are sufficiently knowable to materialize as new Cards without reviving superseded R1 `M03-T01`.

The first executable obligation is the Codex-LB prerequisite/client boundary. It is blocked before external mutation because current evidence proves a dependency reconciliation is required and R2 explicitly places the following behind the dependency live-write gate:

1. any Codex-LB fork/image/config/network mutation;
2. creation/revocation of the dedicated Pi client credential.

After that prerequisite is accepted, Pi-side integration can proceed, followed by separately gated production bootstrap and disruptive restart/recovery acceptance.
