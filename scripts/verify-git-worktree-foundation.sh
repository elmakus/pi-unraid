#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${1:-pi-unraid:local}"
fixture="$(mktemp -d "${TMPDIR:-/tmp}/pi-unraid-m01-t03.XXXXXX")"
name="piunraid-m01-t03-$$"
uid="${PI_TEST_UID:-21001}"
gid="${PI_TEST_GID:-21001}"

cleanup() {
  docker rm -f "$name" >/dev/null 2>&1 || true
  rm -rf "$fixture"
}
trap cleanup EXIT

mkdir -p "$fixture/home" "$fixture/projects" "$fixture/worktrees"
chmod 0777 "$fixture/projects" "$fixture/worktrees"

start_container() {
  docker run -d --name "$name" \
    -e PI_UID="$uid" -e PI_GID="$gid" -e TZ=Europe/Zurich \
    -v "$fixture/home:/home/pi" \
    -v "$fixture/projects:/projects" \
    -v "$fixture/worktrees:/worktrees" \
    -v "$repo_root:/opt/pi-unraid-src:ro" \
    "$image" sleep infinity >/dev/null

  for _ in $(seq 1 100); do
    if docker exec "$name" sh -ec 'test "$(id -u pi)" = "$PI_UID"; test "$(id -g pi)" = "$PI_GID"' \
      && docker exec -u pi "$name" test -w /home/pi; then
      return 0
    fi
    sleep 0.1
  done

  docker logs "$name" >&2 || true
  echo "M01-T03 fixture error: service-user initialization did not become ready" >&2
  return 1
}

start_container
docker exec -u pi "$name" sh -ec '
  mkdir -p "$HOME/.ssh"
  cat > "$HOME/.ssh/config" <<'"'"'EOF'"'"'
Host github.com
  StrictHostKeyChecking no
  UserKnownHostsFile /tmp/insecure-known-hosts
Host preserved.example
  Port 2222
EOF
'
docker exec -u pi "$name" sh /opt/pi-unraid-src/scripts/configure-operator.sh \
  "Fixture User" "fixture@example.invalid"

docker exec -u pi "$name" sh -ec '
  mkdir -p /projects/demo
  git -C /projects/demo init >/dev/null
  printf "fixture\n" > /projects/demo/README.md
  git -C /projects/demo add README.md
  git -C /projects/demo commit -m fixture >/dev/null
  git -C /projects/demo worktree add -b fixture-branch /worktrees/demo-wt >/dev/null
  printf "project\n" > /projects/demo/project-write
  printf "worktree\n" > /worktrees/demo-wt/worktree-write
'

docker exec -u pi -w /projects/demo "$name" sh -ec '
  test "$PWD" = /projects/demo
  pi --version >/dev/null
  test "$(git rev-parse --show-toplevel)" = /projects/demo
  git worktree list --porcelain | grep -Fx "worktree /projects/demo" >/dev/null
  git worktree list --porcelain | grep -Fx "worktree /worktrees/demo-wt" >/dev/null
  gh --version >/dev/null
'

docker exec -u pi -w /worktrees/demo-wt "$name" sh -ec '
  test "$PWD" = /worktrees/demo-wt
  test "$(git rev-parse --show-toplevel)" = /worktrees/demo-wt
  test "$(git rev-parse --git-common-dir)" = /projects/demo/.git
  git status --short >/dev/null
'

docker exec -u pi "$name" sh -ec '
  test "$(git config --global user.name)" = "Fixture User"
  test "$(git config --global user.email)" = "fixture@example.invalid"
  ssh -G github.com 2>/dev/null | grep -Eq "^stricthostkeychecking (yes|true)$"
  ssh -G github.com 2>/dev/null | grep -Fx "userknownhostsfile /home/pi/.ssh/known_hosts" >/dev/null
  ssh -G preserved.example 2>/dev/null | grep -Fx "port 2222" >/dev/null
  ssh-keygen -lf "$HOME/.ssh/known_hosts" -E sha256 | grep -F "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU" >/dev/null
  ssh-keygen -lf "$HOME/.ssh/known_hosts" -E sha256 | grep -F "SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM" >/dev/null
  ssh-keygen -lf "$HOME/.ssh/known_hosts" -E sha256 | grep -F "SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s" >/dev/null
'

test "$(stat -c '%u:%g' "$fixture/projects/demo/project-write")" = "$uid:$gid"
test "$(stat -c '%u:%g' "$fixture/worktrees/demo-wt/worktree-write")" = "$uid:$gid"

docker rm -f "$name" >/dev/null
start_container

docker exec -u pi "$name" sh -ec '
  test "$(git config --global user.name)" = "Fixture User"
  test "$(git config --global user.email)" = "fixture@example.invalid"
  grep -F "github.com ssh-ed25519 " "$HOME/.ssh/known_hosts" >/dev/null
  git -C /projects/demo worktree list --porcelain | grep -Fx "worktree /worktrees/demo-wt" >/dev/null
  test "$(git -C /worktrees/demo-wt rev-parse --git-common-dir)" = /projects/demo/.git
'

echo "M01-T03 fixture verification: GREEN"
