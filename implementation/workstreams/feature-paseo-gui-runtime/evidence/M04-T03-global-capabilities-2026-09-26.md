# M04-T03 — SpecPi/MCP/global capability delivery evidence

Date: 2026-09-26
Card: `M04-T03`
Implementation subject: `elmakus/pi-unraid@8914f92b3f832e81c28b276e0ebee08d374f5013`

## Exact predecessors

- `M02-T03`: `cac4ac5e5a4b6c96ad71d9bbce12962388f7a4be:implementation/workstreams/feature-paseo-gui-runtime/results/M02-T03.md@0d13d7fe5a6dd29fb68e700d13cc5c1251722c28`
- `M04-T01`: `affd83590ec534ed144b9048a2b9075434761f27:implementation/workstreams/feature-paseo-gui-runtime/results/M04-T01.md@5173447ec3ab8775450a9defbf193aede63ca290`
- `M04-T02`: `e9a412557bfbe927a64b1f7ba0d892f5f059e08a:implementation/workstreams/feature-paseo-gui-runtime/results/M04-T02.md@c6adc8514548b701c3aa959df9f5a6f4ff581a9d`

## Implemented surface

- The frozen candidate remains authoritative for the exact approved global packages: `specpi@0.34.0` and `pi-mcp-adapter@2.37.0`; no latest/version-line resolution was introduced by this Card.
- `scripts/pi_global_capabilities.py` manages only the accepted Pi-native global package declarations/state in persisted HOME and preserves unrelated Pi settings/provider state.
- Apply remains RED until the exact compatibility smoke has produced its private compatibility marker; status is read-only and returns RED on missing/invalid managed package state.
- Rollback restores only the prior managed-package declarations captured in the bounded private snapshot and then permits deterministic re-apply.
- SpecPi scope policy remains `inactive_in_fresh_session`; no PW scope authority or OR runtime-use policy was copied into pi-unraid.
- The disposable verifier proves package load/readback, MCP surface availability, inactive SpecPi scope, preservation of unrelated settings, read-only status, rollback/re-apply, UID/GID 99:100 behavior and private `0600` state files.
- Verifier fixture operations that must act as the Paseo user are executed through the child image as UID/GID 99:100; the temporary bind root is traversable while private state files remain private.

## Exact CI/readback

GitHub Actions run `36213649679` (run #42):
- workflow: `Paseo image and runtime foundation`
- job: `contract-build-and-smoke`
- exact head SHA: `8914f92b3f832e81c28b276e0ebee08d374f5013`
- conclusion: `success`

The exact-SHA job completed GREEN for:
- exact predecessor bindings;
- the complete candidate/image/runtime/Relay/Pi instruction-plane/Pi global-capability/GraphQL/host-safety/host-doctor/environment-inventory/environment-control contract suite;
- frozen Paseo child-image build;
- disposable image/provenance smoke;
- disposable persistence/ownership smoke;
- disposable Pi instruction-plane smoke;
- disposable Pi global-capability smoke;
- immutable foundation metadata inspection.

Disposable image/provenance readback on the successful run reported candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`, image `sha256:f41cdcf6c89179d496606314d5d8b7696839baf3424f9f37f91dffa591f8c18f`, Paseo `0.9.2`, Pi `0.87.1`, Playwright `1.63.0`, Paseo health GREEN and secret scan GREEN.

The M04-T03 disposable smoke returned:
`{"card":"M04-T03","global_packages":2,"compatibility_smoke":true,"scope_inactive":true,"mcp_surface":true,"status_read_only":true,"rollback_reapply":true,"runtime_uid":99,"runtime_gid":100,"result":"GREEN"}`

A separate detached worktree on Tower at the same exact implementation SHA also ran `bash -n scripts/verify-pi-global-capabilities.sh` and the M04-T03 disposable verifier against the prepared child image; it completed GREEN with exit code 0.

## Boundary

No production/Tower Paseo deployment, live MCP credential materialization, SpecPi scope activation, OR policy mutation, PW authority mutation, coordinated global version-line update, M05 update orchestration, or M06 integrated acceptance was performed by M04-T03.
