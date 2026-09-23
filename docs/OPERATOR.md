# Pi on Unraid — Phase 1 operator path

This document covers the M01 native terminal/TUI, Git identity, GitHub SSH trust, workspace and backup setup. It does not claim live ChatGPT OAuth, host-restart or update/rollback acceptance.

## Persistent user setup

The service home is the persistent bind:

- host: `/mnt/user/appdata/pi-unraid/home`
- container: `/home/pi`

From the repository checkout mounted beneath `/projects`, configure the persistent Git identity and GitHub host trust once:

```sh
docker compose exec -u pi pi \
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
