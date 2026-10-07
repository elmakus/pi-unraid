# M07-T07 ev2 correction (worker, appends f5d9b5c, no DONE)

Date: 2026-10-07. Base f5d9b5c preserved. No source changes (validation
binding fd12d2bb intact, no rebuild). Fake rehearsal inputs only, no real
inference/auth/production effects. No Board/result/review/Research writes.

## (1) Generic structural/source readback — exact boundary, setup corrected
- Shipped source `scripts/paseo_tower_validator.py:1686`: generic
  `candidate structural/source readback unavailable` comes from
  `except (OSError, TypeError, AttributeError, KeyError, IndexError)` which
  discards the exception message. PASS-count/`real:false` was NOT used as waiver.
- True capture via /tmp settrace driver (shipped validator run IN PLACE,
  no repo modification, no copies, ROOT-relative loads intact; m07-t07-ev2/
  exc1243-companionbundle-none-traceback.txt, full feed 1339 exceptions):
  `EXC #1243 AttributeError: 'NoneType' object has no attribute 'get'` at
  `validate:1154` (`companion_bundle.get('validation_sources', {})`) —
  the full-wired invocation omitted `--companion-bundle`, leaving it None.
  Exact disposable-setup omission, not a product defect.
- Diag-copy attempts (patched /tmp copies) are HONESTLY CLASSIFIED as layout
  artifacts, not results: resolver `ROOT=parents[1]` + frozen inventory
  `config/environment-capabilities.json` are location-sensitive by design
  (ModuleNotFoundError / missing-inventory failures proved the copies could
  not reproduce the boundary). Repo untouched throughout (binding unchanged).
- Correction: re-ran with `--companion-bundle` extracted from the frozen
  tested evidence (tested-image-evidence.json → companion-bundle.json, source
  67e15435). Result: exact reasons everywhere, no masking (see 2).

## (2) Complete wired rehearsal — 18/19 PASS, one exact FAIL with mechanism
- 5 identical deterministic runs (complete/retry/watch/watch2/watch3,
  exit 2): status FAIL, reason `applied companion interval changed or
  unavailable`, real:false, cleanup COMPLETE. Full JSON retained
  (m07-t07-ev2/validator-complete-18pass-applied-fail.json, secret-safe).
  PASS: registry_digest/image_mapping/image_config/frozen_chain/
  companion_binding(67e15435,19)/policy_binding/mount/network/runtime/
  secret/uid_gid/daemon_binding/pi_binding/muse_guard_readback/
  muse_policy_readback/muse_effective_config/muse_effective_readback.
  Codex stage never reached (fails before); no codex_* keys recorded.
- Underlying cause (targeted tracer, shipped code in place;
  m07-t07-ev2/applied-cause-targeted-capture.log): pinned in-container
  client `observe()` → `ValueError: applied interval changed`
  (returncode 1) — the kernel-backed interval (inotify + snapshot over
  staged /home/paseo/.pi/agent, direct watches on manifest +
  /home/paseo/.paseo/config.json) reports bound False at the post-daemon
  check (validator line 1509). Timeline from source + passing checks:
  1353 check PASS → 1480 check PASS → 1489 owned `paseo daemon start`
  → 1501 pi observe → 1509 check FAIL. Preflight (1552) excluded (after).
- Writer proof (bisects with mirrored validator staging, shipped adapter
  import only, disposable containers, no source change):
  - Pi observe (`command -v pi`, `pi --version` 1.0.4, `sha256sum`,
    99:100, staged home mounted): 21 files, zero adds/removes/changes
    → PI_CLEAN, exonerated.
  - Daemon replication outside validator context fails to start
    (DAEMON_START_FAILED, needs validator network/secret context) →
    reduced-harness daemon bisect inconclusive (documented, not claimed).
  - Host-side 0.5s mtime watch over the validator's OWN state tree during
    a full run (m07-t07-ev2/watch-mtime-staged-tree.log): staged agent
    tree/manifest/config.json mtimes STABLE — no content writes anywhere
    watched; meanwhile the owned paseo 0.11.0 daemon wrote paseo.pid,
    daemon.log, server-id, daemon-keypair.json, runtime/opencode/*.mjs,
    schedules, local-credential, cli-client-id, models/local-speech
    downloads+extracts (kokoro/sherpa, still extracting at run end).
  - Host-side ctime/mode watch (m07-t07-ev2/watch-ctime-config-chmod.log):
    `/home/.paseo/config.json` ctime bumped TWICE (mode constant 600,
    mtime unchanged) AFTER daemon bring-up and BEFORE the failing check
    — metadata-only mutation (same-mode chmod/chown) by the running
    daemon. This trips BOTH the IN_ATTRIB event on the direct config
    watch (any event on non-parent wd trips) AND the ctime-identity
    comparison in inputs(). Timeline matches exactly
    (bumps precede 1509; 1353/1480 predate bumps → passed).
- Classification (honest limits): NOT setup (all 6 evidence inputs wired;
  daemon must use the staged home; watch paths fixed by design), NOT
  validator-logic defect (machinery proven: 1480-PASS in-run + local
  M07-T05 tests; the check correctly caught a real metadata mutation —
  chmod trips the documented mask), NO inference anywhere (fake URL/model;
  codex stage unreached; _assert_no_inference intact). The :ro agent
  submount rules out agent-tree writes (EROFs would fail loudly); the
  trip is the daemon's own config metadata normalization.
- Consequence: the SAME daemon binary normalizes the SAME staged config
  in real mode (bring-up path identical; rehearsal bring-up succeeded),
  so real mode would trip identically — `real_validation_satisfied`
  cannot become true for the frozen fd12d2bb validator + paseo-0.11.0
  candidate pair. Satisfying it needs a Card-level decision: (i) validator
  source change (ignore ctime/ATTRIB → binding change → freeze, reconcile,
  authorized rebuild + re-bootstrap; NOT done here, would weaken a
  security check), or (ii) candidate-side change (not ours). No automatic
  rebuild; binding intact.

## (3) State/promotion/Update+Verify with actual commands + complete outputs
- Full Tower command log retained
  (m07-t07-ev2/tower-ev2-commands.log): clone f5d9b5c, evidence staging,
  secret fixture (fake, 0600 99:100), validator runs, settrace/diag runs,
  state roundtrip, promotion, guards, probes, transitions, cleanup.
- State roundtrip (shipped `paseo_state_roundtrip.prove`, new candidate):
  4/4 PASS (baseline_clone_isolated/candidate_state_mutation/
  direct_skip_path/previous_runtime_reopen), candidate aa4c522e vs
  previous 05e140da (m07-t07-ev2/state-roundtrip-new.json).
- Promotion (ACTUAL candidate bytes, disposable localhost:5500):
  push digest `sha256:aa7425c8…` == GHCR immutable digest (content match),
  promoted image `aa4c522e` == expected; registry removed; GHCR
  :accepted untouched (production exclusion absolute).
- Update+Verify (disposable anchor+guards, binding f0d4c5b5,
  candidate aa7425c8/previous 05e140da/config ebc1b352):
  probes on aa4c522e (exact-digest/health 1.0.4/mounts 99/invariants) PASS;
  GREEN armed→observed→validating→committed; post-GREEN committed
  restore_calls=0; RED with ACTUAL disposable predecessor run
  (05e140da health/mounts/invariants executed, not image-inspect)
  → rolling-back→recovered. RPC direct without smoke harness exit-0-empty
  classified NOT-APPLICABLE (exact-bytes plane proven by CI PR25
  instruction_plane GREEN + validator runtime PASS).
- Cleanup: all Tower disposables removed (clones/states/outputs/guards/
  secrets/networks/registries/drivers/watchers); production
  pi-unraid-paseo-1 05e140da running; :accepted absent.

## (4) Suites — concrete attribution + durable positives
- `50131ab^{tree} == 8144bda^{tree}` (7809c254…, byte-identical ALL
  tracked files; allowance revert restored the exact tree) + 50131ab full
  `737 OK` (651s, exit 0; m07-t07-ev2/full-suite-50131ab-positive-737OK.log
  with direct exit) ⇒ the 8144bda single
  `test_every_declared_member_byte_drift_after_catalog
  (member extensions/m07-t05-witness.js, observed['mutated']=False —
  mutation hook never fired)` is definitively run-conditions, not source.
- Focused controls at f5d9b5c (identical test inputs), isolated HOME,
  direct exits, durable logs: single test alone 1/1 OK (55.6s)
  (witness-single-1pass.log); module 11/11 OK (145.5s)
  (witness-module-11pass-rerun.log). No full-suite reflex, no duplicates.
- bd9c03d 23+4 = mid-run-commit contamination (provenance in
  M07-T07-fresh-2026-10-07.md); /tmp-location 1 = harness artifact.
  No assertions/bindings/watchers weakened.

## (5) Locators (full, Git-accessible)
- Candidate f5f52337…/digest aa7425c8…/image aa4c522e…/companion 67e15435/
  validator fd12d2bb…/PR25 run 37684609105 success/tested 11510403897/
  published 11509864607/feat f5d9b5c/cleanup 8144bda/allowance 90e68b3/
  bootstrap 71f17d6/old b1dde889 superseded (preserved, unused).
- Evidence: M07-T07-fresh-2026-10-07.md + m07-t07-fresh/ (this correction)
  + m07-t07-ev2/ (boundary proofs); ccb16a3/bd9c03d preserved.
- Main reconciles final Card classification; open Card-level decision in
  (2) is returned, not taken.
