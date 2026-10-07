# Muse max delivery (M07-T05A) — procedure and limitations

## Status and boundaries

This document describes the M07-T05A implementation subject, **not** an accepted
Card result, independent review, or real validation. Main owns acceptance
classification and workflow reconciliation. No real inference, live provider
auth, credential admission, installed HOME/catalog/runtime mutation, live
Docker/Tower/host operation, CI/build/publication/push, or production cutover
is established here. All evidence is synthetic/local with fake-only external
boundaries. Catalog presence, launcher shape, and fake-wire success establish
delivery/clamp correctness only — never endpoint acceptance or candidate
eligibility. M08-T01 owns dedicated credentials and exact-candidate real
inference; M07-T07 owns fresh immutable artifact identity.

## What is delivered

One secret-free frozen fragment through the existing companion/candidate path:

- Fragment: `config/pi-agent/models.muse-max-override.json` (0644), exactly
  `{"providers":{"meta":{"modelOverrides":{"muse-spark-1.3-contributor":
  {"thinkingLevelMap":{"max":"max"}}}}}}`, nothing else.
- Merge helper: `config/pi-agent/bin/paseo-muse-max-merge.py` (0755), the ONLY
  writer of the derived effective file. Narrow validated merge preserving every
  unrelated provider/model setting verbatim; never installs or overwrites a
  whole `models.json`; never reads `auth.json` or the mutable `models-store.json`.
- Effective file: `<HOME>/.pi/agent/models.json` (0600), produced host-side by
  the helper from fragment + existing file, then bound continuously.

Pinned Pi 0.87.1 semantics used (read in full from installed docs/source):
`docs/models.md` (`modelOverrides` changes metadata without replacing the list;
unknown IDs ignored); `dist/core/provider-composer.js` (`applyModelOverride`
shallow key-merges `thinkingLevelMap`, `modelOverrides` is the topmost
user-config layer applied after catalog overlay, `hasOverrides` accepts a
provider carrying only `modelOverrides`); `dist/core/model-config.js`
(`ModelOverrideSchema`/`ProviderConfigSchema` permit the minimal shape);
`dist/core/model-runtime.js` + `remote-catalog-provider.js` (`models.json` is
the frozen layer, `models-store.json` is mutable cache, never provenance);
`pi-ai/dist/models.js` (`getSupportedThinkingLevels` excludes null, requires
explicit non-null for max; `clampThinkingLevel` scans up then down);
`openai-responses.js` (wire effort is `map[effort] ?? effort`, so forced max
serializes verbatim — wire bytes alone prove nothing).

## Procedure (disposable candidate)

1. Stage companion via the existing instruction-plane/prepare path. The fragment
   and helper enter `companion_bundle_identity` and propagate through
   prepare/build/package; old digests are never eligible.
2. Host-side merge: `apply_muse_max_merge(dst_agent, source_root)` (adapter) or
   `paseo-muse-max-merge.py --fragment <frag> --models <models.json>` — validates
   the fragment strictly, reads existing effective (or starts from
   `{"providers":{}}`), ensures only
   `meta.modelOverrides.muse-spark-1.3-contributor.thinkingLevelMap.max="max"`
   via shallow merge, writes atomically with 0600 when changed (idempotent
   otherwise). Any validation failure preserves the existing file unchanged.
3. Stage the applied interval AFTER the merge so its kernel-backed rows include
   both the fragment and the derived effective file. The interval watches
   `/home/paseo/.pi/agent` (read-only mount in the candidate) plus manifest and
   daemon config; writes, chmod, replacement, move/delete, or overflow
   invalidate irreversibly, even if bytes are restored.
4. Validator readbacks (all compared, never returncode-only): every companion
   file hash+mode, guard/policy hash+mode+fixed-profile fields, fragment
   validity, effective hash+mode vs the host-staged merge record plus
   `verify_muse_max_effective`, daemon/Pi lifecycle inside the candidate,
   `preflight_candidate_profile` (candidate daemon must advertise max).
5. Continuous binding: `applied_check()` now also re-reads the effective file
   hash+mode at every acquisition, preflight, dispatch, and completion
   boundary. Changed/missing/substituted/restored fragment or derived config,
   wrong model/provider/profile, ambiguous config, fixture-as-real, or fallback
   fails closed before fake prompt/transport; uncertainty after dispatch retains
   UNKNOWN with no replay.
6. Dispatch remains the existing fixed-profile guarded path
   (`meta/muse-spark-1.3-contributor/max`, no fallback, `gpt-6-astra` forbidden,
   witness aggregation, owned-child inspection). Fixture outcomes always leave
   `real_validation_satisfied=false`.

## Limitations (not claims)

- Fragment + synthetics prove supported configuration delivery and
  clamp-correctness only. They do not prove on-wire `reasoning.effort`
  acceptance, endpoint capability, or candidate eligibility.
- `models-store.json` overlay provenance remains untraced; delivery never relies
  on it. Installed HOME override and mutable overlay are diagnostic only.
- Endpoint acceptance/rejection of Contributor max on the direct-Meta path is
  untested by design (M08-T01 owns it). Credential availability/restrictions are
  deferred operator input.
- If M08-T01 later proves endpoint/credential non-acceptance, that new durable
  evidence — not this delivery — routes the Planning/Definition owner. No
  fallback, substitution, relabeling, or diagnostics-as-acceptance is authorized.
- Changed candidates require new immutable build identity and affected-gate
  evidence (M07-T07); never attach modified HOME to an old eligible digest.
