# Decision — GHCR accepted channel with user-triggered Unraid cutover

- Decision ID: `ADR-PUD-001`
- Date: `2026-09-28`
- Status: `accepted`
- Definition subject: `paseo-update-distribution@10`
- Supersedes for this scope: the local-first/Tower-build and GHCR-optional operational path in `ADR-PGR-004`

## Decision

Normal update distribution uses GitHub-hosted discovery/build/test, GHCR immutable image identity, one serialized mutable accepted channel, Tower-specific disposable validation, and a user-triggered production cutover from the Unraid surface.

The production image identity is the OCI digest. The accepted tag is signaling metadata only and may move only after the exact digest has passed required GitHub and Tower gates. Production never auto-updates merely because the accepted tag moves.

The preferred operator gesture remains stock DockerMan Update. A pre-armed Tower transaction guard must own acceptance/rollback semantics around that gesture. If exact crash-safe binding to the installed DockerMan behavior cannot be proven, one project/plugin `Update + Verify` action inside Unraid is the accepted fallback. A custom dashboard or patching DockerMan core is not part of this scope.

## Consequences

The legacy Git/Compose production updater is no longer the normal path. Compose remains useful for development, disposable validation and recovery. GHCR is no longer an optional enhancement for this scope; it is the normal accepted-image distribution channel.
