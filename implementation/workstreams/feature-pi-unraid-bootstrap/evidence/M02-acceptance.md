# M02 integrated acceptance evidence

- Milestone: `M02 — Recoverable runtime and deployment lifecycle`
- Workstream: `feature-pi-unraid-bootstrap`
- Execution policy: `chatgpt_only`
- Final implementation head: `340121090f4b78ef3d2a3c1377d8bf5477026835`
- Date: 2026-09-23
- Verdict: **GREEN**

## Accepted Card results

- `M02-T01` — terminal GREEN review on `70d0ed0c74c965a1ba6cc0196f14e256faa1b7a1`; latest-stable selector, persistent LKG/seed fallback, exact version + RPC readiness and bounded failure state.
- `M02-T02` — terminal GREEN re-review on `7152b99f7e4844d3a2328aeffc0a0f4d099891c0`; managed native Pi registration, non-root supervisor, readiness and bounded planned shutdown/session-state preservation.
- `M02-T03` — terminal GREEN re-review on `340121090f4b78ef3d2a3c1377d8bf5477026835`; host update transaction, actual deployed-LKG snapshot, verified candidate cutover and retained-image/config rollback.

Historical RED evidence for M02-T02/T03 remains preserved; the terminal subjects above are the corrected independently reviewed subjects.

## Integrated checkpoint verification

Fresh close-time verification was completed on `Tower` from a detached checkout of exact final implementation head `340121090f4b78ef3d2a3c1377d8bf5477026835`, using only disposable Docker/Compose resources and temporary filesystem state.

- `git diff 7152b99f7e4844d3a2328aeffc0a0f4d099891c0 340121090f4b78ef3d2a3c1377d8bf5477026835 --check` — GREEN.
- `bash -n scripts/update.sh` — GREEN.
- `bash -n scripts/verify-update-rollback.sh` — GREEN.
- `bash scripts/verify-update-rollback.sh pi-unraid:m02-t02-r2` — GREEN, exit code 0.
- M01 base/Compose/Git-worktree regressions — GREEN.
- M02-T01 packaged Pi runtime selector — GREEN, stable Pi `0.87.1`.
- M02-T02 managed lifecycle — GREEN; observed escalation `3280 ms` with the explicit 3-second fixture grace.
- M02-T03 active-tag drift, successful update, explicit offline rollback, pre-cutover build failure, post-health runtime-readback failure and unhealthy post-cutover rollback scenarios — GREEN.
- Persistent home/projects/worktrees fixture hashes and ownership, failed-candidate marker, Docker log bounds and transaction retention remained valid.

Observed deployment identities:
- retained/running LKG image: `sha256:3ad9ef172eefd26be1a7a0ba139153478d943a129735d31bdf4a1df1750f696e`
- successful candidate image: `sha256:8cc449b04f4de729e394f20c98effe8e1931446103738ea760f58205221c531a`
- retained transaction count: `2`

## Milestone outcome readback

The approved M02 checkpoint is satisfied on the authorized disposable test surface:

- latest stable runtime admission is stable-only and a failed candidate cannot replace the working runtime;
- container recreation can recover through persistent compatible LKG or the immutable image seed;
- no stale success reports a missing compatible runtime as healthy;
- exec-launched managed Pi receives planned SIGTERM and bounded escalation exists for an uncooperative process;
- persisted native session state used by the lifecycle fixture remains intact across stop/recreation;
- host update uses a serialized fast-forward-only transaction, separately builds/verifies the candidate and retains the actual running healthy deployment image/config before cutover;
- failed post-cutover health or runtime readback restores the retained deployment and rechecks health;
- rollback uses retained local artifacts without restoring or rewriting persistent home/projects/worktrees;
- bounded Docker logging and deployment transaction retention remain effective;
- the single normal operator update/rollback path is documented.

The OpenSpec runtime-lifecycle contract remains consistent with the accepted implementation. Live OAuth, authenticated Git/GitHub acceptance, actual production Unraid cutover/rollback and host/Docker restart acceptance remain intentionally owned by M03.

## Safety / scope readback

No live `pi-unraid` production service, canonical persistent bind source, OAuth/provider credential or live GitHub credential was mutated or consumed by M02 close verification. M02 therefore does not overclaim M03 live acceptance.

## Verdict

**GREEN** — M02 satisfies its approved milestone checkpoint. The next deterministic route is JIT Execution Prep for approved milestone M03, beginning with read-only target readiness and preserving all explicit live-write/credential/restart authorization gates.
