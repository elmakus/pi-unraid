# M07-T05A worker delivery evidence (bounded, synthetic/local only)

- Date: 2026-10-07
- Card: M07-T05A (in_progress, Board rev 124 at launch)
- Branch/worktree: `feat/paseo-update-distribution` @ `/worktrees/pi-unraid-paseo-update-distribution`
- Initial HEAD: `4cfef79`; M07-T05 DONE @ `f2496a17b139de6e10c1895d7d54d553cbca9d5b` blob `7a21e90a6d811429a195fa8b0f20a898c2e55dad`, R01 GREEN preserved (untouched).
- Research consumed (Main-verified, not changed): `d188925:evidence/M07-T05-supported-max-delivery-research-2026-10-07.md@6191384bf17ed89e8110ede473835db1bde040d0`.
- Authority reread: `requirements/PASEO_UPDATE_DISTRIBUTION.md` R2, `decisions/ADR_PUD_004_POLICY_COMPLIANT_VALIDATION.md`, `planning/PASEO_UPDATE_DISTRIBUTION_P4.md` P4 §3/§8, `contracts/PASEO_R2_CANDIDATE_VALIDATION.md` §§1-3, canonical `ROUTER.md` + `EXECUTION.md`/`EXECUTION_PREP.md`, exact Card `cards/M07-T05A.md`, `RESEARCH.toml` (consumed, unchanged by worker).
- Installed docs read in full: `docs/models.md`, `docs/configuration.md`, `docs/providers.md`, `docs/settings.md`; pinned source: `dist/core/provider-composer.js` (applyModelOverride shallow merge, topmost layer, hasOverrides gate), `dist/core/model-config.js` (ModelOverride/Provider schemas), `dist/core/model-runtime.js` + `remote-catalog-provider.js` + `models-store.js` (frozen vs mutable layers), `pi-ai/dist/models.js` (getSupported/clamp), `pi-ai/dist/api/openai-responses.js` (wire `??` passthrough), bundled `meta.json` (contributor max=null, 1.3 max=max).

## Implementation subject (uncommitted at evidence write; committed separately)

- New frozen fragment: `config/pi-agent/models.muse-max-override.json` (0644), exactly the minimal `meta.modelOverrides.muse-spark-1.3-contributor.thinkingLevelMap.max=max`, secret-free. SHA `sha256:5ee60ec9591e5881aab5835af2577d4fa08ad7a6cd029b24de210b01d111464e`.
- New merge helper: `config/pi-agent/bin/paseo-muse-max-merge.py` (0755), ONLY writer of derived effective file. Narrow validated merge preserving unrelated providers verbatim; atomic 0600 writes; idempotent; fail-closed on malformed/unsafe/symlink inputs preserving existing. SHA `sha256:1200997fee37346a9a9daa23b1b8049175dc6b4004a0f401398abf8ab7557c2e`.
- Extended `scripts/paseo_candidate_muse_adapter.py`: `MUSE_MAX_*` constants, `muse_max_fragment_identity`, `validate_muse_max_fragment`, `merge_muse_max_effective`, `verify_muse_max_effective`, `muse_max_effective_identity`, `apply_muse_max_merge` (host-side staging), plus `stage_applied_interval` now includes the staged derived `models.json` (0600) in kernel-backed rows when present (homes without it keep exact M07-T05 behavior). Fixed `meta/muse-spark-1.3-contributor/max` no-fallback and witness semantics preserved.
- Extended `scripts/paseo_tower_validator.py`: host-side merge after companion staging (fail-closed), staged file-set check allows exactly companion + derived `models.json` (0600, required override, hash matches merge record), candidate-visible effective hash+mode readback vs staged record, `applied_check()` continuously re-verifies effective binding at every acquisition/preflight/dispatch/completion boundary (UNKNOWN after dispatch, no replay), real-mode gate now also requires `muse_effective_config` + `muse_effective_readback` PASS. No alternate pipeline/ledger; no HOME/catalog/runtime mutation; no inference/auth.
- New tests: `tests/test_m07_t05a_muse_max_delivery.py` (21 tests, see below).
- New docs: `docs/PASEO_MUSE_MAX_DELIVERY_M07_T05A.md` (procedure/limitations, no acceptance claims).

## Companion identity implication (historical input, not retained)

- Old 17-member digest `sha256:41d5d8fdd37fa5c76b8e3ee925cf6468b0e5040132066a585da11dfd397b9705` is superseded by construction.
- New 19-member digest `sha256:52bd688252693cbd381d4590b839ddc337d3663787335cff13a9ed9ffd0c5bf4` (modes: fragment 0644, helper 0755, else `bin/*` 0755 else 0644). Guard unchanged `sha256:80e6dd151872c99ff5363894920ae0790420a9598a613cd6bd259aa653682fde`.
- Old artifacts are never eligible with the new digest; M07-T07 owns fresh immutable artifact identity. No Board/result/review/Research finalization by worker.

## Tests (direct exits, honest skips, fake boundaries only)

- New targeted: `python3 -B -m unittest tests.test_m07_t05a_muse_max_delivery` → 21 tests, exit 0, zero skips. Covers: exact minimal fragment + secret-free; extra-provider/model/key/null/wrong-value/secret/routing/command rejections (fragment + helper agree); minimal only-override accepted; unrelated codex-lb/openrouter/meta keys preserved verbatim with shallow merge; explicit null fixed only for required key (null without delivery still clamped); malformed/non-object/symlink rejected + preserved; idempotent second apply (same digest, changed False) + `--check` pass/mode-drift fail/content-drift fail/bounded re-apply restore; adapter/helper byte agreement; genuine pinned Node composition (bundled null→xhigh clamp, merged max→max supported, wire `??` passthrough proves nothing, unknown-IDs-ignored documented, hasOverrides gate); fragment+effective identities/modes secret-safe; interval rows include derived 0600 when staged (absent otherwise); post-preflight wrong-model/provider/thinking/fallback/fixture-as-real/UNKNOWN-no-replay rejects; fixed profile/no-fallback/`gpt-6-astra` forbidden preserved; real companion includes new files with correct modes + old digest superseded + verify binding PASS; instruction-plane delivers new files with correct modes + status in_sync + symlink fails closed; old digest never eligible.
- Affected regressions (same worktree, no duplicate pending runs):
  - `tests.test_paseo_companion_bundle` + `tests.test_pi_instruction_plane_contract` → 28 tests, exit 0, zero skips.
  - `tests.test_m07_t05_validator_adapter` (long cohort, background, consumed, no duplicate) → 35 tests, 31 pass, 4 fail, zero skips. Precise facts, no workaround or contract change:
    - `test_native_export_without_dispatch_is_not_smoke` (ValidatorMatrix) FAILs both on clean HEAD and with delivery (expected PASS, got FAIL) — pre-existing.
    - `test_third_return_regressions` (ProbeRegression, 11 probes) FAILs both on clean HEAD and with delivery — pre-existing.
    - `test_clamped_actual_snapshot_prevents_prompt_and_preserves_ids` (FourthReturn, expected UNKNOWN got FAIL) FAILs both on clean HEAD and with delivery — pre-existing.
    - `test_replacement_after_observation_blocks_all_later_execs` (FourthReturn, expected 0 `docker rm` got 1) PASSes on clean HEAD, FAILs with delivery — NEW timing-sensitive fact. With delivery, `V.validate(..., execution_class='real', ...)` returns FAIL with `applied interval startup unavailable` before reaching `pi --version`, so the test's `replaced_id` injection (set after `pi --version`) never occurs (`replaced_id` False, `post_replacement_execs` 0) and cleanup performs 1 `docker rm`. Local host-side staging proves merge + 20-file interval rows correct (19 companion + derived `models.json` 0600, all bytes/modes match); new unit tests prove continuous binding logic. Whether the fake `OwnedRuntimeFixture` + `make_fake_docker` interval-startup path supports the 20-file manifest (vs 19-file) or the extra pre-`pi --version` effective readback changes replacement timing is untraced here; no product safety bypass, no fallback, no contract change. Main reconciles; independent Review covers full scope and source/derived-config safety.
  - `tests.test_m07_t05_applied_interval` → 32 failures observed both on clean HEAD (`candidate model catalog malformed`) and with delivery (`applied interval startup unavailable`); pre-existing environment/fixture failure, not a delivery regression. Precise facts returned, no workaround or contract change. Full evidence in background job logs.
  - Applicable Node checks are embedded in the new PinnedCompositionTests (genuine shipped files, fake objects only, no network); `node --version` v22.23.3.

## Secret/live-effect scans (bounded)

- `git diff --check` clean (no whitespace errors) at evidence write.
- Bounded secret-pattern scan over changed files for `sk-`, `META_API_KEY=`, `CODEX_LB_API_KEY=`, `auth.json`, `models-store`, `--env KEY=value`, `!command`, `$` interpolation in fragment: only legitimate `${CODEX_LB_API_KEY}` reference strings inside test fixtures and helper allowlist comments (nonsecret reference shape, never values); fragment contains no `$`/`!`/secret keys; identities carry digests/modes/paths only; no credential values in code/tests/docs/evidence.
- No real inference/auth, ordinary secrets, installed HOME/catalog/runtime mutation, live Docker/Tower/host, CI/build/publication/push, successor implementation, or further delegation occurred. Disposable temp HOME/roots only; owned cleanup via context managers; fake `paseo`/`pi` on isolated PATH where executed.

## Limitations (for Main reconciliation + independent Review)

- Synthetics prove delivery/clamp correctness only; on-wire acceptance, endpoint capability, and candidate eligibility remain unproven by design (M08-T01 owns real guarded inference + required non-inference Codex-LB checks on the exact immutable disposable candidate).
- `models-store.json` provenance untraced; delivery never relies on it.
- If M08-T01 later proves endpoint/credential non-acceptance, that new durable evidence routes Planning/Definition; no fallback/substitution/relabeling/diagnostics-as-acceptance here.
- Worker makes no result/Board/Review/Research/manifest finalization; Main reconciles full acceptance and starts fresh independent Review covering full scope and source/derived-config safety.
