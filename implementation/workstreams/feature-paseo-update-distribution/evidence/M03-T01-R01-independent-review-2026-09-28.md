# M03-T01-R01 — independent operational-workflow review

Date: 2026-09-28
Card: M03-T01
Attempt: R01

## Exact subject

- Frozen result commit: 25719c4caffa7940898ec723e2a099f0fa3ad412
- Frozen result blob: b967d7c65055b5fc9ba79b6faae0502f1fcd1bdb
- Result path: implementation/workstreams/feature-paseo-update-distribution/results/M03-T01.md
- Implementation subject: 717172b3e23327ae87e5c7a64f89d764081c6392
- Acceptance Card: implementation/workstreams/feature-paseo-update-distribution/cards/M03-T01.md

## Independence

This review context did not materially produce or repair the exact M03-T01 implementation, implementation evidence, frozen result subject or pending R01 attempt. It independently recovered the live canonical router, stable Card, exact authority refs, predecessor result, implementation diff and exact-subject tests before issuing the verdict.

## Review result

No blocking finding was found.

- Routine discovery is now schedule + workflow_dispatch and the job is guarded to the repository default branch; the closed feat/paseo-gui-runtime automatic push activation is removed from all six historical validation workflows while manual dispatch remains.
- Candidate resolution freezes one exact candidate file and validates that same file before handoff classification; the handoff helper compares immutable candidate_id values without re-resolving.
- no_op creates no durable handoff directory/artifact/evidence/PR state beyond ordinary runner-local/log output.
- update preserves the exact frozen candidate bytes plus machine-readable identity/source evidence and updates one deterministic automation/paseo-update-candidate branch/PR.
- Concurrency uses one default-branch-scoped group with cancel-in-progress; branch replacement additionally uses an exact observed remote head with --force-with-lease so an intervening branch write fails closed instead of being silently overwritten.
- Workflow write permissions are limited to repository contents and pull requests needed for the candidate handoff. The reviewed workflow contains no build/publish, GHCR, accepted-channel, Tower, SSH or production-mutation action.
- The exact M02-T03 predecessor result commit/blob binding is verified in the workflow before resolution.

## Independent verification on exact implementation subject

Detached exact commit: 717172b3e23327ae87e5c7a64f89d764081c6392.

- python3 -m unittest tests.test_paseo_candidate_resolver tests.test_paseo_core_compat tests.test_paseo_independent_resolution tests.test_paseo_update_workflow_topology -q -> 63/63 GREEN.
- python3 -m py_compile scripts/resolve-paseo-candidate.py scripts/paseo_core_compat.py scripts/paseo_independent_resolution.py scripts/paseo_candidate_handoff.py -> GREEN.
- git diff HEAD^ HEAD --check -> GREEN.
- python3 -m unittest discover -s tests -p "test_*.py" -q -> 437/437 GREEN from a full-history checkout outside the system temporary directory.
- Frozen result blob readback -> b967d7c65055b5fc9ba79b6faae0502f1fcd1bdb.

A preliminary full-suite run from a worktree under /tmp produced 436/437 with only test_scope_guard_refuses_fixture_outside_system_temp failing because that test intentionally rejects a repository checkout inside the system temporary tree. The authoritative rerun outside /tmp passed 437/437.

## Verdict

GREEN.

The exact M03-T01 subject satisfies the stable Card acceptance surface and is eligible for deterministic post-review finalization.
