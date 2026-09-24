# Decision — Paseo is the Pi execution/UI substrate on Unraid

- Decision ID: `ADR-PGR-001`
- Date: `2026-09-24`
- Status: `definition-active`
- Definition subject: `paseo-gui-runtime@2`

## Decision

Use one production Paseo container as the normal Android/PC GUI and execution surface, with Pi installed inside the image and spawned by Paseo on demand. Preserve native HOME/config paths, persist the full Paseo HOME as sensitive convenience state, keep Git workspaces outside HOME, use Relay as the initial access path, and include a practical development/browser baseline.

Git/PW state remains canonical; Paseo sessions/history/HOME are not project authority.

## Consequences

The old standalone Pi container is transitional only and is retired after Paseo GREEN. Native Paseo capabilities are preferred over custom UI duplication. Browser/session convenience state is backed up but may be lost without losing legal project continuation.
