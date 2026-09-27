# M05-T02A local Buildx/cache foundation evidence

- Implementation subject: `elmakus/pi-unraid@dcc726adfbefbf92d13a48eea222ca46aa180052`.
- Exact dependencies: `results/M05-T01-R02.md@40ad9529f7f3bb05a27caa306d21a3cdc83c5bcd:7b3855238c59f35f2cd2af05a0d1456db34832db` and `results/M01-T03.md@bbc862c37c0da81a08a91876499cfe865be958ab:3772f647f5a0c55e856d3ae8e3feb05c6fb3e1f5`, verified in the exact-SHA CI workflow.
- Changes: dedicated local `docker-container` Buildx path in `scripts/paseo_buildx.py`, frozen-candidate and immutable image readback, measured phases and guarded post-smoke prune; `.github/workflows/paseo-buildx-foundation.yml` provides disposable cold/warm evidence; `Dockerfile` separates the slow browser layer from Pi for bounded invalidation; `tests/test_paseo_buildx_contract.py` covers the contract. No private GHCR or Tower mutation.

## Verification

- Local contract suite: 12 test files, 130 tests passed. The Buildx suite covers namespace/path separation, exact frozen input, builder reuse, immutable image/label readback, phase recording, bounded prune gating, failure preservation, and exclusion of floating latest, registry and legacy standalone-Pi paths.
- [Buildx foundation CI run 36221691315](https://github.com/elmakus/pi-unraid/actions/runs/36221691315): GREEN at exact implementation SHA, including 130 contracts, exact predecessor bindings, three disposable builds, complete image/provenance, persistence/ownership, instruction-plane and global-capability smokes, then bounded prune. The uploaded machine-readable records and logs were read back.
- Cold build: fresh dedicated builder, image ID `sha256:0a389c1c7d52f5b947ba1bc6fda04b2bb41e2e37fd61d7540fc5fac1a0f8ac3d`, build 157349 ms, full smoke test 47908 ms, post-smoke prune 93 ms. Resolution/readback and builder phases also recorded; all required cold phases are `ok`.
- Warm identical build: builder reused, same image ID, 8 cached BuildKit steps, build 4901 ms. Warm bounded-label change: builder reused, distinct image ID `sha256:4e3838b97bd23e3492467eada80d2dfc8339faa301bead18174a82218096be45`, 8 cached steps, build 4830 ms. These are measured CI observations, not a time SLA.
- The prune step was gated on the same cold record's successful build and complete smoke test. The workflow verified builder cache and cold image remained inspectable after the size-bounded prune. A failed smoke test blocks prune; negative tests verify refusal without a successful tested record.

The CI runner is ephemeral, so reuse was proven across separate invocations within one job. Persistent Tower builder survival, private GHCR and registry-backed cache are the separate M05-T02B live obligation. The accepted frozen candidate, project-local locks and production state were untouched.
