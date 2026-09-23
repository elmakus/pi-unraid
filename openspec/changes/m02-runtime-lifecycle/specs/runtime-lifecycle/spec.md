# Runtime lifecycle specification

## Stable runtime selection

1. Normal Compose service startup MUST attempt to resolve the current npm `latest` version of `@earendil-works/pi-coding-agent` within a bounded lookup time.
2. The resolved target MUST be a stable semantic version; prerelease/nightly-shaped targets MUST NOT be activated.
3. Downloaded candidates MUST be installed into a new versioned persistent-home slot with lifecycle scripts disabled and Node engine compatibility enforced.
4. Candidate activation MUST require both exact version readback and a bounded Pi RPC `get_state` readiness response from the staged binary.
5. Installation/probe failure MUST leave the previous working selection intact and MUST NOT overwrite the image seed.
6. Runtime state mutation MUST be serialized and atomically published. Interrupted or overlapping reconciliations MUST not expose a partially installed slot or partial state file.
7. A proven-bad candidate MUST be remembered long enough to avoid immediate restart-loop reselection. Explicit retry remains possible.
8. Registry/network unavailability MUST degrade to an already compatible persistent LKG or the image seed; it is not itself proof that a version is bad.
9. Every image carries a pinned seed runtime. If persistent runtime state is absent/incompatible/broken, the image seed MUST remain an offline recovery candidate.
10. Dynamic runtime state MUST stay under persistent `/home/pi` and MUST NOT mutate `~/.pi/agent` auth/session/config content.

## Readiness and diagnostics

1. Runtime reconciliation MUST atomically publish non-secret state identifying readiness/unavailability, selected source/version, seed version, observed latest version when known, LKG/previous-LKG identities and failed-candidate diagnostics.
2. A health/readiness command MUST fail when no compatible runtime is currently usable or when startup reconciliation has not completed; stale prior success MUST not report healthy.
3. Compose MUST expose that readiness through a healthcheck.
4. Lifecycle diagnostics MUST go to bounded Docker logs and/or bounded state fields; M02 MUST NOT introduce an unbounded parallel log.

## Managed native Pi lifecycle

1. The supported `pi` entry MUST execute the selected persistent runtime or image seed and preserve the native terminal/TUI behavior.
2. Before exec, the launcher MUST register its PID plus a reuse-resistant identity such as Linux process start-time in an ephemeral container registry.
3. Stale registry entries MUST be validated/pruned before any signal is sent.
4. The normal service PID1 MUST run as the configured non-root service user after M01 initialization.
5. On planned service SIGTERM, PID1 MUST stop admitting new managed Pi launches, send SIGTERM to each still-valid managed Pi process, wait a bounded internal grace period, SIGKILL only still-running managed processes after that bound, then terminate its keepalive and exit.
6. Compose's outer stop grace MUST exceed the internal Pi grace so current Pi can run its own SIGTERM cleanup before Docker's final SIGKILL.
7. The default contract is 12 seconds internal Pi grace and 20 seconds Compose `stop_grace_period`. Fixture tests MAY use shorter explicit overrides.
8. Planned shutdown claims apply to SIGTERM-driven managed shutdown. M02 MUST NOT claim arbitrary dead-PTY/EIO crashes are graceful.
9. Persisted Pi session/native state MUST remain untouched by stop/escalation. M02 does not promise persistence of an uncommitted in-flight provider/tool operation.

## Host update and deployment rollback

1. `scripts/update.sh` is the one normal user-facing repository/image/deployment update entry.
2. Before repository/deployment mutation it MUST acquire a host update lock, require a safe fast-forwardable checkout, record the pre-update source HEAD, current deployed image identity and rendered deployment config, and keep that transaction outside the container's replaceable image.
3. Repository synchronization MUST be fast-forward-only; local conflicting changes MUST stop before deployment mutation.
4. Updated source MUST build to a separate candidate image tag and pass the applicable disposable verification/readiness gate before replacing the active local tag.
5. Immediately before candidate cutover, the currently deployed known-working image MUST be retained under a previous/rollback tag.
6. Candidate cutover MUST preserve the accepted bind sources and verify service health. Failure after cutover MUST restore the previous image tag plus recorded deployment config and re-check health.
7. Deployment rollback MUST NOT rewrite, delete or restore `/home/pi`, `/projects` or `/worktrees`.
8. Rollback artifacts MUST be sufficient for an offline deployment rollback once the previous image/config are retained; rollback MUST NOT require fetching the broken candidate again.
9. Keep at least the active image and one previous known-working image/deployment candidate. Cleanup MUST never delete the current rollback candidate before a newer deployment is proven healthy.
10. Production defaults MAY use host state beneath `/mnt/user/appdata/pi-unraid/deployment-state`, but this directory is host-operated metadata and MUST NOT be added as a container mount.
11. M02 verification MUST exercise the host operation only against uniquely named disposable Docker/Compose fixtures. Live cutover is an M03 authorization/readiness action.

## Verification boundary

Packaged-Pi checks are required where runtime/TUI behavior is material. Deterministic stubs/synthetic candidates MAY be used only to inject upstream/network/broken-candidate faults and MUST NOT replace real packaged-Pi startup/readiness/shutdown checks.
