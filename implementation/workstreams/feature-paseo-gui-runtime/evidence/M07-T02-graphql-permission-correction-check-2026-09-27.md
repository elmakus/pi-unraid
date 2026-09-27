# M07-T02 GraphQL permission correction verification — 2026-09-27

After the user reported saving the correction, the native Unraid key record was read back directly from persistent key storage.

Result:

- key name remains `pi unraid paseo host control`
- role remains `VIEWER`
- explicit permissions remain:
  - `ACTIVATION_CODE:READ_ANY`
  - `ACTIVATION_CODE:UPDATE_ANY`
  - `DOCKER:READ_ANY`
  - `DOCKER:UPDATE_ANY`
  - `INFO:READ_ANY`
  - `INFO:UPDATE_ANY`
- authenticated GraphQL readback now succeeds with this key
- no GraphQL mutation was attempted because the exact least-privilege acceptance profile is still not met

Required persisted profile remains: no roles; only `INFO:READ_ANY`, `DOCKER:READ_ANY`, `DOCKER:UPDATE_ANY`.
