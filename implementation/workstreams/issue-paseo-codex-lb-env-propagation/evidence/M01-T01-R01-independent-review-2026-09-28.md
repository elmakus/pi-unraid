# M01-T01 R01 independent review evidence

Reviewed subject:
- result: `elmakus/pi-unraid@fad7a0289dcf226e542c056bc7b0254f639ed776:implementation/workstreams/issue-paseo-codex-lb-env-propagation/results/M01-T01.md@2c06f36f79f8e151684e4d5f486ab2f1f90e9f50`
- implementation subject: `elmakus/pi-unraid@167651060a18054ba1033cb2bda31b67ceee4494`
- acceptance: `implementation/workstreams/issue-paseo-codex-lb-env-propagation/cards/M01-T01.md`

Verdict: GREEN.

## Independent subject verification

R01 independently re-derived the exact frozen result blob and confirmed it matches `2c06f36f79f8e151684e4d5f486ab2f1f90e9f50`. The implementation subject is immutable at `167651060a18054ba1033cb2bda31b67ceee4494`. Changes after that subject are limited to durable result/Task Board/review bookkeeping; no runtime implementation file changed after the reviewed implementation subject.

## Independent deterministic verification

A detached worktree at the exact implementation subject was used for review verification:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/codex_lb_dynamic_model_catalog_core_test.mjs
git diff --check 1eaffc98660da3d89a6f2d473570db931c9dc38f..HEAD
```

Results:
- full Python suite: **403/403 GREEN**;
- affected Node dynamic-catalog core suite: **GREEN**;
- diff check: **GREEN**.

The source contract enforces the repository-managed Paseo entrypoint bridge, canonical Compose secret mount and `host.docker.internal:host-gateway`, fail-closed parsing for malformed non-empty secret input, no raw credential in Compose/image environment, preservation of the pinned upstream Paseo entrypoint, and no Paseo/Pi upstream source patch.

The production wrapper at `/usr/local/bin/pi-unraid-paseo-entrypoint` hashes exactly to the reviewed source wrapper, and `/usr/local/bin/paseo-docker-entrypoint` resolves to that project-owned wrapper while the pinned upstream entrypoint remains executable under `/usr/local/libexec/pi-unraid/`.

## Independent production readback

Current production readback is consistent with the accepted result:
- container ID `9477662964b187f85b3f9e1a59e0ecd7143f4069e646472d7872a3cebef981af`;
- image ID `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`;
- running `true`, health `healthy`, restart count `0`;
- configured environment contains `PI_CODEX_LB_SECRET_FILE=/run/secrets/pi-unraid-codex-lb` and does not contain `CODEX_LB_API_KEY`;
- the dedicated Codex-LB secret is a read-only mount at `/run/secrets/pi-unraid-codex-lb`;
- `host.docker.internal:host-gateway` is present.

`paseo provider models pi` independently returns all nine current Codex-LB models without any manual secret sourcing: `codex-auto-review`, `gpt-5.5`, `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-6-astra`, `gpt-6-luna`, `gpt-6-sol`, `gpt-reserve`.

## Durable LLM-test policy verification

The policy is durably present in all required surfaces:
- `config/pi-agent/policies/LLM_TEST_POLICY.md`;
- `config/pi-agent/policies/llm-test-policy.json`;
- `config/pi-agent/AGENTS.md`;
- `config/pi-agent/bin/run-llm-test.sh`;
- `docs/LLM_TEST_POLICY.md`.

The machine policy fixes real LLM tests to provider `codex-lb`, model `gpt-6-luna`, thinking `low`, explicitly forbids `gpt-6-astra`, and disables fallback. The canonical launcher accepts no model/thinking override and rejects policy drift. Production copies of the managed policy/launcher match the reviewed source hashes; the deployed launcher is executable mode `0755` and managed files are owned `99:100`.

The previously accepted real-inference agent was independently read back as:
- name `LLM-TEST:gpt-6-luna:low`;
- model `codex-lb/gpt-6-luna`;
- thinking `low`;
- status `idle`.

No additional real LLM inference was executed during R01 review. Therefore review itself could not accidentally use Astra or another model.

## Conclusion

The exact reviewed result satisfies the stable Card acceptance. Credential propagation is repository-managed and reproducible rather than a production-only hotfix; Paseo-launched Pi catalog discovery works through the permanent runtime boundary; the raw credential is not persisted in Docker configured environment; the Luna/low-only real-LLM test rule is both human-readable and machine-enforced with Astra explicitly forbidden; production remains healthy with rollback readiness retained. No blocking defect remains in the exact R01 subject.
