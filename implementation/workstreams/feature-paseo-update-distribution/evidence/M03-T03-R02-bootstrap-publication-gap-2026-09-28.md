# M03-T03-R02 — bootstrap publication gap

Date: 2026-09-28
Card: `M03-T03`
Attempt: `R02`

## Exact subject

- Result commit: `368006fee9174932e78d273bb2b441ff2df62c71`
- Result blob: `e62506a60dbee2623a482349914c27ee73f5cfb0`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M03-T03.md`
- Implementation subject: `7ac73fd0ee07ffa16ab3b74ac1c0f6768c6274a4`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M03-T03.md`

## Finding

The implementation and contract tests for the publication stage are GREEN, but the exact Card acceptance is not satisfied.

The Card requires that the tested image **is published to GHCR** and that the immutable registry digest is captured/read back as downstream authority. Its durable implementation evidence explicitly states that no live GHCR push was performed. Repository readback also shows no `automation/paseo-update-candidate` branch and no run of the new exact-candidate build/publish workflow.

There is an additional bootstrap topology conflict: `.github/workflows/paseo-candidate-build.yml` exists on the feature branch but not on `main`. The workflow jobs only run for `automation/paseo-update-candidate`, while that candidate branch must be based on the default branch and contain only the two candidate handoff files. Therefore the currently implemented operational path cannot produce the first required immutable digest before integration without a bounded topology correction or a planning/order correction.

This also leaves plan gate G3 ("M03 must produce one tested immutable digest before Tower work can trust a candidate") unsatisfied. M04 must not be materialized as though such a digest already exists.

The earlier R01 GREEN remains immutable history but was over-permissive because it treated publication implementation as equivalent to the Card's required publication effect.

## Verdict

**RED.**

The exact frozen subject does not satisfy the M03-T03 acceptance contract until a real tested GHCR digest is durably produced and read back.
