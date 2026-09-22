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
