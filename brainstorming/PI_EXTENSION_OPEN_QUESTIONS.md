# Pi extension/tooling open questions

Definition subject: `pi-extension-tooling-selection@R1`
Workstream: `change-pi-extension-evaluation`
Evidence: `research/PI_EXTENSION_EVALUATION_R1.md`

These are the remaining user/product or empirical choices. Research evidence is complete enough to frame them, but does not choose on the user's behalf.

## OQ-01 — Web/research layer

Choose the primary web/research path after an identical-task test:
- `pi-web-access`; or
- Ketch (CLI/skill, optionally MCP).

Compare result quality, latency, model behavior, context growth and Paseo rendering.

## OQ-02 — Context7 delivery

After OQ-01:
- Ketch `docs` if Ketch is selected;
- Context7 MCP through the selected MCP adapter;
- dedicated Context7 Pi extension only if it adds material value over those paths.

## OQ-03 — pi-blackhole

Decide separately:
1. deterministic Blackhole compaction vs native Pi compaction;
2. whether observational memory workers are enabled.

Required invariant: Blackhole memory can never become canonical Project Workflow authority.

## OQ-04 — pi-fabric

Decide whether to:
- install Fabric for bounded code-mode/tool composition only; or
- keep it as PWv3 prior art without installing it.

Fabric's agents/workflows/mesh must not become parallel workflow authority without a separate decision.

## OQ-05 — Laya / System One

Decide whether to run a bounded calibration experiment for future PWv3 classification/routing. It must not authorize user-owned/strategic/destructive transitions.

## OQ-06 — rpiv-todo

Decide whether to install it only as a visible/derived session working queue, or use its dependency/cycle model solely as PWv3 design prior art. It must not replace the repository Task Board.

## OQ-07 — Plannotator

Run a live Paseo compatibility test. Current upstream evidence shows incomplete first-class integration/stale plan-card behavior.

## OQ-08 — pi-github-pr

Research resolved its behavior: it is human-facing statusline observability and does not give the model a PR tool/context. Decide whether to skip it because Paseo is the primary UI.

## OQ-09 — MCP adapter

Current evidence strongly favors `pi-mcp-adapter` by nicobailon because Paseo explicitly integrates with it and it minimizes tool-schema context through proxy/search/lazy direct tools.

Before final selection validate:
- exact current Pi + Paseo + Linux/Unraid versions;
- agent-scoped MCP injection;
- OAuth/secret handling;
- interaction with `pi-permission-system`;
- subagent MCP allowlists.

Alternatives retained only for comparison:
- `@qianhuan-lxs/pi-mcp-bridge`;
- `pi-mcp-extension`.

## OQ-10 — PWv3 follow-on

Create a separate future workstream for Project Workflow evolution if desired. Candidate prior art already identified:
- SpecPi capability-gap/wishlist promotion loop;
- deterministic Dagu-style outer state machine;
- Fabric typed code-mode composition;
- Laya/System One bounded classification;
- rpiv-todo derived working queue;
- process-isolated Pi subagents with explicit role/model/tools/context;
- MCP dynamic capability discovery;
- Blackhole non-authoritative session memory/recall.
