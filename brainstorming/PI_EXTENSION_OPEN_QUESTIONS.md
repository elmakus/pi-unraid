# Pi extension/tooling open questions

Definition subject: `pi-extension-tooling-selection@R4`
Workstream: `change-pi-extension-evaluation`
Evidence:
- `research/PI_EXTENSION_EVALUATION_R1.md`
- `research/PI_BLACKHOLE_MEMORY_FACTS_R1.md`

Only unresolved choices that still affect the current extension/tooling Definition remain here. Future PWv3/codex_workflow/subagent/workflow-engine research is intentionally deferred and is not a blocker for this Definition.

## Web/research layer — approved live A/B validation

The user explicitly approved testing both candidates before selection:
- Ketch;
- `pi-web-access`.

Run the same bounded research task in the actual clean Pi + Paseo environment.

For Ketch, begin with its normal free/keyless search path rather than introducing paid API keys before quality is established.

Compare:
- result quality against the user's current Codex web-search quality bar;
- latency;
- model/tool ergonomics;
- context growth;
- Paseo rendering;
- source quality/relevance;
- behavior under repeated searches/fallbacks.

Do not select either candidate until the live comparison is complete.

Context7 is not a separate current blocker. If it is later needed, use/evaluate the user's alternate delivery path rather than assuming a dedicated Pi extension.
