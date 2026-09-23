# M02-T03 independent review evidence

- Review owner: Task Board card `M02-T03`
- Review requirement: `REQUIRED`
- Reviewer: fresh normal ChatGPT session, independent of implementation subject
- Exact review subject: `f45bac572f139fa02dd7ddd04592409023501cfa`
- Verdict: **RED**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M02-T03.md`
- `planning/MASTER_PLAN.md#M02 — Recoverable runtime and deployment lifecycle`, especially M02-W3 and the integrated checkpoint
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-014/015/017/020/021 plus global rollback/data-integrity invariants
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `openspec/changes/m02-runtime-lifecycle/design.md`
- `openspec/changes/m02-runtime-lifecycle/specs/runtime-lifecycle/spec.md`
- `research/PI_UNRAID_M02_LIFECYCLE_FACTS_R1.md`
- terminal GREEN dependencies M02-T01/T02 and M01 handoff/evidence where inherited by the Card

## Independent inspection

- Recovered the immutable subject from the manifest-bound Task Board and validated the selected workstream/branch binding.
- Inspected the exact subject implementation and evidence, including `scripts/update.sh`, `scripts/verify-update-rollback.sh`, `docs/OPERATOR.md` and the M02 OpenSpec update/rollback contract.
- Independent Tower source checks at the exact subject: `git diff <subject>^ <subject> --check`, `bash -n scripts/update.sh`, and `bash -n scripts/verify-update-rollback.sh` were GREEN.
- An independent detached checkout of the exact immutable subject could not run the integrated verifier: `verify-update-rollback.sh` aborted when its internal clones tried to check out the hard-coded local branch `feat/pi-unraid-bootstrap`. This is source-controlled verifier behavior, not an external credential/runtime blocker.

## Blocking findings

### R1 — rollback snapshots the active tag, not the actually deployed known-working image

`snapshot_pre_update()` records `docker image inspect "$ACTIVE_TAG"` as `pre-image-id`. It never resolves the current Compose service container or proves that the tag points to the image actually running as the current healthy deployment.

The accepted Card/OpenSpec require the **current deployed image identity** / **currently deployed known-working image** to be retained before cutover. A mutable tag can diverge from a still-running container image after an out-of-band build/tag operation. In that state the transaction records the wrong image and rollback can replace the genuinely working deployment with an image that was never the deployed known-working subject.

This is a bounded implementation/test correction: derive the pre-update image identity from the current service container (with current health/readback sufficient to call it known-working), then retain that exact image ID. Add a disposable fixture where the active tag deliberately differs from the running container and prove rollback preserves/restores the running known-working image.

### R2 — post-cutover runtime readback failure exits without automatic rollback

After candidate cutover, `continue_update()` rolls back only when `wait_healthy` fails. Once health becomes GREEN, `record_runtime` runs outside the rollback branch under `set -e`.

Therefore a runtime identity/readback failure after cutover exits the updater with the candidate still active and leaves the transaction short of `healthy`, instead of restoring the previous deployment. The accepted design explicitly makes success depend on **healthy/readback** and requires failure after cutover to restore the previous image/config and verify recovery.

This is a bounded implementation/test correction: treat health plus runtime readback as one cutover acceptance gate and invoke the existing automatic rollback path when either half fails. Add a deterministic post-health readback failure injection that proves the prior image/config is restored.

### R3 — integrated M02-T03 verifier is branch-name-dependent rather than immutable-subject reproducible

`scripts/verify-update-rollback.sh` hard-codes `feat/pi-unraid-bootstrap` in its internal checkout/upstream setup. From a normal detached checkout of exact review subject `f45bac572f139fa02dd7ddd04592409023501cfa`, its disposable bare clone does not contain that local branch, so the verifier aborts before exercising M02-T03.

The Card requires integrated checkpoint scenarios as durable evidence. A verifier whose success depends on the implementation branch continuing to exist is not durable across independent exact-subject review or later branch cleanup/integration.

This is a bounded test correction: create a synthetic disposable update branch from the verifier's current `HEAD` inside the temporary remote/clone topology and use that branch throughout the fixture, with no dependency on the repository workstream branch name.

## Verdict

**RED** — exact subject `f45bac572f139fa02dd7ddd04592409023501cfa` does not yet satisfy the complete M02-T03 rollback/readback and durable-verification acceptance surface. All three findings are bounded L1/L2 implementation/test corrections inside existing accepted authority; no Planning, Definition or new user decision is required.
