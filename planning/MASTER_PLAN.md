# Pi on Unraid — Phase 1 Master Plan

Plan revision: `R1`
Plan subject: `pi-unraid-bootstrap-plan@R1`
Status: `draft`
Definition subject: `pi-unraid-bootstrap@R1`
Workstream: `feature-pi-unraid-bootstrap`
Branch: `feat/pi-unraid-bootstrap`
Strategic author: `Codex — Strategic Planning`, as assigned by `PIB-ADR-004`
Independent plan review: `REQUIRED`
Planner audit: `planning/audits/R1.md`
Independent review record: `planning/reviews/R1.md`
Date: `2026-09-22`

## 1. Authority, goal and verified baseline

Organize the approved Phase 1 Definition into a reproducible minimal Pi Coding Agent bootstrap on Unraid: native terminal/TUI use, one directly authenticated ChatGPT Plus/Pro account, durable home/session state, ordinary Git/GitHub development and recoverable operations. This plan adds execution organization inside accepted intent; it does not approve new product or high-level architecture decisions.

Authoritative inputs:

- `requirements/PI_UNRAID_BOOTSTRAP.md`, revision R1, approved; every requirement and all 19 acceptance-level outcomes remain binding.
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md` — Phase 1 scope and user-owned later evaluation.
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md` — native persistent home, non-root runtime, mounts, tooling and backup boundary.
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md` — latest stable on service start, runtime fallback, independent image rollback and one update operation.
- `decisions/PIB_ADR_004_WORKFLOW_ROLES.md` — Codex strategic author; fresh normal ChatGPT reviewer; downstream `chatgpt_only` policy.
- `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md` — Definition's verified installation, OAuth and native session facts.
- `research/PI_UNRAID_BOOTSTRAP_OPERATIONS_R1.md` — bounded planning Research for lifecycle, validation and recovery constraints; evidence, not accepted intent.

Definition baseline: project commit `86e8c57f7c1f1d3bf660d5aeb5df5c36f4a97643`. The repository contains Definition/decision/research/brainstorming/workstream documents only. No deployment code, Dockerfile, Compose source, automated tests, Task Board or Task Cards exist at this baseline. No working Unraid deployment, login, rollback or host-ownership result has been demonstrated by this planning session. The historical brainstorming is provenance; it is not a source of additional Phase 1 requirements.

Workflow baseline: current remote `main` of `elmakus/chatgpt-codex-project-workflow`, verified at `7aa7512ead67a86256089d1af0171e2e655e700d`. Applicable contracts: `workflow/common/AUTHORITY.md`, `workflow/common/RESEARCH.md`, `workflow/common/OPENSPEC.md`, and `workflow/chatgpt_only/{ROUTER,WORKSTREAMS,PLANNING,RESEARCH,PLAN_REVIEW}.md`. Future entries re-resolve current workflow main; this provenance does not pin future workflow behavior.

The Definition fixes the native package/path model and documents Node >=22.19, with Node 24 Debian guidance as the verified baseline. Execution must recheck the then-current supported stable package/runtime combination; neither a floating image tag nor a remembered version is reproducibility evidence.

## 2. Scope and invariants

Phase 1 implements only the accepted Docker/Compose bootstrap and operational support. All Definition non-goals apply, including Web UI, Android/PWA, ingress/proxy, uploads, web search, subagents, MCP, browser automation, compaction extensions, notifications, provider/account routing, Muse, `chatgpt-web/*`, Project Workflow-on-Pi, broad host administration and automated project creation. No real coding benchmark is an acceptance gate. Later research begins only after the user's own base-Pi evaluation and decision.

Execution must preserve these boundaries throughout every milestone:

1. `compose.yaml` is deployment source of truth. Repository/image source captures the normal expected environment, including tools first tried interactively and then adopted.
2. Host `/mnt/user/appdata/pi-unraid/home` maps to `/home/pi`; native `~/.pi/agent` contains Pi auth/settings/sessions. Do not relocate native state merely to simplify scripts. Keep the entire home in the ordinary Unraid appdata backup scope, including ordinary interactive credential stores; add no special backup exclusion or encryption requirement.
3. `/mnt/user/projects` maps to `/projects`; `/mnt/user/pi-worktrees` maps to `/worktrees`. Normally each canonical Git repository is one level below `/projects`. Explicit working-directory selection must be honored; startup must not modify mounted repositories or invent branch/worktree lifecycle rules.
4. Pi and normal development commands run as the configurable non-root service UID/GID. Sudo remains available for legitimate container-local tools. If a short privileged initialization step is necessary, bound it to account/mount preparation and drop privilege before normal operation. Do not recursively change ownership of existing projects/worktrees or overwrite a working home.
5. No Docker socket, host-root or unrelated-appdata mount; no inbound SSH daemon for shell access. Maintain ordinary outbound networking, persistent configurable Git identity, strict GitHub SSH host verification and persistent `known_hosts`. `gh` supports normal authorized API/PR/check/release work without new per-command local approval gates.
6. Pi runtime binaries and Docker images are replaceable; durable home/repositories/worktrees are not rollback payloads. Updates, retries, crashes and rollbacks must preserve them. No secrets in Git, image layers, diagnostics or acceptance artifacts.
7. Normal startup seeks latest stable Pi only. Failed candidate selection/install/start must preserve an immediately usable previously working runtime when available. Image rollback is a separate mechanism and must remain usable when new entrypoint/dependencies are broken.
8. `unless-stopped`-style availability, `Europe/Zurich`, bounded logs and bounded graceful shutdown are required. A running container or `pi --version` alone does not prove usable Pi or graceful session handling.
9. `chatgpt-ce-workstation` stays independent and unchanged: no dependency on its service, credentials, routing, mounts or availability. Existing repository data is not test collateral.

## 3. Execution strategy and operational seams

The following are implementation-shaping obligations within ADR-002/003, not new product choices. Exact paths for project-owned metadata, script internals and probe interfaces are JIT details. Use ordinary Docker/Compose, native Pi, files and bounded process handling before adding machinery.

### 3.1 Reproducible base and native access

Build a repository-owned image with a supported Node runtime and the complete accepted tool set: Python, Git, OpenSSH client, GitHub CLI, curl, jq, ripgrep, fd/find tooling, archive utilities, standard build toolchain and Git LFS. Record resolved image/package versions and image identity in build evidence. Include a tested stable Pi seed so initial empty-home startup does not depend on successfully downloading a new candidate at that instant.

Initialize only missing service-home/runtime scaffolding. Validate UID/GID and access to the three exact mounts, including reused-home and changed-UID cases; give an actionable failure instead of silently taking ownership of unrelated files. Native `pi` must resolve in the service user's normal interactive environment when entered through Unraid/Docker exec. Document explicit user, home and working-directory selection; do not rely on exec inheriting a prior shell's cwd.

Normal Git/GitHub setup uses the user's chosen identity and credentials in the persistent home. Verify GitHub host keys against an authoritative GitHub source before enrollment; unverified `ssh-keyscan` output is not trust evidence. Do not disable checking to make initial setup pass. Test SSH Git transport separately from `gh` API authentication. Credential values, OAuth redirects/codes and private keys stay out of evidence.

Existing linked Git worktrees need a path-consistency check ([upstream Git worktree documentation](https://git-scm.com/docs/git-worktree), inspected 2026-09-22): their `.git`/`gitdir` references may contain host paths that do not resolve under `/projects` and `/worktrees`. Before selecting a real test worktree, verify bidirectional Git metadata resolution. Do not silently remap the requested workspace or rewrite other repositories' metadata. A bounded compatibility solution inside accepted mounts is an L1/L2 detail; a solution needing new mounts or altered accepted layout returns to Definition.

### 3.2 Pi runtime selection and recovery

Retain replaceable, version-identified runtime candidates outside the native auth/session tree but within accepted storage. Their recorded compatibility includes the image/Node/platform context; an old native dependency tree is not assumed portable across a changed base image. Preserve a known-working candidate across restart/recreation; also keep the tested image seed. Staging must not overwrite the only working runtime or mutate native live state before candidate admission. The managed update path must not call Pi's in-place self-updater against a retained candidate; document/protect that boundary in the normal entry path without inventing per-command Git/tool approval gates.

Required semantic sequence:

- At normal service start, resolve the published npm stable distribution (`latest` plus concrete package/version metadata, not the newest Git tag) and verify the selected concrete version is not a prerelease/nightly and satisfies the actual Node/runtime constraints. Bound resolution/download/probe time; offline or invalid metadata cannot stall fallback indefinitely.
- Stage an explicit version with enough dependency/version metadata to reproduce or identify it. Validate package integrity and a real startup path with an isolated disposable home/session fixture, not live credentials; a version/help command is only a cheap preliminary check.
- Validate the state-compatibility and graceful-exit obligations identified by operations Research. A newly installed package is a candidate, not automatically last-known-working. Distinguish runtime startup failure from missing credentials, provider quota or transient network failure.
- Activate only a complete validated candidate through an interruption-safe selection step. Serialize overlapping start/update operations, and prevent removal of runtime files still used by a Pi process. Failed/cancelled staging leaves the working selection intact; incomplete staging is never mistaken for ready state after restart.
- On install/start/validation failure select the retained compatible working runtime, or tested image seed where appropriate, and emit readable degraded/fallback diagnostics with attempted/selected versions and cause. If neither works, report an explicit unavailable state and a recovery path; do not claim success because the service holder remains alive.
- Retain the previous working runtime until the new one has met its promotion checks. Bound cleanup to obsolete project-owned candidates; never clean Pi auth/session/config or user files as part of runtime retention.

A rollback must not immediately retry and reactivate the same failed candidate. Provide a bounded, explicit recovery selection usable by both native entry and the host-side rollback path; normal starts return to latest-stable targeting when recovery selection is intentionally cleared. This exception implements recovery, not an automatic permanent pinning policy.

State compatibility is an admission/test obligation, not an assumed upstream downgrade guarantee. Use representative native session/config fixtures and reversible, isolated checks for the candidate/fallback pair. Before first candidate use against an existing home, check relevant existing-state compatibility on a protected disposable local copy with provider/network activity disabled; do not print or export credentials. No-cost probes may still migrate state. Reject a candidate whose observed state effects make the retained fallback unusable, and preserve the working live state. Never restore an old live home merely to make old binaries run. If observed upstream behavior makes accepted no-loss/resumability guarantees infeasible, stop affected work for Research/Definition; do not silently weaken them. Compatibility evidence cannot prove all future upstream releases safe.

### 3.3 Process lifecycle, stop and logs

The native terminal path and the service lifecycle must form one coherent stop contract. Account for Pi instances launched through Docker exec and any running children; Docker stopping its main process is not, by itself, proof that these TUI processes received a graceful request.

Operations Research found native SIGTERM/SIGHUP handling but no guarantee of settling every in-flight turn; new sessions may remain memory-only before their first assistant completion. These are acceptance-test distinctions, not permission to discard already-persisted sessions. Before implementation, freeze a small process/shutdown contract from the exact current Pi/Docker evidence. Planned restart/update closes admission of new managed Pi starts, requests the supported graceful path for each active Pi process, waits within an explicit finite inner deadline, then escalates if necessary. Configure the Docker/Compose outer stop grace to permit that inner sequence. No indefinite shutdown and no silent claim that forced termination saved every in-flight operation.

Previously persisted native sessions must remain resumable, including after timeout escalation. Demonstrate an orderly active-session stop and a deliberately non-cooperative-process timeout separately. Include a session with a completed saved exchange, an in-flight turn and a pre-first-response session; prove the accepted persisted-session guarantees and report the native limits of the latter two honestly. A minimal authenticated exchange is a functional persistence test, not a coding benchmark. Preserve completed conversation records; interrupted external work is not made transactional by the shutdown wrapper. Exact signals, process registration/forwarding, deadlines and PTY behavior are JIT details established against actual runtime evidence, not assumed from a generic init example.

Use bounded Docker/backend log rotation and readable start/update/stop/fallback diagnostics. Session history is durable product state, not a log-retention target. Do not add a metrics stack, daemon or web endpoint just to report readiness.

### 3.4 One update path and separate image rollback

Provide one normal user-facing repository/image/deployment update operation, run from a host-authorized deployment context. It must not require a Docker socket inside Pi. Lower-level Compose recovery/development commands remain documented.

The operation identifies the current repository revision, rendered deployment settings and immutable image/candidate before replacement; preserves a known-working previous deployment candidate; validates/builds the proposed candidate before disrupting the running service where possible; uses the graceful-stop contract; recreates with the unchanged persistent mounts; and proves service/Pi readiness. A failed candidate must leave or restore the working deployment without deleting durable data. Protect local deployment configuration and refuse ambiguous/dirty-source replacement rather than resetting user work.

Rollback must be possible from outside the failing container even when its startup/update code cannot run. Select the previous image together with its compatible deployment configuration and working-runtime selection, without requiring a new download/build or allowing the ordinary startup updater to immediately undo recovery. Retain recoverable image identity/artifacts before cleanup; a mutable tag is not sufficient evidence of retention. Pruning must not delete the last usable rollback candidate.

There is no previous deployed image on first installation. Bootstrap from the tested seed, establish the first known-working deployment after baseline startup, native-session and persistence checks, then test a second candidate and rollback before full M03 acceptance. Do not label an untested first build as a proven previous deployment. Do not roll back home/auth/session data with binaries. Document owner-controlled restore from existing appdata backups only for actual data damage; destructive restore is never an automatic update/fallback step.

## 4. Milestones and planned work packages

Dependency chain: **M01 → M02 → M03**. M01 establishes the testable base; M02 proves failure handling before live use; M03 proves the complete contract on the target. Work-package labels below are plan references, not Task Cards, execution state or executor assignments.

### M01 — Reproducible non-root development environment

**Outcome:** repository-owned image/Compose and documented native access can produce the accepted isolated environment using disposable mounts, without modifying a live Unraid service.

**Owner requirements:** PIB-REQ-001/002/003/006/007/008/009/010/011/012/013/016/018. Final target-specific proof also occurs in M03. All section 2 invariants and ADR-001/002 apply; runtime seeds must remain compatible with ADR-003.

**Dependencies/gates:** approved exact plan after independent review; concrete Execution Prep/Refresh Gate; a permitted build/test surface with disposable data. No live-home, credential, existing-repository or host-restart action is implied by this milestone.

**Planned packages:**

- **M01-W1:** reproducible base image and stable seed, complete tool inventory, resolved-version/build evidence and policy for promoting adopted runtime tools into source.
- **M01-W2:** Compose mounts/restart/timezone/logging foundation; non-root UID/GID/sudo and idempotent home initialization; safe filesystem/permission diagnostics.
- **M01-W3:** native exec/TUI entry and operator setup documentation for explicit cwd, projects/worktrees, SSH trust/identity, `gh`, independent credentials and ordinary appdata backup scope. Establish disposable Git/worktree fixtures.

**Checkpoint:** build succeeds; required tools and seed are usable as service user; UID/GID and sudo work as intended; repeated startup preserves an existing fixture home; selected repo/worktree writes have expected ownership; explicit cwd and linked-worktree Git metadata resolve; negative configuration inspection confirms only accepted mounts/no inbound SSH; timezone/restart configuration and backup source are explicit. No live OAuth/GitHub or Unraid-reboot success is claimed from fixtures.

**Evidence:** exact source/image/package identities, build/tool checks, resolved Compose inspection, numeric uid/gid and fixture ownership, initialization before/after checks, workspace-selection observations and setup/backup instructions. Use synthetic state without secrets. Record the initial proposed signal/process and runtime-packaging seams for M02 without claiming the later lifecycle contract already passes.

**JIT trigger:** current source/official package/runtime facts and permitted Docker builder are known at M01 prep. Choose concrete base/digests, package versions, UID configuration, startup mechanism and minimal tests then. Before coding, evaluate whether initialization/permissions need a small OpenSpec contract; freeze it if persistence/security ambiguity spans packages.

### M02 — Recoverable runtime and deployment lifecycle

**Outcome:** the full bootstrap operates and fails safely in an isolated Docker test environment, including native TUI process shutdown, stable-runtime fallback and host-operated image rollback/update.

**Owner requirements:** PIB-REQ-014/015/017/020/021. Integrates M01 persistence/security/availability requirements and prepares M03 authentication/session proof. ADR-002/003 and all invariants apply.

**Dependencies/gates:** M01 accepted evidence and usable fixture image; refreshed exact Pi/Docker lifecycle and state behavior; fixture-only failure injection. No production disruption or credentials are required to fault-test the lifecycle. Use synthetic native session fixtures for this checkpoint; a real authenticated exchange/resume is proven in M03.

**Planned packages:**

- **M02-W1:** staged stable-candidate selection, persistent working-runtime retention, startup validation/activation and bounded failed-update fallback/recovery selection.
- **M02-W2:** native entry/process ownership, graceful-stop and timeout escalation, readiness and bounded diagnostics/log rotation.
- **M02-W3:** the single normal update operation, external previous-image/deployment rollback, preservation/cleanup boundaries and operator recovery runbook; integrated failure-injection verification.

**Checkpoint:** the fixture-applicable §6 operational scenarios are demonstrated against real packaged Pi where relevant and deterministic failure fixtures where upstream faults are needed. Live OAuth, actual Unraid/host restart and workstation observations remain M03 obligations. Fallback works after container removal/recreation, not just process restart. A deliberately broken candidate image can be recovered using retained external artifacts. Stop handles exec-launched active Pi and a non-cooperative process within the documented bound; saved native state remains readable/resumable. No stale successful status masks unavailable Pi, and no rollback silently changes native state or reselects a known failed candidate.

**Evidence:** exact old/new image and Pi identities, rendered deployment/config identity, fixture state before/after, failure/activation outcomes, process-stop timing and session-resume observations, update/rollback command results and log-rotation configuration/behavior. Passing mock-only tests cannot substitute for packaged-Pi TUI/persistence tests.

**JIT trigger:** M01 evidence supplies actual packaging/path/user/process seams. Reconcile operations Research against current sources before selecting probes, graceful signals/deadlines and state-compatibility checks. Create/reconcile OpenSpec just before implementing the runtime selection/promotion/fallback state contract and process/update/rollback contract; these may be one small change if cohesive. Split real Cards only when their boundaries are knowable. If facts invalidate feasibility or require new accepted layout/behavior, use Research/Definition instead of an invented workaround.

### M03 — On-Unraid acceptance and recoverable user handoff

**Outcome:** the complete Phase 1 deployment is proven on the actual Unraid target, independently accepted through the project's execution/review lifecycle, and available for the user's own Pi evaluation.

**Owner requirements:** PIB-REQ-004/005/019; final integrated acceptance for every M01/M02 requirement and all acceptance outcomes in §5. All accepted decisions and invariants apply.

**Dependencies/gates:** accepted M02 evidence and recovery runbook; target readiness and explicit authority for concrete installation/update/restart/test effects. Recover any existing valid authorization before asking again. Before disruptive host/Docker restart, confirm the permitted window and affected services; a Docker-wide/host restart can affect the independent workstation even though this project does not modify it. Credential entry belongs to the account owner through the native login/auth paths. Use deliberately selected disposable repository/remote/worktree for writes.

**Planned packages:**

- **M03-W1:** target readiness: actual Unraid/Docker/Compose/CPU/filesystem facts, existing path ownership and backup inclusion, collision-free service/config, preserved rollback artifacts; initial deployment and native headless login.
- **M03-W2:** persistent auth/session create-exit-resume across restart and recreation; explicit project/worktree use, SSH and `gh` proof, required tools, user/permissions/network and negative isolation checks.
- **M03-W3:** normal update, real retained-image rollback, safe runtime-fallback demonstration and planned-stop/resume; authorized host/Docker restart availability check; bounded logs and workstation independence; consolidated acceptance/recovery handoff.

**Checkpoint:** every §5 acceptance row has a passed outcome with exact evidence, or remains visibly incomplete. No simulation-only replacement for host restart, OAuth persistence or real image rollback. Restart-policy proof preserves `unless-stopped` semantics: explicitly stopped services need not restart automatically. Operator can reproduce normal update and recover the retained deployment; home/repositories/worktrees are preserved. User's later coding evaluation is explicitly separate from technical acceptance and does not open extension scope automatically.

**Evidence:** immutable deployed source/image/Pi/Node identities and sanitized configuration, target version/architecture, ordered restart/recreate/update/rollback observations, service-user/mount/port/process checks, session IDs or sanitized fixture markers rather than transcripts/secrets, authorized test repository reference, Git/gh operation results, backup-scope and workstation-independence observations, final coverage/evidence index and operator instructions.

**JIT trigger:** accepted M02 artifacts plus read-only target readiness determine concrete installation/update commands, actual compose launcher, approved restart method/window, numeric UID/GID, test repositories, native credential actions and evidence locations. Do not invent these values now. A selected worktree with unresolved host-path metadata must be fixed within authority or left blocked before claiming its acceptance. Missing access/approval leaves relevant live acceptance incomplete; it is not permission to weaken requirements.

## 5. Complete coverage

Each owner milestone must receive concrete Task Card coverage from Execution Prep before implementing its requirements. Planned packages below supply the execution path; §4 JIT triggers supply details. M03 re-verifies the integrated target even where M01/M02 owns implementation. No speculative Card IDs are created by this plan.

### Requirement ownership

| Requirement | Owner / planned path | Required proof |
|---|---|---|
| PIB-REQ-001 | M01 / W1-W2 | Repository build and Compose truth; on-Unraid start in M03. |
| PIB-REQ-002 | M01 / W2 | Exact persistent non-root home/native Pi path; restart/recreate preservation in M03. |
| PIB-REQ-003 | M01 / W2 | Configurable numeric UID/GID, normal non-root writes and working sudo. |
| PIB-REQ-004 | M03 / W1-W2 | One direct Plus/Pro native login; same auth after restart/recreation. |
| PIB-REQ-005 | M03 / W2-W3 | Native session create, exit, resume and continued use after lifecycle events. |
| PIB-REQ-006 | M01 / W2-W3 | Exact /projects mount, normal direct-child repository and selected-cwd writes. |
| PIB-REQ-007 | M01 / W2-W3 | Exact /worktrees mount; existing linked-worktree path/metadata and selected-cwd operation. |
| PIB-REQ-008 | M01 / W1 | Complete accepted tool inventory, supported Node and Git LFS. |
| PIB-REQ-009 | M01 / W3 | Persistent verified known_hosts, strict SSH Git transport and gh capability; live M03 proof. |
| PIB-REQ-010 | M01 / W2-W3 | Persistent configured Git identity, outbound access, authorized Git/gh actions without new local per-command gates. |
| PIB-REQ-011 | M01 / W2 | Negative rendered/live mount and process/service inspection; no prohibited mounts or SSH server. |
| PIB-REQ-012 | M01 / W3 | Native terminal/TUI through Unraid/Docker exec, also usable during recovery. |
| PIB-REQ-013 | M01 / W2 | Europe/Zurich and unless-stopped configuration; authorized target restart behavior in M03. |
| PIB-REQ-014 | M02 / W1 | Stable-only resolution, attempted/selected exact versions, failed install/start fallback after recreation. |
| PIB-REQ-015 | M02 / W3 | Retained previous image/config/runtime candidate; external rollback preserving all durable mounts. |
| PIB-REQ-016 | M01 / W1-W3 | Normal adopted tools captured in image/repo; recreate tool-inventory proof and documented adoption path. |
| PIB-REQ-017 | M02 / W2-W3 | Explicit bounded rotation/retention and readable failure/recovery diagnostics. |
| PIB-REQ-018 | M01 / W2-W3 | Whole-home backup scope including normal credential stores, no Pi-specific exclusion/encryption gate. |
| PIB-REQ-019 | M03 / W1-W3 | No workstation dependency/config/secret changes; baseline and post-acceptance independence evidence. |
| PIB-REQ-020 | M02 / W3 | One documented executable normal update path, proven in M03; lower-level recovery remains available. |
| PIB-REQ-021 | M02 / W2-W3 | Bounded graceful stop of active exec-launched Pi, escalation test, saved-session resume after restart/update. |

### Acceptance-level outcomes

`A01`–`A19` below are local cross-reference labels for the Definition's numbered acceptance list, not additional requirements. M03 owns final on-target sign-off for all rows.

| Definition outcome | Establishing milestone/package | Outcome-level evidence obligation |
|---|---|---|
| A01 (1) | M01-W1/W2 → M03-W1 | Exact repository-owned deployment builds and starts on Unraid. |
| A02 (2) | M01-W2 → M03-W3 | Running service returns after authorized host/Docker restart; explicitly-stopped exception understood. |
| A03 (3) | M01-W1/W3, M02-W1 → M03-W1 | Real TUI on supported Node, exact stable Pi; fallback separately identified. |
| A04 (4) | M03-W1 | Owner completes native one-account headless login; no inbound UI/SSH service required. |
| A05 (5) | M03-W2 | Auth works after both normal restart and image/container recreation preserving home. |
| A06 (6) | M03-W2/W3 | Create, exit and resume native persisted session after restart/recreation; correct working folder. |
| A07 (7) | M01-W2/W3 → M03-W2 | Deliberately selected /projects repository read/write with acceptable host ownership. |
| A08 (8) | M01-W3 → M03-W2 | Explicit existing /worktrees worktree operation with valid Git references and no silent remap. |
| A09 (9) | M01-W3 → M03-W2 | SSH Git read/write on authorized test remote plus gh authenticated ordinary API operation. |
| A10 (10) | M01-W3 → M03-W2 | Strict verified GitHub host trust; wrong-key test safely fails in isolated fixture. |
| A11 (11) | M01-W2 → M03-W1/W2 | No Docker socket/root/unrelated-appdata mounts and no inbound SSH shell daemon. |
| A12 (12) | M01-W1 → M03-W2 | Every accepted tool is present and usable, including Git LFS. |
| A13 (13) | M02-W1 → M03-W3 | Failed latest-stable install/start falls back to working Pi with native state preserved. |
| A14 (14) | M02-W3 → M03-W3 | Actual prior deployment candidate selected and runs without durable-data rollback/loss. |
| A15 (15) | M02-W2 → M03-W3 | Bounded retention config and observable rotation behavior; readable diagnostics. |
| A16 (16) | M02-W3 → M03-W3 | Operator executes the documented single normal update path successfully. |
| A17 (17) | M03-W1/W3 | Workstation configuration/runtime integration unchanged; independent operation confirmed. |
| A18 (18) | M02-W2/W3 → M03-W3 | Planned restart/update grants bounded graceful opportunity; persisted session resumes afterward. |
| A19 (19) | M03-W3 | Technical evidence handoff records no mandatory coding benchmark; later evaluation/scope decision remains user-owned. |

## 6. Verification and recovery obligations

Keep a durable evidence index in the selected workstream's `evidence/`/`handoffs/` once execution produces real evidence. Every result identifies source/image/runtime/config, context (fixture or actual Unraid), expected versus observed result, and limitations. Record failures and skipped/blocked checks explicitly. No raw auth stores, private keys, OAuth codes or private session content belong in Git. Do not assert deployment success in planning artifacts.

The integrated test matrix must cover:

| Scenario | Expected safety/result |
|---|---|
| Empty and already-populated home; repeated starts; valid/invalid/changed UID/GID | Idempotent owned initialization; no overwrite or sweeping ownership change; actionable permission failure. |
| Online stable startup; prerelease/malformed candidate; unsupported Node engine | Admit only compatible stable runtime; record exact attempt/selection; preserve working selection on rejection. |
| Offline/timeout; partial download; install or startup failure; full/unwritable runtime storage | Bounded attempt; retained runtime/seed usable without network; native state unchanged; explicit unavailable state if no viable fallback. |
| Interruption before/after activation; two overlapping update/start attempts | No incomplete runtime selected; deterministic recoverable selection and serialized mutation; no loss of only working candidate. |
| Real TUI startup/exit and session fixtures; previous/candidate pair | Startup probe exceeds --version; native persistence and compatible resume proven without live secrets in tests. |
| Active Pi launched by exec; normal stop; uncooperative process | Graceful request reaches intended instances; bounded completion/escalation; saved session remains resumable; no false claim for unpersisted/in-flight work. |
| Container restart and removal/recreation with preserved binds | Auth/settings/sessions, Git identity/trust/config and retained working runtime survive; same selected workspace. |
| Normal update; build failure; broken new entrypoint/dependency/image; rollback while offline | Prior image plus compatible config/runtime remains externally selectable; mounts unchanged; failed newest version not immediately reselected. |
| Wrong SSH host key; explicit repo/worktree; invalid linked-worktree paths | Host-key mismatch fails safely; correct cwd/ownership; no metadata rewrite or substitute workspace without authority. |
| Sustained backend output; negative mount/process inspection | Rotation bounded and diagnostics readable; no extra privilege/mount/service introduced. |
| Actual authorized host/Docker restart; workstation independence | Restart policy behavior proven; no dependency on workstation and no project-owned changes to it. |

Use proportionate static checks for rendered Compose/build recipes, real disposable Docker integration for process/filesystem behavior, and on-target checks for Unraid-specific facts. Keep external Git tests scoped to a disposable authorized remote; test `gh` capability with a harmless authorized operation rather than creating real PRs/releases solely as a benchmark.

Operational recovery distinguishes three cases: (1) failed Pi candidate → retained compatible runtime/seed; (2) failed deployment image/config/startup → external previous deployment rollback; (3) actual persistent-data damage → stop writes and the user's existing backup/restore authority. Case 3 is not an automatic rollback mechanism. Evidence must show no auth/session/repository/worktree data is restored backward in cases 1–2.

## 7. JIT authority, review and continuation boundaries

Execution Prep owns real Task Cards and the one manifest-selected Task Board under the exact workstream. No cards/board or separate milestone documents are produced by Strategic Planning. These milestone sections are the default milestone contracts; add a milestone file only if JIT preparation needs materially new execution detail.

Each requirement gets at least one concrete Card before its implementation. Follow current `workflow/chatgpt_only/EXECUTION_PREP.md` and `TASK_CARDS.md` for decomposition and Refresh Gate, `workflow/common/OPENSPEC.md` for selective behavior/state/security contracts, and policy-local execution/review/close modules when those roles become current. Do not load or import `codex_only` execution rules.

- **L1:** concrete packaging, script internals, supported probes, timeout values and test mechanics inside accepted contracts.
- **L2:** split/merge/reorder not-yet-started Cards, refine technical acceptance and optional milestone detail from exact predecessor evidence. This cannot change the plan's accepted milestone outcomes or safety obligations.
- Changed execution strategy/milestone structure within unchanged Definition returns to Strategic Planning.
- Changed requirements, layout, product behavior, invariants or authorization boundaries returns to Project Definition/user authority. Missing material facts uses a durable Research obligation with exact owning return target; implementation-owned Research belongs to its Task Board, not this pre-execution manifest pointer.

Required fresh boundary now: independent Plan Review of the exact frozen R1 draft by a fresh normal ChatGPT that did not author it. Review state belongs only in `planning/reviews/R1.md`; manifest `routing.plan_review` is its locator. This authoring session must not produce a verdict, approve its own plan or enter Execution Prep. Approval requires the planner audit plus independent GREEN and an unchanged reviewed plan body, per current Planning contract.

Later independent implementation reviews follow the `chatgpt_only` lifecycle; no extra arbitrary fresh-session cadence is imposed. Exact source/accepted predecessor evidence, Cards/OpenSpec and cumulative handoffs provide continuity. Plan approval does not waive explicit live-write/credential/restart authorization or turn this planning-only delivery into deployment permission. Recover existing valid authority and request only genuinely missing concrete scope.

The next reviewer reconstructs the immutable plan subject, Definition and relevant evidence from the separate review record and repository. After its verdict, its router owns legal continuation; a corrective substantive draft requires a new revision/review subject. This plan contains no mutable execution progress.
