# M05-T01 execution evidence — serialized promotion writer

Date: 2026-09-28
Implementation subject: 8bc1b27f289b918ae00f195a429ccced4337fe62
Branch: feat/paseo-update-distribution

## Implemented
- Added `scripts/paseo_accepted_promotion.py` as the project-owned exact-digest promotion writer.
- Non-production promotion binds an expected current digest, performs two registry readbacks before mutation to reject stale/superseded/racing attempts, writes only the exact immutable candidate digest, and immediately reads the alias back.
- The production `:accepted` path fails closed unless exact GREEN final-gate evidence names the same candidate digest and an exact matching transaction guard is already read back as `armed`.
- Guard predecessor, rollback and configuration identities must be immutable sha256 digests; mutable rollback tags are rejected.
- Promotion output records previous, candidate, rollback and registry-readback digests.

## Verification
Checkout: `/mnt/user/pw-m05-t01-checkout` on Tower (outside the system temporary directory), exact subject `8bc1b27f289b918ae00f195a429ccced4337fe62`.

- Focused M05-T01 tests: 7/7 GREEN.
- Full repository unit suite: 468/468 GREEN.
- `python3 -m py_compile scripts/paseo_accepted_promotion.py tests/test_paseo_accepted_promotion.py`: GREEN.
- `git diff --check`: GREEN.
- Focused coverage includes non-production promotion/readback, stale current-digest rejection, second-read newer-candidate race rejection, production rejection without GREEN final evidence, production rejection without exact matching armed guard, post-promotion digest mismatch, and mutable rollback-tag rejection.

## Registry exercise
A bounded attempt was made to seed only `ghcr.io/elmakus/pi-unraid:m05-t01-fixture` from immutable digest `sha256:22673ae79a31da54a1e539adbb2ba5dd1f4c2d33944421fb47eba15efc9b9ec3`. GHCR rejected the write with HTTP 401 before alias creation/movement because the Tower Docker client has no package-write credential. No credential was exposed or requested, and no retry/bypass was attempted.

The isolated registry behavior required by the Card is covered by the focused command/readback fixture tests. The real GHCR refusal is retained as bounded readback evidence and does not authorize production mutation.

## Safety readback
- Production `:accepted`: not addressed by any write command.
- Production container/runtime: unchanged.
- Transaction guard: not armed or mutated.
- Secrets: none exposed.
