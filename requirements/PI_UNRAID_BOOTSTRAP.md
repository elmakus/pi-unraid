# Pi on Unraid — Phase 1 Bootstrap Requirements

Revision: `R3`
Status: `approved`
Updated: `2026-09-23`

Definition subject: `pi-unraid-bootstrap@R3`
Workstream: `feature-pi-unraid-bootstrap`
Source brainstorming: `brainstorming/PI_UNRAID_BRAINSTORM.md`
Verified evidence:
- `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`
- `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`

## Goal / target state

Establish a reproducible, always-available **minimal Pi Coding Agent bootstrap on Unraid** that can be used through Pi's native terminal/TUI path, with durable Pi session/config state, ChatGPT/Codex access through Codex-LB, and normal Git/GitHub development capability.

This Phase 1 exists to prove the base Pi runtime and persistence model before any Web UI, Android client, web-search, subagent, MCP, browser-automation or other extension stack is selected.

## Product / system requirements

| ID | Requirement | Priority | Source / decision | Status |
|---|---|---|---|---|
| PIB-REQ-001 | The deployment MUST run Pi in Docker on Unraid and be reproducible from repository-owned deployment source, with `compose.yaml` as the deployment source of truth. | MUST | G21, G39, G95 | accepted |
| PIB-REQ-002 | The Pi service MUST use a persistent non-root user home mapped from `/mnt/user/appdata/pi-unraid/home` to `/home/pi`, preserving Pi's native `~/.pi/agent` state. | MUST | G13, G14, G45 | accepted |
| PIB-REQ-003 | The service user MUST support configurable UID/GID alignment with Unraid shares and MUST have sudo available for legitimate runtime package/tool installation without making the container itself root-operated by default. | MUST | G14, G40, G116 | accepted |
| PIB-REQ-004 | From the first real Pi model interaction, Phase 1 MUST use Codex-LB as the required ChatGPT/Codex access and OAuth/account-routing layer. Direct Pi built-in ChatGPT/Codex OAuth MUST NOT be required or performed for Phase 1 acceptance; ChatGPT/Codex account login, token storage and refresh are owned by Codex-LB. | MUST | user redefinition 2026-09-23; PIB-ADR-005; Codex-LB integration research | accepted |
| PIB-REQ-005 | Pi session history MUST persist across normal container restart/recreation, and the user MUST be able to create, exit and later resume a native Pi session through the terminal/TUI path. | MUST | G19, G61, G86; verified research | accepted |
| PIB-REQ-006 | The container MUST expose the canonical projects root as `/projects` from host `/mnt/user/projects`, with canonical repositories normally one directory directly beneath that root. | MUST | G07, G35, G87 | accepted |
| PIB-REQ-007 | The container MUST expose the dedicated worktree root as `/worktrees` from host `/mnt/user/pi-worktrees`; the runtime MUST support operating in existing repositories/worktrees without hard-coding worktree lifecycle policy. | MUST | G03, G08, G36, G43, G62 | accepted |
| PIB-REQ-008 | The base image MUST include the common development tooling accepted for normal agent work: a Pi-supported Node runtime, Python, Git, OpenSSH client, GitHub CLI, curl, jq, ripgrep, fd/find tooling, archive utilities, standard build toolchain and Git LFS. | MUST | G39, G100; verified research | accepted |
| PIB-REQ-009 | Git transport to GitHub MUST use SSH with strict host-key verification and persistent `known_hosts`; GitHub CLI MUST be available for GitHub API/PR/check/release operations. | MUST | G05, G112 | accepted |
| PIB-REQ-010 | The Pi service user MUST have persistent configurable Git identity, normal outbound Internet access, and technical authority to perform normal authorized Git/GitHub operations without per-command local approval gates. | MUST | G06, G70, G104, G106 | accepted |
| PIB-REQ-011 | The base deployment MUST NOT mount the Docker socket, host root or unrelated appdata, and MUST NOT run an inbound SSH server merely for shell/TUI access. | MUST | initial scope, G14, G24, G111 | accepted |
| PIB-REQ-012 | Direct terminal/TUI fallback MUST be available through the Unraid/Docker exec path; a Web UI is not required for Phase 1 acceptance. | MUST | G15, G42, G86, G121 | accepted |
| PIB-REQ-013 | The deployment MUST be configured for automatic start after Unraid/Docker restart with `unless-stopped`-style behavior and MUST use timezone `Europe/Zurich`. Phase 1 acceptance does not require executing a Docker-wide or host restart; the residual risk of not live-verifying that broad restart path is explicitly accepted by the user. | MUST | G50, G115; user acceptance-scope change 2026-09-23 | accepted |
| PIB-REQ-014 | Normal Pi startup MUST target the latest stable Pi release, excluding prerelease/nightly channels. A failed runtime update MUST fall back to the last known working Pi runtime rather than making the service unavailable. | MUST | G16, G46, G53, G105 | accepted |
| PIB-REQ-015 | The deployment MUST preserve a previous known-working Docker image/deployment candidate so a broken image/dependency/startup change can be rolled back without losing persistent home, repositories or worktrees. | MUST | G119 | accepted |
| PIB-REQ-016 | Runtime-installed tools are allowed for experimentation, but any tool that becomes part of the normal expected environment MUST be captured in repository/image source for reproducibility. | MUST | G17, G40 | accepted |
| PIB-REQ-017 | Docker/backend logs MUST have bounded rotation/retention, and normal deployment diagnostics MUST remain readable without requiring a full metrics stack. | MUST | G44, G98 | accepted |
| PIB-REQ-018 | The persistent Pi home, including normal interactive credential stores, MUST remain within the user's ordinary Unraid appdata backup scope; no Pi-specific secret-backup exclusion/encryption requirement is added by this project. | MUST | G20, G45, G51, G123 | accepted |
| PIB-REQ-019 | The existing `chatgpt-ce-workstation` deployment MUST remain independent and unchanged; Phase 1 MUST NOT depend on its runtime, secrets, routing stack or availability. | MUST | initial scope; relationship-to-workstation decision | accepted |
| PIB-REQ-020 | The deployment MUST provide one normal user-facing update operation/script that handles the expected repository/image/deployment update path, while lower-level Compose commands remain available for recovery/development. | MUST | G96 | accepted |
| PIB-REQ-021 | Planned service/container shutdown for restart or update MUST give active Pi processes a bounded graceful-stop opportunity to persist native session state before forced termination; persisted sessions MUST remain resumable afterward. | MUST | G102 | accepted |
| PIB-REQ-022 | Pi → Codex-LB requests MUST use a dedicated authenticated Codex-LB client credential supplied through an approved runtime/host secret path. The credential MUST survive normal Pi restart/recreation as needed for service continuity and MUST NOT be committed, baked into an image, or emitted into ordinary logs/evidence. | MUST | user redefinition 2026-09-23; PIB-ADR-005; Codex-LB integration research | accepted |
| PIB-REQ-023 | Codex-LB MUST own ChatGPT/Codex account selection, OAuth refresh and multi-account routing for Phase 1. Pi MUST NOT import or manage pooled account OAuth tokens. Acceptance MUST NOT claim seamless migration of account-owned continuation state when Codex-LB cannot safely move that continuation; a fresh conversation may route through another eligible account. | MUST | user redefinition 2026-09-23; PIB-ADR-005; Codex-LB integration research | accepted |
| PIB-REQ-024 | Codex-LB MUST remain an independently deployed and persistent service/dependency, separate from the Pi container and from `chatgpt-ce-workstation`. Pi MUST NOT mount Codex-LB's data directory. Before Phase 1 acceptance, the selected Codex-LB deployment MUST have verified health, compatible client behavior, persistent OAuth/account state and a current-enough reviewed deployment baseline. | MUST | user redefinition 2026-09-23; PIB-ADR-005; Codex-LB integration research | accepted |

## Constraints

- Current official Pi npm installation requires **Node.js 22.19+**; current official Plain Docker guidance uses a Node 24 Debian image. Planning may choose a current Pi-supported Node image, but MUST not fall below Pi's documented runtime requirement.
- Current Pi package is `@earendil-works/pi-coding-agent`.
- Pi's default persistent config/auth/session root is `~/.pi/agent`; this Definition intentionally keeps the native path under persistent `/home/pi` rather than relocating it.
- Pi's built-in ChatGPT/Codex OAuth remains an upstream capability, but Phase 1 deliberately does **not** use it as the bootstrap authentication path.
- ChatGPT/Codex OAuth account state for Phase 1 is owned by the independently persistent Codex-LB deployment; Pi sees one authenticated provider endpoint and does not receive pooled account refresh/access tokens.
- Pi connects to Codex-LB through a supported OpenAI Responses-compatible endpoint. The accepted research identifies Pi `openai-responses` → Codex-LB `/v1` as the minimal compatible seam; the native Pi `openai-codex-responses` path is not used with an opaque Codex-LB client key.
- Codex-LB multi-account routing is in scope only as the access-layer behavior needed by Pi. Reimplementing or extending Codex-LB's routing product is not part of this project.
- Normal project identity is Git/GitHub-first. Local-only non-Git directories are not first-class normal projects for the intended operating model.
- Active implementation is not intended to occur directly on `main`; branch/worktree lifecycle policy belongs to higher-level workflow rather than the Pi base runtime.

## Non-goals

The following are **not part of Phase 1 acceptance** and MUST NOT be pulled into the Phase 1 plan merely because they are desired later:

- Web UI selection or implementation;
- native Android client or PWA;
- HTTPS/reverse-proxy/UI ingress design;
- file-upload/session-attachment system;
- web search / full-page research extension;
- subagent extension/orchestration;
- MCP client extension selection/configuration;
- browser automation/computer use;
- context-compaction extension selection;
- notification backend;
- OpenCodex or a new/replacement account-router implementation;
- implementation or redesign of the Codex-LB dashboard/account-management product beyond configuration/integration required for Pi;
- Muse integration;
- `chatgpt-web/*` provider adapter;
- embedding Project Workflow V2 into Pi;
- broad Unraid host administration through MCP/SSH;
- automated GitHub new-project skill/UI;
- a prescribed real coding benchmark as a formal bootstrap acceptance gate.

Those items remain later follow-on Research/Definition scopes after the user has personally evaluated the base Pi bootstrap.

## Global invariants

- Persistent state MUST survive normal image rebuild/recreate.
- Container/image rollback MUST NOT roll back or destroy durable Pi home state.
- Repository/worktree mounts MUST not be silently remapped to a different workspace when explicitly selected.
- Runtime freshness MUST NOT be achieved by consuming beta/nightly/prerelease Pi builds automatically.
- Secrets MUST never be committed to this repository or baked into the image.
- Existing project repositories MUST not be modified merely because they are mounted or cloned.
- Phase 1 MUST remain independent of the existing ChatGPT CE workstation.
- Implementation MUST prefer the least-complex design that satisfies these accepted requirements; later extension architecture is not justification for Phase 1 complexity.

## External contracts / dependencies

- Unraid Docker/Compose environment.
- Host paths:
  - `/mnt/user/appdata/pi-unraid/home` → `/home/pi`
  - `/mnt/user/projects` → `/projects`
  - `/mnt/user/pi-worktrees` → `/worktrees`
- GitHub access through SSH + GitHub CLI.
- Existing independently deployed Codex-LB service on Unraid, with its own persistent OAuth/account data and an authenticated Pi client path.
- Dedicated Pi → Codex-LB client credential supplied outside Git/image source.
- Current stable Pi package/runtime behavior as evidenced in `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`.
- Current Pi → Codex-LB compatibility/OAuth/routing facts as evidenced in `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`.

## Data integrity / idempotency / security constraints

- Persistent-home initialization MUST be idempotent and MUST not overwrite an existing working Pi home on restart/update.
- Update/fallback logic MUST preserve Pi session/config/client-integration state. ChatGPT/Codex OAuth account state remains independently persistent in Codex-LB and MUST NOT be restored backward or copied into Pi by Pi runtime/image rollback.
- GitHub SSH host verification MUST remain enabled.
- Container startup/rebuild MUST avoid creating root-owned repository/worktree files during normal Pi operation.
- Runtime/package update failure MUST fail safely into a usable prior Pi runtime when that fallback is available.
- Deployment update/rollback MUST not delete repository/worktree data.
- Normal backup behavior follows the user's existing Unraid appdata backup authority.

## Acceptance-level requirements

Phase 1 Definition is satisfied when planning/execution can prove all of the following without requiring any later Web UI/extension scope:

1. The repository-owned deployment builds and starts on Unraid.
2. The production deployment has the accepted automatic restart policy (`unless-stopped`-style) and timezone configured/read back; a Docker-wide or host restart is explicitly not required as a Phase 1 acceptance exercise, and the corresponding unverified broad-restart risk is user-accepted.
3. `pi` runs from the terminal/TUI path using a current stable Pi release on a supported Node runtime.
4. Codex-LB has usable authorized ChatGPT/Codex account capacity and Pi completes a real model interaction through the authenticated Codex-LB path without performing direct Pi ChatGPT/Codex OAuth.
5. Pi → Codex-LB access survives a normal Pi container restart and image/container recreation using the approved persistent/runtime client configuration, while Codex-LB OAuth/account state remains independently persistent and does not require import into Pi.
6. A Pi session can be created, exited and resumed from persistent session state after restart/recreation.
7. Pi can read/write a deliberately selected repository beneath `/projects` with acceptable host ownership/permissions under the configured non-root UID/GID.
8. Pi can operate in an explicitly selected existing worktree beneath `/worktrees`.
9. Git SSH operations and `gh` authentication/normal API operations work from the service user environment.
10. Strict GitHub host-key verification is active.
11. The container has no Docker-socket, host-root or unrelated-appdata mount and exposes no dedicated inbound SSH shell service.
12. Required base development tools, including Git LFS, are available.
13. A failed Pi latest-stable update has a defined/testable fallback path to the last known working Pi runtime without loss of persistent home state.
14. A previous known-working deployment image/candidate can be selected for rollback without loss of persistent data.
15. Logs are bounded by rotation/retention.
16. The normal user-facing update operation is documented and executable.
17. Existing ChatGPT CE workstation operation is unaffected.
18. A planned service restart/update provides a bounded graceful-stop path, and a previously persisted Pi session remains resumable afterward.
19. No prescribed real coding benchmark is required for workflow acceptance; after these technical checks, the user performs their own real-world Pi evaluation and decides whether later scopes proceed.
20. With the configured Codex-LB account pool, normal Pi requests are routed by Codex-LB according to its accepted routing configuration; evidence explicitly records that account-owned continuation state is not guaranteed to migrate transparently across accounts.
21. Pi and Codex-LB remain separately persistent/deployed: Pi restart/recreation does not mount or mutate Codex-LB data, Codex-LB health/compatibility/persistence are verified, and the existing ChatGPT CE workstation remains outside this dependency chain.

## R3 acceptance-scope change

On 2026-09-23 the user explicitly chose to skip the remaining Docker-wide/host restart exercise. This does **not** claim that such a restart was tested. It changes Phase 1 acceptance so configuration/readback of the automatic restart policy is sufficient for this project phase, while the residual broad-restart behavior remains unverified and user-accepted. All completed M01/M02/M03 evidence remains valid and is not rewritten.

## Definition completeness

Definition Complete: **GREEN**

- target state is explicit;
- material MUST requirements are enumerated;
- Phase 1 non-goals prevent later extension scope creep;
- verified current Pi runtime/session facts and current Pi → Codex-LB compatibility/OAuth/routing facts are incorporated;
- strategic choices needed before planning, including Codex-LB as the mandatory Phase 1 access layer, are captured in accepted decision records;
- completed M01/M02 implementation/evidence remain valid historical checkpoints; R3 preserves the completed R2/M03 evidence while removing the previously mandatory disruptive-restart acceptance exercise;
- no unresolved user/product choice remains that can materially alter the Phase 1 planning architecture; the user explicitly chose to omit Docker-wide/host restart testing from Phase 1 acceptance;
- implementation-specific mechanics such as the exact updater/fallback script design remain properly delegated to Strategic Planning rather than being hidden product decisions.

## Downstream coverage

Strategic Planning MUST provide requirement coverage for every `PIB-REQ-xxx` requirement and the acceptance-level outcomes above.

No Master Plan is created by this Definition role.
