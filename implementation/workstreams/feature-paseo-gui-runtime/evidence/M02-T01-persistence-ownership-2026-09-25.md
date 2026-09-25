# M02-T01 — Paseo persistence/workspace ownership evidence

Date: 2026-09-25
Card: `M02-T01`
Final implementation commit: `bc4e6cf3979f8d55ac7640a51a3638438cd32365`

## Exact implementation subjects

- Compose runtime contract: `compose.yaml@87f57b46f485918b50f560581ea86d580abcff6e`
- Native persistent config helper: `scripts/configure-paseo-runtime.sh@4e21f5e542723a98076c753a85e80687ced3b32b`
- Disposable persistence/ownership smoke: `scripts/verify-compose-foundation.sh@3b1113bdb1f4af63e397602a54fd616632bbd8ce`
- Frozen predecessor result: `implementation/workstreams/feature-paseo-gui-runtime/results/M01-T03.md@bbc862c37c0da81a08a91876499cfe865be958ab:3772f647f5a0c55e856d3ae8e3feb05c6fb3e1f5`

## Final GitHub Actions evidence

- Workflow run: `36148683285`
- Job: `108116155699` / `contract-build-and-smoke`
- Head SHA: `bc4e6cf3979f8d55ac7640a51a3638438cd32365`
- Conclusion: **success**
- Exact M01-T03 dependency binding: GREEN
- Candidate resolver tests: 4/4 GREEN
- M01 child-image contract tests: 6/6 GREEN
- M02-T01 runtime contract tests: 5/5 GREEN
- Frozen Paseo child-image build: GREEN
- Disposable image/provenance smoke: GREEN
- Disposable persistence/ownership/recreate smoke: GREEN
- Immutable foundation metadata readback: GREEN

## Runtime/readback

The exact CI image was:

- Candidate ID: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- Built image ID: `sha256:7f1565cd33ab0b0bf04793ce2c2ea7a8428071a4e7ea6fc8f9e99978b0f1d41e`
- Paseo: `0.9.2`
- Pi: `0.87.1`
- Playwright: `1.63.0`
- Chromium headless/headed-Xvfb: `153.0.8010.12`
- Paseo `/api/health`: GREEN
- High-confidence image config/history secret scan: GREEN

The disposable persistence smoke emitted:

```json
{"card":"M02-T01","home_persisted":true,"projects_persisted":true,"worktrees_persisted":true,"worktrees_root":"/worktrees","runtime_uid":99,"runtime_gid":100,"shm_bytes":1073741824,"resource_caps":"none","result":"GREEN"}
```

The smoke also verified:

- normal container identity is non-root numeric `99:100`, using the upstream-supported Compose `user:` path rather than rewriting Paseo's image UID/GID;
- `/home/paseo`, `/projects` and `/worktrees` are the only runtime bind targets in this Card and all use explicit host paths with `create_host_path: false`;
- native Paseo `worktrees.root` is persisted in `/home/paseo/.paseo/config.json` as `/worktrees`;
- HOME, project and worktree markers survive container removal/recreation;
- marker/config ownership remains numeric `99:100` on the bind-mounted host filesystem;
- shared memory is exactly 1 GiB, Docker Memory/NanoCpus are uncapped, the container is not privileged, and json-file logging is bounded to 10 MiB x 3;
- the fixture container/network and temporary host directories are removed by the smoke cleanup path; no production/Tower runtime was deployed or mutated.

## Repair history

Two earlier CI attempts were intentionally not accepted:

- `36147966745`: RED because the test seeded `--home /home/paseo` instead of the upstream `PASEO_HOME=/home/paseo/.paseo`.
- `36148342609`: RED because the GitHub runner correctly could not traverse private `.paseo` state owned by UID 99 for a host-side `stat`; the final smoke reads numeric bind ownership through a disposable root inspector without weakening HOME permissions.

Only the final exact subject/run above is acceptance evidence.
