# Decision — Main receives full Unraid administration with explicit high-impact gates

- Decision ID: `ADR-PGR-003`
- Date: `2026-09-24`
- Status: `definition-active`
- Definition subject: `paseo-gui-runtime@2`

## Decision

Main is intended to have full administrative capability over the Unraid host through a researched structured-primary/fallback control architecture. Ordinary bounded host operations inside accepted task authority do not need per-command approval.

Explicit user gates remain for whole-host reboot, whole Docker-engine restart, Unraid OS upgrade, formatting storage, deleting broad shares/appdata, broad network-routing changes and comparable high-impact actions.

Runtime Pi/Paseo stays non-root/no-sudo where practical; host administration uses explicit host-control credentials/transports. Secrets never become Git authority.

## Consequences

Full capability does not imply indiscriminate host mounts or Docker-socket exposure to the Paseo runtime. Exact transport/credential mechanics are Definition Research/Planning choices.
