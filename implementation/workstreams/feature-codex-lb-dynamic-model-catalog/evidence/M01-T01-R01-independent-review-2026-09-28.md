# M01-T01 R01 independent review evidence

Reviewed subject:
- result blob: `elmakus/pi-unraid@c71284052cbbb492a3ce19e3384c4b64388a8e34:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M01-T01.md@12f4ac9605be8c0ba4fcbaaa118179d7c73c6a74`
- implementation subject named by that result: `elmakus/pi-unraid@38e03a0eb163d940dac1cf06a7d900de45fb15d9`
- acceptance: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/cards/M01-T01.md`

Verdict: RED.

## Independent checks performed

The review read the exact frozen result, exact implementation files, accepted requirements, CLDMC-ADR-001, PIB-ADR-005 and Strategic Plan P1. It also independently inspected the Pi 0.87.1 provider-extension/model-refresh contracts for `RefreshModelsContext`, `registerProvider` and extension `refreshModels`.

The implementation correctly uses the supported extension/provider refresh seam, preserves the generic `openai-responses` transport, consumes the Pi-resolved credential, suppresses overlapping timer refreshes, avoids `setModel`, and keeps diagnostics free of secret material.

## Blocking findings

### R01-F01 — provider-config reconciler does not fully fail closed on invalid baseUrl

`scripts/reconcile-codex-lb-provider-config.py::validate_provider` accepts any string whose trimmed trailing slash form ends in `/v1`. It does not require HTTP(S), reject embedded credentials, or otherwise enforce the same baseUrl contract used by the extension's `normalizeBaseUrl`.

Examples such as `ftp://host/v1` or `not-a-url/v1` therefore pass reconciliation validation. `migrate()` can then remove the static model list and rewrite the file even though the resulting provider bootstrap is invalid and the extension will reject it later.

This violates the Card acceptance requirement that the reconciler fail closed on invalid/conflicting config and preserve the accepted Codex-LB transport contract.

The static-model ID validation is also weaker than the extension validator because it rejects whitespace but not all control characters. Validation should be aligned so the reconciler never mutates config that the runtime extension will reject.

### R01-F02 — required failure-preservation tests are incomplete

The Card explicitly requires focused contract/unit proof for timeout, authentication, invalid JSON and invalid-shape failure preservation.

The exact implementation test suite exercises:
- malformed/empty IDs through `parseCatalog`;
- one 401 authentication rejection;
- cache-only restore;
- overlap suppression and timer cleanup.

It does not exercise a timed-out discovery request, invalid JSON through `refreshModels`, or invalid catalog shape through the full refresh path while asserting the previously stored catalog is preserved and no publish occurs.

The implementation paths appear designed to preserve prior state by throwing before publication, but the required test/readback obligation is not satisfied by the frozen evidence as written.

## Required correction

1. Make reconciler validation at least as strict as the extension bootstrap for baseUrl and model IDs.
2. Add focused tests proving timeout, invalid JSON and invalid-shape refresh failures preserve the prior stored catalog and do not publish replacement state.
3. Re-run the exact focused suites and record a new semantic result subject.
4. Freeze a new independent review attempt; R01 remains immutable RED history.
