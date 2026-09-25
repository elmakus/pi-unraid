# M02-T02 — Paseo Relay/auth/secret-state evidence

Date: 2026-09-25
Card: `M02-T02`
Final implementation commit: `31fb3c000cd1d7bd9d6c3ac49daff75fe22feadb`

## Exact implementation subjects

- Existing no-port Compose runtime contract: `compose.yaml@87f57b46f485918b50f560581ea86d580abcff6e`
- Native runtime configuration helper: `scripts/configure-paseo-runtime.sh@fc0e7e341529e7ad3f6a718bd8631ffe49c8ffdd`
- Human-gated Relay/auth operator helper: `scripts/paseo-relay-access.sh@4037b4104f90be184f88f19aed81abeac057bcbb`
- Disposable Relay/state persistence smoke: `scripts/verify-compose-foundation.sh@c34d3c9e5a5b1a200cb65ba0134f075d80273d6b`
- Operator/security contract: `docs/PASEO_RELAY_AUTH.md@67b013336b5abaaf03ce63c20de920875425f9de`
- Relay/auth contract tests: `tests/test_paseo_relay_auth_contract.py@250dac9e1c220502d1593a4df29e7500507bed85`
- CI contract: `.github/workflows/paseo-child-image.yml@61c587232cbc0fcfee98b8b4f0235c127a4c9eb5`
- Frozen predecessor result: `implementation/workstreams/feature-paseo-gui-runtime/results/M02-T01.md@727b6f25a3b957551d10c9c24d9e9d1e26efd6ab:e5075d474bb7aaf0583baf66757add56fb556253`

## Frozen upstream behavior

Verified against exact `getpaseo/paseo@v0.9.2`:

- `public-docs/configuration.md` documents persisted config under `PASEO_HOME/config.json`, Relay disablement for new homes and legacy omitted-setting compatibility.
- `public-docs/security.md` documents Relay as opt-in/outbound/E2E and the persistent daemon identity at `$PASEO_HOME/daemon-keypair.json`.
- `public-docs/cli.md` documents native `paseo daemon pair`, explicit `--relay` consent, and non-interactive `--json` behavior.
- `packages/cli/src/commands/daemon/pair.ts` confirms disabled Relay returns `RELAY_DISABLED`, `--relay` is the explicit non-interactive enable path, and the normal command does not silently consent.
- `packages/server/src/server/pairing-offer.ts` confirms a daemon keypair is created only when a Relay pairing offer is actually generated.
- `packages/server/src/server/daemon-keypair.ts` plus `private-files.ts` confirm `daemon-keypair.json` is native sensitive state and is written/private-enforced as mode `0600`.
- The v0.9.2 daemon CLI command surface has no command for listing and individually revoking paired-device credentials. The repository therefore exposes explicit unsupported capability readback rather than inventing a destructive substitute.

## Final GitHub Actions evidence

- Workflow run: `36151258901`
- Job: `108124815714` / `contract-build-and-smoke`
- Head SHA: `31fb3c000cd1d7bd9d6c3ac49daff75fe22feadb`
- Conclusion: **success**
- Exact predecessor bindings: GREEN, including frozen M02-T01 result
- Candidate resolver / child-image / M02 runtime / M02-T02 Relay-auth contract tests: GREEN
- Frozen Paseo child-image build: GREEN
- Disposable image/provenance smoke: GREEN
- Disposable Relay/persistence/ownership/recreate smoke: GREEN
- Immutable foundation metadata readback: GREEN

The exact CI image was:

- Candidate ID: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- Built image ID: `sha256:480e7207f0a0998e252ea5fe0cc63aa370a456348c245271e5ccb541f20326b9`
- Paseo: `0.9.2`
- Pi: `0.87.1`
- Playwright: `1.63.0`
- Chromium headless/headed-Xvfb: `153.0.8010.12`
- Paseo health: GREEN
- Image config/history secret scan: GREEN

The disposable smoke emitted:

```json
{"card":"M02-T02","home_persisted":true,"projects_persisted":true,"worktrees_persisted":true,"worktrees_root":"/worktrees","relay_enabled":false,"daemon_identity_persisted":true,"raw_host_ports":0,"revocation_cli":"unsupported","runtime_uid":99,"runtime_gid":100,"shm_bytes":1073741824,"resource_caps":"none","result":"GREEN"}
```

## Acceptance readback

The final exact run proves:

- persisted native config explicitly contains `daemon.relay.enabled=false`, avoiding legacy omitted-setting ambiguity;
- a non-consenting, non-interactive native `pair --json` returns `RELAY_DISABLED`;
- CI creates a pairing offer only in its disposable HOME with explicit `--relay`, captures the trust-anchor output without logging it, then immediately restores Relay=false;
- native `daemon-keypair.json` is owned by runtime UID:GID `99:100`, remains mode `0600`, and its exact bytes survive container recreation;
- normal Compose startup does not invoke pairing, provider login or another first-time authentication action;
- the operator `pair` path requires a TTY and invokes native `paseo daemon pair` without `--relay`, retaining Paseo's human consent prompt;
- the operator `auth-shell` path also requires a TTY and enters the persisted `/home/paseo` boundary for native provider/account login rather than accepting credential arguments or adding credential environment wiring;
- `status` reports only non-secret Relay/keypair metadata; it never emits key contents or a pairing offer;
- `revocation-capability` explicitly reports v0.9.2 individual-device revocation as unsupported;
- Docker has zero host port bindings for Paseo; Relay remains the intended outbound remote path;
- existing HOME/projects/worktrees ownership, 1 GiB shared memory, uncapped CPU/RAM and bounded logging remain intact;
- cleanup removes the disposable runtime and temporary fixture. No production/Tower runtime, real phone pairing or real provider credential was touched.

## Repair history

Two earlier M02-T02 CI attempts were not accepted:

- `36150639582`: RED because the first smoke incorrectly expected upstream to create `daemon-keypair.json` while Relay was still disabled. Exact v0.9.2 source showed pairing-offer generation returns before identity creation in that state.
- `36150994457`: RED before the runtime probe because a text-patching escape collapsed the disposable Compose project PID suffix from `$$` to `$`.

Only run `36151258901` on exact final implementation SHA `31fb3c000cd1d7bd9d6c3ac49daff75fe22feadb` is acceptance evidence.
