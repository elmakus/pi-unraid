# M01-T01 — Managed component registry schema evidence

Implementation subject: `elmakus/pi-unraid@6dd33c4d4744c4360b8f0211766c75c0048dad4c`

## Scope realized

- Extended the existing single `config/environment-capabilities.json` inventory rather than creating a second registry.
- Preserved `authority = environment_availability_only` for doctor/reconcile semantics and added a separate in-file `managed_component_registry` authority limited to update membership.
- Added typed `managed_update` metadata for all 12 currently approved managed capabilities.
- Represented current source kinds only: `oci`, `npm`, `github_release`, `github_tag`, `derived`, and `repository_tree`.
- Represented stable channel, immutable-identity kind, install class, update class, derived owner, and a reference to the existing capability probe.
- Added deterministic managed-registry readback through `environment_capability_inventory.py --managed-registry`.
- Did not add apt/pip/cargo adapters, component-specific scheduler workflows, update execution, add/remove mutation, candidate promotion, Tower mutation, secrets, or production cutover behavior.

## Exact changed content

- `config/environment-capabilities.json` blob `7a77aa5a07d2aa75bd454b255a22d99ffb94cdb7`
- `scripts/environment_capability_inventory.py` blob `389b81ac380a61c7c91607ffcc2d6178f83167f7`
- `tests/test_environment_capability_inventory_contract.py` blob `06861246d59f84709b8f6cd74f58bc6f04ca4001`

## Verification

Targeted contract/regression command:

`python3 -m unittest tests.test_environment_capability_inventory_contract tests.test_environment_capability_control_contract tests.test_paseo_candidate_resolver`

Result: **48/48 GREEN**.

Full repository regression on the exact implementation commit:

`python3 -m unittest discover -s tests -p 'test_*.py'`

Result: **385/385 GREEN**.

Exact registry readback:

`python3 scripts/environment_capability_inventory.py --managed-registry`

Result: **GREEN**, authority `managed_update_membership_only`, 12 deterministic component entries. The source-kind set is exactly `derived,github_release,github_tag,npm,oci,repository_tree`; `apt`, `pip`, and `cargo` are absent.

Contract tests additionally prove invalid source classes, install-class drift, and invalid derived-owner bindings fail closed, and that no credential-bearing fields are introduced.

## Acceptance classification

M01-T01 acceptance is satisfied by the exact implementation subject. The existing availability/readback authority remains distinct from update-membership metadata while both live in the same declarative inventory. Required independent review remains outstanding.
