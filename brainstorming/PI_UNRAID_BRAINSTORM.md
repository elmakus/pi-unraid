# Pi on Unraid — Brainstorming

Status: brainstorming
Date: 2026-09-22
Repository: `elmakus/pi-unraid`

## Why this exists

The immediate goal is to evaluate **Pi as a real coding harness on the existing Unraid host** without changing or replacing the current ChatGPT CE workstation.

The first installation should deliberately stay small:

- one isolated Pi container;
- one ChatGPT Plus/Pro account authenticated directly through Pi OAuth;
- persistent Pi configuration, credentials and sessions;
- one or more explicitly mounted project directories;
- no dependency on Codex-LB, OpenCodex, Muse, ChatGPT-Web or the existing workstation.

This is an evaluation environment first. If Pi proves useful, this repository can become the reproducible Unraid deployment source.

## Facts verified from current Pi documentation

- Pi officially documents **Plain Docker** as a supported isolation pattern.
- The current official Docker example uses Node 24 and installs `@earendil-works/pi-coding-agent`.
- Pi's default persistent agent directory is `~/.pi/agent`.
- `PI_CODING_AGENT_DIR` can relocate the entire config directory.
- Pi supports ChatGPT Plus/Pro through `/login` using the OpenAI Codex subscription provider.
- OAuth credentials are stored under the Pi agent directory and refresh automatically.
- Pi sessions are persistent and are also stored under the agent directory unless separately overridden.
- Pi extensions may be global or project-local; installed packages/extensions therefore need to live on persistent storage if they should survive container recreation.
- Pi intentionally has a minimal core and is expected to be extended with packages/extensions.

Primary references:

- https://pi.dev/docs/latest/containerization
- https://pi.dev/docs/latest/environment-variables
- https://pi.dev/docs/latest/providers
- https://pi.dev/docs/latest/extensions
- https://pi.dev/docs/latest/sessions

## Candidate v0 architecture

```text
Unraid
|
+-- pi-unraid container
|   |
|   +-- Pi runtime
|   |    +-- ChatGPT OAuth: one account only for initial evaluation
|   |    +-- sessions
|   |    +-- settings
|   |    +-- extensions/packages
|   |
|   +-- persistent Pi state
|   |    host: /mnt/user/appdata/pi-unraid/...
|   |
|   +-- project mount(s)
|        host: selected /mnt/user/projects/... paths
|
+-- existing chatgpt-ce-workstation
     unchanged and independent
```

The first deployment should **not** mount the Docker socket, host root, or unrelated appdata.

## Persistence choices to decide during planning

Two reasonable layouts exist.

### A — Preserve Pi's native path

```text
/mnt/user/appdata/pi-unraid/agent
    -> /root/.pi/agent
```

Advantages:

- exactly matches Pi's documented Docker layout;
- least custom configuration.

### B — Unraid-style /config

```text
/mnt/user/appdata/pi-unraid/config
    -> /config

PI_CODING_AGENT_DIR=/config
```

Advantages:

- familiar Unraid convention;
- explicit separation between application image and durable state.

Both preserve auth, settings, sessions and installed Pi resources. No choice is frozen during brainstorming.

## Project mount strategy

Three levels are possible.

### Conservative initial test

Mount one expendable or test repository:

```text
/mnt/user/projects/<test-repo>
    -> /workspace
```

This gives the cleanest filesystem boundary.

### Normal single-project use

Launch Pi with a selected repository mounted at `/workspace`.

This fits Pi's model well because the current working directory represents the active project.

### Future multi-project host

Expose a projects root, for example:

```text
/mnt/user/projects
    -> /projects
```

and start/resume Pi in individual directories beneath it.

This is more convenient but grants Pi access to every mounted repository. It should be a deliberate later choice rather than the v0 default.

## Container identity / file ownership

This needs an explicit implementation decision before deployment.

Questions:

- Run Pi as root inside the isolated container, matching Pi's simplest official Docker example?
- Or run with a UID/GID matching the Unraid user-share ownership?
- Which choice preserves correct Git/file ownership for bind-mounted repositories?
- Do npm-installed extensions/packages require any writable paths outside the persistent Pi directory?

Acceptance should include creating/editing a file in a mounted test repository and verifying ownership from the Unraid host.

## Initial authentication scope

For v0:

```text
Pi
  -> one ChatGPT Plus/Pro OAuth account
```

No account pooling yet.

Reasons:

- isolates evaluation of Pi itself;
- avoids confusing harness behavior with routing behavior;
- makes failures easier to diagnose;
- lets us verify OAuth persistence across container recreation first.

If Pi is retained, multi-account routing becomes a separate decision.

## Multi-account direction — deferred

Two future approaches remain viable:

### Pi-native / extension-managed accounts

```text
Pi
+-- ChatGPT account A
+-- ChatGPT account B
+-- ChatGPT account C
```

Pros:

- fewer external services;
- everything stays inside Pi.

Cons:

- behavior depends on a Pi extension/account-routing implementation;
- account pooling becomes coupled to the selected harness.

### Codex-LB as a dedicated account pool

```text
Pi
  -> Codex-LB
       +-- ChatGPT account A
       +-- ChatGPT account B
       +-- ChatGPT account C
```

Pros:

- centralizes account quotas/routing outside the harness;
- easier to reuse the same pool from Pi, OMP, Codex or other clients;
- keeps Pi focused on harness behavior.

Cons:

- another service and network hop;
- Codex-specific compatibility needs explicit verification.

No decision should be made until the one-account Pi test is successful.

## Extensions — deliberate staged approach

Do **not** try to turn Pi into OMP before evaluating Pi.

### v0

Use Pi as close to stock as practical.

Possible exception: nothing beyond what is needed to make the container usable.

### v1 after basic acceptance

Evaluate additions one at a time:

- remote/mobile control;
- web search;
- subagents;
- MCP;
- LSP;
- browser automation;
- richer session/project GUI.

Each extension should earn its place through a concrete requirement.

This makes it possible to tell whether Pi's minimal harness is itself attractive before recreating OMP through extensions.

## Remote/mobile — deferred but important

Desired end-state behavior is similar to Codex Remote:

- start a Pi session on Unraid;
- view/control the same session from Android;
- see tool activity;
- resume prior sessions;
- ideally navigate projects/sessions rather than only attaching to one terminal.

Candidate approaches include Pi remote extensions and web/desktop frontends, but v0 should not depend on them.

A later evaluation should distinguish:

1. **remote control of one live session**, and
2. **GUI for browsing projects and historical sessions**.

These are separate requirements.

## GUI — deferred

Pi itself is terminal-first.

The desired GUI experience, if adopted later, is:

```text
Projects
+-- project A
|   +-- session 1
|   +-- session 2
|
+-- project B
    +-- session 1
```

A GUI should ideally reuse Pi's real persistent session store rather than create a second independent history.

No GUI should be selected until the base Pi container/session lifecycle is proven.

## Web / research capability — deferred

Pi core should not be judged solely by whether it ships a built-in browser/search tool.

If Pi is retained, evaluate a web-search extension separately and compare it against current Codex research behavior using the same task.

Important distinction:

- retrieval/search backend;
- model reasoning over search results;
- harness decisions about when/how often to search.

## Future providers — explicitly out of v0

Potential later targets:

```text
Pi
+-- ChatGPT/Codex
+-- Muse
+-- chatgpt-web/*
+-- other providers
```

### Muse

Pi already supports Meta Muse subscription login, but it is intentionally excluded from the first test.

### ChatGPT Web / browser-backed models

A future Pi provider/adapter may expose `chatgpt-web/*` through the existing browser-backed service.

This is a separate integration project because plain model access and the current Codex-specific Full Harness bridge are not the same problem.

### OpenCodex

Do not insert OpenCodex merely because it exists in the workstation architecture.

If Pi becomes the selected harness, provider topology should be reconsidered from Pi's capabilities rather than copied from the Codex/ChatGPT CE design.

## Relationship to existing workstation

The existing workstation is a baseline and fallback, not a dependency.

```text
chatgpt-ce-workstation   Pi on Unraid
       |                     |
       |                     |
       +---- independent -----+
```

The Pi experiment must not:

- alter ChatGPT CE;
- alter CE's bundled Codex;
- change existing OpenCodex/Codex-LB routing;
- reuse workstation secrets by mounting its home;
- require stopping the workstation.

## Relationship to Project Workflow v2

Pi is being evaluated as a possible future harness for Project Workflow v2.

That does **not** mean the first Pi deployment should embed Project Workflow.

First establish:

1. Pi works reliably on Unraid.
2. sessions/auth survive recreate;
3. real coding tasks are comfortable;
4. desired extensions/mobile/GUI are feasible.

Only then test whether Project Workflow v2's execution/review contracts remain harness-agnostic enough for Pi.

## Proposed v0 success criteria

The initial container is successful when all of the following are true:

1. Pi starts interactively on Unraid.
2. One ChatGPT Plus/Pro account can authenticate through Pi.
3. Authentication survives container restart/recreation.
4. A Pi session can be created, exited and resumed.
5. Session history survives container recreation.
6. Pi can read and edit a deliberately mounted test repository.
7. Files written by Pi have acceptable ownership/permissions on the host.
8. Git operations work inside the mounted repository.
9. Pi has no Docker socket, host-root mount or unintended appdata access.
10. Installed configuration/resources can be made reproducible from this repository.
11. One real coding task is completed and compared qualitatively with the existing Codex experience.

## Likely repository deliverables after brainstorming

If this direction is accepted, planning can decompose implementation into a small first milestone:

```text
Dockerfile
compose.yaml
.env.example / documented environment
scripts or runbook for interactive attach/login
persistent appdata mapping
project mount strategy
source validation / smoke test
README
```

Optional remote/GUI/provider work should be later milestones, not bundled into the first container.

## Open questions for the next phase

- Native Pi path vs Unraid-style `/config`?
- Exact UID/GID strategy on Unraid?
- One fixed project mount vs projects-root mount?
- Should the container stay alive continuously, or be an on-demand interactive service?
- What is the preferred attach UX from Unraid/SSH?
- Which real repository/task should be the first Pi-vs-Codex comparison?
- After base acceptance, which comes first: remote control, GUI, web search, or subagents?
- If multiple ChatGPT accounts are added later, use Pi extensions or Codex-LB?
- If Pi becomes primary, should Muse connect directly to Pi?
- Is browser-backed `chatgpt-web/*` valuable enough to justify a Pi-specific adapter?


## Grill decisions

### G01 — Primary user experience

Accepted:

- Pi runs as an always-available service on Unraid.
- The **primary UI is a browser-based Web UI**, not noVNC and not a local desktop GUI.
- From a PC, the UI must allow browsing/selecting multiple projects and opening/resuming multiple historical sessions.
- Android must expose the **same project/session navigation**, not merely attach to one currently running terminal/session.
- A native Android app is preferred if a good one exists, but it is **not a hard requirement**; a mobile-capable Web UI is acceptable.
- noVNC/desktop GUI is out of scope for the Pi deployment unless a future concrete requirement appears.

Open follow-up: decide whether the project should depend on an existing third-party Pi Web UI, require an official/native Pi surface, or own a thin repository-managed frontend.


### G02 — Session lifetime and concurrency

Accepted:

- Browser disconnect, tab close or navigation away must **not** terminate the Pi session.
- Active sessions continue running on Unraid independently of the client UI.
- Reopening the Web UI must reconnect to the existing session and current state.
- Multiple Pi sessions may run concurrently.
- Concurrency must work across different projects and may also be needed within the same project.
- The Web UI therefore cannot be only a terminal attachment layer; the backend needs durable session/process ownership independent of any one browser connection.


### G03 — Project, worktree and session identity

Accepted:

- One Pi project should normally correspond to one Git repository / GitHub repository.
- Active implementation work must not be performed directly on `main`.
- Independent workstreams/tasks may use their own branch + Git worktree so concurrent work does not share a mutable checkout.
- **A Pi session is not the same thing as a branch or worktree.**
- Multiple sessions may intentionally attach to the same existing branch/worktree when they belong to the same ongoing workstream/task.
- A historical session must retain enough workspace identity to reopen against the intended checkout/worktree rather than silently attaching to some other branch.
- `pi-unraid` should provide the runtime/storage capability for this model, but should **not hard-code the policy that creates a new branch/worktree for every new session**.
- Higher-level workflow policy (for example Project Workflow V2) may decide when branches/worktrees are created, reused, reviewed, merged or retired.
- The Pi deployment must therefore be able to operate both:
  1. on an existing repository checkout/worktree selected by the caller/user; and
  2. with multiple isolated worktrees of the same repository active concurrently.

Deferred:
- whether the Web UI itself should offer convenience actions for creating/selecting worktrees;
- exact branch naming and merge policy;
- exact Project Workflow V2 ownership of branch/worktree lifecycle.


### G04 — Project discovery and creation

Accepted:

- The Web UI must discover and show repositories that already exist under the configured local projects root.
- The Web UI should also provide a **Clone from GitHub** path for creating a new local Pi project from a GitHub repository.
- A normal project identity should preserve the Git repository/repository-name relationship rather than inventing a second unrelated project identifier.
- Cloning a repository should create the local project in the configured projects root and make it immediately available to Pi sessions.
- Existing local repositories must not need to be re-imported or recreated merely to appear in the UI.

Deferred:
- exact GitHub authentication method used by the Web UI/backend;
- whether repository discovery is automatic, refresh-based or explicit;
- whether non-Git local folders are supported as first-class Pi projects.


### G05 — GitHub authentication and agent access

Accepted:

- Use **SSH** as the normal Git transport for repository clone/fetch/push.
- Also install and authenticate **GitHub CLI (`gh`)** for GitHub API operations such as pull requests, review/status inspection, issues and Actions/CI.
- These are complementary capabilities, not redundant alternatives:
  - SSH owns Git transport;
  - `gh` owns higher-level GitHub operations.
- Credentials/state for both must persist across container recreation and remain outside Git.
- Agents should have the GitHub permissions needed for the intended development workflow, including pushing feature branches and operating pull requests/CI, subject to the GitHub account/repository permissions.
- Direct work/push to protected `main` is not the intended development path; normal work happens on branches and is integrated through the accepted review/merge workflow.

Deferred:
- exact SSH key provisioning method;
- exact `gh` authentication/token mechanism and scope;
- whether destructive GitHub operations need an additional policy/approval layer.


### G06 — Agent GitHub autonomy

Accepted:

- Agents may have full operational GitHub autonomy within the permissions granted to the configured GitHub identity.
- This includes creating/pushing branches, creating/updating/merging pull requests, deleting branches, managing releases and performing other repository operations when needed by the active workflow.
- The Pi deployment itself should not introduce an additional mandatory human-approval gate for these GitHub actions.
- Higher-level workflow rules may still define the preferred development process, but the runtime credentials/capabilities should not artificially block the agent from completing an authorized workflow end to end.

### G07 — Projects root exposure

Accepted:

- The Pi container may access the full configured projects root (initially expected to map the Unraid projects share).
- The Web UI must treat each Git repository under that root as a distinct project rather than exposing the entire root as one undifferentiated workspace.
- Repository/project discovery must avoid presenting Git worktrees as duplicate top-level projects unless explicitly desired.

### G10 — Web UI ownership strategy

Accepted:

- Start with the best suitable existing Pi Web UI rather than building a custom frontend from scratch.
- Keep Pi's durable projects/session state independent from that frontend so the UI can be replaced later without losing projects, sessions or history.
- Any chosen frontend is therefore a replaceable client/control surface, not the canonical owner of Pi session data.

### G11 — Network access

Accepted:

- The primary Web UI must be reachable on the trusted LAN.
- Remote access outside the home network should use Tailscale rather than direct public Internet exposure.
- PC and Android should reach the same Pi service and project/session state through this path.

### G12 — Web UI authentication boundary

Accepted:

- No separate Pi Web UI username/password is required initially.
- Access control is provided by trusted-LAN reachability and Tailscale.
- Direct public exposure is not part of the accepted initial design.


### G08 — Worktree storage and policy boundary

Accepted:

- Use a dedicated global worktree root separate from the canonical projects root, for example:
  - host: `/mnt/user/pi-worktrees`
  - container: `/worktrees`
- Canonical repositories remain under the projects root and are not cluttered with embedded `.worktrees` directories.
- Worktree placement is standardized by the Pi runtime environment, but branch/worktree **creation, reuse, merge and retirement policy belongs to the higher-level workflow** (for example Project Workflow V2).
- Sessions may bind to an existing worktree path and must resume against that same path.
- Web UI project discovery must not treat worktree directories as duplicate top-level projects by default.

### G09 — Persistent backend-owned sessions

Accepted:

- The container/service remains available continuously.
- Starting a Pi session from Web UI creates/attaches to a backend-owned session/process on Unraid.
- Closing the browser tab, browser, phone app or network connection must not terminate the Pi session.
- A running session may continue working while no UI client is connected.
- Reopening the Web UI reconnects to the existing session state.
- Multiple backend sessions may run concurrently across projects/worktrees.


### G13 — Pi state path

Accepted:

- Preserve Pi's native agent-state layout under `~/.pi/agent` rather than relocating it to a generic `/config` path.
- The host bind/volume must persist that native path across container recreation.
- Auth, settings, sessions and installed Pi resources that belong under the native agent directory must survive rebuild/recreate.

### G15 — Terminal fallback

Accepted:

- Web UI is the normal user interface.
- The deployment must also allow direct terminal/TUI access for debugging, recovery and advanced use (for example through `docker exec` or an equivalent container shell path).
- Terminal access is a fallback/maintenance capability, not the primary daily UI.

### G16 — Pi update policy

Accepted:

- Prefer the latest available Pi release rather than deliberately pinning a long-lived version.
- Container update/rebuild flow should advance Pi to the current release.
- Exact reproducibility/provenance mechanics may be added later if needed; the product preference is freshness over a permanent fixed pin.

### G17 — Extension/package lifecycle

Accepted:

- Extensions/packages may be installed experimentally at runtime with agent assistance.
- Runtime experimentation is allowed and does not require every trial package to be declared in repository source first.
- Once an extension/package is accepted as part of the normal setup, its installation/configuration should be captured reproducibly in the repository so rebuild/recreate does not depend on memory or manual repetition.


### G14 — Container user and privilege model

Accepted:

- Run Pi as a non-root user whose UID/GID can be aligned with the Unraid project-share ownership.
- The Pi user must be able to read/write mounted repositories and worktrees without producing unintended root-owned files.
- Provide sudo inside the container for legitimate package/tool installation and maintenance tasks.
- The base deployment should not require Docker socket access, host-root mounts or equivalent host-level privilege.
- Broader future access to Unraid resources is intentionally deferred and must be added through an explicit mechanism rather than being implicit in the base container.

Deferred:
- exact PUID/PGID defaults;
- whether broader Unraid control later uses SSH, a skill/extension, MCP, or another bounded integration.

### G18 — Resource policy

Accepted:

- Do not impose hard CPU or RAM limits initially.
- Configure a reasonable container shared-memory size (`shm_size`) to avoid avoidable failures for browser/Chromium-style tooling or future extensions.
- Exact shared-memory sizing is a planning/implementation detail.

### G19 — Session persistence across restart

Accepted:

- After container/service restart or recreation, the Web UI must still show the same project list and the previously created sessions beneath each project.
- Session metadata/history must persist independently of the running process.
- A user must be able to reopen/resume a prior session after restart from the normal project/session UI.
- If the container was restarted while a tool/process was actively executing, that in-flight process is not required to continue automatically.
- The persisted session should instead be reopenable with enough history/state to continue intentionally.


### G20 — Backup boundary

Accepted:

- Do not build a separate Pi-specific backup subsystem.
- The existing Unraid appdata backup mechanism is the backup authority for Pi deployment state.
- All durable Pi state that must survive disaster/rebuild must therefore live under the Pi application's appdata boundary.
- Web UI durable configuration/state should also live under appdata when the selected frontend permits it.
- Git repositories themselves are not the primary backup target because their authoritative history is expected to live on GitHub.

### G21 — Pi backend and Web UI packaging

Accepted:

- Prefer a single `pi-unraid` container containing both the Pi backend/runtime and selected Web UI when that frontend architecture supports it cleanly.
- If the selected Web UI requires a separate service/container, using two containers is acceptable.
- Packaging simplicity is preferred, but not at the cost of forcing an unsuitable frontend/runtime design.
- Durable session/project state must remain independent of whether the UI is colocated or split.

### G22 — Android client experience

Accepted:

- The Web UI must be mobile-friendly and support installation/use as a PWA where practical.
- PWA behavior is the minimum preferred Android experience beyond plain browser tabs.
- A native Android app is highly desirable but is not a hard dependency for the initial deployment.
- Any future native app should connect to the same project/session backend rather than create a separate history silo.

### G23 — Notifications

Accepted:

- Initial notification target: Web/PWA push notifications from the selected frontend when practical.
- Desired events include at least session completion and waiting-for-user/attention states.
- A later phase may add UI-independent notifications through a dedicated channel such as Home Assistant, ntfy, Gotify or equivalent.
- The initial deployment should not block on the external notification integration.

### G24 — Future Unraid host control

Accepted:

- Long-term target is to support both:
  1. structured MCP/tools for common Unraid operations; and
  2. SSH access as a full-capability fallback/administration path.
- The base Pi container does not receive implicit unrestricted host access merely because this is the future target.
- Exact Unraid MCP/tool/SSH design is deferred to a dedicated later integration decision.

### G25 — GitHub-first project lifecycle

Accepted:

- Move away from ordinary local-folder-only projects.
- Every newly created normal Pi project should be initialized as a Git repository and have a corresponding GitHub repository created/attached automatically.
- The local project and GitHub repository should normally share the same project/repository name.
- Existing GitHub repositories can be cloned/imported as projects.
- A future Pi equivalent of the existing `newproject-skill` should automate project creation, Git initialization, GitHub repository creation, remote setup and initial push.
- Non-Git local folders are not a desired first-class normal workflow.

Deferred:
- public vs private default;
- organization/owner selection;
- initial branch protection/repository settings;
- exact skill/extension implementation.

### G26 — Session titles

Accepted:

- Sessions should receive an automatic useful title by default.
- The user must be able to rename a session manually.
- Session identity/history must not depend on the editable display title.


### G27 — Default GitHub repository visibility

Accepted:

- New-project automation asks for repository visibility when creating a GitHub repository.
- The interaction should make the visibility choice explicit rather than silently forcing one global policy.
- `private` is the preselected/default choice.
- The user can switch to `public` per project before creation.

### G28 — Main branch protection

Accepted:

- Normal repositories should protect `main` so active development does not push directly to it.
- Changes reach `main` through branch/PR integration.
- Agents may themselves satisfy the required checks/review conditions and merge the PR without an additional mandatory human approval when repository/workflow policy allows it.
- This preserves agent autonomy while technically enforcing the branch/PR development model.

### G29 — New-project automation

Accepted:

- A future Pi new-project skill/extension should automate the complete normal bootstrap path:
  - create local project directory;
  - initialize Git;
  - create matching GitHub repository;
  - configure `origin`;
  - create the initial commit;
  - push the repository;
  - make the resulting repository immediately available/openable as a Pi project.
- The normal path should not stop for a separate pre-push confirmation after the project creation command has been authorized.

### G30 — Initial model/provider scope

Accepted:

- First Pi deployment uses one ChatGPT Plus/Pro OAuth account directly in Pi.
- Do not add Muse, Codex-LB, OpenCodex, multi-account routing or ChatGPT-Web to the first acceptance slice.
- The purpose of v0 is to evaluate Pi itself before introducing routing/provider complexity.

### G31 — Per-session model controls

Accepted:

- The Web UI should expose model selection per session.
- Thinking/reasoning effort should also be selectable per session when supported by the selected provider/model.
- A session may later switch model/effort without requiring a separate project.
- Model/effort are session/runtime choices, not project identity.

### G32 — Web search in v0

Accepted:

- Web search is required in the first useful Pi setup; stock Pi without Internet research is not the intended daily baseline.
- Select a high-quality Pi web-search extension through explicit research rather than choosing the first available package.
- The chosen solution should be evaluated for:
  - search quality;
  - source/citation usefulness;
  - compatibility with ChatGPT/Codex OAuth;
  - ability to use provider-native/hosted search where useful;
  - maintenance/activity and security;
  - behavior in multi-step research rather than only one-shot queries.
- Exact package selection remains open pending bounded extension research.

### G33 — Subagents in v0

Accepted:

- Subagent capability is required in the first useful Pi setup.
- Select a mature Pi subagent extension through explicit research rather than freezing an arbitrary package during brainstorming.
- Evaluation should cover:
  - independent child context;
  - model selection per child where supported;
  - parallel and sequential delegation;
  - result return to parent;
  - cancellation/failure handling;
  - persistent/session behavior;
  - compatibility with future Project Workflow V2 execution/review semantics.
- Exact package selection remains open pending bounded extension research.

### G34 — Web UI minimum acceptance surface

Accepted MUST requirements:

- project browsing;
- historical session browsing/resume;
- multiple concurrent sessions.

Mobile/PWA:

- strong SHOULD rather than a hard blocker;
- responsive Android use is still expected;
- installable PWA behavior is preferred;
- a native Android app remains a desirable bonus.


### G35 — Projects root

Accepted:

- Host projects root: `/mnt/user/projects`.
- Container projects root: `/projects`.
- Pi should use the same durable Unraid project repository root rather than creating a separate Pi-only project share.

### G36 — Worktrees root

Accepted:

- Host worktree root: `/mnt/user/pi-worktrees`.
- Container worktree root: `/worktrees`.
- Keep worktrees physically separate from canonical repositories under `/mnt/user/projects`.

### G37 — GitHub repository owner

Accepted:

- New-project automation creates repositories under the GitHub owner `elmakus`.
- Do not prompt for alternate owner/organization in the normal creation path.
- Support for alternate owners/orgs may be added later only if a concrete need appears.

### G38 — Project/repository naming

Accepted:

- Normal project name, local canonical repository directory name and GitHub repository name are identical.
- This one-name rule is the default project identity convention.

### G39 — Base development image

Accepted:

- Use a reasonably complete development base rather than an ultra-minimal Pi-only image.
- Initial image should include common tooling needed by coding agents, including at least:
  - Node/runtime required by Pi;
  - Python;
  - Git;
  - OpenSSH client;
  - GitHub CLI;
  - curl;
  - jq;
  - ripgrep;
  - fd/find tooling;
  - archive/unzip utilities;
  - standard build toolchain/build-essential or equivalent.
- Avoid turning the image into an all-SDK workstation without a concrete requirement.

### G40 — Runtime tool installation and reproducibility

Accepted:

- Agents may install additional tools/packages at runtime with sudo when needed for experimentation or a task.
- Runtime-only installation is acceptable temporarily.
- If a tool becomes part of the normal expected Pi environment, its installation must be captured in the repository/image definition so recreate/rebuild remains reproducible.

### G41 — Web UI development views

Accepted SHOULD:

- Prefer a Web UI that also provides useful development context such as:
  - file tree;
  - diff viewer;
  - Git status;
  - current branch/worktree visibility.
- These features are desirable but are **not hard blockers** if the strongest Web UI for projects/sessions/concurrency lacks them.
- Core Web UI acceptance remains governed by G34.

### G42 — Integrated Web UI terminal

Accepted:

- An integrated terminal inside the Web UI is not required.
- Terminal/TUI recovery and advanced access are already provided through the container access path defined by G15.
- A frontend may include a terminal, but its presence must not drive frontend selection.

### G43 — Session workspace binding

Accepted MUST:

- A session opened in a particular repository checkout/worktree remains bound to that exact workspace path.
- Reopening/resuming the session must return to the same worktree/checkout rather than silently switching to the canonical repository or another branch.
- Branch name alone is insufficient session identity when multiple worktrees may exist.

### G44 — Logs and diagnostics

Accepted:

- Preserve normal Docker/container logs.
- Also keep readable Pi backend/Web UI diagnostic logs under durable appdata where the selected components support file logging.
- Full metrics/observability infrastructure is not required initially.


### G45 — Persistent home boundary

Accepted:

- Persist the entire Pi service user's home directory under Unraid appdata rather than mounting only individual state subdirectories.
- Target shape:
  - host: `/mnt/user/appdata/pi-unraid/home`
  - container: `/home/pi`
- This persistent home should contain Pi state plus user-level credentials/configuration such as:
  - `~/.pi`;
  - `~/.ssh`;
  - GitHub CLI configuration;
  - user-level package/tool configuration;
  - other normal per-user state required by accepted extensions/tools.
- Repository source must never contain these credentials/secrets.

### G46 — Pi update-on-start policy

Accepted:

- The Pi runtime should check/install the latest available Pi release on normal container/service startup rather than remaining on the image-baked version until a rebuild.
- Restarting the deployment may therefore advance Pi when a newer release exists.
- Durable user state remains in persistent home and must survive the runtime update.
- The implementation must fail safely if an update cannot be completed; a failed update must not destroy persistent Pi state.
- Exact rollback/version-retention mechanics are deferred to planning/research.

### G47 — Tailscale placement

Accepted:

- Tailscale remains outside the Pi container/deployment.
- Pi/Web UI exposes the required service port(s) on the trusted host/LAN boundary.
- Existing host/network Tailscale reachability provides remote access to those services.
- Do not add a second Tailscale client inside the Pi container unless a future concrete need appears.

### G48 — HTTPS for Web UI/PWA

Accepted:

- Expose the normal Web UI through HTTPS so PWA/mobile browser features are not unnecessarily constrained by an insecure origin.
- HTTPS may be provided by an external reverse proxy, Tailscale Serve or another existing trusted ingress layer.
- TLS termination does not need to live inside the Pi container if the surrounding deployment provides it cleanly.

### G49 — Health checks

Accepted:

- Health checking should verify more than process existence.
- The deployment should check the relevant HTTP backend/Web UI health surface.
- Health should also verify that required persistent session/storage state is reachable enough for normal service operation.
- Exact endpoint/check implementation is deferred.

### G50 — Automatic deployment startup

Accepted:

- The complete Pi deployment starts automatically after Unraid/Docker restart using an `unless-stopped`-style policy.
- If Pi backend/runtime and Web UI are packaged in one container, that container owns the policy.
- If architecture requires separate backend and Web UI containers, **both** use automatic restart/startup behavior.
- Manual startup is not the normal operating model.

### G51 — Secret and credential storage

Accepted:

- Interactive/user credentials such as ChatGPT OAuth state, SSH private keys and GitHub CLI authentication may live in the persistent Pi user home/appdata with appropriate filesystem permissions.
- Do not require Docker secrets for these normal interactive credential stores.
- Secrets/credentials must never be committed to the repository or baked into the image.

### G52 — Bounded component research before implementation

Accepted:

- Before freezing implementation choices, perform a bounded current-source research phase comparing real candidates for:
  - Pi Web UI/project-session frontend;
  - web-search extension;
  - subagent extension;
  - Android/PWA/remote-control surface.
- Prefer official/upstream documentation and source first, then issues/trackers and relevant community evidence.
- The research should produce explicit candidate selection evidence rather than installing the first plausible package.


### G53 — Failed Pi update fallback

Accepted:

- Startup may attempt to advance Pi to the latest release.
- If the new release cannot be installed or started successfully, fall back to the last known working Pi runtime rather than leaving the whole service unavailable.
- Persistent user/session state must not be rolled back or destroyed merely because the runtime version falls back.
- Exact version-retention and rollback mechanics are deferred to planning.

### G54 — Session concurrency limit

Accepted:

- Do not impose an artificial global limit on the number of concurrent Pi sessions initially.
- Practical concurrency is bounded by host resources and provider/account limits.
- Monitoring or later guardrails may be added only if real usage shows a need.

### G55 — Multiple sessions on one worktree

Accepted:

- Do not enforce a hard one-session-per-branch/worktree lock in the Pi runtime.
- Multiple sessions may exist and may run against the same worktree concurrently.
- The UI/backend should preferably surface an advisory warning when another active session is already bound to the same worktree.
- Avoid introducing mandatory locking complexity at the base Pi runtime layer.
- Higher-level workflows may impose stricter lane/worktree discipline when they need it.

### G56 — Commit policy boundary

Accepted:

- Commit timing/content is governed by the higher-level workflow/task contract rather than an unconditional Pi runtime rule.
- Pi/agents must have the technical ability to commit, but the base deployment does not force automatic commits or mandatory user confirmation for every commit.

### G58 — Pull-request timing

Accepted:

- Pull-request timing is controlled by the active workflow.
- A workflow may open a draft PR early, wait until implementation is ready for review, or use another explicit lifecycle.
- The Pi runtime does not force one PR timing policy globally.

### G59 — Worktree cleanup after integration

Accepted:

- Default toward automatic cleanup after a confirmed successful merge/closure.
- Cleanup must not remove a worktree that still contains uncommitted/untracked work that would be lost.
- Cleanup should only occur once merge/integration success and the relevant workflow closure are known.
- Higher-level workflows may retain a worktree longer when needed.

### G60 — Session archival

Accepted:

- Closed/completed workstream sessions should remain durable and accessible.
- Prefer moving them to an Archived/inactive view rather than deleting them.
- Archived sessions remain reopenable for history/reference.
- Normal active-session views should not become cluttered indefinitely by completed work.
