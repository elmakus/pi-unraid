# M02-T03-R02 — independent repaired component-fallback review

Date: 2026-09-28
Card: M02-T03
Attempt: R02

## Exact subject

- Frozen result commit: 1226bef3261b5ba1c3eae8e073a0918e6dbbe001
- Frozen result blob: 770e5c22b7c1fcd355d6e473e15d8ab2c287028a
- Result path: implementation/workstreams/feature-paseo-update-distribution/results/M02-T03.md
- Repaired implementation subject: 08e308bcea419f633493db52b906274bac9e677d
- Acceptance Card: implementation/workstreams/feature-paseo-update-distribution/cards/M02-T03.md

## Independence

This review context did not materially produce or repair the exact M02-T03 implementation, repair evidence, frozen result subject or R02 attempt before review. It independently recovered the current canonical router, stable Card, requirements/ADR/plan authority, R01 finding, bounded repair, implementation diff and tests.

## Review result

No blocking finding remains.

- Ordinary non-core managed components remain outside Paseo/Pi combinatorial backtracking and independently fall back only on exact proven install/build unavailability.
- BLOCKED/transient outcomes stop resolution without becoming incompatibility, and exact identity binding prevents stale failure evidence from poisoning a changed upstream identity.
- Playwright and its derived Chromium identity fall back together by restoring the previous accepted Playwright record.
- R01's defect is repaired in the real resolver path: fallback now exhaustively enumerates the bounded compatible Paseo/Pi domain, constructs complete candidates, Pareto-filters them and applies equal-weight aggregate version lag before a deterministic SHA-256 technical tie-break.
- The newest/newest fast path remains valid because zero core lag dominates every fallback alternative; fallback enumeration remains fail-closed on BLOCKED or an incomplete search budget.
- Independent fallback is applied before core fallback ranking, so every ranked core alternative contains the same already-resolved non-core state; restricting the ranking domain to Paseo/Pi therefore preserves equal-weight ordering among the actual alternatives.
- Exact unchanged candidates retain deterministic no_op reporting.

## Independent verification on exact implementation subject

Detached exact commit: 08e308bcea419f633493db52b906274bac9e677d.

- python3 -m unittest tests.test_paseo_independent_resolution tests.test_paseo_core_compat tests.test_paseo_candidate_resolver -q -> 56/56 GREEN.
- python3 -m py_compile scripts/paseo_independent_resolution.py scripts/paseo_core_compat.py scripts/resolve-paseo-candidate.py -> GREEN.
- git diff --check 08e308b^ 08e308b -> GREEN.
- python3 -m unittest discover -s tests -p "test_*.py" -q -> 430/430 GREEN from a full checkout outside the system temporary directory, preserving path-sensitive scope guards and historical Git binding tests.
- Frozen result blob readback -> 770e5c22b7c1fcd355d6e473e15d8ab2c287028a.

A preliminary full-suite run from a shallow checkout under /tmp was not accepted as verdict evidence because that environment intentionally violates a path-sensitive scope-guard test and lacked historical Git objects required by predecessor-binding tests. The full-history rerun outside /tmp is the authoritative suite result above.

## Verdict

GREEN.

The exact repaired M02-T03 subject satisfies the stable Card acceptance surface and is eligible for deterministic post-review finalization.
