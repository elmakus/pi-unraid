# M03-T02 — build-once candidate pipeline evidence

Date: 2026-09-28
Implementation subject: `c50028af07193aeb868166a06b0c667af7a0d9cb`

## Implemented contract

- Added a candidate-only GitHub-hosted workflow guarded to the deterministic `automation/paseo-update-candidate` handoff and the repository default branch ancestry.
- The workflow requires the candidate commit to differ from its parent only by `candidates/paseo-update/candidate.json` and `candidates/paseo-update/evidence.json`, verifies the exact frozen M03-T01 result, and never re-runs candidate resolution.
- Added an isolated candidate-context renderer. It binds candidate bytes, M03-T01 evidence, accepted-candidate identity, discovery source SHA/ref, then renders only candidate-bound Dockerfile literals into a disposable context while leaving accepted source state unchanged.
- Generalized the existing Buildx smoke runner so staged builds execute smoke scripts/config from the exact isolated context. The new `core` smoke profile gates image provenance/runtime/persistence/instruction invariants while keeping optional extension feature behavior out of the blocking M03 core gate; historical `full` behavior remains the default.
- The workflow invokes the existing Buildx build command exactly once with the frozen candidate and reuses that loaded exact image for core smoke.
- After GREEN build/smoke, packaging rechecks the local image ID, saves that same tested image to a Docker archive, rechecks the image ID, and records streaming SHA-256 plus candidate/handoff/build-record identities for M03-T03. No rebuild is used to create the publishable handoff.
- Workflow permissions are `contents: read`; there is no GHCR login/push/tag, Tower access, production secret, accepted-channel movement or production mutation.

## Verification

- Exact-subject targeted suite: 122/122 GREEN for candidate build pipeline, Buildx, child image, operational topology, resolver/core compatibility, independent-resolution fallback and global-capability contracts.
- Exact-subject full repository suite from `/root/pw-review/m03-t02-subject` (outside the system temporary tree): 446/446 GREEN.
- `python3 -m py_compile` on the changed build/handoff code and relevant resolver modules: GREEN.
- `git diff 5ffd9e0dc6c15319926041df45cbb93bee70fa8e..c50028af07193aeb868166a06b0c667af7a0d9cb --check`: GREEN.
- Real resolver-render readback: a valid candidate produced by `resolve-paseo-candidate.py --fixture ... --check` was staged through `paseo_candidate_build.py prepare`; the resulting isolated Dockerfile/config passed the existing exact `paseo_buildx.verify_build_inputs` contract. A deliberate reserved-builder preflight then failed only at builder validation, after candidate/build-input verification, proving no hidden dependency on accepted config.

## Scope readback

The M03-T02 workflow contains no candidate resolver invocation, registry publication credentials/actions, GHCR push, accepted tag, SSH/Tower operation or production mutation. Optional extension feature smoke is not part of the `core` candidate gate; independent component fallback semantics remain owned by the accepted M02 resolver and its exact-identity outcome contract.
