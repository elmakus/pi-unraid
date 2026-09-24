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


#### L. Update control, host access and disaster recovery

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Build the Paseo+Pi image through the self-hosted GitHub runner on Unraid rather than making manual local builds the normal path. | Manual local builds are simple but weaker as a reproducible repo-driven deployment flow. | Stable. |
| Every successful build should have both a normal `latest` reference and an immutable build identity/tag/digest for evidence and rollback. | `latest` alone is convenient but cannot identify the exact deployed artifact reliably. | Stable. |
| Main must not initiate a Paseo/Pi upgrade merely because a newer version exists; it may detect/propose the upgrade, but applying it requires explicit user approval. | Fully autonomous upgrades reduce maintenance but can change the control plane unexpectedly. | Stable. |
| Do not run a dedicated periodic version-polling loop for Paseo/Pi/extensions by default; check during maintenance/update work, relevant doctor flows or explicit user requests. | Continuous polling catches updates earlier but adds background machinery without a current need. | Stable. |
| Interpret normal `latest` as latest stable release; prerelease/beta/nightly/canary requires an explicit user decision. | Following prerelease channels gives faster access to fixes/features but increases instability. | Stable. |
| Do not cut over/restart the Paseo+Pi runtime while mutating agents are mid-write; first reach a safe checkpoint/drain state. | Immediate update minimizes version lag but can interrupt mutations and leave uncertain side effects. | Stable. |
| Main will ultimately have full administrative access to the Unraid host. The permanent architecture must not assume that Main is intentionally limited to a narrow Paseo-only deployment helper. | Least-privilege host-only helper reduces blast radius, but the user explicitly wants full Unraid administration available to Main for broader system work. | Stable after explicit user correction. |
| The exact full-access transport is intentionally undecided and must be researched later: candidates include an Unraid-specific MCP/integration, Unraid/API-token access, Docker-host control and SSH. A preferred primary path plus SSH as a broad fallback is an explicit candidate, not yet a frozen design. | Choosing a transport prematurely could lock the environment to a less capable or less ergonomic integration. | Open implementation/research decision. |
| Container startup should not silently perform broad capability/config mutation; startup detects critical problems, while reconciliation remains an explicit controlled operation. | Self-healing startup can reduce downtime but makes boot behavior less deterministic and can hide drift. | Stable. |
| If an already-approved capability is missing but declarative inventory says it should exist, Main may restore it automatically during an explicit reconcile/doctor flow and report the repair. | Requiring fresh approval for restoration would repeat an already-made capability decision. | Stable. |
| If one extension is deterministically proven to prevent Pi startup, the environment may quarantine/disable that offender to recover core runtime, preserving evidence and reporting the action; do not mass-disable unrelated extensions. | Refusing all automatic isolation can leave the whole control plane unavailable because of one extension. | Stable. |
| Keep a manual administrative break-glass shell path from Unraid even though normal user interaction is through Paseo. | GUI-only recovery simplifies the operating model but removes a valuable last-resort diagnostic path. | Stable. |
| The manual administrative break-glass shell may run as root; normal Main/Pi execution inside Paseo remains `99:100` without `sudo`. | Rootless recovery is safer but may be unable to repair broken ownership/runtime/system state. | Stable. |
| Provide two doctor depths: a quick core/runtime/workspace/Git/config check and a full browser/Relay/Codex-LB/MCP/extensions/GitHub-auth/permissions/E2E check. | One universal full doctor is simpler conceptually but too expensive/noisy for frequent use. | Stable. |
| Maintain a documented disaster-bootstrap path that can recover from total Paseo HOME loss using the image, secrets, capability inventory and Git/PW state. Paseo UI/session history may be lost without losing canonical project work. | Treating HOME as irreplaceable would make a local-state loss a project-recovery failure. | Stable. |


#### M. Full Unraid administration semantics

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Main may use its full Unraid administrative capability autonomously while carrying out an already-authorized task; do not require confirmation before each ordinary host command. | Per-command confirmation maximizes direct control but would make infrastructure work impractical. | Stable. |
| Full Unraid access is a global Main/environment capability, not something scoped only to the `pi-unraid` repository. | Repo-local access is narrower but misrepresents Unraid as merely one project's runtime. | Stable. |
| Prefer a structured Unraid-specific/API/MCP control surface over raw SSH when it provides materially equivalent full coverage. | SSH is universal, but structured operations are easier to validate, observe and reason about. | Stable. |
| Keep SSH as a universal fallback even if another transport becomes the primary path. | A single control path is simpler but creates a larger recovery dependency. | Stable. |
| Main may fall back from the primary Unraid transport to SSH without asking again when the task authority is unchanged and the fallback is only a transport change. | Requiring a new user decision for transport fallback would add friction without changing task scope. | Stable. |
| Prefer the highest-level adequate control surface for each operation (dedicated/API/MCP operation first, shell/SSH when needed). | Always using SSH is uniform but loses typed/structured semantics where available. | Stable. |
| SSH should use non-interactive key-based authentication suitable for autonomous agent use. | Password prompts preserve manual involvement but break unattended execution. | Stable. |
| Host-access credentials must persist across Paseo rebuilds while remaining outside the repository. | Re-provisioning after every rebuild is safer in one dimension but operationally brittle. | Stable. |
| Full Unraid administration includes all Docker containers, not only the Paseo stack. | Limiting Docker control to Paseo would contradict the intended host-wide admin capability. | Stable. |
| Full Unraid administration may include host files/appdata/shares/network/configuration when a concrete authorized task requires them. | Restricting to Docker would make "full access" incomplete. | Stable. |
| Highly destructive or broad irreversible host operations still require explicit user approval, including examples such as deleting a whole share/appdata tree, formatting disks or materially changing storage pools. | Blanket authority would reduce prompts but create unacceptable irreversible-risk exposure. | Stable. |
| Restarting an individual container/service within an already-authorized maintenance task does not require a separate confirmation. | Reconfirming each restart would add low-value friction. | Stable. |
| Restarting the whole Unraid host requires explicit user approval because it disrupts all workloads. | Autonomous host reboot could simplify maintenance but has broad system impact. | Stable. |
| Before host-level mutation, Main should perform a bounded readback of the current target state instead of acting on stale assumptions. | Skipping readback is faster but increases risk of applying actions to changed infrastructure. | Stable. |
| Later dedicated research must compare at least Unraid-specific MCP/integration, available token/API control, Docker-host access and SSH, then select a preferred primary + fallback based on coverage, reliability, agent ergonomics and recovery behavior. | Choosing from intuition now could lock in a weaker long-term control plane. | Stable research obligation. |


#### N. Host-wide administration safety and maintenance semantics

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Full Unraid administration is available to Main as a global environment capability, not only after entering a specific project. | Delaying host access until project selection is narrower but artificial for infrastructure diagnosis. | Stable. |
| Main may use Unraid diagnostics while working on another project when evidence points to host/runtime causes. | Forcing repo-local reasoning can hide infrastructure causes and create bad workarounds. | Stable. |
| Different Unraid access transports should use separate credentials so rotation/failure of one transport does not remove all access. | Sharing one credential set is simpler but couples failure/revocation across paths. | Stable. |
| Prefer a dedicated administrative identity with controlled root escalation for SSH when practical, rather than making raw root login the default normal SSH path. | Direct root SSH is simpler but gives every SSH action maximum privilege. | Stable. |
| Main may rotate its host-access credentials within authorized maintenance, but must preserve at least one working access path throughout. | Rotating all access at once is simpler but risks self-lockout. | Stable. |
| Before rotating/removing an access credential, Main must verify a working fallback path. | Assuming fallback works can strand the control plane. | Stable. |
| Main may install additional Unraid-side packages/plugins needed for an authorized task, while genuinely new durable global capabilities still follow the capability-approval rule. | Treating every package as trivial can silently expand permanent host capability. | Stable. |
| Reversible network configuration changes directly required by an authorized task may be autonomous, but broad-impact routing/firewall/default-gateway/DNS changes require a user gate. | Treating all network edits alike either over-prompts or under-protects broad connectivity changes. | Stable. |
| Changing a single application's/container's port as part of accepted implementation does not need a separate user confirmation. | Per-port confirmation adds friction without changing task authority. | Stable. |
| Main may stop/restart multiple dependent containers during authorized maintenance after checking dependencies and restoring them afterward. | Reconfirming each dependent stop makes coordinated maintenance impractical. | Stable. |
| Restarting the Docker engine as a whole requires explicit user approval because it affects nearly the entire container estate. | Treating it like a single-container restart understates blast radius. | Stable. |
| Upgrading the Unraid OS itself requires explicit user approval separate from ordinary maintenance. | Autonomous platform upgrade could change the whole host control plane unexpectedly. | Stable. |
| Main may update ordinary Unraid plugins autonomously within authorized maintenance when no known broad-impact/reboot requirement applies. | Requiring explicit approval for every routine plugin patch adds little value. | Stable. |
| Before broad host-level changes, Main should capture a practical configuration/state snapshot or equivalent rollback anchor. | Skipping a rollback anchor saves time but weakens recovery from broad changes. | Stable. |
| When an authorized change fails its smoke/acceptance check, Main may automatically restore the prior known-good configuration if rollback is unambiguous and safe. | Waiting for another approval can unnecessarily prolong a known-bad state. | Stable. |
| Such rollback may restart affected services/containers without another confirmation; a full host reboot still remains a separate user gate. | Requiring confirmation for each rollback restart can block recovery. | Stable. |
| Maintain a lightweight derived operational inventory of important Unraid containers, shares, appdata paths, networks, storage and dependencies. | No inventory forces repeated broad discovery, while treating it as canonical risks drift. | Stable. |
| The operational inventory should be regenerated/reconciled from live host readback rather than treated as a hand-maintained source of truth. | Static inventories are easy to inspect but go stale. | Stable. |
| Keep a host-level doctor distinct from Paseo doctor: host doctor covers Unraid access/storage/Docker/network/core dependencies; Paseo doctor covers the Pi/Paseo control plane. | One monolithic doctor is simpler to name but harder to use and reason about. | Stable. |
| Unraid-access research must test failure behavior, not only feature coverage: primary unavailable → fallback → recovery → return to primary. | A feature matrix alone does not prove operational resilience. | Stable research obligation. |


#### O. Project onboarding, dependencies, caches and temporary services

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Paseo startup should not perform heavy discovery across every repository/project; discover lazily after the user enters a project. | Eager discovery makes the home screen richer but wastes startup time/context and touches projects the user may not use. | Stable. |
| The project list should primarily derive from actual repositories/workspaces under the canonical workspace filesystem rather than require a separate mandatory registry. | A registry can add metadata but becomes a second state source that can drift from the filesystem. | Stable. |
| Main may automatically clone a user-selected/requested repository into the canonical repos area when it is not present locally. | Requiring manual cloning adds unnecessary setup friction. | Stable. |
| A clone does not need separate approval when the repository is explicitly selected by the user or unambiguously required by the accepted task. | Per-clone approval adds little control after repo selection. | Stable. |
| After cloning/entering a repository, Main should automatically detect relevant `PROJECT.md`/PW state and recover the applicable route. | Requiring the user to identify workflow files manually defeats durable recovery. | Stable. |
| Repositories without Project Workflow may still be worked on ad hoc, subject to the global branch/worktree mutation policy. | Requiring PW for every repository would unnecessarily block ordinary coding work. | Stable. |
| Main may install project-local dependencies required by the repository/lockfiles within an authorized task. | Asking for every dependency install adds friction and project dependencies are not new global capabilities. | Stable. |
| Project-local dependencies do not require the same capability approval as new durable global tools. | Treating all dependencies as global capability changes would over-govern normal project setup. | Stable. |
| Prefer reproducible/locked dependency installation when the project provides a lockfile or equivalent. | Floating installs are simpler but weaken reproducibility and diagnosis. | Stable. |
| Main may create/cache project-local virtualenvs, node_modules and build caches as needed. | Recreating them every run is cleaner but wastes substantial time. | Stable. |
| Rebuildable project caches should not be included in the protected Paseo HOME backup. | Backing them up simplifies warm recovery but inflates backup volume with reproducible data. | Stable. |
| Large npm/pip/Playwright-style caches may live outside the protected HOME backup boundary. | Keeping everything in HOME is simpler conceptually but bloats snapshots. | Stable. |
| Temporary downloads/browser artifacts should have automatic cleanup with bounded retention. | Indefinite retention aids debugging but creates unbounded storage growth. | Stable. |
| When PW requires an artifact as durable evidence, Main may promote/copy it from temporary storage into the canonical evidence location. | Leaving evidence only in temp storage would make it non-durable. | Stable. |
| Ordinary screenshots/debug artifacts that are not accepted evidence should expire automatically. | Retaining every debug artifact indefinitely wastes storage. | Stable. |
| Main may fetch project-local binaries/CLI tools without additional approval when they are declared or clearly required project dependencies. | Treating declared local tools as global capability additions would over-govern repository setup. | Stable. |
| When work requires a new durable global service/system dependency, Main should surface the capability gap and seek approval rather than silently globalize it. | Silent global install reduces prompts but changes the shared environment without user authority. | Stable. |
| Main may launch temporary project-scoped helper services such as test databases/Redis/containers when needed by an authorized task. | Forcing every helper service into durable infrastructure slows ordinary testing. | Stable. |
| Temporary project helper containers/services should be automatically removed after the work when they are not part of the accepted final architecture. | Leaving them running creates drift and resource leakage. | Stable. |
| Any new durable service/container intended to remain on Unraid should be represented reproducibly in project/infrastructure configuration rather than left as an undocumented manual container. | GUI-only/manual durable services are fast to create but become hidden infrastructure state. | Stable. |


#### P. Instruction-plane progressive disclosure and PWv2.1 integration

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Keep the global Pi `~/.pi/agent/AGENTS.md` deliberately short: stable global invariants plus routing/discovery pointers, not a full operational encyclopedia. | Duplicating all policy into AGENTS.md makes every session pay the full context cost and creates drift. | Stable. |
| Detailed Unraid administration knowledge should live in a global `unraid-admin` skill rather than in the global AGENTS.md. | Keeping it all in AGENTS.md guarantees visibility but bloats every context. | Stable. |
| `unraid-admin/SKILL.md` should act as a compact procedure/router and progressively load detailed `references/` only for the branch of work actually needed. | Loading every reference up front is simpler but defeats progressive disclosure. | Stable. |
| The global instruction plane should contain a small hard invariant that Unraid host mutation must consult/load the Unraid administration policy/skill before acting. | Relying only on model discovery of a skill risks skipping policy entirely. | Stable. |
| The Unraid skill should decide which references are needed rather than loading all references on every invocation. | Eager loading improves completeness but wastes context and increases anchoring/noise. | Stable. |
| Keep one canonical authorization-matrix reference for autonomous versus approval-required host operations rather than duplicating that matrix across files. | Duplicate tables are easier to read locally but drift over time. | Stable. |
| Keep access-transport selection/fallback guidance in a separate reference from authorization policy so transport can evolve without rewriting authority semantics. | Combining them is simpler initially but unnecessarily couples two different concerns. | Stable. |
| Keep recovery/fallback procedures in a separate reference that is loaded only during recovery/relevant failures. | Always loading recovery detail wastes normal-turn context. | Stable. |
| Keep host-doctor procedures within the same Unraid administration skill initially; split only if the skill becomes materially too large. | A separate doctor skill is cleaner categorically but adds routing overhead before size justifies it. | Stable. |
| Bundle reusable host-administration scripts such as doctor/inventory/readback helpers with the skill/package where appropriate. | Re-expressing every operation as prompt text is less reproducible and harder to test. | Stable. |
| Project-level AGENTS.md files should contain project-local instructions only and must not duplicate global Unraid policy. | Copying global policy into every repository increases drift and context cost. | Stable. |
| Project-level AGENTS.md should not copy the Project Workflow implementation/router text. | Embedding the workflow in every repository would duplicate canonical policy. | Stable. |
| The environment must reliably recognize repositories governed by Project Workflow and enter the PW authority path when their durable project state indicates it; the exact runtime bootstrap mechanism is deferred because PWv2.1 is intended to be packaged as a Pi extension once its final shape is stable. | Freezing an AGENTS.md-based bootstrap now could conflict with the eventual PWv2.1 extension contract. | Stable intent; integration mechanism deliberately deferred. |
| PWv2.1 is intended to become a Pi extension rather than being implemented as part of the `unraid-admin` skill. Exact installation, discovery, bootstrap, fallback and AGENTS.md relationship must be designed after PWv2.1's final contract stabilizes. | Prematurely choosing installation details could force the unfinished workflow design into an awkward runtime package. | Stable direction; implementation deferred. |
| The Unraid skill and PWv2.1 remain separate ownership domains: Unraid administration is host capability/policy, while PWv2.1 owns project workflow/governance. | Combining them would entangle host administration with project lifecycle semantics. | Stable. |
| Where technically reliable, a Pi extension/policy guard should mechanically enforce a small set of critical destructive/broad approval gates rather than relying only on prompt memory. | Soft instructions alone are easier to implement but weaker for high-impact operations. | Stable. |
| Mechanical enforcement should cover only a bounded set of critical gates, not attempt to encode the entire Unraid administration policy as a second workflow engine. | Encoding everything mechanically creates complexity and duplicates semantic policy. | Stable. |
| Preference rules such as structured MCP/API before SSH should remain soft policy in the skill/reference layer rather than hard blockers. | Hard enforcement could prevent valid fallback/recovery paths. | Stable. |
| Global skills/references should have reproducible version-controlled sources in the repository and be installed/synchronized into Pi's native global runtime locations. | Editing HOME-only copies is quick but not reconstructable or auditable. | Stable. |
| The global AGENTS.md should also have a reproducible source under version control rather than existing only as hand-edited HOME state. | HOME-only global instructions are fragile after recovery/rebuild. | Stable. |
| Doctor should validate the instruction plane itself: expected global AGENTS.md, skills/references/extensions and their inventory/version alignment. | Runtime/tool checks alone can miss loss or drift of the policies that tell Main how to act. | Stable. |


#### Q. Capability inventory, doctor/reconcile and instruction-plane updates

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Keep one declarative global capability inventory for Main covering skills, extensions, CLI tools, MCPs, browser/runtime capabilities and similar durable environment features. | Fragmented inventories are easier locally but make recovery/drift analysis inconsistent. | Stable. |
| Capability inventory entries should include a concise purpose/rationale, not only package identity. | Package-only records are smaller but do not explain why a capability is retained. | Stable. |
| Inventory should distinguish version-controlled source from native runtime/install location. | Treating runtime HOME as the source obscures reproducibility and provenance. | Stable. |
| Record the exact observed installed version/commit/digest even when the desired policy is a moving channel such as latest stable. | Channel-only state cannot identify the exact known-good artifact for diagnosis/rollback. | Stable. |
| Model capability state as desired versus observed; observed state is derived from live doctor/readback rather than hand-maintained as authority. | A single field is simpler but conflates intent with reality. | Stable. |
| A declared approved capability missing from runtime is drift. | Ignoring missing capabilities allows silent degradation. | Stable. |
| An undeclared unexpected global capability present in runtime is also drift, but is reported for adopt/remove decision rather than automatically deleted. | Auto-pruning is deterministic but can destroy useful/manual state without authority. | Stable. |
| Main may restore a missing already-approved capability during explicit reconciliation without asking for the same approval again. | Reapproval would repeat settled authority rather than change scope. | Stable. |
| During an explicit update-oriented reconciliation, Main may update an already-approved capability to its accepted latest-stable line without re-approving the capability itself. | Reapproval for every routine version movement is operationally noisy. | Stable. |
| Keep `doctor` diagnostic/read-only and `reconcile` mutating/repairing. | Combining diagnosis and repair into one command is convenient but makes effects less predictable. | Stable. |
| `doctor quick` must be read-only. | Auto-fixing during a quick health check would hide drift and change state unexpectedly. | Stable. |
| `doctor full` is also read-only even when it performs active E2E probes. | A full doctor that repairs state makes diagnosis non-repeatable and harder to audit. | Stable. |
| Separate `reconcile` (restore current desired state) from `update` (intentionally move desired/current version lines forward). | One generic repair/update command is simpler but conflates recovery with version change. | Stable. |
| Global AGENTS.md, skills and extensions should use the same controlled update/smoke/rollback discipline as other durable capabilities. | Treating instruction-plane updates as plain file copies understates their impact on Main behavior. | Stable. |
| Snapshot/retain the prior instruction-plane set before changing global AGENTS.md, skills or extensions. | Without a rollback anchor a bad instruction update can disable the control plane. | Stable. |
| After changing a global skill/extension/instruction set, smoke it in a fresh Pi session rather than relying only on the currently loaded context. | Current-session tests can falsely pass because old instructions are already cached/loaded. | Stable. |
| Instruction-plane smoke must verify real discovery/progressive disclosure, including selecting the appropriate skill/reference without loading the whole policy corpus. | File-existence checks do not prove the model can actually route to the right authority. | Stable. |
| Critical policy guards require automated positive and negative tests (for example allowed ordinary action versus approval-required broad action). | Untested guards can silently over-block or under-protect. | Stable. |
| Changing the authorization matrix is a material policy/authority change, not a routine skill-content update. | Treating it as ordinary content could expand or contract Main autonomy without explicit authority handling. | Stable. |
| Provide a lightweight capability-status surface showing desired/observed/drift/version without requiring Main to load the full capability documentation. | Full-document inspection is wasteful for routine status checks. | Stable. |


### Verified PWv2.1 implementation dependency

Live readback on 2026-09-24 from `elmakus/chatgpt-codex-project-workflow` branch `work/pwv21-policy-kernel-brainstorming` established:

- `M02-T01` is `done`; its latest Card review `M02-T01-R06` is GREEN.
- M02 is not yet milestone-complete: `reviews/M02-MILESTONE-R01.toml` is still `pending`.
- `after-M02-T01` remains `waiting`; M03 has not yet been materialized.
- Approved Plan P2 defines M03 as **Portability, helper-less recovery, and parity** (PWV21-REQ-011…017), not packaging/runtime installation.
- Current approved PWv2.1 Definition/Plan does **not** define packaging PWv2.1 as a Pi extension. Occurrences of “extension” in P2 refer to extending the V2 baseline or fixture extension points, not Pi-extension deployment.
- Therefore the Pi-extension packaging/bootstrap/install design is a later integration concern and should not be injected into current M02/M03 execution unless PWv2.1 authority is deliberately reopened. Preferred current direction: finish the accepted PWv2.1 core plan, then design a separate packaging/integration workstream against the stable final contract.



#### R. Secrets, authentication, browser identity and Relay acceptance

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Capability inventory must never contain raw secrets/tokens; it may record only secret requirements, identifiers and expected locations. | Embedding secrets in inventory simplifies discovery but would make Git/config unsafe. | Stable. |
| When a tool can consume a credential directly from a mounted/native secret file, prefer that over copying the secret into place during startup. | Startup-copy is simple but creates extra mutable secret material and lifecycle complexity. | Stable. |
| If an upstream tool requires writable persistent native config in HOME containing credentials, allow it and treat that HOME/config/backup as secret-bearing. | Forcing every credential into an external mount may break native tooling semantics. | Stable. |
| Doctor must not print raw token/key/password values; it may report presence, permissions, fingerprints/metadata and authentication-probe results. | Printing raw values aids debugging but leaks credentials into logs/context. | Stable. |
| Logs/evidence should redact known secrets where practical. | Raw logs preserve exact output but create unnecessary credential exposure. | Stable. |
| Capability/status surfaces may report authentication state such as GitHub/SSH auth OK without exposing credentials. | Hiding all auth status makes diagnosis harder. | Stable. |
| Prefer OAuth/device-flow/token-based auth over storing ordinary passwords when the service supports it. | Password auth may be simpler initially but is generally less suitable for persistent automated use. | Stable. |
| First-time authentication of a new account/service requires deliberate user participation. | Fully autonomous credential enrollment risks binding the wrong account or authority. | Stable. |
| Automatic refresh of an already-approved OAuth/session token may occur without repeated user approval. | Reapproval on every refresh would make long-lived automation impractical. | Stable. |
| If authentication expires/revokes during work, stop the dependent action and request re-authentication rather than hunting for alternative credentials autonomously. | Secret-hunting could accidentally cross account or authority boundaries. | Stable. |
| Start browser automation with one persistent automation profile. | Multiple profiles from day one add complexity without a proven need. | Stable. |
| Create additional browser profiles only when multiple concurrent identities/accounts or isolation requirements justify them. | Precreating profiles anticipates hypothetical needs and adds management overhead. | Stable. |
| Treat browser profiles containing cookies/session tokens as secret-bearing state. | Treating them as ordinary cache would under-protect credentials. | Stable. |
| Browser downloads should default to temporary workspace storage rather than persistent browser-profile/HOME storage. | Persisting all downloads aids later inspection but bloats protected state. | Stable. |
| Screenshots/PDFs/downloads become durable evidence only when the workflow/task actually requires them; otherwise they remain temporary artifacts. | Persisting every browser artifact wastes storage and blurs evidence boundaries. | Stable. |
| Main may reuse an existing authenticated browser session for an already-approved service without asking before each visit. | Per-visit approval would make browser automation impractical. | Stable. |
| Paseo Relay device pairing should be individually identifiable/revocable when upstream supports it. | One undifferentiated pairing state is simpler but weakens device-specific revocation. | Stable. |
| Loss of one paired device should be recoverable by revoking that device without resetting all Relay/Home state when upstream supports it. | Resetting everything is simpler but needlessly disrupts unaffected devices. | Stable. |
| Do not design or configure a permanent/temporary alternate local/tunnel Relay-access path in this scope now. If Relay-break-glass access becomes necessary later, treat it as a separate explicit design/configuration decision. | Preconfiguring a second path increases attack surface and scope before a demonstrated need. | Deferred by explicit user correction. |
| Paseo deploy/update acceptance should include both internal Relay/Paseo health validation and an actual user-phone end-to-end test for the real UX path. | Internal health alone cannot prove the user-facing access path. | Stable. |


#### S. Image registry, build provenance and staged deployment

| Choice | Counterfactual challenge | Stability note |
|---|---|---|
| Publish promoted Paseo+Pi images to a registry as well as deploying them locally on Unraid. | Local-only images are simpler but make recovery/rollback less portable. | Stable. |
| Prefer GHCR as the default registry candidate unless later implementation research finds a materially better local option. | A local registry can avoid external dependency but adds another service to maintain. | Stable direction; exact registry may be revisited on evidence. |
| Keep the image repository private. | Public images are easier to distribute but expose tooling/capability structure without current benefit. | Stable. |
| Build only from an exact Git commit SHA, never an unidentified working tree. | Working-tree builds are convenient but weaken provenance/reproducibility. | Stable. |
| Add OCI provenance labels such as source repository, exact commit SHA and build metadata to produced images. | Omitting labels saves trivial metadata but harms diagnosis. | Stable. |
| The `latest` tag is assigned only after a candidate passes the required smoke/promotion gate; a merely successful build does not automatically become `latest`. | Tagging every build latest is simpler but can expose unvalidated candidates. | Stable. |
| Failed/debug candidates may keep immutable identities for diagnosis but must never receive the promoted `latest` alias. | Deleting all failed candidates immediately loses useful failure evidence. | Stable. |
| Production deployment resolves and records an immutable tag/digest even when the user-facing selection policy is `latest stable`. | Deploying by floating tag obscures the exact running artifact. | Stable. |
| Record the exact running image digest/identity in operational state/evidence. | Container-name-only state is insufficient for reliable rollback diagnosis. | Stable. |
| Keep at least one prior known-good promoted image locally even when registry copies exist. | Registry-only rollback saves disk but is slower and depends on external availability. | Stable. |
| Garbage-collect older promoted images automatically after retaining a bounded recent known-good set; exact count is an implementation choice. | Unlimited retention wastes storage; exact retention count need not be frozen now. | Stable. |
| Failed/debug images may use shorter retention than promoted images. | Equal retention is simpler but wastes storage on non-production candidates. | Stable. |
| The self-hosted build runner may have the Docker-host access needed for build/push/test operations. | Refusing host Docker access would complicate local build/test orchestration. | Stable. |
| Keep build-runner capability operationally separate from the Paseo runtime so a broken Paseo instance does not remove the ability to rebuild/recover it. | Co-locating everything is simpler but creates circular recovery dependency. | Stable. |
| Use Docker/BuildKit layer caching for builds. | Cacheless builds are maximally clean but unnecessarily slow routine updates. | Stable. |
| Build caches are disposable and excluded from protected backup. | Backing them up reduces cold-build time but bloats recovery state with reproducible data. | Stable. |
| Run fast static/unit/build validation before admitting an image to runtime smoke. | Skipping early checks wastes runtime-smoke time on obvious failures. | Stable. |
| Run the candidate image in a separate temporary container for pre-deploy runtime smoke before touching production. | Testing only after cutover increases production disruption risk. | Stable. |
| Production cutover occurs only after candidate pre-deploy smoke is GREEN. | Immediate cutover is faster but weakens rollback confidence. | Stable. |
| After cutover, run a bounded post-deploy smoke; if it fails and rollback is safe/unambiguous, automatically restore the previous known-good image. | Waiting for manual rollback prolongs a known-bad production state. | Stable. |
| Update validation must be tiered and time-proportional: routine updates use cached/fast checks plus bounded runtime smoke, while exhaustive E2E/regression is reserved for first deployment, material control-plane/security/Relay changes, failures, or explicit full validation. | Running every possible test on every routine update would make maintenance unnecessarily slow. | Stable clarification prompted by user concern about update duration. |

## Material dependencies / unresolved decisions

The following remain open and should drive subsequent grilling rather than being guessed during implementation.

| Decision | Prerequisites | Status |
|---|---|---|
| Exact image build/publish path: local Unraid build vs self-hosted runner/registry flow. | Current Unraid runner/deployment capabilities and desired rollback ergonomics. | open |
| Exact image tag strategy in addition to user-facing `latest` (e.g. immutable build tag/digest retention). | Build/publish path. | open |
| Exact policy for who/what initiates Paseo/Pi `latest` updates and whether version checks are on-demand or scheduled. | Update/rollback mechanics. | open |
| Exact meaning of `latest` regarding stable releases versus prerelease/beta/nightly channels. | Upstream release practices for Paseo and Pi. | open |
| Exact full-administrative Unraid access transport and precedence for Main (e.g. Unraid MCP/integration, API token, Docker-host control, SSH primary/fallback). | Capability/security/ergonomics comparison and failure-mode testing. | open |
| Exact secrets materialization method for each CLI/provider that insists on a HOME file versus env/secret mount. | Verified upstream auth/config behavior. | open |
| Exact browser-control extension/MCP layer above Chromium+Playwright, if any. | Later browser-control research/selection; current choice covers runtime only. | open |
| Exact PWv2.1 Pi-extension packaging, installation, discovery/bootstrap, helper-less fallback and relationship to global/project AGENTS.md after PWv2.1 final contract stabilizes. | Final PWv2.1 Definition/implementation contract. | open |
| Exact capability inventory schema/reconciliation command shape. | Definition/implementation design; user-facing policy is already settled. | open |
| Exact doctor command/check matrix and which checks are quick vs full. | Concrete container/tool layout. | open |
| Exact Relay deployment/pairing behavior and persistence details against the then-current Paseo release. | Fresh upstream verification before Definition/implementation. | open |
| Exact retirement/delete procedure for the unused bootstrap container/appdata after Paseo GREEN. | Final deployment acceptance and rollback window. | open |

## Research needed before Definition/implementation

- Re-verify current Paseo Docker/provider/Relay/security/session behavior and current image conventions at the time Definition begins.
- Re-verify current Pi installation/package/global extension paths and latest release/install semantics.
- After PWv2.1 reaches a stable final contract, research/design its Pi-extension packaging and the minimal bootstrap relationship among the extension, global/project AGENTS.md and helper-less recovery.
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
- **Permanent narrow Paseo-only host deployment helper as Main's sole host-control path: superseded.** Main is intended to receive full Unraid administration; the exact preferred and fallback transport remains open for later research.

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
