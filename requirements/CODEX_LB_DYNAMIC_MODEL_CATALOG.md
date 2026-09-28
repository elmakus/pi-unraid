# Codex-LB dynamic model catalog — Requirements

Revision: `R1`
Status: `approved`
Definition subject: `codex-lb-dynamic-model-catalog@1`
Source Brainstorming: `brainstorming/CODEX_LB_DYNAMIC_MODEL_CATALOG_R1.md`
Definition Research: `research/CODEX_LB_DYNAMIC_MODEL_CATALOG_R1.md`

## Goal

Make the Pi/Paseo model picker reflect the live Codex-LB model catalog without hardcoded model IDs, while preserving the existing Codex-LB authentication/account-routing boundary and safe behavior during catalog failures.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| CLDMC-REQ-001 | Pi MUST discover Codex-LB models dynamically from the authenticated Codex-LB `/v1/models` endpoint; the accepted implementation MUST NOT require a hardcoded list of Codex-LB model IDs. | MUST |
| CLDMC-REQ-002 | A model newly exposed by Codex-LB MUST become selectable in Pi/Paseo without a repository edit, manual `models.json` change, or Pi/Paseo container restart. | MUST |
| CLDMC-REQ-003 | A model removed from the Codex-LB catalog MUST cease to be offered after the bounded refresh path converges, without forcing an unrelated runtime restart. | MUST |
| CLDMC-REQ-004 | Long-lived Paseo/Pi RPC sessions MUST receive catalog changes through a bounded in-session refresh/publish mechanism rather than relying only on process startup. | MUST |
| CLDMC-REQ-005 | The integration MUST retain a last-known-good model catalog across transient discovery failures. A fetch, authentication, parse, or timeout failure MUST NOT replace a valid catalog with an empty list. | MUST |
| CLDMC-REQ-006 | Model requests MUST continue to use the existing generic Pi `openai-responses` path through Codex-LB and the existing `CODEX_LB_API_KEY` secret boundary. | MUST |
| CLDMC-REQ-007 | ChatGPT/Codex OAuth ownership, pooled-account state, and account routing MUST remain owned by Codex-LB; this feature MUST NOT import or manage those credentials in Pi. | MUST |
| CLDMC-REQ-008 | The implementation MUST use Pi's supported provider-extension/model-refresh interfaces and be installed reproducibly by `pi-unraid`; manual production-home edits are not an accepted deployment mechanism. | MUST |
| CLDMC-REQ-009 | Discovery MUST publish only validated model IDs. Richer model capabilities such as reasoning, context limits, image support, cost, or token limits MUST NOT be inferred solely from an ID; use verified metadata where available and conservative defaults otherwise. | MUST |
| CLDMC-REQ-010 | The refresh cadence MUST be bounded and modest. Exact interval selection is a Planning/Execution tuning decision and MUST be testable without waiting for real wall-clock production intervals. | MUST |
| CLDMC-REQ-011 | Production-like acceptance MUST prove: current Codex-LB models appear; an added catalog ID becomes visible to an already-running RPC session; a removed ID disappears after refresh; and a temporary catalog failure preserves the previous valid list. | MUST |
| CLDMC-REQ-012 | The integration MUST NOT automatically switch the user's currently selected model merely because the catalog changes. | MUST |

## Out of scope

- Changing Codex-LB OAuth/account routing or its service lifecycle.
- Automatic model selection/routing in Pi.
- Changes to the separate Paseo update/distribution workstream.
- Inventing model capability metadata not supplied or otherwise verified.
