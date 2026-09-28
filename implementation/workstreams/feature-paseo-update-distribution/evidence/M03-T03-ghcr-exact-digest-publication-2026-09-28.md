# M03-T03 — exact tested-image GHCR publication evidence

Date: 2026-09-28
Implementation subject: `7ac73fd0ee07ffa16ab3b74ac1c0f6768c6274a4`

## Implemented contract

- Extended the exact-candidate workflow with a separate `publish` job that depends on the successful M03-T02 build job.
- The build job remains read-only and still invokes `paseo_buildx.py build` exactly once.
- The publish job alone receives `packages: write` plus `contents: read`, checks out the same exact `CANDIDATE_HEAD`, downloads the exact tested-image artifact produced by the build job, and authenticates only to `ghcr.io` using the run-scoped `GITHUB_TOKEN`.
- Added `scripts/paseo_candidate_publish.py` to fail closed unless candidate bytes, handoff bytes, build-record bytes, source-head provenance, discovery provenance, image ID and Docker-archive SHA-256 all match the M03-T02 tested-image evidence.
- Publication loads the preserved Docker archive instead of rebuilding, verifies the loaded local image ID, tags only a candidate-readable non-authoritative GHCR alias, pushes that exact image, obtains the OCI digest through registry inspection, then independently reads the same digest back through `repository@sha256:...`.
- Machine-readable publication evidence retains the candidate/tested-image/provenance hashes, local image ID, GHCR repository, candidate alias, authoritative OCI digest and immutable digest reference for M04+.
- The publish job rejects fork PR publication by requiring the PR head repository to equal the current repository. The workflow contains no production `:accepted` tag movement, Tower/SSH action, production cutover or rollback mutation.

## Verification

Tower clean checkout outside the system temporary directory at exact subject `7ac73fd0ee07ffa16ab3b74ac1c0f6768c6274a4`:

- `python3 -m unittest tests.test_paseo_candidate_publish tests.test_paseo_candidate_build_pipeline -q` -> 13/13 GREEN.
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> 450/450 GREEN.
- `python3 -m py_compile scripts/paseo_candidate_publish.py scripts/paseo_candidate_build.py scripts/paseo_buildx.py tests/test_paseo_candidate_publish.py tests/test_paseo_candidate_build_pipeline.py` -> GREEN.
- `git diff 5287ef2186eb81d0176e5d0c8e1f4943bb3876fc..HEAD --check` -> GREEN.
- Publication-unit coverage proves fail-closed archive/source-head binding, exact local image-ID verification, one image load/push, registry digest capture and immutable digest readback. Workflow-contract coverage proves one build invocation total, exact artifact download, GHCR-only login, package-write permission only on publication, publication evidence retention, and absence of `:accepted`, SSH/Tower and rebuild operations from the publish job.

No manual live GHCR push was performed during Tower verification; package publication is intentionally owned by the GitHub-hosted operational workflow and its run-scoped package credential.
