# M03-T03-R01 — independent GHCR exact-digest publication review

Date: 2026-09-28
Card: `M03-T03`
Attempt: `R01`

## Exact subject

- Frozen result commit: `368006fee9174932e78d273bb2b441ff2df62c71`
- Frozen result blob: `e62506a60dbee2623a482349914c27ee73f5cfb0`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M03-T03.md`
- Implementation subject: `7ac73fd0ee07ffa16ab3b74ac1c0f6768c6274a4`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M03-T03.md`

## Independence

This review context did not materially produce, reconcile or repair the exact M03-T03 implementation, result subject or R01 attempt before issuing the verdict. It independently read the canonical router and REVIEW contract, exact Card, pointed requirements/ADR/plan authority, M03-T02 dependency result, implementation source, tests and durable implementation evidence.

## Review

The publication path consumes the exact M03-T02 tested-image artifact and does not rebuild in the publish job. The workflow checks out the same exact `CANDIDATE_HEAD`, downloads the handoff artifact keyed by that head and gates package publication on the successful build job.

`paseo_candidate_publish.py` fails closed on candidate identity, accepted-candidate binding, candidate/handoff/build-record byte hashes, exact source-head provenance, discovery provenance, local image ID and Docker-archive SHA-256 before any Docker publication command. It loads the preserved archive, verifies the loaded image ID, tags only a `candidate-<candidate_id>` alias, pushes that image, captures the registry OCI digest and independently reads the same digest back through the immutable `repository@sha256:...` reference.

The publish job alone receives `packages: write` plus `contents: read`, authenticates only to `ghcr.io` with the run-scoped `GITHUB_TOKEN`, rejects fork-PR publication, and contains no production `:accepted` movement, Tower/SSH access or production mutation. Machine-readable publication evidence retains the candidate/tested-image/provenance hashes, image ID, repository, candidate alias, digest and immutable reference for downstream use.

Independent verification on Tower from a fresh checkout at exact implementation subject `7ac73fd0ee07ffa16ab3b74ac1c0f6768c6274a4`:
- targeted M03-T03/M03-T02 regression suite: 13/13 GREEN;
- `py_compile`: GREEN;
- exact implementation-range `git diff --check`: GREEN;
- full repository unit suite: 450/450 GREEN.

No blocking defect was found against the exact M03-T03 Card acceptance. A live GHCR publication was not replayed by this reviewer; the Card's required review surface is satisfied by the exact publication implementation plus workflow/contract verification, while the operational workflow owns package publication with its run-scoped credential.

## Verdict

**GREEN.**

The frozen R01 subject satisfies the M03-T03 acceptance contract.
