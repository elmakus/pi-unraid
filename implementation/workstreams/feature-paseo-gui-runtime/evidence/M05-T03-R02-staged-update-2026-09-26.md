# M05-T03 R02 correction evidence

- Implementation subject: `elmakus/pi-unraid@900fb0fdef62c21bbc3c484cc4627cd3a3e8b3ea`, correction of the two R01 RED findings recorded in `evidence/M05-T03-R01-independent-review-2026-09-26.md`.
- Exact-SHA CI: [Paseo staged update run 36258902151](https://github.com/elmakus/pi-unraid/actions/runs/36258902151), GREEN. The `paseo-staged-update-evidence` artifact holds the post-init HOME manifest, three preservation reports, state records and coherent readbacks. CI revalidated all four immutable predecessor blobs before execution.
- Tests: all 15 workflow-listed suites passed on the implementation SHA: 243 tests total, including the new restricted-HOME and protected-state regressions. Workflow YAML parse and diff whitespace checks passed locally. The hosted Docker runner completed the full disposable scenario.

## R01 findings resolved

1. **Post-init HOME seed.** CI first initialized the disposable daemon and a no-credential Relay offer, then seeded a run sentinel and representative Pi session/browser markers. The manifest contains eight actual files, including `.paseo/config.json` with Relay enabled, `.paseo/daemon-keypair.json`, `.paseo/server-id`, the sentinel, session and browser markers. Every success, pre-smoke-failure and post-smoke-failure preservation report has `ok=true`, zero missing/altered protected files, unchanged Relay state and zero newly added protected files. The 366 added volatile daemon/model files are reported separately. Tests prove deletion or alteration of each protected type fails, and a Relay flip fails.
2. **Runtime-identity HOME guard.** Preflight, temporary smoke, promotion, post smoke, rollback and readback now collect HOME metadata through the runtime UID/GID on a read-only mount. Walk, permission, transport, malformed-data or truncated-inventory failures refuse the operation. The protected digest covers identity/config/session/browser files while defined volatile daemon logs, PID, runtime caches and model downloads may change. The CI readback observed 37 HOME entries before the transaction and 433 afterward, while the protected set remained 20 entries; all three state scenarios passed the guard. Tests cover restricted mode-0700 daemon data and protected deletion/alteration.

## Transaction readback

| Scenario | Phase and recovery record | Final observation |
| --- | --- | --- |
| Success | `promoted`; preflight, build, fast checks, temporary smoke, promotion and post smoke `ok` | Coherent readback, no mismatches; prior rollback anchor retained. |
| Injected temporary-smoke failure | `failed`, `no_mutation`, trigger `temp_smoke`; promotion/post smoke/rollback skipped | Active anchor unchanged; protected HOME preserved. |
| Injected post-smoke failure | `rolled_back`, trigger `post_smoke`; rollback `ok` | Prior coherent runtime/image alias restored; coherent readback and protected HOME preserved. |

The frozen candidate image and four smoke suites were exercised on a disposable GitHub-hosted Docker runner. Production scope was refused; no Tower production cutover, interactive phone pairing, real credentials, destructive HOME restore, reboot or Docker-engine restart occurred. The end-to-end runner uses one frozen image for active/new/rollback; distinct-image behavior is covered by contract tests and later production-relevant acceptance remains outside this Card.
