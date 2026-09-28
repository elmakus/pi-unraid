# M01-T01 R03 independent review evidence

Reviewed subject:
- result blob: `elmakus/pi-unraid@9c1c31cf5fa51f68235040e8fcc7a5212feca55a:implementation/workstreams/feature-codex-lb-dynamic-model-catalog/results/M01-T01.md@f9c201415f2f4693a8b9d5d3f20c876e752b4b3b`
- implementation subject named by that result: `elmakus/pi-unraid@9805d9b0c08465d5cbfbfe9f0f99a13a405ddaf9`
- acceptance: `implementation/workstreams/feature-codex-lb-dynamic-model-catalog/cards/M01-T01.md`

Verdict: RED.

## Independent checks performed

The review inspected the exact frozen result, exact R02 correction subject, full reconciler, dynamic extension/core, focused Python/Node contract tests, R01/R02 findings and correction evidence, accepted CLDMC requirements, CLDMC-ADR-001, PIB-ADR-005 and Strategic Plan P1.

The R02 fixture defects are corrected: the invalid-base-URL test now writes valid JSON, the model-ID test uses an actual U+0000 character, and malformed/out-of-range ports plus an empty hostname are exercised.

## Blocking finding

### R03-F01 — reconciler baseUrl validation still accepts authorities rejected by runtime bootstrap

The R02 correction adds `parsed.hostname`, `parsed.port`, raw-backslash and control-character checks, but the reconciler still validates with Python `urllib.parse.urlsplit` while the runtime extension validates with WHATWG `new URL(...)`.

There remain inputs for which `valid_base_url()` returns true even though `normalizeBaseUrl()` rejects the same configured value before provider registration. Examples include:

- `http://%5chost.invalid/v1`
- `http://%2fhost.invalid/v1`
- `http://example.com%00/v1`
- `http://[v1.fe80::]/v1`

For the percent-encoded authority examples, `urlsplit` leaves the encoded octets in `netloc/hostname`, so the current checks see a non-empty hostname, no raw backslash/control byte and no invalid port. Node's `new URL(...)` rejects those authorities. Python also accepts the IPvFuture-style bracketed authority above while Node's runtime URL parser rejects it.

Therefore the reconciler can still remove the static model list and establish rollback state for provider configuration that the extension will refuse to load. This keeps the fail-closed bootstrap-equivalence requirement materially open and violates the Card acceptance requirement that migration fail closed on invalid/conflicting configuration while preserving the accepted Codex-LB transport bootstrap.

## Required correction

1. Make reconciler authority validation a conservative subset of the runtime URL parser: reject percent-encoded/non-ASCII authorities and validate bracketed host literals as real IPv6 (or otherwise use an equivalently strict parser/contract).
2. Add focused regression cases for at least the percent-encoded authority and invalid bracketed-host classes so the reconciler path itself proves rejection before mutation.
3. Re-run the focused Python/Node suites and `git diff --check` on the exact corrected subject.
4. Reconcile a new result subject and freeze a fresh independent review attempt. R01-R03 remain immutable RED history.
