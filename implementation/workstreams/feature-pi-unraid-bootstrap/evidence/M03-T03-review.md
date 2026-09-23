# M03-T03 independent review evidence

- Review owner: Task Board card `M03-T03`
- Review requirement: `REQUIRED`
- Reviewer: fresh normal ChatGPT session, independent of implementation subject
- Exact review subject: `906ba4020905981be75c1b44e23d7f0ef6589535`
- Verdict: **GREEN**
- Date: 2026-09-23
- Production mutation: **none**
- Secret handling: no real Codex-LB client key, pooled OAuth token, account identifier or private model transcript was read into or written by this review.

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M03-T03.md`
- `planning/MASTER_PLAN.md#M03 — Codex-LB-integrated on-Unraid acceptance and recoverable handoff`, especially M03-W2
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-001/002/004/005/011/022/023/024
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md`
- JIT OpenSpec `openspec/changes/m03-codex-lb-integration/`
- accepted and independently reviewed M03-T02 dependency result
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T03.md`

## Exact-subject review

The immutable subject `906ba4020905981be75c1b44e23d7f0ef6589535` was reviewed rather than the moving branch head.

Independent Git history inspection confirmed that the executable subject tested by implementation evidence, `c553746e425777a2ace3d9992125c5bd6a1b5cf6`, differs from the exact review subject only by OpenSpec task reconciliation and the implementation-evidence record. No executable source changed after the tested image was built.

Static review confirmed that:
- Compose uses a file-backed dedicated client secret and host-gateway route without placing the resolved key in service environment declarations;
- persistent provider configuration uses the generic `openai-responses` seam and a literal `${CODEX_LB_API_KEY}` reference;
- the managed launcher exposes the resolved key only to the Pi child process as allowed by the OpenSpec;
- compatible existing provider configuration and unrelated user configuration are preserved, while conflicting configuration is rejected without replacement;
- runtime/service health remains independent from provider health;
- no direct Pi OAuth fallback, pooled OAuth material, Docker socket, host-root/unrelated-appdata mount, inbound SSH service, Codex-LB appdata mount or workstation dependency is introduced.

## Independent disposable runtime verification

A fresh temporary checkout on Tower was detached at the exact review subject and the repository's M03-T03 verifier was rerun against the exact implementation image `sha256:b2eb64b04aedd6a6dfc1429f2016de95d1d4102be0727cd3f11f1c174c063ce3`.

The independent gate passed:
- fresh-home authenticated provider initialization;
- idempotent initialization and force-recreation persistence;
- populated-home preservation;
- missing and invalid credential failure separation without key leakage;
- unreachable endpoint classification while Pi runtime health remains GREEN;
- Compose/log/source redaction checks;
- real packaged `pi --list-models` visibility;
- affected M01 base/Compose/Git foundations;
- M02 stable runtime selector/LKG behavior using stable Pi `0.87.1`;
- M02 managed lifecycle and bounded shutdown.

Terminal marker: `M03_T03_INDEPENDENT_GATE=GREEN`, exit code 0.

Two additional independent edge checks also passed:
- an incompatible pre-existing `codex-lb` entry causes provider initialization to fail while leaving `models.json` byte-identical;
- the OpenSpec-supported raw one-line secret-file form is loaded correctly into the Pi child environment without persisting it.

No production Pi path/service, real production credential, Codex-LB production configuration or workstation state was mutated.

## Verdict

**GREEN.** The exact M03-T03 subject satisfies the Task Card acceptance surface and the JIT OpenSpec provider/secret/persistent-config contract. The security-sensitive secret boundary remains non-Git and redacted, existing user configuration is protected, provider failures stay distinct from Pi runtime health, and inherited M01/M02 guarantees remain intact on the independently rerun disposable gate.

Production secret placement, production deployment and the first real Codex-LB model interaction remain correctly deferred to M03-T04 and its explicit live-write authorization boundary.
