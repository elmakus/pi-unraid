# Pi extension/tooling open questions

Definition subject: `pi-extension-tooling-selection@R2`
Workstream: `change-pi-extension-evaluation`
Evidence:
- `research/PI_EXTENSION_EVALUATION_R1.md`
- `research/PI_BLACKHOLE_MEMORY_FACTS_R1.md`

Only unresolved choices that still affect the current extension/tooling Definition remain here. Future PWv3/codex_workflow/subagent/workflow-engine research is intentionally deferred and is not a blocker for this Definition.

## Web/research layer — live A/B validation

Compare `pi-web-access` and Ketch on the same bounded task in the actual Pi + Paseo environment.

Measure:
- result quality;
- latency;
- model/tool ergonomics;
- context growth;
- Paseo rendering.

Context7 is not a separate current blocker. If it is later needed, use/evaluate the user's alternate delivery path rather than assuming a dedicated Pi extension.

## pi-blackhole — final selection/configuration

Verified facts:
- deterministic Blackhole compaction itself uses no LLM;
- observational memory uses three model-backed workers: Observer, Reflector and Dropper;
- each worker can have its own primary model, fallbacks and thinking level;
- a shared base model can also be configured;
- the session model can be a final fallback when `sessionFallback` is enabled;
- normal observations/reflections are stored as custom entries in the Pi session branch/session file, not in a separate global vector database;
- manual mode additionally persists per-session buffers under `~/.pi/agent/pi-blackhole/<sessionId>-pending.json`;
- Blackhole config lives at `~/.pi/agent/pi-blackhole/pi-blackhole-config.json`;
- model cooldown state lives at `~/.pi/agent/pi-blackhole/pi-blackhole-cooldown.json`.

Remaining user choice:
- adopt Blackhole or keep native Pi compaction;
- if adopted, enable observational memory immediately or start with deterministic compaction only;
- choose worker model(s)/fallbacks after deciding which providers should bear the background memory cost.

Required invariant: Blackhole memory is non-authoritative convenience context; repository-backed Project Workflow state wins on conflict.
