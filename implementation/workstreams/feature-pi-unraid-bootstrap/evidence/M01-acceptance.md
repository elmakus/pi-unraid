# M01 integrated acceptance evidence

- Milestone: `M01 — Reproducible non-root development environment`
- Workstream: `feature-pi-unraid-bootstrap`
- Execution policy: `chatgpt_only`
- Final implementation head: `d016731a276e33f09b9a23df682951e89b21c8dc`
- Tested image: `pi-unraid:local`
- Tested image ID: `sha256:7ef10cfe06313730505dda1e4ae33227eace1f3bfa5d5a48fe592cb7f5866e6f`
- Date: 2026-09-23
- Verdict: **GREEN**

## Accepted Card results

- `M01-T01` — terminal GREEN review on `bd25b5317d9b53cd9d2d17d21adfc75e9c86beb3`; reproducible digest-pinned Node 24 image, stable Pi seed 0.87.1 and required development-tool inventory.
- `M01-T02` — terminal GREEN review on `412c9ce143f883f13b885aa93502651184809a10`; non-root Compose/persistent-home foundation, bounded UID/GID initialization, accepted mounts, restart/timezone/logging and safe incompatible-home failure.
- `M01-T03` — terminal GREEN re-review on `d016731a276e33f09b9a23df682951e89b21c8dc`; explicit native cwd/worktree path, persistent Git identity, strict GitHub host trust and operator setup.

## Integrated checkpoint verification

Fresh close-time verification on `Tower`, using only disposable containers and unique `/tmp` fixtures:

- `bash scripts/verify-base-image.sh pi-unraid:local` — GREEN.
- `bash scripts/verify-compose-foundation.sh pi-unraid:local` — `M01-T02 fixture verification: GREEN`, exit 0.
- `bash scripts/verify-git-worktree-foundation.sh pi-unraid:local` — `M01-T03 fixture verification: GREEN`, exit 0.

The T03 independent re-review also rechecked the tracked GitHub.com Ed25519/ECDSA/RSA host keys/fingerprints against the official GitHub Docs values current on 2026-09-23.

## Milestone outcome readback

The approved M01 checkpoint is satisfied on the disposable test surface:

- repository-owned image builds and the required stable Pi/tool surface is usable;
- normal service execution is non-root with configurable UID/GID and working sudo;
- persistent-home restart fixture preserves existing state and ownership;
- only accepted home/projects/worktrees mounts are present; no Docker socket, host-root or inbound SSH service is introduced;
- timezone `Europe/Zurich`, `unless-stopped` policy and bounded Docker log rotation are present;
- explicit `/projects` and linked `/worktrees` cwd/metadata/write behavior is GREEN;
- persistent Git identity and strict GitHub host trust survive recreation;
- ordinary whole-home appdata backup scope is documented;
- no live OAuth/GitHub credential, live project/worktree, or Unraid host-restart success is claimed from M01 fixtures.

## Deferred by approved authority

M01 does not claim M02 runtime-update/fallback/graceful-stop/deployment-rollback behavior or M03 live OAuth/session/host-restart acceptance. Those remain the next approved milestones.

## Verdict

**GREEN** — M01 satisfies its approved milestone checkpoint and may be marked `done`. The next deterministic route is JIT Execution Prep for approved milestone M02.
