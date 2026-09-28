# M01-T02 — managed component lifecycle implementation evidence

Implementation subject: `elmakus/pi-unraid@0b76bf048da65158c3aaa13803d6f631fbfa1e16`

## Scope realized

- Added project-owned agent-facing helper `scripts/managed_component_lifecycle.py`.
- Extended each managed registry entry with explicit `installation_intent` kept inside the same declarative inventory entry as update membership.
- Add/remove therefore mutates one durable JSON authority and commits via a single atomic file replacement rather than a cross-file pseudo-transaction.
- Supported helper classes are `pi_extension`, `developer_tool` and `derived_component`.
- Helper rejects duplicate IDs, unsupported classes/source/install metadata, missing derived owners, credential-bearing spec keys and removal of an owner that still has derived dependents.
- Existing M01-T01 availability authority remains `environment_availability_only`; managed membership authority remains `managed_update_membership_only`.
- No live-container install/remove, scheduler, resolver, build, GHCR, Tower, transaction-guard, DockerMan or production-cutover behavior is added.

## Exact changed content

- `config/environment-capabilities.json` blob `27e288c07c357d7d27cc376e789c4ba1f16fb1a4`
- `scripts/environment_capability_inventory.py` blob `2ee3697135ae99f1687c4ba7348008c8646a4153`
- `scripts/managed_component_lifecycle.py` blob `4d656f44da944b711de4af4a1e10be2844797a04`
- `tests/test_managed_component_lifecycle.py` blob `25cbeeaeab6cdcef29b47343c0753cf5a1afd4b9`

## Verification on exact remote subject

Targeted command:

`python3 -m unittest tests.test_environment_capability_inventory_contract tests.test_managed_component_lifecycle`

Result: **15/15 GREEN**.

Full repository regression:

`python3 -m unittest discover -s tests -p 'test_*.py'`

Result: **392/392 GREEN**.

CLI readback:

`python3 scripts/managed_component_lifecycle.py list`

Result: authority `managed_update_membership_only`, 12 current components, intent classes `core_component,derived_component,developer_tool,pi_extension,repository_managed`.

Dry-run add of a synthetic developer tool produced a deterministic 13-component snapshot while the SHA-256 of `config/environment-capabilities.json` remained unchanged.

Failure-injection test patches `os.replace` to fail and proves the original inventory bytes remain unchanged and the temporary file is removed.

## Acceptance classification

M01-T02 acceptance is satisfied by the exact implementation subject. Required independent review remains outstanding.
