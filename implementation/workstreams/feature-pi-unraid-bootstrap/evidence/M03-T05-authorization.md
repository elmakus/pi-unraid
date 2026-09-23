# M03-T05 bounded production-recovery authorization

- Card: `M03-T05 — Production recovery, restart and final technical handoff`
- Date: 2026-09-23
- Authority: explicit current user authorization
- Status: **AUTHORIZED — bounded recovery scope**

## Authorized now

The user explicitly authorized M03-T05 **without Docker-wide/host restart**.

Authorized production operations:
- normal `scripts/update.sh` production update with exact readback;
- controlled failed latest-stable runtime candidate with LKG/seed recovery proof;
- retained previous-deployment rollback with durable-mount preservation proof;
- planned stop/restart/update and native-session resume checks;
- bounded diagnostics/log-retention readback;
- controlled Codex-LB dependency outage/restart/recreation checks within the existing deployment, preserving Codex-LB persistent data and without product/source redesign;
- sanitized routing/multi-account behavior readback.

Every material mutation requires post-write/readback evidence.

## Not authorized

The following remain behind a separate explicit gate:
- Docker-wide restart;
- Unraid host restart;
- any similarly broad interruption.

No later authorization may be inferred from this record.
