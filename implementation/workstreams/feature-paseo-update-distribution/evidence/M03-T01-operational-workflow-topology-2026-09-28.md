# M03-T01 — operational default-branch workflow topology

Date: 2026-09-28
Card: M03-T01
Implementation subject: 717172b3e23327ae87e5c7a64f89d764081c6392

## Implemented scope

- Replaced the historical feature-branch candidate resolver trigger with daily schedule plus manual dispatch, guarded to the repository default branch.
- Added one concurrency group with cancellation of stale overlapping discovery runs.
- The resolver freezes exactly one candidate file per run and validates that exact file before handoff classification.
- Added `scripts/paseo_candidate_handoff.py` to classify exact candidate identity as `no_op` or `update` against the accepted candidate without re-resolving.
- `no_op` creates no handoff directory, candidate artifact, evidence file or pull request.
- `update` preserves the exact frozen candidate bytes plus machine-readable evidence containing candidate identity, accepted identity, file digest and source SHA/ref.
- Material changes upload the handoff artifact and create/update the deterministic `automation/paseo-update-candidate` branch/PR using exact-head `--force-with-lease` protection.
- Candidate workflow permissions are limited to repository contents and pull-request writes required for the handoff; it does not build/publish images, touch GHCR, Tower, production tags or production runtime.
- Removed stale automatic `push` activation on `feat/paseo-gui-runtime` from the six historical validation workflows; they remain available through manual dispatch.

## Verification

- Exact subject targeted suite: `63/63 GREEN` for M03 topology/handoff plus M02 resolver/core/independent regressions.
- Exact subject full repository suite from a full-history checkout outside the system temporary directory: `437/437 GREEN`.
- `python3 -m py_compile` for the resolver/core/independent/handoff scripts: GREEN.
- `git diff --check`: GREEN.
- Static topology readback confirms no workflow contains the closed `feat/paseo-gui-runtime` trigger or any automatic `push` trigger.

## Result

GREEN implementation evidence. The exact implementation subject is ready for semantic result binding and an independent review.
