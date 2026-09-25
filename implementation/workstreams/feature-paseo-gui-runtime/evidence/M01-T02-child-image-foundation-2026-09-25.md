# M01-T02 — Paseo child-image foundation verification

Date: 2026-09-25
Card: `M01-T02`
Implementation acceptance: **GREEN pending independent review**

## Immutable implementation subject

- Implementation commit: `00942c095f1b03636d07ffd06f0071e0027ffea8`
- Dockerfile: `Dockerfile@8d969ca746c3506897901a55cdff8cf050a43a48`
- Contract tests: `tests/test_paseo_child_image_contract.py@09a146f356794bffc8350da5808266096662740f`
- CI workflow: `.github/workflows/paseo-child-image.yml@6603b0b1435d6586ad284989fc2098295fef762b`
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`

## CI/readback

GitHub Actions run `36144249446` completed successfully for exact commit `00942c095f1b03636d07ffd06f0071e0027ffea8`.

- Existing candidate-resolver suite: 4/4 tests GREEN.
- M01-T02 child-image contract suite: 6/6 tests GREEN.
- Docker build: GREEN.
- Built image ID in this disposable CI build: `sha256:158aea1c0c56f6c64736e87122a84f6c97bfef2147e4c00cd0f6bd9fea5a7965`.
- Candidate label readback matched `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`.

## Exact foundation checks

- Base pull resolved `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136` with linux/amd64 manifest `sha256:79bf8774b0d71ab3afed3d0f4dc556b160de9d2e15841786eb92b446540dc791`.
- Pi `0.87.1` installed and version readback passed.
- Playwright `1.63.0` installed and version readback passed.
- Playwright downloaded Chrome for Testing `153.0.8010.12`, Chromium revision `1243`, and the matching headless shell into image-owned `/opt/ms-playwright`.
- Xvfb is installed and `command -v Xvfb` returned `/usr/bin/Xvfb`.
- GitHub CLI asset checksum `sha256:9bca2d1c16825f109907a23307628a2f0698fbf99662b73a5cf0b020293072b8` validated before install.
- Docker CLI readback returned `Docker version 29.8.1, build 4a63305`, matching the frozen source-commit prefix.
- Docker Compose asset checksum `sha256:db1889184726840f75c4f9c001048430d4f25b3be3cb084d3ddd762bc0aed576` validated and `docker compose version --short` returned `5.5.1`.

## Upstream-contract and scope checks

The deterministic contract test confirms the child Dockerfile contains no legacy Node base selector, `/home/pi` identity rewrite, NOPASSWD sudo contract, legacy pi-unraid entrypoint/service, or child `USER`/`ENTRYPOINT`/`CMD` override. Therefore the exact Paseo parent's `/home/paseo`, root-capable setup entrypoint, gosu drop to the `paseo` user, server command, healthcheck and volume contract remain inherited.

This Card performed a build only. It did **not** start a Paseo container, deploy a temporary or production runtime, change Compose persistence/ownership, configure Relay/auth, install SpecPi/pi-mcp-adapter, mutate Unraid host control, or perform OR/PW-extension integration. Executable image/runtime smoke remains M01-T03.
