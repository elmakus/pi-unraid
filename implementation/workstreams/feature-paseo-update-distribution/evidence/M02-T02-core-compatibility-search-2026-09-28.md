# M02-T02 — core Paseo/Pi compatibility search evidence

Date: 2026-09-28  
Card: M02-T02  
Implementation subject: `5378f29b1294da20053242e8c3b91a947a0e5e86`

## Implemented scope

- Added a bounded newest-first compatibility search for the core Paseo/Pi pair only.
- Node remains derived from the exact Paseo OCI identity and is checked against the project Pi Node floor plus the discovered Pi package Node engine range when available.
- Live fallback domains are bounded at the currently accepted Paseo/Pi baseline; normal forward resolution never searches below the accepted baseline.
- Added a content-addressed nogood cache contract scoped to exact Paseo/Pi immutable identities, the core gate ID/definition hash, the inventory compatibility-contract hash, the platform/runtime fingerprint, and the incompatible failure class.
- Proven incompatible dynamic gate results require durable evidence before they may enter the cache.
- Changed pair identity, gate hash, contract hash, or platform fingerprint invalidates stale cache reuse.
- Network/transient transport failures and explicit gate BLOCKED outcomes classify as BLOCKED and are never recorded as incompatibility.
- Independent components do not participate in this backtracking search. Existing authority-bound independent compatibility exceptions remain separate.
- Added optional resolver inputs for exact core nogood cache, gate-definition fingerprint, platform fingerprint, and an operational search budget. Budget exhaustion is `RESOLUTION_INCOMPLETE`, not a successful fallback.
- No M02-T03 independent-component fallback, aggregate-lag/Pareto tie-break, Playwright/Chromium fallback, workflow scheduling, build/GHCR, Tower, promotion, or production mutation behavior was added.

## Verification

On the implementation content committed as `5378f29b1294da20053242e8c3b91a947a0e5e86`:

- `python3 -m unittest tests.test_paseo_core_compat tests.test_paseo_candidate_resolver -q` -> **43/43 GREEN**.
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> **417/417 GREEN**.
- `python3 -m py_compile scripts/paseo_core_compat.py scripts/resolve-paseo-candidate.py` -> **GREEN**.
- `git diff --check` -> **GREEN**.
- Existing fixture candidate output is byte-identical to the accepted M02-T01 implementation baseline; SHA-256 of rendered fixture output remains `8ad365a63f97e69708f2f289bd817421f751f0f0cb6feb7b6e59624436b824e0`.
- Fixture candidate identity remains `sha256:f6520024c285915eab782a99f28cf451ae37c092b05eff2e1cc5957838cda085`.

## Result

Implementation evidence is GREEN and satisfies the M02-T02 execution contract. Independent review remains required before Card finalization.
