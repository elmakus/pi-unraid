# M01-T01 implementation evidence

Implementation subject: `elmakus/pi-unraid@38e03a0eb163d940dac1cf06a7d900de45fb15d9`

## Pi 0.87.1 contract readback

Read-only inspection of the accepted Pi 0.87.1 installation confirmed:
- `ProviderConfigInput.refreshModels(context: RefreshModelsContext)`;
- typed API-key credentials on `RefreshModelsContext.credential`;
- provider-scoped `stored` plus generation-checked `publish()`;
- `ModelRegistry.refresh({ providers: [...], allowNetwork: true })`;
- `session_start` and `session_shutdown` extension lifecycle events;
- Pi conservative custom-model defaults: reasoning off, text-only, zero unknown cost, 128000 context and 16384 max output.

## Exact-subject tests

The exact GitHub commit above was fetched back to Tower and passed:
- 11 Python instruction-plane/contract tests;
- the Node dynamic-catalog core suite;
- `git diff --check`.

Disposable Pi 0.87.1 smoke also loaded the TypeScript extension through the normal extension loader. A disposable RPC process using a local authenticated catalog fixture and a 1-second test refresh interval returned `dynamic-one` and `dynamic-two` from `get_available_models` in the same running process after refresh, replacing the static fallback. No production HOME or production container state was mutated.

## Reconciliation behavior

The repository-managed reconciler validates the existing Codex-LB transport/auth-reference contract, removes only the managed static model list, preserves unrelated configuration semantically, snapshots exact prior bytes and mode for rollback, refuses destructive rollback after intervening edits, and fails closed on conflicting configuration. M01-T01 did not apply that migration to production.
