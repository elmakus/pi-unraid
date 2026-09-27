# M07-T02 staged HA final acceptance — 2026-09-27

M07-T02 staged Human Acceptance is complete subject to its required independent review.

## Human UI/phone judgment

The user opened the already-paired staged Paseo from the phone after the staged runtime had been recreated and accepted the interface as generally good and suitable as the intended native Paseo UI. The first observation had no sessions, so session-label judgment was initially not applicable rather than failed.

A real staged session was then created through Paseo using the approved Pi provider path:

- session title: `HA session label check`
- provider/model: `pi/codex-lb/gpt-6-sol`
- prompt result: `HA session ready`
- final state: `idle`

The user then viewed that real session from the phone and explicitly accepted the session label and notification behavior as sensible. Because the session was created after the latest staged recreation and was visible from the already-paired phone without re-pairing, this also provides the final staged post-recreate real-phone reuse witness.

## Provider/auth completion

The staged Pi provider now reuses the previously approved Tower Codex-LB path without copying the secret into Git or plain HOME configuration:

- secret remains outside Git at `/mnt/user/appdata/pi-unraid/secrets/codex-lb.env`, mode `0600`, owner `99:100`;
- staged runtime mounts it read-only at `/run/secrets/pi-unraid-codex-lb`;
- staged `models.json` exposes only the approved `codex-lb/gpt-6-sol` endpoint/model contract;
- staged `auth.json` stores only a native Pi `!command` resolver for the mounted secret, not the credential value;
- `pi auth check --provider codex-lb --model gpt-6-sol --json --no-refresh` => ready;
- Paseo exposes the same model through the Pi provider.

## Final live state

- staged container: running, healthy, exact image `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`, runtime identity `99:100`;
- staged server ID remains `srv_jmdR4FLNIxrE`;
- Relay remains enabled and daemon reachable;
- GitHub CLI auth remains valid;
- Pi provider reports available and Codex-LB auth reports ready;
- production Paseo container remains absent;
- legacy `pi-unraid-pi-1` remains running and healthy.

## Prior acceptance evidence consumed

- `implementation/workstreams/feature-paseo-gui-runtime/evidence/M07-T02-ha-progress-2026-09-27.md`
- `implementation/workstreams/feature-paseo-gui-runtime/evidence/M07-T02-graphql-key-diagnosis-2026-09-27.md`
- `implementation/workstreams/feature-paseo-gui-runtime/evidence/M07-T02-graphql-permission-correction-check-2026-09-27.md`
- `implementation/workstreams/feature-paseo-gui-runtime/evidence/M07-T02-staged-ha-technical-2026-09-27.md`
- `implementation/workstreams/feature-paseo-gui-runtime/evidence/M07-T02-provider-session-ui-prep-2026-09-27.md`

Those evidence records prove the user-approved GitHub OAuth/workflow access, real phone Relay pairing and restart persistence, explicit upstream individual-revocation limitation, exact least-privilege Unraid GraphQL credential, authenticated readback, exactly one reversible staged container GraphQL mutation/restoration, bounded UID99/OpenSSH correction without rebuilding the candidate, credentialed strict SSH forced fallback with automatic smoke-marker cleanup and non-sticky return to GraphQL primary.

## Regression

The full repository contract suite was re-run after the final provider/session setup:

- **381 tests**
- verdict: **OK**
- exit code: 0

No raw credentials are recorded. No production Paseo cutover, production HOME/autostart mutation, high-impact host action, SpecPi wishlist activation or legacy Pi retirement occurred.
