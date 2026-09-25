# Unraid GraphQL host-control foundation

M03-T01 defines the GraphQL-primary host-control boundary for the Paseo/Pi environment. It does not implement SSH fallback, high-impact host operations, the M03-T03 doctor, or production cutover.

## Exact live substrate observed on Tower

Read-only live checks on 2026-09-25 observed:

- Unraid: `7.2.4`
- native `unraid-api`: `4.37.4+ad268301`, online
- GraphQL HTTP path: `/graphql`
- API-key authentication header: `x-api-key`
- native API-key resources/actions expose granular resource permissions
- unauthenticated GraphQL readback fails closed with `UNAUTHENTICATED`

The exact installed resolver code requires `INFO:READ_ANY` for the `info` tree and `DOCKER:READ_ANY` for Docker readback. Docker start/stop/restart/pause/unpause require `DOCKER:UPDATE_ANY`.

## Least-practical M03-T01 credential

The operational key for this Card has no broad role. Its exact intended permission set is:

```text
INFO:READ_ANY
DOCKER:READ_ANY
DOCKER:UPDATE_ANY
```

It does not need `ADMIN`, Docker create/delete permission, API-key administration permission, network mutation permission, array mutation permission, OS mutation permission, or VM mutation permission.

On the exact live API build, the CLI accepts the granular `--permissions` syntax but its create path currently fails validation when persisting the parsed nested permission objects. Do not compensate by leaving an `ADMIN` key in place. Create the dedicated key through the native typed API/UI surface with the exact permission set above, then materialize only its returned secret into protected runtime state.

## Secret materialization

`scripts/configure_unraid_graphql_credential.py` installs or rotates a client key without putting it on the command line. The target parent must already exist. The resulting file is an atomic regular file with mode `0600`.

Example interactive use:

```bash
python3 scripts/configure_unraid_graphql_credential.py install \
  --path /protected/persistent/path/unraid-api.key
```

The prompt does not echo the key. For automation, pass secret material on stdin from the platform secret mechanism, never as an argument or tracked environment value.

Bounded status readback reports only presence, ownership, mode and a truncated SHA-256 fingerprint:

```bash
python3 scripts/configure_unraid_graphql_credential.py status \
  --path /protected/persistent/path/unraid-api.key
```

The final production secret path/mount is bound during deployment; this Card does not create a production Paseo HOME or introduce a second credential database.

## Structured GraphQL client

`scripts/unraid_graphql_host_control.py` requires both an explicit `/graphql` endpoint and a private API-key file. It never accepts a key value on the command line.

Readback:

```bash
python3 scripts/unraid_graphql_host_control.py \
  --endpoint http://tower/graphql \
  --api-key-file /protected/path/unraid-api.key \
  readback
```

The read path returns structured system/OS data plus the observable Docker container list. Derived inventory is live/readback state only; it is not written as canonical project state.

The only supported Docker mutations are `start`, `stop`, `restart`, `pause`, and `unpause` for one explicit container ID. Every mutation performs a container read before the mutation and a second read after it:

```bash
python3 scripts/unraid_graphql_host_control.py \
  --endpoint http://tower/graphql \
  --api-key-file /protected/path/unraid-api.key \
  container-action --id <prefixed-id> --action pause
```

Remove, image update, bulk update, Docker-engine restart, host reboot, storage formatting, broad deletion and broad network changes are not exposed by this helper.

## M03 boundary

SSH fallback and generalized mutation guards/rollback anchors belong to M03-T02. Host-control doctor semantics belong to M03-T03. The helper in this Card is intentionally narrower: GraphQL primary transport, least-practical credential, structured readback, and one-container reversible ordinary mutations with before/after readback.
