# M02-T02 production activation evidence

Verdict: GREEN.

Implementation subject:
- `elmakus/pi-unraid@9f9c7653c93105154808dd6504d5d13ca51e4826`

Dependency subject:
- `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M02-T01.md@ad5ca62c34673ca4ea088a56c15e2697b0eb3c96:4f10d2754a9722e0f38b69676fef5eacd8f0fb0f`

Runtime:
- Pi `0.87.1`
- image `pi-unraid:paseo-b4e0c1e7c276`
- production container ID `fb0722489b579e796605f08094feec8e031237ed200ad1a1943384621a291fd0`
- container start time remained `2026-09-28T09:16:28.292365808Z`
- health remained `healthy`; restart count remained `0`

## One-shot production activation

Exact command:

```sh
python3 tests/run_codex_lb_production_activation.py --image pi-unraid:paseo-b4e0c1e7c276
```

Result: exit 0, `verdict=GREEN`. The command was not replayed after the verified expected external effect.

Production changes and readback:
- instruction-plane apply changed state and status is `in_sync=true`, source digest `sha256:00405ab148b91d73c7d38c131a8a47d228f189d33da8bbd51d537c844e7c8f42`;
- persisted `codex-lb` auth shadow was removed; current auth SHA-256 is `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`; auth rollback is available;
- provider config migrated from `9be7ad743160fb5eaf889d4811ea9dfd625ecd6fe871a18c4cb23404740928ff` to dynamic `b91fae25b9c91515fcfda7769daac14a7c176d2fd2a41e4e766723c4bfdeee37`; provider rollback is available;
- `baseUrl`, `api: openai-responses`, `apiKey=${CODEX_LB_API_KEY}` and unrelated provider semantics remained accepted;
- same-window live Codex-LB, the seed production Pi RPC, the post-migration fresh production Pi RPC and persisted provider-scoped LKG all contained exactly 9 IDs: `codex-auto-review, gpt-5.5, gpt-5.6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-6-astra, gpt-6-luna, gpt-6-sol, gpt-reserve`;
- no container rebuild, replacement or restart was required.

Security and recovery:
- current dedicated-secret scan of production HOME: zero hits;
- current dedicated-secret scan of all tracked repository files: zero hits;
- rollback anchors remain present for instruction plane, auth shadow and provider config;
- anchor directories are mode `700`; auth/provider snapshots are mode `600`; owner is `99:100`;
- no Codex-LB service, OAuth/account-routing state or separate Paseo update/distribution workstream was mutated.

Post-write verification:
- `python3 -m unittest tests.test_codex_lb_auth_shadow_contract tests.test_codex_lb_dynamic_model_catalog_contract tests.test_pi_instruction_plane_contract`: 18/18 GREEN;
- production instruction status: GREEN;
- provider status: `dynamic=true`;
- auth status: `shadow_present=false`;
- production runtime health: `healthy`, restart count `0`.
