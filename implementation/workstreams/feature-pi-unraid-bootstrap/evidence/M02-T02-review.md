# M02-T02 independent review evidence

- Review owner: Task Board card `M02-T02`
- Review requirement: `REQUIRED`
- Reviewer: fresh normal ChatGPT session, independent of implementation subject
- Exact review subject: `3ee4fd740bfa4afb1ec3f1fba5f4452624588d72`
- Verdict: **RED**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M02-T02.md`
- `planning/MASTER_PLAN.md#M02 — Recoverable runtime and deployment lifecycle`, especially §3.3 and M02-W2
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-005/017/021 plus inherited M01 persistence/security invariants
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `openspec/changes/m02-runtime-lifecycle/{design.md,specs/runtime-lifecycle/spec.md}`
- `research/PI_UNRAID_M02_LIFECYCLE_FACTS_R1.md`
- terminal GREEN dependency `M02-T01`

## Independent inspection

- Recovered the immutable subject from the manifest-bound Task Board and verified workstream/branch identity.
- Inspected the full T02 implementation delta relative to terminal M02-T01, including `Dockerfile`, `compose.yaml`, `scripts/pi-launcher.sh`, `scripts/pi-unraid-service` and `scripts/verify-managed-lifecycle.sh`.
- Confirmed PID/start-time/UID registration, stale-entry validation, shutdown admission locking, non-root PID1, current-start readiness marker handling, real packaged-Pi SIGTERM coverage, concurrent-registration coverage and bounded non-cooperative escalation are implemented coherently.
- Confirmed the reviewed image from implementation evidence remains present on Tower as `sha256:3ad9ef172eefd26be1a7a0ba139153478d943a129735d31bdf4a1df1750f696e`.
- On a disposable Tower `/tmp` home, the packaged Pi CLI independently exposed native session controls (`--session`, `--continue`, `--resume`) and an RPC `get_state` response identified its native session file as a `.jsonl` session path. No live home, credentials or production service were used.

## Blocking findings

### R1 — required native session/readability proof is absent

The Card's required checks explicitly require **fixture-home before/after state hashes plus a native session/readability probe**. The exact verifier instead:

- creates a hand-written `~/.pi/agent/sessions/m02-fixture/state.json`;
- hashes that arbitrary file before/after recreation;
- launches the only real packaged Pi shutdown test with `--no-session`;
- never opens the persisted fixture through Pi using `--session`, `--continue`, `--resume` or an equivalent native SessionManager/readability path.

Therefore the test proves generic bind persistence, but it does not prove that already-persisted native Pi session state remains readable/resumable after planned stop/recreation. This leaves the Card acceptance clause for synthetic/native session readability and the applicable PIB-REQ-005/021 / Master Plan §3.3 resumability obligation unverified.

A bounded correction can use a real native-format synthetic session fixture and a provider-free native readability/resume probe. M02 does not require live OAuth for this proof.

### R2 — configurable inner grace can violate the mandatory outer > inner invariant

The exact `compose.yaml` fixes Compose `stop_grace_period` at 20 s but exposes `PI_UNRAID_MANAGED_GRACE_SECONDS` as an unconstrained deployment interpolation. `pi-unraid-service` accepts any non-negative integer.

The OpenSpec requires the outer Compose grace to exceed the internal Pi grace; the Card records 12 s internal / 20 s outer and permits **shorter fixture overrides**. With the current source, an operator can set the inner grace to 20 s or greater (or to 0), violating that shutdown contract and allowing Docker's outer kill boundary to pre-empt the intended supervisor sequence.

No accepted requirement justifies arbitrary production configurability here. A bounded correction should make the production relation fail-safe, for example by keeping the production inner grace fixed below the outer bound and applying shorter overrides only in disposable fixture Compose, or by otherwise enforcing the invariant.

## Verdict

**RED** — exact subject `3ee4fd740bfa4afb1ec3f1fba5f4452624588d72` does not yet satisfy the complete M02-T02 acceptance surface. The two defects are bounded L1/L2 implementation/test corrections inside existing accepted authority; no Planning, Definition or new user decision is required.
