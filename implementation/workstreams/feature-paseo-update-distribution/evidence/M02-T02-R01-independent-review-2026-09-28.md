# M02-T02-R01 — independent core compatibility-search review

Date: 2026-09-28
Card: M02-T02
Attempt: R01

## Exact subject

- Frozen result commit: 7e86b22f1b4481199bbecb912e6c91beb6f0e4e8
- Frozen result blob: 38fa0c94e8afa10f8ef02a2b006b0f64868e3933
- Result path: implementation/workstreams/feature-paseo-update-distribution/results/M02-T02.md
- Implementation subject: 5378f29b1294da20053242e8c3b91a947a0e5e86
- Acceptance Card: implementation/workstreams/feature-paseo-update-distribution/cards/M02-T02.md

## Independence

This review context did not materially produce or repair the exact M02-T02 implementation, evidence or frozen result subject. It independently inspected the stable Card, binding requirements/ADR/plan authority, implementation diff, tests and frozen result binding.

## Review result

No blocking finding remains.

- Core backtracking is limited to Paseo/Pi and is deterministic newest-first inside the accepted baseline-bounded domains; non-core components are not added to this search policy.
- Node is derived from the exact Paseo image and checked against both the project floor and the selected Pi package Node engine range.
- Exact-pair nogoods bind immutable Paseo/Pi identities plus gate-definition, core-contract and platform fingerprints; changed identities/fingerprints do not reuse stale entries.
- Only proven incompatible gate outcomes carrying durable evidence can be recorded; BLOCKED/transient outcomes raise without poisoning the cache.
- Infrastructure/network failures propagate as BLOCKED and the optional operational search budget reports RESOLUTION_INCOMPLETE rather than claiming a compatible fallback.
- The exact frozen result blob matches the Task Board locator and the implementation subject is an ancestor of the frozen result commit.

## Independent verification on exact implementation subject

Detached exact commit: 5378f29b1294da20053242e8c3b91a947a0e5e86.

- python3 -m unittest tests.test_paseo_core_compat tests.test_paseo_candidate_resolver -q -> 43/43 GREEN.
- python3 -m py_compile scripts/paseo_core_compat.py scripts/resolve-paseo-candidate.py -> GREEN.
- git diff --check -> GREEN.
- python3 -m unittest discover -s tests -p "test_*.py" -q -> 417/417 GREEN from a checkout outside the system temporary directory, preserving the path-sensitive temp-scope contract.
- Frozen result blob readback -> 38fa0c94e8afa10f8ef02a2b006b0f64868e3933.
- Implementation subject ancestry to frozen result commit -> GREEN.

## Verdict

GREEN.

The exact M02-T02 subject satisfies the stable Card acceptance surface and is eligible for deterministic post-review finalization.
