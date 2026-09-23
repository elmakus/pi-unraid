#!/usr/bin/env bash
set -euo pipefail

image="${1:-pi-unraid:m01-t01}"

printf 'IMAGE=%s\n' "$image"
docker image inspect "$image" --format 'IMAGE_ID={{.Id}}'
docker image inspect "$image" --format 'PI_SEED_LABEL={{index .Config.Labels "io.pi-unraid.pi-seed-version"}}'

docker run --rm "$image" sh -ec '
  printf "node="; node --version
  printf "pi="; pi --version
  printf "python="; python3 --version
  printf "git="; git --version
  printf "ssh="; ssh -V 2>&1 | head -n1
  printf "gh="; gh --version | head -n1
  printf "curl="; curl --version | head -n1
  printf "jq="; jq --version
  printf "rg="; rg --version | head -n1
  printf "fd="; fd --version
  printf "find="; find --version | head -n1
  printf "tar="; tar --version | head -n1
  printf "gzip="; gzip --version | head -n1
  printf "unzip="; unzip -v | head -n1
  printf "zip="; zip -v | sed -n "2p"
  printf "gcc="; gcc --version | head -n1
  printf "make="; make --version | head -n1
  printf "git_lfs="; git lfs version
  printf "sudo="; sudo --version | head -n1
  printf "seed_env=%s\n" "$PI_UNRAID_SEED_VERSION"
  npm ls -g --depth=0 @earendil-works/pi-coding-agent
'
