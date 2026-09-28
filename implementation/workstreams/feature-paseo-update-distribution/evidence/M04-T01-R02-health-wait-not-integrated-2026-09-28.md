# M04-T01-R02 — health-readiness repair not integrated

Date: 2026-09-28
Card: `M04-T01`
Attempt: `R02`

## Exact subject

- Result commit: `551acbc886c2f7f67243ccee361cb2b93cea230b`
- Result blob: `c2179793147d7b295cbd1524169aac814c10603e`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M04-T01.md`
- Implementation subject: `c09e0312df658d68a5e71437fe5f8d036c1fbf83`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M04-T01.md`

## Finding

The R01 correction added a bounded `wait_for_runtime()` helper and focused helper-level tests for `starting -> healthy` and terminal `unhealthy`.

However, the production validator path does not call that helper. After `docker run -d`, `validate()` still performs one immediate `docker inspect`, computes `health = State.Health.Status or State.Status`, and accepts only `healthy` or `running`. With the inherited Paseo healthcheck, a normal initial `State.Health.Status = "starting"` therefore still reaches the existing FAIL branch immediately.

The new transition test invokes `wait_for_runtime()` directly, so it proves the helper in isolation but does not prove that `validate()` uses it. The exact R01 defect consequently remains present on the real validation path despite the GREEN test summary.

## Required correction

Wire the bounded readiness helper into `validate()` after candidate launch and before runtime invariant acceptance, remove the obsolete one-shot health rejection path, and add an integration-level validator test whose mocked candidate inspect sequence is `starting -> healthy`. Re-run the Card-required targeted/full verification and reconcile a new immutable result before freezing a new review attempt.

## Verdict

**RED.**
