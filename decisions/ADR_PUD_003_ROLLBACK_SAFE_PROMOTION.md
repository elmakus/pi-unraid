# Decision — Rollback-safe promotion and bounded automatic recovery

- Decision ID: `ADR-PUD-003`
- Date: `2026-09-28`
- Status: `accepted`
- Definition subject: `paseo-update-distribution@10`

## Decision

A candidate becomes normally update-ready only after exact-digest GitHub validation, Tower-specific disposable validation, dedicated Codex-LB smoke, and a direct rollback-safety proof against representative current persistent state.

Production keeps a known-good ledger containing current plus exactly two previous immutable production-known-good image identities. The user chooses when to initiate cutover. That cutover and immediate acceptance are one bounded transaction: immediate RED automatically restores the previous known-good image and verifies recovery; immediate GREEN ends automatic rollback authority.

A future irreversible persistent-state migration that cannot pass the ordinary `A -> C -> A` proof is not an ordinary update. It remains held back until handled through a separately authorized maintenance procedure.

## Consequences

Image rollback is not assumed to equal state rollback. Direct skipping over intermediate candidates is permitted only when the actual production baseline -> selected candidate transition is proven. Later runtime failures after acceptance never trigger autonomous rollback.
