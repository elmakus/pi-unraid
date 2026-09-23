# M03 read-only target readiness — Tower

- Workstream: `feature-pi-unraid-bootstrap`
- Milestone: `M03 — On-Unraid acceptance and recoverable user handoff`
- Target: `Tower` (actual Unraid host)
- Date: 2026-09-23
- Mode: read-only readiness only; no production deployment/path/repository mutation performed
- Result: **READY WITH EXPLICIT LIVE-WRITE GATE**

## Host/runtime facts

- architecture: `x86_64`
- kernel: `6.12.54-Unraid`
- Docker: `27.5.1`
- Docker Compose: `v5.5.0`
- current project checkout: `/mnt/cachedl/projects/pi-unraid`
- accepted host projects path: `/mnt/user/projects` → `/mnt/cachedl/projects`
- projects root ownership/mode: `99:100`, mode `2777`
- project checkout ownership/mode: `99:100`, mode `2755`
- derived production service UID/GID: `99:100`, matching the canonical projects share and checkout ownership

## Current checkout/readiness

The existing checkout is:
- branch: `feat/pi-unraid-bootstrap`
- local HEAD observed: `21cee93349dc1b0e432d0ca844234a36494a76ba`
- upstream: `origin/feat/pi-unraid-bootstrap`
- origin: `https://github.com/elmakus/pi-unraid.git`
- worktree: clean at readback time
- current local checkout does **not** yet contain `compose.yaml` or `scripts/update.sh`

The durable workstream branch has advanced well beyond that local checkout. Initial M03 bootstrap therefore requires an explicit clean fast-forward synchronization of this host checkout before Compose can be rendered or started. This is a live repository mutation and is part of the M03-T01 authorization gate.

## Canonical persistent paths

Read-only readback:
- `/mnt/user/appdata/pi-unraid` — missing
- `/mnt/user/appdata/pi-unraid/home` — missing
- `/mnt/user/pi-worktrees` — missing
- `/mnt/user/projects` — present

The accepted Compose contract uses `create_host_path: false`, so M03-T01 must deliberately create the missing canonical paths with ownership compatible with `99:100` before first production start. No path was created during readiness.

## Service/image collision and workstation baseline

No existing `pi-unraid` container was present. Existing `pi-unraid:*` images are fixture/build artifacts from M01/M02 and do not represent a production deployment.

Independent workstation baseline before Pi deployment:
- container: `chatgpt-ce-workstation`
- container ID: `ba960b239bd29c1908e314ea64b9d44c8883f238feaa4367e6d889227713d5a7`
- image ID: `sha256:9ede8f1f522a710707acac32d01fd8c4d7671b91912791e299d1c635d964b893`
- state: running / healthy
- restart policy: `unless-stopped`

M03 must compare this baseline after Pi deployment and again around any authorized Docker/host restart. Pi work must not modify the workstation.

## Backup readiness

The installed Appdata Backup configuration includes `/mnt/user/appdata` in its allowed sources, with daily scheduling and verification enabled by default. Because `pi-unraid` does not exist yet, there is no container-specific Pi entry to inspect.

After production deployment, M03 must verify that the new Pi appdata path/container is actually included and not marked skipped. Read-only readiness establishes that the canonical appdata root is within the configured backup source surface; it does not claim a completed Pi backup.

## Current Compose contract to deploy

The durable branch Compose contract:
- service `pi`
- image `pi-unraid:local`, repository-owned build context
- `restart: unless-stopped`
- `stop_grace_period: 20s`
- `PI_UID` / `PI_GID` configurable; M03 target values derived as `99:100`
- `TZ=Europe/Zurich`
- readiness healthcheck through `pi-unraid-service health`
- binds only `/mnt/user/appdata/pi-unraid/home`, `/mnt/user/projects`, `/mnt/user/pi-worktrees`
- no published port, Docker socket, host-root or unrelated appdata mount
- bounded json-file logging `10m × 3`

## M03 preparation conclusion

The next bounded operation is production bootstrap/initial deployment. It is technically derivable, but it is not authorized by read-only readiness.

Required explicit gate before execution:
1. permission to fast-forward the live host checkout on `feat/pi-unraid-bootstrap`;
2. permission to create the missing Pi appdata/worktree directories;
3. permission to build/start the production `pi-unraid` Compose service with target UID/GID `99:100`.

Native ChatGPT login, Git/GitHub write acceptance, deployment update/rollback and host/Docker restart remain later gates and are not authorized by this readiness result.
