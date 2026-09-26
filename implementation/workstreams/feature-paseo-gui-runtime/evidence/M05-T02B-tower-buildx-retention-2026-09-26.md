# M05-T02B — Tower Buildx / cache / retention acceptance

Date: 2026-09-26  
Card: `M05-T02B`  
Final implementation subject: `elmakus/pi-unraid@4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8`

## Authority and predecessor binding

- Strategic plan: `planning/PASEO_GUI_RUNTIME_P3.md` (approved P3; blob `fb071b96e5e7b54187bfaa7040640f5f3eb59b89`).
- Requirements: `requirements/PASEO_GUI_RUNTIME.md`, especially PGR-REQ-061, PGR-REQ-066, PGR-REQ-067, PGR-REQ-070 and PGR-REQ-083.
- Decision: `decisions/ADR_PGR_004_UPDATE_BUILD_ROLLBACK.md`.
- Exact predecessor result: `implementation/workstreams/feature-paseo-gui-runtime/results/M05-T02A-R02.md@d6643ffcdf202add37a39bc7653d6192cde36637:4273708d8f1cc8fb5eb33b3a7582fd0b21e143f4`.

P3 makes the current path local-first. Private project GHCR publication, registry-backed project cache and a self-hosted GitHub runner are explicitly deferred/optional and were not introduced by this Card.

## Pre-mutation Tower readback

Before M05-T02B mutation, Tower had:
- Buildx builders `default` and `chatgpt-ce-workstation`, but no dedicated `pi-unraid-paseo` builder.
- No dedicated `/mnt/user/appdata/pi-unraid/buildx` state/cache surface.
- Existing production runtime `pi-unraid-pi-1` healthy.
- The Workstation builder/cache namespace remained separate.

No production cutover, whole-host reboot or Docker-engine restart was performed.

## Implementation

M05-T02B adds `scripts/paseo_tower_build.py` as a bounded Tower-local layer over the accepted M05-T02A `scripts/paseo_buildx.py` foundation.

The implementation:
- creates/reuses the isolated `pi-unraid-paseo` docker-container builder;
- persists Docker Buildx config, portable local cache, records, cache policy and retention state below the accepted pi-unraid appdata boundary;
- keeps the Tower builder/cache independent from disposable runtime containers and from `chatgpt-ce-workstation`;
- consumes only the already-frozen candidate; it performs no fresh latest resolution;
- retains a bounded set of local immutable Paseo child images (default maximum: 3);
- validates retained records and live image/candidate identity before protection;
- removes only unprotected managed `pi-unraid:paseo-*` image tags;
- runs cache/image cleanup only after a successful build and smoke;
- uses current Buildx `--max-used-space 8GB` post-success pruning for the dedicated builder;
- performs OCI-local portable-cache reachability GC and enforces an 8 GiB hard cap, recording `cache-policy.json`;
- leaves failed candidate/build/smoke paths without retention/image cleanup;
- records machine-readable Tower readback and supports deterministic recovery by rebuilding from canonical Git plus the frozen candidate/provenance if local Docker/BuildKit/cache state is lost.

A transient connector transport commit (`abf421dd…`) contained an injected Remote Desktop footer and was corrected before any live Tower mutation. It is not an accepted implementation subject or acceptance artifact.

## Automated contract tests

On final implementation subject `4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8`:

- Build/Tower cache contract subset: **50/50 GREEN**.
- Full repository unittest discovery: **147/147 GREEN**.

The full suite covers candidate resolution, child image, runtime, Relay auth, instruction plane, capability inventory/control, GraphQL host control, host doctor/safety guard, Buildx foundation and Tower build/cache/retention behavior.

Negative argparse output for the required `prune --record` argument is expected test evidence; the suite verdict is GREEN.

## Tower builder and persistent paths

Live accepted builder:
- builder: `pi-unraid-paseo`
- driver: `docker-container`
- BuildKit: `v0.32.2`
- BuildKit container: `buildx_buildkit_pi-unraid-paseo0`
- final observed container ID: `c57c3aba9e594cafe6f6e31e842079826c46b406be1bfd3ff80930cb428d9922`
- final observed state: running

Persistent/readback paths resolve on Tower to:
- root: `/mnt/cachezfs/appdata/pi-unraid/buildx`
- state/config: `/mnt/cachezfs/appdata/pi-unraid/buildx/docker-config`
- portable cache: `/mnt/cachezfs/appdata/pi-unraid/buildx/cache`
- records: `/mnt/cachezfs/appdata/pi-unraid/buildx/records`
- retention: `/mnt/cachezfs/appdata/pi-unraid/buildx/retention.json`
- cache policy: `/mnt/cachezfs/appdata/pi-unraid/buildx/cache-policy.json`
- readback: `/mnt/cachezfs/appdata/pi-unraid/buildx/tower-readback.json`

These are the resolved backing paths for the accepted `/mnt/user/appdata/pi-unraid/buildx` boundary.

## Cold build acceptance

Cold record:
`/mnt/user/appdata/pi-unraid/buildx/records/m05-t02b-cold.json`

Frozen candidate:
`sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`

Official frozen Paseo base:
`ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`

Cold facts:
- Paseo `0.9.2`; Pi `0.87.1`.
- build status: GREEN.
- build duration: 108143 ms.
- cached steps: 0.
- image at cold acceptance: `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`.
- managed tag: `pi-unraid:paseo-b4e0c1e7c276`.
- four smoke surfaces all GREEN: image provenance, persistence/ownership, instruction plane and global capabilities.
- smoke/test phase duration: 40682 ms.

The cold run predates only the later post-success cache-hard-cap/current-prune-flag refinement. Candidate and build graph were unchanged; final-SHA acceptance below revalidated the warm path and all smoke surfaces with the completed cache policy.

## Representative warm update acceptance on final SHA

Final warm record:
`/mnt/user/appdata/pi-unraid/buildx/records/m05-t02b-final-warm.json`

Bound implementation SHA:
`4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8`

Facts:
- same frozen candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`;
- harmless build-label-only representative update;
- **8 cached steps**;
- build duration: **7945 ms**;
- immutable image: `sha256:a8ea7f236b5167e4e02a3847b4af21db3b3a91be635be550c591f860d03f40b7`;
- candidate label on image exactly matches the frozen candidate;
- four smoke surfaces all GREEN;
- smoke/test duration: 37076 ms;
- post-success Buildx prune GREEN using `--max-used-space 8GB --force`, reclaimed `0B`.

This demonstrates real cache reuse across separate invocations.

## Portable cache bound

Final `cache-policy.json`:
- bytes before: `933087833`
- bytes after OCI reachability GC: `933087833`
- bytes after: `933087833`
- hard maximum: `8589934592` bytes (`8GB`)
- reachable blobs: `48`
- stale blobs removed in the final warm run: `0`
- over-bound fail-safe clear required: `false`

The final warm run therefore stayed well inside the configured bound and did not grow the portable cache.

## Bounded image retention and disposable-runtime survival

Final protected retention entry:
- tag: `pi-unraid:paseo-b4e0c1e7c276`
- image: `sha256:a8ea7f236b5167e4e02a3847b4af21db3b3a91be635be550c591f860d03f40b7`
- candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- retention maximum: 3.

A disposable managed tag/runtime probe was created and removed. Post-success retention cleanup removed only `pi-unraid:paseo-disposable-final` and explicitly skipped the protected tag.

Before/after invariants:
- production `pi-unraid-pi-1` remained the same container ID `aa7d11dce3e2727df1f44caf7196273264743f428d9446fe8a5777f054f312d7`, running and healthy;
- BuildKit container remained the same `c57c3aba9e594cafe6f6e31e842079826c46b406be1bfd3ff80930cb428d9922`, running;
- protected image ID remained unchanged;
- portable cache remained present.

## Fail-closed proof on final SHA

An intentionally corrupted candidate produced:
- wrapper return code: `2`;
- resolution failure: candidate ID mismatch;
- build: skipped;
- test: skipped;
- prune: skipped.

The SHA256 of `retention.json` was identical before and after the failure, and the protected image remained present. Therefore a failed candidate cannot trigger retention mutation, image cleanup or Buildx prune.

## Final host readback

At the end of acceptance:
- implementation subject: `4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8`;
- production `pi-unraid-pi-1`: unchanged, running, healthy;
- dedicated `pi-unraid-paseo` builder: running;
- portable cache: `933087833` bytes;
- protected image: `sha256:a8ea7f236b5167e4e02a3847b4af21db3b3a91be635be550c591f860d03f40b7`;
- protected image candidate label: exact frozen candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`.

No private project registry, registry-backed project cache, self-hosted runner, production cutover, host reboot or Docker-engine restart was introduced.

## Execution verdict

Implementation acceptance for M05-T02B is **GREEN pending required independent implementation review**.
