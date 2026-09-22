# Research — Pi/Docker operations constraints for safe last-known-working runtime

## Durable continuation metadata

Research ID: `pi-bootstrap-operations-r1`
Status: `consumed`
Origin role: `strategic_planning`
Origin subject: `feature-pi-unraid-bootstrap:planning-R1`
Origin authority: `requirements/PI_UNRAID_BOOTSTRAP.md (pi-unraid-bootstrap@R1)`
Workstream: `feature-pi-unraid-bootstrap`
Return target: `strategic_planning:feature-pi-unraid-bootstrap:planning-R1`
Research question: `What current upstream Pi and Docker behavior must constrain a safe last-known-working Pi runtime across container recreation, candidate validation/activation and deployment-image rollback, and a bounded graceful stop of native Pi TUI processes launched through Docker exec? Verify available startup probes, session-write/shutdown semantics, Docker process/signal boundaries and state-compatibility limits; distinguish verified facts from JIT validation obligations.`
Return reconciliation: `applied`
Return reconciliation result: `planning/MASTER_PLAN.md@bc2f2cec2007a09e2d11882a2df1170879392948 (Git blob; pi-unraid-bootstrap-plan@R1)`; `planning/audits/R1.md`; `planning/reviews/R1.md (pending; same exact Review subject)`

## Scope

Bounded evidence for PIB-REQ-004/005/014/015/020/021 and acceptance 3/5/6/13/14/16/18. Existing Definition facts remain authority context. No deployment/code/prototype, credentials, Unraid host access, new product choice or later extensions. Main remains the strategic decision owner; Research is evidence only. The exact approved Definition and this durable planning obligation identify the return subject before a Master Plan exists.

Synthesized 2026-09-22 from three complementary factual lanes; not Plan Review. No model inference was executed.

## Sources / evidence (checked 2026-09-22)

- Initial snapshot: npm `@earendil-works/pi-coding-agent`, `latest=0.87.0` (published 2026-09-21); https://registry.npmjs.org/@earendil-works%2fpi-coding-agent
- Initial stable API snapshot `{"ok":true,"version":"0.87.0"}`; https://pi.dev/api/latest-version
- Release `v0.87.0` = `16787ad5b2dc748047f314ca1bfe7708f30f54f3`; https://github.com/earendil-works/pi (at initial inspection tag `v0.87.1` already existed before npm publication; Git tags alone do not establish a published stable npm candidate)
- Release permalinks under `https://github.com/earendil-works/pi/blob/16787ad5b2dc748047f314ca1bfe7708f30f54f3/packages/coding-agent/src/`: `main.ts`, `config.ts`, `migrations.ts`, `core/session-manager.ts`, `core/auth-storage.ts`, `cli/auth-command.ts`, `utils/version-check.ts`, `package-manager-cli.ts`, `modes/interactive/interactive-mode.ts`, `modes/print-mode.ts`, `modes/rpc/rpc-mode.ts`
- Scan provenance: one lane first read main `@a8ed497`; recheck found all 10 load-bearing files byte-identical to `v0.87.0`, so release is now primary
- npm v11 install/dist-tag/config semantics; https://docs.npmjs.com/cli/v11/commands/npm-install (global `{prefix}/lib/node_modules`, bins `{prefix}/bin`)
- Pi docs `quickstart`, `containerization`, `sessions`, `cli`, `session-format`, `settings`, `environment-variables`, `providers`; https://pi.dev/docs/latest/sessions
- Docker stop/exec/kill/restart/Dockerfile/run/storage/multi-service/start-automatically and Compose file/compose-stop/down/up references; e.g. https://docs.docker.com/reference/cli/docker/container/stop/ , https://docs.docker.com/reference/cli/docker/container/exec/
- Tini README (Docker-embedded init); https://github.com/krallin/tini

## Verified findings

1. **Version/install truth.** Tarball 0.87.0 (7.2 MB, 1100 files, bin `dist/bundle/cli.js`) has no package install scripts and ships `npm-shrinkwrap.json`; upstream uses `--ignore-scripts`, while usable dependency/runtime behavior still needs execution tests. Bare `npm install` follows `latest` (conventionally stable); ranges skip prereleases unless explicit.
2. **Staging vs in-place update.** Side-by-side explicit `--prefix <stage> <pkg>@<exact>` installs with PATH/symlink activation are feasible (inference from npm layout); npm itself offers no staging/rollback. Built-in `pi update` is destructive in place (`npm install -g --ignore-scripts --min-release-age=0 [--prefix <inferred>] pkg@version`, truth from pi.dev API, refused unless writable global root) with no backup/fallback; a staged binary run through it would self-update that stage. Image-baked runtime plus volume-kept state (official Docker pattern; uninstall never removes `~/.pi/agent`) makes image-seeded fallback across recreation feasible, but the project must retain a compatible working runtime outside the replaceable container writable layer.
3. **Probe/state-safety ordering.** Only `pi --version`, `pi auth ...`, `--export` exit before `runMigrations`; `--help`, `--list-models`, every session path run after. `version` proves install/Node only. `help`/`list-models` are spend-free (`allowModelNetwork/Network:false`, presence-only auth filter) but build runtime services and may migrate/rewrite state, so they must use an isolated/copied home. `auth check --no-refresh --json` proves credential presence/shape/readiness only (0/1/2); default mode can refresh expired OAuth and write `auth.json`, so auth checks are never broadly write-free. TUI health and provider/auth success need distinct runtime evidence (real TTY/caps/auth/model).
4. **Session/state compatibility.** Sessions are JSONL `CURRENT_SESSION_VERSION=3`, forward-only v1→v2→v3; opening an old session immediately rewrites it forward, while future-version files load best-effort without error/validation. Settings are lenient JSON plus in-memory renames (safest downgrade direction, still no promise). Auth validation is strict per provider and unknown credential types throw; no schema-version field. One-time migrations are forward-only without backups. No downgrade promise was found in the inspected docs, sampled CHANGELOG or sources; forward rewrite and strict auth show compatibility risk, not proof that downgrade is impossible. Retention alone is not downgrade safety: fallback means old runtime plus compatible state, so compat probes must copy state first.
5. **Shutdown/persistence.** `SIGTERM`/`SIGHUP` are handled in all Pi modes (interactive exits 0 after dispose/drain; print/RPC dispose and exit 143/129) and preserve synchronously appended completed messages plus extension cleanup, but the signal-disposal path does not provide the awaited abort/settle used in session switching, so in-flight turns may be lost. A new session file waits for the first completed assistant message; pre-first-response termination leaves no file. `--no-session` never persists; auth persists on login/refresh, not shutdown.
6. **Docker stop/exec boundary.** `docker stop` signals the container main process (PID 1) only, then `SIGKILL` after grace (default 10 s Linux; `-t`/`--stop-timeout`/`stop_grace_period`/`stop_signal`/`STOPSIGNAL` configurable). Exec sessions run only while PID 1 runs and never restart with the container. That exec Pi gets no automatic graceful fan-out is an inference from stop plus exec docs; generic init/shell/hook alone is not proven sufficient for unrelated exec PIDs. Exec-form entrypoint and/or `init:true` plus a PID-1 mechanism bounded by an explicit grace period are project-owned; exact handling, grace, and Unraid Docker/Compose versions are JIT. `pre_stop` needs Compose 2.30+, runs in the running container, never runs on self/sudden stop, and its accounting against grace is unstated; there is no requirement to add it.
7. **Rollback/restart durability.** `compose up` recreates preserving mounted volumes; `down` by default removes only service containers/networks (anonymous volumes not remounted, named only with `-v`, images only with `--rmi`); container-layer writes vanish on destroy. Bind/volume durability is preservation, not data-version rollback: rollback restores neither writable-layer changes nor versioned data, so prior image/config/runtime must stay externally selectable and volume-destroying flags excluded. `unless-stopped` returns after crash/daemon restart except after an explicit manual stop, and only after a successful start (~10 s); do not restate it as unconditional always-restart.

## Alternatives

In-place-only update without a retained runtime, mutable-tag-only rollback without a kept prior candidate, and rollback treated as data restore are inconsistent with accepted `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md` fallback/preserve requirements (sole in-place install, mutable tag, state rollback rejected on that existing evidence). Exact updater/fallback/rollback mechanics remain Strategic Planning choices.

## Limitations / JIT obligations

- Static source/doc reads only; probe, migration, stop, TUI, forward-compat, and failure behavior are code/doc-evidenced, not observed. Actual package/TUI/stop/compatibility/failure tests and target/credential checks are execution obligations.
- Future session tests must separate persisted sessions from in-flight turns and pre-first-response state (mid-stream `SIGTERM` then resume/inspect JSONL).
- Consumption-time refresh on 2026-09-22: direct npm `/latest` and Pi API both returned `0.87.1` (Node engine `>=22.19.0`); publication advanced during this work. Source-behavior findings remain explicitly pinned to inspected `v0.87.0`, not represented as an execution test or source audit of `0.87.1`. Refresh the selected release/source again at the M01/M02 JIT boundaries; docs.docker.com is rolling and Tini was read from master (both 2026-09-22); CHANGELOG sampled by grep; installer/Bun/issues out of scope; no Unraid host/daemon/Compose versions inspected.

## Analysis

No material evidence gap remains for milestone strategy. Definition intent is unchanged. Continuation belongs to the exact stored Return target `strategic_planning:feature-pi-unraid-bootstrap:planning-R1`; the workstream `routing.research_obligation` pointer stays on this record through `complete` until that target reconciles it.

Research is evidence, not accepted requirement/decision/plan authority.

## Planning reconciliation

Strategic Planning consumed these findings into the R1 draft's runtime-selection, state-compatibility, stop and image-recovery strategy (§3), milestone/JIT obligations (§4) and verification matrix (§6). Accepted Definition/decisions remain unchanged. The exact plan blob and pending review result above are persisted with this reconciliation; the Research pointer is cleared and the manifest now locates the pending independent Plan Review. Re-entry must not replay Research consumption or create another semantic plan revision.
