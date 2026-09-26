# M04-T03 R01 independent review — GREEN evidence

Task ID: PI-UNRAID-M04-T03-R01. Role: independent tester (did not produce/repair subject).
Review authority: Project Workflow V2 `workflow/REVIEW.md`
(exact-subject gate: immutable subject + Task Card acceptance + append-only attempt +
semantic independence + pending/GREEN/RED lifecycle + durable evidence).
Consumer branch: feat/paseo-gui-runtime, reviewed at
HEAD 7d442b6424e8204ce3af78a01699d95264e57ba5; the review did not change the subject.

## Exact bindings (all verified in git)

- Review attempt: implementation/workstreams/feature-paseo-gui-runtime/reviews/M04-T03-R01.toml,
  was pending and sole last attempt for M04-T03 when reviewed (lifecycle-conformant).
- Result subject: elmakus/pi-unraid @ commit fb6195831d047ede2f359146b69ede2690e84ef3,
  path implementation/workstreams/feature-paseo-gui-runtime/results/M04-T03.md,
  blob e31658fda900d748010bedc6caa0bb3aacf8c430 (`git ls-tree` + `hash-object` match;
  Task Board result binding identical).
- Acceptance: implementation/workstreams/feature-paseo-gui-runtime/cards/M04-T03.md.
- Implementation subject named by result: elmakus/pi-unraid@8914f92b3f832e81c28b276e0ebee08d374f5013
  (verified commit, ancestor of HEAD).
- Dependencies verified exact commit:blob — M02-T03 cac4ac5e5a4b6c96ad71d9bbce12962388f7a4be :
  0d13d7fe5a6dd29fb68e700d13cc5c1251722c28; M04-T01 affd83590ec534ed144b9048a2b9075434761f27 :
  5173447ec3ab8775450a9defbf193aede63ca290; M04-T02 e9a412557bfbe927a64b1f7ba0d892f5f059e08a :
  c6adc8514548b701c3aa959df9f5a6f4ff581a9d.
- Evidence ref: implementation/workstreams/feature-paseo-gui-runtime/evidence/M04-T03-global-capabilities-2026-09-26.md.

## Checks and evidence

1. Frozen candidate: config/paseo-candidate.json Pi 0.87.1 / specpi 0.34.0 / pi-mcp-adapter 2.37.0
   with npm integrity + source commits; Dockerfile env + labels match; no `@latest`; candidate
   file untouched in a1e8297..8914f92.
2. Local contract suites: all 11 pass (74 tests), incl. test_pi_global_capabilities_contract 4/4.
3. CI: run 36213649679, https://github.com/elmakus/pi-unraid/actions/runs/36213649679
   (job 108325177837), independently pulled via gh: conclusion success, headSha
   8914f92b3f832e81c28b276e0ebee08d374f5013, all steps green incl. predecessor bindings,
   full contract suite, child-image build, image/provenance, persistence, instruction-plane,
   global-capability smoke, metadata inspection. Logs reproduce the evidence readbacks
   (candidate sha256:b4e0c1e7…, image sha256:f41cdcf6…, Paseo 0.9.2, Pi 0.87.1,
   secret_scan GREEN) and the exact M04-T03 GREEN payload.
4. Delivery behavior: scripts/pi_global_capabilities.py reviewed — apply gated on exact
   compatibility marker, build_status read-only (no pi/process writes), bounded snapshot of
   prior managed declarations only, rollback restores managed state, convergence on re-apply,
   mismatch/missing yields bounded RED (no silent reinstall); covered by contract tests and
   verifier asserts executed GREEN in CI.
5. Provider-free exact-candidate smoke: run_compatibility_smoke uses --offline + PI_OFFLINE=1
   + --no-session, asserts exact-source command surface (scope/wishlist/harness-improvement/
   mcp/pi-mcp/mcp-auth) and empty specpi-scope statusText; SpecPi policy string
   inactive_in_fresh_session; adapter config counted, never exposed (contents_exposed false).
6. Secret safety: unexpected/raw values fingerprinted (sha256:16), desired versions only on
   exact match; snapshot excludes unrelated packages/settings; CI secret scan GREEN.
7. Inventory/doctor feed: independent local run fed build_status inventory_observations into
   derive_inventory → specpi GREEN/none, pi_mcp_adapter GREEN/none, overall GREEN;
   identities match config/environment-capabilities.json (pi_extension_readback).
8. Scope boundary: impl range = 6 files only (workflow, Dockerfile pins, 2 sh scripts,
   pi_global_capabilities.py, 1 test); Dockerfile diff adds specpi/adapter pins only; no
   compose/candidate/production/M05/M06/OR-policy/PW-authority/live-MCP changes. bash -n +
   py_compile pass.

## Independence basis

This review context did not materially produce, reconcile, or repair the exact M04-T03 result
subject or its implementation; consistent with the R01 TOML independence declaration. No
provider/model/session identity persisted (non-canonical per REVIEW.md).

## Limitations

- No local docker: image build and disposable Pi smoke not re-executed here; behavior proof
  taken from independent gh pull of CI logs on the exact SHA.
- Detached Tower re-verification claim in evidence not corroborated (no Tower access).
- SpecPi/MCP expected command names validated via exact-candidate CI smoke, not external docs.

## Conclusion

REVIEW.md lifecycle/identity/independence/evidence requirements are satisfied and introduce no
new product gap. All Task Card acceptance is supported. Verdict: GREEN for the exact frozen subject.
