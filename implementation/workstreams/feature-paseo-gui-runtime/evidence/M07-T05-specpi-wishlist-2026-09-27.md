# M07-T05 — SpecPi wishlist post-deploy disposition

- Card: `M07-T05`
- Disposition: **activated-GREEN**
- Implementation subject: `elmakus/pi-unraid@35b2d837690e9e7ef0f4d3b3a87b7756173fbacf`
- Production image: `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`
- Exact runtime pair: Pi `0.87.1`, SpecPi `0.34.0`, pi-mcp-adapter `2.37.0`
- Base final GREEN predecessor: M07-T04 exact result `1cf7cf3277edda7d9f5a82615f3e27d5f8d6a3c9:3fca9476ac6fd96d7b039571952c0be43c18192f`

## Native activation discovery

The installed SpecPi package exposes wishlist collection through `/wishlist on|off`. Its native state is `~/.pi/agent/specpi/tool-wishlist-config.json`; upstream `readCollectionMode` returns `undecided` when that file is absent and `setCollectionMode` writes schema 1 with mode `on` or `off`. The upstream `observationToolWanted(mode, interactive)` contract makes `report_capability_gap` available in headless sessions when mode is `on`, while an undecided headless session leaves it withdrawn. This activation is independent of SpecPi project-scope monitoring.

Pre-state on production was `undecided` with no wishlist config file. No wishlist observation or artificial capability gap was created.

## Activation and exact-pair smoke

Wishlist collection was activated through the installed SpecPi native state API. Readback after activation:

- mode: `on`;
- native config: `{"schema":1,"mode":"on"}`;
- mode file: `0600`, owner `99:100`;
- upstream headless observation-tool gate: `true`;
- fresh Pi RPC showed no extension error and SpecPi scope status remained inactive;
- production Paseo remained on the exact accepted image and healthy;
- Relay remained enabled/reachable with server ID `srv_jmdR4FLNIxrE`;
- `pi auth check --provider codex-lb --model gpt-6-sol --no-refresh` returned `ready`;
- legacy `pi-unraid-pi-1` remained running/healthy.

## Desired-state persistence

The already-existing `scripts/pi_global_capabilities.py` mechanism was extended instead of creating a second desired-state store. Its canonical managed state now includes:

- SpecPi wishlist desired mode `on`;
- secret-safe wishlist status/readback;
- compatibility marker binding to wishlist collection `on`;
- activation before exact-pair compatibility smoke;
- snapshot/rollback preservation of any prior supported wishlist config;
- backward-compatible handling of the pre-M07-T05 M04 snapshot;
- a wishlist-only fail-safe path: when managed packages are already exact, smoke failure restores only the prior wishlist/compatibility state rather than uninstalling/reinstalling SpecPi or pi-mcp-adapter.

Production persistence was then applied using the exact accepted image and production HOME. Before persistence, the new manager correctly reported only the expected stale compatibility marker while both packages were `installed_exact=true` and wishlist mode was already GREEN/on. Apply completed GREEN and rewrote only the compatibility/desired-state metadata. The following production files were unchanged across persistence:

- `~/.pi/agent/settings.json`: SHA-256 `9644b660e6b41a909ff1804bcae8dc2e3db39880b98f1c7ceda506bb85a0a605`;
- `~/.pi/agent/npm/package-lock.json`: SHA-256 `8e91375491d2473a0988471367e4df3de124d767b8e0b4f328e394b8e2378466`.

Post-apply manager status was GREEN/in-sync for both managed packages, compatibility, wishlist mode `on`, and scope policy `inactive_in_fresh_session`.

## Verification

Disposable verification on the exact production image completed GREEN:

- `bash -n scripts/configure-pi-global-capabilities.sh scripts/verify-pi-global-capabilities.sh`;
- focused Python contract: 5/5 GREEN;
- `scripts/verify-pi-global-capabilities.sh pi-unraid:paseo-b4e0c1e7c276`: GREEN, including apply, wishlist persistence, compatibility smoke, rollback to pre-managed state, re-apply and status;
- full repository suite run inside the production container's UID-compatible checkout: **382/382 GREEN**.

An earlier host-side full-suite attempt reported two failures only because root Git rejected the UID-99-created disposable checkout as `dubious ownership`; rerunning the exact suite inside the production container under the checkout owner produced 382/382 GREEN. No repository defect was inferred from the host-only ownership refusal.

## Restart/readback

After ordinary production container restart:

- production returned `running/healthy` on the exact image;
- wishlist native mode remained `on`;
- headless observation-tool gate remained enabled;
- global-capability status remained GREEN/in-sync with exact packages, compatibility GREEN, wishlist GREEN/on and scope inactive;
- environment full doctor: **12 GREEN / 0 WARN / 0 RED / 0 unexpected**;
- Relay and Codex-LB remained healthy;
- legacy Pi remained running/healthy.

## Boundary

No SpecPi project-scope monitoring was enabled. No new global capability was approved. No Paseo/Pi/SpecPi version was re-resolved or rebuilt. No destructive HOME operation, host reboot, Docker-engine restart, network mutation, OR/PW semantic change or legacy retirement occurred. Wishlist activation remains isolated from the already-established M06/M07-T01..T04 base final GREEN.
