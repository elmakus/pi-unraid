# M05-T03 staged-update evidence

- Implementation subject: `elmakus/pi-unraid@5ff48abb0129c0708c436b2abde8197e167821d5` on `feat/paseo-gui-runtime`.
- Exact-SHA CI: [Paseo staged update/cutover/rollback run 36255547260](https://github.com/elmakus/pi-unraid/actions/runs/36255547260), GREEN. The run's `paseo-staged-update-evidence` artifact contains build records, phase records, before/after readbacks, and HOME preservation reports. CI rechecked exact predecessor result blobs before execution.
- Local and CI contract tests: 196 contract tests plus 27 candidate-resolver tests, all GREEN on the implementation SHA. The workflow checks the frozen candidate, image/runtime/Relay/instruction plane/GraphQL/host safety/doctor/inventory/control/Buildx/Tower/staged-update contracts. YAML syntax and `git diff --check` passed before the push.

## Disposable transaction readback

| Scenario | Recorded outcome and recovery | Observed state |
| --- | --- | --- |
| Successful staged update | `promoted`; preflight, build, fast checks, temporary smoke, promotion and post smoke all `ok` | Readback coherent with no mismatches; the frozen candidate image was built and retained, and the prior anchor remained available for rollback. |
| Injected temporary-smoke failure | `failed`; recovery `no_mutation`, trigger `temp_smoke`; promotion and later phases skipped | Active anchor checksum unchanged; HOME preservation report GREEN. |
| Injected post-smoke failure | `rolled_back`; recovery `rolled_back`, trigger `post_smoke`; rollback phase `ok` | Prior coherent runtime/image alias restored, readback coherent with no mismatches, HOME preserved. |

The runner exercised all scenarios against `pi-unraid-staged-*` disposable Compose projects. Four image/runtime smokes (provenance, persistence/ownership, instruction plane, global capabilities) were GREEN within the staged path. Production scope was refused, `/mnt/user/appdata/pi-unraid` was absent on the runner, and cleanup left no production mutation. The workflow separately checked readback idempotence and phase/recovery JSON.

The HOME check uses a read-only mount under the runtime identity. It retains a run-specific sentinel and compares the bytes of every seeded file by SHA-256 while checking the Relay setting and native config marker. All three scenarios reported no missing or altered seeded file and no Relay change. The seed contained two files (config marker and sentinel); the running daemon added 370 entries after initialization, which the reports list explicitly. Contract tests additionally cover pre-existing keypair/session-like files, removal/alteration, symlinks, unreadable files and destructive-restore detection. Directory mtime noise from a temporary create/delete operation was removed from the transaction's own HOME probe.

## Portability and bounds

The end-to-end Docker proof ran on the GitHub-hosted Ubuntu runner, not the Unraid production host. The accepted Tower-local Buildx/retention result remains `M05-T02B`; this Card did not rerun a Tower production cutover. Live user authentication, phone pairing, production deployment, destructive HOME restore, host reboot and Docker-engine restart were outside M05-T03. Any future production deployment and recovery checks remain owned by their later Cards and approved gates.
