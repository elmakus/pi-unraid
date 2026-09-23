# Research — Pi extension/tooling evaluation R1

- Research ID: `pi-extension-evaluation-r1`
- Status: `complete`
- Origin role: `other`
- Origin subject: `change-pi-extension-evaluation`
- Return target: `project_definition:pi-extension-tooling-selection-r1`
- Research question: Evaluate the shortlisted Pi extensions/tools and MCP integration options for a clean Pi + Paseo setup; verify unresolved behavior/compatibility; identify prior art that could materially improve a future Pi-oriented Project Workflow revision and native subagent design.
- Return reconciliation: `pending`
- Return reconciliation result: `none`

## Constraints and already-accepted user choices

Target architecture assumptions:
- clean Pi, not `pi-code` or OMP;
- Paseo as the intended primary GUI/Android remote;
- PWv2 remains current workflow authority; external orchestration must not silently become a second authority source;
- MCP usage is required;
- research may identify PWv3 ideas, but does not authorize PWv2 mutation.

Accepted by user:
- `rpiv-ask-user-question`;
- `pi-permission-system`;
- `pi-lens`;
- loop detector / `pi-antiloop`;
- `pi-skill-gate`;
- Paseo as primary Pi UI/remote.

Rejected by user:
- `@narumitw/pi-lsp`;
- `pi-file-context`;
- `pi-btw`;
- `pi-zentui`;
- `pi-code`;
- Pi Desktop.

## Findings

### 1. pi-web-access vs Ketch; impact on Context7

#### pi-web-access

Upstream: https://github.com/nicobailon/pi-web-access

`pi-web-access` is a Pi-native extension. It exposes web search/content extraction and supports many search/extraction providers. Its scope is broader than plain search: current upstream also includes GitHub-aware handling and video/YouTube-oriented paths.

Relevant architecture finding: current versions do not need to put the entire web surface into the model tool list from the first turn. The extension can start with a compact activation surface and enable the web tools when needed, so the context-cost objection is weaker than a naive "all web schemas always loaded" model.

Advantages for this project:
- native Pi tools and native tool-call rendering;
- no shell command serialization needed;
- broad provider/fallback support;
- richer web-specific functionality.

Costs/risks:
- larger Pi-specific extension surface;
- overlaps with other research/documentation tools;
- more extension-owned behavior to validate through Paseo RPC.

#### Ketch

Upstream: https://github.com/1broseidon/ketch

Ketch is a stateless Go CLI rather than a Pi extension. It provides:
- `ketch search` — web search;
- `ketch code` — public source-code search;
- `ketch docs` — Context7-backed docs;
- `ketch scrape` / `crawl`;
- structured `--json` output and documented exit-code semantics;
- `ketch mcp serve` exposing the same research surfaces as MCP tools.

Advantages for this project:
- agent-agnostic, reusable outside Pi;
- one binary/no daemon for the CLI path;
- code search is first-class rather than incidental;
- can be used through Bash/skill or through MCP;
- clean failure semantics for deterministic workflow/tooling.

Costs/risks:
- normal CLI use depends on Bash/tool permission policy;
- less Pi-native UX;
- `ketch docs` currently requires a free Context7 API key.

#### Current conclusion

No final choice yet. Both remain viable and should be evaluated on the actual Pi/Paseo deployment.

A useful future experiment is:
1. same bounded research task with `pi-web-access`;
2. same task with Ketch as a skill/CLI;
3. compare model tool behavior, result quality, latency, context growth and Paseo rendering.

Context7 consequence:
- if Ketch wins and `ketch docs` is sufficient, a separate Context7 Pi extension is probably unnecessary;
- if `pi-web-access` wins, dedicated current-library docs remain useful, but Context7 can be provided through MCP rather than another Pi-specific extension;
- because MCP is already required, Context7-over-MCP is a strong low-coupling candidate.

### 2. pi-blackhole

Upstream: https://github.com/k0valik/pi-blackhole

`pi-blackhole` is two systems bundled together, which explains why community descriptions can be confusing.

#### A. Deterministic compaction

It replaces Pi's LLM-written compaction summary with an algorithmic structural compiler. It extracts useful categories such as goals, files/changes, commits, outstanding context/preferences and a bounded transcript tail.

Important distinction:
- the compaction algorithm itself does **not** call an LLM;
- therefore the compaction operation is fast and model-cost-free;
- upstream's demo reports roughly 143k -> 6.3k tokens, but that is a maintainer demo, not a guaranteed ratio.

Modes:
- `auto`: Blackhole owns threshold/overflow compaction;
- `manual`: background memory workers may still run, but Blackhole compaction occurs when explicitly requested;
- `off`: Pi owns normal compaction; explicit `/blackhole` remains available.

With `memory: false`, observational-memory workers are disabled independently of the compaction engine.

#### B. Observational memory

This **does use models**.

It runs background roles conceptually described as:
- Observer — extracts facts/decisions/events from the session;
- Reflector — distills durable higher-level observations/reflections;
- Dropper — prunes lower-value observations when the pool grows.

The workers support independent model/fallback configuration. This means "Blackhole is zero-cost" is only correct for deterministic compaction, not for the optional memory pipeline.

It also provides:
- a `recall` tool / `/blackhole-recall` for searching raw session history;
- IDs linking observations/reflections back to source entries;
- session/lineage-aware recall;
- `/blackhole-export` for exporting distilled project memory;
- per-session pending buffers in manual mode.

#### Fit with PWv2/PWv3

Strong candidate, but it must never become authority.

Rule required if adopted:
- Blackhole summaries/memory are convenience context and evidence locators only;
- repository durable state (`WORKSTREAM.yaml`, Task Board, requirements, decisions, evidence, Git/runtime readback) always wins on conflict;
- a remembered "task completed" fact cannot advance workflow state.

Recommended initial experiment:
- install Blackhole;
- first evaluate deterministic compaction with observational memory disabled;
- then separately evaluate memory with cheap worker models if wanted;
- compare recovery accuracy against native Pi compaction on long PWv2 runs.

This is one of the highest-value experiments in the list because long workflow sessions are a known context-pressure surface.

### 3. pi-fabric

Upstream: https://github.com/monotykamary/pi-fabric

Fabric gives the model one programmable `fabric_exec` surface. The model writes checked TypeScript (or configured Python) and can perform branches, loops, fan-out and dataflow inside one code-mode execution. Only the bounded result needs to return to the conversation.

This is materially different from asking the model to emit many independent nested JSON tool calls.

Useful PWv3 ideas:
- one flat model-facing capability surface;
- type-check tool composition before execution;
- parallel independent tool calls inside code;
- bounded final return with large intermediates kept outside conversation;
- capability discovery/search/describe rather than injecting every schema.

However Fabric also contains its own:
- agents;
- worktrees;
- workflows;
- actors;
- mesh/councils;
- durable coordination.

Those areas overlap strongly with PWv2/PWv3 authority/orchestration.

Current conclusion:
- research/use **code-mode and capability routing as prior art**;
- if installed for an experiment, initially constrain use to tool composition;
- do not adopt Fabric workflow/agent authority alongside PWv2 without an explicit architecture decision.

### 4. Laya / System One

Upstream: https://github.com/NandhaKishorM/laya

Laya is not a text-generating chat model. It is a non-autoregressive typed decision engine supporting operations such as:
- `choice`;
- `score`;
- calibrated boolean/probability-style decisions.

Its attraction is bounded cheap/fast classification rather than reasoning prose.

Potential PWv3 use:
- rank a closed list of candidate tools/skills;
- classify a bounded route;
- decide whether evidence belongs in one predeclared category;
- triage whether a larger model should be invoked.

Required safety/authority rule:
- System One output is evidence/classification, not workflow authority;
- low-confidence/ambiguous results escalate;
- it must not autonomously authorize strategic/user-owned/destructive decisions.

Upstream benchmark notes also make clear that checkpoint choice/calibration matters; raw confidence must not be treated as truth.

### 5. rpiv-todo

Current package: `@juicesharp/rpiv-todo`
Upstream moved to the `juicesharp/rpiv-mono` monorepo.

It gives the model a session-local task list with:
- pending / in_progress / completed / deleted states;
- `blockedBy` dependencies;
- cycle detection;
- live UI;
- replay from the conversation branch so it survives Pi reload/compaction.

This is **not** an appropriate replacement for the PWv2 Task Board because its lifecycle/authority is session-derived rather than repository-durable.

But the design is valuable prior art for PWv3:
- expose a small "current working queue" to the agent;
- dependency/cycle guards;
- visible progress UX;
- restore the working view after compaction/reload.

A promising design is to make any Pi todo layer a **derived execution view** of the canonical Task Board/Card, never an independently authoritative state machine.

### 6. Plannotator with Paseo

Plannotator can operate alongside Paseo, but current integration is not seamless.

Paseo issue #1125 is still open:
https://github.com/getpaseo/paseo/issues/1125

Reported behavior: after Plannotator feedback/approval drives the CLI forward, Paseo can leave stale plan approval cards visible. The issue explicitly requests first-class Plannotator support.

Conclusion:
- compatible enough to experiment;
- not suitable yet as a required baseline component for Paseo;
- evaluate after the base UI/workflow path is working;
- do not make PWv3 approval semantics depend on Plannotator-specific UI.

### 7. pi-github-pr

Package: `@narumitw/pi-github-pr`

This is **human-facing observability only** in its current design.

It passively reads current-branch PR/check/review/comment metadata through `gh` and displays status in Pi's statusline. It does not register a model tool and does not inject the PR content into model context.

Therefore:
- useful to a human working directly in Pi TUI;
- provides no material new capability to the agent;
- likely low value when Paseo is the primary UI.

The agent should use GitHub CLI/MCP/another explicit GitHub tool for actionable PR data.

### 8. Reddit capability-gap comment / SpecPi

Exact Reddit thread:
https://www.reddit.com/r/PiCodingAgent/comments/1wml882/what_extensions_do_you_think_are_essential_and/

The referenced commenter explicitly identifies **SpecPi** and its Harness Improvement Loop.

Verified mechanism:
1. user enables collection with `/wishlist on`;
2. when the model repeatedly hits a tooling/capability limitation, it can invoke the `wishlist` tool and record the capability gap;
3. later the user reviews logged gaps;
4. the user selects one through `/harness-improvement`;
5. SpecPi guides the agent through a bounded harness change and validation.

Docs:
https://tannermidd.github.io/SpecPi/wiki/

Critical architecture property: **detecting/logging a capability gap does not authorize changing the harness**. User selection remains the promotion gate.

This is excellent prior art for PWv3:
- add a durable "capability gap / workflow friction" inbox;
- allow Pi roles to report repeated missing abilities;
- preserve evidence such as role/task/tool/failure count;
- user or policy later promotes a gap into a normal Research/Definition/change workstream;
- never self-modify PWv3 merely because a worker complained.

### 9. External deterministic workflow-engine prior art

Dagu now has direct Pi harness support:
https://docs.dagu.sh/step-types/harness/pi

It can run Pi as a workflow step using `pi -p`, with explicit provider/model/thinking/tool allowlists. Dagu also supports structured output validation, retries, approval gates and deterministic DAG dependencies.

This validates a useful PWv3 architectural pattern:

`deterministic workflow state machine -> bounded Pi worker -> validated result -> next state`

rather than relying on one LLM conversation to own the entire lifecycle.

Current conclusion:
- do not add Dagu to the Pi bootstrap now;
- use it as prior art when evaluating whether parts of PWv3 should move from Markdown/router interpretation into executable deterministic state transitions.

### 10. Pi subagent prior art

Official Pi ships a subagent example where every subagent is a separate Pi process with an isolated context:
https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/subagent/README.md

A strong community implementation:
https://github.com/mjakl/pi-subagent

Useful mechanisms observed across current implementations:
- separate Pi process/session per child;
- fresh context by default;
- explicit model + thinking + tool allowlist per role/call;
- optional persistent named child sessions;
- explicit cwd;
- parallel calls;
- inactivity timeout/stall watchdog;
- depth and cycle guards;
- bounded model-facing result;
- optional parent snapshot only when deliberately requested.

These map closely to the desired PWv3/native-subagent contract.

PWv3 design candidate:
- thin role-runtime, not another autonomous orchestrator;
- router chooses role/model/tools/context;
- child gets a bounded package rather than the whole parent transcript;
- Tester/reviewer permissions enforced through tool allowlists/permission layer;
- mutating parallel children use isolated Git worktrees;
- result comes back as a structured bounded handoff/verdict;
- recursion/depth/concurrency limits are technical invariants.

Do not adopt a large multi-agent framework as workflow authority merely because it implements these useful primitives.

### 11. MCP for clean Pi + Paseo

#### Primary candidate: pi-mcp-adapter

Upstream:
https://github.com/nicobailon/pi-mcp-adapter

Current package is actively maintained. Paseo's own Pi provider documentation explicitly states that Pi MCP support through Paseo depends on `pi-mcp-adapter` being loaded for the agent cwd:
https://github.com/getpaseo/paseo/blob/main/docs/providers.md

This makes it the strongest MCP client candidate for this project.

Important architecture:
- default model-facing surface is one `mcp` proxy tool, roughly ~200 tokens rather than every MCP tool schema;
- server/tool metadata is cached;
- servers are lazy by default;
- the agent can search/describe tools and invoke the selected MCP tool on demand;
- selected high-frequency tools can be promoted as direct first-class tools;
- each direct tool costs additional system-prompt/schema context, so direct exposure should remain narrow;
- `directTools: "search"` provides an intermediate path: real tools exist but are activated by search instead of all being permanently active;
- include/exclude filters allow a noisy server to expose only useful tools;
- current versions include an MCP-only scripting/code-mode surface for multi-call composition;
- current v2.36.0 can optionally use Jev/TypeSafe semantic discovery across MCP tool catalogs.

Paseo behavior:
- Paseo talks to Pi through RPC;
- it detects the adapter's `mcp` command;
- when Paseo injects agent-scoped MCP servers, it writes a per-agent config and passes `--mcp-config`;
- this lets Paseo expose configured MCP servers without rewriting the normal shared project/global files.

Caveat: an Aug-2026 Paseo issue reported a race involving agent-scoped MCP injection with then-current Pi/adapter versions on macOS. This is a reason to test the exact Linux/Unraid/Paseo combination, not evidence that the architecture is unusable.

#### Alternative: @qianhuan-lxs/pi-mcp-bridge

Upstream:
https://github.com/qianhuan-lxs/pi-mcp-bridge

It uses three generic model-facing tools and a filesystem registry of MCP schemas. Small catalogs can inline schemas; larger ones expose names/descriptions and let the agent load exact schema files on demand. Servers are lazy and oversized results have output guards.

This is architecturally interesting prior art for dynamic context discovery, but Paseo explicitly integrates against `pi-mcp-adapter`, so it is a weaker deployment fit.

#### Alternative: pi-mcp-extension

Catalog:
https://pi.dev/packages/pi-mcp-extension

It is a conventional direct MCP client with transport/reconnection/tool discovery support. It registers MCP tools more directly. It is simpler conceptually, but does not solve schema/context pressure as aggressively and does not match Paseo's documented adapter contract.

#### Other packages

There are multiple forks/adapters in the Pi catalog. Their existence is not a reason to mix them. Installing multiple MCP clients that discover the same servers would create duplicate tool surfaces, duplicate processes and ambiguous permissions.

#### Recommended minimal MCP architecture to validate

```text
Paseo
  -> Pi RPC
      -> pi-mcp-adapter
          -> one proxy/search surface by default
          -> narrow directTools only for hot/important tools
          -> MCP servers (Context7, GitHub, browser, future private services)
```

Security/authority requirements for later Definition:
- whitelist MCP servers and their effective privileges;
- secrets stay outside repository;
- destructive MCP actions remain subject to permission/authorization policy;
- do not expose hundreds of direct tools by default;
- treat MCP server instructions/tool descriptions as untrusted external input, not workflow authority;
- test how `pi-permission-system` gates proxy MCP calls versus direct MCP tools before relying on it as a security boundary.

### 12. Cross-cutting PWv3 opportunities

The research exposes several ideas that are more valuable than the individual packages:

1. **Capability-gap feedback loop** from SpecPi:
   worker may report a missing capability; only user/policy promotes it into a change.
2. **Deterministic orchestration boundary** from Dagu:
   code/state machine owns ordering; Pi performs bounded roles.
3. **Code-mode tool composition** from Fabric:
   one typed program can coordinate many deterministic tool operations while returning a bounded result.
4. **Small-model typed classification** from Laya/System One:
   cheap bounded classification with confidence-based escalation.
5. **Derived working queue** from rpiv-todo:
   nice agent/user progress view derived from canonical durable state rather than replacing it.
6. **Native process-isolated subagents** from Pi/subagent packages:
   fresh context, explicit model/tools, worktree isolation, structured return, depth/cycle guards.
7. **Dynamic capability discovery** from pi-mcp-adapter:
   search/describe/on-demand activation instead of permanently injecting every tool schema.
8. **Non-authoritative session memory** from Blackhole:
   context compression/recall can improve continuity while repository state remains canonical truth.

These are candidates for a later PWv3 Definition/Research workstream, not automatic changes to PWv2.

## Unresolved decisions requiring user/product authority or empirical test

1. Choose `pi-web-access` vs Ketch after a same-task evaluation.
2. Decide whether Context7 is supplied by Ketch, dedicated MCP through `pi-mcp-adapter`, or a Pi-specific extension.
3. Decide whether Blackhole observational memory is enabled after deterministic-compaction testing.
4. Decide whether Fabric is installed at all, or only studied as PWv3 prior art.
5. Decide whether Laya/System One becomes part of PWv3 after domain-specific calibration tests.
6. Decide whether rpiv-todo is installed as a derived session UX or only borrowed as design prior art.
7. Decide whether Plannotator's current Paseo rough edges are acceptable after a live test.
8. Choose the exact MCP adapter after a live Paseo/Pi integration check; current evidence strongly favors `pi-mcp-adapter`.
9. Decide the scope/timing of a separate PWv3 redesign workstream; the present workstream must not silently mutate Project Workflow itself.

## Evidence sources

Primary/upstream:
- https://github.com/k0valik/pi-blackhole
- https://github.com/nicobailon/pi-web-access
- https://github.com/1broseidon/ketch
- https://github.com/monotykamary/pi-fabric
- https://github.com/NandhaKishorM/laya
- https://github.com/juicesharp/rpiv-todo
- https://github.com/getpaseo/paseo/issues/1125
- https://www.npmjs.com/package/@narumitw/pi-github-pr
- https://tannermidd.github.io/SpecPi/wiki/
- https://docs.dagu.sh/step-types/harness/pi
- https://docs.dagu.sh/step-types/harness/
- https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/subagent/README.md
- https://github.com/mjakl/pi-subagent
- https://github.com/nicobailon/pi-mcp-adapter
- https://github.com/getpaseo/paseo/blob/main/docs/providers.md
- https://github.com/qianhuan-lxs/pi-mcp-bridge
- https://pi.dev/packages/pi-mcp-extension

Community lead confirmed against upstream:
- https://www.reddit.com/r/PiCodingAgent/comments/1wml882/what_extensions_do_you_think_are_essential_and/

## Limitations / live validation still required

This research is source-level. The final stack must still be tested on the actual clean Pi + Linux/Unraid + Paseo deployment because RPC UI forwarding, permission interposition, MCP injection and extension-to-extension interactions can differ from each project's isolated documentation.
