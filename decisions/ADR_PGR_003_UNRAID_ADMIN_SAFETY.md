# Decision — Main receives full Unraid administration with explicit high-impact gates

- Decision ID: `ADR-PGR-003`
- Date: `2026-09-24`
- Status: `accepted`
- Definition subject: `paseo-gui-runtime@2`

## Decision

Main receives full administrative capability over the Unraid host with the native Unraid GraphQL API as the preferred structured primary control path and non-interactive SSH as fallback for API gaps, API outage, and OS/plugin/filesystem/recovery work. After fallback/recovery, normal operation returns to GraphQL when healthy. Ordinary bounded host operations inside accepted task authority do not need per-command approval.

Explicit user gates remain for whole-host reboot, whole Docker-engine restart, Unraid OS upgrade, formatting storage, deleting broad shares/appdata, broad network-routing changes and comparable high-impact actions.

Runtime Pi/Paseo stays non-root/no-sudo where practical; host administration uses explicit host-control credentials/transports. Secrets never become Git authority.

## Consequences

Full capability does not imply indiscriminate host mounts or Docker-socket exposure to the Paseo runtime. Planning owns concrete API-key permissions, SSH credential materialization, health/readback and failover mechanics while preserving GraphQL-primary/SSH-fallback semantics.
