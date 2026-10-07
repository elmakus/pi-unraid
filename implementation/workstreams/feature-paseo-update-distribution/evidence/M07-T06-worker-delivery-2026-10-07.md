# M07-T06 worker delivery evidence (bounded, synthetic/local only) — CORRECTED

- Date: 2026-10-07 (corrects `fa28fba`; supersedes its counts/provenance where they differ)
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
- Companion refreshed (not retained as eligibility): 19 files
  `sha256:67e1543572b6b471da6525899766711812c281a3e40327b003e52ba289ba7199`; guard bytes unchanged.
- Provenance correction (durable R01 record): M07-T05A independent Review covered
  **29+11+4+1+28+1 = 74 tests** (direct exit 0, zero skips); the "99" cohort was the producer's
  isolated-local prior run (`M07-T05A-main-return-classification`); full discovery (652) was explicitly
  **not rerun by R01 by design**. No Tower full-suite attribution is claimed here.

## Implementation subject (`8bff080`, 7 files, +1827/−19)

- New `scripts/paseo_final_gate.py` (trusted assembler): real validator record (schema 2, `real`
  execution, terminal PASS, satisfied real validation, 20 producer + 6 source/isolation checks PASS
  incl. effective-max bindings, distinct OCI/local, COMPLETE cleanup), state A→C→A PASS with
  baseline==previous binding, exact source/companion/policy/launcher/guard bindings; rejects
  fixture-as-real, generic PASS maps, wrong-digest reports, stale baselines.
- Extended `scripts/paseo_accepted_promotion.py`: verified HTTP-404-only absence (401/403/network/timeout
  never absence), `promote_first_channel` under one lock (absence → race recheck → create → OCI readback),
  strict gates + armed guard before create/update, channel observation distinct from running predecessor,
  Tower single-writer domain preserved (guard-before-domain-before-gates keeps both classifications).
- New `scripts/paseo_legacy_identity.py`: typed `oci`/`local`/`legacy`; legacy = verified local image-ID +
  independently recoverable archive/config/state anchor; never relabels image-ID as manifest digest.
- Extended `scripts/paseo_known_good.py`: terminal-only rotation + typed migration (never on RED/UNKNOWN/BLOCKED).
- New `scripts/paseo_trigger_intent.py` + extended `scripts/paseo_dockerman_binding.py`: guard-local narrow
  intent (no universal ledger); absent intent = safe to trigger, present = observe-only; trigger exceptions
  become uncertain-observe (never blind reissue); terminal states short-circuit retrigger. Missing-container
  transient, third-digest fail-closed, RED exact-restore, post-GREEN denial via unchanged state machine.
- New tests: `tests/test_m07_t06_trusted_gate.py` (33 tests, genuine entrypoints, fake-only transports,
  disposable temp state).

## Tests (direct exits, honest skips, fake boundaries only)

- New targeted `tests.test_m07_t06_trusted_gate` → **33/33 GREEN, exit 0, zero skips** (absent-channel
  positive+readback; 404 vs 401/403/network/timeout/ambiguous; create/update races; gates+guard-before-write
  with `assert_not_called`; channel-vs-running split; Tower lock/readback on faked root/host; typed legacy
  incl. no-publish first-create; ledger rotation/retention/typed migration; intent lifecycle; interruption
  before/after trigger; uncertain-observe; missing-container; third-identity; RED restore; post-GREEN denial;
  single-RepoDigest; lock contention).
- Affected validation/delivery/build-adjacent cohorts: promotion 11 + guard 4 + ledger 3 + acceptance 8 +
  dockerman 8 + update-verify 4 + state-roundtrip 4 → **42/42 GREEN**; combined focused+affected **75/75**;
  companion 21/21 GREEN; Node catalog core GREEN. All pre-existing tests unmodified. `py_compile` GREEN;
  `git diff --check` GREEN.
- **Corrected full classified synthetic discovery** (one run, all old jobs terminal, no duplicate): isolated
  R01-shape env (`env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/pud-m07t06-disc TMPDIR=/tmp
  PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/pud-m07t06-pycache python3 -B -m unittest discover -s
  tests -p "test_*.py"`, full stdout/stderr redirected to file, `DIRECT_EXIT:$?` captured with **no pipe**)
  → **`Ran 714 tests in 565.482s`, `OK`, `DIRECT_EXIT:0`, zero `FAIL`/`ERROR` lines, zero skips**.
  Complete terminal output committed as `evidence/M07-T06-discovery-2026-10-07.log` (14,966 bytes).
  This run includes the 33 new M07-T06 tests and all validation/delivery/build matrix cohorts.
- Earlier non-isolated full run (job 1, `| tail` carrier — exit masked, lesson per R01 repair §73) showed
  714 ran / 27 failed with only tail preserved; those 27 are classified below as an ambient bytecode-write
  artifact, absent under the corrected isolated env. No failure is hidden in M07-T06 scope (targeted 75 prove it).

## Exact root cause of the 27 (disposable diagnostics, no repo changes, no secrets)

- Chain (each step observed, not inferred): preflight catalog stdout `'undefined\n'` ← daemon replies
  `{id,error:true}` ← daemon logged `{"method":"catalog","message":"synthetic Pi closed"}` (patched
  **disposable copy** of the fixture; repo file untouched) ← Pi child exit `{"code":42}` ← Python bridge
  `sys.exit(42)` ← `ValueError('applied interval changed')` ← socket readback `bound=False`.
- Trigger (proven by controlled pair on disposable fixture copies): first bridge exec writes
  `bin/__pycache__/m07-t05-applied.cpython-311.pyc` into the staged tree **after** interval start →
  inotify CREATE → `bound=False` (P1: exit 42 + pycache appears). With `PYTHONDONTWRITEBYTECODE=1`
  (P2a): returncode 0, exact catalog `[{id:meta/muse-spark-1.3-contributor,thinkingOptionIds:[max]}]`,
  no pycache. The validator's direct candidate execs carry the flag, but the daemon-spawned Pi evidently
  runs without it on this host, so its first bridge exec poisons the watch it must then satisfy.
- Experimental confirmation: the corrected discovery adds isolated `PYTHONPYCACHEPREFIX` (plus `env -i`,
  disposable HOME, `python3 -B`) → all 27 pass unmodified. The defect is ambient bytecode-write behavior
  interacting with the kernel-backed watch, not M07-T06 (or any product) logic.
- Base-vs-subject (same non-isolated env): 2/2 exemplar FAIL with byte-identical cause on clean `cdf0ed4`
  (disposable detached `/tmp/pud-base-clean`, removed) and on `8bff080`. File-level non-causation: the
  M07-T06 diff touches none of validator/harness/bridge/fixture/adapter files (promotion, dockerman-binding,
  known-good + 3 new consumer-side modules + 1 new test file only). Tower GREEN history is consistent
  (watch-timing outcome varies by host/fs scheduling; cf. R01 load-sensitivity notes).
- Minimum proposed fix scope (**for the owning lineage — NOT implemented here**): propagate the bytecode
  guard (or precompile staged bytecode before interval start, or mask `__pycache__` in watch rows) in the
  validator/harness/bridge lineage with affected-gate re-evidence; no DONE verdict changes (diagnosis only).
  M07-T06 requires no change: its gates never traverse that path, and the corrected env proves the full
  suite green without touching this Card's subject. If Main/Planning wants the hardening, that is a separate
  bounded repair Card, not a silent in-scope edit.

## Secret/live-effect scans (bounded)

- Changed-file + evidence-log scans: only digest-shaped synthetic strings and allowlist regex definitions;
  no credential values, ordinary HOME/auth reads, token argv, raw secret env, or provider echo in new/changed
  code, tests, or evidence (log holds synthetic digests + harness output only).
- No real inference/auth, credential admission, installed HOME/catalog/runtime/host mutation, live
  Docker/Tower/registry/Unraid operations, CI/build/publication/push/PR/Issue, actual accepted-channel
  writes, production guard arm, update triggers, M07-T07/M08/M09 scope, or further delegation. Disposable
  temp dirs/locks/homes only; all external transports mocked; diagnostics confined to `/tmp` (removed).

## Limitations (for Main reconciliation + fresh independent Review)

- All positives are synthetic/local through faked transports; no final real gate, actual channel exposure,
  production arm/update, or eligibility is claimed (M08 owns real validation/production).
- Worker makes no result/Board/Review/Research/manifest finalization; Main reconciles acceptance and starts
  a fresh independent reviewer (this context materially produced the subject).
