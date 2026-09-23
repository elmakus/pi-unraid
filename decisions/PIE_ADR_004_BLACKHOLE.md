# Decision — Adopt pi-blackhole for compaction and optional observational memory

- Decision ID: `PIE-ADR-004`
- Date: `2026-09-23`
- Status: `accepted`
- Authority: `user`
- Related requirements: `requirements/PI_EXTENSION_TOOLING.md`
- Evidence: `research/PI_BLACKHOLE_MEMORY_FACTS_R1.md`

## Decision

Adopt `pi-blackhole` as part of the clean Pi baseline.

Blackhole may provide:
- deterministic compaction;
- observational memory through Observer, Reflector and Dropper;
- recall over session history/memory.

Exact worker model/provider/fallback choices are configuration details to tune later.

## Authority boundary

Blackhole memory is non-authoritative. Project Workflow recovery must continue from exact repository durable pointers and Git/runtime evidence.

For independent review:
- start a genuinely fresh Pi session/process;
- do not inherit executor-session Blackhole memory;
- do not inject exported/cross-session Blackhole memory unless the exact review contract explicitly permits it.

## Consequences

- Blackhole is no longer an unresolved Definition choice.
- Native Pi compaction remains a fallback/recovery option, not the selected baseline behavior.
- Memory-model selection can be optimized for cost/quality separately from the main session model.
