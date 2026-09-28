# M01-T01-R01 — independent managed-registry review

Date: 2026-09-28  
Card: `M01-T01`  
Attempt: `R01`

## Exact subject

- Frozen result commit: `d9d6ad81fa2e8b7c531948696da8607440541fed`
- Frozen result blob: `4c513cf4617f3b1bfcb4b244039edad603fd93c2`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M01-T01.md`
- Implementation subject claimed by that result: `6dd33c4d4744c4360b8f0211766c75c0048dad4c`
- Acceptance Card blob at review time: `24edd3d4aa033c164f58090d6809af68c8cac874`

## Independence

This review context did not materially produce, reconcile or repair the exact M01-T01 implementation, evidence, result subject or frozen review attempt. It independently inspected the exact result, Card acceptance, pointed authority, implementation diff and executable readback/tests.

## Independent verification

- The frozen result blob is unchanged between commit `d9d6ad8` and the current review branch.
- Exact implementation commit `6dd33c4` changes only `config/environment-capabilities.json`, `scripts/environment_capability_inventory.py` and `tests/test_environment_capability_inventory_contract.py`.
- The existing inventory authority remains `environment_availability_only`; managed update membership is a separate in-file authority `managed_update_membership_only`.
- Deterministic managed-registry readback returns 12 managed components and source kinds exactly `derived,github_release,github_tag,npm,oci,repository_tree`.
- No `apt`, `pip` or `cargo` source adapter is admitted by the schema, and the implementation adds no scheduler/workflow surface.
- All managed entries carry source, stable-channel, immutable-identity kind, install class, update class, derived owner and probe reference metadata; derived owners resolve to existing registry members.
- A recursive credential-key scan of the declarative registry found no credential-bearing keys.
- The evidence-declared implementation blobs match the exact `6dd33c4` blobs for all three changed files.
- Targeted regression rerun: `48/48 GREEN`.
- Full repository regression rerun: `385/385 GREEN`.
- Independent negative validation additionally mutated source/install/update class fields to unsupported values and confirmed all three fail closed with `InventoryError`. This closes the Card's explicit source/install/update invalid-value readback requirement.

## Scope check

The subject does not implement add/remove mutation, drift enforcement, scheduling, candidate resolution/promotion, Tower mutation, GHCR promotion, transaction guard, DockerMan integration, secrets or production cutover. Those remain outside M01-T01 as required.

## Verdict

**GREEN.**

The exact frozen result and implementation subject satisfy the stable M01-T01 Card acceptance and its pointed authority. No material defect or scope violation was found.
