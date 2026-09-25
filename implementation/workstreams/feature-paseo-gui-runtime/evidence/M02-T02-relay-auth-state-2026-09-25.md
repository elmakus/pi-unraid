# M02-T02 — Paseo Relay/auth/secret-state evidence

Date: 2026-09-25
Card: `M02-T02`
Final implementation commit: `c4952b4b08c48550b392c2b57da0f2bcab6ce39f`

## Exact implementation subjects

- Existing no-port Compose runtime contract: `compose.yaml@87f57b46f485918b50f560581ea86d580abcff6e`
- Native runtime configuration helper: `scripts/configure-paseo-runtime.sh@fc0e7e341529e7ad3f6a718bd8631ffe49c8ffdd`
- Human-gated Relay/auth operator helper: `scripts/paseo-relay-access.sh@469073e476ac9856c97bd7a089d6ace339eb29f6`
- Disposable Relay/state persistence smoke: `scripts/verify-compose-foundation.sh@b143814903caffd96a4db9470a91c3522533943e`
- Operator/security contract: `docs/PASEO_RELAY_AUTH.md@fad4358d055ed093d90a718e3b018651aca8b703`
- Relay/auth contract tests: `tests/test_paseo_relay_auth_contract.py@b377af825658c4d022a9cecb1a5809200369c541`
- CI contract: `.github/workflows/paseo-child-image.yml@61c587232cbc0fcfee98b8b4f0235c127a4c9eb5`
- Frozen predecessor result: `implementation/workstreams/feature-paseo-gui-runtime/results/M02-T01.md@727b6f25a3b957551d10c9c24d9e9d1e26efd6ab:e5075d474bb7aaf0583baf66757add56fb556253`

## Frozen upstream behavior

Verified against exact `getpaseo/paseo@v0.9.2`:

- `public-docs/configuration.md` documents persisted config under `PASEO_HOME/config.json`, Relay disablement for new homes and legacy omitted-setting compatibility.
- `public-docs/security.md` documents Relay as opt-in/outbound/E2E and the persistent daemon identity at `$PASEO_HOME/daemon-keypair.json`.
- `packages/cli/src/commands/daemon/pair.ts` and `packages/cli/tests/03-daemon.test.ts` prove that plain `paseo daemon pair` does not prompt to enable a disabled Relay; it returns `RELAY_DISABLED`. `daemon pair --relay` is the explicit-consent path and persists Relay enablement.
- `packages/cli/src/commands/onboard.ts` contains upstream's interactive Relay confirmation; that confirmation is part of onboarding, not the standalone `daemon pair` command.
- `packages/server/src/server/pairing-offer.ts` confirms a daemon keypair is created only when a Relay pairing offer is generated.
- `packages/server/src/server/daemon-keypair.ts` plus `private-files.ts` confirm `daemon-keypair.json` is native sensitive state and is written/private-enforced as mode `0600`.
- The v0.9.2 daemon CLI command surface has no command for listing and individually revoking paired-device credentials. The repository therefore exposes explicit unsupported capability readback rather than inventing a destructive substitute.

## Final GitHub Actions evidence

- Workflow run: `36153362603`
- Job: `108131863706` / `contract-build-and-smoke`
- Head SHA: `c4952b4b08c48550b392c2b57da0f2bcab6ce39f`
- Conclusion: **success**
- Exact predecessor bindings: GREEN, including frozen M02-T01 result
- Candidate resolver / child-image / M02 runtime / corrected M02-T02 Relay-auth contract tests: GREEN
- Frozen Paseo child-image build: GREEN
- Disposable image/provenance smoke: GREEN
- Disposable Relay/persistence/ownership/recreate smoke: GREEN
- Immutable foundation metadata readback: GREEN

The exact CI image was:

- Candidate ID: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- Built image ID: `sha256:9795f5c00b1c04cd03afd51bc40dec07499ff8132c4b3efec6cc53f80594677a`
- Paseo: `0.9.2`
- Pi: `0.87.1`
- Playwright: `1.63.0`
- Chromium headless/headed-Xvfb: `153.0.8010.12`
- Paseo health: GREEN
- Image config/history secret scan: GREEN

The disposable smoke emitted:

```json
{"card":"M02-T02","home_persisted":true,"projects_persisted":true,"worktrees_persisted":true,"worktrees_root":"/worktrees","relay_default_disabled":true,"relay_enabled_after_consent":true,"relay_enabled_after_recreate":true,"daemon_identity_persisted":true,"raw_host_ports":0,"revocation_cli":"unsupported","runtime_uid":99,"runtime_gid":100,"shm_bytes":1073741824,"resource_caps":"none","result":"GREEN"}
```

## Acceptance readback

The final exact run plus source readback prove:

- initial persisted native config explicitly contains `daemon.relay.enabled=false`, avoiding legacy omitted-setting ambiguity;
- a non-consenting, non-interactive native `pair --json` returns `RELAY_DISABLED`;
- the repository `pair` helper requires an interactive TTY and its own explicit yes/no confirmation with a default-negative `[y/N]` prompt;
- only an affirmative helper response reaches native `paseo daemon pair --relay`; a negative/default response exits before Relay enablement;
- disposable acceptance simulates that explicit consent, captures the trust-anchor pairing offer without logging it, and proves persisted `daemon.relay.enabled=true` survives container recreation;
- native `daemon-keypair.json` is owned by runtime UID:GID `99:100`, remains mode `0600`, and its exact bytes survive container recreation;
- normal Compose startup does not invoke pairing, provider login or another first-time authentication action;
- the operator `auth-shell` path requires a TTY and enters the persisted `/home/paseo` boundary for native provider/account login rather than accepting credential arguments or adding credential environment wiring;
- `status` reports only non-secret Relay/keypair metadata; it never emits key contents or a pairing offer;
- `revocation-capability` explicitly reports v0.9.2 individual-device revocation as unsupported;
- Docker has zero host port bindings for Paseo; Relay remains the intended outbound remote path;
- existing HOME/projects/worktrees ownership, 1 GiB shared memory, uncapped CPU/RAM and bounded logging remain intact;
- cleanup removes the disposable runtime and temporary fixture. No production/Tower runtime, real phone pairing or real provider credential was touched.

## Repair and review history

Two early implementation CI attempts were not accepted:

- `36150639582`: RED because the first smoke incorrectly expected upstream to create `daemon-keypair.json` while Relay was still disabled.
- `36150994457`: RED before the runtime probe because a text-patching escape collapsed the disposable Compose project PID suffix from `$$` to `$`.

The first independently reviewed semantic result used implementation SHA `31fb3c000cd1d7bd9d6c3ac49daff75fe22feadb` and CI run `36151258901`. Independent review attempt `M02-T02-R01` is durably **RED** because exact upstream v0.9.2 source/tests disproved that implementation's claim that plain `paseo daemon pair` would interactively ask to enable Relay. R01 also observed that the old smoke reset Relay to false before recreation and therefore did not directly prove enabled-Relay persistence.

The bounded same-Card repair is `c4952b4b08c48550b392c2b57da0f2bcab6ce39f`. It adds repository-owned explicit human confirmation before native `--relay`, corrects documentation/tests, and extends disposable acceptance to keep and prove Relay enabled across recreation. Only run `36153362603` on this repaired SHA is final execution acceptance evidence for the repaired subject.
