# M03 operator/recovery handoff — R3 finalization candidate

- Milestone: `M03 — Codex-LB-integrated on-Unraid acceptance and recoverable handoff`
- Definition: `pi-unraid-bootstrap@R3`
- Status: **technical handoff consolidated; M03-T06 REQUIRED independent review pending before milestone terminal close**
- Production mutation performed by M03-T06: **none**
- Broad Docker/host restart acceptance exercise: **not performed and not required by R3**

## Current accepted operating model

Pi runs as the repository-owned Docker/Compose service on Unraid with persistent `/home/pi`, canonical `/projects` and `/worktrees`, non-root UID/GID alignment, native terminal/TUI access, strict GitHub SSH trust, GitHub CLI and the accepted development-tool inventory.

ChatGPT/Codex model access is through the independently deployed Codex-LB service using Pi's authenticated `openai-responses` provider path. Codex-LB owns pooled ChatGPT/Codex OAuth state, refresh and account routing. Pi does not own pooled OAuth tokens and has no direct-Pi-OAuth Phase 1 fallback.

The dedicated Pi client credential remains outside Git/image source and normal evidence. Codex-LB appdata remains separate from Pi appdata.

## Persistence and lifecycle

Accepted evidence shows:

- native Pi home/config/session state survives normal service/container recreation;
- a native Pi session can be reopened after recreation and after a planned graceful stop;
- latest-stable runtime failure preserves the accepted LKG path and durable state;
- the normal production update path is executable;
- actual retained-image rollback preserves Pi home/projects/worktrees rather than restoring them backward;
- bounded Docker logging remains active;
- Codex-LB outage/restart affects model access without destroying Pi runtime/session/Git state;
- ChatGPT CE workstation remains independent and unchanged by this project.

## Restart-policy limitation accepted in R3

Production readback proved the intended `unless-stopped`-style restart policy and `Europe/Zurich` timezone.

No Docker-wide restart or Unraid host restart was executed as a Phase 1 acceptance exercise. Therefore this handoff does **not** claim broad restart recovery was live-proven. PIB-ADR-007 records the user's explicit acceptance of that residual risk, and broad restart proof is not a Phase 1 completion blocker.

A later real-world Docker/host restart may provide opportunistic observation, but it is outside the required R3 acceptance surface.

## Failure-domain recovery

### 1. Pi runtime candidate failure

Use the accepted latest-stable/LKG/seed recovery path. Do not replace a working runtime with a failed candidate. Preserve Pi home and mounted repositories/worktrees.

### 2. Pi deployment image/config/startup failure

Use the retained previous deployment candidate/config transaction. Roll back replaceable image/config layers only; do not restore Pi home/projects/worktrees backward.

### 3. Codex-LB/model-access dependency failure

Treat provider/model failure separately from Pi runtime health. Preserve Pi service/session/Git state, recover Codex-LB under its own authority, and do not bypass the dependency with direct Pi ChatGPT/Codex OAuth. Account-owned continuation state is not guaranteed to migrate transparently across pooled accounts.

### 4. Persistent-data damage

Stop writes and use the existing Unraid backup/restore authority. Runtime/image rollback is not a persistent-data restore procedure. Pi and Codex-LB persistent stores remain separate.

## Evidence index

- M01 integrated environment: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-acceptance.md`
- M02 runtime/deployment lifecycle: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M02-acceptance.md`
- Codex-LB dependency/client boundary: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T02.md` + independent review
- Pi provider/secret integration: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T03.md` + REQUIRED review
- Production bootstrap/live functional acceptance: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T04.md` + independent review
- Non-disruptive production recovery: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T05-partial.md`
- R3 final coverage/reconciliation: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T06.md`
- R3 Definition/waiver: `requirements/PI_UNRAID_BOOTSTRAP.md` + `decisions/PIB_ADR_007_SKIP_DISRUPTIVE_RESTART_ACCEPTANCE.md`

## Completion boundary

Technical Phase 1 does not include a prescribed real-world coding benchmark. After terminal workflow close, practical Pi evaluation remains user-owned and any Web UI/extensions/subagents/MCP/browser/research additions require their own later accepted scope.

This handoff is part of the M03-T06 implementation subject and becomes terminal milestone handoff authority only after the REQUIRED independent Card review and normal milestone Close lifecycle complete.
