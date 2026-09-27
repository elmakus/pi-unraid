# M06-T04 — automatic host-control integration evidence

Date: 2026-09-27  
Card: `M06-T04`  
Exact implementation/acceptance subject: `elmakus/pi-unraid@6d9e13018eaaf3da331d93d9a6d91bdf7f758464`  
Plan authority: approved P4, blob `3c0949e50b41100630b8e57f7dc51472e183f49c`

## Dependency and authority refresh

Launch refresh re-read and byte-verified every dependency bound by the Card:
- M06-T03 result `a140f95fef4cd99a433d3b7b08f3e482e4c4dbc2`
- M03-T01 result `1b157d85116b5a9dffab7df7766f62cc8a288f3e`
- M03-T02 result `a5c8a0c3a84b5c7f6da3d147896ee60995860800`
- M03-T03 result `db16908476e2f081669c65a4ff8e8e7062579f71`
- M05-T03 result `b526cf4717ea6d353fc6d23f082b1c726e7f55ed`

Current requirements plus ADR-PGR-002/003/004 and frozen P4 were re-read before launch. P4 supersedes the old P2 timing note that had placed credential-backed GraphQL mutation in M06: under P4, credential-backed authenticated GraphQL readback and every live mutation belong to staged HA M07-T02; M06-T04 remains automatic/noninteractive.

## Exact-SHA contract regression

On Tower, the existing isolated worktree was cleaned of generated `__pycache__` only, fetched, and fast-forwarded to the exact subject `6d9e13018eaaf3da331d93d9a6d91bdf7f758464`.

The complete current contract matrix ran on that exact SHA:

- 18 test modules
- **378 tests**
- verdict: **OK**
- test-log SHA-256: `f6dc1c9f7e43971f6d6c5d6633d6b9edde284174322d13e1be10ab50f72358c7`

The matrix includes candidate/image/runtime/Relay/instruction-plane, GraphQL, host safety/router, host doctor, capability inventory/control, Buildx/Tower/staged-update, RPC/workspace, browser/tool compatibility, and Relay/doctor readiness.

Relevant host-control coverage explicitly includes:
- exact bounded GraphQL permission profile and mutation surface;
- GraphQL machine-readable fail-closed behavior;
- mutation policy classification before side effects;
- strict private credential-file handling;
- exact high-impact user-gate policy;
- GraphQL-primary routing with SSH fallback only for accepted bounded reasons;
- no fallback on GraphQL credential/auth/application failures;
- non-sticky fallback and return to GraphQL after primary recovery;
- SSH `BatchMode`, `IdentitiesOnly`, strict host-key checking and disabled password/keyboard-interactive authentication;
- exact-scope authorization/pre-readback/anchor binding for gated SSH commands;
- read-only host doctor with structured transport/auth/protocol classification and GREEN/WARN/RED aggregation.

Surface-drift readback:
- integrated GraphQL/client/profile surface is unchanged from the accepted M03-T02 repaired subject `97faf73d43283d47538f331f5a41697a35618045`;
- SSH fallback/router/safety surface is unchanged from that same accepted M03-T02 subject;
- host-doctor surface is unchanged from accepted M03-T03 implementation `a19e53e35a729820a1dc62ec98ca01e354053a5d`.
The one post-M03-T01 GraphQL change is the already-reviewed M03-T02 repair that enforces shared safety policy before GraphQL mutation.

## Fresh live non-secret Tower readback

Fresh read-only checks on 2026-09-27 establish:

- Unraid: `7.2.4`
- native `unraid-api`: `4.37.4+ad268301`
- API service status: `online`
- GraphQL path: `/graphql`
- unauthenticated `info` query: HTTP 200 envelope with GraphQL error code `UNAUTHENTICATED`, no data
- accepted API-key request header remains `x-api-key`
- exact installed API version is unchanged from the prior M03 live resolver/schema evidence, so the already-reviewed permission mapping remains applicable: `INFO:READ_ANY` for info, `DOCKER:READ_ANY` for Docker readback and `DOCKER:UPDATE_ANY` for the bounded Docker update actions.

Repository readback confirms the least-practical profile still has no broad role and exactly:
- `INFO:READ_ANY`
- `DOCKER:READ_ANY`
- `DOCKER:UPDATE_ANY`

The only GraphQL container mutations exposed are:
`start`, `stop`, `restart`, `pause`, `unpause`.

## SSH reachability and credential boundary

The initial loopback probe to `127.0.0.1:22` was refused. This is not an SSH service outage: host readback shows sshd intentionally bound to the Tower LAN address only. A fresh TCP read against that bound address succeeds and returns protocol `SSH-2.0`.

The existing persistent Pi/Paseo SSH state is secret-safe but is not an already-approved Tower host-control credential:
- the private identity exists and is mode `0600`;
- the persistent SSH config is GitHub-only;
- the persistent known_hosts file has no Tower host entry;
- a temporary strict-host-key witness was constructed from Tower's own public host key without persisting any new trust or secret;
- the existing identity was then tried in `BatchMode`/strict-host-key/no-password/no-keyboard-interactive mode against Tower and was rejected with authentication failure.

Therefore M06-T04 proves live SSH transport reachability but **does not invent, persist or request a Tower SSH credential**. The credentialed forced-fallback witness is explicitly deferred to M07-T02 under the P4 clause that staged HA owns a forced bounded SSH-fallback confirmation only when M06-T04 leaves a credentialed-fallback witness gap.

The forced-test fallback mechanics themselves are already covered hermetically by the exact-SHA contract matrix: bounded fallback reasons, readback/anchor policy, strict noninteractive transport, secret-safe outputs, no arbitrary ordinary shell path, and return-to-GraphQL behavior.

## Safety and mutation accounting

The current safety policy keeps GraphQL primary and allows fallback only for:
`api_gap`, `api_outage`, `os_plugin_filesystem_recovery`, `forced_test`.

High-impact classes remain explicit external-user gates, including:
- generic SSH administration
- host reboot
- Docker-engine restart
- Unraid OS upgrade
- disk format
- broad share deletion
- broad appdata deletion
- broad network change

Unknown operations remain deny-by-default.

No authenticated GraphQL call, live GraphQL mutation, SSH mutation, high-impact action, production Paseo alias/HOME mutation, autostart change, destructive HOME restore or legacy-Pi change was performed. No raw credential, private key or API token was copied into Git/evidence.

## Automatic-slice outcome

**GREEN for the M06-T04 automatic technical acceptance surface.**

The exact candidate's host-control implementation is structurally and behaviorally GREEN for the automatic scope: GraphQL-primary contract, bounded least-practical profile, failure classification, safety gates, SSH transport reachability, hermetic bounded fallback/return-to-primary behavior, and read-only host doctor all pass.

Outstanding by design:
- credential-backed authenticated GraphQL INFO/DOCKER readback;
- least-privilege permission-sufficiency witness;
- one safe reversible live container mutation plus restoration readback;
- credentialed forced SSH-fallback witness because no already-approved Tower SSH identity exists;
- all other staged/manual/phone UX acceptance.

Those obligations belong to M07-T02/M07-T03. This evidence claims **M06 technical GREEN only after required independent review of M06-T04**, never full GREEN.
