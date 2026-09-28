# M02-T01 — typed discovery/freeze verification

Date: 2026-09-28  
Card: `M02-T01`

## Exact implementation subject

- Commit: `ee2addb20a2b9b25e9282264a62f6ce87005c150`
- Resolver blob: `660e6f53add77ab9684dbe09c38836df6ea2b09b`
- Resolver-test blob: `b0daacd08276d98cdf920ac1277c353603ee1eff`

## Implemented boundary

- Managed candidate inventory entries are projected into a typed source descriptor with bounded families `npm`, `github`, `oci`, and `derived`.
- GitHub release assets and the existing Docker CLI exact tag/commit identity are bounded variants of the same GitHub family.
- Typed discovery normalizes stable version plus immutable provenance; freeze revalidates the typed record and reconstructs the exact existing component/install record.
- npm requires package, integrity, shasum and exact Git source commit.
- GitHub release requires exact Git source plus release-asset digest; GitHub tag/commit forbids inventing an asset digest.
- OCI requires digest-bound reference plus linux/amd64 manifest and config digest.
- Derived identity requires a durable owner and exact immutable-parent binding to the owner reference.
- Candidate assembly now passes through the typed discovery/freeze boundary before the pre-existing compatibility/exception policy.
- No scheduler/workflow topology, compatibility search/backtracking, independent fallback, build/GHCR, Tower or production-cutover behavior was added.

## Exact-subject verification

On detached `ee2addb20a2b9b25e9282264a62f6ce87005c150`:

- `python3 -m unittest tests.test_paseo_candidate_resolver -q` -> **31/31 GREEN**.
- `python3 -m unittest tests.test_environment_capability_inventory_contract tests.test_managed_component_lifecycle -q` -> **24/24 GREEN**.
- `python3 -m unittest discover -s tests -p "test_*.py"` -> **405/405 GREEN**.
- Typed negative coverage rejects missing npm integrity, GitHub release digest, OCI digest, derived immutable parent, unsupported source kinds, source-family substitution and derived-owner drift.
- Baseline commit `1baadd009cacb66906abb144ca644c573c91416b` and implementation commit produced byte-identical fixture candidate JSON.
- Fixture candidate identity remained `sha256:f6520024c285915eab782a99f28cf451ae37c092b05eff2e1cc5957838cda085`.

## Verdict

Implementation evidence is GREEN for the M02-T01 Card acceptance surface. Independent Card review remains required.
