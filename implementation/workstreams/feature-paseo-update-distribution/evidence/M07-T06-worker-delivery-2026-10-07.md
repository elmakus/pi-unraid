# M07-T06 worker delivery evidence (bounded, synthetic/local only)

- Date: 2026-10-07
- Card: M07-T06 (in_progress, Board rev 128 at launch; JIT `after-M07-T05-materialize-M07-T06` consumed)
- Branch/worktree: `feat/paseo-update-distribution` @ `/worktrees/pi-unraid-paseo-update-distribution`
- Initial HEAD: `cdf0ed4`; implementation commit: `8bff08066083f43148b5e2bc0cfb1e02038d5588`
- DONE dependencies consumed (reread, unchanged, verdicts untouched):
  `M05-T01@56e80b3a:2a00b007`, `M05-T03@258a9c46:0a7e2133`, `M06-T01@bc0854f1:d6d77f96`,
  `M06-T02@d3f7b4c8:7b65d385`, `M06-T03@478152f7:71a3620c`, `M07-T05@f2496a17:7a21e90a` (R01 GREEN),
  `M07-T05A@87a1607:f52d818a` (R01 GREEN `170be5d`, finalized `3285e1c`).
- Authority reread: `requirements/PASEO_UPDATE_DISTRIBUTION.md` R2, `decisions/ADR_PUD_003_ROLLBACK_SAFE_PROMOTION.md`,
  `decisions/ADR_PUD_004_POLICY_COMPLIANT_VALIDATION.md`, `planning/PASEO_UPDATE_DISTRIBUTION_P4.md` P4 §M07-T06,
  `contracts/PASEO_R2_CANDIDATE_VALIDATION.md`, canonical `ROUTER.md` + `EXECUTION.md`/`EXECUTION_PREP.md`,
  exact Card `cards/M07-T06.md` (Main-owned Prep preserved; no strategy/order/product change).
- M07-T05A delivery input refreshed (not retained as eligibility): final companion 19 files
  `sha256:67e1543572b6b471da6525899766711812c281a3e40327b003e52ba289ba7199`; guard bytes unchanged.

## Implementation subject (`8bff080`, 7 files, +1827/−19)

- New `scripts/paseo_final_gate.py` (trusted Tower final-gate assembler): requires real validator record
  (schema 2, `execution_class=real`, terminal PASS, `real_validation_satisfied`, all 20 producer + 6
  source/isolation checks PASS incl. effective-max bindings, distinct OCI/local, COMPLETE cleanup),
  state A→C→A PASS with baseline==previous binding, and exact source/companion/policy/launcher/guard
  bindings; rejects fixture-as-real, generic PASS maps, wrong-digest reports, stale baselines.
- Extended `scripts/paseo_accepted_promotion.py`: verified HTTP-404-only absence
  (`classify_channel_status`/`verify_channel_absence`; 401/403/network/timeout never absence),
  `promote_first_channel` under one lock (absence → race recheck → create → OCI readback),
  strict trusted gates + armed guard before both create/update, channel observation distinct from
  running predecessor (`running_predecessor` + typed `predecessor_mapping`), Tower single-writer
  domain preserved (guard-before-domain-before-gates ordering keeps both negative classifications).
- New `scripts/paseo_legacy_identity.py`: typed `oci`/`local`/`legacy` mapping; legacy = verified local
  image-ID + independently recoverable archive/config/state anchor; import verification never relabels
  image-ID as manifest digest; no legacy publication.
- Extended `scripts/paseo_known_good.py`: `commit_on_terminal` (rotate only on GREEN/committed; never on
  RED/RECOVERED/UNKNOWN/BLOCKED/FAIL) + `migrate_with_predecessor` (typed binding to ledger current).
- New `scripts/paseo_trigger_intent.py` + extended `scripts/paseo_dockerman_binding.py`: guard-local narrow
  intent sibling (no universal ledger); pre-trigger intent readback — absent means safe to trigger,
  present means observe-only; trigger exceptions become uncertain-observe (never blind reissue);
  terminal committed/recovered short-circuits post-GREEN retrigger. Missing-container transient,
  third-digest fail-closed, RED exact-restore, post-GREEN rollback denial preserved via existing
  guard/acceptance state machine (unchanged semantics).
- New tests: `tests/test_m07_t06_trusted_gate.py` (33 tests, genuine product entrypoints, fake-only
  Docker/registry/trigger/probe boundaries, disposable temp state).

## Tests (direct exits, honest skips, fake boundaries only)

- New targeted: `python3 -m unittest tests.test_m07_t06_trusted_gate` → **33/33 GREEN, exit 0, zero skips**.
  Covers: assembler positive via actual entrypoint; fixture/rehearsal/missing/forged/failed/unknown
  gates; stale source/companion/policy/baseline; wrong guard candidate/binding; state gates; OCI/local
  distinctness; 404 absence vs 401/403/network/timeout/ambiguous; absent-channel positive with readback;
  first-create races; gates+guard-before-write proof (inspect/run assert_not_called); channel-vs-running
  separation; Tower lock/readback (faked root/hostname); typed legacy validate/anchor/import/relabel
  rejection; legacy first-create without publishing; ledger rotation/retention/never-on-uncertain/typed
  migration; intent record/readback/stale; interruption before/after trigger; trigger-exception
  uncertain-observe; missing-container convergence; third-identity fail-closed; RED restore; post-GREEN
  denial; single-RepoDigest; lock-contention single winner.
- Affected regressions (same worktree, no duplicate pending runs): promotion (11) + guard (4) + ledger (3)
  + immediate-acceptance (8) + dockerman (8) + update-verify (4) + state-roundtrip (4) → **42/42 GREEN**;
  combined focused+affected **75/75 GREEN, exit 0, zero skips**. All pre-existing tests unmodified.
- Companion: `tests.test_paseo_companion_bundle` → 21/21 GREEN. Node catalog core: GREEN (`node --check` +
  `codex-lb dynamic catalog core tests: GREEN`).
- `py_compile` GREEN (7 files); `git diff --check` GREEN.
- Full classified synthetic discovery (background job 1, consumed terminal, no duplicate):
  **714 ran, 27 failed, 398.885s** (log `/home/paseo/.pi/agent/specpi/background/398890-e7b4227b/job-1.log`,
  tail-preserved; only 2 FAIL headers + tail JSON survive truncation — limitation noted, no M07-T06-scope
  failure hidden: all 75 M07-T06-scope + 21 companion GREEN by targeted runs above).

## Pre-existing validator-catalog failures: exact base-vs-subject evidence (no repair in scope)

- Symptom (all sampled): validator result `status FAIL/UNKNOWN` with reason
  `candidate model catalog malformed` (preflight `paseo provider models` stdout unparsable).
- Subject (`8bff080`, this env): `test_m07_t05a…test_positive…` FAIL + `test_uncertainty…` FAIL (2/2).
- Clean base (`cdf0ed4`, disposable detached `/tmp/pud-base-clean`, removed after): same 2 tests FAIL
  with byte-identical cause (2/2, 4.673s). Base worktree created read-only for evidence, no branch/push
  mutation; removed immediately.
- TowerValidator genuine (subject, background job 2, terminal 2/2 FAIL 4.533s,
  log `…/job-2.log`): `test_positive_fixture_through_genuine_api` + `test_real_mode_structurally_succeeds_under_fakes`
  FAIL (`'FAIL' != 'PASS'`); job-1 tail preserves a fixture validator result JSON carrying the identical
  `"reason": "candidate model catalog malformed"`.
- Prior GREEN (durable, other env): M07-T05A R01 (29 new + 99 prior + 76 affected + Node1 GREEN on Tower),
  M07-T05 99-targeted GREEN. Same code GREEN on Tower, FAIL here on both base and subject → environment/fixture
  cause, not subject regression.
- Mechanism (proven by argv-shape debug, no product change): product wraps candidate execs with
  `env -i …` (`controlled_candidate_argv`); harness routes `argv[3:5]==['env','-i']` to `OwnedRuntimeFixture`;
  its Node daemon `catalog` handler threw (daemon replies `{id,error:true}`), CLI prints `row.value`
  (`undefined`), preflight `json.loads` fails → `AdapterError("candidate model catalog malformed")`.
  Exact throw site is swallowed by the daemon catch; Green-on-Tower vs Fail-here with identical inputs
  bounds it to fixture/environment (Node daemon path in this host), not M07-T06 inputs.
- Repair decision: **none within this Card**. The harness/fixture is owned by DONE M07-T05/M07-T05A
  (independent GREEN verdicts); this Card forbids rewriting DONE history/authority and owns only the
  consumer/writer/legacy/intent surfaces. No existing assertion was relaxed (all 11 promotion + 27 other
  affected tests pass unmodified); M07-T06 tests never traverse the owned-runtime daemon catalog path
  (synthetic producer-shaped records + direct mocks). Classified as precise unresolved environment
  evidence for Main/independent Review; M07-T06 acceptance does not depend on that path by design
  (real gates remain M08-T01).

## Secret/live-effect scans (bounded)

- Changed-file secret-pattern scan: only digest-shaped synthetic strings (`sha256:<hex>`, `ab*20` head),
  allowlist regex definitions in untouched sources, and synthetic fixture tokens in pre-existing tests;
  no real credential values, ordinary HOME/auth reads, token-bearing argv, raw `--env KEY=value`, or
  provider-output echo in new/changed code, tests, or this evidence.
- No real inference/auth, credential admission, installed HOME/catalog/runtime/host mutation, live
  Docker/Tower/registry/Unraid operations, CI/build/publication/push/PR/Issue, actual accepted-channel
  create/update, production guard arm, update trigger, M07-T07/M08/M09 scope, or further delegation.
  Disposable temp dirs/files/locks only; all external transports mocked.

## Limitations (for Main reconciliation + fresh independent Review)

- All positives are synthetic/local through faked transports; no final real gate, actual channel exposure,
  production arm/update, or eligibility is claimed (M08 owns real validation/production).
- Full-discovery 27 failures are pre-existing environment/fixture evidence (above), preserved not waived;
  REQUIRED Review must independently challenge full stable acceptance.
- Worker makes no result/Board/Review/Research/manifest finalization; Main reconciles acceptance and starts
  a fresh independent reviewer (worker materially produced this subject).
