# M06-T02 browser/tool/extension compatibility evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T02.md`, Board rev 101 `in_progress`.
- Implementation subject: `elmakus/pi-unraid@f12bb4a0ba23a61830c7ea4b4ea6f0d81b7ed513` (exact SHA on `origin/feat/paseo-gui-runtime`).
- Exact-SHA CI: [run 36276859470](https://github.com/elmakus/pi-unraid/actions/runs/36276859470), SUCCESS on `f12bb4a` (push to `feat/paseo-gui-runtime`, job `browser-tool-compat-disposable-evidence`, 3m21s, all 12 steps GREEN). M06-T02 automatic browser/tool/extension acceptance is proven on this SHA: readback `technical_green_ha_outstanding`, disposable flow `browser_tool_compat_green`, 336-test suite, build, production-scope refusal, and untouched proof all GREEN. Authenticated gh workflow, headed UX judgment, and wishlist activation remain deferred to HA/M07-T05; no full M06 milestone, production, login, pairing, or wishlist claim is made.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, Playwright 1.63.0 / Chromium 153.0.8010.12 rev 1243, SpecPi 0.34.0, pi-mcp-adapter 2.37.0, gh 2.101.0, Docker CLI 29.8.1 / Compose 5.5.1, Node 22.23.3, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
- Flow image: tag `pi-unraid:paseo-b4e0c1e7c276`, id `sha256:f3b8f2c9ba0bade5e582c9c6fe15e5abdcf9e37aff2966421f89b4e10ea489a0`, candidate label matching the frozen candidate; seed record and flow report agree.
- P4 authority blob `3c0949e50b41100630b8e57f7dc51472e183f49c` revalidated unchanged.
- Exact predecessor bindings revalidated via `git rev-parse` and pinned in CI: M06-T01 `e01bd1dd`, M04-T03 `e31658fd`, M01-T01 `4ccca450`, M01-T02 `be820f52`, M01-T03 `3772f647` (all match Card bindings; all DONE with GREEN reviews).
- Contract suite: 17 suites / 336 tests GREEN locally and in CI run 36276859470 (16 pre-existing suites 284 tests plus `test_paseo_browser_tool_compat_contract.py` 52 tests).
- Static readback (local and CI): verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`, 12 HA/M07-T05 deferrals.
- Disposable Docker flow: GREEN in CI run 36276859470 (details below). No Docker in this workstation; live execution happened only on the hosted runner.
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no credentials/OAuth/phone/GraphQL-mutation/UX judgment attempted; no wishlist activation path exists in the harness.

## Changed files

- `scripts/paseo_browser_tool_compat.py` (new): `readback` static verifier; `flow --scope disposable` end-to-end (fixture, image-label binding, headless launch + screenshot + PDF, headed/Xvfb persistent-context + screenshot + real temp/task download, container-side profile-isolation readback, dev-baseline readback, gh unauth fail-closed, Docker presence fail-closed, exact-pair extension compat with wishlist-inactive proof and adapter failure/restore observability, lingering-container asserts, failure-report emission). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_browser_tool_compat_contract.py` (new): 52 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-browser-tool-compat.yml` (new): predecessor binding checks, complete 17-suite run, static readback assert, frozen-candidate build/test, disposable flow with phase/detail asserts, production-scope refusal proof, untouched proof, evidence artifact upload; piped steps use `set -o pipefail`.
- `implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml`: rev 101, M06-T02 `in_progress` (transition only; Main owns result/review binding).
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI run 36276859470) |
| --- | --- | --- | --- |
| Headless Chromium/Playwright launch + screenshot/PDF | `chromium.launch headless:true`, version assert, `screenshot` + `pdf` to temp downloads | Probe syntax + pin checks GREEN | GREEN: Chromium 153.0.8010.12, `headless.png` + `headless.pdf` |
| Headed/Xvfb launch + screenshot + download | `xvfb-run -a` + `launchPersistentContext` on dedicated profile, `downloadsPath` temp dir, real download event | Probe syntax GREEN | GREEN: Chromium 153.0.8010.12, `headed.png` + `task-download.txt` (PDF headless-only per upstream) |
| Dedicated persistent automation profile, temp downloads, no personal profile | Container-side profile scan: 13 entries, non-empty `Default/Preferences`, exact 4-file download set, personal-path probe | Policy checks GREEN | GREEN: profile populated, downloads exact, `personal_profiles_touched: []` |
| Dev baseline shell/Git/network/build/Python/Node | Version/presence readback, Node `v22.23.3` exact, dig/getent/nc/ssh present | Dockerfile/pin checks GREEN | GREEN: bash/git/gcc/make/python present, Node `v22.23.3`, 4 network tools |
| gh binary unauthenticated mechanics only | Version pin + `gh auth status` fail-closed, no login attempted | Pin checks GREEN | GREEN: gh 2.101.0, auth exit 1, `not logged in` |
| Docker CLI/Compose presence as tooling, not host control | Version pins, socket absent, `docker ps` fail-closed; compose has no socket/ports | Static GREEN | GREEN: CLI 29.8.1 / Compose 5.5.1, socket absent, control refused |
| SpecPi core scope/wishlist inactive, exact-pair smoke | M04 delivery apply GREEN, scope policy `inactive_in_fresh_session`, marker schema without activation fields, settings exactly managed+sentinel | Policy checks GREEN | GREEN: SpecPi 0.34.0 + adapter 2.37.0, compatibility GREEN, wishlist not activated (M07-T05) |
| Adapter config/readback/failure observability | `contents_exposed: false`, missing-package RED `package_missing_or_invalid`, secret-safe, restore GREEN | Wrapper reuse checks GREEN | GREEN: config `unconfigured`/unexposed, failure RED observed, restored GREEN |
| Candidate/image identity + machine-readable readback | readback JSON + image label asserts in flow | Static GREEN | GREEN: label candidate matches, seed/flow image `f3b8f2c9` |
| Fail-closed HA/M07-T05 deferral | 12-item deferred list, scope guards, no activation path | GREEN | GREEN: production scope refused in CI |
| No lingering containers / production untouched | `docker ps ancestor` asserts, `/mnt/user/appdata/pi-unraid` absent | N/A (no Docker) | GREEN: no lingering containers, production path absent |

## CI GREEN run 36276859470

- Scope/outcome: flow `scope: disposable`, `outcome: browser_tool_compat_green`; `production_mutation: false`, `full_green_claimed: false`.
- Image: tag `pi-unraid:paseo-b4e0c1e7c276`, id `sha256:f3b8f2c9ba0bade5e582c9c6fe15e5abdcf9e37aff2966421f89b4e10ea489a0`, label candidate `sha256:b4e0c1e7...` matching the frozen candidate.
- Flow phases, all `ok`: fixture, image_labels, browser_headless, browser_headed_xvfb, profile_isolation, dev_baseline, gh_unauth, docker_tooling, extension_compat.
- Browser: headless and headed/Xvfb both Chromium `153.0.8010.12`; headless screenshot + PDF; headed screenshot + verified `task-download.txt` content; automation profile 13 entries with non-empty `Default/Preferences`; downloads exactly the 4 expected files; zero personal-profile paths touched (host HOME untouched by browser, container HOME scan clean).
- Tooling: Node `v22.23.3` exact with bash/git/gcc/make/python3/dig/getent/nc/ssh readback; gh `2.101.0` unauthenticated fail-closed (exit 1, `not logged in`); Docker CLI `29.8.1` / Compose `5.5.1` present with socket absent and `docker ps` fail-closed.
- Extension: apply GREEN `in_sync` with SpecPi `0.34.0` + adapter `2.37.0`, compatibility marker GREEN, scope `inactive_in_fresh_session`, wishlist activation not performed (owner M07-T05), adapter config `unconfigured` with `contents_exposed: false`; bounded missing-adapter failure observed RED `package_missing_or_invalid` with secret-safe readback and settings untouched, then restored GREEN.
- Seed build/test: frozen-candidate build plus full smoke suite GREEN (incl. M02-T03 instruction-plane and M04-T03 global-capability smokes); production-scope refusal step GREEN with `/mnt/user/appdata/pi-unraid` absent and no seed containers left running.

## CI-host portability

The workflow reuses the proven M05-T03/M06-T01 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, root-chown cleanup). The harness is stdlib-only plus repo scripts. Extension-leg `pi install` uses the same npm-registry path already proven by the M04-T03 CI disposable verifier. No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03. PDF is asserted headless-only per upstream Playwright design.

## Prior run history (concise)

- Run 36273187258 (RED on `868915c`): headed leg crashed at launch under numeric `--user 99:100`. Repaired with default-user browser context, `0777` fixture dirs, full failure diagnostics, `phases_completed` (committed as `f22f08f`).
- Run 36273641228 (RED on `f22f08f`): host chmod after chown failed EPERM before any phase. Repaired with chmod-before-chown ordering (committed as `1902848`).
- Run 36274045464 (RED on `1902848`): browser legs live-GREEN; wrong top-level `Preferences` path. Repaired with `Default/Preferences` marker (committed as `c5b10dd`).
- Run 36274364618 (RED on `c5b10dd`): host-side stat of 0600 `Default/Preferences` denied. Repaired with container-side profile/downloads readback (committed as `60bcd29`).
- Run 36276154540 (RED on `60bcd29`): isolation live-GREEN; multi-line `network_tools` value parsed to one path. Repaired with space-joined probe plus `parse_dev_baseline` (committed as `0c6bdd2`).
- Run 36276486393 (RED on `0c6bdd2`): legs through docker_tooling live-GREEN; host-side HOME seeding denied after chown. Repaired with container-side seeding/marker reads (committed as `f12bb4a`).
- No repair weakened an assertion, excluded a phase, or changed candidate/image inputs.

## Residual risks

- The M06-T02 automatic acceptance (browser/tool/extension compatibility) is proven on the exact SHA above; authenticated gh workflow proof and headed UX judgment are owned by the already-planned M07-T02 staged interactive proof, and wishlist activation by conditional post-deploy M07-T05.
- Review requirement `required` per Card; independent implementation review still due. Exit claimed is M06-T02 technical GREEN with HA outstanding only: no full M06 milestone, production, authenticated, UX-judgment, or wishlist-activation claim.
- Project Workflow Main owns the single semantic result/review binding; this file is the worker evidence contribution, not the semantic result.
