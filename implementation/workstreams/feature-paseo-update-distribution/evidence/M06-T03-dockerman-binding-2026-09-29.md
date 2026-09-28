# M06-T03 execution evidence — stock DockerMan guard binding

Date: 2026-09-29
Implementation subject: `8b236ed040343b60b9fa692c50ba0f8edbc375b2`

- Exact installed target: Unraid `7.2.4`.
- Read-only stock DockerMan inspection shows the Update path pulls the selected repository, stops/removes the existing container, recreates/starts it, flushes DockerMan caches, then removes the old orphan image when the image ID changed.
- Stock DockerMan therefore supplies no project pre-hook, but the accepted architecture already pre-arms the exact durable transaction guard before production `:accepted` exposure. The stock gesture can be bound after the gesture by authoritative Docker inspect of the running immutable digest against that pre-armed candidate binding; DockerMan status/cache is not an authority input.
- Added `scripts/paseo_dockerman_binding.py` to require exact guard binding plus authoritative running-image digest equality before entering M06-T02 immediate acceptance.
- Added regression coverage proving exact inspect binds, wrong/stale digest cannot masquerade as success, inspect failure stays fail-closed in `armed`, and restart/readback after committed is idempotent.
- Tower checkout outside the system temporary directory: focused guard/immediate-acceptance/DockerMan suite 16/16 GREEN; full repository suite 494/494 GREEN; `git diff --check` GREEN.
- Read-only production baseline after tests: `pi-unraid-paseo-1` remains running/healthy on `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`; no real transaction guard was created at the checked production path.
- No production `:accepted` movement, production restart/cutover/rollback, DockerMan core patch or custom dashboard was performed.
