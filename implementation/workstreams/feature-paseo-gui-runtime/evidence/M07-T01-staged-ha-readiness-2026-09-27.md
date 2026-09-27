# M07-T01 staged HA readiness — technical GREEN, HA-entry user gate pending

- Card ID: `M07-T01`
- Implementation subject: `elmakus/pi-unraid@51c0c563abd380e2bbfa5274f073940b0367b35e`
- Machine-readable evidence: `implementation/workstreams/feature-paseo-gui-runtime/evidence/M07-T01-staged-ha-readiness-2026-09-27.json`
- Technical verdict: **GREEN** for every noninteractive M07-T01 surface completed so far.
- Remaining acceptance item: explicit user-presence scheduling/start of the consolidated Human Acceptance wave. This is the P4 HA-entry authority boundary and is not inferred from the review-entry prompt.

## Authority and dependency refresh

All six exact Card dependency result bindings were re-read before launch and matched their pinned blobs:

- M05-T02B: `7bdb9fffcbada5f0dc6475f3bb2b7be92d8e1d20`
- M05-T03: `b526cf4717ea6d353fc6d23f082b1c726e7f55ed`
- M06-T01: `e01bd1dd4d84c94ec9b29f7bd1914e7160162d82`
- M06-T02: `13a49bd857c50b79213561ece74e06a585069d73`
- M06-T03: `a140f95fef4cd99a433d3b7b08f3e482e4c4dbc2`
- M06-T04: `fc2bb31f794480e3fc954d28a47ac09086f2734e`

Current requirements, ADR-PGR-001/002/003/004 and frozen P4 were re-read. The P4 boundary keeps first-time credentials, phone pairing, authenticated GraphQL/SSH proof, manual UX judgment and production cutover out of M07-T01.

## Tower readiness and isolation

Fresh readback found Unraid `7.2.4` and `unraid-api 4.37.4+ad268301` online. The dedicated `pi-unraid-paseo` Buildx builder is running. Cache readback remains 933,087,833 bytes under the accepted 8 GiB bound. Protected retention still binds `pi-unraid:paseo-b4e0c1e7c276` to candidate id `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`; current Tower image id is `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`.

Before staged provisioning there was no production `pi-unraid-paseo-1` container and no production `/mnt/user/appdata/pi-unraid/paseo-home`. The legacy `pi-unraid-pi-1` safety anchor was running and healthy. After staged provisioning those production facts remain unchanged and legacy Pi remains healthy.

## Staged runtime

A dedicated non-production Compose project `pi-unraid-staged-ha` now runs `pi-unraid-staged-ha-paseo-1` from the exact protected candidate tag.

Readback:
- container is running and `healthy`;
- runtime user is UID:GID `99:100`;
- Paseo `0.9.2`, Pi `0.87.1`, Node `v22.23.3`;
- persisted `worktrees.root=/worktrees`;
- Relay remains explicitly disabled;
- staged HOME is `/mnt/user/appdata/pi-unraid/paseo-ha-staged-home`, distinct from the production Paseo HOME;
- mounts are exactly staged HOME -> `/home/paseo`, `/mnt/user/projects` -> `/projects`, and `/mnt/user/pi-worktrees` -> `/worktrees`;
- no Docker socket is mounted;
- no host port is published; only container-local `6767/tcp` is exposed;
- shm is exactly 1 GiB; memory and NanoCPU limits are unset;
- restart policy is `no`, so this staging instance does not become production autostart;
- json-file logs remain bounded at 10 MiB x 3.

The secret-safe staged HOME manifest contains 372 entries. Immediate verification found 372/372 present, zero missing, zero altered, zero added, no Relay drift, and `ok=true`. Only hashes/metadata are retained as evidence; raw key material is not recorded.

## Tests and backup/rollback anchors

The exact implementation subject ran the complete repository unittest surface: **378/378 GREEN in 3.977 s**.

The Appdata Backup policy allows `/mnt/user/appdata`, targets `/mnt/user/appdatabackup/`, has verification enabled, and is scheduled daily at 04:00. Its last normally named successful directory is `ab_20260923_040002`; the September 24–26 runs are marked `failed`, so routine scheduled-backup health is explicitly considered degraded rather than silently treated as GREEN.

M07-T01 therefore created a bounded staged-HOME rollback/backup anchor without stopping unrelated containers. The post-initialization archive is stored mode 0600 at `/mnt/user/appdatabackup/pi-unraid-m07-t01-pre-ha/paseo-ha-staged-home-postinit-20260927T001813Z.tar`, SHA-256 `fe782f5efa36d07a87ea7e7f31ad2702b260fe11f0400814934aa8bb8d2339b2`. A pre-daemon anchor was also created. These anchors cover the current staged state; M07-T02 must refresh bounded backup evidence after user-authenticated state is materialized before relying on it for later cutover/recovery.

## Real stop

All automatic M07-T01 technical readiness work is complete. Per the accepted P4/Card boundary, the next legal transition requires the user to explicitly start/schedule the consolidated Human Acceptance wave. No credential, phone pairing, authenticated host mutation or manual UI judgment has been requested or inferred.
