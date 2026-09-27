# M07-T04 R01 independent review — GREEN

- Task ID: PASEO-P4-M07-T04-R01
- Exact subject: `elmakus/pi-unraid@1cf7cf3277edda7d9f5a82615f3e27d5f8d6a3c9:implementation/workstreams/feature-paseo-gui-runtime/results/M07-T04.md`, blob `3fca9476ac6fd96d7b039571952c0be43c18192f`.
- Implementation subject recorded by the result: `5646131327c45e4caff28a5206c01394e4a4ec0f`.
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M07-T04.md` (review required).
- Independence: this review context did not author or repair the M07-T04 evidence, result or exact reviewed subject. The pending attempt was reserved by the execution context for a fresh independent reviewer.
- Verdict: **GREEN**. No blocking acceptance gap was found. This permits deterministic M07-T04 finalization only; M07-T05/M07-T06/M08 remain outstanding.

## Exact identity and authority reconciliation

- Remote branch HEAD was revalidated at `c8db4505b542fa843d4f127d3b3b3229f1ba9c8b` immediately before the review write.
- Pending R01 still bound exact result commit/blob `1cf7cf3277edda7d9f5a82615f3e27d5f8d6a3c9:3fca9476ac6fd96d7b039571952c0be43c18192f`.
- All nine Card dependency result blobs were independently re-read at their immutable commit locators and matched the Card.
- Requirements R2, ADR-PGR-001..004 and P4 section 7.1 were reconciled against the Card.

## Reuse/invalidation review

The M05-T02B reuse claim is supported. Independent blob comparison between M05-T02B implementation `4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8` and M07-T04 implementation subject `5646131327c45e4caff28a5206c01394e4a4ec0f` is identical for:
- `Dockerfile` `870a20bdb2d9be6a06a8a258494ed3dab26a0b64`;
- `compose.yaml` `87f57b46f485918b50f560581ea86d580abcff6e`;
- `scripts/paseo_tower_build.py` `c90dedb0ec5ac2ca2d17fd7d8af2ab4d613a18fb`;
- `scripts/paseo_buildx.py` `e2568b2c956409de5661b3a8ecd5d79aafa3b172`;
- environment capability inventory/control and host-control doctor contracts are likewise unchanged.

Fresh Tower readback through the accepted persistent Docker config shows builder `pi-unraid-paseo`, driver `docker-container`, BuildKit `v0.32.2`, portable cache `933087833` bytes, the accepted 8 GiB cache bound and retention maximum 3 protecting the exact candidate/image. No cold/warm leg invalidation was found.

## Acceptance evidence review

- Failed-candidate protection records candidate-id mismatch at resolution readback with builder/build/test/prune skipped and production/retention unchanged.
- Production post-deploy failure uses the exact production image and persistent HOME, reaches deterministic exit code 42, and rolls back with the exact accepted M07-T03 compose. Final image, restart policy, shm and HOME identity fingerprint are restored; no destructive HOME restore occurs.
- Ordinary `docker restart` returns production to healthy on the exact image with preserved Relay/server identity, Pi/Codex-LB auth, GitHub workflow access and the durable phone session.
- Separate empty-HOME exact-image recovery reads canonical Git/PW state, recovers M07-T04 as `in_progress`, and records `side_effect_replay=none`.
- Final environment capability doctor is 12 GREEN / 0 WARN / 0 RED / 0 unexpected; host-control doctor is GREEN for GraphQL/SSH/safety policy.
- No high-impact user-gated host operation, new capability approval, wishlist activation, destructive HOME restore or legacy retirement is claimed.

## Independent fresh Tower corroboration

After the exact subject was frozen, fresh read-only checks showed:
- production `pi-unraid-paseo-1` healthy on image `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`;
- `pi auth check --provider codex-lb --model gpt-6-sol --no-refresh` => `ready`;
- authenticated `gh workflow list -R elmakus/pi-unraid` returned seven workflows;
- `PHONE-PROD-GREEN` remains inspectable on `pi/codex-lb/gpt-6-sol`;
- Paseo daemon 0.9.2 is running, Relay enabled/reachable, server ID `srv_jmdR4FLNIxrE`;
- legacy `pi-unraid-pi-1` remains running/healthy.

A later independent bounded recovery corroboration also exercised a healthcheck-only post-deploy failure, exact compose rollback, ordinary restart and disposable session deletion/Git-PW recovery; the production runtime returned healthy with unchanged hash-only HOME/auth identity. This corroboration did not modify the frozen reviewed result subject and is not required to establish its acceptance.

## Boundary assessment

The reviewed result satisfies the exact M07-T04 Card acceptance. Reuse remains identity-gated rather than ceremonial, production failure/rollback and routine restart are directly proven, non-authoritative session-state loss recovers from Git/PW without replay, HOME/auth state is preserved, and the legacy rollback anchor remains healthy. No blocking defect was found.