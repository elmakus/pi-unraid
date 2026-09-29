# M07-T02 — failure and race matrix

Date: 2026-09-29
Implementation subject: `b2189728cb92c784a3fdda951994c1cda2e13e0a`

## Matrix

The bounded focused matrix executed the existing production-path contracts without production mutation:

- mutable/stale/newer-candidate and concurrent-writer races: fail closed before unauthorized mutation;
- wrong/mismatched digest and mutable rollback identity: rejected;
- production `:accepted` without GREEN final gate, matching armed guard, valid guard provenance, Tower writer domain or valid lock domain: rejected before registry mutation;
- same exact proven-incompatible core pair + unchanged gate fingerprint: cached/reused rather than retried; changed gate fingerprint or exact identity forces re-evaluation;
- independent-component stale failure identity does not poison a replaced latest identity;
- transient transport/network failure remains BLOCKED rather than being cached as incompatibility;
- immediate acceptance local failure restores the exact predecessor; failed recovery remains in rolling-back state and retains recovery authority;
- transient remote outage is non-blocking by default, while an explicitly contract-blocking remote outage rolls back;
- DockerMan stale status cannot masquerade as success; waiter restart resumes from durable armed guard and committed readback is idempotent;
- stale guard binding blocks before trigger/restore.

## Verification

Focused modules:
`tests.test_paseo_accepted_promotion`,
`tests.test_paseo_core_compat`,
`tests.test_paseo_independent_resolution`,
`tests.test_paseo_dockerman_binding`,
`tests.test_paseo_immediate_acceptance`,
`tests.test_paseo_known_good`.

Result: **53/53 GREEN**.

Full repository unit suite on the same clean subject before the focused matrix: **503/503 GREEN**.

`git diff --check`: **GREEN**.

## Production readback

Before: `pi-unraid-paseo-1` = `running healthy`, image ID `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`, configured image `pi-unraid:paseo-codex-lb-env-bc87a92`; production transaction guard absent.

After: identical `running healthy` runtime/image/configuration; production transaction guard absent.

No real Codex-LB key was used, no production cutover/restart/rollback was performed, and no successful production `:accepted` movement was exercised.
