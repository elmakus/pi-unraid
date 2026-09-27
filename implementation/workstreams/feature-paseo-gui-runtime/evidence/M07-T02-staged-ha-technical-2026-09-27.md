# M07-T02 staged HA technical evidence — 2026-09-27

Implementation subject for the bounded HA repair: `elmakus/pi-unraid@8f2d9f59bd054f46a5aa61e8491de0880332068b`.

This is staged-only Human Acceptance evidence. It does not claim M07-T02 terminal GREEN until the remaining manual UI/UX judgment and post-recreate phone reconnect are supplied.

## GitHub OAuth / workflow access

- User-approved native GitHub device/OAuth flow completed successfully.
- Account readback: `elmakus`.
- Repository and workflow listing for `elmakus/pi-unraid` succeeded.
- `HOME/.config/gh/hosts.yml` mode `0600`; bounded fingerprint `sha256:0521e7d95071e6e002c07520043311132efa51fc3a7ec8c16e3d6c9e611a15fa`.
- GitHub auth survived routine staged restart/replacement.
- No raw GitHub token is recorded.

## Relay / phone / persistence

- Real phone Relay pairing completed against staged Paseo 0.9.2.
- Staged server ID: `srv_jmdR4FLNIxrE`.
- Relay enabled at `relay.paseo.sh:443`.
- Earlier live logs recorded external phone sessions and `resumed=true` reconnects across the required routine staged restart.
- Server ID and daemon keypair survived subsequent staged recreations; daemon-keypair SHA-256 remains `b3669df8389566032adcb6c21c1f4cfd0b2f0c5988b8db2805534015f063a3f4`.
- Current Paseo 0.9.2 CLI exposes no individual device/session revoke or unpair command; individual revocation is therefore recorded as an upstream CLI limitation, not claimed.
- After the final staged recreation used for the SSH repair, no phone client was open long enough to emit a new `resumed=true` log line. The remaining manual UI step will also provide that final post-recreate phone reconnect confirmation.
- Pairing offers/push tokens/raw session material are omitted.

## GraphQL least-privilege host control

Persistent Unraid API-key metadata was read back and now matches the exact accepted profile:

- roles: none;
- `INFO:READ_ANY`;
- `DOCKER:READ_ANY`;
- `DOCKER:UPDATE_ANY`;
- no additional permissions.

The client secret is outside Git at `/mnt/user/appdata/pi-unraid/secrets/unraid-api.key`, mode `0600`, owner `99:100`, bounded fingerprint `sha256:9514c3c99c4a70e5`.

Authenticated INFO/DOCKER GraphQL readback succeeded.

Exactly one reversible ordinary single-container mutation witness was performed against non-production `pi-unraid-staged-ha-paseo-1`:

- pre-state: `RUNNING`, healthy;
- forward mutation: GraphQL `pause` -> `PAUSED`;
- bounded post-readback confirmed `PAUSED`;
- restoration: GraphQL `unpause` -> `RUNNING`;
- health briefly reported unhealthy immediately after unpause, then recovered to `healthy` without further mutation;
- final daemon readback remained reachable and GitHub auth remained valid.

No production or legacy Pi mutation occurred.

## Credentialed SSH fallback and bounded HA repair

Live staged acceptance exposed a candidate/runtime integration defect: Compose runs the exact candidate as numeric `99:100`, while the image's `/etc/passwd` originally had no UID 99 entry, causing OpenSSH to fail with `No user exists for uid 99`.

Bounded correction under the active Card:

- added `scripts/prepare_paseo_passwd_overlay.py` plus unit tests;
- helper derives a passwd overlay from the exact image passwd, preserves all image accounts, refuses UID collisions, and adds only `paseo-unraid:x:99:100:...:/home/paseo:/bin/false`;
- staged runtime mounts the generated passwd overlay read-only at `/etc/passwd`;
- exact image identity remained `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`; no candidate rebuild occurred;
- staged runtime remained `user=99:100`, healthy, Relay-enabled, with the same server ID, daemon keypair and GitHub auth fingerprint;
- OpenSSH 9.2p1 now executes successfully as `uid=99(paseo-unraid) gid=100(users)`.

A dedicated staged SSH identity was created at `HOME/.ssh/tower_host_control_ed25519`, mode `0600`, bounded public fingerprint `SHA256:xg4287wuiRxBW03vSti4GQ+bNLuuLBQbsbpfyIPeat8`. Tower known_hosts is strict and mode `0600`. The public identity is authorized in persistent Unraid `/boot/config/ssh/root/authorized_keys`; a pre-change rollback anchor is stored under M07-T02 appdata.

Credentialed strict noninteractive witness from inside staged runtime:

- BatchMode/no-password/no-keyboard-interactive/IdentitiesOnly/StrictHostKeyChecking path: GREEN;
- forced-test SSH probe: GREEN;
- forced readback: hostname `Tower`, kernel `Linux 6.12.54-Unraid x86_64`, uid `0`;
- forced bounded smoke marker: pre `absent` -> post `present` -> restored `absent`, automatic cleanup GREEN;
- explicit host-control router invocation with `forced_test`: `transport=ssh`, `primary_transport=graphql`, `primary_attempted=false`;
- next normal router invocation: `transport=graphql`, `primary_attempted=true`, proving non-sticky fallback and return to GraphQL primary.

Raw private key material is not recorded.

## Regression

Full repository contract discovery after the HA repair:

- **381 tests**
- verdict: **OK**
- runtime: about 4.2 s

## Remaining manual acceptance

One user action remains before M07-T02 can produce its semantic result:

1. open the already-paired staged Paseo from the phone after the latest recreation without re-pairing;
2. confirm Paseo is acceptable as the normal entrypoint;
3. confirm it is the native Paseo UI rather than a second dashboard;
4. confirm session labels are usable;
5. confirm notifications are sane/not confusing.

That action also closes the final post-recreate real-phone Relay confirmation for the staged Card.
