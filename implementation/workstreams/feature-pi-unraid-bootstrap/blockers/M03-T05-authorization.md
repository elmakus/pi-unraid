# M03-T05 authorization blocker

- Card: `M03-T05 — Production recovery, restart and final technical handoff`
- Date: 2026-09-23
- Status: **WAITING_USER_AUTHORIZATION**
- Origin: post-M03-T04 router continuation / Execution Prep

## Why execution is blocked

M03-T04 is terminal GREEN. M03-T05 is now the next planned Card, but its accepted Card contract and Master Plan require explicit authorization before the material production recovery mutations owned by this Card.

The earlier M03-T04 authorization is deliberately bounded to M03-T04 and explicitly excludes M03-T05 recovery/disruptive work. It therefore cannot be reused.

## Authorization requested now

The smallest next authorization covers M03-T05 production recovery work that does **not** require a Docker-wide or host restart:

- execute the documented production update operation with exact post-write readback;
- exercise a controlled failed latest-stable Pi runtime candidate and verify LKG/seed recovery without durable-state loss;
- exercise the retained previous-deployment rollback and verify Pi home/projects/worktrees remain unchanged;
- exercise planned stop/restart/update behavior and native-session resume;
- perform bounded diagnostics/log-retention readback;
- perform controlled Codex-LB dependency outage/restart/recreation checks required by the Card while preserving Codex-LB's independent persistent data and without source/product redesign;
- record routing/multi-account behavior and its accepted continuation-state limitation.

Every material write remains bounded to the Card and requires readback/sanitized evidence.

## Still excluded from this authorization

Docker-wide restart, Unraid host restart, or any similarly broad interruption remains behind the Card's **separate explicit disruptive-restart authorization/window** and is not requested at this stop.

No M03-T05 production mutation has been executed while this gate is unresolved.

## Return route

After explicit user authorization for the bounded scope above, Execution Prep may reconcile M03-T05 from blocked to ready and return through the router to Execution. The later Docker-wide/host-restart gate remains independent.
