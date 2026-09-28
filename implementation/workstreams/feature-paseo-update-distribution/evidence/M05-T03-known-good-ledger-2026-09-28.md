# M05-T03 execution evidence — known-good ledger and guard-input contract

Date: 2026-09-28
Branch: feat/paseo-update-distribution

## Implemented
- Added `scripts/paseo_known_good.py` with strict immutable-digest validation and exactly three ledger slots: `current`, `previous_1`, `previous_2`.
- Rotation is deterministic: a new current shifts current -> previous_1 and previous_1 -> previous_2; a same-current update is idempotent.
- Guard-input materialization binds exact candidate digest, predecessor digest, production-configuration digest and independently retrievable rollback-anchor path, and emits `state: unarmed`.
- Mutable tags are rejected as ledger identities.

## Tower readback
- Active production remained `pi-unraid-paseo-1`, running/healthy, image `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`, configured image `pi-unraid:paseo-codex-lb-env-bc87a92`.
- Durable ledger at `/mnt/user/appdata/pi-unraid/update-distribution/known-good.json` records current `sha256:05e140...`, previous_1 `sha256:4bf8bb...`, previous_2 `sha256:ddb23c...`; all three local immutable images were retained and the previous_1 image was independently inspectable.
- Rollback-anchor readback was persisted at `/mnt/user/appdata/pi-unraid/update-distribution/rollback-anchor.json`.
- Guard-input readback binds candidate GHCR digest `sha256:22673ae79a31da54a1e539adbb2ba5dd1f4c2d33944421fb47eba15efc9b9ec3`, predecessor `sha256:05e140...`, template configuration digest `sha256:ebc1b352c340e1796f30bdb1b9b0df5424294bd8e5465b027f5dffb7c1f13f89`, the rollback anchor, and remains explicitly `unarmed`.
- Production `ghcr.io/elmakus/pi-unraid:accepted` still returned `manifest unknown`; no tag write, production restart/cutover/rollback, or transaction-guard arm occurred.

## Verification
- Focused known-good tests: 3/3 GREEN.
- Full repository unit suite: 477/477 GREEN from `/mnt/user/pw-m05-t03`, outside the system temporary directory.
- `git diff --check`: GREEN.
