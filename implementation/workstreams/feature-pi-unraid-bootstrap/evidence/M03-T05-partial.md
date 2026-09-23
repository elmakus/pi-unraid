# M03-T05 partial production recovery evidence

- Card: `M03-T05 — Production recovery, restart and final technical handoff`
- Date: 2026-09-23
- Status: **AUTHORIZED NON-DISRUPTIVE SCOPE GREEN; blocked only on separate Docker-wide/host-restart authorization**
- Authorization: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T05-authorization.md`
- Current production source after update: `e5ca17b98f0f7177e7e616e19a29d613902bb460`
- Current production image: `sha256:293f88a02ee015b4b3be05f071534b5405cdca8cb4948e3b0ee4321c0deea72c`
- Previous retained production image: `sha256:ddb23ca173e47cbd77739e6177a5860190221bc9556eeff561e8b2c9c888f005`
- Secret handling: no client key, OAuth token, account identifier or private transcript content is recorded here.

## Refresh-gate correction before production update

Pre-write refresh found that the production checkout had no `.env`. A plain pre-existing `scripts/update.sh` invocation would therefore have rendered Compose defaults (`1000:1000` and the repository default model) instead of preserving the already accepted live production values (`99:100`, `gpt-6-sol`).

This was a bounded M03-T05 L1/L2 correction inside the existing update/reproducibility authority:
- `scripts/update.sh` now inherits `PI_UID`, `PI_GID`, `PI_CODEX_LB_BASE_URL`, `PI_CODEX_LB_MODEL` and the dedicated secret source from the currently running Compose service when the operator did not explicitly provide overrides;
- explicit operator values retain precedence;
- `scripts/verify-update-rollback.sh` proves the rendered pre-update snapshot inherits non-default live settings when operator variables are absent;
- `docs/OPERATOR.md` documents the behavior.

Before any production cutover, exact-subject syntax/diff checks and full disposable `verify-update-rollback.sh pi-unraid:local` completed GREEN, including successful update, explicit rollback, build failure, runtime-readback failure rollback, unhealthy cutover rollback, persistent-bind preservation and the new inherited-settings regression.

The first live update attempt stopped before repository/deployment mutation because host Git rejected the root-side checkout as dubious ownership. The retry used a process-scoped Git `safe.directory` setting only; no global Git configuration was changed.

## Normal production update

The normal update operation then:
- fast-forwarded the clean production checkout from `a78ea7a7e749bd64c1012b47847680712fb1e3ab` to `e5ca17b98f0f7177e7e616e19a29d613902bb460`;
- snapshotted the actual running previous image and rendered deployment config;
- built and ran the full candidate verification gate;
- retained the previous image;
- recreated production and reached GREEN runtime readback.

Transaction readback:
- pre-source: `a78ea7a7e749bd64c1012b47847680712fb1e3ab`;
- post-source: `e5ca17b98f0f7177e7e616e19a29d613902bb460`;
- pre-image: `sha256:ddb23ca173e47cbd77739e6177a5860190221bc9556eeff561e8b2c9c888f005`;
- post-image: `sha256:293f88a02ee015b4b3be05f071534b5405cdca8cb4948e3b0ee4321c0deea72c`;
- transaction status: `healthy`.

Post-update production readback was GREEN:
- PID1 UID/GID `99:100`;
- `PI_CODEX_LB_MODEL=gpt-6-sol`;
- accepted host-gateway Codex-LB base URL retained;
- runtime `0.87.1`;
- Pi service health and separate provider health GREEN;
- native session `01a0cede-b93e-75fe-9f70-1268afcf3bca` preserved.

## Controlled runtime failure / LKG recovery

A synthetic stable candidate `9.9.99` with a deliberately missing install source was reconciled against the real persistent production home.

Result:
- outcome: `candidate_install_failed`;
- selected runtime remained `0.87.1`;
- runtime health remained GREEN;
- Codex-LB provider health remained GREEN;
- the native session remained present;
- preservation markers in home/projects/worktrees retained exact content hashes and `99:100` ownership.

A subsequent ordinary reconcile returned to the real current stable path.

## Planned stop and native-session resume

A real managed Pi RPC process was opened against the persisted M03 native session before a planned Compose stop.

Readback:
- managed Pi registrations were present before stop;
- PID1 logged SIGTERM delivery to managed Pi;
- no managed Pi SIGKILL was required;
- service restarted healthy with the accepted production values;
- provider health returned GREEN;
- packaged Pi reopened the same native session ID `01a0cede-b93e-75fe-9f70-1268afcf3bca`;
- preservation markers remained unchanged.

## Actual retained-image rollback and return to current deployment

The production update transaction was rolled back using only its retained local image/config artifacts.

Rollback readback:
- running production image returned to `sha256:ddb23ca173e47cbd77739e6177a5860190221bc9556eeff561e8b2c9c888f005`;
- Git source deliberately remained at `e5ca17b98f0f7177e7e616e19a29d613902bb460`;
- provider health was GREEN;
- the native session remained resumable;
- marker content and `99:100` ownership were unchanged across all three durable mounts.

Production was then advanced again using a **plain** update invocation with `PI_UID`, `PI_GID`, provider model/base URL and secret-source variables intentionally absent from the caller environment. The corrected update path inherited them from the running deployment and returned production to image `sha256:293f88a02ee015b4b3be05f071534b5405cdca8cb4948e3b0ee4321c0deea72c`.

Readback proved:
- `PI_UID=99`;
- `PI_GID=100`;
- `PI_CODEX_LB_MODEL=gpt-6-sol`;
- accepted Codex-LB base URL retained;
- runtime/provider health GREEN;
- native session unchanged;
- update transaction GREEN.

## Codex-LB dependency outage and restart

The independent `codex-lb-clean` service was deliberately stopped.

During the outage:
- Pi runtime/service health remained GREEN;
- Pi provider-health failed as expected;
- Pi native session remained present;
- Pi `auth.json` remained empty, so no direct-Pi OAuth fallback appeared.

Codex-LB was started and then independently restarted. After each operation its health returned and Pi provider-health returned GREEN. The Codex-LB image identity remained `sha256:867eeb726bf3d8141ed18ac35a827d3a3d0f49e6a6cca285567adf1f98102f0f`.

The accepted M03-T02 dependency evidence remains the authoritative sanitized routing/account-pool evidence: three active ChatGPT/Codex accounts, `capacity_weighted` routing, sticky threads and proxy-key authentication, with the explicit limitation that account-owned continuation state is not guaranteed to migrate transparently across accounts. M03-T05 did not expose account identifiers or token material while exercising dependency recovery.

## Diagnostics, security and independence

Final non-disruptive readback:
- production container healthy;
- provider health GREEN;
- runtime `0.87.1`;
- log rotation remains `10m × 3`;
- current json-file log size was bounded and small at readback;
- container remains non-privileged with no published service ports and no inbound `sshd`;
- current container logs contained zero matches for the resolved dedicated Pi client key;
- `chatgpt-ce-workstation` remained exactly on baseline container/image identity and healthy;
- Codex-LB remained running on its accepted image;
- temporary preservation markers were removed after successful readback.

## Remaining required gate

No Docker-wide restart, Unraid host restart or similarly broad interruption was performed.

M03-T05 acceptance item 8 and therefore final all-21-outcome/M03 technical completion remain intentionally incomplete until the user separately authorizes the disruptive restart window. The Card must not enter REQUIRED independent review or terminal completion before that remaining acceptance is executed and consolidated.
