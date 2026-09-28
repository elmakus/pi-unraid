# M01-T01 R04 independent review evidence

Reviewed subject:
- result blob: `elmakus/pi-unraid@bedf22af3a27fc823b0b5bf7001c71c3822a1629:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M01-T01.md@0ec960b8eabe20d4c955eca01aa1aa2805aae13c`
- implementation subject named by that result: `elmakus/pi-unraid@2c38c280f1f7a78045ead22b4aa70f21a6992680`
- acceptance: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/cards/M01-T01.md`

Verdict: GREEN.

## Independent checks performed

The review inspected the exact frozen result, the corrected implementation subject, the full provider-config reconciler, dynamic provider extension/core, focused Python/Node tests, the R03 RED finding and correction evidence, and the accepted CLDMC requirements/ADR/plan authority.

The R03 fail-closed URL-authority mismatch is closed. The reconciler now rejects percent-encoded and non-ASCII authorities, accepts bracketed authorities only when the hostname parses as real IPv6, restricts ordinary hosts to the accepted ASCII subset, and retains the earlier credentials/query/fragment/backslash/control/port checks. Regression fixtures cover the exact percent-encoded and invalid bracketed-host classes identified by R03.

## Independent exact-subject verification

On Tower, the reviewer created a disposable temporary clone, checked out exact implementation subject `2c38c280f1f7a78045ead22b4aa70f21a6992680`, and ran:
- `python3 -m unittest tests.test_pi_instruction_plane_contract tests.test_codex_lb_dynamic_model_catalog_contract` — 13 tests GREEN;
- `node tests/codex_lb_dynamic_model_catalog_core_test.mjs` — GREEN;
- `git diff --check 9805d9b0c08465d5cbfbfe9f0f99a13a405ddaf9..HEAD` — GREEN.

The disposable clone was removed automatically. No production HOME, Paseo container/image, or Codex-LB service state was mutated.

No blocking acceptance defect remains in the exact R04 subject.
