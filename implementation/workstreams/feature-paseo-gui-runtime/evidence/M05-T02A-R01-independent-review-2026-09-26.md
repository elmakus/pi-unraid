# M05-T02A R01 independent review — RED

- Exact result subject: `elmakus/pi-unraid@37cafe03986fdd2d1033877b962c6194c05a1a85:implementation/workstreams/feature-paseo-gui-runtime/results/M05-T02A.md@2bdccbfb850e1594ab4a30ac4b43650301f3d2a9` (Git blob verified).
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M05-T02A.md`.
- Implementation subject named by result: `elmakus/pi-unraid@dcc726adfbefbf92d13a48eea222ca46aa180052`.
- Independence: the reviewing context did not materially produce, reconcile or repair this result or its implementation. It rechecked its initial recommendation before issuing this terminal verdict.

## Passing evidence retained

The exact predecessor result bindings, frozen candidate continuity and four-file implementation scope were verified. [Buildx CI run 36221691315](https://github.com/elmakus/pi-unraid/actions/runs/36221691315) was GREEN on the exact implementation SHA: 130/130 contract tests, cold build with fresh dedicated builder, warm identical and bounded-change builds with 8 cached steps each, four disposable smokes, then size-bounded prune. The uploaded cold record contains successful measured resolution/readback, build, test and prune phases; cache and image remained inspectable after pruning. Local contracts also passed 130/130. No private GHCR, Tower, production or legacy standalone-Pi mutation was performed.

## Blocking findings

1. **RED-1 — Wrong effective base can pass frozen-input validation.** `verify_build_inputs` searches Dockerfile text for the expected `FROM` substring. A build context with an actual `FROM` naming a different Paseo digest and the expected frozen `FROM` only in a comment passes validation. In a controlled mocked-Docker run, `cmd_build` proceeds, returns build success and writes a record claiming the frozen candidate while building from the wrong effective base. The supported `--context` option makes this reachable. It violates the Card's requirement to reject mismatched immutable identities. Parse effective Dockerfile instructions rather than comments; reject wrong digest and comment aliases in regression tests.
2. **RED-2 — Shared default builder is accepted.** `--builder default` and `PI_UNRAID_BUILDX_BUILDER=default` pass the namespace guard. The tool then invokes `docker buildx build --builder default`; standalone prune can likewise invoke `docker buildx prune --builder default`. This reaches the shared default cache instead of the dedicated namespace required by the Card. Apply one reserved-name validator to build and prune and test both flag and environment entry paths.

Both findings are bounded corrections inside the existing Card authority. Preserve this RED attempt, correct the implementation, run the full contracts and exact-SHA cold/warm/smoke/prune CI, then freeze a new result and independent review attempt. The reviewer also noted that a forged local record could release bounded prune; it classified this as an operator-local trust assumption without a Card attestation requirement, not a blocking finding.

The review environment had no local Docker. The two failures were reproduced with mocked Docker decisions and no repository or production writes; real build/smoke/prune evidence came from exact-SHA CI artifacts.
