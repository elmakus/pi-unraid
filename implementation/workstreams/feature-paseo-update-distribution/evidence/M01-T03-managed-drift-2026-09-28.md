# M01-T03 — managed installation drift enforcement evidence

Date: 2026-09-28  
Card: `M01-T03`

## Exact implementation subject

`elmakus/pi-unraid@d6b2ef3ffba092d202fe13a75975ea0229009fce`

Exact changed runtime/contract surfaces on that subject:
- `scripts/managed_component_lifecycle.py` blob `56c77b34598b0563a1c2f681d88fdb4cd749a563`
- `tests/test_managed_component_lifecycle.py` blob `9d0ffd6442d9f72d82fd4cc5b4b57a18bd230eb3`
- `config/pi-agent/AGENTS.md` blob `8465815e60bc783aa2d42673c8799111c88502b4`

## Scope realized

- The existing project-owned managed lifecycle helper now exposes deterministic `validate-readback`.
- Managed installation readback has a dedicated authority, `managed_installation_readback_only`, distinct from generic environment-availability observations and from registry membership authority.
- Validation compares the explicit managed-installed component set against the durable managed registry derived from each entry's `managed_update.installation_intent`.
- A registered-but-not-installed component yields RED.
- An installed-managed-but-unregistered component yields RED, with unknown installed identifiers fingerprinted in output rather than echoed.
- Explicit temporary live installs are separately represented, fingerprinted, report-only and never adopted into durable managed state.
- Malformed readback, duplicate IDs, overlapping managed/temporary IDs and unexpected schema fields fail closed.
- The CLI exits non-zero on RED drift, so build/readback callers can use it as a blocking validation gate.
- Global Pi agent guidance now directs durable extension/developer-tool/derived-component add/remove through `scripts/managed_component_lifecycle.py`, forbids manual registry membership editing, and states that direct live-container installs remain temporary unless adopted through the helper.
- No live-container mutation, resolver/discovery scheduling, build/GHCR publication, Tower production mutation, accepted-channel movement, transaction guard, DockerMan or production cutover behavior was added.

## Exact executable verification

A detached Tower worktree was reset to exact remote subject `d6b2ef3ffba092d202fe13a75975ea0229009fce`.

Targeted command:

`python3 -m unittest tests.test_environment_capability_inventory_contract tests.test_managed_component_lifecycle tests.test_pi_instruction_plane_contract`

Result: **30/30 GREEN**.

Full repository command:

`python3 -m unittest discover -s tests -p 'test_*.py'`

Result: **401/401 GREEN**, exit code 0.

The targeted suite covers:
- add/remove round-trip for `pi_extension`, `developer_tool`, and `derived_component`;
- malformed/contradictory metadata rejection and atomic write failure protection;
- exact readback GREEN;
- registered-but-not-installed RED;
- installed-but-unregistered RED;
- temporary live install report-only/no-adoption behavior;
- malformed/duplicate/overlap readback rejection;
- non-zero CLI return on drift;
- agent guidance routing.

A direct CLI exact-match readback also returned:
- authority `managed_installation_registry_consistency`;
- registry authority `managed_update_membership_only`;
- state `GREEN`;
- 12 registered / 12 installed-managed / 0 temporary;
- no missing or unregistered managed components.

## Acceptance classification

M01-T03 implementation acceptance is satisfied on the exact immutable implementation subject. Independent review is required before terminal Card completion.
