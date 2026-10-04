# M07-T04 — Baseline implementation (preserved target + reproducible R2 delivery)

Date: 2026-10-04
Card: `M07-T04`
Implementation subject (pre-change): `87af8a8efad04ab5c9b184d6ca41f861cca35d72`
Target observation (refreshed before changes): `main@e9476b4987290767a195a9de2ecd655de5f09605`
Merge-base: `fc7a470a7330839cbaf8eaf0c2914323981d6901`
DONE dependency (verified unchanged): `implementation/workstreams/feature-paseo-update-distribution/results/M07-T03.md@c9d18c3f1c159684128221a6569496630d7fcbce:21dea73b5f663125cce8642486abc7cbffb506e3`
Authority: `requirements/PASEO_UPDATE_DISTRIBUTION.md` (R2), `requirements/PASEO_GUI_RUNTIME.md`,
`decisions/ADR_PUD_001_DISTRIBUTION_AND_CUTOVER.md`, `decisions/ADR_PUD_002_MANAGED_COMPONENT_LIFECYCLE.md`,
`decisions/ADR_PUD_004_POLICY_COMPLIANT_VALIDATION.md`, `planning/PASEO_UPDATE_DISTRIBUTION_P4.md`.
Technical contract: none. Factual input: `evidence/M07-T04-provider-delivery-research-2026-10-04.md`
at `3f92235a47cf0fad140f3a5e8a782a0b2ce429ca`.

Scope: substantive implementation/debugging/synthetic testing only. No Card/plan authoring,
no gate satisfaction, no Task Board/manifest/result/review finalization, no second Card.
All selected-workstream authority/state/historical subjects preserved byte-for-byte
(no `implementation/workstreams/feature-paseo-update-distribution/cards/*`,
`TASK_BOARD.toml`, `WORKSTREAM.toml`, `results/*`, `reviews/*` modified).

## 1. Target preservation (what was kept, what changed)

Accepted target repairs reconciled into the legal source workstream without regressing
the update system and without touching unrelated target-side recovery packages
(`feature-codex-lb-dynamic-model-catalog`, `issue-paseo-codex-lb-env-propagation`,
`issue-codex-lb-current-main-gpt6-image` workstream packages left untouched on `main`;
none copied as competing authority).

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

Intentionally NOT imported (classified, not executed, not silently bypassed):

- Target stale real-test policy (`codex-lb/gpt-6-luna` + `low` in `AGENTS.md`,
  `bin/run-llm-test.sh`, `policies/*`, `docs/LLM_TEST_POLICY.md`,
  `contracts/PASEO_CODEX_LB_RUNTIME_ENV.md` policy section,
  `tests/test_llm_test_policy_contract.py` Luna assertions) — superseded by R2/ADR-PUD-004.
  The mechanical secret/catalog portions are preserved; the Luna/low profile is not
  copied as authority. `contracts/PASEO_CODEX_LB_RUNTIME_ENV.md` left absent from this
  branch; its policy section is recorded here as superseded, not as a preserved contract.
- Target live harnesses `tests/run_codex_lb_live_rpc_acceptance.py`,
  `tests/run_codex_lb_production_activation.py`, `tests/run_codex_lb_staged_home_acceptance.py` —
  classified as inference-capable/live provider/RPC/activation entrypoints; not imported,
  not executed, not modified. See §5.
- `PROJECT.md` untouched (workstream index authority preserved).

Preserved update-system intent (unchanged, still GREEN):

- `scripts/managed_component_lifecycle.py`, `scripts/paseo_candidate_build.py`,
  `scripts/resolve-paseo-candidate.py`, `config/unraid/templates/pi-unraid-paseo.xml`,
  `config/paseo-candidate.json`, all M01–M07 resolver/build/promotion/ledger/guard/adapter
  scripts and their contracts. `config/pi-agent/AGENTS.md` managed-lifecycle line retained.

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
  no fallback). Total 33 lines (≤40 contract bound). Stale `codex-lb/gpt-6-luna` absent.

Instruction-plane bundle (existing `scripts/pi_instruction_plane.py` + `configure-pi-instruction-plane.sh`):

- Source: `config/pi-agent` (10 files, see §4 digest).
- Mode: `bin/*` → `0755`, all else `0644` (path-based, not inferred from checkout).
- Synthetic readback on disposable temp HOME only (production HOME never touched):
  `apply` → `changed true, in_sync true`; `status` → `in_sync true`;
  second `apply` → `changed false` (no-op); `rollback` → `restored_prior_state true`;
  `bin/run-llm-test.sh` observed `755`, `AGENTS.md`/`llm-test-policy.json` observed `644`.
- Digest: `sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`
  (`files: 10`). Companion bundle participates in eligibility identity via the existing
  candidate build context (`scripts/paseo_candidate_build.py` `shutil.copytree` of the
  whole source root; `staged_candidate = stage_dir / "config" / "paseo-candidate.json"`).
  Old digests (incl. M07 `77e29f0d…`) are not made eligible by this change; a fresh
  exact artifact remains M07-T07 scope.

Provider/dependency/artifact provenance (public/source metadata only; no credential
value read, admitted, or persisted):

- Pinned: `pi 0.87.1` (`@earendil-works/pi-coding-agent@0.87.1`,
  `dist.integrity sha512-m8ArJUtVcQMSe1lLE/Ei7vX/JV7O39sWmWBsXV2NOU70F0qCp8GubA24pT3LnwTmM6LL2xV80/h6sQg85n69ew==`),
  `paseo 0.9.2` (`ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`),
  `Dockerfile` `FROM` + `PI_UNRAID_PI_VERSION="0.87.1"` + `pi --version` gate match
  `config/paseo-candidate.json` (`candidate sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`).
- Bundled direct-Meta catalog (installed `pi-ai@0.87.1`,
  `dist/providers/data/meta.json`): `muse-spark-1.3-contributor` `thinkingLevelMap.max = null`
  (unsupported); non-contributor `1.3` `max = "max"`. Synthetic clamp check proves
  unmodified `clampThinkingLevel(model,"max")` → `"xhigh"` (fake-max hazard explicit).
- Documented `modelOverrides` (`docs/models.md`) is a supported configuration interface.
  No repo-managed `modelOverrides` fragment is adopted in this Card: the Sep-28
  unmanaged `~/.pi/agent/models.json` override (`meta.modelOverrides.muse-spark-1.3-contributor.thinkingLevelMap.max="max"`)
  remains environment-local only, is not part of reproducible delivery, and is not
  imported. Unrelated providers and user model selection preserved (no `settings.json`/
  `auth.json` delivery; merge/readback bounds asserted by contract tests).
- Supported adoption here is provenance/request delivery only (fixed request through the
  canonical guard, no fallback). Effective `max` wire/inference acceptance remains
  unverified and stays at M08-T01 after autonomous machinery/rehearsal. Unsupported/
  missing profile, downgraded effective level, wrong bundle, or unverifiable binding
  cannot report real acceptance.

## 3. Test classification and results (explicit no-inference)

All executed tests are synthetic/local fixtures, mocks, temp dirs, or static readback.
No test inference was run, no validation credential admitted, no ordinary-agent
credential value read/copied, no HOME/runtime/harness mutated, no image built/published,
no CI triggered, no host/production action taken.

- NOT executed (classified inference-capable/live, excluded by Card):
  old live provider/RPC/activation harnesses (not imported, not run);
  `config/pi-agent/bin/run-llm-test.sh PROMPT` with a real prompt (would infer — never run);
  `paseo_tower_validator` Codex `/responses` smoke with a real secret (M07-T05 scope, not run);
  docker-image builds, Tower live state, production guard/channel/cutover/rollback.
- Executed synthetic only:
  - `python3 -m unittest tests.test_llm_test_policy_contract tests.test_m07_t04_policy_delivery tests.test_pi_instruction_plane_contract` → **20/20 GREEN**.
    Covers fixed identity, `DOC==GLOBAL_DOC`, fake-`paseo` launcher arg capture
    (`meta/muse-spark-1.3-contributor` + `max`, no `astra`/`luna`),
    `--native-create-agent-args` fixed shape (no inference), wrong-profile fail-closed,
    bundled `max=null` + `max→xhigh` clamp, no-fallback/no-override, Luna-absent,
    target-repair presence, update-system preservation, bundle secret-safe + provenance,
    build-context binding.
  - Affected: `test_paseo_codex_lb_entrypoint_contract`, `test_codex_lb_auth_shadow_contract`,
    `test_codex_lb_dynamic_model_catalog_contract`, `test_paseo_runtime_contract`,
    `test_paseo_child_image_contract`, `test_paseo_relay_doctor_readiness_contract`,
    `test_paseo_rpc_workspace_contract`, `test_managed_component_lifecycle`,
    `test_environment_capability_inventory_contract`, `test_paseo_candidate_resolver`
    → **168/168 GREEN** (plus `node --test tests/codex_lb_dynamic_model_catalog_core_test.mjs` → **1/1 GREEN**).
  - Full: `python3 -m unittest discover -s tests -p 'test_*.py'` → **534/534 GREEN**
    (prior 503 + new/imported synthetic coverage).
  - `git diff --check` → **GREEN**.
  - Secret-safe scans: repo-wide `config/`+`scripts/`+`docs/` grep for
    `BEGIN PRIVATE KEY|MUSE_API_KEY=|CODEX_API_KEY=|GITHUB_TOKEN=` → clean;
    instruction-plane corpus scan (contract test) → clean.
  - Instruction-plane disposable readback (temp HOME, §2) → mode/rollback/drift/readback GREEN.

## 4. Delivery provenance (secret-safe, frozen source identity)

- Instruction bundle: `config/pi-agent` 10 files:
  `AGENTS.md`, `bin/run-llm-test.sh`, `extensions/codex-lb-dynamic-model-catalog.ts`,
  `extensions/lib/codex-lb-dynamic-model-catalog-core.mjs`, `policies/LLM_TEST_POLICY.md`,
  `policies/llm-test-policy.json`, `skills/project-recovery/SKILL.md`,
  `skills/project-recovery/references/bootstrap.md`, `skills/unraid-admin/SKILL.md`,
  `skills/unraid-admin/references/safety-boundary.md`.
- Bundle digest: `sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`.
- R2 launcher/policy bytes match the installed HOME R2 reference; target stale Luna/low
  bytes intentionally differ (superseded, not a regression).
- No credential material in Git, logs, or this evidence. Auth material never opened;
  only `diagnostic` presence/file metadata from Research was reused, no values read.

## 5. Limitations and real blockers (for Main owner classification, not bypassed)

- Effective `max` on the direct-Meta path remains unverified (bundled + `pi.dev` catalog
  metadata say unsupported; local HOME advertisement rests on the unmanaged override;
  no inference permitted here). Fixed request delivery is not capability/inference proof.
  Final exact-candidate effective-profile/wire/inference proof remains M08-T01.
- `models-store.json` non-contributor flip provenance untraced (Research C4, unchanged).
- `contracts/PASEO_CODEX_LB_RUNTIME_ENV.md` policy section superseded; mechanical secret/catalog
  portions preserved without that file. If Main requires the contract file present, its R2
  correction belongs to Planning/Prep authority, not this worker.
- Tower validator still performs direct Codex-LB `/responses` inference and can PASS without
  a real Muse smoke (P4 §2 risk 2) — intentionally untouched (M07-T05 scope). No final
  eligibility, credential admission, or production mutation claimed.
- Old M07 candidate `77e29f0d…` fixture rehearsal does not establish R2 acceptance; new
  exact artifact remains M07-T07 scope. No image build/publication performed here.
- No genuine missing agent-findable facts beyond the above; no fallback, substitution,
  or policy change invented. No real blocker preventing this baseline Card's synthetic
  acceptance; final real gates remain blocked by design until M08 inputs.

## 6. Return to Main

- Implementation commits: to be recorded by Main on commit (bounded product/source changes
  in §1–§2 plus this evidence file only; no push, PR, Issue, or workflow-state change).
- Evidence: this file (`implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T04-baseline-implementation-2026-10-04.md`).
- Tests: §3 classification/results (20/20, 168/168 + node 1/1, 534/534, diff-check GREEN).
- Preserved target: §1 verbatim list + update-system intact; delivery provenance §4.
- Limitations/blockers: §5 (effective-max unverified → M08-T01; validator → M07-T05;
  fresh artifact → M07-T07). Main alone normalizes the semantic result, obtains a fresh
  independent review, and continues canonical routing.
