# Pi on Unraid — Phase 1 operator path

This document covers the M01 native terminal/TUI, Git identity, GitHub SSH trust, workspace and backup setup. It does not claim live ChatGPT OAuth, host-restart or update/rollback acceptance.

## Persistent user setup

The service home is the persistent bind:

- host: `/mnt/user/appdata/pi-unraid/home`
- container: `/home/pi`

From the repository checkout mounted beneath `/projects`, configure the persistent Git identity and GitHub host trust once:

```sh
docker compose exec -u pi pi sh \
  /projects/pi-unraid/scripts/configure-operator.sh \
  "Your Name" "you@example.com"
```

The script writes only user-owned persistent state beneath `/home/pi`: `~/.gitconfig`, `~/.ssh/config`, and missing GitHub entries in `~/.ssh/known_hosts`. It keeps unrelated existing SSH config/known_hosts lines.

The tracked host-key source is `config/github-known-hosts`. Its keys/fingerprints must be rechecked against GitHub's official published SSH fingerprints before changing them. The managed SSH stanza enforces `StrictHostKeyChecking yes`.

## Native Pi/TUI entry

Always choose the intended repository or worktree explicitly with Docker's working-directory option.

Canonical repository:

```sh
docker compose exec -u pi -w /projects/REPOSITORY pi pi
```

Existing linked worktree:

```sh
docker compose exec -u pi -w /worktrees/WORKTREE pi pi
```

The runtime does not create, remap or rewrite worktrees automatically. Use normal Git commands and verify `git rev-parse --show-toplevel` / `git worktree list --porcelain` when troubleshooting linked-worktree metadata.

## GitHub SSH and `gh`

SSH Git transport and GitHub CLI API authentication are separate concerns:

- SSH remotes use the persistent `~/.ssh` material and strict host-key verification.
- `gh auth login` configures GitHub CLI API authentication separately.
- M01 fixture checks verify the SSH trust/config surface and `gh` availability without storing real credentials in project evidence.
- Live authenticated Git/gh proof belongs to the later authorized on-Unraid acceptance milestone.

## Backup and reproducibility

The entire host directory `/mnt/user/appdata/pi-unraid/home` is the ordinary appdata backup source, including Pi native state under `~/.pi/agent`, Git identity and normal interactive credential stores. There is no project-specific secret-backup exclusion.

Runtime-installed tools may be used for experiments. If a tool becomes part of the normal expected environment, add it to repository/image source rather than relying on a one-off persistent install.

## Disposable verification

With the M01 image already built:

```sh
bash scripts/verify-git-worktree-foundation.sh pi-unraid:local
```

The verification uses only a unique `/tmp` fixture and disposable container. It creates a synthetic repository + linked worktree, verifies explicit cwd behavior, non-root writes, metadata resolution, persistent Git/SSH setup, GitHub host-key fingerprints and `gh` availability. No live OAuth or GitHub credential is required.

## Host update and deployment rollback

The normal host-operated maintenance entry is:

```sh
bash scripts/update.sh
```

Run it from the tracked deployment checkout on the Unraid host. The operation requires a clean branch with an upstream that can be fast-forwarded. When deployment-shaping values such as `PI_UID`, `PI_GID`, `PI_CODEX_LB_BASE_URL`, `PI_CODEX_LB_MODEL` or the Codex-LB secret source are not supplied explicitly, the update entry inherits them from the currently running Compose service so a plain `bash scripts/update.sh` preserves the live production identity/provider configuration. Explicit operator values still override the inherited values. Before changing the checkout or deployment it records the current source HEAD, active image ID and fully rendered Compose configuration under `/mnt/user/appdata/pi-unraid/deployment-state`. It then fast-forwards source, re-enters the updated script, builds a separate `pi-unraid:candidate`, runs the repository verification gate, retains the current image as `pi-unraid:previous`, and only then recreates the service. A candidate is accepted only after Compose health is GREEN.

If the post-cutover service is unhealthy, the script automatically retags the retained image as `pi-unraid:local`, recreates from the pre-update rendered Compose snapshot and verifies health. Persistent `/home/pi`, `/projects` and `/worktrees` are never restored or rewritten by image rollback.

An explicit deployment rollback uses the most recent retained transaction:

```sh
bash scripts/update.sh rollback
```

A specific transaction directory may be supplied as the second argument. Rollback consumes only local retained image/config artifacts, so it does not require fetching the failed candidate again. It deliberately does **not** reset Git source; the transaction records `pre-source-head` and `post-source-head` so source recovery, when actually desired, is a separate explicit Git operation.

The deployment-state directory is host metadata and is not mounted into the Pi container. Keep it alongside the normal appdata backup/host recovery surface. M02 validates this workflow only with disposable projects, tags and `/tmp` binds; running it against the live `pi-unraid` deployment is an M03 authorization/readiness action.

Disposable M02 update/rollback verification:

```sh
bash scripts/verify-update-rollback.sh pi-unraid:m02-t02-r2
```
