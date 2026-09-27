# M07-T02 GraphQL key diagnosis — 2026-09-27

Secret materialization itself is correct and secret-safe:

- client file: `/mnt/user/appdata/pi-unraid/secrets/unraid-api.key`
- mode `0600`, owner `99:100`
- bounded fingerprint `sha256:9514c3c99c4a70e5`
- exact client secret matches the native Unraid key record; raw value is not recorded.

The native key record is named `pi unraid paseo host control` because this Unraid build restricts API-key names to letters/numbers/spaces. That naming difference is benign.

The record currently does **not** satisfy the accepted least-practical profile. Current native metadata contains:

- role: `VIEWER`
- `ACTIVATION_CODE:READ_ANY`
- `ACTIVATION_CODE:UPDATE_ANY`
- `DOCKER:READ_ANY`
- `DOCKER:UPDATE_ANY`
- `INFO:READ_ANY`
- `INFO:UPDATE_ANY`

Required exact profile remains no roles and only:

- `INFO:READ_ANY`
- `DOCKER:READ_ANY`
- `DOCKER:UPDATE_ANY`

The first authenticated GraphQL readback failed closed with `API key validation failed`. No GraphQL mutation was attempted.
