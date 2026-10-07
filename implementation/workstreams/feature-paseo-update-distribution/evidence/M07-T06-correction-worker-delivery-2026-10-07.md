# M07-T06 correction worker delivery evidence (bounded, synthetic/local only)

- Date: 2026-10-07 (separate correction evidence; R01, Main RED classification and all
  prior evidence/result/review history preserved untouched)
- Card: M07-T06 (in_progress); Main RED classification
  `evidence/M07-T06-main-red-classification-2026-10-07.md` (`ade440d`) routes bounded correction
  to Execution under unchanged P4/R2/Card — implemented here, no amendment/replanning/new Card.
- Branch/worktree: `feat/paseo-update-distribution` @ `/worktrees/pi-unraid-paseo-update-distribution`
- Correction implementation: `5c28170c762e8a6fef500f3e941621f478a1c390`
  (renders R01 §§3.2–3.4; prior `767977f` corrected within the same turn before any evidence claim)
- Frozen R01 reviewed subject `8bff080` / failed result `ff3e3fd` / R01 `7aa9b8c` read as failed
  history only; no rewrites of verdicts, DONE results, authority, Card, Board, Research, manifest or plan.
- DONE dependencies reread unchanged (M05-T01/M05-T03/M06-T01/M06-T02/M06-T03/M07-T05/M07-T05A,
  M07-T05 + M07-T05A R01 GREEN); companion 19 files
  `sha256:67e1543572b6b471da6525899766711812c281a3e40327b003e52ba289ba7199`; guard bytes unchanged.
- Provenance: M07-T05A R01 covered 74 independent tests (29+11+4+1+28+1), direct exit 0, zero skips;
  "99" was the producer isolated-local cohort; 652-discovery was not rerun by R01 by design. No Tower
  full-suite attribution is claimed.

## What R01 blocked and what changed (locations)

- (§3.2) FIXED constants were defined but never enforced; effective presence-only; daemon/Pi/Codex
  PASS-only; arbitrary PASS-shaped fixtures assembled. Fix: `scripts/paseo_final_gate.py`
  `validate_validator_record` now references `FIXED_PROVIDER/MODEL/THINKING` at its call site and
  value-enforces fragment (`sha256`+`0644`) / effective (`sha256`+`0600`+`bytes>0`+`models.json`) /
  readback (`sha256`+`0600`, digest-equals-staged), preflight + observed + on-wire-effort triples,
  owned-child thinking+id, daemon loopback endpoint (IP-literal/`localhost`/wildcard;
  `127.attacker.invalid` rejected without DNS), exact candidate home, positive pid/worker-pid,
  version==frozen Paseo, server-id, absolute node, Pi exact `/usr/local/bin/pi` path,
  version==frozen Pi, digest, plus a recursive `fallback_allowed` truthy scan. Codex trust stays
  checks-PASS by contract design (response bodies never persisted); acquisition authenticity comes
  from the shipped integration boundary below, proven by end-to-end tests.
- (§3.3) `baseline_digest==previous_local` conflation removed. `assemble` takes a typed `predecessor`
  (`oci`/`local`/`legacy` via the shipped legacy authority + repository check); divergent OCI vs
  local values pass, equality rejected; legacy anchors genuinely verified from real bytes; gate
  schema v2 stores `predecessor` + `baseline_oci` + `baseline_local_image_id` distinctly. Writer
  (`validate_trusted_final_gate`/`validate_production_gate`/`promote`/`promote_first_channel`)
  resolves running per kind with mapping↔gate kind/value/repository cross-checks; first-channel
  requires the typed mapping. Ledger slots are typed (`oci` with optional repository / `local` /
  `legacy` with archive/config/state digests) with coherent legacy-string migration; rotation stays
  terminal-only. Update+Verify observes typed running identity (OCI single-RepoDigest preserved;
  local/legacy via image-ID + relabel/mismatch rejection + genuine legacy anchor/import verification).
- (§3.4) New shipped provenance boundary `paseo_final_gate.assemble_from_acquisition`: invokes shipped
  `paseo_tower_validator.validate(real)`, shipped `paseo_state_roundtrip.prove`, shipped guard readback
  itself; recomputes companion/policy/launcher from `source_root` bytes (caller bundle must equal
  recomputation); reads source head from genuine chain bytes; binds live guard digest. Only the typed
  predecessor, ledger-owned local observation and file/secret locators arrive from caller layers.
  Writer `promote_first_channel`/`promote` consume genuinely assembled gates (registry transport +
  Tower domain faked in tests). No production caller existed to rewire (M08 owns production); the
  boundary is shipped code exercised by tests, not test-side sequencing.

## Tests (direct exits, honest skips, fake-only external transports)

- New `tests/test_m07_t06_trusted_gate` → **46/46 GREEN, direct exit 0, zero skips**, incl.:
  `GenuineTrustTests` (5) through `assemble_from_acquisition` (divergent OCI namespaces, local
  predecessor, OCI existing-channel production update with Tower-domain fakes + digest readback,
  legacy first-create with typed-ledger rotation + no legacy publish, production accepted lock/readback);
  `ForgeryTests` (17: empty/hacked/substituted/clamped/null/fallback/provider forgeries, evil daemon
  endpoints ×4, wrong home+Pi path, version mismatch, 6 missing blocks, fixture class, wrong digest,
  stale source/bundle/config ×4, wrong guard binding, 2 chain-tamper rejections by the genuine
  producer) every case asserting rejection AND `assert_not_called` registry/trigger effects;
  `TypedPredecessorTests` (4: conflation, ambiguity/invalid ×6, real-byte archive mismatch, mapping
  shapes/anchor/relabel); mechanics preserved (absence, races, channel-vs-running, intent, crash-safe
  trigger/uncertain/missing-container/third-identity/RED/post-GREEN/stale-binding, legacy restore
  with exact typed value, RepoDigest + local/legacy observation, lock contention).
- Affected: promotion/guard/ledger/acceptance/dockerman/update-verify/state/companion/instruction-plane
  → **74/74 GREEN, direct exit 0, zero skips** (pre-existing 11 promotion tests pass unmodified).
  Node catalog core → **1/1 pass, 0 fail, 0 skipped**. `py_compile` + `git diff --check` GREEN.
- Test-scope bytecode isolation (R01 normative shape) is pinned at the new test module import
  (`PYTHONDONTWRITEBYTECODE=1` + disposable `PYTHONPYCACHEPREFIX`, restored afterwards); product code
  and the kernel watch are untouched. This is documented isolation, not an assertion relaxation:
  every assertion still executes; the watch still trips on any other staged-tree writer.
- **Authoritative full classified synthetic discovery** (one run on frozen `5c28170`, isolated R01 env,
  output redirected to file, `DIRECT_EXIT:$?` with no pipe): **`Ran 731 tests in 653.584s`, `OK`,
  `DIRECT_EXIT:0`, zero `FAIL`/`ERROR` lines, zero skips**. Complete terminal output committed as
  `evidence/M07-T06-correction-discovery-final-2026-10-07.log` (14,985 bytes). Includes the 46 new
  tests and all validation/delivery/build matrix cohorts. An earlier same-name run on superseded
  `767977f` (job 4, also `DIRECT_EXIT:0`) is recorded here as a superseded diagnostic only — its
  output file was removed to prevent confusion; it never qualifies `5c28170`. Zero residuals, so no
  clean-base residual comparison was required (pre-existence of the since-resolved ambient harness
  artifact on `cdf0ed4` was proven separately during diagnosis and is not re-litigated here).

## Exact ambient-harness root cause (closed; owned elsewhere, not implemented here)

- Chain (each step observed in disposable `/tmp` diagnostics, repo files untouched): preflight catalog
  stdout `'undefined'` ← daemon `{id,error:true}` ← logged `synthetic Pi closed` ← Pi exit 42 ←
  `ValueError('applied interval changed')` ← interval readback `bound=False`.
- Writer proven sufficient by controlled pair: first staged-python exec writes
  `__pycache__` into the watched tree post-interval-start → trip (exit 42 + pycache appears);
  with `PYTHONDONTWRITEBYTECODE=1` → exit 0 + exact catalog JSON, no pycache.
- Decisive locus: the harness staged-Codex-check subprocess inherits ambient test env without the
  flag and directly imports a staged sibling (`via direct import`), writing bytecode into the watched
  tree after interval start (codex checks run before muse preflight per failing-record check ordering).
  Ambient flip experiments: `PYTHONPYCACHEPREFIX`-only → OK; exported flag-only → OK; `-B`-only/HOME-only
  → still FAIL. Standalone fixture flow succeeds (no validator staging + own env). Identical failures on
  clean `cdf0ed4` and subject; M07-T06 diff touches none of validator/harness/bridge/fixture/adapter files.
- Minimum fix scope (**for the owning harness lineage — NOT implemented here**): bytecode-guarded env
  for harness-spawned staged-python subprocesses (or precompile/mask in watch rows) with affected-gate
  re-evidence; no product/watch weakening, no DONE verdict changes. The watch behaved correctly
  throughout (fail-closed on a genuine post-start mutation). M07-T06 requires no change; corrected-env
  full green (731 OK) was obtained without touching this Card's subject. Bytecode safety remains a
  separate concern; this correction does not weaken the watcher.

## Secret/live-effect scans (bounded)

- New/changed code, new tests, rewritten evidence and the committed discovery log scanned: only
  digest-shaped synthetic strings, harness fixture-secret *names* in pre-existing patterns, and
  allowlist regex definitions. Discovery-log secret-pattern grep: zero hits. No credential values,
  ordinary HOME/auth reads, token argv, raw secret env, or provider echo.
- No real inference/auth, credential admission, installed HOME/catalog/runtime/host mutation, live
  Docker/Tower/registry/Unraid operations, CI/build/publication/push/PR/Issue, actual accepted-channel
  writes, production guard arm, update triggers, M07-T07/M08/M09 scope, or further delegation. Disposable
  temp dirs/locks/homes/caches only; external transports mocked; diagnostics confined to `/tmp` (removed).

## Limitations (for Main reconciliation + fresh independent R02)

- All positives are synthetic/local through faked transports; no final real gate, actual channel exposure,
  production arm/update, or eligibility is claimed (M08 owns real validation/production).
- R02 must be performed by a fresh independent context (this context materially produced the corrected
  subject); R02 assesses the full corrected subject (`5c28170` + this evidence), not the failed attempt.
- Worker makes no result/Board/Review/Research/manifest finalization; Main binds the corrected result
  and appends R02.
