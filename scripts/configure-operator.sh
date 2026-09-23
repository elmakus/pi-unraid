#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <git-user-name> <git-user-email>" >&2
  exit 2
fi

git_name="$1"
git_email="$2"
repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
host_keys="$repo_root/config/github-known-hosts"

[ -r "$host_keys" ] || {
  echo "pi-unraid setup error: missing $host_keys" >&2
  exit 1
}

umask 077
mkdir -p "$HOME/.ssh"
touch "$HOME/.ssh/known_hosts" "$HOME/.ssh/config"

while IFS= read -r line; do
  case "$line" in
    ''|'#'*) continue ;;
  esac
  grep -Fqx "$line" "$HOME/.ssh/known_hosts" || printf '%s\n' "$line" >> "$HOME/.ssh/known_hosts"
done < "$host_keys"

begin="# BEGIN pi-unraid github"
end="# END pi-unraid github"
tmp="$(mktemp "$HOME/.ssh/config.XXXXXX")"
cat > "$tmp" <<'EOF'
# BEGIN pi-unraid github
Host github.com
  HostName github.com
  User git
  StrictHostKeyChecking yes
  UserKnownHostsFile ~/.ssh/known_hosts
# END pi-unraid github
EOF

awk -v begin="$begin" -v end="$end" '
  $0 == begin { skip=1; next }
  $0 == end { skip=0; next }
  !skip { print }
' "$HOME/.ssh/config" >> "$tmp"

mv "$tmp" "$HOME/.ssh/config"
chmod 600 "$HOME/.ssh/config" "$HOME/.ssh/known_hosts"

git config --global user.name "$git_name"
git config --global user.email "$git_email"

printf 'pi-unraid operator setup: Git identity + strict GitHub host trust configured in %s\n' "$HOME"
