# M04-T01-R01 — health readiness race

Date: 2026-09-28
Card: `M04-T01`
Attempt: `R01`

## Exact subject

- Result commit: `61e4054ac3d5fde79f98442ae09575ba84a49bcc`
- Result blob: `4bf3c8266f2409ba0cc870bace0e294178129316`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M04-T01.md`
- Implementation subject: `6bec81ca3317bb82af3424c98a9692efe2b542b8`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M04-T01.md`

## Finding

The immutable-digest admission and isolation boundary are materially aligned with the Card: the candidate is launched on validator-owned state and network surfaces without the production Docker socket, host-control credentials, Codex-LB secret, GitHub token, or production state mounts.

However, the runtime-readiness implementation is not reliable for the exact production image contract. The child Dockerfile explicitly inherits Paseo's parent-image healthcheck. Immediately after `docker run -d`, the validator performs one `docker inspect` and computes:

`health = State.Health.Status or State.Status`

It then accepts only `healthy` or `running`. When a healthcheck exists, a normally starting container reports `State.Health.Status = "starting"`; that non-empty value masks `State.Status = "running"`, so the validator immediately returns FAIL instead of waiting boundedly for the inherited healthcheck to become healthy.

The focused PASS unit test does not cover this production-shaped path: its mocked inspect payload omits `State.Health` and supplies only `State.Status = "running"`. Therefore the test suite can be GREEN while a valid exact candidate is rejected on Tower.

## Required correction

Implement a bounded readiness wait/poll for the inherited container healthcheck (with deterministic timeout/error classification), retain the no-healthcheck fallback only where explicitly valid, and add focused tests covering at least `starting -> healthy` and terminal unhealthy/timeout behavior. Re-run the Card-required targeted/full verification before reconciling a new result and review attempt.

## Verdict

**RED.**
