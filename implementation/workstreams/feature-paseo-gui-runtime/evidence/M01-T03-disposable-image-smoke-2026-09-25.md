# M01-T03 — Disposable image/provenance smoke evidence

Date: 2026-09-25
Card: `M01-T03`
Implementation commit: `474fbd5fd95c7e2f1a1043f973c82c13e4a521b8`

## Exact implementation subjects

- Smoke harness: `scripts/smoke_paseo_image.py@8ee036d3607ec0ed6ef2662cff998eaa55035218`
- CI workflow: `.github/workflows/paseo-child-image.yml@b84e4bedc30a3bd968741ebcbee7a4a30b177d4f`
- Exact frozen dependency result revalidated by CI: `implementation/workstreams/feature-paseo-gui-runtime/results/M01-T02.md@4e60c855a84b2e74d50de812db1ba9cc156af400:be820f52901a9d2d4a40b71c3da6d19ffc08edea`

## GitHub Actions evidence

- Workflow run: `36146096127`
- Job: `108107533411` / `contract-build-and-smoke`
- Head SHA: `474fbd5fd95c7e2f1a1043f973c82c13e4a521b8`
- Conclusion: **success**
- Exact dependency binding check: GREEN
- Candidate resolver tests: GREEN
- M01-T02 child-image contract tests: GREEN
- Frozen child-image build: GREEN
- Disposable image/provenance smoke: GREEN
- Immutable foundation metadata readback: GREEN

## Disposable smoke readback

The smoke emitted this machine-readable result from the exact CI image:

- Candidate ID: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- Built image ID: `sha256:345e87e7f01345875603b9d8bc0bf0c4914aee6e9f8b224a03a009fc01df4c1f`
- Paseo: `0.9.2`
- Pi: `0.87.1`
- Pi provider-free RPC `get_state`: GREEN / `true`
- Playwright: `1.63.0`
- Chromium headless: `153.0.8010.12`
- Chromium headed under Xvfb: `153.0.8010.12`
- Default Paseo `/api/health`: GREEN
- High-confidence raw-secret scan of image config/history: GREEN

Baseline tool readback from the disposable image:

- Git `2.39.5`
- Python `3.11.2`
- GitHub CLI `2.101.0`
- Docker CLI `29.8.1`
- Docker Compose `5.5.1`
- Playwright CLI `1.63.0`
- `Xvfb`: `/usr/bin/Xvfb`
- `xvfb-run`: `/usr/bin/xvfb-run`

The build log also resolved the exact frozen parent `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`.

## Scope/readback

- The health smoke used only a short-lived un-published CI container and removed it after the check.
- Pi RPC was exercised without provider/model authentication or inference.
- No Compose persistence/ownership, Relay/auth, SpecPi/pi-mcp-adapter, Unraid host-control, GHCR publication, BuildKit cache/cutover/rollback, OR, future PW-extension, or production deployment work was introduced.
