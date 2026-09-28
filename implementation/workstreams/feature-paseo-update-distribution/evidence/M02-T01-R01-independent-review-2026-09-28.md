# M02-T01-R01 — independent typed discovery/freeze review

Date: 2026-09-28  
Card: `M02-T01`  
Attempt: `R01`

## Exact subject

- Frozen result commit: `75b2c7a77037b31857ff2b5adb2f50ae248c2e76`
- Frozen result blob: `d6fd5e657466e068cb0aa78461d892c33672cab9`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M02-T01.md`
- Implementation subject claimed by that result: `ee2addb20a2b9b25e9282264a62f6ce87005c150`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M02-T01.md`

## Independence

This review context did not materially produce or repair the exact M02-T01 implementation, evidence or frozen result subject. It independently inspected the stable Card, requirements/ADR/plan authority, exact implementation diff, tests and frozen subject.

## Findings

### F1 — RED: the new typed freeze boundary does not preserve existing provenance checks

The Card requires the typed discovery/freeze boundary to preserve existing provenance checks and to fail closed on malformed provenance. On the exact implementation subject, `typed_discovery_freeze()` validates structural identity fields but does not enforce the existing component provenance bindings that remain in the later whole-candidate `validate()` step.

Concrete counterexamples against the exact subject show that the new freeze boundary accepts and returns an npm component when its `source.repository` is changed to `attacker/example`, when its source tag is changed to `v9.9.9`, or when its npm package identity is changed to `attacker-package`. The same wrong-repository case is rejected only later by `assemble_candidate()` via the pre-existing `validate()` check (`pi source substitution rejected`).

This means the newly introduced freeze API can emit a supposedly frozen immutable component record that violates the resolver's established provenance contract. Downstream M02 cards are expected to consume this typed boundary, so relying on a later candidate-level validator is not equivalent to a fail-closed freeze boundary. The required adapter/freeze negative coverage also does not exercise these source/package substitution cases.

### F2 — scope gap: stable-source acquisition itself is still outside the typed adapter boundary

The exact diff leaves the live acquisition path (`resolve_live()` and its component-specific calls to the existing npm/GitHub/OCI helpers) unchanged. The new `typed_discover_components()` receives already-resolved full component records and re-wraps/validates them after acquisition. Thus the implementation adds a typed normalization/freeze layer, but does not actually generalize the existing stable-source acquisition into typed source adapters as required by the Card's Included scope.

This is visible in the exact diff: the only integration into candidate resolution is `comps = typed_discovery_freeze(components, definition)` inside `assemble_candidate()`; no source-kind-driven acquisition dispatch replaces or wraps the current component-specific acquisition path.

## Positive verification

- Exact-subject resolver tests: 31/31 GREEN.
- Managed registry/lifecycle regressions: 24/24 GREEN.
- Full repository unit suite: 405/405 GREEN.
- Fixture candidate identity remains deterministic and byte-stable as claimed.
- No M02-T02/T03 compatibility/fallback policy was introduced.

## Verdict

**RED.**

M02-T01 cannot be finalized on `ee2addb20a2b9b25e9282264a62f6ce87005c150`. The corrective scope is bounded to the typed discovery/freeze adapter and its tests: make the freeze boundary enforce the accepted provenance bindings itself, add the missing negative cases, and ensure current source acquisition is actually routed through the typed source-adapter boundary without introducing M02-T02/T03 policy.
