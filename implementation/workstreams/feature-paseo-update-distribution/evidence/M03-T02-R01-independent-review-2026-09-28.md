# M03-T02-R01 — independent build-once candidate pipeline review

Date: 2026-09-28
Card: `M03-T02`
Attempt: `R01`

## Exact subject

- Frozen result commit: `48ddbee949fdcec8e0d1c15c819f311d5df9fa2b`
- Frozen result blob: `afd0ee1e260b419a4e7d36bdd617beadecf885dd`
- Result path: `implementation/workstreams/feature-paseo-update-distribution/results/M03-T02.md`
- Implementation subject: `c50028af07193aeb868166a06b0c667af7a0d9cb`
- Acceptance Card: `implementation/workstreams/feature-paseo-update-distribution/cards/M03-T02.md`

## Independence

This review context did not materially produce, reconcile or repair the exact M03-T02 implementation, evidence, frozen result subject or R01 attempt before issuing this verdict. It independently inspected the canonical router/review contract, exact Card, pointed requirements/ADR/plan authority, dependency result, implementation range, final workflow/code/tests and frozen evidence.

## Findings

### F1 — RED: PR builds record the merge-branch SHA as `source_head`, not the exact checked-out candidate commit

The workflow deliberately checks out the deterministic candidate head with:

`ref: ${{ github.event.pull_request.head.sha || github.sha }}`

but both `prepare` and `package` persist:

`--source-head "$GITHUB_SHA"`

For a `pull_request` event, GitHub defines `GITHUB_SHA` as the last merge commit of the PR merge ref, while `github.event.pull_request.head.sha` is the actual source-branch head. Therefore the candidate bytes are built from one commit while the durable machine-readable provenance can record a different commit.

This violates the Card acceptance requirement for exact candidate/evidence binding and weakens the immutable handoff to M03-T03. The current static workflow test checks the checkout expression but does not assert that the persisted `source_head` is that same exact SHA, so the defect is not caught.

The bounded repair is to define one candidate-head identity from `github.event.pull_request.head.sha || github.sha`, use it for checkout, verify `git rev-parse HEAD` equals it, and pass that exact same value to both `prepare` and `package`; add a regression assertion that `$GITHUB_SHA` is not used as the candidate source-head provenance.

## Positive checks

- Candidate-only PR/manual gating and read-only repository permission are present.
- The workflow proves the candidate commit changes only the frozen candidate/evidence files relative to its parent.
- The candidate is not re-resolved in M03-T02.
- One Buildx build invocation is used, and the same loaded image is smoke-tested and then saved without rebuild.
- The bounded core smoke excludes the optional global-capability feature smoke while preserving the historical full profile.
- GHCR login/push/tag, Tower access, production accepted-channel movement and production mutation are absent from the workflow.
- The frozen implementation evidence reports 122/122 targeted tests, 446/446 full repository tests, py_compile and diff-check GREEN on the exact implementation subject. This review did not independently rerun those tests because the local sandbox could not resolve github.com; the source-level finding above is sufficient to block acceptance.

## Verdict

**RED.**

M03-T02 cannot be finalized on `c50028af07193aeb868166a06b0c667af7a0d9cb` because the durable tested-image provenance is not bound to the exact candidate commit on the normal pull-request path. The Card contract remains valid and the defect is bounded to the candidate-head workflow binding and its regression test, so corrective execution is appropriate.
