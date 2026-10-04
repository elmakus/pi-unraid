# M07-T05 — Validator implementation contribution report (synthetic/local only)

Date: 2026-10-04
Owner: implementation worker (source/tests/docs only; no result classification,
no independent verdict, no Board/manifest finalization).
Card: `M07-T05` (`in_progress`, Board revision 119).
Legal worktree: `/home/paseo/projects/pi-unraid-paseo-update-distribution`,
branch `feat/paseo-update-distribution`.
Launch checkpoint: `8a0553079abac233b4ddc88ef4ce666cfbf3a661`.
Target observation: `main@e9476b4987290767a195a9de2ecd655de5f09605`.
Workflow: `elmakus/project_workflow_v2@d3ab917f02e4de91b7dbb17915c2287c2387333e`
(router → Execution; EXECUTION.md single-Card execution, Main-only
reconciliation).

This report is a secret-safe contribution record for Main reconciliation
and later fresh independent review. It claims no semantic result, no GREEN,
no candidate eligibility, and no production authorization. All execution
below is synthetic/local with fake-only executables and disposable roots;
no real inference, credential admission, or live Docker/Tower/host action
occurred.

## Authority and dependency bindings (reread before mutation)

- Stable Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M07-T05.md`
  (replace direct Codex-LB inference; bounded Muse adapter via canonical
  guard; typed fixture-vs-real outcome; dedicated plumbing; owned cleanup).
- Selective technical contract:
  `contracts/PASEO_R2_CANDIDATE_VALIDATION.md` (producer/consumer trust,
  bound subject, outcome interface, candidate-local adapter, non-inference
  Codex, dedicated secrets, disposable cleanup, required evidence).
- Prep reconciliation:
  `implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-prep-reconciliation-2026-10-04.md`.
- Exact DONE dependency:
  `implementation/workstreams/feature-paseo-update-distribution/results/M07-T04.md`
  `@6329cf488cebaf955a49cbace71d87613381dc11:c45b3f707b1246e195c9138d027cbb1b05b9b112`
  (implementation `bbe3e254e1961b14b0a6c64ff302caf4c1cb7515`; independent
  R01 GREEN
  `evidence/M07-T04-R01-independent-review-2026-10-04.md`
  `@6c7f952b42ae6365295af6c7f0f05fb3aa2f3188:dffad8bf2a2e872375c11fbccc74ce53362e6a0d`).
  Baseline companion `sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`
  treated as historical input; recomputed below, not reused blindly.
- P4 approval/A/B/C: `PLANNING.toml` (cycle 4, revision P4, `approved`,
  `premium_a/b/c satisfied`) plus exact GREEN
  `PLAN_REVIEW.toml` (`P4/R01 green`), not frozen-plan prose.
- Named authority reread: `requirements/PASEO_UPDATE_DISTRIBUTION.md` (R2),
  `requirements/PASEO_GUI_RUNTIME.md`, `decisions/ADR_PUD_001/002/004`,
  `planning/PASEO_UPDATE_DISTRIBUTION_P4.md` (M07-T05 section).
- Exclusions honored: no Card/contract/plan/requirement/decision/result/
  Board/manifest/Research/review-history modification; no M07-T06
  promotion/final-gate/guard/ledger/legacy/action, M07-T07/M08/M09, image
  build/publication, CI trigger, PR/Issue, push, delegation, installed
  HOME/runtime/harness mutation, or live Docker/Tower/host/production action.

## Implementation subject and reachable paths

Implementation commit (source/tests/docs):
`9abd0fcbb3e1ba4a7f3cf50d3b76d734d4aa19cc`
(branch `feat/paseo-update-distribution`; unpushed).

Files (all inside validator/guard/delivery/binding + tests/docs):

- `scripts/paseo_tower_validator.py` (reworked, `SCHEMA_VERSION 2`):
  registry digest readback, `RepoDigests` OCI→local mapping check
  (`SKIP` when unverified, never silent PASS), companion/policy/launcher
  recompute-and-compare when `source_root` is supplied, disposable
  `UID:GID`/mount/network/secret isolation, authenticated GET
  catalog/health structural checks only (no `/responses`), Muse
  effective-profile gate recording, typed
  `execution_class/terminal_class/real_validation_satisfied` outcome,
  secret-safe bounded reasons, ownership-verified cleanup (container only
  if created by this attempt and still owned; work only if
  `candidate-*` under `state_root`; network only if created here;
  preexisting same-name foreign objects never removed).
- `scripts/paseo_codex_noninference.py` (new): `validate_base_url`
  (`/v1` suffix, no inference substring), `validate_model_id`,
  `read_dedicated_secret` (regular file, no symlink, `0600`/`0400`,
  single entry, `CODEX_LB_API_KEY=` or bare), `parse_catalog_body`
  (OpenAI-compatible list, non-empty valid ids), `parse_health_body`,
  `check_catalog` (`GET {base}/models` + Bearer, `401/403`→auth-denied
  FAIL, unreachable→BLOCKED, malformed→FAIL), `check_health`
  (`GET {root}/health`, structural `ok|healthy|ready|up`), `run_all`
  (health without credential; catalog `SKIP` when missing; never calls
  inference; secret-safe `sanitize_message`), `INFERENCE_SUBSTRINGS`
  guard (`/responses`, `/chat/completions`, `/completions`, `/embeddings`).
- `scripts/paseo_candidate_muse_adapter.py` (new): fixed
  `meta/muse-spark-1.3-contributor/max` no-fallback profile,
  `guard_identity`/`policy_identity` readback of the exact delivered bytes,
  `validate_candidate_home` (absolute, under disposable root, never
  production `~/.paseo`/`/home/paseo/.paseo`/appdata home),
  `validate_daemon_binding` (home/endpoint/pid/version, candidate-local,
  pinned `0.9.2`), `validate_pi_binding` (bindir-resolved, pinned `0.87.1`),
  `classify_effective_profile` (exact `max`→profile-gate `PASS`;
  `xhigh`/downgraded→`FAIL` with M08-T01 boundary; unknown→`UNKNOWN`;
  never replays), `run_guard_dispatch` (real guard bytes via disposable
  agent root, fake-only `PATH`, snapshot before cleanup),
  `outcome_for_fixture` (always `real_validation_satisfied: false`;
  timeout→`UNKNOWN` without replay).
- `tests/test_paseo_tower_validator.py` (reworked, 10 tests): stateful
  docker fake (preexisting `inspect` is not-found until `run`; `RepoDigests`
  JSON; catalog+health exec), disposable/secret-free PASS, column-spacing
  digest, runtime healthy/unhealthy, non-inference mount/classification
  (`catalog_rc 0/20/21/23` → `PASS/BLOCKED/FAIL/FAIL`, two execs on PASS,
  no `/responses`), missing credential BLOCKED, structured BLOCKED,
  preexisting foreign container never removed, private-mode required.
- `tests/test_m07_t05_validator_adapter.py` (new, 31 tests): `CodexNonInference`
  (8), `MuseAdapter` (9: fixed-profile rejection, pinned readback,
  home/production, daemon binding, clamp/unknown, positive dispatch
  observed, negative absent, native fixed shape, fixture never real),
  `ValidatorMatrix` (9: wrong OCI fails before `run`/`exec`, wrong bundle,
  fixture PASS not real, no inference, timeout UNKNOWN, leaked-token absent,
  collision preserves foreign, malformed base, redaction), `ExtendedMatrix`
  (5: fallback/bypass, daemon/endpoint/Pi, wrong source policy with
  fallback, negative/uncertain, mount/env procedure shape).
- `docs/PASEO_CANDIDATE_VALIDATION_M07_T05.md` (new): supported
  interfaces, provenance, secret plumbing procedure, cleanup, outcome
  interface, and remaining real-gate limitations (no eligibility claim).

No guard modification was adopted; the canonical
`config/pi-agent/bin/run-llm-test.sh` bytes are used verbatim, so the
companion identity is unchanged (see provenance).

## Synthetic/local evidence (worker-observed, not an independent verdict)

All counts below were obtained by the implementation worker via
`python3 -m unittest` with fake-only `PATH`/mocked Docker/no provider,
plus one node core check. Ordinary worker activity is not smoke evidence.
Exit statuses preserved; no skips taken.

- Targeted (new/changed validator + adapter):
  `python3 -m unittest tests.test_paseo_tower_validator tests.test_m07_t05_validator_adapter`
  → `Ran 41 tests … OK` (exit 0). Breakdown: tower 10, adapter/matrix 31.
  Positive synthetic dispatch observed (`meta/muse-spark-1.3-contributor`
  + `max` in fake `paseo` marker); negatives assert absence before temp
  cleanup; malformed catalog parser executed via `node -e` and fails closed.
- Affected sample (guarded-policy/instruction-plane/companion/build/runtime):
  `test_llm_test_policy_contract + test_m07_t04_policy_delivery +
  test_paseo_companion_bundle + test_paseo_candidate_build_pipeline +
  test_paseo_transaction_guard + test_pi_instruction_plane_contract +
  test_paseo_runtime_contract + test_paseo_child_image_contract`
  → `Ran 72 tests … OK` (exit 0).
- Full classified Python suite:
  `python3 -m unittest discover -s tests -p "test_*.py"`
  → `Ran 594 tests … OK` (exit 0), zero skips.
- Node: `node tests/codex_lb_dynamic_model_catalog_core_test.mjs`
  → `codex-lb dynamic catalog core tests: GREEN` (exit 0).
- Secret-safe scans: result/call blobs scanned for fixture tokens in-test
  (`test_leaked_token_never_in_output_or_calls`); exception tails redacted
  (`_sanitize`/`sanitize_message`); `grep` for high-confidence patterns
  over changed files shows only the `CODEX_LB_API_KEY=` *name* and
  synthetic `fixture-*` values in disposable temp fixtures, no real secret.
- Diff check: `git diff --name-only` shows only the six allowed paths
  above; no Card/contract/plan/requirement/decision/result/Board/manifest/
  Research/review file modified.

## Entry-point classification (every touched entrypoint)

- NOT executed: `run-llm-test.sh PROMPT` with a real prompt (would infer);
  `paseo run/status/daemon`, `pi --model/--list-models` as real binaries;
  `paseo_tower_validator` Codex `/responses` smoke (removed, never run);
  `scripts/verify-codex-lb-integration.sh` and live RPC/activation harnesses;
  docker image builds, Tower live state, production guard/channel/cutover.
- Executed synthetically: real `run-llm-test.sh` bytes via disposable agent
  root + test-owned bindir (`dirname`/`jq`/`bash` symlinks + fake `paseo`);
  `--native-create-agent-args` without inference; real
  `paseo_tower_validator.validate` via stateful mocked `docker`;
  real `paseo_codex_noninference` via injected `http_get` fixtures and temp
  `0600` secret files; real `pi-ai dist/models.js` clamp readback remains
  covered by the preserved M07-T04 suite (not rerun as real inference);
  `node -e` structural parsers against malformed fixtures (fail closed).
- Approved non-inference readback: `paseo --help`, `paseo run --help`,
  `paseo --version` (`0.9.2`), `pi --version` (`0.87.1`), pinned
  `meta.json` Contributor `max:null`, `Dockerfile`/`compose.yaml`/
  `paseo-candidate.json` provenance, guard/policy file bytes. No prompt,
  inference, or auth-value read.

## Source/provenance (recomputed)

- Pinned: Paseo `0.9.2`
  (`ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`),
  Pi `0.87.1` (`sha512-m8ArJUtVcQMSe1lLE/Ei7vX/JV7O39sWmWBsXV2NOU70F0qCp8GubA24pT3LnwTmM6LL2xV80/h6sQg85n69ew==`),
  candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`.
- Guard `sha256:7fd922da42fcebfb6ed9e83f1f3471ed5365ea7961bec2ca25cdc9fd62827e33`
  (`0755`); policy `sha256:943ba67c3b23ca3d40f745ed4c4f653964898a460b94ec83c3cc7aebeec01d40`.
- Companion `config/pi-agent` (10 files, `bin/*→0755` else `0644`),
  `source_digest sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`
  (recomputed via installer; matches historical baseline because the guard
  was not modified; any future guard change must propagate through
  prepare/build/package, never attach to the old digest).
- Negative facts preserved: Contributor `thinkingLevelMap.max=null`,
  unmodified `max→xhigh` clamp. No override, workflow return, or launcher
  arguments presented as effective-`max` proof.

## Preserved subjects and boundaries

- All 22 DONE result/review subjects and unaffected target
  repairs/recovery packages preserved (no `results/*`, `reviews/*`,
  `TASK_BOARD.toml`, `WORKSTREAM.toml`, `PLANNING.toml`,
  `PLAN_REVIEW.toml`, requirements/decisions/plans modified; `git diff`
  confirms).
- Real exit statuses preserved; honest executed/skipped accounting
  (41/72/594 executed, 0 skipped in full run, 1/1 node).
- No real credential, inference, candidate eligibility, or production
  authorization claimed; supported gaps return the owning boundary.

## Remaining real-gate limitations (for Main/reviewer, not waived)

- Effective `max` on the direct-Meta path remains unobservable with the
  pinned bundle; fixtures always leave `real_validation_satisfied: false`.
  Real guarded inference with observed exact effective profile,
  candidate/daemon/Pi/policy binding, and successful required
  non-inference checks belongs to M08-T01 after autonomous
  machinery/rehearsal and dedicated credential admission. No fallback,
  downgraded level, unofficial provider, or direct provider bypass is
  adopted; unsupported realization fails closed to Research/Planning.
- Real candidate-local daemon bring-up, real `pi --version`/provider path
  inside the candidate image, and real Codex-LB `GET /v1/models` +
  `GET /health` against operator endpoints remain to be exercised with
  dedicated credentials in the disposable boundary.
- A changed candidate/companion requires a new immutable build identity
  and exact affected-gate evidence (M07-T07); the old digest gains no
  eligibility here. M07-T06 final-gate/ledger/legacy work is excluded.

## Return

- Implementation commit:
  `9abd0fcbb3e1ba4a7f3cf50d3b76d734d4aa19cc`
  (six paths above; unpushed).
- This report path:
  `implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-validator-implementation-2026-10-04.md`
  (report commit/blob to be filled by the committing step; secret-safe).
- Reachable behavior: `scripts/paseo_tower_validator.validate`
  (fixture `PASS` with `real_validation_satisfied: false`,
  `codex_no_inference: PASS`, no `/responses`);
  `scripts/paseo_codex_noninference.run_all` (catalog/health `PASS`/`FAIL`/
  `BLOCKED`/`SKIP` without inference);
  `scripts/paseo_candidate_muse_adapter.run_guard_dispatch` (fake-only
  positive dispatch observed, negatives absent) and
  `classify_effective_profile`/`outcome_for_fixture` (clamp/unknown fail
  closed without replay).
- Completion is a return to Main for classification/reconciliation and
  later fresh independent review; not a workflow stop, result, or verdict.

---

## Correction (2026-10-04) — bounded repair for Main return-validation A-E

This section is appended by the fresh implementation/repair context. Old bytes
above remain in Git history (implementation `9abd0fc`, report `5942df3`). This
is a correction contribution, not a new task/contract, result, or verdict. Board
remains 119, M07-T05 `in_progress`, no result/Review attempt. No push.

### Legal scope and recovery

- Legal worktree: `/home/paseo/projects/pi-unraid-paseo-update-distribution`,
  branch `feat/paseo-update-distribution`. Default `main` worktree untouched
  (read-only/outside write scope).
- Launch checkpoint: `6b4bef92e48ddd4d52b062634fa8790e840292ba` (unpushed).
  Independent recovery: `project-recovery` SKILL + bootstrap, `PROJECT.md`,
  default-branch `elmakus/project_workflow_v2@d3ab917f02e4de91b7dbb17915c2287c2387333e`
  (`ROUTER.md` → `EXECUTION.md` common Execution), workstream root
  `implementation/workstreams/feature-paseo-update-distribution`
  (`WORKSTREAM.toml`, `TASK_BOARD.toml` rev 119, `cards/M07-T05.md`, exact DONE
  `results/M07-T04.md@6329cf488cebaf955a49cbace71d87613381dc11:c45b3f707b1246e195c9138d027cbb1b05b9b112`,
  `contracts/PASEO_R2_CANDIDATE_VALIDATION.md`,
  `evidence/M07-T05-prep-reconciliation-2026-10-04.md`, and most importantly
  Main's `evidence/M07-T05-return-validation-2026-10-04.md` at `6b4bef9`).
- P4 approval/A/B/C in `PLANNING.toml` + GREEN `PLAN_REVIEW.toml`, not frozen-plan
  prose. All 22 DONE preserved; stable Card/technical contract unchanged.
- Unaccepted contribution source `9abd0fcbb3e1ba4a7f3cf50d3b76d734d4aa19cc`;
  report `5942df3ec5ac73817f94a000ab86affc83fffbf6:12e7f82056d236d043aa7ba834e5393037c6c28c`
  (reported 594 tests are not acceptance; Main reran 41 OK + 7 probes).

### Exact source and provenance (recomputed)

- Corrected implementation commit: `d937e8f7ade60ee284f29d7dee42259318ce9755`
  (six paths: `scripts/paseo_tower_validator.py`,
  `scripts/paseo_codex_noninference.py`,
  `scripts/paseo_candidate_muse_adapter.py`,
  `tests/test_paseo_tower_validator.py`,
  `tests/test_m07_t05_validator_adapter.py`,
  `docs/PASEO_CANDIDATE_VALIDATION_M07_T05.md`; unpushed).
- Pinned: Paseo `0.9.2`
  (`ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`),
  Pi `0.87.1` (`sha512-m8ArJUtVcQMSe1lLE/Ei7vX/JV7O39sWmWBsXV2NOU70F0qCp8GubA24pT3LnwTmM6LL2xV80/h6sQg85n69ew==`),
  candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`.
- Guard `sha256:7fd922da42fcebfb6ed9e83f1f3471ed5365ea7961bec2ca25cdc9fd62827e33`
  (`0755`); policy `sha256:943ba67c3b23ca3d40f745ed4c4f653964898a460b94ec83c3cc7aebeec01d40`
  (verbatim, no modification).
- Companion `config/pi-agent` recomputed
  `source_digest sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`
  (unchanged; any future guard change must propagate via prepare/build/package).
- Negative facts preserved: Contributor `thinkingLevelMap.max=null`
  (pinned `meta.json`), unmodified `max→xhigh` clamp (`pi-ai/dist/models.js`);
  `before_provider_request`/`after_provider_response` are extension events
  requiring explicit handlers (`dist/core/sdk.js`, `extensions/types.d.ts`,
  `onPayload`/`onResponse` in compat chunks) — source lead only, not proof.
  Witness extension records only nonsecret `provider/model/thinking/status/count`.

### Reachable behavior (genuine entrypoints, fake-only boundaries)

- `scripts/paseo_tower_validator.validate` (integrated product path):
  fixture `PASS` with `real_validation_satisfied:false`,
  `codex_no_inference:PASS`, no `/responses`; real mode missing → `BLOCKED/FAIL`;
  foreign daemon/Pi → `FAIL`; wrong running `Image` → `FAIL`; absent
  `RepoDigests` → `FAIL`; foreign secret-only → preserved (`0 run/rm`);
  opaque echoes redacted; `UNKNOWN` preserves `owned_reference` + container.
- `scripts/paseo_codex_noninference.run_all`/`check_catalog`/`check_health`/
  `parse_*`/`assert_safe_redirect`/`sanitize_message`: `PASS`/`FAIL`/`BLOCKED`/
  `SKIP` without inference; redirects validated (no inference traversal, no
  cross-host auth forward); bodies bounded in-memory, never persisted.
- `scripts/paseo_candidate_muse_adapter.run_guard_dispatch` (real guard bytes
  via disposable agent root + fake-only `PATH`): positive dispatch observed
  (`meta/muse-spark-1.3-contributor` + `max` marker); missing policy →
  `AdapterBlocked` (no fabrication); `classify_effective_profile`/`outcome_for_fixture`
  clamp/unknown fail closed without replay; `read_dedicated_muse_secret` +
  `write_effective_witness_extension`/`parse_effective_witness_file` provide
  dedicated Muse plumbing + secret-free witness.
- CLI now exposes `--candidate-file`/`--muse-secret`/`--companion-bundle`/
  `--daemon-info`/`--pi-info` for typed frozen inputs (expected versions from
  candidate, not host pins).

### Counts and exits (worker-observed, honest, preserved)

- Targeted: `tests.test_paseo_tower_validator` + `tests.test_m07_t05_validator_adapter`
  (incl. new `MainSevenProbesTests` 10 tests) → `Ran 51 tests … OK`, exit 0, 0 skips.
- Affected (guarded-policy/instruction-plane/companion/build/runtime, 8 modules):
  `Ran 72 tests … OK`, exit 0.
- Full classified Python: `discover -s tests` → `Ran 604 tests … OK`, exit 0, 0 skips.
- Node: `codex_lb_dynamic_model_catalog_core_test.mjs` → GREEN, exit 0.
- Diff: only the six allowed source/test/doc paths; no Card/contract/plan/
  requirement/decision/result/Board/manifest/Research/review writes.
- Secret-safe scans: changed files contain only `CODEX_LB_API_KEY=` name +
  synthetic `fixture-*` in disposable temp fixtures; opaque tokens redacted;
  no raw headers/body/prompt/token output.
- Entry-point classification: every touched inference-capable entrypoint
  (`run-llm-test.sh PROMPT`, `--native-create-agent-args`, `paseo run/status`,
  `pi --model`, validator Codex `/responses` (removed), live harnesses, docker
  builds, Tower live) — NOT executed as real; executed synthetically only via
  fake bindirs/mocked Docker/injected HTTP/disposable roots + approved
  non-inference readback (`paseo --help/version`, `pi --version`, pinned
  `meta.json`, guard/policy bytes). `PATH` isolated so actual test inference
  cannot occur. No test agent created; no real provider inference.

### Preservation and remaining real-gate limitations

- Preserved all 22 DONE result/review subjects, stable Card/technical contract,
  P4/R2/authority, unrelated target repairs/recovery packages. No
  M07-T06/M07-T07/M08/M09 implementation; no state/result/Review writes.
- Fixture/rehearsal never satisfies the real gate by construction.
  Unsupported/unobservable effective `max` fails closed to M08-T01/
  Research-Planning (precise facts above), not bypass/manufactured witness/
  M08 coding. Real guarded inference, dedicated credential admission,
  candidate-local daemon bring-up, exact wire/inference proof, and real
  Codex-LB reads against operator endpoints remain M08-T01 after autonomous
  machinery/rehearsal. Changed candidate/companion needs new immutable identity
  (M07-T07). No eligibility/production authorization claimed.

### Return

- Implementation SHA: `d937e8f7ade60ee284f29d7dee42259318ce9755` (unpushed).
- This report path:
  `implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-validator-implementation-2026-10-04.md`
  (correction commit/blob to be filled by the committing step; secret-safe).
- Completion returns to Main for classification/reconciliation; not a workflow
  stop, result, or verdict. Later independent reviewer must be another
  non-producing context.
