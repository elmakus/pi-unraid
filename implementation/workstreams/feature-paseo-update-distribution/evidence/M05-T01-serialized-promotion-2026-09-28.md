# M05-T01 execution evidence — serialized promotion writer

Date: 2026-09-28
Implementation subject: aebe0096074338c48ba5fc43a32e4d7920158098
Branch: feat/paseo-update-distribution

## Implemented
- Added `scripts/paseo_accepted_promotion.py` as the project-owned exact-digest promotion writer.
- Non-production promotion binds an expected current digest, performs two registry readbacks before mutation to reject stale/superseded/racing attempts, writes only the exact immutable candidate digest, and immediately reads the alias back.
- The production `:accepted` path fails closed unless exact GREEN final-gate evidence names the same candidate digest and an exact matching transaction guard is already read back as `armed`.
- Guard predecessor, rollback and configuration identities must be immutable sha256 digests; mutable rollback tags are rejected.
- Promotion output records previous, candidate, rollback and registry-readback digests.

## R01 correction

Independent review M05-T01-R01 found that double registry readback alone left a race between the second read and the write. The writer now takes an exclusive per-repository/alias OS file lock before the authoritative read-check-write-readback sequence. The production topology for this project-owned writer is a single Tower-side writer domain; the lock additionally serializes competing local processes. A focused contention test starts two writers from the same expected digest and proves the winner is the only process that issues a mutation while the loser re-reads the winner digest and fails closed.

## Verification
Checkout: `/mnt/user/pw-m05-t01-checkout` on Tower (outside the system temporary directory), exact subject `aebe0096074338c48ba5fc43a32e4d7920158098`.

- Focused M05-T01 tests: 8/8 GREEN.
- Full repository unit suite: 469/469 GREEN.
- `python3 -m py_compile scripts/paseo_accepted_promotion.py tests/test_paseo_accepted_promotion.py`: GREEN.
- `git diff --check`: GREEN.
- Focused coverage includes non-production promotion/readback, stale current-digest rejection, second-read newer-candidate race rejection, two concurrent writers contending from the same expected digest with only the winner permitted to mutate, production rejection without GREEN final evidence, production rejection without exact matching armed guard, post-promotion digest mismatch, and mutable rollback-tag rejection.

## Registry exercise
A bounded attempt was made to seed only `ghcr.io/elmakus/pi-unraid:m05-t01-fixture` from immutable digest `sha256:22673ae79a31da54a1e539adbb2ba5dd1f4c2d33944421fb47eba15efc9b9ec3`. GHCR rejected the write with HTTP 401 before alias creation/movement because the Tower Docker client has no package-write credential. No credential was exposed or requested, and no retry/bypass was attempted.

The isolated registry behavior required by the Card is covered by the focused command/readback fixture tests. The real GHCR refusal is retained as bounded readback evidence and does not authorize production mutation.

## Safety readback
- Production `:accepted`: not addressed by any write command.
- Production container/runtime: unchanged.
- Transaction guard: not armed or mutated.
- Secrets: none exposed.
