# M02 runtime lifecycle design

## Runtime layout

- Persistent runtime packages: `/home/pi/.local/share/pi-unraid/runtimes/<version>/`
- Persistent lifecycle state: `/home/pi/.local/state/pi-unraid/runtime.json`
- Mutation lock: `/home/pi/.local/state/pi-unraid/runtime.lock` using `flock` so process death releases ownership.
- Staging: sibling `.staging-<pid>-<version>` directory, renamed only after successful install/probe.
- Ephemeral managed-process registry: `/tmp/pi-unraid/managed-pi/`.
- Image seed executable: preserve the M01 global package behind `/usr/local/bin/pi-seed`.
- User/operator entry: repository-owned `/usr/local/bin/pi` launcher.

The runtime state schema starts at `schema: 1` and records no credential/session payload. Exact fields may expand compatibly, but must include status, selected source/version, image seed version, LKG, previous LKG, observed latest when known, failed candidate metadata and last reconciliation outcome.

## Runtime defaults

- registry/latest lookup bound: 15 s;
- staged RPC `get_state` probe bound: 10 s;
- failed-candidate retry cooldown: 3600 s by default, with an explicit forced retry path;
- production internal managed-Pi graceful stop: 12 s;
- Compose outer `stop_grace_period`: 20 s.

The updater may use npm's own retries within the outer lookup/install bounds. Failure categories must keep lookup/offline fallback distinct from candidate install/readiness rejection.

## Service shape

M01 root entrypoint keeps ownership/UID reconciliation, then execs the requested command as `pi`. Normal Compose `CMD` becomes a non-root `pi-unraid-service` supervisor rather than `sleep infinity`.

The service supervisor performs startup runtime reconciliation before publishing ready state, then remains PID1 with signal traps. The `pi` launcher uses already reconciled selection and does not perform an unbounded network lookup on every interactive exec.

PID registry records include PID and Linux start-time; stop logic re-reads `/proc`, UID and start-time before signaling. Registration is deliberately ephemeral: persistent home stores runtime selection, not process identities.

## Candidate readiness

Use the exact candidate binary:

1. exact `--version` readback;
2. launch `--mode rpc --no-session`;
3. send one JSONL `get_state` command;
4. require a matching successful response within 10 s;
5. terminate/close the probe and ensure it does not leave a managed interactive registration.

This follows the same readiness primitive used by upstream Pi's startup profiling tooling and avoids provider/OAuth calls.

## Host update transaction

Production default host metadata root: `/mnt/user/appdata/pi-unraid/deployment-state` (not mounted into the container). Fixture tests override it to a unique `/tmp` path.

A normal update transaction:

1. lock update state;
2. snapshot pre-update source HEAD, current image ID and `docker compose config`;
3. fast-forward-only synchronize the current tracking branch;
4. re-enter the updated `scripts/update.sh` transaction phase;
5. build `pi-unraid:candidate`;
6. run image/runtime/Compose fixture verification applicable to the candidate;
7. tag current known-working image as `pi-unraid:previous`;
8. tag candidate as `pi-unraid:local` and recreate/start the service without rebuilding;
9. wait for healthy/readback;
10. on failure, retag the previous image as `pi-unraid:local`, recreate from the saved rendered config and verify recovery;
11. only after successful cutover rotate transaction metadata and any older superseded rollback artifact.

A failed deployment rollback does not silently reset the Git checkout. The transaction records the pre-update HEAD so source recovery is explicit and auditable.

## Failure injection

M02 tests use unique Docker project names/tags and `/tmp` binds. Real current Pi is used for successful staged startup and planned SIGTERM. Controlled PATH/npm stubs or synthetic broken candidate state may inject registry/install/start failures, but the state machine must also pass a real packaged-Pi path. A deliberately broken disposable image exercises image rollback.
