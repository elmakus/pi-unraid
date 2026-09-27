# M06-T03 Relay/persistence/capability/doctor readiness evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T03.md`, Board rev 105 `in_progress`.
- Implementation subject: `elmakus/pi-unraid@4bcb5aaa8f9754a76df46603f90f0152c7891ced` (exact SHA on `origin/feat/paseo-gui-runtime`).
- Exact-SHA CI: [run 36278632419](https://github.com/elmakus/pi-unraid/actions/runs/36278632419), SUCCESS on `4bcb5aa` (push to `feat/paseo-gui-runtime`, job `relay-doctor-readiness-disposable-evidence`, 3m37s, all 12 steps GREEN). M06-T03 automatic Relay/persistence/capability/doctor acceptance is proven on this SHA: readback `technical_green_ha_outstanding`, disposable flow `relay_doctor_readiness_green`, 378-test suite, build, production-scope refusal, and untouched proof all GREEN. Real phone pairing/transfer, credentials/auth, and wishlist activation remain deferred to HA/M07-T05; no full M06 milestone, production, login, pairing, or wishlist claim is made.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`). Candidate/build inputs unchanged.
- Exact predecessor bindings revalidated locally via `git rev-parse`/`git cat-file` and pinned in CI: M06-T02 `13a49bd8`, M06-T01 `e01bd1dd`, M02-T02 `7b8574df`, M02-T01 `e5075d47`, M04-T01 `5173447e`, M04-T02 `c6adc851` (all match Card bindings; all DONE with terminal GREEN reviews).
- Contract suite: 18 suites / 378 tests GREEN locally and in CI run 36278632419 (17 pre-existing suites 336 tests plus `test_paseo_relay_doctor_readiness_contract.py` 42 tests; per-suite counts 42/27/6/5/5/6/4/9/10/7/5/13/39/11/68/28/41/52, all OK in the 2831-line job log).
- Static readback (local and CI): verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`, 14 HA/M07-T05 deferrals.
- Disposable Docker flow: GREEN in CI run 36278632419 (details below). No Docker in this workstation; live execution happened only on the hosted runner.
- Flow image: tag `pi-unraid:paseo-b4e0c1e7c276`, id `sha256:1dd9aad512310849089435fc18a7c0d0d0cb34f83ceee53e58732b03c5e46d7d`, candidate label matching the frozen candidate; seed record and flow report agree.
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no real phone, no credentials/OAuth/2FA, no authenticated gh/GraphQL, no UX judgment attempted; no wishlist activation path exists in the harness.

## Changed files

- `scripts/paseo_relay_doctor_readiness.py` (new): `readback` static verifier (candidate, Relay policy, zero-port/secret-safe shape, inventory authority, reconcile/doctor semantics, lightweight healthcheck, bounded fingerprints, no-activation policy); `flow --scope disposable` end-to-end (fixture, image labels, Relay fail-closed incl. consent gate + revocation unsupported, synthetic-identity consent simulation + keypair sha/mode container-side, compose daemon health/ports, recreate survival with sha equality, container-side secret-safe HOME scan, inventory drift without deletion, approved-only reconcile with readback, quick/full doctor GREEN/WARN/RED, credential-injection fingerprint proof, lingering-container asserts, failure-report emission). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_relay_doctor_readiness_contract.py` (new): 42 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-relay-doctor-readiness.yml` (new): 6 predecessor binding checks, complete 18-suite run, static readback assert, frozen-candidate build/test, disposable 10-phase flow with detail asserts, production-scope refusal proof, untouched proof, evidence artifact upload; piped steps use `set -o pipefail`.
- `implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml`: rev 105, M06-T03 `in_progress` (transition only; Main owns result/review binding).
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI run 36278632419) |
| --- | --- | --- | --- |
| Relay default-disabled + every enablement path fail-closed | Configure persists `relay=false`; non-consenting `pair --json` asserts `RELAY_DISABLED` | Policy checks GREEN | GREEN: `relay_default_disabled`, `pair_code: RELAY_DISABLED` |
| Pairing-helper consent gate | `require_tty` + `[y/N]` + cancel message in helper; re-asserted in flow | Source checks GREEN | GREEN: `consent_gate: true` |
| Synthetic-identity persistence/recreate survival, no real phone | `--relay --json` consent simulation, offer discarded unlogged; keypair sha/mode container-side; markers; compose down/up; sha equality | Probe-shape checks GREEN | GREEN: sha `dd4580fb…e195` match, mode 0600, owner 99:100, markers persisted, `real_phone_claimed: false` |
| Zero public ports | Compose has no `ports:`; `{{len .HostConfig.PortBindings}}` == 0 before + after recreate | Static GREEN | GREEN: 0 ports in both daemon phases |
| Secret-safe HOME, no raw credentials in Git/evidence | Container-side config scan (no secret env, no secret assignments); keypair metadata-only (sha/mode, never contents); offer never logged; secret-pattern scan of outputs + report | Static + scan GREEN | GREEN: `home_secret_free`, nothing captured/logged; artifact secret-scan clean |
| Revocation/readback fail-closed | `revocation-capability` JSON `supported:false` + `no-individual-device-revocation-cli`; status metadata-only (no keypair read) | Source + CLI JSON GREEN | GREEN: `revocation_supported: false` |
| Inventory desired/observed readback, drift without silent deletion | `derive_inventory` perfect GREEN; pi missing + node mismatch + fingerprinted unexpected extra | GREEN host-side | GREEN: GREEN/RED, 1 reported, 0 deleted |
| Approved-only reconcile + post-action readback | Plan targets exactly `[node, pi]` with `restore_desired_state`; restored WARN (extra still reported); unrestored RED; vanished-extra RED | GREEN host-side | GREEN: actions `[node, pi]`, restored WARN, unrestored RED |
| Quick/full doctor machine-readable GREEN/WARN/RED | `doctor(quick/full)` GREEN on perfect, full RED on drifted; counts + summary; quick defers, full covers 12 | GREEN host-side | GREEN: quick/full GREEN, drifted full RED |
| Lightweight healthcheck | `http_health /api/health :6767` in inventory + M02 smoke; compose inherits parent check; daemon poll + 200 assert before/after recreate | Static GREEN | GREEN: health GREEN before + after recreate |
| Bounded auth-health fingerprints only | Credential injection into version/location/unknown-id leaves only `*_fingerprint` + `sha256:` refusal; secret + `token` absent | GREEN host-side | GREEN: `fingerprints_only`, nothing captured |
| Fail-closed HA/M07-T05 deferral | 14-item deferred list, scope guards, no activation path, no phone/auth claim | GREEN | GREEN: production scope refused in CI |
| Candidate/image identity + no lingering containers | Image label asserts; `docker ps ancestor` asserts | Shape checks GREEN | GREEN: label candidate matches, `1dd9aad5`, no lingering containers, production path absent |
| No full GREEN | `full_green_claimed: false` in readback, flow, failure reports; technical-slice-only outcome | GREEN | GREEN: asserted in CI readback + flow |

## CI GREEN run 36278632419

- Scope/outcome: flow `scope: disposable`, `outcome: relay_doctor_readiness_green`; `production_mutation: false`, `full_green_claimed: false`.
- Image: tag `pi-unraid:paseo-b4e0c1e7c276`, id `sha256:1dd9aad512310849089435fc18a7c0d0d0cb34f83ceee53e58732b03c5e46d7d`, label candidate `sha256:b4e0c1e7...` matching the frozen candidate.
- Flow phases, all `ok`: fixture, image_labels, relay_fail_closed, synthetic_persistence, daemon_health_ports, recreate_survival, secret_safe_home, inventory_drift, reconcile_doctor, auth_fingerprints.
- Relay: default-disabled after configure; non-consenting pair fails closed with `RELAY_DISABLED`; consent gate re-asserted; revocation `supported: false` with `no-individual-device-revocation-cli`.
- Synthetic identity: `--relay` consent simulation inside the disposable fixture only, offer discarded unlogged; keypair sha `dd4580fb59c0842270ef0c4805d3b93ce499b6f21c29f148307bcfd49856e195` identical before/after recreate, mode 0600, owner 99:100; home/projects/worktrees markers persisted; `real_phone_claimed: false`.
- Daemon: `/api/health` GREEN on port 6767 before and after recreate; zero public port bindings in both phases; user 99:100; shm 1073741824 bytes; mounts exactly /home/paseo + /projects + /worktrees; relay still enabled; keypair still 0600.
- Capability: inventory perfect GREEN, drifted RED (pi missing, node version_mismatch, 1 unexpected reported fingerprinted, 0 deleted); reconcile plan targets exactly `[node, pi]` with `restore_desired_state`, `report_only_never_delete`, no desired mutation; restored WARN (approved actions restored, extra still reported), unrestored RED, vanished-extra RED; doctor quick/full GREEN on perfect, full RED on drifted, machine-readable counts + summary.
- Auth fingerprints: credential injection into inventory version/location/unknown-id and reconcile refusal leaves only `*_fingerprint` + `sha256:` markers; secret material and `token` keys absent; nothing captured.
- Seed build/test: cold build 130804 ms / 0 cached, plus 4/4 smokes GREEN (image_provenance incl. Chromium 153.0.8010.12 both legs, paseo_health GREEN, secret_scan GREEN; persistence_ownership M02-T02 GREEN; instruction_plane M02-T03 GREEN; global_capabilities M04-T03 GREEN); production-scope refusal step GREEN with `/mnt/user/appdata/pi-unraid` absent and no seed containers left running.
- Artifact: `paseo-relay-doctor-readiness-evidence` (id 10917926282, 8 files: seed record/metadata/build/test logs, readback, flow + flow-out identical, production refusal); secret-pattern scan of the full artifact clean. The 9 `FAILED|ERROR:` grep hits in the job log are all benign (fail-closed test names, expected negative-path stderr, intentional refusal message); zero Tracebacks, zero suite failures.

## CI-host portability

The workflow reuses the proven M05-T03/M06-T01/M06-T02 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, compose project isolation, root-chown cleanup). The harness is stdlib-only plus repo scripts. No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03.

## Pitfall avoidance (from M06-T02 history)

- Every HOME content read after the 99:100 chown runs container-side as the runtime identity (`docker run --user 99:100` / `docker exec`); the host never stats 0600 container-owned material.
- All container probes are single-line `key=value` machine-readable (`parse_kv_output`); JSON outputs (revocation, labels) are parsed whole, never line-split.
- Docker legs capture full combined output with secret-pattern scanning and bounded 6000-char diagnostics; every flow failure emits a machine-readable report with `phases_completed`.
- One genuine defect found locally and fixed without weakening assertions: the restored reconcile readback keeps the unexpected extra reported, so its correct state is WARN (approved actions restored, extra still observed), not GREEN; the harness, test, and CI assert now pin WARN plus the reason.

## Residual risks

- The M06-T03 automatic acceptance (Relay/persistence/capability/doctor readiness) is proven on the exact SHA above; real phone pairing/transfer, first credential/authenticated proof, and UX judgment are owned by the already-planned HA wave (M07-T02 staged proof, M07-T03 production-confirmation tail), and wishlist activation by conditional post-deploy M07-T05.
- Review requirement `required` per Card; independent implementation review still due after the semantic result is frozen. Exit claimed is one M06 technical slice GREEN with M06-T04 and HA outstanding only: no full M06 milestone, production, phone, authenticated, UX-judgment, or wishlist-activation claim.
- Project Workflow Main owns the single semantic result/review binding; this file is the worker evidence contribution, not the semantic result.
