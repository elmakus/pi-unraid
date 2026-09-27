# Close — pre-integration refresh

Date: 2026-09-27  
Workstream: `feature-paseo-gui-runtime`  
Integration target: `main`

## Target refresh

- Refreshed target commit: `ca196378bc38d87f5267b870de2c5545905279d4`.
- Source head verified before this evidence-only record: `6eaac5fa05d6c9b98a9e6c88755e4974a6764773`.
- Compare result: source is 512 commits ahead and 0 behind; merge-base equals the current target commit.
- There is no target-side content/behavior drift relative to the source creation base.

## Review coverage

- Critical final production subject: `M08-T01` result `1b25ec8fd1c82c3c317dcf3fbb63193873042768:605e11fc08f563354a61a258ea8120dade11986d`.
- REQUIRED independent `M08-T01-R01`: GREEN.
- `M08-T02`: close-ready GREEN; all Card-level approved P4 obligations are terminal.

Because the integration target has not moved since workstream creation, no accepted covered product behavior is invalidated by target drift.

## Affected compatibility verification

The exact source head `6eaac5fa05d6c9b98a9e6c88755e4974a6764773` was checked in a real detached Git worktree outside system `/tmp`.

`python3 -m unittest discover -s tests -p 'test_*.py'` => **382/382 GREEN**.

An earlier archive-only run under `/tmp` produced three environment-artifact failures: two predecessor-binding tests require Git metadata and one scope-guard test intentionally distinguishes paths outside the system temp directory. Re-running the identical exact head in the required real-worktree context produced 382/382 GREEN, so no implementation defect was identified.

## Integration boundary

No production, host, HOME, backup, capability, OAuth/pairing or network state was changed during Close refresh.

The scheduled Appdata Backup residual risk remains explicitly degraded through the 2026-09-27 failed run; bounded M07 rollback/migration archives remain verified.

The exact merge subject must retain this workstream package, stable Cards, results, review evidence, M08 final ledger and M08-T02 handoff so target-side recovery does not depend on source-branch survival. OR live integration and future PWv2.1 Pi-extension packaging/bootstrap remain outside this scope.
