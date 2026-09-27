# M03-T01 R01 — Independent implementation review

Date: 2026-09-25
Card: `M03-T01`
Attempt: `R01`
Verdict: **GREEN**

## Reviewed exact subject

- Review subject: `elmakus/pi-unraid@16e5a14f1f0357b8af40fa23602c6d6c1da24724:implementation/workstreams/feature-paseo-gui-runtime/results/M03-T01.md@1b157d85116b5a9dffab7df7766f62cc8a288f3e`
- Implementation commit named by the result: `43d082317339e6aef4362d2d456b41442dc739e1`
- Acceptance surface: `implementation/workstreams/feature-paseo-gui-runtime/cards/M03-T01.md@8878355288447c64c88e10bf430f43a0497be6ee`
- Frozen predecessor result: `implementation/workstreams/feature-paseo-gui-runtime/results/M02-T03.md@cac4ac5e5a4b6c96ad71d9bbce12962388f7a4be:0d13d7fe5a6dd29fb68e700d13cc5c1251722c28`
- Primary implementation surfaces: `scripts/unraid_graphql_host_control.py`, `scripts/configure_unraid_graphql_credential.py`, `config/unraid-host-control/permission-profile.json`, `tests/test_unraid_graphql_host_control_contract.py`, and `docs/UNRAID_GRAPHQL_HOST_CONTROL.md`.

## Independent checks

- The exact result locator was re-read at commit `16e5a14f1f0357b8af40fa23602c6d6c1da24724` and its blob matches the frozen attempt. Comparing the implementation SHA `43d082317339e6aef4362d2d456b41442dc739e1` to the result commit shows no later changes to the reviewed implementation surfaces.
- GitHub Actions run `36160307230` is completed/success on exact implementation SHA `43d082317339e6aef4362d2d456b41442dc739e1`. The single `contract-build-and-smoke` job is GREEN, including exact predecessor verification, contract tests, frozen child-image build, disposable provenance/persistence/instruction-plane smoke, and immutable metadata readback. The exact Unraid host-control contract suite ran seven tests and all seven passed.
- The GraphQL client requires an explicit `/graphql` endpoint and a private regular non-symlink API-key file, emits structured readback, and limits mutation construction to one-container `start`, `stop`, `restart`, `pause`, and `unpause`. Each mutation performs container readback before and after the write, and credential/GraphQL failures are fail-closed.
- The machine-readable permission profile has no broad role and exactly `INFO:READ_ANY`, `DOCKER:READ_ANY`, and `DOCKER:UPDATE_ANY`. The reviewed Compose/runtime surface has neither the Docker socket nor a broad host-root mount, and the M03-T01 helper does not add SSH fallback or high-impact host commands.
- Credential materialization consumes the secret through an interactive prompt or stdin, writes atomically with mode `0600`, rejects symlink targets, and exposes bounded status/fingerprint metadata rather than the raw key. Contract tests cover private-file enforcement and secret-safe install/status behavior.
- Preserved live non-secret Tower evidence binds Unraid `7.2.4`, native `unraid-api 4.37.4+ad268301`, GraphQL path `/graphql`, header `x-api-key`, the exact INFO/DOCKER permission mapping, and real unauthenticated `UNAUTHENTICATED` fail-closed behavior.
- Approved P2 explicitly moved credential-backed authenticated INFO/DOCKER readback plus reversible mutation/restoration proof from M03-T01 to mandatory M06-T04 acceptance before M07. The reviewed result does not claim that deferred proof; the earlier credential blocker remains preserved as historical evidence rather than being silently discarded.
- Authority boundaries remain intact: M03-T02 still owns SSH fallback and generalized mutation guards/rollback anchors, M03-T03 owns host-control doctor semantics, and accepted high-impact operations remain explicitly user-gated.

No acceptance-blocking defect was found.

**GREEN** — the exact reviewed subject satisfies the M03-T01 Task Card and is eligible for deterministic post-review finalization.
