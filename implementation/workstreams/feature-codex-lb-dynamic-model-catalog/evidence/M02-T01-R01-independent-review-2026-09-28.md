# M02-T01 R01 independent review evidence

Reviewed subject:
- result: `elmakus/pi-unraid@ad5ca62c34673ca4ea088a56c15e2697b0eb3c96:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M02-T01.md@4f10d2754a9722e0f38b69676fef5eacd8f0fb0f`
- implementation subject: `elmakus/pi-unraid@e8cb6c021766250b360b2488fff582afad092349`
- acceptance: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/cards/M02-T01.md`
- exact dependency: `M01-T02@c8160b88de6ebe506e4328810d325938659934e2:96f78959ab95d6ac18bd7fc71a670383b1481a59`

Verdict: GREEN.

## Independent review

R01 inspected the exact frozen result, Card acceptance, CLDMC requirements/ADR/plan authority, staged acceptance evidence, and the complete implementation delta from the launch baseline through `e8cb6c021766250b360b2488fff582afad092349`.

The implementation delta is bounded to the staged-HOME acceptance harness, a reversible `codex-lb` auth-shadow reconciler, and its focused contract tests. It does not mutate the production HOME, Codex-LB service/OAuth routing, Paseo image/container lifecycle, automatic model-selection behavior, or the separate Paseo update/distribution workstream.

The auth-shadow reconciler removes only the persisted `codex-lb` API-key entry from staged `auth.json`, preserves unrelated auth entries semantically, snapshots exact prior bytes with restrictive permissions, refuses malformed/symlink/drifted state, and restores exact prior bytes on rollback. It does not copy the accepted dedicated credential into HOME or evidence.

## Independent verification

Exact implementation files were unchanged between implementation subject `e8cb6c021766250b360b2488fff582afad092349` and the frozen result commit.

Commands rerun on Tower:

```sh
python3 -m unittest tests.test_codex_lb_auth_shadow_contract tests.test_codex_lb_dynamic_model_catalog_contract tests.test_pi_instruction_plane_contract
python3 tests/run_codex_lb_staged_home_acceptance.py --image pi-unraid:paseo-b4e0c1e7c276
```

Results:
- contract tests: 18/18 GREEN;
- staged acceptance: GREEN on Pi 0.87.1;
- same-window authenticated real Codex-LB and fresh staged RPC both exposed exactly 9 IDs;
- provider-scoped LKG contained the same 9 IDs;
- provider config, staged auth store and effective instruction plane restored to their exact pre-change accepted state;
- raw current dedicated-secret scan: zero hits;
- production container identity, health, start time, restart count, provider-config hash, auth-store hash and effective instruction-plane fingerprint were identical before and after.

No blocking acceptance, scope, rollback, secret-boundary or reproducibility defect remains in the exact R01 subject.
