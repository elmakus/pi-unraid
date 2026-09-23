# Research — Pi Blackhole memory model and persistence facts R1

- Research ID: `pi-blackhole-memory-facts-r1`
- Status: `consumed`
- Origin role: `project_definition`
- Origin subject: `pi-extension-tooling-selection@R1`
- Return target: `project_definition:pi-extension-tooling-selection@R2`
- Research question: Can pi-blackhole use explicitly selected models for observational memory, and where is memory persisted?
- Return reconciliation: `applied`
- Return reconciliation result: `requirements/PI_EXTENSION_TOOLING.md; brainstorming/PI_EXTENSION_OPEN_QUESTIONS.md; decisions/PIE_ADR_002_TOOLING_SELECTIONS.md`

## Verified findings

Upstream sources:
- https://github.com/k0valik/pi-blackhole
- https://github.com/k0valik/pi-blackhole/blob/main/docs/CONFIG.md
- https://github.com/k0valik/pi-blackhole/blob/main/docs/observational-memory.md
- https://github.com/k0valik/pi-blackhole/blob/main/docs/architecture.md

### Worker models

Blackhole exposes separate model configuration for:
- `observerModel`;
- `reflectorModel`;
- `dropperModel`.

Each model config may include provider/id and supported thinking level. Each worker can also have an ordered fallback list. Resolution order is:
1. worker-specific primary model;
2. worker-specific fallback models;
3. shared `model`;
4. current session model when session fallback is enabled.

This permits cheap/fast models for frequent Observer work and different models for Reflector/Dropper.

### Memory persistence

Normal observational-memory records are appended to the current Pi session branch as custom session entries:
- `om.observations.recorded`;
- `om.reflections.recorded`;
- `om.observations.dropped`.

Therefore observations/reflections normally live with Pi's durable session history rather than in a separate global memory database.

In Blackhole manual-compaction mode, pending observations/reflections/drops and pipeline cursors are additionally persisted in:
`~/.pi/agent/pi-blackhole/<sessionId>-pending.json`

A stale backup may exist as:
`~/.pi/agent/pi-blackhole/<sessionId>-pending.stale.json`

Other Blackhole state:
- config: `~/.pi/agent/pi-blackhole/pi-blackhole-config.json`;
- model cooldowns: `~/.pi/agent/pi-blackhole/pi-blackhole-cooldown.json`.

### Scope implication

The primary ledger is session-scoped. It is not a cross-project authoritative knowledge base. Blackhole can export/distill project memory across sessions, but Project Workflow durable repository state remains the authority for project execution truth.
