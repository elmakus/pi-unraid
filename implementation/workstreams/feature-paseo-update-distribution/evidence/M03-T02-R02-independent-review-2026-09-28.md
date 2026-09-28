# M03-T02-R02 — independent repaired build-once candidate pipeline review

Date: 2026-09-28
Card: `M03-T02`
Attempt: `R02`

## Exact subject

- Frozen result commit: `38d55095f83768404f91a2a199831feb12ec0f95`
- Frozen result blob: `b54c39bd9fad7402d2fcfca62d243691ac152e54`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M03-T02.md`
- Repaired implementation subject: `feb5762a82833e3e47e35264ea9f57a3e063d69a`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M03-T02.md`

## Independence

This review context did not materially produce, reconcile or repair the exact M03-T02 implementation, repaired result subject or R02 attempt before issuing the verdict. It independently read the canonical router and REVIEW contract, exact Card, pointed requirements/ADR/plan authority, M03-T01 dependency result, R01 finding, repair evidence, repaired workflow, regression test and candidate handoff implementation.

## Review

R01 correctly identified that the pull-request path checked out `github.event.pull_request.head.sha` while persisting `$GITHUB_SHA` as `source_head`, allowing durable provenance to name the PR merge ref rather than the exact candidate commit.

The repaired workflow now establishes one job-level `CANDIDATE_HEAD = github.event.pull_request.head.sha || github.sha`, uses it for checkout, verifies `git rev-parse HEAD == CANDIDATE_HEAD`, passes that same value to both `paseo_candidate_build.py prepare` and `package`, and uses it in the tested-image artifact name. The regression test asserts both source-head uses and forbids the old `$GITHUB_SHA` provenance path.

The bounded repair does not alter the existing build/package implementation. Source inspection confirms the Card's core invariants remain intact: candidate/evidence byte binding and default-branch-parent provenance are fail-closed; the candidate is not re-resolved; the workflow has one Buildx build invocation; core smoke runs against that loaded image; packaging rechecks the exact image ID and saves the same image as a Docker archive with machine-readable hashes; repository permission remains read-only; and GHCR push/tag, Tower access, production credentials, accepted-channel movement and production mutation are absent.

The durable repair evidence reports a clean Tower checkout at exact implementation subject `feb5762a82833e3e47e35264ea9f57a3e063d69a` with 9/9 candidate-pipeline tests and 446/446 full repository tests GREEN, plus py_compile and exact-range diff-check GREEN. This review independently verified the source-level repair and evidence binding; it did not replay Tower execution.

## Verdict

**GREEN.**

The R01 provenance defect is repaired on the exact current implementation subject, and the frozen R02 result satisfies the M03-T02 acceptance contract.
