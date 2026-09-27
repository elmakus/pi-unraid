# M08-T01-R01 — independent final production evidence review

Date: 2026-09-27  
Card: `M08-T01`  
Attempt: `R01`

## Exact subject

- Result commit: `1b25ec8fd1c82c3c317dcf3fbb63193873042768`
- Result blob: `605e11fc08f563354a61a258ea8120dade11986d`
- Result path: `implementation/workstreams/feature-paseo-gui-runtime/results/M08-T01.md`
- Acceptance Card blob reviewed: `14df9fcd3d204d64d434c42618c0f8044a89064b`
- Final ledger blob at the result subject: `6a11563d69e7fb7a4c7a49d57f3bc2558b442475`

## Independence

This review context did not materially produce or repair the M08-T01 final ledger, its execution evidence, or the exact frozen result subject. It independently inspected the frozen subject, acceptance Card, approved P4 authority, durable Task Board bindings and fresh read-only Tower state.

## Durable subject review

- All 26 dependency locators in the M08-T01 Card exactly match DONE predecessor result path/commit/blob bindings in the current Task Board.
- The ledger preserves exact accepted M01-M07 result/evidence identities and separates the M01-M05 foundations, M06 technical proof, M07 staged HA, production confirmation/recovery, wishlist disposition and legacy retirement.
- Requirement coverage is continuous across PGR-REQ-001..087 with no uncovered numeric range: 001-010, 011-020, 021-026, 027-035, 036-044, 045-054, 055-070, 071-080, 081-082, 083-084, 085 and 086-087. Explicit deferred boundaries remain deferred rather than being falsely claimed implemented.
- The final ledger records the scheduled Appdata Backup condition as degraded rather than GREEN and preserves the bounded M07 backup anchors.
- OR live integration and future PWv2.1 Pi-extension packaging/bootstrap remain outside this workstream.

## Fresh independent Tower readback

Read-only checks performed during R01 independently confirmed:

- production `pi-unraid-paseo-1` is running/healthy on exact image `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`;
- restart policy is `unless-stopped`, runtime user is `99:100`, shm is 1 GiB and there are no host port bindings;
- `pi auth check --provider codex-lb --model gpt-6-sol --no-refresh` returns `ready`;
- Paseo `/api/health` returns `status=ok` and `/api/status` reports server ID `srv_jmdR4FLNIxrE`, version `0.9.2`;
- the full environment capability doctor returns `GREEN` with 12 GREEN / 0 WARN / 0 RED / 0 unexpected;
- Pi instruction-plane status is in sync; managed global capability state is GREEN/in-sync; SpecPi wishlist is `on`; SpecPi project-scope policy remains `inactive_in_fresh_session`;
- full Unraid host-control doctor returns GraphQL=GREEN, SSH=GREEN and safety-policy=GREEN;
- the standalone `pi-unraid-pi-1` container is absent;
- retained legacy image remains exactly `sha256:293f88a02ee015b4b3be05f071534b5405cdca8cb4948e3b0ee4321c0deea72c`;
- legacy HOME remains present at `/mnt/user/appdata/pi-unraid/home`, UID:GID 99:100, logical bytes `548285730`;
- legacy retirement archive remains mode 0600, size 576768000, SHA-256 `4a21b1ce87bcf01219095b04d2267fb4c315fb6ceaa30c3d62c701fcf056a61b`;
- production pre-cutover HOME archive remains mode 0600 with SHA-256 `e4f8d86fec6254c53e3c89022d3c2c10cf907dd48ab734fa2ea40f3c4e104e7d`;
- recent scheduled Appdata Backup directories for 2026-09-24 through 2026-09-27 are marked `-failed`, matching the ledger's explicit degraded residual-risk statement.

No interactive HA, cold/warm build, rollback injection, production mutation, destructive HOME action or other acceptance ceremony was replayed.

## Verdict

**GREEN.**

The exact M08-T01 subject satisfies the frozen Card acceptance. Its final ledger is consistent with durable predecessor state and fresh production readback, preserves explicit residual risks without false GREEN claims, and keeps downstream OR/PW-extension work outside the closed Paseo/Pi base scope.
