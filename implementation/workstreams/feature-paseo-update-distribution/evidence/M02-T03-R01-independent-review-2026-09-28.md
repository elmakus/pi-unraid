# M02-T03-R01 — independent component-fallback review

Date: 2026-09-28
Card: `M02-T03`
Attempt: `R01`

## Exact subject

- Frozen result commit: `0c8a3d43ef8602cc27e417a74dcf3d6c5d7e5fed`
- Frozen result blob: `1b4b0563a92ad361065a92f48170f1a8f5359fc3`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M02-T03.md`
- Implementation subject: `2906ccdba597aaefd57cddc5cf38a0729798af3b`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M02-T03.md`

## Independence

This review context did not materially produce, reconcile or repair the exact M02-T03 implementation, evidence, result subject or frozen R01 attempt before issuing this verdict. It independently inspected the exact result binding, Card, pointed requirements/ADR/plan, implementation diff, resolver policy code and tests.

## Findings

### F1 — RED: Pareto/aggregate-lag selection is not integrated into the real resolver path

The Card and PUD-REQ-010 require complete compatible candidates to be Pareto-filtered and, when incomparable, selected by smallest equal-weight aggregate version lag followed by a deterministic technical tie-break.

The implementation adds `select_freshest_complete_candidate()` and a `select_complete_candidate()` wrapper, but the production resolver never calls either function. Repository search on the exact subject finds calls only from `tests/test_paseo_independent_resolution.py`.
A concrete counterexample against the exact subject demonstrates the material behavior: with two complete compatible core pairs, `Paseo 2.0.0 / Pi 1.0.0` (lag vector `0,2`, aggregate 2) and `Paseo 1.0.0 / Pi 3.0.0` (lag vector `1,0`, aggregate 1), `search_core_pairs()` returns the first newest-Paseo pair `2.0.0 / 1.0.0`, while the newly added accepted ranking helper correctly selects `1.0.0 / 3.0.0`. The real `resolve_live()` path still uses the former behavior because it never assembles/ranks the complete alternatives.

This is a direct acceptance defect: the new helper exists and its unit tests pass, but the required selection policy is not applied by the actual resolver.

## Positive checks and independent verification

- Independent fallback is wired into `resolve_live()` for registry-classified non-core components.
- A proven exact-identity unavailable outcome falls back only that component to its accepted identity while unrelated components advance.
- Playwright plus Chromium fall back together by restoring the accepted Playwright record.
- BLOCKED outcomes remain BLOCKED and exact-identity binding prevents stale failure evidence from poisoning a changed upstream identity.
- pi-mcp-adapter peer metadata is no longer used as a Paseo/Pi core compatibility gate.
- Exact unchanged-candidate `no_op` status is implemented.
- `python3 -m unittest tests.test_paseo_independent_resolution tests.test_paseo_core_compat tests.test_paseo_candidate_resolver -q` -> 54/54 GREEN.
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> 428/428 GREEN.
- `python3 -m py_compile scripts/paseo_independent_resolution.py scripts/paseo_core_compat.py scripts/resolve-paseo-candidate.py` -> GREEN.
- `git diff --check 2906ccd^ 2906ccd` -> GREEN.
- Frozen result blob readback matches `1b4b0563a92ad361065a92f48170f1a8f5359fc3`.

## Verdict

**RED.**

M02-T03 cannot be finalized on `2906ccdba597aaefd57cddc5cf38a0729798af3b` because the required Pareto/aggregate-lag selection is not integrated into the actual candidate-resolution path. The Card contract remains valid and the defect is bounded to the resolver/search/test surface, so corrective execution is appropriate.
