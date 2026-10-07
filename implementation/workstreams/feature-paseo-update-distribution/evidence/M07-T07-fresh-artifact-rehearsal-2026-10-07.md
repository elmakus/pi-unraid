# M07-T07 — fresh exact artifact, autonomous rehearsal (worker evidence, no DONE)

Date: 2026-10-07
Card: M07-T07 in_progress (worker only; Board/result/review Main-owned)
Source: feat/paseo-update-distribution@effcf05 (P4 bootstrap allowance removed, smoke/buildx fixes retained)
Authority: requirements/PASEO_UPDATE_DISTRIBUTION.md R2, ADR-PUD-003/004, planning/PASEO_UPDATE_DISTRIBUTION_P4.md, contracts/PASEO_R2_CANDIDATE_VALIDATION.md
Dependencies: M03-T03@55b65d4, M07-T03@c9d18c3, M07-T04@6329cf4, M07-T05@f2496a1, M07-T05A@87a1607, M07-T06@5213b07 (all DONE GREEN, R02 for M07-T06)

## Frozen identities (recomputed)
- Target main@e9476b4, source feat@effcf05
- Companion 19 files sha256:67e15435, guard template ebc1b352, policy meta/muse-spark-1.3-contributor/max no-fallback
- Candidate 6f1e3b5c (paseo 0.11.0/pi 1.0.4/gh 2.102.0/docker-cli 29.8.2/compose 5.6.0, etc.)
- Old PR19 dec0cde/de809dab and old digests 9ee6074/22673ae/77e29f0 obsolete only

## GitHub build-once/test/preserved-image/GHCR publication (exact, terminal GREEN)
- Bootstrap: automation/paseo-update-candidate-p4-bootstrap -> feat/paseo-update-distribution, parent b397464 (allowance 1d13427 + fixes), 2 handoff files only, normal build/package/publish reuse
- PR24 3dfd895->b397464 OPEN then CLOSED without merge after GREEN; ref deleted verified absent
- Run 37674844486 completed/success: build pass 4m34s, publish pass 2m20s
- Tested artifact 11505933117 (2.4G image.tar, build-record all ok, companion 67e15435, image e3f72af2)
- Published artifact 11506902713: candidate 6f1e3b5c, digest b1dde889, immutable ghcr.io/elmakus/pi-unraid@b1dde889, alias candidate-6f1e3b5c, image e3f72af2, source 3dfd895/b397464/feat
- GHCR independent inspect: immutable ref exists, config e3f72af2 matches tested ID
- Failed runs preserved: 37669942106/PR20 (models.json missing), 37671818998/PR21 (root-owned 0600), 37673279739/PR22 (same), 37673930175/PR23 (host Permission denied) — all closed without merge, root causes fixed via runtime-identity synthetic bootstrap (b07f0f0/2e47bd1/1c4c594/b397464) + buildx logging (5aab567)
- Allowance reverted (effcf05), default-branch-only restored, companion unchanged — no rebuild needed

## Autonomous Tower rehearsal (disposable, fake creds only, no inference/real auth/production mutation)
- Production baseline: pi-unraid-paseo-1 image 05e140da running healthy, :accepted absent (manifest unknown), guard-input unarmed (22673ae, not new candidate) — unchanged before/after
- Pull: GHCR b1dde889 -> local e3f72af2 (matches tested ID)
- Validator rehearsal (fake secret 0600 99:100, disposable net/state, fake baseUrl): companion/image_mapping/policy/registry PASS, frozen_chain PASS with full binding (SKIP minimal), real_validation_satisfied false (correct), overall FAIL due to generic structural/source readback exception (beyond rehearsal scope; isolation gates PASS, reported as limitation for independent review)
- State roundtrip PASS: baseline_clone_isolated/candidate_state_mutation/direct_skip_path/previous_runtime_reopen (sanitized clone, no HOME mount, exact IDs e3f72af2/05e140da)
- Guard M07-only armed/readback PASS: binding bacab02a, candidate b1dde889, previous 05e140da, config ebc1b352, disposable anchor, production guard absent
- Promotion isolated PASS: localhost:5500/pwv2/promotion:rehearsal 5b0745af->7dc2e94a, production false, readback matches (fixtures prove mechanics; production candidate b1dde889 remains GHCR-bound, :accepted untouched)
- Update+Verify: packaging/readback covered by M07-T06 DONE + full suite (8/8); trigger not invoked (production preserved)
- Cleanup: disposable registry/network/state/guard removed after evidence capture (see below); production container/guard/channel/ledger untouched

## Tests/readback (isolated HOME/cache, -B, direct exits, honest skips, secret scans)
- Final full suite at effcf05: 737/737 OK in 645s, Node check OK, diff check OK
- Targeted: 58/58 contracts + 14/14 build/publish + 48/48 instruction/rpc + 11/11 publish/contract GREEN at fix stages
- CI smokes for exact image e3f72af2: provenance/persistence/instruction_plane GREEN (with runtime-identity synthetic models.json)
- Secret scans: no gho_/ghp_/private keys/tokens in scripts/config/workflows/evidence; fake values redacted (synthetic disposable only, not in Git)
- Inference/live entrypoints inventoried before CI (muse_adapter/tower_validator/codex_noninference/final_gate); all exercised via fakes/disposable, no real inference/auth/ordinary credentials in CI/image/Git/logs/evidence

## Limits (for independent review)
- No M08 credential admission, real smoke, eligibility, production acceptance, guard arm/channel/cutover claimed
- Validator overall FAIL (generic exception) despite 6 isolation/binding PASS — independent review must judge rehearsal sufficiency
- Promotion fixtures are disposable (busybox/alpine), not production candidate promotion
- Evidence commits only; Board/result/review/Research Main-owned; Card remains in_progress
