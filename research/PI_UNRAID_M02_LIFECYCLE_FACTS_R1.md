# Research — M02 runtime lifecycle facts

Date: `2026-09-23`

## Durable continuation metadata

Research ID: `pi-unraid-m02-lifecycle-facts-r1`
Status: `consumed`
Origin role: `execution_prep`
Origin subject: `M02`
Return target: `execution_prep:M02`
Return reconciliation: `applied`
Return reconciliation result: `openspec/changes/m02-runtime-lifecycle/proposal.md@754774d07619f7272a58db8febaf20c19c4404a6; openspec/changes/m02-runtime-lifecycle/specs/runtime-lifecycle/spec.md@9b2fe0ed1c3f1dfe5d0ac1e4efaf0a467a669a2b; openspec/changes/m02-runtime-lifecycle/design.md@77f7af02061703e434c0587a4123590412107ab3; implementation/workstreams/feature-pi-unraid-bootstrap/cards/M02-T01.md@eadaeb00e115166e57a91ae71f182b688391e97e; implementation/workstreams/feature-pi-unraid-bootstrap/cards/M02-T02.md@2e71e1742e44dabb6981be56f84f645762a976e2; implementation/workstreams/feature-pi-unraid-bootstrap/cards/M02-T03.md@f0ccc3638573e4a1db75c28d281a2b3e4cf37207; implementation/workstreams/feature-pi-unraid-bootstrap/TASK_BOARD.yaml@3de99543120cae68d8c82713c813e27ccd511fb3`

## Research question

Refresh the exact current Pi/Docker lifecycle facts needed to contract `M02 — Recoverable runtime and deployment lifecycle` without reopening accepted product intent.

## Authority / predecessor inputs

- `planning/MASTER_PLAN.md#M02 — Recoverable runtime and deployment lifecycle`
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-014/015/017/020/021 and integrated M01 invariants
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `implementation/workstreams/feature-pi-unraid-bootstrap/handoffs/M01_HANDOFF.md`
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-acceptance.md`

## Sources / evidence

Primary/upstream:

- Pi current documentation:
  - https://pi.dev/docs/latest
  - https://pi.dev/docs/latest/sessions
  - https://pi.dev/docs/latest/cli
  - https://pi.dev/docs/latest/containerization
- Pi upstream source, current main indexed at commit `898ab804050730e9dcefb4443875d5a932aa6a32`:
  - `packages/coding-agent/package.json`
  - `packages/coding-agent/src/modes/interactive/interactive-mode.ts`
  - `packages/coding-agent/src/modes/rpc/rpc-types.ts`
  - `packages/coding-agent/src/modes/rpc/rpc-mode.ts`
  - `scripts/profile-coding-agent-node.mjs`
- Pi upstream lifecycle prior art:
  - https://github.com/earendil-works/pi/issues/5080
  - https://github.com/earendil-works/pi/issues/5724
  - https://github.com/earendil-works/pi/issues/9352
- Docker current documentation:
  - https://docs.docker.com/reference/compose-file/services/#stop_grace_period
  - https://docs.docker.com/reference/cli/docker/container/stop/
  - https://docs.docker.com/reference/cli/docker/container/exec/
  - https://docs.docker.com/reference/cli/docker/compose/up/
  - https://docs.docker.com/reference/dockerfile/
- npm current documentation:
  - https://docs.npmjs.com/files/package.json/#engines
  - https://docs.npmjs.com/using-npm/config/#engine-strict

Current disposable Tower readback on 2026-09-23:

```json
{
  "dist-tags": {
    "legacy-node20": "0.74.2",
    "latest": "0.87.1"
  },
  "version": "0.87.1",
  "engines": {
    "node": ">=22.19.0"
  }
}
```

The command was an isolated `npm view @earendil-works/pi-coding-agent dist-tags version engines --json` against the existing `pi-unraid:local` image. No persistent project/user state was mounted.

## Verified findings

### 1. Current stable admission facts

- The current npm `latest` dist-tag is `0.87.1`; upstream package/change-log state also identifies 0.87.1 as the 2026-09-22 release.
- Current package engine requirement is Node `>=22.19.0`. M01's Node 24 base satisfies it.
- Pi's current official installation still uses `npm install -g --ignore-scripts @earendil-works/pi-coding-agent`; Pi explicitly documents that normal npm installs do not require dependency lifecycle scripts.
- npm's `engines` declaration is advisory by default; `engine-strict=true` is therefore an appropriate installation-time compatibility guard when staging a candidate.
- The production selector must still reject a prerelease-shaped version even if a future registry mistake points `latest` at one. ADR-003 requires stable-only behavior; do not infer stability solely from the dist-tag name.

### 2. Pi has a real startup/readiness probe that does not require a provider request

- RPC mode accepts `{"type":"get_state"}` and returns a typed `get_state` response.
- Upstream's own `scripts/profile-coding-agent-node.mjs` uses receipt of a `get_state` response as the point at which Pi is ready for its startup benchmark.
- This is materially stronger than only checking `pi --version`, remains headless/non-interactive, and does not require sending a model prompt or exposing an OAuth credential.
- M02 can therefore validate a staged candidate by launching its exact binary in RPC/no-session mode, sending `get_state`, requiring a valid response within a bounded timeout, then closing it cleanly.

### 3. Planned SIGTERM is a supported graceful Pi shutdown path in current source

- Current interactive-mode source registers `SIGTERM` and, on Linux/macOS, `SIGHUP`.
- Signal-triggered shutdown calls runtime disposal first, including `session_shutdown` extension cleanup, drains terminal input with a bounded internal drain, stops the TUI and exits.
- This behavior is significant because older releases had concrete SIGTERM/SIGHUP cleanup defects (#5080 and #5724); current 0.87.1-era source contains the corrected path.
- A separate upstream report (#9352, 0.85.1) shows that a dead PTY can still fail through a stdin-EIO crash path. M02 must therefore test and claim **planned SIGTERM shutdown**, not claim that every arbitrary terminal-disappearance failure is graceful.

### 4. Pi's native session state is already persistent/resumable

- Pi saves sessions automatically unless `--no-session` is used.
- Default sessions are under `~/.pi/agent/sessions/`, grouped by working directory.
- `pi --continue` resumes the most recent session for the current working directory and `--resume` opens the picker.
- M01 already persists the whole service-user home, so M02 does not need a parallel session database.
- The shutdown contract should only claim preservation of state already committed by Pi. It must not claim that an unpersisted/in-flight model/tool operation survives forced termination.

### 5. Docker stop semantics require an explicit propagation seam for exec-launched Pi

- Docker `stop` sends the configured stop signal to the container's **main process**, defaulting to `SIGTERM`, and sends `SIGKILL` after the timeout.
- Compose `stop_grace_period` controls this outer wait and defaults to 10 seconds when unset.
- `docker exec` starts an additional command that exists only while the primary process exists; Docker's stop contract does not promise to deliver the primary stop signal to each exec-launched process.
- The current M01 service is PID1 `sleep infinity` after the entrypoint drops privileges. Therefore a Compose timeout alone cannot satisfy M02's requirement to give active native Pi exec sessions a graceful-stop opportunity.
- M02 needs a normal-service PID1 supervisor running as the service user plus a bounded registry/discovery mechanism for Pi processes launched through the supported operator entry. On service SIGTERM it should:
  1. stop admitting new managed Pi launches;
  2. send SIGTERM to every still-valid registered Pi PID;
  3. wait a bounded internal grace period;
  4. SIGKILL only remaining registered/non-cooperative fixture processes;
  5. stop the keepalive child and exit before Compose's larger outer grace period.
- PID registration must validate PID identity/start-time (or equivalent) before signaling so stale files cannot target a reused PID.
- An exec-form image entrypoint remains required; shell-form entrypoints can swallow signals.

### 6. Runtime LKG can live under persistent home without replacing the only working copy

ADR-003 does not prescribe the slot format. Current facts support a bounded implementation inside persistent `/home/pi`:

- keep the image's pinned Pi seed as an immutable offline-compatible fallback;
- install downloaded versions into versioned persistent-home slots rather than overwriting the image seed or active slot;
- serialize startup/update mutation with a crash-releasing lock (for example `flock`);
- stage into a temporary slot, enforce engine compatibility, then run the RPC `get_state` probe;
- only after a successful probe atomically publish the candidate as active/LKG;
- preserve the previous active/LKG pointer until the new candidate is proven;
- persist a rejected-version/failure marker so the same broken newest version is not immediately selected again on a restart loop;
- distinguish an unavailable registry/network check from a proven-bad candidate: offline/transient lookup falls back for this start, whereas failed install/probe can be subject to a cooldown or explicit retry;
- every startup must revalidate that the selected persistent runtime is compatible with the current image/Node; image rollback can always fall back to that image's seed if a newer persistent slot is incompatible.

These are delegated L1/L2 mechanics consistent with ADR-003, not new product decisions.

### 7. Current service needs a health/readiness state, not only a running PID1

- The M01 container can be running while no dynamically selected Pi runtime has been proven.
- M02's “no stale success” acceptance is best represented by atomically written non-secret runtime state plus a Compose healthcheck/readiness command.
- Healthy should mean that a viable exact runtime selection exists for the current image and the current startup reconciliation completed.
- If no active/LKG/seed candidate can pass compatibility/readiness, the service may remain up for operator recovery but must be visibly unhealthy/unavailable; it must not publish a stale previous “success” marker.
- Existing Docker `json-file` rotation from M01 already satisfies bounded container log growth; M02 only needs concise lifecycle diagnostics/state and must not create an unbounded second log.

### 8. Image/deployment rollback is distinct from runtime LKG and is safely host-operated

- The current Compose service uses mutable local tag `pi-unraid:local`. A rebuild can move that tag and leave the previous image unreferenced unless the host operation retains it deliberately.
- Before changing the deployed tag/config, the update path can preserve the currently deployed image ID under a dedicated previous/rollback tag and snapshot the rendered deployment configuration as external host-side rollback state.
- Build/verify the new image under a separate candidate tag first; only a verified candidate should replace `pi-unraid:local`.
- Compose recreates a service when its image/config changes while preserving bind-mounted host data. The accepted `/home/pi`, `/projects` and `/worktrees` binds therefore remain independent of image replacement.
- If candidate deployment/readiness fails, the host can restore the previous image tag plus previous rendered configuration and recreate the service without touching those bind sources.
- Docker's Swarm-oriented `deploy.rollback_config` is not the right primitive for this plain Compose deployment; the project-owned host script should own explicit candidate/previous tags and readback.
- No Docker socket needs to enter the container. The update/rollback operation remains a host command.

### 9. Safe pre-M03 fixture boundary

M02 can verify without live OAuth/GitHub credentials or the live Unraid service:

- version/engine admission and stable-only rejection;
- staged-install failure and startup-probe failure preserving LKG;
- offline lookup using LKG/seed;
- interrupted/stale mutation recovery and two overlapping selector/update attempts;
- persistent slot/state survival across container recreation;
- service health not reporting stale success;
- one or more registered exec-launched Pi processes receiving planned SIGTERM;
- non-cooperative registered process bounded escalation;
- retained previous image/config rollback in a disposable Compose project using `/tmp` binds;
- preservation of synthetic session/native-state files across runtime/image rollback.

M03 still owns:

- real ChatGPT OAuth persistence/readback;
- authenticated provider interaction;
- authenticated Git/`gh` operations against an authorized remote;
- live target paths and actual Unraid/Docker-host restart acceptance;
- production deployment/cutover authorization.

## Prior-art / failure-mode conclusions

The upstream SIGTERM issues are relevant evidence that shutdown must be tested end-to-end rather than inferred from “SIGTERM is conventional”. Current source has the corrected signal path, but dead-terminal EIO remains a distinct failure class. Docker's PID1-only stop semantics similarly mean a naive `stop_grace_period` change would not satisfy the accepted exec-session requirement.

No external evidence requires a new product/system decision.

## Execution-resolution classification

Classification: **return to Execution Prep**.

- Accepted requirements/ADR-003/M02 outcome remain valid.
- No finding changes user/product intent.
- No finding requires a new strategic milestone shape.
- Remaining choices are exact state layout, deadlines, locking, probes and rollback mechanics already delegated by the approved plan.
- Final owner: `execution_prep:M02`.

## Execution-Prep implications

The evidence is sufficient to contract M02 inside existing authority. A practical decomposition is:

1. persistent stable-runtime selector/LKG + readiness state;
2. native Pi launcher registration + service supervisor/graceful-stop contract;
3. host update/candidate/previous-image rollback operation plus integrated failure-injection verification.

The runtime selection/promotion/fallback and process/update/rollback behavior is cross-package stateful behavior, so the approved M02 JIT trigger to materialize/reconcile OpenSpec before implementation is satisfied and should be honored.

## Assumptions / uncertainties

- The exact state-directory names, cooldown duration, internal/outer stop deadlines and number/name of retained image tags remain delegated implementation details; select them in Execution Prep/OpenSpec and verify them.
- A direct disposable RPC probe attempt made during this Research used malformed shell quoting and produced a Pi parse error; it is **not** claimed as runtime GREEN evidence. The RPC readiness mechanism itself is established by current upstream source/docs and should be exercised correctly by M02 implementation tests.
- Exact package-slot installation mechanics under the non-root service user's home remain implementation work; current npm/Pi contracts support the approach, but M02 must verify the exact chosen command and ownership on Tower fixtures.

Research is evidence, not accepted requirement/decision/plan authority.
