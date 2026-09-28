# M02-T03 — independent non-core fallback and freshness selection

Date: 2026-09-28
Card: M02-T03
Implementation subject: 2906ccdba597aaefd57cddc5cf38a0729798af3b

## Implemented scope

- Added scripts/paseo_independent_resolution.py as a separate non-core policy layer; the Paseo/Pi bounded core solver remains unchanged.
- Independent managed components are derived from the accepted managed-component registry (update_class = independent) rather than being added to Paseo/Pi backtracking.
- Exact discovered non-core identities select newest by default. A matching unavailable outcome must carry durable evidence and may fall back only to that component's previous exact accepted identity.
- BLOCKED outcomes propagate as BLOCKED and are not converted into incompatibility or a persistent known-bad entry. Failure evidence is exact-identity bound, so stale evidence cannot poison a changed upstream identity.
- Playwright and its derived Chromium record move together because fallback restores the exact previous accepted Playwright component record, including Chromium identity.
- Automatic independent fallback is authorized by the accepted policy and no longer requires a component-specific compatibility exception. Deliberate/manual compatibility exceptions remain authority-bound.
- pi-mcp-adapter peer metadata is no longer part of the core Paseo/Pi compatibility gate; install/build unavailability belongs to independent fallback and extension-specific runtime functionality remains outside the core gate.
- Added Pareto filtering and equal-weight ordinal aggregate-lag selection across caller-supplied bounded version domains. Equal aggregate lag uses only a canonical SHA-256 technical tie-break.
- Added deterministic exact-candidate no_op/update status and exposed it through --resolution-status.
- Added optional --independent-outcomes resolver input and protected it as a resolver input path against output overwrite.

## Guardrails

- No scheduler/default-branch workflow, build/GHCR publication, Tower mutation, production promotion/cutover, or new source-adapter family was added.
- Core Paseo/Pi search remains owned by scripts/paseo_core_compat.py.
- The existing normal fixture resolution remains byte-identical to the pre-card baseline.

## Verification

Exact implementation subject: 2906ccdba597aaefd57cddc5cf38a0729798af3b.

- python3 -m unittest tests.test_paseo_independent_resolution tests.test_paseo_core_compat tests.test_paseo_candidate_resolver -q -> 54/54 GREEN.
- python3 -m unittest discover -s tests -p "test_*.py" -q -> 428/428 GREEN from a checkout outside the system temporary directory, preserving the path-sensitive scope-guard contract.
- python3 -m py_compile scripts/paseo_independent_resolution.py scripts/paseo_core_compat.py scripts/resolve-paseo-candidate.py -> GREEN.
- git diff --check -> GREEN.
- Standard fixture output is byte-identical to pre-card df2068d979bf9e3b900f2c6b4ce8e19e2d3e406b: output SHA-256 8ad365a63f97e69708f2f289bd817421f751f0f0cb6feb7b6e59624436b824e0.
- Fixture candidate identity remains sha256:f6520024c285915eab782a99f28cf451ae37c092b05eff2e1cc5957838cda085.
- Tests cover extension fallback, developer-tool fallback, Playwright+Chromium unit fallback, unrelated-component advancement, exact-identity stale-evidence non-poisoning, BLOCKED propagation, automatic lag without manual exception, non-core peer metadata exclusion from the core gate, Pareto filtering, aggregate lag, deterministic tie-break and exact no-op detection.

## Result

GREEN implementation evidence. The exact implementation subject is ready to be frozen into the M02-T03 result and independently reviewed.
