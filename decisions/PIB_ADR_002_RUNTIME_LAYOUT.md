# Decision — Native persistent-home Unraid runtime layout

- Decision ID: `PIB-ADR-002`
- Date: `2026-09-22`
- Status: `accepted`
- Authority: `user`
- Supersedes: `none`
- Related requirements: `PIB-REQ-001..013, PIB-REQ-016..019`
- Related milestone/card: `none`

## Context

The bootstrap needs durable Pi state, correct Unraid file ownership, access to canonical repositories/worktrees and sufficient developer tooling without granting broad host authority.

Pi natively stores auth/settings/sessions beneath `~/.pi/agent`, and current official documentation supports Plain Docker as a whole-process isolation pattern.

## Decision

Use a repository-owned Docker/Compose deployment with:

- persistent host `/mnt/user/appdata/pi-unraid/home` → container `/home/pi`;
- Pi's native `~/.pi/agent` state layout inside that home;
- non-root Pi service user with configurable UID/GID and sudo;
- `/mnt/user/projects` → `/projects`;
- `/mnt/user/pi-worktrees` → `/worktrees`;
- normal outbound Internet;
- GitHub SSH + GitHub CLI;
- strict SSH host verification;
- richer common developer base image, including Git LFS;
- no Docker socket, host-root mount, unrelated appdata mount or inbound SSH daemon.

The entire Pi home remains in the user's normal Unraid appdata backup scope, including normal interactive credential stores. No Pi-specific backup exclusion or additional encryption requirement is introduced.

## Rationale

This keeps Pi close to its native persistence model while fitting Unraid ownership and backup behavior. It avoids root-owned project files, preserves one durable user environment across rebuilds and provides the expected development surface without granting implicit host-administration capability.

## Alternatives considered

- Relocate Pi state to a custom `/config`: rejected in favor of native `~/.pi/agent` under persistent home.
- Run Pi as root: rejected to avoid ownership/permission problems on Unraid shares.
- Per-project Docker sandboxes: rejected for the base deployment; the container may access the mounted projects root.
- Mount Docker socket/host root for convenience: rejected for Phase 1.
- Separate special secret-backup policy: rejected by user; normal appdata backup applies.

## Consequences

- Image/recreate operations must preserve `/home/pi`.
- Planning must handle UID/GID initialization idempotently.
- Pi can operate across canonical repositories/worktrees, but higher-level branch/worktree policy is not embedded in the runtime.
- Broader future Unraid administration requires a separate explicit integration.

## Required authoritative updates

- Requirements / Project Definition: captured in `requirements/PI_UNRAID_BOOTSTRAP.md`.
- Planning: choose concrete Dockerfile/entrypoint/permission mechanics within this layout.
- Task Card/OpenSpec: later.
- PROJECT.md: point to this decision.

## Provenance

- Source discussion/request: G07/G08/G13/G14/G20/G35/G36/G39/G45/G51/G87/G100/G104/G111/G112/G116/G123.
- Evidence/research: `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md`.
- Strategic `request_id`: none.
- Exact `DECISION FOR CODEX:` marker: none.
- Persisting commit: recorded by Git history.
