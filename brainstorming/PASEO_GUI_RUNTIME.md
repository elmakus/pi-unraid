# Brainstorm — Paseo GUI runtime for Pi on Unraid

Date: `2026-09-24`
Scope ID: `paseo-gui-runtime`
Revision: `R1`
Status: `tentative`

## Problem / goal

Make Paseo the normal GUI/control surface for Pi on Unraid. The user intends to work with Pi through Paseo on Android/PC rather than through a terminal. The production layout should be clean, native to upstream expectations, recoverable from repository state, easy to update/rollback, and ready for later orchestration-runtime integration without making Paseo or runtime-private state project authority.

This record is exploratory state only. It preserves accepted user choices from the current grilling session so recovery never depends on chat history.

## Current understanding

### Verified project/workflow facts

- The prior `feature-pi-unraid-bootstrap` workstream is terminal and integrated into `main`.
- The current feature is independent of that closed workstream and starts from current `main`.
- Project Workflow remains the governance/durable-authority layer; `PROJECT.md` is only the high-level project router/index.
- `pi-unraid` issue #3 remains open and separately tracks the repository mutation policy: reads on `main` are allowed, managed writes must occur on a legal PW workstream or an automatically isolated ad-hoc branch/worktree.
- The current PWv2.1 exploratory branch treats Paseo as the expected Pi backend/infrastructure while keeping OR/Paseo private runtime state non-canonical.
- The current orchestration-runtime exploratory branch records Paseo-managed child creation, event-driven completion/error/attention handling, descriptive child titles, and repository/worktree isolation as accepted exploratory directions. Those external records remain authority only for their own projects until promoted there.

### Existing accepted constraints relevant here

- Repository/PW durable state must remain sufficient to recover legal project continuation without Paseo private state.
- Paseo must not become a second Project Workflow/governance authority.
- Later orchestration-runtime integration must consume legal PW state rather than inventing another project lifecycle.

## Adaptive discovery state

### Accepted exploratory choices

The entries below are explicit user/product choices from this Brainstorming. "Stable" means accepted for continued exploration; Project Definition must still promote them before they become canonical requirements/decisions.

#### A. User experience and primary entrypoint

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Paseo is the normal user-facing GUI for Pi on Android and PC; terminal Pi is not the normal usage path. | A terminal-first fallback would reduce GUI dependency but would duplicate the intended operating model and is not wanted by the user. | Stable. |
| The user manually chooses the project in Paseo; Main must not guess the project from conversation content. | Automatic project inference is convenient but can bind the wrong repo/workstream. | Stable after user correction. |
| After project selection, Main should recover the active PW workstream/durable state automatically. | Requiring the user to select branch/workstream manually would add avoidable workflow friction. | Stable. |
| Session/agent names must be short and descriptive: project + subject +, where useful, workstream/milestone/card/role. | Raw UUID-centric names are recoverable technically but poor operational UX. | Stable; user explicitly said this is necessary. |
| Do not auto-generate a closing summary merely because a Paseo session is archived/closed. | Extra summaries could help recall but duplicate durable PW handoffs/evidence and add clutter. | Stable after explicit user rejection. |
| Completed sessions should leave the active view while remaining available as history; blocked sessions should show the gate they await when Paseo supports it. | Keeping every completed session active improves visibility but creates noise. | Stable. |
| Use native Paseo UI/status/agent visibility where possible; do not build a custom dashboard unless a real gap is later proven. | A custom cockpit could expose more PW data but adds a second UI to maintain. | Stable. |

#### B. Container/runtime architecture

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Final production shape is one active Paseo container that also contains the Pi CLI/runtime needed for `pi --mode rpc`. | Two active containers could isolate responsibilities, but Paseo expects to launch the provider CLI locally and the user has no reason to operate standalone Pi separately. | Stable after revisiting one-vs-two-container design. |
| Paseo daemon stays up; Pi RPC processes are spawned by Paseo on demand rather than keeping one permanent Pi process alive. | A permanent Pi process might look simpler operationally but does not match Paseo's process-backed provider model. | Stable. |
| The existing standalone `pi-unraid` container is bootstrap/validation infrastructure only and should be retired after Paseo reaches GREEN acceptance. | Retaining it as a permanent fallback would create two Pi environments and configuration drift. | Stable. |
| No user-state migration from standalone `pi-unraid` is required because the user has not used it for real work. | A blanket migration could preserve unknown state but would copy bootstrap debris into the new canonical environment. | Stable after explicit user correction. |
| Use a child image based on Paseo that installs Pi and required system tooling during build; do not bind-mount Pi binaries/node_modules from another container. | Runtime-mounted binaries reduce rebuild needs but make provenance/recovery less reproducible. | Stable. |
| Paseo and Pi both track `latest` rather than manually pinned release numbers. | Pinning maximizes reproducibility but the user explicitly prefers latest; rollback must therefore carry the safety burden. | Stable, exact release-channel semantics still open. |
| Do not impose CPU or RAM limits on the production container. | Limits can protect the host but may cause hard-to-diagnose agent/browser failures under bursty workloads. | Stable. |
| Set container shared memory to 1 GiB. | Default Docker SHM is smaller and sufficient for simple Pi-only work, but browser tooling is explicitly in scope. | Stable. |
| Run as Unraid-friendly UID/GID `99:100`. | Upstream default IDs could simplify image assumptions but cause ownership friction on host-mounted data. | Stable. |
| Paseo autostarts with Unraid. | Manual start gives stronger operator control but conflicts with Paseo being the normal Pi entrypoint. | Stable. |

#### C. Native filesystem layout and persistence

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Preserve native upstream paths rather than inventing custom Pi/Paseo config locations. | Custom host-centric paths can look cleaner in Compose but may break extensions/tools that assume native HOME paths. | Stable; explicitly emphasized by user. |
| Use a real `HOME=/home/paseo`; persist the entire `/home/paseo` rather than only selected dot-directories. | Selective mounts reduce backup surface but risk missing future native `~/.tool` state. | Stable. |
| Pi uses its natural `~/.pi/...` tree and Paseo its native HOME state. Avoid symlink/path-translation tricks unless later proven necessary. | Symlinks can bridge legacy layouts but create hidden assumptions for extensions. | Stable. |
| Use `/workspace` as the canonical code root. Keep repository/worktree data physically separate from appdata/HOME on the Unraid host. | Keeping code inside appdata makes one backup target but mixes large Git working data with application state. | Stable. |
| Keep a clear repos/worktrees organization under the workspace rather than exposing arbitrary host storage. | Mounting all of `/mnt/user` is flexible but grants unnecessary filesystem scope. | Stable. |
| Initial project scope is `pi-unraid`; migration/onboarding of older Codex projects is later work that Main can perform deliberately. | Importing everything immediately could prove multi-project handling sooner but expands this feature unnecessarily. | Stable. |

#### D. Networking and access

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Use Paseo Relay as the initial remote-access path. Do not expose a raw Paseo port to the Internet. | Direct reverse-proxy access is conventional but creates extra auth/TLS/exposure configuration. | Stable. |
| Initially use Relay even on LAN rather than maintaining a separate direct-LAN access path. | Direct LAN is lower-latency and independent of Relay, but creates a second security/UX path. | Stable. |
| Do not configure `PASEO_PASSWORD` while there is no direct LAN/public daemon exposure. | A password is defense-in-depth, but the user explicitly rejected it for this Relay-only design. | Stable. |
| Persist Relay/pairing state in HOME so rebuild/restart does not force re-pairing. | Ephemeral pairing is cleaner security-wise but would add recurring setup friction. | Stable. |
| Pair only the user's own devices initially. | Pre-pairing more household devices is convenient but unnecessary until there is a real user. | Stable. |

#### E. Health, readiness, backup and recovery

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Docker healthcheck should be lightweight for Paseo itself; a separate doctor/readiness check exercises Paseo → Pi and deeper dependencies. | A full Pi RPC smoke on every health interval gives stronger assurance but creates needless process churn. | Stable. |
| Full readiness/doctor runs on deploy/update/config change/error/on demand, not before every normal turn. | Per-turn validation maximizes safety but wastes time/context and duplicates stable checks. | Stable. |
| Back up the whole persistent Paseo HOME with the normal appdata strategy. Treat that backup as sensitive. | Git/PW alone is enough for project legality but would not preserve sessions, pairing, auth, browser profile and convenience state. | Stable. |
| Browser profile/cookies are included in protected HOME backup and treated as credentials/secrets. | Excluding them reduces backup sensitivity but forces re-authentication and loses session continuity. | Stable. |
| Take a pre-update HOME snapshot/pointer. Default rollback restores the previous image only; HOME is rolled back only when migration/state corruption requires it. | Always rolling back HOME is simpler but can destroy sessions/state created after the update. | Stable. |
| Destructive HOME restore requires user approval after Main diagnoses/prepares the recovery. | Fully automatic restore reduces downtime but can discard newer state incorrectly. | Stable. |
| Keep at least one known-good prior image for rollback. | Rebuilding an older version on demand uses less storage but is slower and less certain during outage. | Stable. |
| Update should be build/smoke/promote rather than destructive in-place replacement when practical. | In-place update is simpler but weakens rollback confidence. | Stable. |
| Final acceptance must include a real end-to-end test from the user's phone through Paseo Relay, not backend-only checks. | Backend smoke alone is automatable but does not prove the user's actual access path. | Stable. |

#### F. Tooling baseline and browser capability

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| The image should have a reasonably rich general development baseline, not an artificially minimal toolset. | A tiny image reduces size/attack surface but pushes Main into repeated poor workarounds for standard development tasks. | Stable. |
| Baseline should include common shell/Git/network/build/Python/Node tooling sufficient for normal repository work; specialized tools remain capability-driven. | Installing every possible tool preemptively would violate YAGNI. | Stable; exact package list is implementation detail/research. |
| Install Chromium plus Playwright and required system libraries in the image. | Deferring browser runtime until first use makes the base smaller, but the user reversed an initial rejection and explicitly wants browser capability present. | Stable. |
| Support both headless browser work and headed/Xvfb execution, without adding a full desktop/noVNC stack. | Headless-only is simpler but can fail on sites/workflows that behave differently with a display. | Stable. |
| Allow browser screenshots/PDF generation. | Excluding artifacts reduces storage but harms browser evidence/debugging. | Stable. |
| Persist a dedicated automation browser profile; do not mix it with a personal desktop-browser profile. | Ephemeral profiles are cleaner but lose authenticated sessions. | Stable. |
| Logged-in browser sessions/credentials may be reused for approved services, while first-time credential/account setup remains deliberate. | Requiring manual login every run is safer but significantly less useful. | Stable. |
| Install `gh` and keep GitHub auth usable across rebuilds through the secrets/native-config strategy. | Re-auth per rebuild minimizes persistent credentials but breaks autonomous repo workflow. | Stable. |
| Install Docker CLI and Docker Compose plugin, but do not mount `/var/run/docker.sock` by default. | Socket access is powerful and convenient for self-deployment but effectively grants broad host control. | Stable. |
| Main may run internal development servers on needed container ports; do not expose them publicly by default and do not build public preview plumbing in the first version. | Automatic public previews are convenient but add exposure and infrastructure scope. | Stable. |

#### G. Extensions, skills, MCP and capability management

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Install SpecPi core in the target environment, with SpecPi scope control disabled; retain its improvement-loop/wishlist value. | SpecPi scope overlaps PW authority; disabling that part avoids two governance systems while retaining harness-improvement feedback. | Stable exploratory choice carried into this scope. |
| Install the already-selected `pi-mcp-adapter` in the initial environment if its current integration remains compatible. | Delaying it simplifies first boot but would immediately require a second environment change for planned MCP use. | Stable, compatibility still needs verification. |
| Global Pi extensions/skills should use native Pi locations in HOME. | Image-baking every extension is more immutable but makes frequent capability changes require image rebuilds. | Stable. |
| Maintain a declarative capability inventory in `pi-unraid`, including classification and brief rationale. | Relying only on actual HOME state is simpler short-term but makes rebuild/drift analysis opaque. | Stable. |
| Inventory categories: baseline, approved optional/global, and project-local. | A much more detailed permission taxonomy could model more cases but is not currently justified. | Stable. |
| Doctor should detect drift between declared capability inventory and actual environment; unexpected items are reported, not automatically removed. | Auto-pruning enforces exact state but may delete useful/manual state without authority. | Stable. |
| New permanent global capabilities or global skills require user approval. Removal of existing global capabilities also requires user approval. | Fully self-modifying tooling would reduce interruptions but changes the global execution environment without user authority. | Stable. |
| Main may create project-local skills/extensions as part of an already accepted project scope, subject to normal PW/branch policy. | Requiring user approval for every local helper would create unnecessary friction. | Stable. |
| Once a global capability is already approved, routine extension updates may be performed through the controlled update/rollback process without re-approving the capability itself. | Re-approval for every patch maximizes control but is operationally noisy. | Stable. |
| If an approved extension update fails smoke/health checks, rollback to the prior known-good extension/environment state. | Leaving a broken latest version installed would defeat the update safety model. | Stable. |
| Do not automatically remove capabilities merely because they have not been used recently. | Automatic cleanup controls bloat but usage age is not proof that a capability is obsolete. | Stable. |
| SpecPi wishlist/improvement state should be consulted when capability/reliability work or repeated friction makes it relevant, not on every normal turn. | Reading it every turn could surface improvements earlier but wastes context. | Stable. |
| Capability-gap escalation: when Main repeatedly or materially lacks a durable tool/CLI/extension/MCP that would make work substantially simpler/safer, it should tell the user what is missing and recommend permanent installation instead of forcing a bad workaround. | Aggressive workaround-first behavior avoids interruptions but accumulates brittle execution patterns. | Stable; user explicitly requested this behavior. |

#### H. Sessions, agents, concurrency and later orchestration

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Do not impose a Paseo/container-level hard cap on parallel Pi agents initially. | A hard cap protects resources but the host already has no CPU/RAM limit and real contention should be measured first. Later OR may still impose its own orchestration ceiling. | Stable and compatible with a future OR-specific concurrency policy. |
| Main may create workers automatically when the accepted workflow allows it; no repeated user approval is needed for ordinary delegation. | Asking each time maximizes visibility but makes orchestration impractical. | Stable. |
| A mutating worker should have an isolated legal worktree/branch context; read-only workers may share safe read-only context when appropriate. | Shared writable checkouts are simpler but unsafe under concurrency and conflict with repo mutation policy. | Stable. |
| Main should normally receive bounded structured worker results/handoffs rather than full transcripts; full logs remain available for error/debugging. | Full history provides maximum context but causes context bloat. | Stable. |
| Worker-to-worker direct communication is not the default; Main/OR coordinates. | Peer communication can accelerate some workflows but makes authority/causality harder to track. | Stable. |
| Crash recovery must inspect durable/checkpoint state before retrying mutating work; do not blindly replay uncertain side effects. | Blind retry is faster but can duplicate mutations. | Stable. |
| Multiple project workstreams may exist concurrently with their own durable state/isolation. | Serializing the whole project is simpler but unnecessarily blocks independent work. | Stable. |
| Paseo should preserve session state across container restart but must not automatically resume mutating work after restart. | Auto-resume improves continuity but can restart side effects without operator awareness. | Stable. |
| A user-gated workstream should resume in the same logical session after the user answers the gate. | New sessions at every gate are cleaner but fragment continuity. | Stable. |
| Use a long-lived project Main entry session plus distinct workstream/worker sessions rather than one giant global session. | One global session minimizes navigation but mixes authorities/projects and grows stale context. | Stable. |
| Orchestration-runtime is added only after the base Paseo+Pi deployment is GREEN. | Installing both at once reduces rollout steps but makes fault isolation much worse. | Stable. |
| Paseo is UI/execution infrastructure, not governance. OR/PW own their respective orchestration/governance concerns. | Letting Paseo own project policy would couple legal workflow to GUI-private state. | Stable. |
| Runtime architecture may support multiple providers/models, but Main may not switch the configured model/provider on its own; that requires user decision. | Automatic model selection can optimize cost/capability but violates the user's desired control. | Stable after explicit user correction. |
| When Paseo/OR exposes native agent status/timelines, use them rather than duplicating another agent dashboard/store. | Duplicating timelines can give a custom UX but creates drift and maintenance. | Stable. |

#### I. PW/Git operational behavior

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Project Workflow/repository remains the source of truth; Paseo session state is convenience/recovery acceleration only. | Treating Paseo as authority would simplify resume but make project legality dependent on private runtime state. | Stable. |
| Keep `pi-unraid` issue #3 as the separate global repository-mutation guard concern rather than folding that policy into Paseo-specific implementation. | Embedding it only in Paseo might solve the immediate path but fail for other Main/worker entrypoints. | Stable direction; issue remains open. |
| Main may automatically commit, push, open PRs and merge when the current PW route authorizes those mechanics and no separate user gate exists. | Asking the user for every Git operation maximizes control but creates unnecessary stops. | Stable. |
| Lightweight pre-mutation sanity/readback should verify expected repo/worktree/branch/PW binding before writes; do not run a full doctor before every mutation. | Full verification each time is safer but wasteful and noisy. | Stable. |


#### J. Conversation-reconciliation additions

These choices were recovered by a line-by-line audit of the current Brainstorming conversation against this durable record on 2026-09-24. They were explicitly accepted earlier but were missing or only implicit in the first retroactive persistence pass.

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Reproducible Paseo/Pi deployment configuration belongs in `pi-unraid` (Dockerfile/Compose/template/config/inventory); Unraid GUI is an execution/deployment surface, not a second configuration authority. | GUI-only configuration is convenient but becomes hidden mutable state that fresh recovery cannot reconstruct from Git. | Stable. |
| Keep one production Paseo+Pi image variant rather than several parallel image flavors. | Multiple images can isolate optional capabilities but multiply update/rollback combinations without a current need. | Stable. |
| Paseo and Pi are updated as one controlled image promotion unit even though both track `latest`; the retained previous image provides rollback. | Independent runtime upgrades offer finer control but create a larger compatibility matrix. | Stable. |
| Host appdata for Paseo is separate from the retired standalone Pi appdata; the persistent Paseo HOME lives under the Paseo appdata area while code/worktrees stay outside appdata. | Reusing the old Pi appdata would reduce paths but would mix bootstrap state into the new canonical environment. | Stable. |
| Paseo/Pi gets read-write access to the intended `pi-unraid` workspace/repos/worktrees root, not broad arbitrary Unraid storage. | Per-repo Docker mounts provide narrower isolation but add friction for Main-managed worktrees and later project onboarding. | Stable. |
| Use a separate secrets layer/source where possible while presenting credentials to tools through their native expected path/env; never put secrets in the repository. | Keeping all credentials as ordinary HOME files is simpler but weakens separation and backup hygiene. | Stable; exact per-tool materialization remains a research/design detail. |
| Pi/Main retains a normal shell toolchain inside the container even though the user does not use a terminal. Do not give Main `sudo`; system-level packages are added through the image/deployment workflow. | Removing shell access would cripple normal coding work; giving sudo would enable uncontrolled runtime mutation. | Stable. |
| Main may edit Dockerfile/Compose/deployment source in a legal PW branch, but live self-deployment/rebuild of its own production environment must go through the intended deployment workflow rather than an ad-hoc mid-turn mutation. | Direct self-rebuild is fast but can destroy the running control plane and bypass acceptance/rollback gates. | Stable. |
| Runtime logs use rotation/finite retention; durable project evidence belongs in Git/PW rather than indefinite operational logs. | Infinite logs maximize forensic history but waste storage and blur authority. | Stable. |
| Approved Pi extensions normally follow their current/latest release line; the environment/inventory should retain enough installed-version evidence to diagnose and roll back a bad update. | Full version pinning is more reproducible but conflicts with the user's latest-first preference. | Stable; exact release-channel semantics remain open. |
| Main may close/clean up completed worker sessions after durable handoff/result capture; history may remain for debugging but is not authority. | Keeping every worker alive preserves immediate context but consumes resources and clutters UI. | Stable. |
| Opening Paseo should show the normal Paseo home screen, without Main auto-selecting a project from conversation context or automatically binding to the last project. The user chooses/enters the project explicitly. Paseo may remember or visually highlight the last project if that is native behavior, but this is optional rather than a requirement. | Auto-binding the last project saves a click but conflicts with the user's explicit desire to choose the project; forcing a custom project picker would also unnecessarily diverge from native Paseo UX. | Stable after explicit user clarification. |
| Paseo may remember the configured model/provider selection per project/session, but Main must not change that selection autonomously. | Forgetting it forces repetitive setup; autonomous switching removes user control. | Stable. |
| If Paseo exposes it natively, the active branch/worktree should be visible in the UI/session context. | Hiding Git placement simplifies UI but makes mutation mistakes harder to notice. | Stable. |
| Multiple mutating workers inside the same workstream are allowed only when the governing plan/obligation explicitly permits parallel decomposition and each worker has isolated scope/worktree; otherwise mutate sequentially. | Unrestricted parallel writes increase throughput but can violate PW seriality and create conflicts. | Stable. |
| Main should emit very short user-visible phase/status transitions when materially useful (for example review GREEN → next phase), while routine worker progress remains local. | No progress messages is quieter but makes GUI operation opaque during long workflows. | Stable. |
| Session search/filter by project/workstream/card should be used when Paseo supports it natively. | Relying only on chronological history is simpler but degrades quickly with many workstreams. | Stable. |
| Use the existing normal Unraid/appdata backup mechanism for Paseo HOME rather than building a dedicated backup engine; if that mechanism safely stops containers during backup, that is acceptable. | A custom backup engine could optimize consistency but is unnecessary complexity. | Stable. |

### Conversation-to-durable audit

- Audit performed: `2026-09-24`.
- Scope: every explicit user acceptance/correction in the current Paseo grilling conversation up to the user's question asking how completeness can be trusted.
- Result: the first retroactive persistence pass was **not complete**; the missing/implicit choices are the entries in section J above.
- The final unanswered 15-question batch about image build location/tagging/update polling/stable channel/etc. remains **unaccepted** and is intentionally represented only by open decisions where applicable.
- Superseded/rejected choices remain preserved separately below; they are not silently overwritten.
- Future Brainstorming rounds must persist accepted/rejected/reopened choices before asking the next batch so this kind of retrospective reconstruction is not required again.


#### K. Repository entry, worktree and session safety

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Opening Paseo should use the native Paseo home screen; do not add a custom project launcher solely to choose repositories. | A custom launcher could centralize project metadata but would duplicate native UI and add maintenance without a current need. | Stable. |
| A Paseo project/workspace should remain an ordinary repository/workspace concept; Project Workflow becomes responsible for legal continuation only after Main enters the chosen project. | Embedding PW project selection directly into Paseo would couple UI and governance unnecessarily. | Stable. |
| On entering a selected project, Main should perform a read-only PW/workstream readback, but must not create a new workstream until an actual task requires one. | Pre-creating workstreams reduces one later step but pollutes durable state with speculative work. | Stable. |
| Pure read-only repository inspection may occur on `main` without creating a branch/worktree. | Forcing branches for inspection would add friction with no mutation-risk benefit. | Stable. |
| For ad-hoc non-PW mutation starting from `main`, Main should automatically create an isolated task branch/worktree before the first write. | Requiring the user to remember branch hygiene manually is error-prone. | Stable; aligns with issue #3 direction. |
| Ad-hoc task branch/worktree names should be generated automatically from the task subject as concise slugs. | Asking the user for names every time adds no meaningful control. | Stable. |
| Main may automatically clean up an ad-hoc worktree after successful merge/close once no live obligation remains. | Retaining every worktree indefinitely aids forensics but creates clutter and stale execution surfaces. | Stable. |
| Protect repository `main` against accidental mutation with a mechanical guard where practical, not prompt-only discipline. | Prompt-only safety is simpler but weaker and easier to bypass accidentally. | Stable. |
| Keep one stable `main` checkout per repository for read-only inspection and use separate worktrees for mutation. | Reusing one mutable checkout reduces disk usage but blurs execution boundaries. | Stable. |
| Read-only workers may share the stable read-only `main` checkout when safe. | Isolating every read-only worker gives maximum separation but adds unnecessary worktree churn. | Stable. |
| Every mutating worker should receive its own worktree even when it is the only active mutating worker. | Conditional isolation based on concurrency saves setup work but makes the rule context-dependent and easier to violate. | Stable. |
| Main itself may mutate an authorized workstream worktree directly; delegation to a worker is optional, not mandatory. | Forcing every mutation through a worker would add an unnecessary orchestration layer for simple tasks. | Stable. |
| A Paseo session should remain associated with its concrete workspace/worktree so resume returns to the same execution location when that location is still valid. | Rebinding sessions dynamically is more flexible but risks resuming in the wrong repository context. | Stable. |
| If a historical session's worktree no longer exists, do not recreate that stale worktree automatically. Main must read current Git/PW state and continue from the current legal location. | Automatic recreation preserves conversational continuity but can revive obsolete execution state. | Stable. |
| Opening a stale/archived session must not automatically re-enable mutation from its old execution context; Main should treat it as historical until current durable state is revalidated. | Treating every reopened session as live is convenient but unsafe after branches/worktrees move or close. | Stable. |

## Material dependencies / unresolved decisions

The following remain open and should drive subsequent grilling rather than being guessed during implementation.

| Decision | Prerequisites | Status |
|---|---|---|
| Exact image build/publish path: local Unraid build vs self-hosted runner/registry flow. | Current Unraid runner/deployment capabilities and desired rollback ergonomics. | open |
| Exact image tag strategy in addition to user-facing `latest` (e.g. immutable build tag/digest retention). | Build/publish path. | open |
| Exact policy for who/what initiates Paseo/Pi `latest` updates and whether version checks are on-demand or scheduled. | Update/rollback mechanics. | open |
| Exact meaning of `latest` regarding stable releases versus prerelease/beta/nightly channels. | Upstream release practices for Paseo and Pi. | open |
| Exact secrets materialization method for each CLI/provider that insists on a HOME file versus env/secret mount. | Verified upstream auth/config behavior. | open |
| Exact browser-control extension/MCP layer above Chromium+Playwright, if any. | Later browser-control research/selection; current choice covers runtime only. | open |
| Exact capability inventory schema/reconciliation command shape. | Definition/implementation design; user-facing policy is already settled. | open |
| Exact doctor command/check matrix and which checks are quick vs full. | Concrete container/tool layout. | open |
| Exact Relay deployment/pairing behavior and persistence details against the then-current Paseo release. | Fresh upstream verification before Definition/implementation. | open |
| Exact retirement/delete procedure for the unused bootstrap container/appdata after Paseo GREEN. | Final deployment acceptance and rollback window. | open |

## Research needed before Definition/implementation

- Re-verify current Paseo Docker/provider/Relay/security/session behavior and current image conventions at the time Definition begins.
- Re-verify current Pi installation/package/global extension paths and latest release/install semantics.
- Re-verify SpecPi core install flags, scope-disable behavior and improvement-loop persistence before first deployment.
- Re-verify `pi-mcp-adapter` current compatibility and configuration needs.
- Verify Chromium/Playwright/Xvfb package/runtime requirements against the selected Paseo base image.
- Verify the best build/publish/deploy route available on this Unraid host without granting unnecessary Docker-host authority to the runtime container.

## Reopened / superseded exploratory ideas

- **Two permanently active containers (Paseo + standalone Pi): superseded.** The user has no normal standalone-Pi use case; final target is one Paseo+Pi production container.
- **Migrate standalone Pi HOME/state: superseded.** The bootstrap environment was not used for real work.
- **No browser tooling on initial deploy: superseded.** The user clarified that the rejection was a misunderstanding and wants Chromium/Playwright capability included.
- **Main auto-selects project from conversation: superseded.** The user wants to choose the project manually.
- **Main may auto-switch model/provider: rejected.** Provider/model change requires user decision.
- **Automatic session-close summary: rejected.**
- **PASEO_PASSWORD in Relay-only design: rejected.**

## Brainstorming interaction preference

- After each user acceptance/correction round, persist the resulting exploratory choices to this durable record first, then immediately continue with the next coherent question batch unless a real workflow stop/research gate intervenes.
- Do not wait for the user to ask for the next batch again during normal adaptive grilling.

## Outcome of current session

- Tentative conclusions: a substantial portion of deployment/UX/security/capability/session policy is now settled exploratorily and recoverable from this record.
- Explicit user/product choices to promote through Project Definition: all stable entries above after their remaining required challenge/completion audit.
- Research still needed: current upstream verification and the open implementation-facing decisions listed above.
- Open questions: continue adaptive grilling from the unresolved decision frontier.
- Next phase/action: `continue brainstorming`
- Definition promotion authorization: `pending`
- Definition promotion subject: `none`

> Nothing in this file becomes accepted requirement/decision authority by itself. Project Definition owns promotion into canonical `requirements/` and `decisions/`. Only an explicit user instruction may authorize promotion of the exact current `paseo-gui-runtime@R1` scope into Project Definition.
