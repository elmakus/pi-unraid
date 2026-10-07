# M07-T06 second correction worker delivery evidence (bounded, synthetic/local only)

- Date: 2026-10-07 (separate correction evidence; R01, Main RED classification
  `e1b7d25`, failed results and ALL prior evidence/result/review history preserved
  untouched, including the 731-OK log as historical `5c28170` evidence only)
- Card: M07-T06 (in_progress); Main correction-return classification routes this
  bounded correction to Execution under unchanged P4/R2/Card — implemented here,
  no amendment/replanning/new Card, no R02 yet.
- Branch/worktree: `feat/paseo-update-distribution` @
  `/worktrees/pi-unraid-paseo-update-distribution`
- Correction implementation (frozen BEFORE qualifying discovery):
  `ef8ab224c33a64e384dd8644ad75e5fd71f620f0`
  (+530/−57, 3 files; worktree clean at freeze; zero tree edits during discovery)
- DONE dependencies reread unchanged (M05-T01/M05-T03/M06-T01/M06-T02/M06-T03/
  M07-T05/M07-T05A, M07-T05 + M07-T05A R01 GREEN); companion 19 files
  `sha256:67e1543572b6b471da6525899766711812c281a3e40327b003e52ba289ba7199`;
  guard bytes unchanged. No extra secret store/ledger/writer added.

## Blocking defect → correction (locations)

Main source-readback finding: `assemble_from_acquisition` existed, but
`paseo_final_gate.main` still assembled from `--validator/--state` caller files
and `validate_trusted_final_gate` still accepted arbitrary fully populated
schema-2 dicts, so a detached caller could bypass acquisition; the writer's
explicit gate list also omitted the six source/isolation checks (present-key
iteration alone let omissions disappear).

- `scripts/paseo_accepted_promotion.py`
  - Production eligibility is conferred ONLY by in-process acquisition.
    `promote`/`promote_first_channel` on the `accepted` alias REFUSE any
    caller-supplied `final_gate` dict categorically (`DETACHED_GATE_ERROR`,
    before acquisition/registry access) and acquire the gate themselves via
    `_acquire_production_gate` (new `acquisition` locator-only bundle: file/
    secret paths + ledger-owned typed predecessor; NEVER caller gate/
    validator/state/producer objects — the writer lazily imports the shipped
    `paseo_final_gate.assemble_from_acquisition` owner itself). Guard/domain/
    mapping classification order preserved. No label/hash/flag on a detached
    record is read or trusted anywhere.
  - Explicit full required set `FULL_REQUIRED_GATES` (20 producer + 6
    source/isolation + 4 state); omission of ANY name fails closed. Verified
    30/30 IDENTICAL to the assembler's
    (`REQUIRED_VALIDATOR_CHECKS` + `REQUIRED_SOURCE_ISOLATION_CHECKS` +
    `state.`-prefixed `REQUIRED_STATE_CHECKS`).
  - `validate_trusted_final_gate` docstring states the trust boundary: value
    consistency only; direct calls confer nothing.
  - Promotion CLI: `--final-gate` rejected for `accepted` (diagnostic-only),
    `--acquisition` bundle required. Disposable aliases unchanged
    (diagnostics; confer no production eligibility).
- `scripts/paseo_final_gate.py`: detached CLI output labeled
  `acquisition: detached-caller-records` / `eligibility: diagnostic-only`
  (documentation only — enforcement is the writer's categorical refusal).
- `tests/test_m07_t06_trusted_gate.py` (52 tests): shared chain-setup +
  fake-transport context + JSON-serializable bundle builders; production
  positives converted to the acquiring entrypoint; new `DetachedBypassTests`
  (5) + `AcquisitionOwnedPromotionTests` (1).

## Tests (direct exits, honest skips, fake-only external transports)

- New/converted file `tests/test_m07_t06_trusted_gate` → **52/52 GREEN,
  direct exit 0, zero skips**, incl.:
  - Genuine owned positives: OCI update + OCI first-create + legacy
    first-create through `promote`/`promote_first_channel` with
    `acquisition=` bundles (Tower domain faked, registry mocked,
    acquisition transports faked); typed-ledger rotation + crash-safe
    intent assertions preserved.
  - `DetachedBypassTests`: perfect forgery (genuinely acquired gate rebound
    to an attacker candidate, 30/30 PASS incl. six, self-consistent values,
    live armed attacker guard, recomputed binding digest — the helper-level
    check ACCEPTS it, proving content checks are not the trust root)
    rejected `diagnostic-only` at promote, first-channel AND promotion CLI
    (exit 2, no output file), each with `assert_not_called` registry/
    trigger; genuine-valued detached-CLI record chain (CLI exit 0,
    `eligibility: diagnostic-only` → production promote refused); six-name
    omission matrix at the helper (each missing name fails with its name).
  - All preserved mechanics (absence/races/lock, channel-vs-running, intent,
    trigger uncertainty, legacy restore, observation, rollback denial).
- Affected: promotion/guard/ledger/acceptance/dockerman/update-verify/state
  51/51 (incl. rerun bypass class) + companion/instruction-plane 28/28 +
  pre-existing promotion 11 unmodified → all direct exit 0, zero skips.
  Node catalog core 1/1/0. `py_compile` + `git diff --check` GREEN.
- **Authoritative full classified synthetic discovery** (one run on frozen
  `ef8ab22`, isolated R01 env, output redirected to file, `DIRECT_EXIT:$?`
  with no pipe): **`Ran 737 tests in 653.167s`, `OK`, `DIRECT_EXIT:0`,
  zero `FAIL`/`ERROR` lines, zero skips** (737 = 731 historical + 6 new
  bypass/owned tests, consistent). Complete terminal output committed as
  `evidence/M07-T06-correction-discovery-owned2-2026-10-07.log`
  (17,651 bytes). Zero residuals, so no clean-base residual comparison was
  required. Discovery-log secret-pattern grep: zero hits.
- Bytecode isolation pinned at the new test module import (documented
  test-scope isolation; product watch/assertions untouched).

## Secret/live-effect scans (bounded)

- Changed code/tests/evidence/log scanned: synthetic digest-shaped strings,
  harness fixture-secret names and allowlist patterns only. No credential
  values, ordinary HOME/auth reads, token argv, raw secret env, provider echo.
- No real inference/auth, credential admission, installed HOME/catalog/
  runtime/host mutation, live Docker/Tower/registry/Unraid operations,
  CI/build/publication/push/PR/Issue, actual accepted-channel writes,
  production guard arm, update triggers, M07-T07/M08/M09 scope, or further
  delegation. Disposable temp dirs/locks/homes/caches only.

## Limitations (for Main reconciliation + fresh independent R02)

- Synthetic/local faked-transport evidence only; no final real gate, actual
  channel exposure, production arm/update, or eligibility is claimed
  (M08 owns real validation/production).
- R02 must be performed by a fresh independent context (this context
  materially produced the corrected subject); R02 assesses the full
  corrected subject (`ef8ab22` + this evidence), not the failed attempts.
- Worker makes no result/Board/Review/Research/manifest finalization; Main
  binds the corrected semantic result and appends R02.
