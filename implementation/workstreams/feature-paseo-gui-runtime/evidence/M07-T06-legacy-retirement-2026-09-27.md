# M07-T06 — legacy standalone Pi retirement

Date: 2026-09-27  
Card: `M07-T06`  
Execution subject: `elmakus/pi-unraid@0f571e19f360430bd288f532249ca94a2a86d647`

## Launch refresh

Every exact dependency binding in the Card was re-read and matched its immutable blob:

- M07-T05: `0278f67d73b450fa7464525d9e29398b1b988655:56c09a92115ddb83ce58b744ed36e8c76fd39b41`
- M07-T04: `1cf7cf3277edda7d9f5a82615f3e27d5f8d6a3c9:3fca9476ac6fd96d7b039571952c0be43c18192f`
- M07-T03: `3116a20ca46dd56ecdbca187810652dfceb72a42:6fddfd94a8debec5b458f8cc6ddbd1f78005b602`
- M07-T02: `7e2be5ecc2996d62bc22124ddff321f9afbe48de:bf2010c429e7b90a9cb9d47c24e4472dbaf31dcd`

M07-T04 therefore established base-final GREEN and M07-T05 had terminal `activated-GREEN` before retirement began.

## Pre-retirement readback

Canonical current `compose.yaml` rendered exactly one service, `paseo`; it no longer declared a standalone legacy Pi service capable of recreating the old runtime.

Legacy runtime identity before mutation:

- container: `pi-unraid-pi-1`
- exact container ID: `aa7d11dce3e2727df1f44caf7196273264743f428d9446fe8a5777f054f312d7`
- image ID: `sha256:293f88a02ee015b4b3be05f071534b5405cdca8cb4948e3b0ee4321c0deea72c`
- image tag: `pi-unraid:local`
- image size: `1248446995` bytes
- state: running / healthy
- restart policy: `unless-stopped`
- persistent legacy HOME: `/mnt/user/appdata/pi-unraid/home -> /home/pi`
- project/worktree mounts remained `/mnt/user/projects` and `/mnt/user/pi-worktrees`
- Codex-LB secret mount remained read-only.

Production before retirement remained `pi-unraid-paseo-1`, running / healthy on exact accepted image `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`.

## Backup boundary

Existing Appdata Backup policy covers `/mnt/user/appdata`, but prior readiness evidence had recorded recent scheduled-backup failures. M07-T06 therefore created a bounded additional archive of only the legacy HOME before container retirement:

- source: `/mnt/user/appdata/pi-unraid/home`
- source ownership: UID:GID `99:100`
- source logical size before retirement: `548285730` bytes
- source file count: `14445`
- source directory count: `2016`
- archive: `/mnt/user/appdatabackup/pi-unraid-m07-t06-legacy-retirement/legacy-home-20260927T162527Z.tar`
- archive mode: `0600`
- archive size: `576768000` bytes
- SHA-256: `4a21b1ce87bcf01219095b04d2267fb4c315fb6ceaa30c3d62c701fcf056a61b`

No secret contents were inspected or copied into repository evidence.

## Retirement transaction

Immediately before mutation the exact legacy container ID, production image/health, and archive hash were rechecked.

Only the exact legacy container was changed:

1. `docker stop aa7d11dce3e2727df1f44caf7196273264743f428d9446fe8a5777f054f312d7`
2. readback confirmed state `exited`
3. `docker rm aa7d11dce3e2727df1f44caf7196273264743f428d9446fe8a5777f054f312d7`
4. readback confirmed `pi-unraid-pi-1` absent.

No image prune, appdata deletion, HOME restore, broad share deletion, network mutation, reboot, Docker-engine restart or other high-impact operation occurred.

## Post-retirement readback

The independent legacy runtime/autostart authority is absent while rollback/migration material remains:

- no container named `pi-unraid-pi-1`;
- legacy image still present exactly as `sha256:293f88a02ee015b4b3be05f071534b5405cdca8cb4948e3b0ee4321c0deea72c`, tag `pi-unraid:local`;
- legacy HOME still exists at `/mnt/user/appdata/pi-unraid/home`, UID:GID `99:100`, logical size `548285730` bytes;
- bounded archive remains present with mode `0600`, size `576768000` bytes and the same SHA-256;
- canonical Compose still renders only `paseo`.

Production after retirement remains:

- exact image `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`;
- running / healthy;
- restart policy `unless-stopped`;
- `pi auth check --provider codex-lb --model gpt-6-sol --no-refresh` => `ready`.

Global-capability readback is GREEN / in-sync: Pi 0.87.1, SpecPi 0.34.0 and pi-mcp-adapter 2.37.0 are exact; compatibility is GREEN; SpecPi wishlist is `on`; SpecPi scope policy remains inactive. A fresh provider-free Pi RPC command discovery after retirement returned successfully, included both `wishlist` and `scope`, showed scope inactive, and emitted zero extension errors.

## Verdict

M07-T06 retirement is **GREEN**. The standalone legacy Pi container and its autostart authority are gone, production Paseo remains healthy and authoritative, and the legacy image, persistent HOME and bounded backup archive remain available as rollback/migration material.
