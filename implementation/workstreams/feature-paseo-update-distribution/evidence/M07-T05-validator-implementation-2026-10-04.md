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

---

## Correction 2 (2026-10-04) — coherent rewrite for executable-path findings

Old bytes above stay in Git history (`9abd0fc`, `5942df3`, `d937e8f`,
`81dd999`). This corrects Main's second validation
(`evidence/M07-T05-return-validation-2026-10-04.md` §“Second contribution”,
checkpoint `734a6dd`) inside the SAME valid Card/contract. Board 119,
M07-T05 `in_progress`, no result/attempt. No push. All 22 DONE preserved.

### Recovery and scope

- Legal worktree `/home/paseo/projects/pi-unraid-paseo-update-distribution`,
  `feat/paseo-update-distribution` (main worktree read-only). Current Main
  checkpoint `734a6dd93e9515292f8c9add6d880b897fc358e7` (unpushed).
- Recovered: `project-recovery` + bootstrap, `PROJECT.md`, default
  `elmakus/project_workflow_v2@d3ab917` ROUTER + EXECUTION, WORKSTREAM,
  unchanged `cards/M07-T05.md`, every named authority, exact DONE
  `results/M07-T04.md@6329cf488cebaf955a49cbace71d87613381dc11:c45b3f707b1246e195c9138d027cbb1b05b9b112`,
  `contracts/PASEO_R2_CANDIDATE_VALIDATION.md`. No Card/contract/authority/
  state/history/Main-validation writes. Profile `pi/meta/muse-spark-1.3-contributor/max` kept.

### Exact source/provenance

- Implementation commit: `f5a23466767ad4e4828493077858a9fd8356ee8c` (unpushed):
  `scripts/paseo_tower_validator.py` (rewrite),
  `scripts/paseo_candidate_muse_adapter.py` (rewrite),
  `scripts/paseo_codex_candidate_check.py` (new, ONE shared program),
  `tests/test_paseo_tower_validator.py` (genuine harness),
  `tests/test_m07_t05_validator_adapter.py` (rewrite),
  `docs/PASEO_CANDIDATE_VALIDATION_M07_T05.md` (Correction 2).
  `paseo_codex_noninference.py` unchanged (shared transport already sound).
- Provenance recomputed: guard
  `sha256:7fd922da42fcebfb6ed9e83f1f3471ed5365ea7961bec2ca25cdc9fd62827e33`,
  policy `sha256:943ba67c3b23ca3d40f745ed4c4f653964898a460b94ec83c3cc7aebeec01d40`,
  companion `sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`,
  candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
  (Paseo 0.9.2 / Pi 0.87.1 from frozen components).
- Meta auth source: `pi-ai` `providers/meta.ts` (`META_API_KEY` + native
  OAuth) and `env-api-keys.ts` (`meta: "META_API_KEY"`); payload semantics
  from `sdk.js`/`extensions/types.d.ts`/`openai-responses` (`payload.model`,
  `payload.reasoning.effort`, response `status`) and `models.js` clamp.

### Reachable behavior (executing fakes, isolated so real inference never occurs)

- `paseo_codex_candidate_check.py --mode catalog|health` compiles
  (`py_compile`) and runs against a local 127.0.0.1 fixture (counts/health,
  auth-denied/malformed/redirect-inference classified 0/20/21/22/23).
- Genuine validator API AND CLI through staged guard/check/witness + fake
  Paseo/Pi lifecycle to completed shared-subject mechanical PASS (fixture
  real false; real-mode structural `real_validation_satisfied: true`
  proven under fakes). Execs run actual staged bytes (guard `bash`,
  `sha256sum`/`cat` compared, check program via subprocess, fake `paseo`
  writing request/response/terminal witness).
- Negatives (all fail required gates + assert no disallowed calls before
  cleanup): syntax failure, false guard hash, malformed/missing chain
  (incl. `build_record` used), native-export-without-dispatch, false/caller
  witness, aggregation (response-only UNKNOWN, clamp FAIL, missing terminal
  UNKNOWN), empty META value, wrong/missing IDs/nonce/source→dest/modes/
  network, label-less network, readback failure, timeout/UNKNOWN with exact
  owned refs + no resend. Seven old probes stay closed.

### Counts/exits (honest, preserved)

- Targeted: 28 tests OK, exit 0 (validator 6 + adapter/matrix/probe 22).
- Affected (8 modules): 72 OK, exit 0. Full: 581 OK, exit 0, 0 skips.
- Node catalog core: GREEN, exit 0. Diff: only the six permitted paths;
  no Card/contract/authority/state/history writes. Secret scans: only
  `*_API_KEY=` names + synthetic `fixture-*` in disposable temps; no raw
  secrets/bodies/prompts/tokens.

### Limits (not waived)

- Fixture/rehearsal never satisfies the real gate. Real guarded inference,
  dedicated credential admission, live daemon bring-up, and on-wire max
  proof remain M08-T01. Unsupported/unknown fails closed without fallback
  or provider bypass; missing supported interfaces would return facts for
  Research/Planning (none needed — all six findings implemented with
  quoted sources above). No eligibility/production authorization claimed.

### Return

- Implementation SHA: `f5a23466767ad4e4828493077858a9fd8356ee8c` (unpushed).
- This report path:
  `implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-validator-implementation-2026-10-04.md`
  (correction commit/blob below; secret-safe).
- Returns to Main for classification; not a stop/result/verdict. This
  context cannot later review its own subject.

---

## Correction 3 (2026-10-04) — third-return provenance/lifecycle/completion repair

Old bytes above stay in Git history (`9abd0fc`, `5942df3`, `d937e8f`,
`81dd999`, `f5a2346`, `7eba384`). This corrects Main's third validation
(`implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-return-validation-2026-10-04.md`
§"Third contribution", checkpoint `9d4cdecce3cfe4a492b0fb6310ebafdd4ec0296e`)
inside the SAME unchanged Card/technical contract. Board 119, M07-T05
`in_progress`, no result/attempt. No push. All 22 DONE preserved. This
context implemented/repaired the subject and cannot later review it.

### Recovery and scope

- Legal worktree `/home/paseo/projects/pi-unraid-paseo-update-distribution`,
  `feat/paseo-update-distribution` (separate main worktree read-only, outside
  write scope). Launch checkpoint `9d4cdecce3cfe4a492b0fb6310ebafdd4ec0296e`
  (clean, unpushed); earlier producer quiescent.
- Recovered independently: `project-recovery` SKILL + bootstrap, `PROJECT.md`,
  default `elmakus/project_workflow_v2@d3ab917f02e4de91b7dbb17915c2287c2387333e`
  ROUTER + EXECUTION (single-Card execution, Main-only reconciliation),
  WORKSTREAM, unchanged `cards/M07-T05.md`, every named authority
  (`requirements/PASEO_UPDATE_DISTRIBUTION.md` R2,
  `requirements/PASEO_GUI_RUNTIME.md`, `decisions/ADR_PUD_001/002/004`,
  `planning/PASEO_UPDATE_DISTRIBUTION_P4.md` M07-T05 section),
  `contracts/PASEO_R2_CANDIDATE_VALIDATION.md`, prep reconciliation, exact DONE
  `results/M07-T04.md@6329cf488cebaf955a49cbace71d87613381dc11:c45b3f707b1246e195c9138d027cbb1b05b9b112`
  with R01 GREEN evidence, plus the full third-return correction section.
  The prior filename list is not authority to stage unbound code; all changes
  are minimal source/guard/delivery/binding/argument/test/doc inside the Card.
- Preserved real improvements from the third contribution (executable shared
  Codex path, actual guard hash compare, no generic dependency tails) while
  repairing provenance/auth/observer/lifecycle/completion/ownership machinery
  and coverage. No new pipeline, ledger, schema authority, or successor.
- Exclusions honored: no stable Card/contract/authority/history/Main-evidence/
  result/attempt/Board/manifest/Research/planning/successor writes; no real
  inference/auth/credential admission, HOME/runtime/harness changes, live
  Docker/Tower/host/production effects, image build/publication, CI trigger,
  PR/Issue operations, push, or further delegation. Only classified
  synthetic/local fixtures and approved non-inference public source/interface
  readback; fake executables/transports; disposable synthetic credentials.

### Exact source/provenance (recomputed)

- Implementation commit: `f897e03f369a56fb19ea038a7e60ee352f54b7a2` (unpushed):
  `scripts/paseo_tower_validator.py` (publication binding, strict real chain,
  adapter observer callsites, loader dispatch, UNKNOWN preservation,
  ID-bound ownership/cleanup, `--publication-file`, no tested aliasing),
  `scripts/paseo_candidate_muse_adapter.py` (same-origin helpers, terminal
  observer handlers, strict daemon/Pi observers, builtin-only Meta loader,
  loader-based local dispatch),
  `scripts/paseo_codex_noninference.py` (same-origin redirect enforcement),
  `tests/test_paseo_tower_validator.py` (distinct-type chain, loader/node-
  observer harness, `_find_node` which-mock isolation),
  `tests/test_m07_t05_validator_adapter.py` (redirect/observer/loader/
  daemon/Pi negatives + 11-probe regressions),
  `docs/PASEO_CANDIDATE_VALIDATION_M07_T05.md` (Correction 3, implemented
  facts only). `paseo_codex_noninference.py` transport otherwise preserved.
- Provenance recomputed: guard
  `sha256:7fd922da42fcebfb6ed9e83f1f3471ed5365ea7961bec2ca25cdc9fd62827e33`,
  policy `sha256:943ba67c3b23ca3d40f745ed4c4f653964898a460b94ec83c3cc7aebeec01d40`,
  companion `sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`,
  candidate file `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
  (Paseo 0.9.2 / Pi 0.87.1 from frozen components).
- Pinned public sources read (non-inference, no auth): `pi-ai@0.87.1`
  `providers/meta.ts` (`envApiKeyAuth(..., ["META_API_KEY"])` + native OAuth),
  `dist/providers/data/meta.json` (contributor `max:null`, non-contributor
  `max:max`), `dist/models.js` (clamp/support semantics),
  `dist/api/openai-responses.js` (effort wire mapping), Paseo 0.9.2
  `dist/commands/agent/run.js` (only parsed `--env` forwarded to
  `createAgent.env`), `dist/commands/daemon/status.js` (`localDaemon`,
  `connectedDaemon`, `serverId`, `workerPid`, `daemonNode`, `providers` +
  home/listen/version), Pi `dist/core/extensions/types.d.ts`
  (`before_provider_request{type,payload}`,
  `after_provider_response{type,status,headers}`,
  `agent_end{messages}`, `agent_settled{}`), guard bytes (PROMPT +
  `--native-create-agent-args` shapes, fixed profile, no fallback).
- Negative facts preserved: Contributor `max:null`, unmodified `max→xhigh`
  clamp; `modelOverrides` remains unmanaged-HOME-only, not adopted.

### Reachable behavior (executing fakes; fake ONLY external boundaries)

- Distinct-type frozen chain through the genuine validator API+CLI: real
  candidate bytes (`candidate_id sha256:b4e0…`) + synthetic distinct OCI
  digest (`sha256:dddd…`) + real-schema handoff/build-input/build-record/
  tested/publication + staged guard/loader/observer + fake daemon/Pi/Codex
  lifecycle → mechanical PASS (fixture real false; real-mode structural
  `real_validation_satisfied: true` proven under fakes).
- Loader → guard → fake-Paseo (`META_API_KEY` required, exit 42) →
  request/response events; terminal via the ACTUAL staged observer bytes
  under node (fake SDK boundary fires `agent_settled`); per-test
  request+response+terminal aggregation → PASS. No marker-to-returncode
  mocks; internal plumbing (staged file execution, hash compare, guard
  gates, loader auth, observer emission) executes for real.
- Negatives (all fail required gates + assert no disallowed calls before
  cleanup): publication digest mismatch, tested-only minimal record,
  forged/malformed handoff/prepared/build records, stopped/unreachable/
  remote/null-PID daemon + foreign Pi (zero guarded dispatches), empty/
  wrong-name Muse secret, loader exit 42 on missing/empty pointer, clamp
  effort FAIL, response-only UNKNOWN, missing terminal UNKNOWN with
  preserved container + existing owned file, replaced container ID FAIL
  with no foreign removal, cleanup-race work preservation, cross-port
  redirect rejection with zero foreign requests/auth, opaque token redaction.
  Seven old probes stay closed.

### Counts/exits (honest, preserved; worker-observed for Main classification)

- Targeted: 30 tests OK, exit 0, 0 skips (validator 6 + adapter/matrix/probe
  24: 22 preserved/extended + redirect transport + 11-probe regressions).
- Affected (8 modules): 72 OK, exit 0. Full: 583 OK, exit 0, 0 skips
  (`discover -s tests`: 581 prior − 28 old targeted + 30 rebuilt targeted).
  Node catalog core: 1/1 GREEN, exit 0.
- Diff: only the six permitted source/test/doc paths + this report; no
  Card/contract/authority/state/history writes. Secret scans: no
  high-confidence credential patterns; only `*_API_KEY=` names + synthetic
  `fixture-*` in disposable temps; no raw secrets/bodies/prompts/tokens.
- Entry-point classification: every touched inference-capable entrypoint
  (`run-llm-test.sh` PROMPT/native-args, `paseo run/status`, `pi` as real
  binaries, validator ex-`/responses` smoke (removed earlier), live
  harnesses, docker builds, Tower live) — NOT executed as real; executed
  synthetically only via fake bindirs/mocked Docker/injected HTTP/localhost
  servers/disposable roots + approved non-inference readback. `PATH`
  isolated; a `shutil.which` mock-isolation fix (`_find_node`) keeps the
  node observer reachable under the docker-CLI mock. No test agent created;
  no real provider inference.

### Limits (not waived; owning boundaries)

- Fixture/rehearsal never satisfies the real gate. Real guarded inference,
  dedicated credential admission, live daemon bring-up, exact Paseo `--env`
  on-wire forwarding proof, real Codex-LB reads against operator endpoints,
  and on-wire max proof remain M08-T01 under the mandatory
  meta/muse-spark-1.3-contributor/max/no-fallback guard policy (no real test
  run here). Unsupported/unknown fails closed without fallback or provider
  bypass; the precise public source facts above are returned for Main-owned
  proportional Research/Planning if needed — no bypass invented, no
  complete/deferred-machinery claim.
- Changed candidate/companion needs a new immutable identity (M07-T07);
  M07-T06/M08 work excluded. No eligibility/production authorization claimed.
  Staged ephemeral files (observer/loader/per-attempt copies) are test-owned
  tooling outside the frozen companion; guard/delivery changes still need a
  new downstream artifact, never old-digest HOME blessing.

### Return

- Implementation SHA: `f897e03f369a56fb19ea038a7e60ee352f54b7a2` (unpushed).
- This report path:
  `implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-validator-implementation-2026-10-04.md`
  (report commit/blob below; secret-safe).
- Returns to Main for classification/reconciliation and later fresh
  independent review; not a workflow stop, result, verdict, DONE, or
  successor permission. This context cannot later review its own subject.

---

## Correction 4 (2026-10-04) — integrated path, qualified completion, complete binding [INCOMPLETE]

Old bytes above stay in Git history. This corrects Main's fourth validation
(`implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-return-validation-2026-10-04.md`
§"Fourth contribution", checkpoint `564c6a024ce27d3b3659390940e315e9cf1d9fa0`)
inside the SAME unchanged Card/technical contract (stable Card blob
`658fffe1…`, contract blob `54f9ccc3…`, both verified unchanged). Board 119,
M07-T05 `in_progress`, 22 DONE, no result/attempt. No push. This contribution
is explicitly INCOMPLETE for the full Card: it delivers the prioritized
bounded integrated path plus ownership/transport fixes for early Main
readback, with honest remaining gaps below. No `11/11 closed` claim is made
and no missing coding is deferred to M08 (M08 owns execution/admission/proof
only). This context implemented/repaired the subject and cannot later review
it.

### Recovery and scope

- Legal worktree `/home/paseo/projects/pi-unraid-paseo-update-distribution`,
  `feat/paseo-update-distribution`, launch HEAD `564c6a0` (Main evidence-only,
  clean); separate main worktree untouched. Default workflow
  `elmakus/project_workflow_v2@d3ab917` (verified current) ROUTER →
  EXECUTION, same obligation. Reread: full stable Card, selective contract,
  every named authority (PUD R2, PGR R2, ADR-PUD-001/002/004, P4 M07-T05),
  exact DONE `results/M07-T04.md@6329cf4:c45b3f70` + R01 GREEN, prep
  reconciliation, and the new Fourth section (owns this correction). The
optional fourth-probes script was used as diagnostic convenience only.
- Preserved genuine fourth-round progress (distinct identity types,
  publication input, byte checks, loader, terminal handlers, pre-dispatch
  refs, UNKNOWN preservation, ID-bound removal, same-origin checks).
- Changes (all inside the Card boundary; earlier filename lists never
  restricted scope): narrow guard extension + companion identity propagation
  (`config/`), validator/adapter/transport binding and callsites
  (`scripts/`), faithful CLI/daemon fakes + full-sequence observer harness +
  fourth-return regressions (`tests/`), implemented-facts docs (`docs/`),
  this report. No Card/contract/authority/history/result/Review/Board/
  manifest/state writes; no real inference/auth/credential admission, ordinary
  auth/HOME access, installed HOME/runtime/harness change, live effects,
  image build/publication, CI/PR/Issue/push/delegation/successor work.

### Exact source/provenance (recomputed)

- Implementation commit: `56f2728fff2d45be02524eed0128acf9b13d9aee` (unpushed).
- Guard `sha256:7da865ab7c10e74b1eb4a8b6305508a02031486dcb681d8c371e915bf7ba916c`
  (`0755`); policy
  `sha256:943ba67c3b23ca3d40f745ed4c4f653964898a460b94ec83c3cc7aebeec01d40`
  (`0644`); companion (10 files)
  `sha256:34aeccececa9da893be44b27823efe801e09a86a552d0a9dfa6f97d7318b4500`
  — new propagated identity (old `a51036c5…` remains the historical M07-T04
  subject only; fixtures carry the recomputed binding; M07-T07 fresh artifact
  still required; no old-digest eligibility).
  Candidate file `sha256:b4e0c1e7…` (Paseo 0.9.2 / Pi 0.87.1).
- Pinned sources read (non-inference, no auth): Paseo 0.9.2 `agent/run.js`
  (`parseRunEnv` first-`=` split, `createAgent({env})`), `daemon/start.js`
  + `local-daemon.js` (`env: process.env` inheritance),
  `daemon/status.js` (localDaemon/connectedDaemon/serverId/workerPid/
  daemonNode/providers), `agent/run.js` result (`agentId`), `agent/ls.js`
  + `agent/inspect.js` (`--json`, title/effectiveThinking/usage),
  server `paseo-env.js` (`createExternalProcessEnv(daemon env,
  launch.env)`, `META_API_KEY` not denylisted), Pi provider
  `pi/agent.js` + `cli-runtime.js` + `runtime.js` (`buildPiLaunch` argv/env,
  `PI_COMMAND` routing), Pi `extensions/types.d.ts` (request/response/
  turn_end-outcome/agent_end/agent_settled contracts),
  `agent-session.js` (stopReason→turn outcome; settled outcome-less),
  `docs/extensions.md` + `docs/sdk.md` (settled final-notification-only),
  `pi-ai` `providers/meta.ts` (`META_API_KEY` env auth), Meta model data
  (contributor `max:null`), guard bytes (both shapes, fixed gates intact).
- Negative facts preserved (contributor `max:null`, `max→xhigh` clamp,
  unmanaged-HOME override not adopted); presented as specific negatives only.

### Reachable behavior (executing fakes; fake ONLY external effects)

- Guard `--env` triple + correlated title + selector scrub + explicit local
  workspace through the genuine guard bytes (stub-`paseo` argv proof);
  transmitted names asserted exactly; raw secrets never in argv.
- Bring-up (`daemon start` under candidate-env) → status/pid/version → Pi
  path/version → dispatch (candidate-env + guard) → full observer sequence
  (request/response/turn_end/agent_end/agent_settled through staged bytes)
  → `agent ls` unique title match → `agent inspect` provider/model/
  EFFECTIVE thinking/usage corroboration, all through the genuine validator
  API/CLI with fake-only Docker/daemon/transport boundaries.
- Negatives: forged six-record chain (zero docker run/exec), aborted+
  settled → FAIL, garbage response → FAIL, policy bytes/mode drift → FAIL,
  post-observation replacement → FAIL/BLOCKED with zero later execs/rm,
  foreign secret source → FAIL with zero dispatches, replaced network →
  FAIL/BLOCKED with zero execs/rm, remote/null daemon + foreign Pi → FAIL
  with zero dispatches, agent-side clamp → FAIL despite witness,
  encoded `/v1/%72esponses` → check FAIL with zero receiver requests/auth,
  non-literal endpoint → reject without DNS. Seven old + eleven prior
  probes stay closed (rerun in-suite).

### Counts/exits (honest, preserved; worker-observed for Main classification)

- Targeted: 41 tests OK, exit 0, 0 skips (6 validator + 35 helper/adapter/
  matrix/probe: 24 preserved/extended + 11 fourth-return).
- Affected (8 modules): 72 OK, exit 0. Full: 594 OK, exit 0, 0 skips
  (`discover -s tests`: 583 prior + 11 new). Node catalog core: 1/1 GREEN,
  exit 0.
- Diff: only the seven permitted config/source/test/doc paths + this report;
  `git diff --check` clean. Secret scans: no high-confidence credential
  patterns; only `*_API_KEY=` names + synthetic `fixture-*`/`synthetic-*`
  in disposable temps; no raw secrets/bodies/prompts/tokens/headers/tails.
- Entry-point classification: every touched inference-capable entrypoint
  NOT executed as real; synthetic only via fake bindirs (argv-parsing CLI
  fake), mocked Docker, injected/localhost HTTP, disposable roots, node
  observer harness + approved non-inference readback. `shutil.which` mock
  isolation preserved (`_find_node`). No test agent created; no real
  provider inference.

### Explicit remaining gaps (why INCOMPLETE; owning boundaries)

- Real daemon/Pi/Codex execution with dedicated operator credentials, exact
  on-wire/daemon-internal delivery proof, and effective-max wire proof
  remain M08-T01. Fake daemon internals (env merge, Pi spawn, agent
  registry) simulate documented server behavior; the argv contract,
  bring-up/observation/inspection sequence, and all byte/mode comparisons
  execute for real. If any supported pinned realization proves
  unimplementable, exact source/interface facts above go to Main-owned
  Research/Planning — no bypass invented, no credentials requested.
- Corroboration limits: `PI_COMMAND` default resolution (no override
  pinned); image-Env Pi binding assumes the M03-rendered Env (fixtures
  fake it; no real image inspected here); buildx/publish/handoff full
  verifiers not re-run for documented context reasons (record-phase and
  consistency gates required instead); workspace isolation without ID
  readback; `ls` title uniqueness rests on per-attempt test-ID nonces.
- Changed companion needs M07-T07 fresh artifact + affected-gate evidence;
  M07-T06/M08 excluded. No eligibility/production authorization claimed.

### Return

- Implementation SHA: `56f2728fff2d45be02524eed0128acf9b13d9aee` (unpushed).
- This report path:
  `implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-validator-implementation-2026-10-04.md`
  (report commit/blob below; secret-safe).
- Returns to Main for classification/reconciliation and later fresh
  independent review; not a workflow stop, result, verdict, DONE, or
  successor permission. This context cannot later review its own subject.

## Correction 5 — fail-closed safety contribution [INCOMPLETE]

Date: 2026-10-04. Exact source/tests/current product documentation commit:
`e965948e146c671745dcc7e73a3b3f4f90d6a348` (unpushed).

Implementation contribution only: NOT an accepted result, Review verdict,
workflow stop or authorization to run a real test. FULL unchanged M07-T05
acceptance remains **INCOMPLETE**. Passing tests do not close the remaining
realization/binding/cleanup gates. No general unsupported-max impossibility or
non-remediable supported-source blocker is claimed.

### Recovery and preservation

Recovered current environment policy, project-recovery/bootstrap, legal feature
worktree, PROJECT/manifest/pre-execution pointers, Router/Execution/Continuation,
stable Card/technical contract, every named authority, prep reconciliation,
exact M07-T04 DONE/R01 GREEN and the complete Fifth correction. Independently
refreshed remote default workflow `d3ab917f02e4de91b7dbb17915c2287c2387333e`, then
cloned it to a disposable directory and byte-compared Router/Execution/Continuation
to the supplied snapshot. `python3 -m tools.router` selects execution/M07-T05,
no handoff (`python` is absent on this host; no standalone-script invocation).

Refreshed remote main `e9476b4987290767a195a9de2ecd655de5f09605` and remote feature
`8a0553079abac233b4ddc88ef4ce666cfbf3a661`. Clean launch was `12f2de8` on
`feat/paseo-update-distribution`. Seven permitted source/test/doc paths changed;
this appended report is the sole evidence change. Integration worktree remains
clean/read-only. Board119, manifest, stable acceptance blobs, all 22 exact DONE
result blobs and last terminal GREEN bindings, requirements/decisions/planning
and results/reviews are unchanged. Preservation audit initially assumed every
review used lowercase/nested V2 fields, exit 1; corrected mixed-schema audit
verifies all 22 subjects, exit 0. No result/Review/Board finalization, successor,
delegation or push occurred.

### Implemented safety changes (specific gates, not FULL closure)

- Before inference-capable dispatch, candidate-daemon `provider models pi
  --thinking --json --home` requires exactly one
  `meta/muse-spark-1.3-contributor` item with typed `thinkingOptionIds` including
  `max`. Missing/malformed/ambiguous catalog or unavailable max blocks before
  guarded prompt. Known max-null/clamped configuration must not first issue an
  xhigh request and then reject it. Catalog capability is necessary, NOT sufficient
  selected-process/effective/wire proof.
- Failed startup and already_running fail closed. Typed `daemon start --json`
  must report started and home/pid/listen must agree with status. Require explicit
  running/reachable plus worker PID/server identity/Node/provider details. Reread
  the same daemon binding immediately before guarded dispatch; replacement fails.
  This prevents false inheritance acceptance but does NOT implement missing
  controlled pre-staged startup/auth/selection.
- Observer agent_end without negative stop reason emits neutral ended, not done;
  empty messages plus settlement remain UNKNOWN. Aggregation requires one ordered
  request/response exchange, valid 2xx, exact model/max, qualified completed turn
  and final settlement. Duplicate/mixed/contradictory/malformed/reversed exchanges
  fail; arbitrary done/success cannot manufacture completion; abort/error is not
  overwritten. Agent-inspection model and ID comparisons are exact.
- Publication tested-image bytes are checked; prepared/tested candidate and handoff
  links and publication candidate/handoff/build links cannot silently omit hashes.
  Require builder_ensure GREEN, command=build, accepted IDs and complete companion
  declarations across prepared/build/tested. Omitted real-mode CLI companion derives
  from the frozen prepared declaration and is verified. Pulled image candidate label
  and Env must match resolution. Full producer/source/used-payload binding is NOT
  claimed complete.
- Acquired container/network IDs require equality, never prefixes. Every exec/cleanup
  container proof checks configured UID:GID, readonly root, required /tmp and /run
  tmpfs flags, bind mount type, no duplicates/extra destinations and exact secret
  sources. Exec remains immutable-ID addressed. Network/work/partial effects and
  honest cleanup accounting remain open.
- Codex transport positively permits only implemented GET /v1/models and /health,
  with redirects preserving exact check path and scheme/host/port. Arbitrary /v1/*
  is not assumed non-inference. Synthetic Docker's Codex boundary executes shipped
  argv with only namespace mount translation, no model/secret/base substitution.
- Shell markers are comments, not nonexistent commands. Product docs were rewritten
  coherently around current behavior/open gaps, not append-only completion claims.
  Historical evidence is preserved. No observer/success layer, profile/fallback
  relaxation or companion-delivery change was introduced.

### Source-qualified interface facts (metadata/source reads only)

Installed packages: @getpaseo/cli and @getpaseo/server 0.9.2;
@earendil-works/pi-coding-agent 0.87.1. Public locators under
`/usr/local/lib/node_modules/`:

- CLI `@getpaseo/cli/dist/commands/provider/models.js`,
  `sha256:259e92f5ac22bf0acdfd47485fc8db014c842ad0dd8db1cebb1b970c697adeee`:
  emits id/thinkingOptionIds/defaultThinkingOptionId from daemon catalog.
- Server `@getpaseo/server/dist/server/server/agent/providers/pi/agent.js`,
  `sha256:7faa688227512c81e8e5ac18b80c7719e85984a8e0b9b7c55f46b3eb15a40ee3`:
  resolvePiThinkingConfig excludes null mappings; fetchCatalog calls
  getAvailableModels(null) without prompt. PI_COMMAND/PI_ACP_PI_COMMAND and
  runtimeSettings.command affect executable selection, so another command -v
  invocation cannot prove daemon selection.
- Corresponding `pi/cli-runtime.js`,
  `sha256:64fe167d66ecd8a6429a8111bc5e289a9be564b08bdc8db9834ecd950c167ca9`:
  getAvailableModels/getState are non-inference RPC; prompt is inference-capable.
- CLI `dist/commands/daemon/start.js`,
  `sha256:0f78c30f71d905b75f182d5befcc505894316a1d35a34b5d1446e4f7d3100b5f`:
  typed started/already_running; status.js exposes independent connected/live facts.
  An existing process cannot inherit a later loader's auth.
- Pi `dist/core/extensions/types.d.ts`,
  `sha256:14d00e645b453f4361440da6fcda86ed6cef9a8fc36d483a621a0250e0d4a396`:
  response notification precedes stream consumption; turn_end has qualified
  outcome; agent_end has messages; final agent_settled is outcome-less.

These facts support preflight/negative gates, NOT a general unsupported-realization
blocker or effective-profile acceptance. No installed auth/credential value read.

### Executed synthetic verification and limitations

Final runs used PYTHONDONTWRITEBYTECODE=1 and disposable PYTHONPYCACHEPREFIX;
explicit test py_compile output is confined there. Node executes shipped observer
under fake SDK, HTTP is localhost-only, Docker mocked, guard PATH disposable fake
Paseo only. Classification: pure source/catalog/clamp readback, static readback
harnesses, mock-only external subprocesses and disposable synthetic secrets.
No real Paseo/Pi/provider inference entrypoint, auth/admission, installed HOME/
runtime/harness mutation, live Docker/Tower/host, image/CI/publication or production
operation occurred. Tests still have incomplete internal reconstruction; passing
counts are regression evidence, NOT full meaningful-entrypoint acceptance.

Final exact-source commands/counts, direct exits retained:

- `python3 -m unittest tests.test_paseo_tower_validator tests.test_m07_t05_validator_adapter tests.test_m07_t05_fail_closed`:
  **54 tests, exit 0, zero skips**.
- Same eight affected policy/delivery/companion/build/transaction/instruction/
  runtime/image modules as prior contributions: **72 tests, exit 0, zero skips**.
- `python3 -m unittest discover -s tests -p 'test_*.py'`:
  **607 tests, exit 0, zero skips** (594 prior + 13 new).
- `node --test tests/codex_lb_dynamic_model_catalog_core_test.mjs`:
  **1 test, exit 0, zero skips**.
- Changed-file AST and high-confidence secret-pattern scan: exit 0;
  diff check: exit 0; no untracked bytecode. No raw tokens, headers, bodies,
  dependency tails or secret values retained in this report.

Initial targeted run: 41 tests, exit 1 (one failure/two errors): legacy expectations
permitted unqualified done, omitted daemon fields and arbitrary same-origin
/v1/other redirects. Corrected expectations, not waived gates. Intermediate
52-test/full runs were superseded by final exact-source 54/72/607 gates.

New genuine-validate negatives assert no guarded dispatch for unsupported/absent/
ambiguous max, failed/already-running startup, omitted live details, truncated IDs
and independently changed producer links/phase/companion. Actual staged observer
executes empty messages negative. Current-ownership matrix challenges root user,
volume mounts, writable root, missing tmpfs, duplicate mounts and truncated ID.
Omitted-companion positive derives and verifies frozen declaration. Fake-tested
real flags remain structural diagnostics only; fixture mode leaves real gate false.

### Remaining FULL unchanged acceptance (not deferred missing M08 code)

1. Implement controlled pre-staged candidate startup, supported daemon config/env,
   actual daemon-selected Pi/process proof and private auth realization. Existing
   image startup can create upstream daemon; rejecting already_running is safe but
   not complete realization. Positive fake still returns canned startup/reconstructs
   guard plumbing, not a separate daemon selecting/spawning actual fake Pi.
2. Freeze all used observer/loader/Codex/helper behavior and relevant config through
   existing prepare/build/package, with complete actual file/content/mode readback.
   Generated helpers remain outside the 10-file companion. Finish full producer/
   source/archive/config linkage and actual-producer positive fixtures with only
   external effects fake; hand-authored chain is not acceptance proof.
3. Finish independently bound selected provider/workspace/process/owned-child
   observations, usable created-agent references under uncertain inspection and
   per-call correlation. Single-exchange aggregation is conservative protection,
   not full runtime provenance. Catalog max alone cannot prove effective/wire max.
4. Finish positive not-found vs failed inspect, partial/uncertain acquisition,
   full network/work identity/security and honest cleanup. Old cleanup can swallow
   failed removals/unverified mounted work; safe complete cleanup is NOT claimed.
5. Replace remaining harness reconstruction with exact shipped argv and namespace-only
   translation, separate daemon/Pi lifecycle and complete race/absence/partial checks.
   Do not treat 607 passing tests or fake real flag as closure of missing mechanics.

These are remediable SAME-Card implementation obligations, not missing credentials,
user inputs or permission for a bypass. No result/Review should be frozen from this
INCOMPLETE contribution. Main alone classifies/reconciles/reroutes. This context
cannot independently Review the source it materially repaired.

## Correction 6 — frozen payload, strict readback and honest cleanup [INCOMPLETE]

Date: 2026-10-04. Exact source/tests/current product-documentation commit:
`f10e29b6cb0e6e46cb69c8928fdccf8f6c9a51ab` (unpushed).

**FULL unchanged M07-T05 acceptance remains INCOMPLETE.** This is an unsuccessful
full-Card producing return, not a selected-subset completion, accepted result,
independent Review, workflow stop or authorization for real execution. I did not
finish the requested coherent daemon/process/owned-agent/provenance realization
and source-faithful external fixture. No genuine unsupported-realization blocker,
missing permission/credential or runtime safety fuse is established by this
return. Passing regression counts cannot compensate for those missing mechanics.
Main must not freeze Review or accept a semantic result from this contribution.

### Independently recovered authority and preservation

Read current environment AGENTS, project-recovery/bootstrap, feature PROJECT and
manifest, canonical Router/Execution/launch refresh/Continuation, all router-selected
records, unchanged M07-T05 Card and selective technical contract, every named
Card authority/P4 and exact M07-T04 DONE result/R01 GREEN evidence. Verified
`6329cf488cebaf955a49cbace71d87613381dc11:results/M07-T04.md` (workstream-relative)
resolves to `c45b3f707b1246e195c9138d027cbb1b05b9b112`.

Fresh `git ls-remote --symref` and a separate disposable default-branch clone of
`elmakus/project_workflow_v2` both identify
`d3ab917f02e4de91b7dbb17915c2287c2387333e`; selected Router/Execution/Execution Prep/
Continuation/router.py bytes match the supplied read-only snapshot. Invoked the
router from its package root with PYTHONDONTWRITEBYTECODE=1: execution/M07-T05,
handoff none. Fresh target/remote feature are respectively `e9476b4` and `8a05530`.
Clean legal launch was `a6ef5141b5e190de5720d79b6451625a6f541577`; all project work
used the absolute legal feature worktree, never integration/main.

Fourteen source/test/current-doc/delivery paths changed. Board119, the manifest,
stable Card/contract, requirements/decisions/planning/Research, results/reviews and
Main's return-validation evidence are unchanged. Reverified all 22 DONE result
blobs against their immutable bindings. M07-T05 remains in_progress, M08-T01
planned; no successor/result/attempt/state write, delegation or push occurred.
Integration worktree remains clean. Initial commit attempt failed for absent Git
author configuration (exit 128); corrected with invocation-scoped `git -c` identity,
not installed/global configuration mutation.

### Implemented changes and their limits

- Docker's upstream entrypoint/healthcheck is overridden with a non-daemon hold
  process before staging. Candidate code starts only through the later loader/
  daemon path. A fixed PATH and absolute PI_COMMAND are supplied; observed Pi
  resolution must be `/usr/local/bin/pi`. Status must actually advertise Pi, not
  merely a nonempty provider list. These are prerequisites, NOT actual daemon-
  selected executable/descendant/process proof; that remaining gap is explicit.
- Loader, actual ESM observer and the two shared Codex programs are now frozen
  `config/pi-agent` companion members, not host-generated post-staging additions.
  Existing prepare/build/package semantics carry `validation_sources` for nine
  used host-side source/helper files. Producer linkage validates its exact key set
  and SHA types; companion verification compares executing/source bytes. Actual
  staging requires the exact declared file set and actual modes; candidate readback
  compares every declaration member's hash/mode, not just two files/profile fields.
  Old declarations/digests cannot silently gain this payload. A fresh real artifact
  remains M07-T07; full source-commit/producer-chain qualification remains incomplete.
- Shipped observer is opt-in and inert for ordinary agents; absent test ID/private
  witness reference registers no handlers. Generated helper bytes are checked
  against frozen delivery. Strict witness readback validates every row before
  aggregation: malformed JSON/types, wrong subjects, unknown fields/kinds, empty
  rows or exceeded bounds fail instead of being filtered away. Missing readback
  stays UNKNOWN. Existing ordered exchange/qualified-terminal negatives remain.
  Selected Meta/Pi/process/workspace and actual owned-creation correlation are NOT
  thereby proved; title lookup/usage/idle is not full success evidence.
- Exact positively identified Docker absence is required before network/container
  creation; generic nonzero inspect/auth/permission/transport failure is not absence.
  Existing containers are never reclaimed without acquisition authority. Work
  device/inode/nonce are checked before exec/deletion, with symlink markers rejected.
  Network bridge/local/security properties, endpoint membership, acquired full ID
  and container NetworkID are checked at execution boundaries. Acquired-reference
  files exist before any possible object creation and are updated with returned IDs.
- Failed/uncertain cleanup now has explicit bounded fixed summaries and recovery
  locators. Failed removal, replaced/unverified objects or possibly mounted work
  cannot coexist with complete PASS or structural real=true. UNKNOWN is preserved;
  only verified acquired immutable objects are removal targets. Dedicated private
  input is untouched and must be owned by the candidate UID; ordinary auth/HOME
  input roots are rejected before content reads. Helper dispatch summaries no
  longer retain dependency stdout/stderr tails. Partial-acquisition reconciliation
  and the complete race matrix still require qualification.
- Added genuine-validate regressions for malformed/wrong-subject readback, absent
  Pi provider, failed removal and failed absence. Added frozen-source mutation,
  shipped observer opt-in, generated/delivered byte parity and exact hold-argv
  checks. Existing harness metadata/daemon reconstructions remain explicitly
  unqualified; no canned success is promoted to full acceptance.

### Exact stable-source verification (synthetic only)

Final runs used PYTHONDONTWRITEBYTECODE=1 and disposable PYTHONPYCACHEPREFIX,
including explicit py_compile. External Docker/Paseo/provider execution is fake;
HTTP is localhost-only, secrets disposable synthetic values. Actual guard/loader,
observer under fake SDK events and Codex programs are executed by the existing
harness. Existing pure producer prepare/build/package fixtures are exercised in
affected/full suites, but the validator's positive six-record fixture is still
hand-authored and is NOT full actual-producer-chain acceptance.

Stable source was no longer edited during the final run. Direct command exits
were separately captured; no tail pipeline hid failures:

- `python3 -m unittest tests.test_paseo_tower_validator tests.test_m07_t05_validator_adapter tests.test_m07_t05_fail_closed tests.test_m07_t05_readback_cleanup`:
  **64 executed, exit 0, zero skips**.
- `python3 -m unittest tests.test_llm_test_policy_contract tests.test_m07_t04_policy_delivery tests.test_paseo_companion_bundle tests.test_paseo_candidate_build_pipeline tests.test_paseo_transaction_guard tests.test_pi_instruction_plane_contract tests.test_paseo_runtime_contract tests.test_paseo_child_image_contract`:
  **72 executed, exit 0, zero skips**.
- `python3 -m unittest discover -s tests -p 'test_*.py'`:
  **617 executed, exit 0, zero skips**.
- `node --test tests/codex_lb_dynamic_model_catalog_core_test.mjs`:
  **1 executed, exit 0, zero skips**.
- Changed-file AST/explicit py_compile: **11 Python files, exit 0**, cache outside
  the repository. Node observer syntax, loader shell syntax, diff check, no derived
  repository bytecode and bounded high-confidence scan of **14 changed files**:
  exit 0. The scan is not proof of total secret absence.

Intermediate runs are not hidden: initial 74-test combined run exited 1 (8
failures/4 errors), exposing strict-source declaration, old Pi/stale-row expectations
and a fake boundary that mistook shell file readback for Python execution. Later
81-test combined run passed. An intermediate 61-test targeted run passed while
72 affected failed a source-syntax secret-pattern check; its full run also failed
because source fingerprints were changed while the background run was active.
Those mixed-source runs are NOT exact-subject evidence and were superseded by the
stable 64/72/617/1 runs above. Source syntax was corrected rather than weakening
the secret-scan contract. Historical report bytes remain intact.

### Agent-findable pinned source facts, not a general impossibility claim

Official installed source inspected without inference/auth/ordinary-credential
reads, under `/usr/local/lib/node_modules/`:

- Paseo server 0.9.2 `dist/server/server/agent/providers/pi/agent.js`, SHA256
  `7faa688227512c81e8e5ac18b80c7719e85984a8e0b9b7c55f46b3eb15a40ee3`:
  resolvePiThinkingConfig excludes null mappings; PI_COMMAND/PI_ACP_PI_COMMAND
  and runtimeSettings.command can select the executable.
- Corresponding `runtime.js`, SHA256
  `8a17e41b8b04f457580334b61831a2d83f6c1ae4bac76d35f73f5cec5739dcd2`:
  supported replace-command selection and session/runtime env overlay.
- Pi-ai 0.87.1 `dist/providers/data/meta.json`, SHA256
  `1b650998c0f9b404246cde1d353105e6d825d8a7292d8f8c43e85dd3402dc130`:
  exact Contributor max=null; non-Contributor max=max is a different model.
- `dist/models.js`, SHA256
  `75fa33149fb608bc4a7b7a0586c8ca8f0024465d580091b0c426c0baf3fbc80a`:
  getSupportedThinkingLevels excludes max and unmodified clamp maps requested
  Contributor max to xhigh. No override/substitution/fallback was adopted.
- `dist/providers/meta.js`, SHA256
  `f0ba7b97a407336f30cfb230c4c32bece9e0fd23b0ebdbdae11503374e5ab44c`:
  supported META_API_KEY/native OAuth. This does not prove actual private daemon/
  Pi auth inheritance; that realization still needs integrated qualification.

These are precise known default-path negatives and supported-interface facts,
not proof that every supported realization is impossible, a new Research result,
or permission to defer missing M07-T05 code to M08.

### Exact remaining full-Card mechanics

1. Source-qualified private daemon config/auth inheritance and actual selected Pi/
   process/connected-server correlation; scrub/bind every later selector and effect.
2. Complete actual producer schema/status/type/byte/source/shared identity proof,
   including source-commit/configuration linkage and positive chains from the real
   producers with external effects only faked.
3. Supported actual owned creation/readback, selected provider/Pi/process/workspace
   and effective request/response/qualified final completion correlation. Preserve
   actual IDs/references on uncertain creation/inspection, not anticipated titles.
4. Finish partial/uncertain acquisition readback and all current-isolation/race/
   cleanup cases with source-faithful external fixtures. Conservative preservation
   alone is not full lifecycle qualification.
5. Separate fake daemon selecting/spawning fake Pi from inherited/scoped env;
   execute exact shipped argv/internal shell/guard/loader/observer/non-inference
   logic with namespace translation only. Replace remaining internal metadata/
   argv/witness reconstruction and qualify the full omission/mutation matrix.

These remain remediable SAME-Card coding obligations. No user input, credential or
new approval is requested; no canonical stop is asserted. Main retains acceptance,
reconciliation and Review freezing. This context materially produced the source
and cannot independently Review it. The canonical route remains Execution/M07-T05.

## Correction 7 — actual context and qualified pretransport rejection [INCOMPLETE]

Producing repair contribution, not independent Review or accepted Card result.
Source subject: `63823cf0dddb70ba06b9bb3fca6e0cf0416256d9` (unpushed), on the legal
`feat/paseo-update-distribution` worktree. Launch was clean
`d575ce3ca455ab471ab0d41a1350dedc1921340a`; Main's Seventh contribution correction
was consumed unchanged. No delegation or model/thinking change occurred.

**Full M07-T05 is still INCOMPLETE.** This contribution does not fulfill the
instruction to finish the entire unchanged Card. No genuine non-remediable
whole-Card blocker or canonical stop is established. The bounded source facts
and transport fuse below cannot waive the remaining implementation. Main must
not freeze independent Review or reconcile acceptance from these test counts.

### Recovery and preserved authority

Recovered the project/workstream, canonical Router/Execution/Execution Prep/
Continuation, full named Card authority, technical contract and exact GREEN
M07-T04 result/review. Remote readback still yields project main
`e9476b4987290767a195a9de2ecd655de5f09605`, remote feature
`8a0553079abac233b4ddc88ef4ce666cfbf3a661`, workflow main
`d3ab917f02e4de91b7dbb17915c2287c2387333e`. The canonical router, run as its package
module with the exact manifest locator, returns Execution/M07-T05, handoff none.
Initial attempts using a nonexistent archive remote, direct-file router imports
and a short workstream name failed; corrected commands produced these readbacks.
These invocation errors were not authority changes or blockers.

All 22 DONE result blobs match both their exact commits and HEAD. Board119,
M07-T05 in_progress and M08-T01 planned remain unchanged. Integration/main is
clean. No authority, Card/contract, planning/Research, Board/manifest, result,
review, Main classification or historical evidence prefix was changed. The
preexisting worker report's 67,799-byte prefix has SHA256
`a39668933eeff664e16da09c093b156ba509fd9117014fd751530dca07551a6f` and is preserved.

### Implemented repair and limits

- The actual frozen observer reads supported handler context
  `ctx.model.provider` and `ctx.thinkingLevel`, separately from wire model/effort.
  Request readback now requires typed actual provider/thinking facts; aggregation
  cannot infer meta/max from a fixed payload label. Main's codex-lb/max and
  meta/xhigh contexts with max payloads both fail and invoke abort.
- Wrong/unobservable profile and failed private observation invoke supported
  `ctx.abort()`. If context/abort cannot synchronously prove an aborted signal,
  only the explicitly opted-in test Pi process exits 42. This local fail-stop
  is not model fallback, real success or a workflow stop.
- Witness output is restricted to bounded vocabularies, not arbitrary field
  strings. Opening rejects symlinks, nonregular/wrong-owner/nonprivate files and
  oversize files. Unprivate/symlink controls preserve their targets and prevent
  even fake transport. Observer staging copies the actual frozen delivery member
  instead of an independently maintained generator. Legacy fake fixtures now
  supply the supported context and a private test-owned witness file; negative
  context/effort controls remain negative.
- New transport qualification imports actual pinned ExtensionRunner, Agent and
  OpenAI Responses implementation, with every transport explicitly replaced by
  in-memory fake fetch and a disposable synthetic key. No credential store/auth
  resolver or real provider transport is called. The actual runner catches the
  throw-only control and the fake transport entry marker is reached once. With
  supported observer abort, caught rejection yields zero fake fetch calls. Missing
  signal/broken abort exit the child with 42 before that same reachable marker.
- A separate isolated synthetic daemon uses actual Paseo PiRpcAgentClient,
  PiCliRuntime, command replacement and JSONL process code to select/spawn a
  separate metadata-only fake Pi. Only public official Meta model data is served;
  effective-level calculation is the unmodified official clamp. Catalog mapping
  excludes max. An actual created-session runtime readback reports xhigh and
  updates configuration to xhigh despite requested max. Actual child PID/PPID,
  argv and disposable synthetic auth inheritance are checked. Only
  get_available_models/get_state RPCs occur: no prompt, steer or inference RPC.

These qualifications establish the exact unmodified pinned source's negative
behavior, including the caught-error transport hazard and the repair's barriers.
They do not prove general impossibility of every supported realization, the full
candidate's connected server/agent/workspace binding, qualified positive real
completion or the complete external fake validator harness. No provider override,
max mapping substitution, fallback or unofficial capability was adopted.

### Exact final verification

Source was committed before final gates and held unchanged throughout them.
Each launch uses env -i, disposable HOME and explicit disposable compile caches;
all provider-capable diagnostic calls use external synthetic transports, and
existing validator execution is wholly mocked/localhost with synthetic secrets.
The classifications and limits above are part of the evidence, not a real gate.

Final job 7 on exact `63823cf0dddb70ba06b9bb3fca6e0cf0416256d9` records direct exits:

- Six targeted modules: **70 executed, exit 0, zero skips**.
- Eight affected policy/delivery/companion/build/guard/instruction/runtime/image
  modules: **72 executed, exit 0, zero skips**.
- Full classified Python discovery: **623 executed, exit 0, zero skips**.
- Applicable Node catalog suite: **1 executed, exit 0, zero skips**.
- AST and explicit isolated py_compile: **7 changed/new Python files**, PASS.
- Node syntax: observer plus three new fixture programs, PASS; guard/loader shell
  syntax and diff check PASS. No repository bytecode exists.
- Bounded high-confidence secret-pattern scan: **12 changed/new source/test/doc
  files**, PASS; not complete secret-absence proof. Only declared disposable fake
  credentials occur in these tests, never raw real secrets.

Logs: `/tmp/pud-qualified-final-{targeted,affected,full,node}.log`; job 7 records
exact subject and all direct exits. Earlier job 5 ran 67 tests and exited 1 with
one stale observer fixture lacking supported context. It was corrected without
weakening the terminal-negative assertion. Intermediate stable job 6 passed
69/72/622/1 before the missing-signal/broken-abort fail-stop addition. Both are
superseded by exact final job 7; no mixed-source run is called final evidence.
Six new qualification tests also passed directly before the source commit.
Git's missing author configuration initially prevented commit; command-local
worker identity completed it without changing global/repository configuration.

Recomputed companion: 14 files, digest
`sha256:f45f70254c7dbc252955106b54597132d0b17fc57ad8e48a6ea6a3f4e59457f9`, nine
validation-source hashes. Observer digest:
`sha256:a2f5a71b59319f0923db8588d275a3911b49b6f4332e378bca4f9f688a2c5dbf`.
Fresh later artifacts remain required; these changed payloads cannot bless an old
OCI digest. No build, resolve, publication, host, CI or production operation ran.

### Source qualification locators

Read-only installed official sources; SHA256 values:

- Pi extensions/runner.js: `67c7ca2d24197ff46cb5f0a49d7c19a76825ab7c66bc942015a484b550396441`.
- Pi core/agent-session.js: `5ebfae51db5a900596145159428e7cb57d195af9d54a28f41d4ac8ff1bfd5729`.
- Pi modes/rpc/rpc-mode.js: `bdd94e753e6d19731d9fb9ea370462d095d64f1e78bddd7651320663fa57c4ff`.
- Pi-agent-core dist/agent.js: `3a890712a7a02fc29754a2af61b758cba43eec97d289e446cd7e432ed0093085`.
- Pi-ai dist/api/openai-responses.js: `3e95145f94ac2a255d1adc0ae65cf02c2e6d479f7a2dbf5c466db21885c29ec6`.
- OpenAI client.mjs: `45b54e0c0a779a8b284cc8bcfb41a0a0f1817eac32d9cc585ff71875b62aeb6b`.
- Paseo pi/agent.js: `7faa688227512c81e8e5ac18b80c7719e85984a8e0b9b7c55f46b3eb15a40ee3`.
- Paseo pi/cli-runtime.js: `64fe167d66ecd8a6429a8111bc5e289a9be564b08bdc8db9834ecd950c167ca9`.
- Paseo pi/runtime.js: `8a17e41b8b04f457580334b61831a2d83f6c1ae4bac76d35f73f5cec5739dcd2`.
- Paseo jsonl-rpc-process.js: `37b4f3f2620c249d520ce1fa65a9f35366eef4c4fb89c1a0cdf13bc84597c12c`.

RPC mode binds no custom abort handler; normal AgentSession.abort synchronously
calls Agent.abort before awaiting settlement. The SDK checks the signal before
fetch. Executable synthetic controls exercise actual runner/Agent/SDK behavior;
these source facts do not claim installed daemon/production validation.

### Still required under the same unchanged Card

Private daemon configuration/selector scrubbing and full connected-server/Pi/
agent/workspace proof; complete actual-producer and immutable source/configuration
linkage with genuine positive producer chains; actual creation IDs and uncertainty
readback updates; per-test/process effective exchange and final-completion binding;
full separate source-faithful fake daemon/CLI/guard/loader/Pi validator realization;
and the remaining omission/mutation, collision/race/partial-acquisition/current-
isolation/cleanup matrix. The old hand-authored positive chain and reconstructed
full-validator daemon still do not qualify those requirements.

No real credential/input is requested, no acceptance or blocker state is written,
and no independent verdict is possible from this producing context. Main alone
reconciles and freshly reroutes. End of this contribution is not semantic
completion; the unchanged route remains Execution/M07-T05.

## Candidate-local runtime / owned-lifecycle contribution — 2026-10-04

### Scope and immutable source

This is implementation and synthetic qualification evidence for the existing
Execution/M07-T05 obligation, not a semantic Card result or an independent Review.
Main alone classifies and reconciles the full unchanged Card.

Unpushed source commits, in order:

- `8268e2b7b26d3aa50af379940405244b4a6586cc`: private guarded runtime, actual
  native creation, effective context, selected process and API lifecycle binding.
- `c52be1a4b6563388075ab6c64f0584a31e6258be`: actual API request observations
  before cleanup, proof collision qualification and owned fake process teardown.
- **Final qualified source: `306f1565dab551c145122f23484f5232d679c90f`**: require
  actual runtimeInfo.model without falling back to requested model; exact mounted
  synthetic input translation; argv-derived fake Pi state; lost receipt after
  one exchange; exact bigint inode identities; generic secret-safe status errors.

The pre-existing report prefix is preserved byte-for-byte: 77474 bytes, SHA256
`b8937d1b203f702a81633fb2afc99fff688a32da8bf60fbf821252c9a497e0c4`.
No previous contribution or Main correction/classification is rewritten.

### Runtime mechanics implemented

- Controlled env-i launch, private HOME/Paseo/Pi directories and exclusively
  staged private daemon configuration. Pi uses the declared replacement command;
  plugins, relay, MCP injection and browser tools are disabled. No ambient
  endpoint, caller, executable, agent-directory or auth selector is adopted.
- Shipped canonical guard gains a narrow candidate-owned private-config mode.
  Fixed Meta/Contributor/max/native-shape checks run before its owned bridge.
  Native-shape export remains metadata, never execution or provenance evidence.
- Supported prompt-free workspace and agent creation: no initialPrompt. Modern
  creationLifecycle support is mandatory; requested IDs and creation keys are
  written before acquisition, then acknowledged IDs must match. No legacy
  fallback, ambiguous title/prefix lookup or automatic workspace env is used.
- The connected server identity is checked against actual daemon readback.
  Actual snapshots must expose the acquired IDs, workspace, cwd, Pi provider,
  actual runtimeInfo.model and effective thinking. Requested model alone cannot
  substitute for unavailable effective state.
- The daemon-selected wrapper checks the actual Pi entrypoint bytes and dedicated
  auth inheritance in memory, recording only a boolean. Actual PID/PPID, process
  start times, parent Node executable and Pi RPC/model/thinking argv are verified
  before send and after completion. The API message ID is retained before its
  single send and checked in the fixture's actually received request envelope.
- Private references are atomic before/after effects; config/reference/binding
  replacement is rejected, including identical-byte replacement. Bigint dev/ino
  identities avoid Number rounding. Process proofs reject extra fields. The
  observer binds every admitted event to actual process, test, agent, workspace
  and server, preserving the previously qualified abort/opt-in fail-stop barriers.
- Connect/create/inspect/send have bounded observation; completion and total
  observation are bounded. Uncertain creation, dispatch or inspection never
  replays a prompt. UNKNOWN retains usable private requested/acknowledged IDs and
  readback paths and does not trigger unproven cleanup. Neutral idle/usage is not
  final completion evidence; qualified aggregated exchange/completion is required.
- Pinned hooks expose no universal provider request ID: only one exchange is
  admitted. API creation/message IDs are not misrepresented as provider IDs.

### External-fake qualification and boundaries

The separate external fixture supplies a CLI, TCP daemon and separately spawned
fake Pi. It executes namespace-translated shipped validator/guard/loader/wrapper/
bridge/observer plumbing, using exact argv/shell and separate OS processes. Public
pinned buildPiLaunch and PersistedConfigSchema are imported read-only solely as
metadata plumbing. The fake Pi derives selected model/thinking from its launch
argv; the daemon's snapshot comes from that process's RPC state, not a copied
expected provider/title/usage bag. The genuine-validator fixture translates the
mounted input pointer to that SAME synthetic file without substituting a key.

Actual create request keys/IDs and message envelope are captured in the fake
external daemon before cleanup without recording prompt or credential values.
Reachable negatives cover wrong server/daemon/process/executable bytes, wrong or
missing agent/workspace/effective model/thinking, wrong agent env/auth/selectors,
unsupported or unresolved creation, uncertain partial acquisition/inspection,
config/reference/binding replacement, reference/process-proof collision, observer
context disagreement, completion failure and receipt loss after one exchange.
Before-cleanup assertions check no forbidden prompt/transport calls; uncertain
post-effect controls check exactly one exchange, no replay, retained IDs and no
Docker removal. Existing targeted omission/mutation/current-isolation/cleanup and
source-faithful pinned clamp/abort qualifications remain in the executed cohort.
Fake teardown itself checks retained PID start identity, including after its
private HOME disappears; failed fake removal does not prematurely stop its daemon.

All launches use env-i with disposable HOME and compile caches. All credentials,
transports and daemon/Docker/provider boundaries are synthetic or localhost test
fixtures; no real provider/auth resolver, real inference, credentials admission,
installed HOME/runtime/harness mutation, live Docker/Tower/host/production, actual
candidate artifacts/CI/PR/Issue/push or successor work occurred. Synthetic maximum
support is not real availability evidence. The official pinned Contributor max-null/
xhigh-clamp negative remains unchanged; no mapping, override, fallback or substitute
provider/model/thinking was adopted. Ordinary worker/Main settings were not changed
and no further delegation occurred.

### Exact final gates

Final source was committed and held unchanged throughout background job 8:

| Gate | Executed | Direct exit | Skips |
| --- | ---: | ---: | ---: |
| Seven targeted runtime/validator/qualification modules | 77 | 0 | 0 |
| Eight affected policy/delivery/build/image/runtime/instruction modules | 97 | 0 | 0 |
| Full Python discovery | 630 | 0 | 0 |
| Applicable Node catalog suite | 1 | 0 | 0 |

Logs: `/tmp/pud-owned-final306-{targeted,affected,full,node}.log`.
Job 8 ends with exact source `306f1565dab551c145122f23484f5232d679c90f`,
all four direct exits zero and aggregate exit zero. No hidden skips were accepted.
AST/explicit isolated py_compile, Node checks for bridge/observer/external fixture,
guard/loader shell syntax, exact source diff check and bounded high-confidence
secret-pattern scan of all 12 changed source/test/doc files pass. Repository
bytecode is absent. Known synthetic-sensitive strings are absent from final logs;
these bounded scans are not a complete secret-absence proof.

Earlier exact-source runs are diagnostic failures, not final qualification:
8268e2b job 6 had 77/630 tests with one stale legacy CLI-env assertion failure;
c52be1a job 7 had 77/630 tests with 12 fixture cleanup telemetry errors when no RPC
trace yet existed. Both ran affected 97 and Node 1 successfully. Final correction
keeps positive request observations mandatory while correctly recognizing no trace
before RPC acquisition. One short diagnostic named a nonexistent test method and
exited 1; the corrected late-receipt/completion test passed. None is hidden or
called acceptance evidence; exact final job 8 supersedes them.

### Frozen delivery identity and remaining full-Card work

Final companion: **16 delivered files**, nine validation-source hashes; digest
`sha256:f75ba933c2f4b64a3c0050cc81cdbb5ad9a821449ed171505e235a49f0fd428b`.
The new runtime helpers are actual companion members; existing prepare/build/
package/delivery/readback enumeration carries their modes/content. Relevant SHA256:

- guard: `80e6dd151872c99ff5363894920ae0790420a9598a613cd6bd259aa653682fde`;
- owned bridge: `83502725c0a065259cffb6af030ffd5680e55b4fe18e4e612c06c6db4773f7e6`;
- selected-Pi wrapper: `161ee37067cb2ef3750f4253654a4f74514abb953791c24ba6db9fdebcd1f05d`;
- observer: `993f8d47e226afb1b3cd179bbe3883450cd36eb3ed7257929ec1d02c3ac3a56d`.

Changed payload/source identity is not eligible against an old artifact digest.
Historical M07-T04 and earlier M07-T05 companion identities are not reused or
blessed. This contribution's positive full-validator chain is synthetic and does
NOT establish a genuine positive chain made by actual producers.

**Focused runtime contribution: qualified by the described external-fake evidence.**
**Full unchanged M07-T05 Card: still INCOMPLETE.** Main's sequential producer-side
completion remains: claimed Git head versus actual tree/configuration, archive
byte/format linkage, producer-derived alias, complete prepare/build configuration
reconstruction and positive actual-producer chain without replacing internal smoke
aggregation. Actual producer shapes remain authoritative: candidate has no overall
status; Buildx uses command=build and per-phase status=ok; publication has no
companion field. These are not manufactured from expected fixture fields.

Current default workflow main was freshly confirmed as
`d3ab917f02e4de91b7dbb17915c2287c2387333e`; the router invoked as package module with
project root plus full workstream manifest selects Execution/M07-T05, not Review.
Board119/22 DONE bindings, M07-T05 in_progress and M08-T01 planned remain untouched.
Card blob `658fffe1d9d547a1a1525194628cdc2414ccc524` and contract blob
`54f9ccc3515bf0f8af527fec4ba8871868750c6b` remain unchanged. No result, review,
blocker/stop, planning, Research, Board or manifest state was created. Main alone
must classify/reconcile and continue canonical routing; this technical return is
neither semantic completion nor a workflow stop.

## 2026-10-05 — Full unchanged M07-T05 implementation continuation

This prefix-preserving contribution addresses the full delegated producer/source,
supported-interface, owned-runtime/lifecycle and final-qualification work, not a
producer-only checkpoint. It is technical implementation/verification evidence;
Main alone owns acceptance classification, results, Review and reconciliation.
No semantic GREEN/DONE or whole-Card impossibility verdict is asserted here.

### Exact unpushed subject and changes

Qualified source: `3955fc132ad4da57d15118142bc94f07685af8ef` on
`feat/paseo-update-distribution`, legal root
`/home/paseo/projects/pi-unraid-paseo-update-distribution`.
The source-only sequence from `942580a720274d57790674c3ec515a6a1ebc5d49` is:

- `4c4db993d7e75495513dfbf71d88f482aba91643` — immutable producer inputs,
  genuine chain and pinned workspace/client/protocol qualification;
- `eae0c737168ccbb1e6c06e82198da5ef5c3daacf` — preserved layer reconstruction,
  source/configuration revalidation and typed report bindings;
- `dc06b460ec37ce07ee576fd512a98a9f08293c6d` — uncertain ownership, usable
  cleanup references and connected socket server-info qualification;
- `a635302a100c33319bd6647aa95caed6ca29acb4` — type-strict source/companion,
  actual builder/image/cache/candidate configuration;
- `3955fc132ad4da57d15118142bc94f07685af8ef` — preserved platform/rootfs/layer
  forgery qualification.

The cumulative source diff has 11 files: the owned bridge; current product doc;
existing Buildx, candidate-build and Tower-validator programs; separate owned
external fixture; genuine producer fixture; owned-runtime, producer-proof,
validator-adapter and Tower-validator tests. No authority, historical DONE,
planning, Research, result, review, Board/manifest or successor material changed.
Integration/main stayed read-only at `e9476b4987290767a195a9de2ecd655de5f09605`.

### Implemented and exercised full chain

- Actual `facts_to_candidate -> handoff.prepare -> prepare_context/
  verify_build_inputs -> build_parser/cmd_build -> genuine smoke dispatch and
  aggregation -> package_tested_image -> publish -> Tower validate` produces
  all six files and feeds them unchanged into the positive consumer. External
  subprocess/Docker/transport effects alone are faked. Docker save emits
  synthetic bytes consumed by genuine archive/config/layer hash routines.
  The unused hand-authored positive chain helper was removed.
- Immutable Git HEAD, single parent, discovery ref ancestry, commit/tree/file
  contents and executable modes are read against the actual source. Extra,
  changed, missing or symlinked inputs fail closed. Rendered Dockerfile,
  staged candidate/tree, complete prepared readback and executing validation/
  producer source are reconstructed and checked, not trusted as nine hashes.
  Git reads exclude ambient selectors/global configuration/replacement objects.
- Buildx retains actual argv/progress/labels/metadata/smoke configuration and
  frozen prepared source, verifies staged inputs and repeats companion/input
  readback around genuine smoke dispatch. Actual phase `ok`/command `build`
  schema and typed durations/builder/cache/image/candidate data are checked.
  Source/companion schema booleans cannot masquerade as version integer 1.
- The preserved Docker-save bytes, unique safe manifest/config/layer members,
  exact tag/config SHA-to-local-ID link, Linux platform metadata, rootfs and
  layer diff-ID bytes/tar structure are inspected without extraction. Pulled
  runtime config matches the preserved image config. Publisher-derived
  candidate alias and six raw record hashes are bound. Candidate ID, OCI
  digest, local/platform image ID and file/archive/companion hashes stay distinct.
  Raw records, immutable source/config, companion and archive are reread
  immediately before inference-capable dispatch.
- Workspace IDs now use `wks_` plus 16 lowercase hex digits; actual pinned
  protocol rejects UUID/uppercase alternatives. The separate external socket
  fixture uses pinned `DaemonClient`, inbound/outbound/Workspace schemas and
  real SDK receipt selectors, rejects foreign requestIds and exercises modern
  creationLifecycle. Connected server-info is received and parsed from the
  daemon socket rather than copied from the expected status file. Server
  replacement before/after prompt is covered. Reconnect is disabled exactly
  as in the pinned CLI; no automatic creation replay is permitted.
- Genuine validator/private guard/loader/wrapper/bridge/observer/non-inference
  programs run with namespace translation and external fakes. A separate fake
  daemon launches a separate fake Pi through the actual pinned launch builder;
  inspected model/thinking comes from its RPC state and process/auth identity
  from actual separate process observations, not a canned snapshot. Faults
  cover snapshot omission/type/profile/parent binding, ambient/missing auth
  selectors, private-reference/config/process-proof collisions/replacement,
  uncertain creation/prompt/completion/inspection and no-replay retention.
- Numeric 0/1 cannot prove mount RW booleans. Network/container acquisition
  receipt loss becomes UNKNOWN with usable requested names/nonce/private refs,
  no replay and no unproven removal. Cleanup refuses foreign/replaced/in-use
  networks and retains private work/nonce/object refs until external removals
  all succeed. Network cleanup removal/inspection failure is unsatisfied and
  retains references; exactly one exchange is observed, never resent.

`test_m07_t05_producer_proof.py` includes 27 self-consistently relinked
source/configuration/schema/command/smoke/archive/alias negatives plus four
relinked platform/rootfs/layer forgeries. These reject before any Tower Docker/
acquisition/dispatch call. Post-acquisition configuration drift rejects before
prompt/transport/guarded dispatch. Lifecycle cases assert retained private usable
IDs and absence of forbidden calls/removals, not merely an exception string.

### Entry-point classification and exact-source gates

Inference-capable/effectful entrypoints: Tower `validate/main`, guarded bridge
`dispatch`, and the unchanged shipped guard owned-smoke/ordinary launch switches;
its native-shape export path alone is export-only, not dispatch. The loader/
wrapper can start the selected Pi and the observer runs at provider-request time;
tests traverse these shipped programs only into controlled fake processes/fetch.
Existing Buildx build/smoke, package/save and publish entrypoints are effectful
and are exercised only with external process/Docker fakes. Bridge acquire/inspect,
provider-model preflight, version/static checks and authenticated Codex checks are
non-inference. Actual Pi Agent/ExtensionRunner/provider SDK transport tests replace
fetch for every branch, including throw-only control; these are synthetic, not
real LLM tests. No ordinary credential values, real inference/auth, live Docker/
Tower, real build/publication, CI/PR/Issue operation, push or installed HOME/
runtime/auth/harness/instruction-plane mutation occurred.

Final gates ran together against held source `3955fc1`, with direct exit capture
and matching initial/final HEAD plus clean tracked source. Every invocation used
`env -i`, disposable HOME/cache, restricted executable resolution, isolated
Python cache prefix and bytecode suppression. Node/python were explicit disposable
bin symlinks. Full discovery additionally required a disposable external Docker
fake accepting ONLY `rm -f paseo-state-candidate-aaaaaaaa` and
`rm -f paseo-state-previous-bbbbbbbb`; every other operation exits 99 and never
reaches installed Docker. Its trace contains exactly these two accepted calls.
The unchanged historical state-roundtrip test had omitted a subprocess cleanup
fake; its project source/test was not modified to conceal that harness limitation.

| Gate | Exact result | Direct exit / skips |
| --- | --- | --- |
| Targeted eight modules | 88 tests, 335.839s, OK | 0 / 0 |
| Affected eight modules | 72 tests, 1.771s, OK | 0 / 0 |
| Full classified Python discovery | 641 tests, 357.571s, OK | 0 / 0 |
| Node dynamic catalog core | 1 passed, 137.455223ms | 0 / 0 |
| AST + isolated explicit compile | 8 changed Python files | 0 |
| Node syntax | bridge, observer, external socket fixture | 0 |
| Shell syntax | unchanged guard and candidate loader | 0 |
| Cumulative diff and bounded high-confidence scan | 11 source files | 0 |

Final local logs: `/tmp/pud-3955fc1-final-{targeted,affected,full,node}.log`;
combined direct exit/source/cleanup trace receipt is background job 8. Logs are
convenience diagnostics, not workflow authority. There were no intentional skips
or exclusions from full discovery, and test counts alone are not acceptance.

Intermediate failures are preserved rather than converted into qualification:
initial changing-source cohort had 61 tests/128.099s, 11 failures and one error,
including companion/source mismatches and missing Node resolution; subsequent
4c4db99/eae0c73/dc06b46/a635302 background outputs intersected later hardening and
are diagnostics, not exact final qualification. Narrow probes included two wrong
unittest target names (loader errors); corrected probes passed. Static invocation
first used a wrong contract path and then a nonexistent `getModel` export; the
correct root contract and public `metaProvider().getModels()` were checked.
The first held 3955fc1 full gate had 641 tests/345.744s, exit 1, solely the bare
Docker cleanup FileNotFoundError described above; targeted 88, affected 72 and
Node passed. The final complete external fake rerun above supplies the missing
fake, with no source change. Initial commit author failure was resolved by
per-command author settings only, not global Git/environment changes.

### Fresh identities, precise supported-realization limit and return boundary

The current companion is 16 delivery files plus nine validation source hashes:
`sha256:77933b26a3fbd66f32d28020870199010f5edb2de2355853b30bb1dd3d4bac63`.
Guard remains `sha256:80e6dd151872c99ff5363894920ae0790420a9598a613cd6bd259aa653682fde`.
Changed host validation source hashes remain mandatory even where a payload-only
companion digest is unchanged between hardening commits. Fresh later artifacts
are required; neither old OCI nor old companion declarations were deemed eligible.
Positive fixture success remains `real_validation_satisfied=false`; nominal real
branches under complete external fakes prove structure only, never real evidence.

Read-only official-source metadata recheck: Pi 0.87.1; Paseo client/protocol/server
0.9.2; `meta/muse-spark-1.3-contributor` has `thinkingLevelMap.max=null`, supported
levels minimal/low/medium/high/xhigh, and unmodified max clamp returns xhigh.
Public source SHA256s: pi-ai `providers/meta.js`
`f0ba7b97a407336f30cfb230c4c32bece9e0fd23b0ebdbdae11503374e5ab44c`;
pi-ai `models.js` `75fa33149fb608bc4a7b7a0586c8ca8f0024465d580091b0c426c0baf3fbc80a`;
Paseo protocol `messages.js`
`3f854defd7fc5472bd0fbead7fde0d97c127d91758545e7ac862f7edab138d20`.
`tests/fixtures/m07_t05_catalog_{daemon,pi_rpc}.mjs` and
`m07_t05_transport_qualification.mjs` exercise the actual public mapping,
selected-process clamp and transport mechanics. Synthetic max demonstrates
mechanics only. Supported real fixed-max realization has NOT been established;
these negative facts authorize no override, fallback, silent mapping, substitute
model/provider/thinking, unofficial capability adoption or waiver of remediable
work. Main must classify this precise proportional Research/Planning boundary;
this is not a whole-Card impossibility claim and no real smoke was attempted.

Fresh default workflow remains `d3ab917f02e4de91b7dbb17915c2287c2387333e`;
package-module router still selects Execution/M07-T05 under `workflow/EXECUTION.md`.
Board119 all 22 DONE result bindings remain exact; exact M07-T04 result blob
`c45b3f707b1246e195c9138d027cbb1b05b9b112` and independent review evidence blob
`dffad8bf2a2e872375c11fbccc74ce53362e6a0d` were refreshed. M07-T05 stays
in_progress without result/Review; M08-T01 stays planned. Stable Card blob
`658fffe1d9d547a1a1525194628cdc2414ccc524` and root contract blob
`54f9ccc3515bf0f8af527fec4ba8871868750c6b` remain unchanged. The prior report's
87,643-byte prefix at d132d995 is retained. Main alone now reconciles this full
technical contribution and continues canonical routing to a real stop.
