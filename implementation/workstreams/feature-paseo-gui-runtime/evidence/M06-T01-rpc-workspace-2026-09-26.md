# M06-T01 RPC workspace flow evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T01.md`, Board rev 96 `in_progress`.
- Working base: `elmakus/pi-unraid@7ea95d5823b8464fd874c1d965be55b595e95e86` plus uncommitted worker changes below (Main commits; exact implementation SHA assigned at commit).
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
- P4 authority blob `3c0949e50b41100630b8e57f7dc51472e183f49c` at `f87ec5df4215af06302765bad615a6be69a295ef` revalidated unchanged.
- Exact predecessor blobs revalidated via `git rev-parse`: M05-T03-R02 `b526cf47`, M02-T01 `e5075d47`, M02-T03 `0d13d7fe` (all match Card bindings and HEAD).
- Local contract suite: 16 suites / 260 tests GREEN via `python3 -m unittest` (15 pre-existing suites 243 tests plus `test_paseo_rpc_workspace_contract.py` 17 tests incl. 5 ownership/visibility regressions).
- Static readback: `python3 scripts/paseo_rpc_workspace_flow.py readback` verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`.
- Disposable Docker flow: first CI execution RED at run 36265204193 (dubious-ownership, see repair section below); repair implemented locally, re-run pending Main's push. No Docker in this workstation.
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no credentials/OAuth/phone/GraphQL-mutation/UX proof attempted.

## Changed files

- `scripts/paseo_rpc_workspace_flow.py` (new): `readback` static verifier plus `flow --scope disposable` end-to-end (fixture, configure, RPC on-demand x2, workspace readback before/after, session-loss simulation, durable-Git recovery, image-label binding, lingering-container asserts). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_rpc_workspace_contract.py` (new): 12 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-rpc-workspace.yml` (new): predecessor binding checks, complete 16-suite run, static readback assert, frozen-candidate build, disposable flow, production-scope refusal proof, evidence artifact upload.
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI disposable) |
| --- | --- | --- | --- |
| Exact frozen candidate Pi RPC on-demand | `pi --mode rpc --no-session` get_state probes x2 across recreate boundary | Policy checks GREEN | Pending first CI run |
| RPC absence without session not a failure; no permanent RPC | No `rpc` wiring in compose; `docker ps ancestor` lingering asserts | GREEN | Pending first CI run |
| Explicit project selection, no conversational inference | AGENTS.md user-driven/no-inference rules + contract tests | GREEN | Static (no live leg needed) |
| Canonical PW/Git recovery before managed mutation | project-recovery bootstrap locator + flow recovery phase | Static GREEN | Pending first CI run |
| Session-loss recovery without blind replay; no second board | Session dirs destroyed, managed files byte-compared, HOME scanned for board markers, HEAD re-derived from durable fixture git | Logic GREEN | Pending first CI run |
| Workspaces/worktrees outside HOME, intended roots only | Compose targets exactly /home/paseo /projects /worktrees + live /proc/mounts count | Static GREEN | Pending first CI run |
| Host ownership 99:100, non-root upstream identity | Compose user mapping + live stat/id + host stat | Static GREEN | Pending first CI run |
| 1 GiB shm | Compose shm_size + live `df -B1 /dev/shm` equality | Static GREEN | Pending first CI run |
| No CPU/RAM caps | Forbidden-key scan (cpus/mem_limit/mem_reservation/deploy/privileged) | GREEN | Static |
| Bounded logs/rotation | json-file max-size 10m max-file 3 | GREEN | Static |
| Autostart config validated, production autostart not enabled | restart unless-stopped static check, no enable path in harness, no lingering containers | GREEN | Lingering-container leg pending CI |
| Candidate/image identity + machine-readable readback | readback JSON + image label `io.pi-unraid.candidate-id` assert in flow | Static GREEN | Label leg pending CI |
| Fail-closed HA deferral | 11-item deferred list (10x M07-T02, production confirmation M07-T03), scope/production-path guards | GREEN | Guard re-proof in CI |

## CI-host portability

The workflow reuses the proven M05-T03 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, root-chown cleanup). The harness is stdlib-only. Fixture git operations use local `-c` identity (no global mutation). No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03.

## CI run 36265204193 RED and repair (worker contribution, uncommitted)

- Run: https://github.com/elmakus/pi-unraid/actions/runs/36265204193 on implementation commit `f97f69fd36047521d6e0346d0db78291eafd1f13`. Contract suite, static readback, and frozen-candidate build passed; disposable flow failed at the recovery-phase container git call: `fatal: detected dubious ownership in repository at '/projects/m06-t01-fixture'` (exit 128).
- Root cause: the host creates the fixture git repository as the runner UID, then the harness transferred only the top-level fixture directories to 99:100 (non-recursive `chown`). Nested `.git` stayed runner-owned, so container git as 99:100 refused it. Earlier phases (fixture, configure, RPC on-demand x2, workspace readback before, session loss) passed in CI.
- Repair (this change, not yet CI-executed): `chown_fixture` helper applies recursive transfer of home/projects/worktrees to 99:100, so container git works with zero trust exceptions; no `safe.directory` workaround, no global git config writes, no production ownership or image-input changes. `workspace_readback` now also runs a nested-ownership live probe (`find` for paths outside 99:100) that fails loudly on any recurrence. Fixture cleanup chown is recursive as well.
- Fail-visibility repair: `set -o pipefail` added to the three piped workflow steps (build, readback, flow) so the original command failure stops the step; the harness now emits a machine-readable `outcome: failed` report on flow errors (never overwriting success), collected by the existing always-upload artifact. This removes the secondary missing-report exception seen in the RED run.
- Regression tests: 5 new hermetic tests (recursive chown argv incl. `-R`, call-site wiring, nested-probe coverage, failure-report emission/no-overwrite, piped-step pipefail). Focused suite 17/17 GREEN locally; full local suite re-run below. CI GREEN is not claimed; re-run happens on Main's push of the exact new SHA.

## Residual risks

- The disposable flow has not executed anywhere yet; first execution is the CI run on Main's push. RPC response-shape assumptions follow the M02 smoke contract (`type: response`, `command: get_state`, `success: true`).
- `df -B1 /dev/shm` equality assumes `--shm-size=1gb` maps exactly to 1073741824 bytes on the hosted runner (standard Docker behavior).
- Review requirement `required` per Card; independent implementation review still due. Exit claimed is M06 technical GREEN with HA outstanding only.
