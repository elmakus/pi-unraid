# M07-T04 — production recovery/update acceptance

Date: 2026-09-27  
Card: `M07-T04`  
Execution subject: `elmakus/pi-unraid@5646131327c45e4caff28a5206c01394e4a4ec0f`

## Launch and exact dependency refresh

M07-T04 launched only after exact M07-T03 terminal production-confirmation GREEN. Every dependency locator in the Card was reread at its exact immutable commit/blob and matched:

- M07-T03: `3116a20ca46dd56ecdbca187810652dfceb72a42:6fddfd94a8debec5b458f8cc6ddbd1f78005b602`
- M07-T02: `7e2be5ecc2996d62bc22124ddff321f9afbe48de:bf2010c429e7b90a9cb9d47c24e4472dbaf31dcd`
- M07-T01: `bd3f0715993e7f4fff2d0d9c6bfab1f8bcb21f17:5c12fc5fd75b13dc37915c061953c08ecba79a57`
- M05-T02B: `b7aa565649d14168e0d4b2d2d06044c08aac46a0:7bdb9fffcbada5f0dc6475f3bb2b7be92d8e1d20`
- M05-T03-R02: `550c5f76cca783e43eb44b0bdbf82c7fe889bff6:b526cf4717ea6d353fc6d23f082b1c726e7f55ed`
- M06-T01: `0f8538f7d226c6c022b5070aeca42375ba2d751a:e01bd1dd4d84c94ec9b29f7bd1914e7160162d82`
- M06-T02: `724d24e6d25d9a405998d8c6f48bbe65318ba4b4:13a49bd857c50b79213561ece74e06a585069d73`
- M06-T03: `d93bc18a20358ed6cd9cccf9c2c7031094f23410:a140f95fef4cd99a433d3b7b08f3e482e4c4dbc2`
- M06-T04: `9ba5ea11a2510f265a962b7870c8a3a09cb1cf4c:fc2bb31f794480e3fc954d28a47ac09086f2734e`

Current requirements R2, ADR-PGR-001..004 and P4 were also reread before launch.

## P4 section 7.1 reuse ledger

### M05-T02B cold/warm build evidence — reused

No affected build leg is invalidated:

- frozen candidate remains `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`;
- current production image is `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30` and carries that exact candidate label;
- current `Dockerfile` blob `870a20bdb2d9be6a06a8a258494ed3dab26a0b64`, `compose.yaml` blob `87f57b46f485918b50f560581ea86d580abcff6e`, `scripts/paseo_tower_build.py` blob `c90dedb0ec5ac2ca2d17fd7d8af2ab4d613a18fb` and `scripts/paseo_buildx.py` blob `e2568b2c956409de5661b3a8ecd5d79aafa3b172` are identical to M05-T02B implementation `4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8`;
- dedicated builder `pi-unraid-paseo` is still `docker-container`, running on BuildKit `v0.32.2`;
- portable cache remains `933087833` bytes; policy maximum remains `8589934592` bytes / `8GB`;
- retention remains schema 1 with maximum 3 and the exact current protected candidate/image;
- no Tower storage/permission drift affecting the build behavior was observed.

Therefore the accepted M05-T02B cold/warm proof remains applicable and was not replayed.

### M06 / HA / transaction-design reuse

The exact production candidate/image, production compose/runtime shape, HOME/secret strategy, approved capability set and Unraid/API line remain the accepted ones. M07-T03 already covered the expected staged-to-production alias/HOME divergence and actual phone-to-production proof. No auth revocation/permission rotation was observed. M05-T03 transaction semantics are reused as design only; the production-specific failure/rollback delta is proven below.

## Failed-candidate / pre-deploy protection — GREEN

Before the probe, production was container `7ab2afa43b3e4403b603875ac4cc9ce1d1ea31fd3bf6176e3115c9678b6afe18`, exact image `sha256:4bf8...`, running and healthy.

A temporary copy of the frozen candidate was altered only by replacing its `candidate_id` with an invalid self-hash, then passed to the current `scripts/paseo_buildx.py build` path. The command returned validation code 2 with `candidate_id mismatch`.

Recorded phases:
- `resolution_readback=failed`;
- `builder_ensure=skipped`;
- `build=skipped`;
- `test=skipped`;
- `prune=skipped`.

After the failed candidate probe, production container ID, immutable image and health were unchanged, and the SHA-256 of `retention.json` was identical before/after. The temporary corrupt candidate was deleted.

## Production post-deploy failure and rollback — GREEN

The production HOME identity fingerprint was computed only from SHA-256 fingerprints of the persisted server-id/keypair/config files; no secret bytes were placed in evidence. Baseline fingerprint:
`7acd0f57fdfbe8233abc14eb589301382681651f27150b23f8ed582428b9bbd9`.

A first bounded healthcheck-only injection remained in `starting` within its acceptance window. It was not counted as acceptance. Its fail-safe trap immediately recreated the original production compose and returned the exact image to healthy state.

The accepted second probe used a temporary Compose override with:
- the same immutable production image and the same persistent HOME/mounts;
- `restart: "no"`;
- a bounded test entrypoint that exits exactly 42.

The test production runtime was observed as:
- image `sha256:4bf8bb0...`;
- state `exited`;
- exit code `42`;
- restart policy `no`.

The rollback then reapplied only the exact M07-T03 production base+override with `--no-build --force-recreate`. Final restored state:
- exact image `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`;
- running / healthy;
- restart `unless-stopped`;
- shm `1073741824`;
- no host binding for port 6767;
- HOME identity fingerprint after rollback exactly `7acd0f57fdfbe8233abc14eb589301382681651f27150b23f8ed582428b9bbd9`.

After rollback, server identity remained `srv_jmdR4FLNIxrE`, Relay was enabled/reachable, Codex-LB auth reported `ready`, the durable `PHONE-PROD-GREEN` agent remained inspectable on `pi/codex-lb/gpt-6-sol`, and legacy Pi was healthy. No HOME restore occurred. The injected override was deleted after acceptance.

## Ordinary production restart recovery — GREEN

An ordinary `docker restart pi-unraid-paseo-1` was performed after rollback. The same production container ID and exact immutable image returned to running/healthy state with restart policy `unless-stopped`.

Post-restart readback:
- server ID preserved as `srv_jmdR4FLNIxrE`;
- Relay enabled and connected daemon reachable;
- `pi auth check --provider codex-lb --model gpt-6-sol --no-refresh` => `ready`;
- authenticated `gh workflow list -R elmakus/pi-unraid` returned 7 workflow rows;
- `PHONE-PROD-GREEN` persisted as an inspectable Pi/Codex-LB agent (provider/model/session identity preserved; its runtime status is now `closed`, which is convenience state, not workflow authority);
- legacy `pi-unraid-pi-1` remained running/healthy.

## Loss-of-session convenience-state recovery — GREEN

A separate disposable empty HOME owned by UID:GID 99:100 was mounted into the exact accepted production image, while the exact M07-T04 worktree at commit `5646131327c45e4caff28a5206c01394e4a4ec0f` was mounted read-only.

The probe confirmed:
- no Paseo agent/session state existed in the empty HOME;
- canonical repo recovered `project_workflow = "v2"`, `project_id = "pi-unraid"`, repository `elmakus/pi-unraid`;
- selected workstream recovered as `feature-paseo-gui-runtime`, branch `feat/paseo-gui-runtime`;
- Task Board recovered exactly `M07-T04 status = "in_progress"`;
- the exact M07-T04 Card contract was present;
- no M07-T04 result existed at the execution subject, so the correct continuation was the active Card rather than replay of an earlier side effect;
- `side_effect_replay=none`.

The disposable empty HOME was deleted after the probe. Production remained healthy and unchanged.

## Final doctors and anchors

Fresh post-recovery full environment capability doctor:
- **GREEN — 12 GREEN / 0 WARN / 0 RED / 0 unexpected**;
- exact candidate `sha256:b4e0c1e7...`;
- SpecPi remains the accepted core capability; this Card did not activate the later optional wishlist scope.

Fresh full Unraid host-control doctor from production:
- **GREEN: GraphQL=GREEN, SSH=GREEN, policy=GREEN**;
- GraphQL primary readback reached `http://192.168.2.104/graphql`;
- credential mode 0600 and only a bounded fingerprint were emitted;
- strict SSH fallback readback/reachability was GREEN;
- safety policy remained GraphQL-primary, with 5 ordinary GraphQL operations, 8 gated SSH operations, unknown-operation policy deny.

Final live state:
- production `pi-unraid-paseo-1`: running/healthy, exact image `sha256:4bf8...`, user 99:100, `unless-stopped`, 1 GiB shm, no host port binding;
- Relay enabled/reachable; Codex-LB ready;
- production HOME mode 0700 owner 99:100;
- legacy `pi-unraid-pi-1`: running/healthy;
- staged HA Paseo: exited on the accepted image;
- pre-production HOME backup remains present with recomputed SHA-256 `e4f8d86fec6254c53e3c89022d3c2c10cf907dd48ab734fa2ea40f3c4e104e7d`.

No whole-host reboot, Docker-engine restart, destructive HOME restore, broad delete/network mutation, new capability approval, wishlist activation or legacy retirement occurred.

## Verdict

M07-T04 implementation acceptance is **GREEN pending required independent implementation review**. The production-specific recovery/update deltas are proven while the reuse ledger preserves exact prior cold/warm, M06 and HA evidence without ceremonial replay. M07-T05, M07-T06 and M08 remain outstanding.
