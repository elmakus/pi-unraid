# M03-T01 scope reconciliation evidence

Verdict: GREEN.

Scope subject:
- workstream: `feature-codex-lb-dynamic-model-catalog`
- accepted plan: `planning/CODEX_LB_DYNAMIC_MODEL_CATALOG_P1.md` (`P1`)
- integration target at reconciliation: `origin/main@fc7a470a7330839cbaf8eaf0c2914323981d6901`
- workstream creation base: `fc7a470a7330839cbaf8eaf0c2914323981d6901`

## Exact dependency and review reconciliation

All four dependency result blobs were re-derived from their immutable commits and match the Task Board bindings exactly:
- M01-T01: `bedf22af3a27fc823b0b5bf7001c71c3822a1629:0ec960b8eabe20d4c955eca01aa1aa2805aae13c`; terminal required review `M01-T01-R04` is GREEN.
- M01-T02: `c8160b88de6ebe506e4328810d325938659934e2:96f78959ab95d6ac18bd7fc71a670383b1481a59`; terminal required review `M01-T02-R02` is GREEN.
- M02-T01: `ad5ca62c34673ca4ea088a56c15e2697b0eb3c96:4f10d2754a9722e0f38b69676fef5eacd8f0fb0f`; terminal required review `M02-T01-R01` is GREEN.
- M02-T02: `f7bff14d7813cec30051e85c0434156f5d9e85df:082e2c41d532462bdab5b00421bd93c72a118fe2`; terminal required review `M02-T02-R01` is GREEN.

Earlier RED attempts remain immutable history and are superseded only by later exact terminal GREEN attempts for the accepted corrected subjects.

## Requirement reconciliation

| Requirement | Durable proof | Status |
|---|---|---|
| CLDMC-REQ-001 | M01-T01 reviewed provider extension/core plus M01-T02 live RPC proves authenticated Codex-LB catalog discovery with no hardcoded accepted model list. | GREEN |
| CLDMC-REQ-002 | M01-T02 same-process add-ID proof: a newly exposed fixture ID became available without repository edit, manual `models.json` change or runtime restart. | GREEN |
| CLDMC-REQ-003 | M01-T02 same-process remove-ID proof: removed catalog ID disappeared after bounded refresh without unrelated restart. | GREEN |
| CLDMC-REQ-004 | M01-T01 bounded lifecycle refresh implementation plus M01-T02 same-running-RPC add/remove convergence. | GREEN |
| CLDMC-REQ-005 | M01-T01 failure semantics plus M01-T02 witnessed HTTP 503 preservation, persisted provider-scoped LKG and offline restart restoration. | GREEN |
| CLDMC-REQ-006 | M01-T01 provider contract plus M02-T02 production readback preserves `api: openai-responses`, Codex-LB base URL and `${CODEX_LB_API_KEY}` reference. | GREEN |
| CLDMC-REQ-007 | M02-T01/M02-T02 auth-shadow reconciliation preserves Codex-LB ownership of OAuth/account routing; production auth shadow is absent and dedicated credential remains external to Pi HOME/Git evidence. | GREEN |
| CLDMC-REQ-008 | Extension is repository-managed under `config/pi-agent`, delivered through the accepted instruction-plane transaction; M02-T02 current status remains `in_sync=true`. | GREEN |
| CLDMC-REQ-009 | M01-T01 reviewed parser/metadata contract validates IDs and uses conservative capability defaults; no capability inference from model ID is introduced. | GREEN |
| CLDMC-REQ-010 | M01-T01 exposes bounded configurable refresh cadence; M01-T02 uses accelerated test cadence rather than real production waiting. | GREEN |
| CLDMC-REQ-011 | M01-T02 independently proves initial/add/remove/failure behavior in one live RPC; M02-T01 proves staged real-Pi/LKG migration; M02-T02 proves current production live-catalog equality across real Codex-LB, fresh production RPC and LKG. | GREEN |
| CLDMC-REQ-012 | Focused contract asserts `setModel` is absent from extension/core, and M01-T02 proves an explicitly selected model remains selected even after that ID leaves availability. | GREEN |

No accepted requirement remains unresolved.

## Independent execution checks for this Card

Commands/readback performed without replaying the one-shot production activation:

```sh
python3 -m unittest tests.test_codex_lb_auth_shadow_contract tests.test_codex_lb_dynamic_model_catalog_contract tests.test_pi_instruction_plane_contract
node tests/codex_lb_dynamic_model_catalog_core_test.mjs
git diff --check fc7a470a7330839cbaf8eaf0c2914323981d6901..HEAD
```

Results:
- focused Python contracts: 18/18 GREEN;
- Node dynamic-catalog core suite: GREEN;
- branch diff check: GREEN;
- the only `set_model` occurrence in the searched implementation/test surface is the deliberate M01-T02 fixture selection used to prove selected-model stability; the contract test independently asserts no `setModel` call exists in extension/core.

## Current non-mutating production readback

- `pi-unraid-paseo-1`: running, `healthy`, start time `2026-09-28T09:16:28.292365808Z`, restart count `0`;
- instruction plane: `in_sync=true`, source digest `sha256:00405ab148b91d73c7d38c131a8a47d228f189d33da8bbd51d537c844e7c8f42`;
- provider config: `dynamic=true`, mode `0600`, models hash `b91fae25b9c91515fcfda7769daac14a7c176d2fd2a41e4e766723c4bfdeee37`, rollback available;
- auth store: mode `0600`, auth hash `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`, rollback available, `shadow_present=false`;
- instruction/provider/auth rollback-anchor directories remain present, mode `700`, owner `99:100`.

No production write, container restart, image mutation, Codex-LB service mutation or OAuth/account-routing mutation was performed by M03-T01.

## Scope and integration readiness

`origin/main` is still exactly the workstream creation base `fc7a470a7330839cbaf8eaf0c2914323981d6901`, so there is currently no target drift to reconcile. A local merge-tree check of current `origin/main` with the workstream branch is clean. This is only integration-readiness evidence; Close must still refresh target truth and affected compatibility immediately before final integration.

The complete workstream delta from the creation base contains no path belonging to the separate `feature-paseo-update-distribution` package/scope. No automatic model-selection/failover implementation is introduced.

Residual operational dependency remains the already-accepted external Codex-LB availability boundary. Transient catalog failures preserve the current/last-known-good catalog by reviewed contract; this is not an unresolved scope gap.

M03-T01 is ready for the required independent final review before Close/integration.
