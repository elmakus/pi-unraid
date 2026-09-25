# Unraid safety boundary

Accepted environment direction:

- Native Unraid GraphQL is the preferred structured host-control path once implemented and healthy.
- Non-interactive SSH is the fallback for API gaps, outage, filesystem/OS/plugin work, and recovery once that fallback is implemented.
- Perform bounded readback before host mutation and use rollback/snapshot anchors for broad changes where technically applicable.
- Ordinary bounded host/container/service operations may proceed only inside already accepted task authority.
- Whole-host reboot, whole Docker-engine restart, Unraid OS upgrade, disk formatting, broad share/appdata deletion, and broad routing/firewall/default-gateway/DNS changes require explicit user approval.
- A recovery action that itself crosses a user gate remains gated.
- Derived live host inventory is observational and regenerable; it is not a second canonical truth store.

Current capability must be read back. This reference does not claim that M03 host-control transports are already delivered.
