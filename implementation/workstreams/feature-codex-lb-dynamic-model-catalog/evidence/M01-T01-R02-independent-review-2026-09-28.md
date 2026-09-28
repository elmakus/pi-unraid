# M01-T01 R02 independent review evidence

Reviewed subject:
- result blob: `elmakus/pi-unraid@45da0771dc8a882ec5f9986506da770f89fcfbfb:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M01-T01.md@afbe6fa30ea396552b0141b670af79f85c8d812c`
- implementation subject named by that result: `elmakus/pi-unraid@2d33e0d51ebe4f1df2089bfc5c9ca8b4c5696e7a`
- acceptance: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/cards/M01-T01.md`

Verdict: RED.

## Independent checks performed

The review inspected the exact frozen result, exact corrected extension/core/reconciler/tests, R01 findings, correction evidence, accepted CLDMC requirements, CLDMC-ADR-001, PIB-ADR-005 and Strategic Plan P1. The branch contains no implementation-code changes after the named implementation subject.

The R01 failure-preservation additions for timeout, invalid JSON and invalid catalog shape correctly assert that a stored valid catalog is not replaced or published on those failures. The extension still uses the supported provider-refresh seam, keeps `openai-responses`, does not call `setModel`, and does not hardcode Codex-LB model IDs.

## Blocking findings

### R02-F01 — two reconciler correction tests are false positives

The exact corrected Python contract tests build the invalid-base-URL and control-character fixtures with `json.dumps(...)+ "\\n"`. That appends the two literal characters backslash + `n`, not a newline. The resulting `models.json` is invalid JSON, so `parse_document()` raises before `valid_base_url()` or `valid_model_id()` is exercised.

The control-character test also assigns `"bad\\u0000id"`, which is a literal backslash-u sequence rather than an actual U+0000 character. Even with a valid JSON terminator, it would not prove rejection of the intended control character.

Therefore the correction evidence claim that the dynamic contract suite proves invalid-base-URL/control-character fail-closed behavior is not established.

### R02-F02 — reconciler baseUrl validation remains weaker than runtime bootstrap

`valid_base_url()` uses `urllib.parse.urlsplit` but only requires scheme `http|https`, non-empty `netloc`, no credentials/query/fragment and a path ending in `/v1`. It never requires a non-empty parsed hostname and never reads/validates `parsed.port`.

Consequently values such as `http://host.invalid:abc/v1`, `http://host.invalid:99999/v1`, or `http://:123/v1` can satisfy the reconciler predicate while the extension's `new URL(...)` bootstrap rejects them as invalid URLs. The reconciler can therefore still remove the static model list from configuration that the runtime extension will refuse to load.

This keeps R01-F01 materially open and violates the Card requirement that migration fail closed on invalid/conflicting config while preserving the accepted Codex-LB transport bootstrap.

## Required correction

1. Make reconciler URL validation match the runtime bootstrap for hostname and port validity, not only scheme/netloc/path shape.
2. Fix the tests to write valid JSON with a real newline and to exercise an actual control character plus invalid-host/invalid-port URL cases.
3. Re-run the focused contract suites and `git diff --check` on the exact corrected implementation subject.
4. Reconcile a new result subject and freeze a new independent review attempt. R01 and R02 remain immutable RED history.
