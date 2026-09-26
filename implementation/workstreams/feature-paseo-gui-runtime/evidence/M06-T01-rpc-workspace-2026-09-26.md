# M06-T01 RPC workspace flow evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T01.md`, Board rev 96 `in_progress`.
- Implementation subject: `elmakus/pi-unraid@f2fcf37b4932fc33a8b206a42cf2341b97859b8f` plus uncommitted acceptance-gap remediation below (Main commits; exact new SHA assigned at commit; prior implementation `f97f69fd36047521d6e0346d0db78291eafd1f13`).
- Exact-SHA CI: [Paseo RPC workspace flow run 36266005842](https://github.com/elmakus/pi-unraid/actions/runs/36266005842), SUCCESS on `f2fcf37`. Artifact `paseo-rpc-workspace-evidence` holds the readback, flow report, production-refusal proof, seed record/metadata, build log, and smoke log. Run 36266005842 remains valid for the direct-Pi and workspace legs but cannot alone close M06-T01 (see acceptance-gap remediation below); a re-run on the new SHA is required.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
- P4 authority blob `3c0949e50b41100630b8e57f7dc51472e183f49c` at `f87ec5df4215af06302765bad615a6be69a295ef` revalidated unchanged.
- Exact predecessor blobs revalidated via `git rev-parse` and in CI: M05-T03-R02 `b526cf47`, M02-T01 `e5075d47`, M02-T03 `0d13d7fe` (all match Card bindings).
- Contract suite: 16 suites / 271 tests GREEN locally (15 pre-existing suites 243 tests plus `test_paseo_rpc_workspace_contract.py` 28 tests incl. 5 ownership/visibility and 11 recovery/spawn regressions); CI re-run on the new SHA pending.
- Static readback (local; CI re-run pending): verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`.
- Disposable Docker flow: GREEN in CI run 36266005842 for the direct-Pi/workspace legs (details below); strengthened recovery verification and the new Paseo-driven spawn probe execute on the next CI run. No Docker in this workstation; live execution happens only on the hosted runner.
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no credentials/OAuth/phone/GraphQL-mutation/UX proof attempted.

## Changed files

- `scripts/paseo_rpc_workspace_flow.py` (new): `readback` static verifier; `flow --scope disposable` end-to-end (fixture, configure, RPC on-demand x2, workspace readback before/after, session-loss simulation, durable-Git recovery with object-store content verification, image-label binding, lingering-container asserts, nested-ownership probe, failure-report emission); `paseo-spawn --scope disposable` true Paseo-driven Pi spawn probe (disposable daemon, provider diagnostic, `run --provider pi`, daemon-child observation, auth-gate classification). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_rpc_workspace_contract.py` (new): 28 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-rpc-workspace.yml` (new): predecessor binding checks, complete 16-suite run, static readback assert, frozen-candidate build, disposable flow with recovery-detail asserts, Paseo-driven spawn probe step, production-scope refusal proof, evidence artifact upload; piped steps use `set -o pipefail`.
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI run 36266005842) |
| --- | --- | --- | --- |
| Exact frozen candidate Pi RPC on-demand | Direct `pi --mode rpc --no-session` probes x2 (child mechanism) plus Paseo-driven `run --provider pi` spawn probe (orchestration) | Policy checks GREEN | Direct leg GREEN in run 36266005842; Paseo-driven leg pending new probe (not inferred from direct leg) |
| RPC absence without session not a failure; no permanent RPC | No `rpc` wiring in compose; `docker ps ancestor` lingering asserts | GREEN | GREEN (no lingering containers) |
| Explicit project selection, no conversational inference | AGENTS.md user-driven/no-inference rules + contract tests | GREEN | Static (no live leg needed) |
| Canonical PW/Git recovery before managed mutation | project-recovery bootstrap locator + flow recovery phase re-reading committed project/board state from Git objects | Verifier unit GREEN | Prior HEAD-only leg GREEN in run 36266005842; content-verified leg pending re-run |
| Session-loss recovery without blind replay; no second board | Session dirs destroyed and proven absent, managed files byte-compared, HOME scanned for board markers, committed project/board content re-derived from `git show HEAD:` | Verifier unit GREEN | Prior leg GREEN in run 36266005842; strengthened leg pending re-run |
| Workspaces/worktrees outside HOME, intended roots only | Compose targets exactly /home/paseo /projects /worktrees + live /proc/mounts count | Static GREEN | GREEN (2 mounts, root /worktrees) |
| Host ownership 99:100, non-root upstream identity | Compose user mapping + live stat/id + host stat + nested probe | Static GREEN | GREEN (nested_ownership_ok) |
| 1 GiB shm | Compose shm_size + live `df -B1 /dev/shm` equality | Static GREEN | GREEN (1073741824 bytes) |
| No CPU/RAM caps | Forbidden-key scan (cpus/mem_limit/mem_reservation/deploy/privileged) | GREEN | Static |
| Bounded logs/rotation | json-file max-size 10m max-file 3 | GREEN | Static |
| Autostart config validated, production autostart not enabled | restart unless-stopped static check, no enable path in harness, no lingering containers | GREEN | GREEN (none lingering, none enabled) |
| Candidate/image identity + machine-readable readback | readback JSON + image label `io.pi-unraid.candidate-id` assert in flow | Static GREEN | GREEN (label matches candidate) |
| Fail-closed HA deferral | 11-item deferred list (10x M07-T02, production confirmation M07-T03), scope/production-path guards | GREEN | GREEN (production scope refused in CI) |

## CI GREEN run 36266005842

- Scope/outcome: `scope: disposable`, `outcome: integrated_flow_green`, `production_mutation: false`, `full_green_claimed: false`.
- Image: tag `pi-unraid:paseo-b4e0c1e7c276`, id `sha256:be3a6e7abc2285e4da0bf5187aa5b5935f04487fead222d37355ca4fa3685b7d`, label candidate `sha256:b4e0c1e7...` matching the frozen candidate.
- Phases, all `ok`: fixture, configure, rpc_on_demand, workspace_readback_before, session_loss, recovery, workspace_readback_after.
- RPC: both fresh provider-free probes `success: true`; zero lingering containers afterward.
- Workspace readback (before and after): runtime `99:100` non-root, shm `1073741824` bytes, ownership `99:100` on all mounts with matching host-visible ownership, `nested_ownership_ok: true`, 2 workspace mounts, worktrees root `/worktrees`.
- Session loss: managed instructions intact and byte-identical, instruction-plane status `in_sync`, zero second-board markers in HOME.
- Recovery: `decision: recovered_from_durable_git_no_replay`, durable HEAD `779d8a2aa160db97908d8f08e101981a2a467c42` identical before and after; `worktree_clean: false` reflects only the intentionally untracked fixture `PROJECT.md` (stable across the loss; HEAD identity is the recovery criterion).
- Seed build/test: frozen-candidate build plus full smoke suite GREEN (`test: ok`, incl. instruction-plane fresh-RPC and global-capabilities compatibility smokes).
- Production refusal step GREEN: `flow --scope production` refused with `refusing non-disposable scope`; `/mnt/user/appdata/pi-unraid` absent and no seed containers left running.

## CI-host portability

The workflow reuses the proven M05-T03 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, root-chown cleanup). The harness is stdlib-only. Fixture git operations use local `-c` identity (no global mutation). No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03.

## First RED run 36265204193 and repair history

- Run: https://github.com/elmakus/pi-unraid/actions/runs/36265204193 on `f97f69fd36047521d6e0346d0db78291eafd1f13`. Contract suite, static readback, and frozen-candidate build passed; disposable flow failed at the recovery-phase container git call: `fatal: detected dubious ownership in repository at '/projects/m06-t01-fixture'` (exit 128).
- Root cause: the host creates the fixture git repository as the runner UID, then the harness transferred only the top-level fixture directories to 99:100 (non-recursive `chown`). Nested `.git` stayed runner-owned, so container git as 99:100 refused it. Earlier phases (fixture, configure, RPC on-demand x2, workspace readback before, session loss) passed in CI.
- Repair (committed as `f2fcf37`): `chown_fixture` helper applies recursive transfer of home/projects/worktrees to 99:100, so container git works with zero trust exceptions; no `safe.directory` workaround, no global git config writes, no production ownership or image-input changes. `workspace_readback` runs a nested-ownership live probe (`find` for paths outside 99:100) that fails loudly on any recurrence. Fixture cleanup chown is recursive as well.
- Fail-visibility repair: `set -o pipefail` on the three piped workflow steps (build, readback, flow) so the original command failure stops the step; the harness emits a machine-readable `outcome: failed` report on flow errors (never overwriting success), collected by the always-upload artifact.
- Regression tests: 5 hermetic tests (recursive chown argv incl. `-R`, call-site wiring, nested-probe coverage, failure-report emission/no-overwrite, piped-step pipefail), all RED before the repair and GREEN after.

## Acceptance-gap remediation (uncommitted; CI re-run pending)

Main found two Card-acceptance proof gaps in the run 36266005842 subject; no result is normalized yet.

1. Committed canonical fixture state. The old fixture wrote `PROJECT.md` but committed `--allow-empty`, leaving the worktree dirty and recovery a HEAD-only comparison. The harness now commits contentful `PROJECT.md` (project identity plus explicit-selection rule) and `canonical-state.json` (project, explicit selection, Board path/revision 96, authority refs), asserts a clean worktree at creation, and after session loss re-reads both files from the Git object store (`git show HEAD:`), verifies project identity/selection/board locator, requires a clean worktree and identical HEAD, and requires the sessions directory to be absent so recovery cannot draw on session text. Six hermetic regression tests fail on session presence, HEAD drift, dirty status, and absent/corrupt/tampered content; the suite also proves `--allow-empty` is gone. CI asserts the recovery detail (`worktree_clean`, project, explicit selection, sessions absent, board locator).
2. Paseo-driven Pi spawn proof. The old flow proved direct `pi --mode rpc --no-session` but not Paseo-to-Pi orchestration. Inspection of the exact frozen upstream `getpaseo/paseo@v0.9.2` docs (`public-docs/cli.md`, `docs/providers.md`) plus repo/M02 evidence established a real noninteractive interface: Paseo's Pi provider is process-backed (spawns `pi --mode rpc`, binary presence is the documented provider requirement); the v0.9.2 CLI offers `paseo provider diagnostic pi --json` (secret-free wiring probe incl. resolved version) and `paseo run --provider pi --background` (agent launch against the local daemon via `--home`, no pairing/password documented for local endpoint ops). New `paseo-spawn` probe: disposable compose daemon with `/api/health` readiness, diagnostic asserting frozen Pi 0.87.1 resolution, background Pi-provider agent run, up-to-90s poll for a `pi --mode rpc` child whose parent is the daemon worker (node/paseo), best-effort agent stop, full cleanup. Auth/onboarding/relay failures classify loudly as `PASEO_SPAWN_BLOCKED:<gate>` with the exact upstream error instead of an inferred GREEN; any other anomaly fails with raw evidence. Five hermetic tests cover the ps parser, gate classifier, diagnostic check, CLI wiring, and scope refusal. No fake wrappers; turn success is not asserted (model auth stays HA-owned).

## Residual risks

- Direct-Pi RPC handling follows the M02 smoke contract and is proven GREEN on this exact candidate/image pair; the Paseo-driven spawn leg executes for the first time on the next CI run and may return an honest `PASEO_SPAWN_BLOCKED` gate instead.
- If the spawn probe reports a first-auth gate, the minimal human gate is the already-planned M07-T02 staged interactive proof (secret supply plus first provider/account interaction on the staged runtime), reusing this probe's daemon/CLI mechanics with credentials present.
- Review requirement `required` per Card; independent implementation review still due. Exit claimed is M06 technical GREEN with HA outstanding only.
