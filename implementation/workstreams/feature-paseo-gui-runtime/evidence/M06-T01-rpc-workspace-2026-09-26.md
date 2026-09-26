# M06-T01 RPC workspace flow evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T01.md`, Board rev 96 `in_progress`.
- Implementation subject: `elmakus/pi-unraid@24a45813094a22e2a189692204804a54a51c0a6a` (priors `f97f69fd36047521d6e0346d0db78291eafd1f13`, `f2fcf37b4932fc33a8b206a42cf2341b97859b8f`, `f914dcf355528691dd36913cd8c60eb8a1dbfddf`, `1470e9340e494d7e8ea05a176531bec66df66f6e`).
- Exact-SHA CI: [run 36271351095](https://github.com/elmakus/pi-unraid/actions/runs/36271351095), SUCCESS on `24a4581`. M06-T01 automatic spawn and recovery acceptance is proven on this SHA: readback `technical_green_ha_outstanding`, disposable flow `integrated_flow_green`, Paseo-driven spawn `paseo_spawn_green`, 284-test suite, build, and production-scope refusal all GREEN. Provider model-turn authentication remains deferred to late HA (M07); no full M06 milestone, production, login, pairing, or model-turn claim is made.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
- P4 authority blob `3c0949e50b41100630b8e57f7dc51472e183f49c` at `f87ec5df4215af06302765bad615a6be69a295ef` revalidated unchanged.
- Exact predecessor blobs revalidated via `git rev-parse` and in CI: M05-T03-R02 `b526cf47`, M02-T01 `e5075d47`, M02-T03 `0d13d7fe` (all match Card bindings).
- Contract suite: 16 suites / 284 tests GREEN locally and in CI run 36271351095 (15 pre-existing suites 243 tests plus `test_paseo_rpc_workspace_contract.py` 41 tests incl. ownership/visibility, recovery, and spawn/diagnostics/witness regressions).
- Static readback (local and CI): verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`.
- Disposable Docker flow and spawn probe: GREEN in CI run 36271351095 (details below). No Docker in this workstation; live execution happened only on the hosted runner.
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no credentials/OAuth/phone/GraphQL-mutation/UX proof attempted.

## Changed files

- `scripts/paseo_rpc_workspace_flow.py` (new): `readback` static verifier; `flow --scope disposable` end-to-end (fixture, configure, RPC on-demand x2, workspace readback before/after, session-loss simulation, durable-Git recovery with object-store content verification, image-label binding, lingering-container asserts, nested-ownership probe, failure-report emission); `paseo-spawn --scope disposable` true Paseo-driven Pi spawn probe (disposable daemon, provider diagnostic, `run --provider pi`, comm-plus-daemon-ancestry witness with agent binding and error classification, `/proc` snapshots, auth-gate classification, in-probe secret-safe diagnostics with guaranteed failure report on any exception path). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_rpc_workspace_contract.py` (new): 41 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-rpc-workspace.yml` (new): predecessor binding checks, complete 16-suite run, static readback assert, frozen-candidate build, disposable flow with recovery-detail asserts, Paseo-driven spawn probe step with witness/agent asserts, production-scope refusal proof, evidence artifact upload (incl. spawn probe tee output); piped steps use `set -o pipefail`.
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI run 36271351095) |
| --- | --- | --- | --- |
| Exact frozen candidate Pi RPC on-demand | Direct `pi --mode rpc --no-session` probes x2 (child mechanism) plus Paseo-driven `run --provider pi` spawn probe (orchestration) | Policy checks GREEN | GREEN both legs (direct probes + daemon-bound pi child) |
| RPC absence without session not a failure; no permanent RPC | No `rpc` wiring in compose; `docker ps ancestor` lingering asserts | GREEN | GREEN (no lingering containers) |
| Explicit project selection, no conversational inference | AGENTS.md user-driven/no-inference rules + contract tests | GREEN | Static (no live leg needed) |
| Canonical PW/Git recovery before managed mutation | project-recovery bootstrap locator + flow recovery phase re-reading committed project/board state from Git objects | Verifier unit GREEN | GREEN (content-verified, clean, sessions absent) |
| Session-loss recovery without blind replay; no second board | Session dirs destroyed and proven absent, managed files byte-compared, HOME scanned for board markers, committed project/board content re-derived from `git show HEAD:` | Verifier unit GREEN | GREEN (content-verified) |
| Workspaces/worktrees outside HOME, intended roots only | Compose targets exactly /home/paseo /projects /worktrees + live /proc/mounts count | Static GREEN | GREEN (2 mounts, root /worktrees) |
| Host ownership 99:100, non-root upstream identity | Compose user mapping + live stat/id + host stat + nested probe | Static GREEN | GREEN (nested_ownership_ok) |
| 1 GiB shm | Compose shm_size + live `df -B1 /dev/shm` equality | Static GREEN | GREEN (1073741824 bytes) |
| No CPU/RAM caps | Forbidden-key scan (cpus/mem_limit/mem_reservation/deploy/privileged) | GREEN | Static |
| Bounded logs/rotation | json-file max-size 10m max-file 3 | GREEN | Static |
| Autostart config validated, production autostart not enabled | restart unless-stopped static check, no enable path in harness, no lingering containers | GREEN | GREEN (none lingering, none enabled) |
| Candidate/image identity + machine-readable readback | readback JSON + image label `io.pi-unraid.candidate-id` assert in flow | Static GREEN | GREEN (label matches candidate) |
| Fail-closed HA deferral | 11-item deferred list (10x M07-T02, production confirmation M07-T03), scope/production-path guards | GREEN | GREEN (production scope refused in CI) |

## CI GREEN run 36271351095

- Scope/outcome: flow `scope: disposable`, `outcome: integrated_flow_green`; spawn `outcome: paseo_spawn_green`; both `production_mutation: false`, `full_green_claimed: false`.
- Image: tag `pi-unraid:paseo-b4e0c1e7c276`, id `sha256:82ab4f99c8f5c33ea58f6e2584ef64fac7640e57304f145d67818dd92d7cf57e`, label candidate `sha256:b4e0c1e7...` matching the frozen candidate.
- Flow phases, all `ok`: fixture, configure, rpc_on_demand, workspace_readback_before, session_loss, recovery, workspace_readback_after.
- RPC: both fresh provider-free probes `success: true`; zero lingering containers afterward.
- Workspace readback (before and after): runtime `99:100` non-root, shm `1073741824` bytes, ownership `99:100` on all mounts with matching host-visible ownership, `nested_ownership_ok: true`, 2 workspace mounts, worktrees root `/worktrees`.
- Session loss: managed instructions intact and byte-identical, instruction-plane status `in_sync`, zero second-board markers in HOME.
- Recovery: `decision: recovered_from_durable_git_no_replay`, project `m06-t01-fixture-project`, explicit selection, board `implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml` rev 96, durable HEAD `7b5c77e067edf11ce9967914f8f65b591a7ed087` identical before and after, `worktree_clean: true`, `sessions_absent: true`.
- Spawn phases, all `ok`: fixture, daemon_up, diagnostic, spawn_observed. Pi PID 218 (`comm: pi`, `cmdline: pi`, `exe: /usr/local/bin/node`) bound to daemon worker PID 48 (`parent_match: worker_pid`); agent `f15b42a3-4dbb-4941-9ec9-3504dbab76dd` provider `pi/unknown/unknown`. Agent status `error` with `error_class: model_auth`: the Paseo-to-Pi launch is proven while the model turn needs first provider authentication, which belongs to late HA (M07) and is not claimed here.
- RPC provider semantics (distinct two-part proof, no turn inferred): frozen v0.9.2 process-backed `pi --mode rpc` provider docs plus GREEN direct `pi --mode rpc --no-session` smokes (M02 instruction-plane and M06 `rpc_on_demand` x2).
- Seed build/test: frozen-candidate build plus full smoke suite GREEN; production-scope refusal step GREEN with `/mnt/user/appdata/pi-unraid` absent and no seed containers left running.

## CI-host portability

The workflow reuses the proven M05-T03 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, root-chown cleanup). The harness is stdlib-only. Fixture git operations use local `-c` identity (no global mutation). No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03.

## Prior run history (concise)

- Run 36265204193 (RED on `f97f69f`): disposable flow failed with git dubious ownership (non-recursive fixture chown left nested `.git` runner-owned). Repaired with recursive `chown_fixture`, a nested-ownership live probe, `set -o pipefail`, and failure-report emission (committed as `f2fcf37`).
- Run 36266005842 (SUCCESS on `f2fcf37`): direct-Pi/workspace legs GREEN with HEAD-only recovery; accepted as partial evidence only.
- Run 36267353405 (RED on `f914dcf`): suite, readback, build, strengthened content-verified recovery, and refusal GREEN; spawn probe RED after 90s with no failure report captured. Repaired with in-probe secret-safe diagnostics and guaranteed failure reports on every exception path (committed as `1470e93`).
- Run 36268682202 (RED on `1470e93`): everything GREEN except the spawn probe; its diagnostics report proved a real Pi child (PID 219 of daemon worker 48) missed by the literal `pi --mode rpc` predicate (bare-`pi` argv/title normalization) plus an unparsed CLI-table agent ID. Repaired with the comm-plus-daemon-ancestry witness, dynamic `workerPid` binding, table ID parsing, agent binding, and error classification (committed as `24a4581`).

## Residual risks

- The M06-T01 automatic acceptance (spawn plus recovery) is proven on the exact SHA above; provider model-turn authentication is classified `model_auth` and owned by the already-planned M07-T02 staged interactive proof (secret supply plus first provider/account interaction).
- Review requirement `required` per Card; independent implementation review still due. Exit claimed is M06-T01 technical GREEN with HA outstanding only: no full M06 milestone, production, login, pairing, or model-turn claim.
