# M01-T02 disposable live-RPC acceptance evidence

Acceptance subject:
- reviewed M01-T01 implementation: `elmakus/pi-unraid@2c38c280f1f7a78045ead22b4aa70f21a6992680`
- exact dependency result: `elmakus/pi-unraid@bedf22af3a27fc823b0b5bf7001c71c3822a1629:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M01-T01.md@0ec960b8eabe20d4c955eca01aa1aa2805aae13c`
- disposable runtime image: `pi-unraid:paseo-b4e0c1e7c276`
- Pi runtime: `0.87.1`

## Disposable setup

Tower used only a temporary directory under `/tmp`. The repository was checked out at the exact M01-T01 implementation subject and that subject's `config/pi-agent` tree was copied into a temporary HOME. A temporary provider bootstrap preserved `api: openai-responses`, the `${CODEX_LB_API_KEY}` reference, and a local fixture base URL.

A local authenticated fixture served `GET /v1/models`. Its random credential existed only in process environment. Pi ran with `docker run --rm`, the temporary HOME, host networking and `PI_CODEX_LB_MODEL_REFRESH_MS=1000`. Production HOME, Codex-LB and the production Paseo container/image were not targeted.

## RPC readback

Using Pi RPC `get_available_models`, `set_model` and `get_state`:

- initial catalog: `keep-model, remove-me`;
- same running process after add: `added-model, keep-model, remove-me`;
- selected model was set to `codex-lb/remove-me`;
- same running process after removing `remove-me`: `added-model, keep-model`;
- `get_state` still reported `codex-lb/remove-me`, so refresh did not auto-switch the selection;
- after the fixture returned HTTP 503, the available catalog remained `added-model, keep-model`;
- provider-scoped `~/.pi/agent/models-store.json` persisted `added-model, keep-model`;
- after the fixture server was stopped completely, a new Pi 0.87.1 RPC process using the same temporary HOME restored `added-model, keep-model` while discovery was unavailable;
- recursive scans of the temporary HOME before and after restart found no raw fixture credential.

All disposable processes and temporary test files were removed. Production `pi-unraid-paseo-1` read back healthy afterward.

## Verdict

M01-T02 acceptance: GREEN. The exact reviewed M01-T01 implementation satisfies the P1 live-RPC add/remove/failure/offline-restart and no-auto-switch contract on real Pi 0.87.1.
