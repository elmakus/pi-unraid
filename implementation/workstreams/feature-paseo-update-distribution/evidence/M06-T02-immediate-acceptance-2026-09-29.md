# M06-T02 execution evidence — immediate acceptance transaction

Date: 2026-09-29
Implementation subject: `3ce2d829972227abc1752d243901b3c1572fb8b0`

- Added bounded immediate acceptance orchestration over the M06-T01 durable guard.
- GREEN requires all local core probes and transitions to committed, after which rollback transitions are forbidden.
- Injected/local-probe RED transitions to rolling-back, restores only the exact bound predecessor, verifies recovery, then records recovered.
- Failed recovery remains fail-closed in rolling-back.
- Transient remote-service outage is non-blocking unless explicitly marked candidate-contract blocking.
- Focused transaction-guard/promotion/immediate-acceptance suite: 22/22 GREEN.
- Full repository unit suite: 489/489 GREEN.
- `git diff --check`: GREEN.
- Read-only production baseline: `pi-unraid-paseo-1` running/healthy on `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`; real transaction guard absent. No production accepted-channel move, restart, cutover or rollback was performed.
