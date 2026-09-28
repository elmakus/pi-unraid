# M06-T03 correction evidence — bounded Update + Verify fallback

Date: 2026-09-29
Implementation subject: `a05ca3165a674c1e84a15f3d35f0fd1ecd6b6e06`

R02 showed that a restartable stock-update polling primitive did not itself prove a crash-safe lifecycle binding from the stock DockerMan gesture to observer invocation/restart. The correction therefore selects the Card-authorized single project `Update + Verify` fallback instead of relying on the stock gesture.

The fallback validates the exact durable armed binding before allowing the update trigger, owns the update trigger itself, and remains synchronously attached to the observer/immediate-acceptance transaction until a terminal result or fail-closed error. This removes the unproven external gesture-to-observer wakeup assumption. Authoritative Docker inspect remains the observation authority; predecessor/no-container are transient, the exact candidate enters immediate acceptance, and a third digest fails closed.

Tower verification from `/mnt/user/appdata/pwv2-m06t03-review` outside the system temporary directory:
- focused DockerMan binding / Update + Verify suite: 8/8 GREEN;
- full repository unit suite: 498/498 GREEN;
- `git diff --check`: GREEN.
- coverage proves trigger ordering after exact guard validation, trigger-to-observer ownership, predecessor -> missing-container -> candidate convergence, stale binding rejection before triggering update, ambiguous digest rejection, and terminal readback behavior.

No production `:accepted` movement, production restart/cutover/rollback, DockerMan core patch or custom dashboard was performed.
