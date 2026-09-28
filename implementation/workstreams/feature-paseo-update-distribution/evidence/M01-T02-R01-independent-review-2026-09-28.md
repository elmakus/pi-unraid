# M01-T02-R01 — independent managed-lifecycle review

Date: 2026-09-28  
Card: `M01-T02`  
Attempt: `R01`

## Exact subject

- Frozen result commit: `851e5775a863c24e797b99b091e6ca7c46fb8baa`
- Frozen result blob: `23221119f90d2852044ca278bdb6f45ab805554f`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M01-T02.md`
- Implementation subject claimed by that result: `0b76bf048da65158c3aaa13803d6f631fbfa1e16`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M01-T02.md`

## Independence

This review context did not materially produce, reconcile or repair the exact M01-T02 implementation, evidence, result subject or frozen R01 attempt before issuing this verdict. It independently inspected the exact result, stable Card acceptance, pointed requirements/ADR/plan, the exact implementation commit and all four changed files.

## Findings

### F1 — RED: unsupported or contradictory add metadata is silently ignored for some managed classes

The Card requires malformed/unsupported class or metadata to be rejected before any durable replacement, and its required tests explicitly call for negative coverage of unsupported class/metadata.

In `scripts/managed_component_lifecycle.py`, `_validate_common_spec()` validates required common fields and credential-bearing key names but does not reject unexpected class-specific metadata. `_managed_metadata()` then ignores fields that do not apply to the chosen class.

Concrete counterexample on the exact implementation subject: a `pi_extension` spec may include `source_kind: "pip"` and/or `installation_class: "apt_package"`. Those fields are unsupported for the class but are ignored; the helper constructs fixed `npm` / `pi_global_extension` metadata and accepts the add instead of rejecting the malformed input. The same issue applies to other unexpected class-specific fields.

The test suite checks unsupported top-level class, duplicate ID, missing derived owner and credential-bearing keys, but does not include the Card-required negative test proving malformed/unsupported metadata is rejected.

This is a direct acceptance defect, not a style issue.

## Scope and positive checks

- The helper keeps installation intent and registry membership in one declarative inventory entry and writes through a single `os.replace`.
- Add/remove round-trip coverage exists for `pi_extension`, `developer_tool` and `derived_component`.
- Existing M01-T01 availability and managed-membership authority separation is preserved.
- No live-container mutation, scheduler, candidate resolver, build/promotion, Tower, transaction-guard, DockerMan or production-cutover surface is introduced by the exact subject.

## Verdict

**RED.**

M01-T02 cannot be finalized on `0b76bf048da65158c3aaa13803d6f631fbfa1e16` because malformed/unsupported class-specific metadata is not fail-closed and the explicitly required negative metadata test is missing. The Card contract remains valid and the defect is bounded to the current helper/test surface, so corrective execution is appropriate.
