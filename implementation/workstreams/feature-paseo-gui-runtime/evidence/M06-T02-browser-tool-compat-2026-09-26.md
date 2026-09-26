# M06-T02 browser/tool/extension compatibility evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T02.md`, Board rev 101 `in_progress`.
- Implementation state: worktree on `feat/paseo-gui-runtime` at base `6412551` plus uncommitted M06-T02 files listed below; no implementation SHA exists until Main commits. Worker harness forbids git writes, so commit/push and the exact-SHA CI trigger are Main-owned next steps.
- Exact-SHA CI: PENDING. Workflow `.github/workflows/paseo-browser-tool-compat.yml` defines the full gate (predecessor bindings, 17-suite run, static readback assert, frozen-candidate build, disposable flow asserts, production-scope refusal, untouched proof, artifact upload). No live Docker leg ran in this workstation (no Docker daemon); live execution must happen only on the hosted runner.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, Playwright 1.63.0 / Chromium 153.0.8010.12 rev 1243, SpecPi 0.34.0, pi-mcp-adapter 2.37.0, gh 2.101.0, Docker CLI 29.8.1 / Compose 5.5.1, Node 22.23.3, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
- P4 authority blob `3c0949e50b41100630b8e57f7dc51472e183f49c` revalidated unchanged.
- Exact predecessor bindings revalidated via `git rev-parse` and pinned in CI: M06-T01 `e01bd1dd`, M04-T03 `e31658fd`, M01-T01 `4ccca450`, M01-T02 `be820f52`, M01-T03 `3772f647` (all match Card bindings; all DONE with GREEN reviews).
- Contract suite: 17 suites / 317 tests GREEN locally (16 pre-existing suites 284 tests plus `test_paseo_browser_tool_compat_contract.py` 33 tests incl. pin/readback/guard/profile/download/wishlist-deferral/workflow regressions).
- Static readback (local): verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`, 12 HA/M07-T05 deferrals.
- Browser probe scripts: `node --check` GREEN for both headless and headed/Xvfb probes.
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no credentials/OAuth/phone/GraphQL-mutation/UX judgment attempted; no wishlist activation path exists in the harness.

## Changed files

- `scripts/paseo_browser_tool_compat.py` (new): `readback` static verifier (exact pins, Dockerfile labels/pins, tooling boundary, extension policy, 12 deferrals); `flow --scope disposable` end-to-end (fixture, image-label binding, headless launch + screenshot + PDF, headed/Xvfb launchPersistentContext + screenshot + real temp/task download, profile-isolation scan, dev-baseline readback, gh unauth fail-closed, Docker presence fail-closed, exact-pair extension compat with wishlist-inactive proof and adapter failure/restore observability, lingering-container asserts, failure-report emission). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_browser_tool_compat_contract.py` (new): 33 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-browser-tool-compat.yml` (new): predecessor binding checks, complete 17-suite run, static readback assert, frozen-candidate build/test, disposable flow with phase/detail asserts, production-scope refusal proof, untouched proof, evidence artifact upload; piped steps use `set -o pipefail`.
- `implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml`: rev 101, M06-T02 `in_progress` (transition only; Main to commit).
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI, pending push) |
| --- | --- | --- | --- |
| Headless Chromium/Playwright launch + screenshot/PDF | `chromium.launch headless:true`, version assert, `screenshot` + `pdf` to temp downloads | Probe syntax + pin checks GREEN | CI flow `browser_headless` |
| Headed/Xvfb launch + screenshot + download | `xvfb-run -a` + `launchPersistentContext` on dedicated profile, `downloadsPath` temp dir, real download event | Probe syntax GREEN | CI flow `browser_headed_xvfb` |
| Dedicated persistent automation profile, temp downloads, no personal profile | Profile `Preferences` populated assert, exact 4-file download set, host + container personal-path scans | Policy checks GREEN | CI flow `profile_isolation` |
| Dev baseline shell/Git/network/build/Python/Node | Version/presence readback, Node `v22.23.3` exact | Dockerfile/pin checks GREEN | CI flow `dev_baseline` |
| gh binary unauthenticated mechanics only | Version pin + `gh auth status` fail-closed, no login attempted | Pin checks GREEN | CI flow `gh_unauth` |
| Docker CLI/Compose presence as tooling, not host control | Version pins, socket absent, `docker ps` fail-closed; compose has no socket/ports | Static GREEN | CI flow `docker_tooling` |
| SpecPi core scope/wishlist inactive, exact-pair smoke | M04 delivery apply GREEN, scope policy `inactive_in_fresh_session`, marker schema without activation fields, settings exactly managed+sentinel | Policy checks GREEN | CI flow `extension_compat` |
| Adapter config/readback/failure observability | `contents_exposed: false`, missing-package RED `package_missing_or_invalid`, secret-safe, restore GREEN | Wrapper reuse checks GREEN | CI flow `extension_compat` |
| Candidate/image identity + machine-readable readback | readback JSON + image label asserts in flow | Static GREEN | CI readback + flow |
| Fail-closed HA/M07-T05 deferral | 12-item deferred list, scope guards, no activation path | GREEN | CI refusal step |
| No lingering containers / production untouched | `docker ps ancestor` asserts, `/mnt/user/appdata/pi-unraid` absent | N/A (no Docker) | CI untouched proof |

## CI-host portability

The workflow reuses the proven M05-T03/M06-T01 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, root-chown cleanup). The harness is stdlib-only plus repo scripts. Extension-leg `pi install` uses the same npm-registry path already proven by the M04-T03 CI disposable verifier. No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03. PDF is asserted headless-only per upstream Playwright design.

## Boundary and next transition

- Claimed now: implementation + static acceptance GREEN in worktree; M06-T02 stays `in_progress` at Board rev 101.
- Next: Main commits (board transition + implementation + evidence), pushes `feat/paseo-gui-runtime` without force, records the exact-SHA CI run of `paseo-browser-tool-compat.yml`; a follow-up worker turn then binds the CI result (or repairs RED within Card scope) before any result freeze.
- Review requirement `required` per Card; independent implementation review still due after the live CI leg is GREEN. Exit claimed is M06-T02 technical GREEN with HA outstanding only: no full M06 milestone, production, authenticated, UX-judgment, or wishlist-activation claim.
