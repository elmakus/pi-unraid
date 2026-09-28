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

## R01 correction

- R01 found that the GREEN path could commit with an omitted required core-probe set.
- Corrected transaction API now fails closed before leaving `armed` unless all five required local core probes are present exactly once; remote probes remain additive and preserve the candidate-contract blocking policy.
- Added empty/missing/duplicate probe regression coverage and repaired RED-path fixtures to retain the complete required core set.
- Corrected implementation subject: `4f4cea1fd03100a0bca5353bf46bd91e6526a442`.
- Tower non-temporary checkout focused immediate-acceptance + transaction-guard suite: 12/12 GREEN.
- Full repository unit suite: 490/490 GREEN.
- `git diff --check`: GREEN (command chain exited 0).
- No production mutation was performed by this correction; the prior read-only production baseline remains the production evidence for this Card.
