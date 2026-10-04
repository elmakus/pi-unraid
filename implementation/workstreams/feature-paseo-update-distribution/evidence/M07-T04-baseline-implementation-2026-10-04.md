# M07-T04 — Baseline implementation (preserved target + reproducible R2 delivery)

Date: 2026-10-04 (corrected after Main return validations, two rounds)
Card: `M07-T04`
Initial contribution (retained in Git history): implementation `1991306705f894839529ff619bad4f2b0e6f2755`,
evidence `bae5214980f6f0ea21fe41fa07ce4a4096147370`.
First correction (retained): implementation `38d704ac78c40e88dbc4d81851d3bdad4b2337bf`,
evidence `9c3141601b3dc80ef37165f0c809b1b344bb98ac`.
Correction basis: Main return validation `0c0337379b51f9ac305b22bba80e169092b2fa8c`
plus `25d1ff9f3db340dfdafdc9743bfa354055acc34e` (§"Second contribution validation",
boundaries A/B/C) — stable contract valid, contributions incomplete, no semantic
result or review attempt exists.
Target observation (refreshed before correction): `main@e9476b4987290767a195a9de2ecd655de5f09605`
(unchanged). Merge-base: `fc7a470a7330839cbaf8eaf0c2914323981d6901`.
DONE dependency (verified unchanged): `implementation/workstreams/feature-paseo-update-distribution/results/M07-T03.md@c9d18c3f1c159684128221a6569496630d7fcbce:21dea73b5f663125cce8642486abc7cbffb506e3`
Authority: `requirements/PASEO_UPDATE_DISTRIBUTION.md` (R2), `requirements/PASEO_GUI_RUNTIME.md`,
`decisions/ADR_PUD_001_DISTRIBUTION_AND_CUTOVER.md`, `decisions/ADR_PUD_002_MANAGED_COMPONENT_LIFECYCLE.md`,
`decisions/ADR_PUD_004_POLICY_COMPLIANT_VALIDATION.md`, `planning/PASEO_UPDATE_DISTRIBUTION_P4.md`.
Technical contract: none (the reconciled `contracts/` document below is product
documentation, not a Card technical contract). Factual input:
`evidence/M07-T04-provider-delivery-research-2026-10-04.md` at `3f92235`.

Scope: substantive correction/testing only under the unchanged Card. No Card/plan authoring,
no gate satisfaction, no Task Board/manifest/result/review finalization, no second Card.
All selected-workstream authority/state/historical subjects preserved byte-for-byte
(no `implementation/workstreams/feature-paseo-update-distribution/cards/*`,
`TASK_BOARD.toml`, `WORKSTREAM.toml`, `results/*`, `reviews/*`, `PLANNING.toml`,
`PLAN_REVIEW.toml` modified). Board remains `in_progress` for Main reconciliation.

## 1. Target preservation (what was kept, what changed)

Accepted target repairs reconciled into the legal source workstream without regressing
the update system and without touching unrelated target-side recovery packages
(`feature-codex-lb-dynamic-model-catalog`, `issue-paseo-codex-lb-env-propagation`,
`issue-codex-lb-current-main-gpt6-image` workstream packages left untouched on `main`;
none copied as competing authority). `.github/workflows` triggers untouched.

Imported verbatim from `origin/main` (`e9476b4`, `cmp` VERBATIM for new files,
`git diff origin/main -- <file>` MATCH for tracked mechanical files):

- `scripts/paseo-codex-lb-entrypoint.sh` (0755) — dedicated Codex-LB secret prelude,
  upstream entrypoint preserved under `/usr/local/libexec/pi-unraid/`.
- `scripts/reconcile-codex-lb-auth-shadow.py` (0755), `scripts/reconcile-codex-lb-provider-config.py` (0755).
- `config/pi-agent/extensions/codex-lb-dynamic-model-catalog.ts`,
  `config/pi-agent/extensions/lib/codex-lb-dynamic-model-catalog-core.mjs`.
- `Dockerfile` prelude (`COPY` + upstream move + symlink, no `ENTRYPOINT` override).
- `compose.yaml` dedicated secret (`source: codex_lb_client`, `target: pi-unraid-codex-lb`,
  `PI_CODEX_LB_SECRET_FILE`, `host.docker.internal:host-gateway`, file-backed `secrets:` block).
- `scripts/pi_instruction_plane.py` executable `managed_mode` (`bin/` → `0755`, else `0644`),
  mode-aware digest/readback/apply.
- `docs/PI_INSTRUCTION_PLANE.md` managed-executable-tools section.
- `scripts/verify-compose-foundation.sh` (4 mounts incl. secret).
- `scripts/paseo_relay_doctor_readiness.py`, `scripts/paseo_rpc_workspace_flow.py`
  (dedicated-secret allowance; generic secrets still rejected).
- Contract tests updated to the accepted target shape (verbatim):
  `tests/test_paseo_child_image_contract.py`, `tests/test_paseo_runtime_contract.py`,
  `tests/test_paseo_relay_doctor_readiness_contract.py`,
  `tests/test_paseo_rpc_workspace_contract.py`,
  `tests/test_pi_instruction_plane_contract.py`,
  plus new synthetic contracts `tests/test_paseo_codex_lb_entrypoint_contract.py`,
  `tests/test_codex_lb_auth_shadow_contract.py`,
  `tests/test_codex_lb_dynamic_model_catalog_contract.py`,
  `tests/codex_lb_dynamic_model_catalog_core_test.mjs`.

Reconciled (not verbatim) product contract/documentation:

- `contracts/PASEO_CODEX_LB_RUNTIME_ENV.md` — secret propagation, upstream entrypoint
  ownership and verified dynamic capability metadata preserved from the accepted target
  repair; ONLY the superseded real-test profile provisions replaced by the R2 fixed
  profile (`meta/muse-spark-1.3-contributor`/`max`, no fallback, Astra forbidden) with
  pointers to R2/ADR-PUD-004/P4. Rollout wording R2/P4-aligned: final real validation
  is a required gate before any accepted-channel exposure (never "if performed");
  exposure follows validation-GREEN → guard arm/readback → channel write/readback →
  user-triggered Update + Verify with bounded immediate acceptance/recovery; immediate
  GREEN ends automatic rollback authority (later unrelated faults must not restore).
  Real-model-call proof deferred to M08-T01 after M07-T05 machinery. No new product
  decision, no frozen planning/requirements change, no Card technical contract created.

Intentionally NOT imported (classified, not executed, not silently bypassed):

- Target stale real-test profile bytes (`codex-lb/gpt-6-luna` + `low` in `AGENTS.md`,
  `bin/run-llm-test.sh`, `policies/*`, `docs/LLM_TEST_POLICY.md`,
  `tests/test_llm_test_policy_contract.py` Luna assertions) — superseded by R2/ADR-PUD-004,
  replaced by §2 delivery. Product-wide scan asserts no `gpt-6-luna` remains in
  `config/`, `docs/`, `contracts/`, `scripts/`.
- Target live harnesses `tests/run_codex_lb_live_rpc_acceptance.py`,
  `tests/run_codex_lb_production_activation.py`, `tests/run_codex_lb_staged_home_acceptance.py` —
  classified as inference-capable/live provider/RPC/activation entrypoints; not imported,
  not executed, not modified. See §3.
- `PROJECT.md` untouched (workstream index authority preserved).

Preserved update-system intent (additively extended only where the correction requires,
still GREEN):

- `scripts/managed_component_lifecycle.py`, `scripts/resolve-paseo-candidate.py`,
  `config/unraid/templates/pi-unraid-paseo.xml`, `config/paseo-candidate.json`, all M01–M07
  resolver/promotion/ledger/guard/adapter scripts and contracts unchanged.
  `scripts/paseo_candidate_build.py` gains ONLY the additive companion declaration +
  verifier (§2); handoff/render/package semantics unchanged
  (`tests/test_paseo_candidate_build_pipeline.py` extended minimally to stage a fixture
  companion file). `config/pi-agent/AGENTS.md` managed-lifecycle line retained.

## 2. Reproducible R2 policy/provider-delivery (request only, never capability proof)

New repo-managed bundle through the existing instruction plane (frozen source identity,
no HOME mutation, production untouched):

- `config/pi-agent/bin/run-llm-test.sh` (0755) — R2 fixed `meta/muse-spark-1.3-contributor`/`max`,
  no fallback, `gpt-6-astra` forbidden, plus validated `--native-create-agent-args`
  (`pi/meta/muse-spark-1.3-contributor`, `thinkingOptionId max`, `notifyOnFinish true`).
  Byte-identical to the installed `~/.pi/agent/bin/run-llm-test.sh` R2 reference.
- `config/pi-agent/policies/llm-test-policy.json` — R2 fixed profile, byte-identical to HOME R2.
- `config/pi-agent/policies/LLM_TEST_POLICY.md` and `docs/LLM_TEST_POLICY.md` — identical R2
  human contracts (DOC == GLOBAL_DOC asserted by contract test).
- `config/pi-agent/AGENTS.md` — retained managed-lifecycle line; added R2 policy section
  (`meta`/`muse-spark-1.3-contributor`/`max`, `NEVER use gpt-6-astra`, blocked-on-unavailable,
  no fallback). Total 33 lines (≤40 contract bound). Stale Luna profile absent.

Instruction-plane bundle (existing `scripts/pi_instruction_plane.py` + `configure-pi-instruction-plane.sh`):

- Source: `config/pi-agent` (10 files, see §4 digest).
- Mode: `bin/*` → `0755`, all else `0644` (path-based, not inferred from checkout).
- Synthetic readback on disposable temp HOME only (production HOME never touched):
  `apply` → `changed true, in_sync true`; `status` → `in_sync true`;
  second `apply` → `changed false` (no-op); `rollback` → `restored_prior_state true`;
  `bin/run-llm-test.sh` observed `755`, `AGENTS.md`/`llm-test-policy.json` observed `644`.

Explicit frozen companion binding (actual declaration, not copy inference):

- `scripts/paseo_candidate_build.py` now declares AND enforces the companion through
  the existing prepare/build-input/package evidence path:
  `companion_bundle_identity(source_root)` computes the file set, per-path modes and
  content digest with the installer's OWN `safe_files`/`managed_mode`/`digest_source`
  (loaded from this builder's tooling, not from the inspected source);
  `prepare_context` records it as `companion_bundle` in the result and the staged
  `.pi-unraid-candidate-build-input.json` AND verifies the actual staged copy via
  `verify_companion_binding(stage_dir, companion)` before the record is written —
  a divergent staged payload fails the real entrypoint, not just a helper test.
  `package_tested_image(..., build_input_path=None)` retains the declaration in the
  package evidence and checks record presence/shape, candidate linkage and schema
  BEFORE any docker call (omitted input preserves prior CLI/workflow behavior; new
  additive `--build-input` flag, no workflow edit).
- `verify_companion_binding(source_root, declared)` fails closed (raises
  `CandidateBuildError`, never preserves the binding) on changed content, added/removed
  files, wrong modes, wrong digest, missing/unsafe source, or malformed declarations.
- Actual payload split, stated exactly: the IMAGE carries only the entrypoint wrapper
  (`Dockerfile COPY`); the instruction bundle is delivered by the instruction plane
  `apply` from this frozen source. The build-input record binds both to one source
  state for eligibility; it does not claim the bundle is inside the OCI blob.
- Old digests (incl. M07 `77e29f0d…`) are not made eligible by this change; a fresh
  exact artifact remains M07-T07 scope. M07-T05 validator adapters and M07-T06
  final-gate/promotion changes are explicitly untouched; their acceptance boundaries
  stay deferred.

Provider/dependency/artifact provenance (public/source metadata only; no credential
value read, admitted, or persisted):

- Pinned: `pi 0.87.1` (`@earendil-works/pi-coding-agent@0.87.1`,
  `dist.integrity sha512-m8ArJUtVcQMSe1lLE/Ei7vX/JV7O39sWmWBsXV2NOU70F0qCp8GubA24pT3LnwTmM6LL2xV80/h6sQg85n69ew==`),
  `paseo 0.9.2` (`ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`),
  `Dockerfile` `FROM` + `PI_UNRAID_PI_VERSION="0.87.1"` + `pi --version` gate match
  `config/paseo-candidate.json` (`candidate sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`).
- Pinned fixture `tests/fixtures/m07t04/pi-ai-0.87.1-meta-contributor.json` records the
  upstream `thinkingLevelMap` for `muse-spark-1.3-contributor` (`max: null`) with package /
  version / registry-integrity / tarball provenance. Provenance-gated readback executes
  Pi's ACTUAL bundled `getSupportedThinkingLevels`/`clampThinkingLevel`
  (`pi-ai@0.87.1 dist/models.js`, version-checked before trust): supported levels exclude
  `max`, `clampThinkingLevel(model, "max")` → `"xhigh"`. Fixture bytes equal installed
  bundle bytes for the contributor map. Catalog metadata only — never an endpoint
  verdict; the fake-max hazard is explicit and effective `max` acceptance stays at
  M08-T01 after M07-T05 machinery.
- Documented `modelOverrides` (`docs/models.md`) is a supported configuration interface.
  No repo-managed `modelOverrides` fragment is adopted in this Card: the Sep-28
  unmanaged `~/.pi/agent/models.json` override remains environment-local only, is not
  part of reproducible delivery, and is not imported. Unrelated providers and user model
  selection preserved (no `settings.json`/`auth.json` delivery).
- Supported adoption here is provenance/request delivery only (fixed request through the
  canonical guard, no fallback). Unsupported/missing profile, downgraded effective level,
  wrong bundle, or unverifiable binding cannot report real acceptance.

## 3. Test classification and results (explicit no-inference)

All executed tests use fake executables, synthetic/local fixtures, temp dirs, or
approved non-inference source readback. No test inference was run, no validation
credential admitted, no ordinary-agent credential value read/copied, no installed
HOME/runtime/harness mutated, no image built/published, no CI triggered, no
host/production action taken.

- NOT executed (classified inference-capable/live, excluded by Card):
  old live provider/RPC/activation harnesses (not imported, not run);
  `config/pi-agent/bin/run-llm-test.sh PROMPT` with a real prompt (would infer — never run);
  `paseo_tower_validator` Codex `/responses` smoke with a real secret (M07-T05 scope, not run);
  docker-image builds, Tower live state, production guard/channel/cutover/rollback.
- Executed synthetic only (real delivered bytes, fake-only executables, temp roots):
  - Behavioral launcher rejection (`tests/test_llm_test_policy_contract.py`): the ACTUAL
    repo launcher copied into a disposable symlink-free agent root; resolution runs
    ONLY through a test-owned bindir (symlinks to the real `dirname`/`jq`/`bash` plus
    an optional fake `paseo`), so no ambient host binary — including a real Paseo in
    `/usr/bin` or elsewhere — can ever be reached on any host. Dispatch state is
    snapshotted BEFORE temp-dir cleanup. Bad provider (`codex-lb`), bad models
    (`gpt-6-luna`, `gpt-6-astra`), downgraded contributions (`xhigh`, `low`),
    `fallback_allowed: true`, emptied `forbidden_models`, and missing policy each →
    exit `3` (policy) / nonzero (missing) with NO dispatch (no fallback/substitution);
    `--native-create-agent-args` with a bad profile → exit `3` with no payload;
    valid policy with empty bindir → nonzero with no dispatch (unavailable execution
    fails closed on every host). Positive control (valid R2 + fake `paseo`) → exit
    `0` with an OBSERVED dispatch carrying exactly `meta/muse-spark-1.3-contributor` +
    `max`, proving negative assertions are meaningful.
  - Downgraded/native-shape non-acceptance (`tests/test_m07_t04_policy_delivery.py`):
    `xhigh`/`high` policies fail closed in BOTH prompt and native-args shapes
    (exit `3`, no dispatch, no payload) — neither observation satisfies final gates.
  - Upstream-function clamp readback (same file): pinned fixture asserts `max: null`
    as metadata (always executes); provenance-gated readback (installed `pi-ai`
    package version must equal the frozen `0.87.1` pin, else honest skip) EXECUTED here —
    installed bundle is `0.87.1`, `node` present: actual `dist/models.js` functions
    return supported `minimal..xhigh` (no `max`) and clamp `max→xhigh`; fixture map
    equals installed map. Zero skips taken; skip branches documented in-test.
  - Companion binding (`tests/test_paseo_companion_bundle.py`, 14 tests): identity
    declares sorted files + `bin→0755`/`0644` modes + digest deterministically and
    secret-free; `verify` accepts the match and rejects changed content, removed file,
    added file, wrong digest, wrong modes, malformed declarations (6 shapes), missing
    source, and symlink sources; real source bundle binds. Integration against REAL
    entrypoints with mocked Docker only (no image build, no daemon, no production):
    `prepare_context` records the declaration in the staged build-input record and
    enforces the staged copy; post-prepare staged content/file-set mutations each
    break the binding; `package_tested_image` with a build-input record retains the
    declaration in package evidence, and missing/malformed/schema/candidate-mismatch
    declarations fail with zero docker calls (mock asserts not called).
  - `prepare` integration (`test_paseo_candidate_build_pipeline.py`): staged record
    carries the declared `companion_bundle` (source/files/modes/digest).
  - Targeted: `test_llm_test_policy_contract` + `test_m07_t04_policy_delivery` +
    `test_paseo_companion_bundle` + `test_paseo_candidate_build_pipeline` +
    `test_pi_instruction_plane_contract` → **48/48 GREEN**.
  - Affected incl. entrypoint/auth-shadow/catalog/Compose/relay/rpc/lifecycle/resolver →
    GREEN (see full run); `node --test tests/codex_lb_dynamic_model_catalog_core_test.mjs`
    → **1/1 GREEN**.
  - Full: `python3 -m unittest discover -s tests -p 'test_*.py'` → **553/553 GREEN**,
    zero skips in the corrected modules.
  - `git diff --check` → **GREEN**.
  - Secret-safe scans: `config/`+`scripts/`+`docs/`+`contracts/` grep for credential
    patterns → clean; instruction-plane corpus scan (contract test) → clean.
  - Instruction-plane disposable readback (temp HOME, §2) → mode/rollback/drift/readback GREEN.

## 4. Delivery provenance (secret-safe, frozen source identity)

- Instruction bundle: `config/pi-agent` 10 files:
  `AGENTS.md`, `bin/run-llm-test.sh`, `extensions/codex-lb-dynamic-model-catalog.ts`,
  `extensions/lib/codex-lb-dynamic-model-catalog-core.mjs`, `policies/LLM_TEST_POLICY.md`,
  `policies/llm-test-policy.json`, `skills/project-recovery/SKILL.md`,
  `skills/project-recovery/references/bootstrap.md`, `skills/unraid-admin/SKILL.md`,
  `skills/unraid-admin/references/safety-boundary.md`.
- Bundle digest: `sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`
  (unchanged by this correction; `config/pi-agent` bytes untouched).
- Pinned clamp fixture: `tests/fixtures/m07t04/pi-ai-0.87.1-meta-contributor.json`
  (upstream `pi-ai@0.87.1` integrity + tarball recorded inside).
- Prepare record: staged `.pi-unraid-candidate-build-input.json` carries
  `companion_bundle` (source/files/modes/digest) with the candidate/handoff/build identities.
- R2 launcher/policy bytes match the installed HOME R2 reference; target stale Luna/low
  bytes intentionally differ (superseded, not a regression).
- No credential material in Git, logs, or this evidence. Auth material never opened;
  only `diagnostic` presence/file metadata from Research was reused, no values read.

## 5. Limitations and remaining gaps (for Main owner classification, not bypassed)

- Effective `max` on the direct-Meta path remains unverified (bundled + `pi.dev` catalog
  metadata say unsupported; local HOME advertisement rests on the unmanaged override;
  no inference permitted here). Fixed request delivery is not capability/inference proof.
  Final exact-candidate effective-profile/wire/inference proof remains M08-T01 after
  M07-T05 machinery; M07-T05/T06 acceptance boundaries explicitly unimplemented here.
- `models-store.json` non-contributor flip provenance untraced (Research C4, unchanged).
- If the installed `pi-ai` pin ever differs from `0.87.1` or `node` is unavailable, the
  upstream-function clamp test honestly skips (fixture metadata test still executes);
  in this run both were present so the readback EXECUTED with zero skips.
- Tower validator still performs direct Codex-LB `/responses` inference and can PASS
  without a real Muse smoke (P4 §2 risk 2) — intentionally untouched (M07-T05 scope).
  No final eligibility, credential admission, or production mutation claimed.
- Old M07 candidate `77e29f0d…` fixture rehearsal does not establish R2 acceptance; new
  exact artifact remains M07-T07 scope. No image build/publication performed here.
- No genuine missing agent-findable facts beyond the above; no fallback, substitution,
  or policy change invented. No real blocker preventing this baseline Card's synthetic
  acceptance; final real gates remain blocked by design until M08 inputs.

## 6. Return to Main

- Implementation commits: to be recorded by Main on commit (bounded source corrections
  in §1–§2 plus this updated evidence file only; no push, PR, Issue, or workflow-state change).
- Evidence: this file (`implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T04-baseline-implementation-2026-10-04.md`;
  `bae5214` and `9c31416` bytes retained in Git history).
- Tests: §3 classification/results (48/48 targeted, 553/553 full + node 1/1, diff-check
  GREEN; upstream clamp readback executed, zero skips; dispatch snapshots pre-cleanup;
  fake-only PATH on every host).
- Preserved target: §1 verbatim + reconciled-contract list, update-system intact;
  delivery/binding provenance §2+§4.
- Limitations/gaps: §5 (effective-max unverified → M08-T01; validator/gates → M07-T05/T06;
  fresh artifact → M07-T07). Main alone normalizes the semantic result, obtains a fresh
  independent review, and continues canonical routing.
