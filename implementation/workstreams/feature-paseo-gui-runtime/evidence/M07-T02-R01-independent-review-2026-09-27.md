# M07-T02 R01 independent review — GREEN

- Task ID: PASEO-P4-M07-T02-R01
- Exact subject: `elmakus/pi-unraid@7e2be5ecc2996d62bc22124ddff321f9afbe48de:implementation/workstreams/feature-paseo-gui-runtime/results/M07-T02.md`, blob `bf2010c429e7b90a9cb9d47c24e4472dbaf31dcd`.
- Implementation subject: `8f2d9f59bd054f46a5aa61e8491de0880332068b`.
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M07-T02.md` (review required).
- Independence: this review context did not author or repair the exact implementation, result, staged HA evidence, UID99/OpenSSH repair, or live acceptance state.
- Verdict: **GREEN**. No blocking acceptance gap was found. This permits staged HA GREEN only; M07-T03 production cutover and actual phone-to-production confirmation remain outstanding.

## Exact identity and authority reconciliation

- Remote branch HEAD was revalidated at `e2dd50c401c8b2415d4e3d57a6d4baf01277849b` before the review write.
- The pending R01 subject still resolves to result blob `bf2010c429e7b90a9cb9d47c24e4472dbaf31dcd`.
- The M07-T02 dependency remains exact M07-T01 result `implementation/workstreams/feature-paseo-gui-runtime/results/M07-T01.md@bd3f0715993e7f4fff2d0d9c6bfab1f8bcb21f17:5c12fc5fd75b13dc37915c061953c08ecba79a57`.
- Approved requirements R2, ADR-PGR-001..004 and frozen P4 were re-read. P4 assigns staged first-presence auth, real-phone pairing/reuse, least-privilege GraphQL proof, credentialed SSH fallback witness and manual native-UI judgment to M07-T02, while production cutover and actual phone-to-production proof remain M07-T03.

## Acceptance and evidence review

- GitHub OAuth/device approval and repository/workflow access are recorded without token disclosure; auth survived staged restart/recreation.
- Real-phone Relay pairing, persisted server/key identity and resumed/reused phone access are evidenced across staged restart/recreation. Individual revocation is not claimed; the current upstream CLI limitation is recorded explicitly as permitted by the Card.
- The GraphQL credential history correctly preserves failed/over-broad intermediate states. Final evidence records the exact accepted profile: no role, only `INFO:READ_ANY`, `DOCKER:READ_ANY`, `DOCKER:UPDATE_ANY`; authenticated readback succeeds.
- Exactly one reversible ordinary staged-container GraphQL action is evidenced: pause, bounded post-readback, unpause restoration, then health recovery. No production or legacy-Pi mutation is claimed.
- The forced credentialed SSH witness uses strict noninteractive settings, proves bounded marker create/remove cleanup, and demonstrates immediate non-sticky return to GraphQL-primary routing.
- Manual acceptance records native Paseo as the intended normal entrypoint, a real `HA session label check` session through `pi/codex-lb/gpt-6-sol`, sensible label/notification behavior, and already-paired phone visibility after the latest staged recreation.
- Final repository regression is recorded as **381/381 GREEN**.
- Evidence remains bounded and secret-safe; raw GitHub, GraphQL, Relay/session and SSH private credentials are absent.

## Bounded UID99/OpenSSH repair review

- The exact candidate image was not rebuilt; the repair adds a candidate-derived read-only `/etc/passwd` overlay while preserving runtime UID:GID `99:100`.
- `prepare_paseo_passwd_overlay.py` preserves image accounts, rejects UID collisions and writes the non-secret passwd overlay atomically as mode 0644.
- Unit tests cover account preservation/runtime identity insertion, UID-collision fail-closed behavior and file mode.
- Fresh live readback confirms `paseo-unraid:x:99:100:...:/home/paseo:/bin/false` is active in the staged runtime.

## Independent fresh read-only Tower readback

No host or GraphQL mutation was performed during review.

- `pi-unraid-staged-ha-paseo-1`: running, healthy, exact image ID `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`, runtime user `99:100`.
- `pi-unraid-pi-1`: running and healthy.
- Production `pi-unraid-paseo-1`: absent.
- `/mnt/user/appdata/pi-unraid/secrets/unraid-api.key` and `codex-lb.env`: mode 0600, owner `99:100`.
- Staged `gh auth status`: active account `elmakus`, HTTPS, workflow-capable scopes; token value redacted.
- Staged `pi auth check --provider codex-lb --model gpt-6-sol --json --no-refresh`: `status=ready`, `authType=api_key`.

## Boundary assessment

No defect found that invalidates staged HA acceptance. Production Paseo remains intentionally absent and legacy Pi remains healthy. The next legal scope is M07-T03: exact reviewed M07-T02 binding, automatic production cutover, then the required actual phone-to-production confirmation.
