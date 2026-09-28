# M02-T01 staged-HOME migration and rollback acceptance

Verdict: GREEN.

Implementation subject:
- `elmakus/pi-unraid@e8cb6c021766250b360b2488fff582afad092349`

Dependency subject:
- `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M01-T02.md@c8160b88de6ebe506e4328810d325938659934e2:96f78959ab95d6ac18bd7fc71a670383b1481a59`

Runtime subject:
- Pi `0.87.1`
- image `pi-unraid:paseo-b4e0c1e7c276`
- image ID `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`

## Discovery and bounded repair

The first staged-production clone exposed a pre-existing credential shadow in `.pi/agent/auth.json`: the `codex-lb` auth-store entry was an `api_key`, differed from the accepted dedicated `CODEX_LB_API_KEY` secret source, and authenticated to the current Codex-LB `/v1/models` endpoint with HTTP 401. No credential value was printed or persisted to evidence.

The accepted secret mount/provider-auth boundary remained authoritative. The repair adds `scripts/reconcile-codex-lb-auth-shadow.py`, which removes only the staged `codex-lb` auth-store shadow, snapshots the exact prior auth file for rollback, preserves unrelated auth entries semantically, never copies the current dedicated secret into HOME, and fails closed on malformed state or post-migration drift. Five focused synthetic contract tests cover exact rollback, unrelated-entry preservation, no-op states, malformed shadow rejection, and rollback drift rejection.

The staged acceptance harness was also made production-like:
- instruction-plane apply/status/rollback runs as accepted UID:GID `99:100`;
- provider-config and auth-shadow reconciliation run in the accepted image as `99:100`;
- only the current instruction-plane manifest and effective managed files are cloned; the production historical one-level `previous/` rollback slot is not copied into disposable staging and remains untouched on production;
- production HOME/runtime identity is fingerprinted before and after the staged run.

## Exact commands

From repository commit `e8cb6c021766250b360b2488fff582afad092349` on Tower:

```sh
python3 -m unittest \
  tests.test_codex_lb_auth_shadow_contract \
  tests.test_codex_lb_dynamic_model_catalog_contract \
  tests.test_pi_instruction_plane_contract
```

Result: `18 tests`, `OK`.

```sh
python3 tests/run_codex_lb_staged_home_acceptance.py \
  --image pi-unraid:paseo-b4e0c1e7c276
```

Result: exit 0, `"verdict": "GREEN"`.

## Live staged readback

The same-window authenticated real Codex-LB catalog contained exactly:

```text
codex-auto-review
gpt-5.5
gpt-5.6-luna
gpt-5.6-sol
gpt-5.6-terra
gpt-6-astra
gpt-6-luna
gpt-6-sol
gpt-reserve
```

The staged production clone initially had no usable provider-scoped Codex-LB LKG IDs. After the repository-managed instruction-plane apply and bounded auth-shadow removal, a fresh Pi RPC process with the still-reversible static bootstrap auto-loaded the dynamic extension and converged to exactly the nine live IDs above. The provider-scoped `models-store.json` then contained exactly those IDs.

The provider-config reconciler removed the static `models` array while preserving:
- `baseUrl = http://host.docker.internal:2455/v1`;
- `api = openai-responses`;
- `apiKey = ${CODEX_LB_API_KEY}`;
- unrelated provider/config semantics.

A second fresh Pi RPC process after static-list removal exposed exactly the same nine live Codex-LB IDs, and the persisted LKG remained identical to the live catalog.

## Rollback and isolation

Provider-config rollback restored the exact pre-change `models.json` bytes. Auth-shadow rollback restored the exact pre-change `auth.json` bytes. Instruction-plane rollback restored the prior effective managed files/modes and current manifest semantics. Both temporary reconciliation state directories were removed.

The staged HOME scan found zero occurrences of the current dedicated Codex-LB credential.

Production remained untouched by this Card: before/after production runtime identity, start time, restart count, health, provider-config fingerprint, auth-store fingerprint, and effective instruction-plane fingerprint were identical. The production Paseo runtime remained healthy with restart count `0`.
