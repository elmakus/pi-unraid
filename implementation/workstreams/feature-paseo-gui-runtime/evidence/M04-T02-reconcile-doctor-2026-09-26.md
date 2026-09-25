# M04-T02 — Environment capability reconcile/doctor evidence

Date: 2026-09-26
Card: `M04-T02`
Implementation subject: `elmakus/pi-unraid@be7dce5418b0c961bee059cbf35351f4c50feac7`

## Exact predecessor

- `implementation/workstreams/feature-paseo-gui-runtime/results/M04-T01.md@affd83590ec534ed144b9048a2b9075434761f27:5173447ec3ab8775450a9defbf193aede63ca290`
- The final CI workflow independently revalidates that exact commit/blob binding before the M04-T02 contract suite.

## Implemented surface

- Added `scripts/environment_capability_control.py` on top of the accepted `environment_capability_inventory.py`; no second desired-state store was introduced.
- `doctor` has bounded `quick` and `full` views, deterministic machine-readable JSON and concise GREEN/WARN/RED summaries. The control layer consumes only the secret-sanitized inventory payload and performs no install/delete/update action.
- `reconcile` derives canonical restore intents only for already-approved `missing` or `version_mismatch` capabilities. Unknown requested IDs are represented in errors only by SHA-256 fingerprints.
- Reconcile plans are bound to the frozen candidate and selected approved capability IDs. Readback rejects plan tampering, candidate changes, desired-state/version changes, approval/delivery/runtime/probe changes, unresolved restoration and silent disappearance of unexpected extras.
- A bounded executor hook receives only canonical `restore_desired_state` intents and must be followed by observation/readback before restoration can be claimed. Concrete SpecPi/MCP delivery remains M04-T03; coordinated version-line update/build/cutover remains M05.
- No `update` command, delete operation, OR role/action/bundle/assignment authority or PW workflow-state authority was added.
- CI now includes the new control contract and the exact M04-T01 predecessor check.

## Exact CI/readback

GitHub Actions run `36196896865`:
- head SHA: `be7dce5418b0c961bee059cbf35351f4c50feac7`
- workflow: `Paseo image and runtime foundation`
- job: `contract-build-and-smoke`
- conclusion: `success`

The job completed GREEN for:
- exact predecessor binding checks, including M04-T01;
- all existing candidate/image/runtime/Relay/Pi-instruction-plane/GraphQL/host-safety/host-doctor/environment-inventory contracts;
- `tests/test_environment_capability_control_contract.py`, including deterministic quick/full doctor behavior, missing/mismatch/unobserved/unexpected classification, secret-safe unknown IDs, bounded approved-only reconcile actions, canonical-plan tamper rejection, pre/post readback, unchanged desired authority and no silent unexpected-extra deletion;
- frozen Paseo child-image build;
- disposable image/provenance smoke;
- disposable persistence/ownership smoke;
- disposable Pi instruction-plane smoke;
- immutable foundation metadata inspection.

Observed disposable image smoke remained GREEN with candidate `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`; secret scan was GREEN.

## Boundary

No Tower/production mutation, capability approval/removal, version-line update, SpecPi/MCP installation, host-control mutation, OR policy mutation or PW state mutation was performed by M04-T02.
