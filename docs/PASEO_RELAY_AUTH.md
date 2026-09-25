# Paseo Relay, pairing and authentication contract

This repository targets the frozen Paseo `0.9.2` child image for M02-T02. The operational contract intentionally uses Paseo's native state under `PASEO_HOME=/home/paseo/.paseo` and does not create a second credential store.

## Relay and pairing

`scripts/configure-paseo-runtime.sh` persists `daemon.relay.enabled=false`. This explicit value is required because Paseo 0.9.2 documents legacy compatibility behavior for older homes whose setting is absent.

Pairing is a deliberate human action:

```bash
scripts/paseo-relay-access.sh pair
```

The helper requires an interactive terminal and invokes native `paseo daemon pair` without `--relay`. Paseo therefore asks before enabling Relay, with the upstream default answer remaining false. The QR code/pairing link is a trust anchor and must be treated as secret material; it is never emitted by automated CI/evidence.

For bounded non-secret readback:

```bash
scripts/paseo-relay-access.sh status
scripts/paseo-relay-access.sh revocation-capability
```

Status reports only Relay enablement plus presence/mode/ownership metadata for the native daemon keypair. It never prints the keypair or a pairing offer.

Paseo 0.9.2 stores the persistent ECDH daemon identity at `$PASEO_HOME/daemon-keypair.json`. M02-T02 smoke verifies that the private file remains mode 0600, numeric 99:100, and byte-identical across container recreation while Relay remains disabled.

The v0.9.2 CLI exposes `daemon pair` but no command for listing and individually revoking paired-device credentials. `revocation-capability` therefore reports unsupported and fails closed semantically; deleting/regenerating the daemon keypair is not presented as an equivalent device-revocation operation.

## Provider/account authentication

First-time provider or account authentication is never part of normal container startup. When a native CLI needs human interaction, enter the HOME-backed container explicitly:

```bash
scripts/paseo-relay-access.sh auth-shell
```

Run the provider's native login/OAuth/device-flow from that interactive shell. Credential-bearing state remains below the persisted `/home/paseo` boundary used by the upstream image. Do not pass secrets on command lines, add them to Compose environment variables, commit them to Git, or copy them into evidence.

Routine reuse/refresh of already-approved native sessions may occur from the same persistent HOME. Real provider login and phone Relay acceptance are intentionally deferred to the later integrated/production acceptance cards.

## Network boundary

The Compose service has no `ports:` publication. Relay uses the daemon's outbound connection and does not require a raw Paseo host port. M02-T02 smoke checks Docker has zero host port bindings.

## Frozen upstream evidence

Verified against `getpaseo/paseo@v0.9.2`:

- `public-docs/configuration.md`: managed config lives in `PASEO_HOME/config.json`; new homes keep Relay disabled and older omitted settings retain legacy behavior.
- `public-docs/security.md`: Relay is opt-in, outbound and end-to-end encrypted; the persistent daemon keypair lives at `$PASEO_HOME/daemon-keypair.json`.
- `public-docs/cli.md`: `paseo daemon pair` prompts; `pair --relay` is explicit non-interactive consent; `pair --json` never prompts and returns `RELAY_DISABLED` while disabled.
- `packages/cli/src/commands/daemon/pair.ts`: exact 0.9.2 behavior for consent and `RELAY_DISABLED`.
- `packages/server/src/server/daemon-keypair.ts`: exact keypair path and private-file persistence behavior.
