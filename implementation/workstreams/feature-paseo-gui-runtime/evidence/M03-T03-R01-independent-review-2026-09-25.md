# M03-T03 R01 — Independent implementation review

Date: 2026-09-25
Card: `M03-T03`
Attempt: `R01`
Verdict: **RED**

## Reviewed exact subject

- Review subject: `elmakus/pi-unraid@068ceec5545a96a924d00e091bbef76195b47afa:implementation/workstreams/feature-paseo-gui-runtime/results/M03-T03.md@d6ce8d2d5c28e105100a25ebfca711d432d483a5`
- Implementation commit named by the result: `3af85a170eb0f3274ea7321003680051450350dd`
- Acceptance surface: `implementation/workstreams/feature-paseo-gui-runtime/cards/M03-T03.md`
- Frozen predecessors:
  - `implementation/workstreams/feature-paseo-gui-runtime/results/M03-T01.md@16e5a14f1f0357b8af40fa23602c6d6c1da24724:1b157d85116b5a9dffab7df7766f62cc8a288f3e`
  - `implementation/workstreams/feature-paseo-gui-runtime/results/M03-T02.md@97e7833edaa55d54b35336a07c46bf261795fc46:a5c8a0c3a84b5c7f6da3d147896ee60995860800`

## Independence

This review context did not materially produce, reconcile, or repair the exact R01 subject.

## Independent checks

- Revalidated both predecessor result blobs exactly.
- Verified GitHub Actions run `36191535148` is `completed/success` on exact implementation SHA `3af85a170eb0f3274ea7321003680051450350dd`.
- Re-read the stable Card acceptance plus the accepted PGR requirements, authority-boundary ADR, Unraid-admin safety ADR and P2 M03 plan slice.
- Confirmed the host-control doctor itself is read-only: GraphQL uses only the INFO/DOCKER readback query and full SSH diagnosis uses only the fixed read-only probe; the doctor path does not call GraphQL mutation, gated SSH execution or the forced smoke-marker mutation.
- Confirmed bounded credential/identity fingerprints, machine-readable output, concise GREEN/WARN/RED summary, GraphQL-primary aggregation semantics and separation from PW Recovery / OR doctor authority.

## Blocking finding

The Card's Required tests/readback explicitly requires verification that GraphQL **healthy, unreachable, auth and protocol** cases map to bounded structured doctor status.

The exact M03-T03 doctor contract suite verifies the healthy path and one generic `HostControlError("graphql")` failure only. The pre-existing GraphQL contract suite likewise does not supply doctor-level unreachable/auth/protocol coverage. In addition, `graphql_check()` drops `HostControlError.details`; an HTTP 401/403 is therefore collapsed to the same generic `error = "http"` surface as other HTTP failures, so the doctor does not expose a bounded auth distinction/status.

This means the exact R01 subject does not satisfy the Card's required GraphQL failure-matrix verification and bounded structured auth diagnosis.

## Verdict

**RED** — bounded correction inside the accepted M03-T03 authority is required. Add doctor-level coverage for unreachable/auth/protocol cases and preserve a secret-safe bounded auth distinction/status without broadening scope or performing live mutation.
