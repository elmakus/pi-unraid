# M06-T01 execution evidence — durable transaction guard

Date: 2026-09-29
Branch: feat/paseo-update-distribution
Implementation subject: `055f76637bc6a44cd91d45b6ead795c360f3d259`

## Implemented
- Added `scripts/paseo_transaction_guard.py` with durable states `armed`, `observed`, `validating`, `committed`, `rolling-back`, and `recovered`.
- Guard binding is a deterministic digest over the exact candidate digest, predecessor digest, production-configuration digest and independently retrievable rollback-anchor path.
- Durable writes use atomic replace plus fsync; strict readback recomputes and verifies the binding.
- Re-arming the identical active guard is idempotent; rebinding an active guard fails closed.
- Invalid transitions and stale binding digests fail closed. Terminal committed/recovered states cannot silently reacquire rollback authority.
- Production accepted-channel validation now also requires the armed guard predecessor and rollback identity to equal the writer's exact expected current digest.

## Verification
- Focused transaction-guard + promotion + known-good tests: 17/17 GREEN.
- Full repository unit suite: 481/481 GREEN from `/mnt/user/pw-m05-t03`, outside the system temporary directory.
- `git diff --check`: GREEN.
- Read-only production baseline remained `pi-unraid-paseo-1` running/healthy on image `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`.
- No production `:accepted` move, production restart/cutover/rollback or real transaction-guard arm was performed.
