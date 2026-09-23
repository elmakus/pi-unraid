# M02-T02 independent re-review evidence

- Review owner: Task Board card `M02-T02`
- Review requirement: `REQUIRED`
- Reviewer: fresh normal ChatGPT session, independent of corrected implementation subject
- Exact review subject: `7152b99f7e4844d3a2328aeffc0a0f4d099891c0`
- Prior RED subject: `3ee4fd740bfa4afb1ec3f1fba5f4452624588d72`
- Prior RED evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M02-T02-review.md`
- Verdict: **GREEN**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M02-T02.md`
- `planning/MASTER_PLAN.md#M02 — Recoverable runtime and deployment lifecycle`, especially M02-W2
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-005/017/021 plus inherited M01 persistence/security invariants
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `openspec/changes/m02-runtime-lifecycle/design.md`
- `openspec/changes/m02-runtime-lifecycle/specs/runtime-lifecycle/spec.md`
- `research/PI_UNRAID_M02_LIFECYCLE_FACTS_R1.md`
- terminal GREEN dependency `M02-T01`

## Independent inspection

- Recovered the immutable corrected subject from the manifest-bound Task Board and validated workstream/branch identity.
- Inspected the corrected subject and full relevant source surface: `compose.yaml`, `Dockerfile`, `scripts/pi-launcher.sh`, `scripts/pi-unraid-service`, and `scripts/verify-managed-lifecycle.sh`.
- Confirmed production Compose now fixes the accepted 12 s internal / 20 s outer shutdown relationship by omitting the operator-facing `PI_UNRAID_MANAGED_GRACE_SECONDS` interpolation, while disposable fixture Compose supplies the shorter explicit test override.
- Confirmed the lifecycle verifier now creates a native Pi JSONL session through packaged Pi RPC, validates its native `sessionId`, opens that exact session through the supported managed TUI path, hashes the native file only after stabilization, verifies it remains unchanged across planned stop/removal/recreation, and reopens the same native session with the same path and `sessionId`.
- Rechecked the existing process lifecycle implementation against the Card/OpenSpec: non-root PID1, PID/start-time/UID validation, shutdown admission closure, stale-entry pruning, SIGTERM fan-out, bounded grace, SIGKILL only after grace, current-start readiness, and bounded Docker log rotation remain coherent.

## Independent Tower verification

A detached disposable worktree was created at exact subject `7152b99f7e4844d3a2328aeffc0a0f4d099891c0`. No live project paths or credentials were mounted.

Checks:

- `git diff --check` — GREEN
- `bash -n scripts/verify-managed-lifecycle.sh` — GREEN
- `bash -n scripts/pi-unraid-service` — GREEN
- `sh -n scripts/pi-launcher.sh` — GREEN
- reviewed image ID: `sha256:3ad9ef172eefd26be1a7a0ba139153478d943a129735d31bdf4a1df1750f696e`
- `bash scripts/verify-managed-lifecycle.sh pi-unraid:m02-t02-r2` — GREEN
- independent escalation timing: `3211 ms` with fixture grace `3 s`

The runtime verifier independently exercised the real packaged-Pi planned SIGTERM path, native session preservation/reopen, concurrent registrations, stale PID rejection, non-cooperative bounded escalation, and unhealthy readiness when no runtime is available.

## Prior RED closure

### R1 — native persisted-session/resumability proof

**Closed.** The corrected verifier uses Pi's native session format and native SessionManager/RPC/TUI paths rather than an arbitrary fixture file, and independently proves the same persisted native session remains readable/reopenable after recreation.

### R2 — outer grace must exceed production inner grace

**Closed.** Production Compose no longer exposes an ambient/operator inner-grace override. The production source therefore retains service default 12 s with fixed Compose outer 20 s; only the disposable fixture explicitly overrides the inner grace shorter for test execution.

## Findings

No blocking findings.

## Verdict

**GREEN** — exact subject `7152b99f7e4844d3a2328aeffc0a0f4d099891c0` satisfies the M02-T02 Card acceptance and applicable authority/OpenSpec surface. The prior RED evidence remains preserved as historical review evidence.
