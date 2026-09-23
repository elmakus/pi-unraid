# M02 runtime lifecycle — proposal

Status: JIT execution contract for approved milestone M02
Date: 2026-09-23

## Why

M02 adds stateful behavior across the container runtime, native Pi launch path and host-operated deployment update/rollback path. The accepted requirements require latest-stable selection with LKG fallback, bounded graceful shutdown of exec-launched Pi, readable readiness/diagnostics and a separate previous-image rollback mechanism. Those contracts are sufficiently cross-cutting and failure-sensitive to freeze before coding.

## Authority

- `planning/MASTER_PLAN.md#M02 — Recoverable runtime and deployment lifecycle`
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-014/015/017/020/021 plus inherited persistence/data-integrity invariants
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `research/PI_UNRAID_M02_LIFECYCLE_FACTS_R1.md`
- accepted M01 handoff/evidence

## Change

Create one cohesive lifecycle contract covering:

1. persistent, staged stable-runtime selection with image seed and LKG fallback;
2. managed native Pi launch registration, service supervision, readiness and bounded planned shutdown;
3. one host update operation that keeps an external previous image/deployment candidate and can roll back without touching durable home/projects/worktrees.

## Non-goals

- live ChatGPT OAuth/provider validation;
- live GitHub credential/remote validation;
- changing the accepted home/projects/worktrees mount layout;
- Web UI, extensions, MCP or subagent installation;
- executing the production update/cutover against the live Unraid service during M02.

Those remain outside this change or are M03 obligations.
