# M04-T01 R01 — Independent implementation review

Date: 2026-09-26
Card: `M04-T01`
Attempt: `R01`
Verdict: **RED**

## Reviewed exact subject

- Review subject: `elmakus/pi-unraid@08c0d67f8637a9ee8476c9b046f69ee516df9dcb:implementation/workstreams/feature-paseo-gui-runtime/results/M04-T01.md@275f1c360db4719505a9e565e1805df3906e5d1e`
- Implementation commit named by the result: `45a083482855378e6085e261a6181376d4c2fa2d`
- Acceptance surface: `implementation/workstreams/feature-paseo-gui-runtime/cards/M04-T01.md`
- Frozen predecessors:
  - `implementation/workstreams/feature-paseo-gui-runtime/results/M01-T03.md@bbc862c37c0da81a08a91876499cfe865be958ab:3772f647f5a0c55e856d3ae8e3feb05c6fb3e1f5`
  - `implementation/workstreams/feature-paseo-gui-runtime/results/M02-T03.md@cac4ac5e5a4b6c96ad71d9bbce12962388f7a4be:0d13d7fe5a6dd29fb68e700d13cc5c1251722c28`

## Independence

This review context did not materially produce, reconcile, or repair the exact R01 subject.

## Independent checks

- Revalidated the exact M01-T03 and M02-T03 predecessor result blobs.
- Re-read the stable Card acceptance, PGR requirements, authority-boundary ADR, update/build/rollback ADR and P2 M04 plan slice.
- Verified the exact implementation snapshot contains one repository-owned inventory definition, `config/environment-capabilities.json`, covering all independently versioned frozen candidate components plus Chromium, generic base tooling and the repository-managed Pi instruction plane.
- Confirmed desired versions/identities are derived from `config/paseo-candidate.json` or deterministic repository-tree identity rather than duplicated floating version literals or network re-resolution.
- Confirmed the derivation path is read-only: it performs repository/input reads and JSON derivation only, with no subprocess execution, installation, reconcile, deletion or update behavior.
- Confirmed missing and mismatched approved capabilities become RED drift, unobserved state is bounded WARN, and unexpected capability IDs are surfaced as WARN without mutation.
- Confirmed the definition rejects the explicitly reserved OR/PW policy-state keys exercised by the contract tests and the rendered inventory does not itself introduce OR runtime-use policy or PW workflow authority.
- Verified GitHub Actions run `36194185759` is `completed/success` on exact implementation SHA `45a083482855378e6085e261a6181376d4c2fa2d`.

## Blocking finding

The Card's Required tests/readback explicitly requires deterministic JSON output that **contains no raw credentials**, and PGR-REQ-017 states that capability inventories, repository files and logs MUST NOT contain raw credentials.

The exact R01 implementation does not guarantee that boundary. `sanitize_observation()` drops arbitrary extra keys, but it copies the contents of allowed observation fields `version` and `location` directly into rendered output (only length-limited). Therefore credential material supplied accidentally or maliciously inside either allowed field is preserved verbatim in the machine-readable inventory.

The current secret-safety contract test covers only extra fields named `token` and `credential`; it does not place secret material inside `version` or `location`, so the GREEN CI run does not exercise the actual leakage path. For example, an observation with `location = "https://user:secret@example.invalid"` or a secret-bearing `version` string will be echoed into the output.

This is a bounded acceptance defect inside M04-T01: observation rendering needs a secret-safe normalization/redaction policy for allowed string fields, plus contract coverage proving secret material cannot be emitted through those fields, while preserving the required version/drift semantics.

## Verdict

**RED** — bounded correction inside the accepted M04-T01 authority is required before the Card can pass required independent review.
