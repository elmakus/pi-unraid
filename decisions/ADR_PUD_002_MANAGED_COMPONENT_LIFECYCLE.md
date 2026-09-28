# Decision — Managed component registry and narrow compatibility gate

- Decision ID: `ADR-PUD-002`
- Date: `2026-09-28`
- Status: `accepted`
- Definition subject: `paseo-update-distribution@10`
- Supersedes for this scope: the blanket all-global-components-together implication of PGR-REQ-055

## Decision

One managed-component registry/inventory is the durable update membership authority. Durable installation intent and registry membership are changed together through an agent-operated managed-component lifecycle.

Only Paseo↔Pi participates in combinatorial compatibility search. Node is derived from Paseo and checked against Pi constraints. Ordinary Pi extensions and developer tools update independently and may individually remain on their previous accepted version if their newest version cannot be installed/built. Extension-specific functional failure does not automatically block core Paseo/Pi Update Ready. Playwright+Chromium is one derived update unit.

New managed components default to the least complex independent class and are promoted into the core compatibility gate only after demonstrated core startup/API coupling.

## Consequences

The resolver remains small and bounded instead of becoming a universal environment SAT solver. Agents, not the human operator, are responsible for using the managed add/remove helper. Registry/runtime drift is a failed managed change, not something silently adopted.
