# M04-T02 R01 — Independent implementation review

Date: 2026-09-26
Card: `M04-T02`
Attempt: `R01`
Verdict: **RED**

## Reviewed exact subject

- Review subject: `elmakus/pi-unraid@3064a79dee1ae48d6ea0bc5396e477bc2a514c99:implementation/workstreams/feature-paseo-gui-runtime/results/M04-T02.md@a4751b6f310a3da0a730a3b8b22940db01694b4e`
- Implementation commit named by the result: `be7dce5418b0c961bee059cbf35351f4c50feac7`
- Acceptance surface: `implementation/workstreams/feature-paseo-gui-runtime/cards/M04-T02.md`
- Frozen predecessor: `implementation/workstreams/feature-paseo-gui-runtime/results/M04-T01.md@affd83590ec534ed144b9048a2b9075434761f27:5173447ec3ab8775450a9defbf193aede63ca290`

## Independence

This review context did not materially produce, reconcile, or repair the exact R01 subject.

## Independent checks

- Revalidated the exact M04-T01 predecessor result blob and its corrected implementation subject.
- Re-read the stable Card acceptance plus the accepted Environment Capability Inventory, authority-boundary and update/reconcile/doctor requirements.
- Inspected the exact implementation snapshot at `be7dce5418b0c961bee059cbf35351f4c50feac7`, including `scripts/environment_capability_control.py`, the inventory derivation layer and the M04-T02 contract tests.
- Confirmed doctor itself performs no subprocess/network/install/delete/update mutation and emits deterministic machine-readable output plus concise GREEN/WARN/RED summaries.
- Confirmed canonical plans select only already-approved capabilities whose current drift is `missing` or `version_mismatch`, unexpected extras are report-only, plan tampering is rejected, and post-action readback is required before restoration can be claimed.
- Confirmed GitHub Actions run `36196896865` is `completed/success` on exact implementation SHA `be7dce5418b0c961bee059cbf35351f4c50feac7`, including the exact predecessor binding check and the full listed regression/smoke suite.

## Blocking finding

The Card requires reconcile to operate **only against the frozen current desired state**, refuse desired-version changes/new capability authority, and remain semantically separate from update. The exact R01 CLI does not bind its desired-state source to the repository-owned canonical inventory/candidate.

`main()` accepts user-controlled `--root`, `--definition` and `--candidate` values. `derive()` validates only the supplied documents' schema/content shape; it does not prove that they are the canonical repository-owned current desired-state files. `build_reconcile_plan()` then treats that derived payload as authority.

A bounded counterexample is therefore possible without tampering with the generated plan: copy the accepted candidate JSON, change a component desired version and candidate ID, pass that file via `--candidate`, provide a matching missing/mismatched observation, and invoke `reconcile`. The resulting canonical plan contains `restore_desired_state` for the alternate version. If before/after readback is derived from the same alternate candidate, `verify_reconcile_readback()` also accepts that candidate consistently. The existing tamper tests do not cover this authority-source substitution because they start only after a payload has already been accepted as current authority.

This is a bounded M04-T02 acceptance defect. The reconcile CLI must fail closed unless its desired-state inputs resolve to the canonical repository-owned root, inventory definition and current candidate source (or an equivalently immutable canonical binding), while observation inputs may remain external/task-provided. Contract coverage must prove non-canonical root/definition/candidate overrides cannot produce or verify reconcile actions.

## Verdict

**RED** — bounded correction inside the accepted M04-T02 authority is required before the Card can pass required independent review.
