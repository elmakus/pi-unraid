# M03 Pi → Codex-LB integration — proposal

Status: JIT execution contract for approved Card M03-T03
Date: 2026-09-23

## Why

M03-T03 introduces a security-sensitive client-secret boundary and persistent Pi provider configuration before production cutover. The accepted M03 authority requires generic `openai-responses` access to the independently deployed Codex-LB service, durable/idempotent Pi-side configuration, clear dependency-failure diagnostics, and no secret leakage. These contracts are sufficiently stateful and failure-sensitive to freeze before implementation.

## Authority

- `planning/MASTER_PLAN.md#M03 — Codex-LB-integrated on-Unraid acceptance and recoverable handoff`, especially M03-W2
- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M03-T03.md`
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-001/002/004/005/011/022/023/024
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md`
- accepted M03-T02 result and its GREEN independent review

## Change

Add the minimum Pi-side integration contract for:
1. a host/runtime secret-file source that is mounted only as a dedicated client secret and never rendered into Compose output;
2. persistent `~/.pi/agent/models.json` provider materialization using `openai-responses` → Codex-LB `/v1` with environment-based key resolution;
3. idempotent preservation of existing valid user model configuration;
4. separate provider diagnostics that do not redefine Pi runtime/service health;
5. disposable validation of valid, missing/invalid-secret, unreachable-endpoint and recreation/persistence behavior.

## Non-goals

- production Pi deployment or production Pi path creation;
- real model completion or direct Pi ChatGPT/Codex OAuth;
- Codex-LB source/config/account mutation;
- pooled OAuth/token material in Pi;
- model discovery extensions;
- workstation coupling;
- Docker socket, host-root, unrelated-appdata mounts or inbound SSH.
