# Decision — Paseo is the Pi execution/UI substrate on Unraid

- Decision ID: `ADR-PGR-001`
- Date: `2026-09-24`
- Status: `accepted`
- Definition subject: `paseo-gui-runtime@2`

## Decision

Use one production Paseo container as the normal Android/PC GUI and execution surface, derived from the exact resolved official stable `ghcr.io/getpaseo/paseo` image, with Pi and required tooling installed in the child image and Pi spawned by Paseo on demand. Preserve native HOME/config paths, persist the full Paseo HOME as sensitive convenience state, configure Paseo's worktree root outside protected HOME, use Relay as the initial access path, and include an in-container Chromium/Playwright browser baseline. Paseo desktop-hosted Browser Tools are complementary only.

Git/PW state remains canonical; Paseo sessions/history/HOME are not project authority.

## Consequences

The old standalone Pi container is transitional only and is retired after Paseo GREEN. Native Paseo capabilities are preferred over custom UI duplication. Browser/session convenience state is backed up but may be lost without losing legal project continuation. Host-mounted ownership must be Unraid-compatible, but the deployment must respect the official Paseo image's internal non-root user contract rather than blindly forcing the legacy standalone-Pi UID model.
