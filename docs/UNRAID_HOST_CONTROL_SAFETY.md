# Unraid host-control SSH fallback and safety guard

M03-T02 adds the bounded fallback/safety plane around the M03-T01 GraphQL-primary foundation. It does not perform credential-backed Tower integration; approved P2 keeps the authenticated GraphQL mutation plus forced SSH-fallback integration smoke in M06-T04.

## Transport rule

`scripts/unraid_host_control_router.py` is GraphQL-primary on every normal invocation. It falls back automatically only for a transport failure or HTTP 502/503/504, which is recorded as `api_outage`. Authentication, authorization, GraphQL application errors and other non-outage failures fail closed instead of escalating to SSH.

Explicit direct SSH readback is allowed only for the bounded reasons `api_gap`, `os_plugin_filesystem_recovery`, and `forced_test`. No fallback state is persisted, so the next normal invocation attempts GraphQL again.

## SSH credential and connection contract

`scripts/unraid_ssh_fallback.py` requires:
- a private regular non-symlink identity file;
- a regular known_hosts file that is not group/other writable;
- strict host-key checking;
- `BatchMode=yes`, password authentication disabled, keyboard-interactive authentication disabled, and `IdentitiesOnly=yes`.

Status output contains bounded metadata and a truncated identity-file SHA-256 fingerprint, never the private key bytes. The child image contains `openssh-client`; no SSH daemon is added to Paseo.

Read-only fallback exposes fixed probe/readback commands. A forced-test-only smoke marker uses the fixed path `/tmp/pi-unraid-host-control-smoke`, refuses to run if the path already exists, performs pre/post readback, and automatically removes the marker and verifies restoration.

## Mutation safety policy

`config/unraid-host-control/host-safety-policy.json` is consumed by both mutation transports. The existing GraphQL one-container actions are classified as ordinary bounded mutations with transport-internal pre-readback, and the GraphQL mutator checks that exact classification before the side effect. It classifies the following SSH operations as user-gated:
- generic SSH administrative command;
- whole-host reboot;
- whole Docker-engine restart;
- Unraid OS upgrade;
- disk format;
- broad share deletion;
- broad appdata deletion;
- broad network/routing/firewall/default-gateway/DNS change.

Unknown operations fail closed.

The generic SSH administrative path is intentionally not an ordinary shell escape. Each command file must name its concrete gated operation class. The guard binds `operation class + argv` into one exact SHA-256 scope and requires three external artifacts for that scope: GREEN pre-mutation readback, a private GREEN `external_user_authorization` record, and a GREEN rollback anchor. Specific high-impact classes and the generic gated class therefore share the same fail-closed baseline; an ordinary GraphQL class cannot be used by the SSH executor. This repository provides no command that manufactures the user-authorization record.

Generic command stdout/stderr are not copied into machine-readable output; only byte counts and truncated SHA-256 digests are returned. Secret values must not be placed in command argv or committed command/evidence files.

## Authority boundary

The guard mechanically enforces pi-unraid host-safety policy only. It does not create Project Workflow user approval, replace PW review/stop semantics, or become OR runtime policy. M03-T03 owns read-only host-control doctor behavior. M06-T04 remains responsible for real credential-backed GraphQL and forced SSH fallback acceptance before production cutover.
