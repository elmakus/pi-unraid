# M07-T03 production cutover — technical GREEN, phone proof pending

- Card: `M07-T03`
- Durable predecessor: `implementation/workstreams/feature-paseo-gui-runtime/results/M07-T02.md@7e2be5ecc2996d62bc22124ddff321f9afbe48de:bf2010c429e7b90a9cb9d47c24e4472dbaf31dcd`
- Required predecessor review: `M07-T02-R01` GREEN.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- Exact Tower image: `pi-unraid:paseo-b4e0c1e7c276` / `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`
- State: automatic production cutover and technical acceptance are GREEN. The required actual phone-to-production Relay action is still pending; no M07-T03 result/final GREEN is claimed yet.

## Launch refresh and preflight

- M07-T03 was materialized from approved P4 after M07-T02 R01 GREEN. Every exact Card dependency was re-fetched at its pinned commit and matched its pinned blob.
- The branch-owned current `compose.yaml` blob was `87f57b46f485918b50f560581ea86d580abcff6e`.
- The standing `/mnt/user/projects/pi-unraid` checkout was deliberately not used for deployment because read-only preflight showed it on old `feat/pi-unraid-bootstrap@e5ca17b...`.
- Pre-cutover:
  - production `pi-unraid-paseo-1`: absent;
  - staged `pi-unraid-staged-ha-paseo-1`: running/healthy on the exact image;
  - legacy `pi-unraid-pi-1`: running/healthy;
  - staged HOME: `/mnt/user/appdata/pi-unraid/paseo-ha-staged-home`, mode 0700, owner 99:100;
  - production HOME: absent;
  - both mounted secret files: mode 0600, owner 99:100;
  - build retention still protects the exact candidate tag/image.

## Fresh post-HA backup and HOME transfer

- Staged Paseo was quiesced before the state copy. It remains intentionally stopped after cutover so two daemons do not concurrently publish the same persisted Relay identity.
- Fresh post-auth backup:
  - `/mnt/user/appdatabackup/pi-unraid-m07-t03-preprod/paseo-ha-staged-home-post-ha-20260927T140048Z.tar`
  - size: 1,037,967,360 bytes;
  - mode: 0600;
  - SHA-256: `e4f8d86fec6254c53e3c89022d3c2c10cf907dd48ab734fa2ea40f3c4e104e7d`.
- Production HOME was created by `rsync -aHAX --numeric-ids` from the quiesced staged HOME.
- Immediate `rsync -aHAXn --delete --numeric-ids --itemize-changes` returned zero changes.
- Production HOME readback: mode 0700, owner 99:100.

## Production compose and cutover

- Deployment inputs under `/mnt/user/appdata/pi-unraid/m07-t03/` contain the exact branch runtime compose plus a bounded live override for:
  - the exact immutable candidate image;
  - the accepted read-only UID99 `/etc/passwd` overlay;
  - read-only Unraid GraphQL key;
  - read-only Codex-LB provider secret;
  - Docker host-gateway alias.
- Rendered pre-cutover config showed:
  - `image=pi-unraid:paseo-b4e0c1e7c276`;
  - user `99:100`;
  - `restart=unless-stopped`;
  - shm 1 GiB;
  - no public port bindings;
  - HOME/projects/worktrees plus three accepted read-only mounts.
- Production was started with `docker compose ... up -d --no-build`; there was no candidate rebuild or latest resolution.
- Compose reported legacy `pi-unraid-pi-1` as an orphan of the project name, but `--remove-orphans` was not used and legacy Pi was not stopped or removed.

## Production readback

- `pi-unraid-paseo-1`: running/healthy, exact image, user 99:100, restart `unless-stopped`, shm 1073741824, no public port bindings.
- UID 99 readback resolves to `paseo-unraid` through the accepted passwd overlay.
- Production Paseo status:
  - daemon 0.9.2 running;
  - provider `pi` available;
  - Relay enabled and reachable at the upstream Relay service;
  - persisted server ID remains `srv_jmdR4FLNIxrE`, matching the staged HA identity.
- GitHub auth remained usable after transfer and later HOME reconciliation; an authenticated repository workflow-list read returned 7 workflows without exposing a token.
- `pi auth check --provider codex-lb --model gpt-6-sol --json --no-refresh`: ready / api_key.
- Model discovery still exposes `codex-lb/gpt-6-sol`.

## Host-control doctor

- An initial smoke used a guessed Docker-host alias endpoint and correctly failed transport; no mutation followed from that diagnostic.
- The live Tower LAN GraphQL endpoint was then recovered by read-only host/network readback.
- Authenticated INFO/DOCKER readback is GREEN with credential fingerprint only; no raw key is recorded.
- Full production doctor with the persisted strict SSH identity/known-hosts file is GREEN:
  - GraphQL GREEN;
  - SSH forced-test reachability GREEN;
  - host safety policy GREEN.
- No second GraphQL host mutation was executed. The exact staged pause/unpause proof remains the reusable mutation evidence.

## Browser and Pi-provider smoke

- Headless Playwright/Chromium production launch rendered a non-empty 4,254-byte PNG and cleaned the temporary artifact.
- Direct runtime versions match the frozen candidate: Paseo 0.9.2, Node 22.23.3, Pi 0.87.1, Playwright 1.63.0, Chromium 153.0.8010.12, GitHub CLI 2.101.0, Docker CLI 29.8.1, Docker Compose 5.5.1.
- Production Paseo→Pi session `Production RPC smoke` completed through provider `pi`, model `codex-lb/gpt-6-sol`.

## Production capability drift and bounded repair

The first production capability readback found an accepted-desired-state drift in the transferred staged HOME:
- Pi instruction plane: `in_sync=false`;
- SpecPi and pi-mcp-adapter: absent; global-capability state RED.

This was repaired only through already-accepted M02/M04 mechanisms, without new capability approval or wishlist activation:
- `pi_instruction_plane.py apply`: installed the five managed files; post-status `in_sync=true`;
- `pi_global_capabilities.py apply`: exact frozen `specpi 0.34.0` and `pi-mcp-adapter 2.37.0`; compatibility GREEN; snapshot available; `specpi_scope_policy=inactive_in_fresh_session`.
- Post-apply global-capability status is GREEN and instruction-plane status remains in sync.
- Provider auth and Relay stayed healthy after the repair.
- Formal full environment capability doctor: **GREEN, 12 GREEN / 0 WARN / 0 RED / 0 unexpected**.
- A fresh post-reconcile production session `M07-T03 production technical final` completed through provider `pi`, model `codex-lb/gpt-6-sol`.

## Final pre-phone state

- Production Paseo: running/healthy on exact candidate image.
- Production Relay: enabled/reachable with the persisted staged server ID.
- Legacy Pi: running/healthy.
- Staged Paseo: intentionally exited after the coherent HOME copy; its HOME remains preserved as rollback/source state.
- Fresh pre-production post-HA backup is present and checksummed.
- Remaining M07-T03 acceptance item: **actual user phone action through the production Relay path**. This must not be inferred from automated reachability.

For the bounded phone proof, use the already-created production session titled `M07-T03 production technical final` and send the exact message `PHONE-PROD-GREEN` from the phone UI. Because the staged daemon is stopped and only the production daemon is publishing the persisted Relay identity, the resulting agent update can be read back as direct production-path evidence.
