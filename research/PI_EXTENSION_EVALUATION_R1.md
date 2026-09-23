# Research — Pi extension/tooling evaluation R1

- Research ID: `pi-extension-evaluation-r1`
- Status: `active`
- Origin role: `other`
- Origin subject: `change-pi-extension-evaluation`
- Return target: `project_definition:pi-extension-tooling-selection-r1`
- Research question: Evaluate the shortlisted Pi extensions/tools and MCP integration options for a clean Pi + Paseo setup; verify unresolved behavior/compatibility; identify prior art that could materially improve a future Pi-oriented Project Workflow revision and native subagent design.
- Return reconciliation: `pending`
- Return reconciliation result: `none`

## Constraints

- Clean Pi is the target; do not assume `pi-code` or OMP.
- Paseo is the intended primary GUI/Android remote.
- PWv2 remains the current authority/workflow; external orchestration must not silently become a second authority source.
- Research may identify ideas for a future PWv3, but it does not itself authorize PWv2 changes.
- MCP usage is required and must be covered explicitly.

## User decisions already accepted

Accepted: `rpiv-ask-user-question`, `pi-permission-system`, `pi-lens`, loop detector/`pi-antiloop`, `pi-skill-gate`.

Rejected: `@narumitw/pi-lsp`, `pi-file-context`, `pi-btw`, `pi-zentui`, `pi-code`, Pi Desktop.

Paseo selected as the primary Pi UI/remote.

## Research questions

1. Compare `pi-web-access` and Ketch for search, fetch/scrape, docs, code research, auth/cost, tool-schema/context cost, and Paseo/RPC suitability. Determine whether Context7 remains useful in each option.
2. Explain `pi-blackhole` precisely: compaction algorithm, memory architecture, persistence, model calls/cost, branch/session behavior, retrieval/recall, safety/failure modes and overlap with repository-backed durable state.
3. Assess `pi-fabric` as tool-call composition/code mode and separately as an orchestration runtime; identify bounded ideas useful to PWv3 without importing a second workflow authority.
4. Assess Laya/System One and similar fast decision/classifier layers for bounded routing/guard use in PWv3.
5. Assess `rpiv-todo` as Pi-native working-state UX and whether any of its mechanisms could improve PWv3 while preserving the repository Task Board as canonical durable authority.
6. Verify whether Plannotator works through Paseo/Pi RPC and distinguish browser-local/UI coupling from agent/runtime compatibility.
7. Determine whether `pi-github-pr` only helps the human or exposes anything useful to the agent.
8. Locate and verify the Reddit comment about Pi recording a missing extension/ability it needed, and identify the actual extension/mechanism referred to.
9. Research deterministic workflow-engine prior art relevant to Pi/PWv3.
10. Research Pi subagent frameworks as prior art for native subagents, especially role isolation, model selection, context bounding, permissions, lifecycle and handoff.
11. Research MCP support for clean Pi: core capabilities, existing extensions/bridges, server lifecycle/configuration, tool-schema/context cost, permissions/security, Paseo interaction, and recommended minimal architecture.

## Evidence quality

Prefer upstream repositories/docs and current package documentation. Use Reddit/community reports as practical evidence and leads, but distinguish them from upstream facts.
