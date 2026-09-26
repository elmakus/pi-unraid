# M06-T03 Relay/persistence/capability/doctor readiness evidence (worker contribution)

- Card: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T03.md`, Board rev 105 `in_progress`.
- Implementation subject: uncommitted worktree at base `elmakus/pi-unraid@cc108c782583bb187e32f388f69b84ba9a03e25b` on `origin/feat/paseo-gui-runtime`. Exact implementation SHA and CI run are TBD: Main owns commit/push, which triggers the exact-SHA workflow below. No semantic result/review frozen; card not DONE.
- Exact-SHA CI: PENDING Main commit/push. Workflow `.github/workflows/paseo-relay-doctor-readiness.yml` (job `relay-doctor-readiness-disposable-evidence`) will prove the live disposable flow plus the full 378-test suite on that SHA. Live Docker execution is CI-only; this workstation has no Docker.
- Frozen candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69` (Paseo 0.9.2, Pi 0.87.1, base `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`). Candidate/build inputs unchanged.
- Exact predecessor bindings revalidated locally via `git rev-parse`/`git cat-file` and pinned in CI: M06-T02 `13a49bd8`, M06-T01 `e01bd1dd`, M02-T02 `7b8574df`, M02-T01 `e5075d47`, M04-T01 `5173447e`, M04-T02 `c6adc851` (all match Card bindings; all DONE with terminal GREEN reviews).
- Contract suite: 18 suites / 378 tests GREEN locally (17 pre-existing suites 336 tests plus `test_paseo_relay_doctor_readiness_contract.py` 42 tests). CI reruns the same 18 suites on the exact SHA.
- Static readback (local): verdict `technical_green_ha_outstanding`, zero violations, `full_green_claimed: false`, 14 HA/M07-T05 deferrals.
- Disposable Docker flow: implemented with 10 asserted phases (details below); live GREEN pending CI run on Main's commit SHA. Host-side inventory/reconcile/doctor/fingerprint phases already execute GREEN locally (no Docker needed).
- No production alias/HOME mutation, no legacy Pi change, no Tower mutation, no reboot/engine restart, no real phone, no credentials/OAuth/2FA, no authenticated gh/GraphQL, no UX judgment attempted; no wishlist activation path exists in the harness.

## Changed files

- `scripts/paseo_relay_doctor_readiness.py` (new): `readback` static verifier (candidate, Relay policy, zero-port/secret-safe shape, inventory authority, reconcile/doctor semantics, lightweight healthcheck, bounded fingerprints, no-activation policy); `flow --scope disposable` end-to-end (fixture, image labels, Relay fail-closed incl. consent gate + revocation unsupported, synthetic-identity consent simulation + keypair sha/mode container-side, compose daemon health/ports, recreate survival with sha equality, container-side secret-safe HOME scan, inventory drift without deletion, approved-only reconcile with readback, quick/full doctor GREEN/WARN/RED, credential-injection fingerprint proof, lingering-container asserts, failure-report emission). Refuses non-disposable scope and fixture roots outside system temp.
- `tests/test_paseo_relay_doctor_readiness_contract.py` (new): 42 hermetic contract tests (no Docker, no network).
- `.github/workflows/paseo-relay-doctor-readiness.yml` (new): 6 predecessor binding checks, complete 18-suite run, static readback assert, frozen-candidate build/test, disposable 10-phase flow with detail asserts, production-scope refusal proof, untouched proof, evidence artifact upload; piped steps use `set -o pipefail`.
- `implementation/workstreams/feature-paseo-gui-runtime/TASK_BOARD.toml`: rev 105, M06-T03 `in_progress` (transition only; Main owns result/review binding).
- This evidence file.

## Acceptance matrix

| Card item | Mechanism | Local | Live (CI pending) |
| --- | --- | --- | --- |
| Relay default-disabled + every enablement path fail-closed | Configure persists `relay=false`; non-consenting `pair --json` asserts `RELAY_DISABLED` | Policy + probe-shape checks GREEN | Flow phase `relay_fail_closed` asserts live code + exit |
| Pairing-helper consent gate | `require_tty` + `[y/N]` + cancel message in helper; re-asserted in flow | Source checks GREEN | Flow re-asserts markers |
| Synthetic-identity persistence/recreate survival, no real phone | `--relay --json` consent simulation, offer discarded unlogged; keypair sha/mode container-side; markers; compose down/up; sha equality | Probe-shape checks GREEN | Phases `synthetic_persistence` + `recreate_survival` |
| Zero public ports | Compose has no `ports:`; `{{len .HostConfig.PortBindings}}` == 0 before + after recreate | Static GREEN | Daemon inspect asserts in both phases |
| Secret-safe HOME, no raw credentials in Git/evidence | Container-side config scan (no secret env, no secret assignments); keypair metadata-only (sha/mode, never contents); offer never logged; secret-pattern scan of outputs + report | Static + scan GREEN | Flow phase `secret_safe_home` + report scan |
| Revocation/readback fail-closed | `revocation-capability` JSON `supported:false` + `no-individual-device-revocation-cli`; status metadata-only (no keypair read) | Source + CLI JSON GREEN | Flow asserts revocation JSON |
| Inventory desired/observed readback, drift without silent deletion | `derive_inventory` perfect GREEN; pi missing + node mismatch + fingerprinted unexpected extra | GREEN locally (host-side phase) | Same phase reruns in CI |
| Approved-only reconcile + post-action readback | Plan targets exactly `[node, pi]` with `restore_desired_state`; restored WARN (extra still reported); unrestored RED; vanished-extra RED | GREEN locally (host-side phase) | Same phase reruns in CI |
| Quick/full doctor machine-readable GREEN/WARN/RED | `doctor(quick/full)` GREEN on perfect, full RED on drifted; counts + summary; quick defers, full covers 12 | GREEN locally (host-side phase) | Same phase reruns in CI |
| Lightweight healthcheck | `http_health /api/health :6767` in inventory + M02 smoke; compose inherits parent check; daemon poll + 200 assert before/after recreate | Static GREEN | Daemon health asserts in flow |
| Bounded auth-health fingerprints only | Credential injection into version/location/unknown-id leaves only `*_fingerprint` + `sha256:` refusal; secret + `token` absent | GREEN locally (host-side phase) | Same phase reruns in CI |
| Fail-closed HA/M07-T05 deferral | 14-item deferred list, scope guards, no activation path, no phone/auth claim | GREEN | Production scope refused in CI |
| Candidate/image identity + no lingering containers | Image label asserts; `docker ps ancestor` asserts | Shape checks GREEN | Flow phases + untouched proof |
| No full GREEN | `full_green_claimed: false` in readback, flow, failure reports; technical-slice-only outcome | GREEN | Asserted in CI readback + flow |

## CI-host portability

The workflow reuses the proven M05-T03/M06-T01/M06-T02 runner shape (`ubuntu-latest`, setup-python 3.13, `paseo_buildx.py build/test`, `docker run --rm` disposable fixtures, compose project isolation, root-chown cleanup). The harness is stdlib-only plus repo scripts. No Tower, registry, or runner prerequisites beyond the base image pull already required by M05-T03.

## Pitfall avoidance (from M06-T02 history)

- Every HOME content read after the 99:100 chown runs container-side as the runtime identity (`docker run --user 99:100` / `docker exec`); the host never stats 0600 container-owned material.
- All container probes are single-line `key=value` machine-readable (`parse_kv_output`); JSON outputs (revocation, labels) are parsed whole, never line-split.
- Docker legs capture full combined output with secret-pattern scanning and bounded 6000-char diagnostics; every flow failure emits a machine-readable report with `phases_completed`.
- One genuine defect found locally and fixed without weakening assertions: the restored reconcile readback keeps the unexpected extra reported, so its correct state is WARN (approved actions restored, extra still observed), not GREEN; the harness, test, and CI assert now pin WARN plus the reason.

## Next step for Main

Commit and push this work (board rev 105 + harness + tests + workflow + this evidence) to `origin/feat/paseo-gui-runtime`, then record the exact implementation SHA and the `relay-doctor-readiness-disposable-evidence` CI run number/result. On CI SUCCESS, the live 10-phase flow plus 378-test suite constitute M06-T03 automatic technical-slice GREEN (M06-T04 and HA still outstanding); this evidence file should then be updated with the run link, image id, and phase detail.

## Residual risks

- Live Docker phases (Relay fail-closed, synthetic persistence, daemon health/ports, recreate survival, secret-safe HOME) are proven only in CI; local proof covers contract tests, static readback, and the host-side inventory/reconcile/doctor/fingerprint phases.
- Review requirement `required` per Card; independent implementation review still due after the semantic result is frozen. Exit claimed is one M06 technical slice GREEN with M06-T04 and HA outstanding only: no full M06 milestone, production, phone, authenticated, UX-judgment, or wishlist-activation claim.
- Project Workflow Main owns the single semantic result/review binding; this file is the worker evidence contribution, not the semantic result.
