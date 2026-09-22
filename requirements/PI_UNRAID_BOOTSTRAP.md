# Pi on Unraid — Phase 1 Bootstrap Requirements

Revision: `R1`
Status: `approved`
Updated: `2026-09-22`

Definition subject: `pi-unraid-bootstrap@R1`
Workstream: `feature-pi-unraid-bootstrap`
Source brainstorming: `brainstorming/PI_UNRAID_BRAINSTORM.md`
Verified evidence: `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`

## Goal / target state

Establish a reproducible, always-available **minimal Pi Coding Agent bootstrap on Unraid** that can be used through Pi's native terminal/TUI path, with durable authentication/session state and normal Git/GitHub development capability.

This Phase 1 exists to prove the base Pi runtime and persistence model before any Web UI, Android client, web-search, subagent, MCP, browser-automation or other extension stack is selected.

## Product / system requirements

| ID | Requirement | Priority | Source / decision | Status |
|---|---|---|---|---|
| PIB-REQ-001 | The deployment MUST run Pi in Docker on Unraid and be reproducible from repository-owned deployment source, with `compose.yaml` as the deployment source of truth. | MUST | G21, G39, G95 | accepted |
| PIB-REQ-002 | The Pi service MUST use a persistent non-root user home mapped from `/mnt/user/appdata/pi-unraid/home` to `/home/pi`, preserving Pi's native `~/.pi/agent` state. | MUST | G13, G14, G45 | accepted |
| PIB-REQ-003 | The service user MUST support configurable UID/GID alignment with Unraid shares and MUST have sudo available for legitimate runtime package/tool installation without making the container itself root-operated by default. | MUST | G14, G40, G116 | accepted |
| PIB-REQ-004 | Phase 1 MUST support one ChatGPT Plus/Pro account authenticated directly through Pi's built-in ChatGPT/Codex login path, with OAuth state surviving container restart/recreation through persistent home state. | MUST | G30, G51, G86; verified research | accepted |
| PIB-REQ-005 | Pi session history MUST persist across normal container restart/recreation, and the user MUST be able to create, exit and later resume a native Pi session through the terminal/TUI path. | MUST | G19, G61, G86; verified research | accepted |
| PIB-REQ-006 | The container MUST expose the canonical projects root as `/projects` from host `/mnt/user/projects`, with canonical repositories normally one directory directly beneath that root. | MUST | G07, G35, G87 | accepted |
| PIB-REQ-007 | The container MUST expose the dedicated worktree root as `/worktrees` from host `/mnt/user/pi-worktrees`; the runtime MUST support operating in existing repositories/worktrees without hard-coding worktree lifecycle policy. | MUST | G03, G08, G36, G43, G62 | accepted |
| PIB-REQ-008 | The base image MUST include the common development tooling accepted for normal agent work: a Pi-supported Node runtime, Python, Git, OpenSSH client, GitHub CLI, curl, jq, ripgrep, fd/find tooling, archive utilities, standard build toolchain and Git LFS. | MUST | G39, G100; verified research | accepted |
| PIB-REQ-009 | Git transport to GitHub MUST use SSH with strict host-key verification and persistent `known_hosts`; GitHub CLI MUST be available for GitHub API/PR/check/release operations. | MUST | G05, G112 | accepted |
| PIB-REQ-010 | The Pi service user MUST have persistent configurable Git identity, normal outbound Internet access, and technical authority to perform normal authorized Git/GitHub operations without per-command local approval gates. | MUST | G06, G70, G104, G106 | accepted |
| PIB-REQ-011 | The base deployment MUST NOT mount the Docker socket, host root or unrelated appdata, and MUST NOT run an inbound SSH server merely for shell/TUI access. | MUST | initial scope, G14, G24, G111 | accepted |
| PIB-REQ-012 | Direct terminal/TUI fallback MUST be available through the Unraid/Docker exec path; a Web UI is not required for Phase 1 acceptance. | MUST | G15, G42, G86, G121 | accepted |
| PIB-REQ-013 | The deployment MUST start automatically after Unraid/Docker restart with `unless-stopped`-style behavior and MUST use timezone `Europe/Zurich`. | MUST | G50, G115 | accepted |
| PIB-REQ-014 | Normal Pi startup MUST target the latest stable Pi release, excluding prerelease/nightly channels. A failed runtime update MUST fall back to the last known working Pi runtime rather than making the service unavailable. | MUST | G16, G46, G53, G105 | accepted |
| PIB-REQ-015 | The deployment MUST preserve a previous known-working Docker image/deployment candidate so a broken image/dependency/startup change can be rolled back without losing persistent home, repositories or worktrees. | MUST | G119 | accepted |
| PIB-REQ-016 | Runtime-installed tools are allowed for experimentation, but any tool that becomes part of the normal expected environment MUST be captured in repository/image source for reproducibility. | MUST | G17, G40 | accepted |
| PIB-REQ-017 | Docker/backend logs MUST have bounded rotation/retention, and normal deployment diagnostics MUST remain readable without requiring a full metrics stack. | MUST | G44, G98 | accepted |
| PIB-REQ-018 | The persistent Pi home, including normal interactive credential stores, MUST remain within the user's ordinary Unraid appdata backup scope; no Pi-specific secret-backup exclusion/encryption requirement is added by this project. | MUST | G20, G45, G51, G123 | accepted |
| PIB-REQ-019 | The existing `chatgpt-ce-workstation` deployment MUST remain independent and unchanged; Phase 1 MUST NOT depend on its runtime, secrets, routing stack or availability. | MUST | initial scope; relationship-to-workstation decision | accepted |
| PIB-REQ-020 | The deployment MUST provide one normal user-facing update operation/script that handles the expected repository/image/deployment update path, while lower-level Compose commands remain available for recovery/development. | MUST | G96 | accepted |
| PIB-REQ-021 | Planned service/container shutdown for restart or update MUST give active Pi processes a bounded graceful-stop opportunity to persist native session state before forced termination; persisted sessions MUST remain resumable afterward. | MUST | G102 | accepted |

## Constraints

- Current official Pi npm installation requires **Node.js 22.19+**; current official Plain Docker guidance uses a Node 24 Debian image. Planning may choose a current Pi-supported Node image, but MUST not fall below Pi's documented runtime requirement.
- Current Pi package is `@earendil-works/pi-coding-agent`.
- Pi's default persistent config/auth/session root is `~/.pi/agent`; this Definition intentionally keeps the native path under persistent `/home/pi` rather than relocating it.
- Current Pi ChatGPT subscription authentication uses the built-in ChatGPT Plus/Pro (Codex) login path and persists interactive auth in `~/.pi/agent/auth.json`.
- Phase 1 uses one direct ChatGPT account only; no account pooling/router is introduced.
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
- multi-account routing, Codex-LB or OpenCodex;
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
- One ChatGPT Plus/Pro account through Pi's built-in subscription authentication.
- Current stable Pi package/runtime behavior as evidenced in `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`.

## Data integrity / idempotency / security constraints

- Persistent-home initialization MUST be idempotent and MUST not overwrite an existing working Pi home on restart/update.
- Update/fallback logic MUST preserve current auth/session/config state.
- GitHub SSH host verification MUST remain enabled.
- Container startup/rebuild MUST avoid creating root-owned repository/worktree files during normal Pi operation.
- Runtime/package update failure MUST fail safely into a usable prior Pi runtime when that fallback is available.
- Deployment update/rollback MUST not delete repository/worktree data.
- Normal backup behavior follows the user's existing Unraid appdata backup authority.

## Acceptance-level requirements

Phase 1 Definition is satisfied when planning/execution can prove all of the following without requiring any later Web UI/extension scope:

1. The repository-owned deployment builds and starts on Unraid.
2. The Pi container/service returns after host/Docker restart according to the automatic restart policy.
3. `pi` runs from the terminal/TUI path using a current stable Pi release on a supported Node runtime.
4. One ChatGPT Plus/Pro account can complete Pi login on the headless Unraid deployment.
5. Authentication survives a normal container restart and image/container recreation that preserves the configured home.
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

## Definition completeness

Definition Complete: **GREEN**

- target state is explicit;
- material MUST requirements are enumerated;
- Phase 1 non-goals prevent later extension scope creep;
- verified current Pi runtime/auth/session facts are incorporated;
- strategic choices needed before planning are captured in accepted decision records;
- no unresolved user/product choice remains that can materially alter the Phase 1 planning architecture;
- implementation-specific mechanics such as the exact updater/fallback script design remain properly delegated to Strategic Planning rather than being hidden product decisions.

## Downstream coverage

Strategic Planning MUST provide requirement coverage for every `PIB-REQ-xxx` requirement and the acceptance-level outcomes above.

No Master Plan is created by this Definition role.
