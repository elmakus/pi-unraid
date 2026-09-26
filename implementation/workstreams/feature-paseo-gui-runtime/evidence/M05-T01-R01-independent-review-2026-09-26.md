# M05-T01 R01 independent review — RED

- Exact result subject: `elmakus/pi-unraid@456a795737cf981d7297daa45549a9fd78d3e74a:implementation/workstreams/feature-paseo-gui-runtime/results/M05-T01.md@783e1f2696f228a94be26ebc1ac9b1ea9d8a1af3` (Git blob verified).
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M05-T01.md`.
- Implementation subject named by result: `elmakus/pi-unraid@0e073c125d8bd57bd593c269d081fec079fd791e`.
- Independence: the reviewing context did not materially produce, reconcile or repair the exact result or implementation subject. The implementation context did not issue this verdict.

## Passing evidence retained

The exact M04-T03 predecessor result binding and R01 GREEN were verified. The resolver contract suite passed 23/23 tests; the complete local contract suite passed 93/93. [Candidate resolver CI run 36217220455](https://github.com/elmakus/pi-unraid/actions/runs/36217220455) and [child-image CI run 36217220470](https://github.com/elmakus/pi-unraid/actions/runs/36217220470) both completed successfully on the exact implementation SHA. The first includes read-only live resolution; the second includes the frozen child-image build and disposable image/runtime smokes. Independent checks confirmed repeatability, stable-line/provenance binding, rejection of missing or incompatible components and unapproved lag, and no changes to the accepted candidate, inventory, Dockerfile or project-local locks in the implementation diff.

## Blocking findings

1. **F1 — Secret-bearing candidate accepted.** A fixture with a `token` field under `components.pi` passes `--check`, which prints the value, and `--output`, which writes it to a staged candidate. `--validate` and `--readback` then accept that file. The validator rejects only five named secret fields; it does not enforce the Card requirement that frozen output never include secrets. The CI workflow prints resolved candidates to logs, so this output path can also disclose the value there. A `password` field is rejected as a control. The reviewer reproduced the behavior in temporary files; the repository and accepted candidate were not modified.
2. **F2 — Accepted candidate write guard bypassed.** With an alternative `--inventory` whose `candidate_source` points to a staging path, `--output` pointing to the real `config/paseo-candidate.json` succeeds and replaces its bytes. The default inventory correctly refuses the same output. The guard derives the protected path only from the caller supplied inventory, though the Card requires the accepted candidate to remain unchanged until staged promotion. The reviewer reproduced this in a byte-identical temporary repository copy; the real accepted candidate was not modified.

Both findings are within the current Card's accepted authority and have bounded repairs. For F1, reject unknown component fields through an explicit schema allowlist and keep the existing secret-name check as a second barrier. For F2, protect the accepted path from both the canonical inventory and any supplied inventory; fail closed if canonical state cannot be read. Add negative tests showing no secret in output or error and no candidate write on F1, plus refusal and byte-identical accepted-candidate preservation on F2. Re-run the resolver and full suites and both CI workflows on a new exact implementation SHA. Preserve this RED attempt and freeze a new review attempt for any corrected result.

## Verification limits

The review environment could not rerun live upstream resolution because GitHub returned HTTP 403; the exact-SHA CI log provides that evidence. Local Docker was unavailable, so image build and smoke evidence comes from the exact-SHA CI run. These limits do not affect the two reproduced failures.
