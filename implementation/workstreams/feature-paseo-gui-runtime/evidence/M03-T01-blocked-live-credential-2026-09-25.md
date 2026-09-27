# M03-T01 — implementation/readiness evidence and live-credential blocker

Date: 2026-09-25
Card: `M03-T01`
State: **BLOCKED**

## Exact implementation subject

- Implementation head: `43d082317339e6aef4362d2d456b41442dc739e1`
- Primary client: `scripts/unraid_graphql_host_control.py`
- Credential materializer: `scripts/configure_unraid_graphql_credential.py`
- Machine-readable permission profile: `config/unraid-host-control/permission-profile.json`
- Contract tests: `tests/test_unraid_graphql_host_control_contract.py`
- Operational contract: `docs/UNRAID_GRAPHQL_HOST_CONTROL.md`
- Exact predecessor result remains `implementation/workstreams/feature-paseo-gui-runtime/results/M02-T03.md@cac4ac5e5a4b6c96ad71d9bbce12962388f7a4be:0d13d7fe5a6dd29fb68e700d13cc5c1251722c28`.

## Implemented contract

- The client accepts only an explicit `/graphql` endpoint plus a private API-key file; no key value is accepted on the command line.
- Readback covers structured host OS/system identity and Docker container state.
- The only exposed Docker mutations are one-container `start`, `stop`, `restart`, `pause` and `unpause`.
- Every supported mutation performs exact container readback before and after the GraphQL mutation.
- Remove/image-update/bulk-update, SSH fallback, Docker-socket exposure and the accepted high-impact gate operations are not exposed by this subject.
- Credential installation/rotation is stdin/getpass -> atomic regular file with private mode and bounded fingerprint-only readback.
- Final operational profile contains no broad role and exactly:
  - `INFO:READ_ANY`
  - `DOCKER:READ_ANY`
  - `DOCKER:UPDATE_ANY`

## Exact CI evidence

GitHub Actions run `36160307230` completed **success** on exact SHA `43d082317339e6aef4362d2d456b41442dc739e1`.

GREEN steps include:

- exact predecessor binding verification;
- candidate/runtime contract tests, including the M03-T01 host-control contract;
- frozen Paseo child-image build;
- disposable provenance smoke;
- disposable persistence/ownership/recreation smoke;
- disposable Pi instruction-plane smoke;
- immutable foundation metadata readback.

## Live Tower readback already completed

Read-only checks against the real Tower established:

- Unraid `7.2.4`;
- native `unraid-api 4.37.4+ad268301` online;
- GraphQL path `/graphql`;
- API-key request header `x-api-key`;
- native granular resources/actions and the resolver permission checks for `INFO:READ_ANY`, `DOCKER:READ_ANY` and `DOCKER:UPDATE_ANY`;
- Docker start/stop/restart/pause/unpause all bind to `DOCKER:UPDATE_ANY`;
- an unauthenticated live `info` query returns GraphQL `UNAUTHENTICATED`, proving the real endpoint fails closed;
- exact live CLI parsing accepts granular permission syntax, but this API build's CLI create path fails nested permission validation when persisting a granular key. Leaving a broad `ADMIN` key is therefore explicitly rejected as a workaround.

No production Paseo deployment, Relay/provider secret, raw Docker socket, SSH fallback or accepted high-impact host operation was performed.

## Concrete blocker

The remaining Task Card acceptance requires one authenticated live pass with the final least-practical permission set:

1. authenticated structured `info` + Docker readback;
2. one safe disposable-container GraphQL mutation with exact pre-state/post-state and restoration/cleanup;
3. evidence that the key works without any broader role/permission.

The authorized Remote Desktop connector refuses commands that create, materialize or exercise API-key secret values, including an attempted dummy-key path. Existing local Unraid secrets were not extracted or bypassed. This is an access/runtime-input blocker, not a product defect.

## Resume condition

Create a dedicated Unraid API key named `Pi Unraid M03 T01 Smoke` in the native WebGUI with **no role** and exactly:

- `INFO:READ_ANY`
- `DOCKER:READ_ANY`
- `DOCKER:UPDATE_ANY`

Place the key value on Tower at `/tmp/pi-unraid-m03-t01/unraid-api.key` as a regular mode-`0600` file without posting the key in chat. Once that path exists, M03-T01 resumes with authenticated readback, a disposable reversible Docker GraphQL smoke, cleanup/revocation, result reconciliation and required independent review.


## Resume attempt readback — 2026-09-25

After the user reported the credential ready, Tower readback found `/tmp/pi-unraid-m03-t01/unraid-api.key` as a regular non-symlink file owned by root:root with mode `0600`, but its size is exactly **1 byte**. This is consistent with a newline-only/empty credential and does not satisfy the live-authentication resume condition. The raw file content was not printed or copied.

The blocker therefore remains active. Resume requires the same path to contain the actual dedicated API key value and remain a private `0600` regular file.
