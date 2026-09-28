# Brainstorming — Codex-LB dynamic model catalog

Scope subject: `codex-lb-dynamic-model-catalog@1`
Status: promoted to Definition

## Accepted target

Pi/Paseo must not carry a hardcoded Codex-LB model list. The model catalog is owned by Codex-LB and Pi must discover it dynamically from the authenticated `/v1/models` endpoint.

When Codex-LB starts exposing a new model, it must become selectable in Pi/Paseo automatically without a repository edit, manual `models.json` change, or container restart. When Codex-LB removes a model, the runtime catalog should converge accordingly after refresh.

## Chosen shape

- Use a small global Pi `codex-lb` provider extension; do not modify Codex-LB for this feature.
- Keep the existing generic `openai-responses` transport and existing `CODEX_LB_API_KEY` secret boundary.
- Use Pi's supported dynamic provider model-discovery path and a bounded in-session refresh/publish loop so long-running Paseo RPC sessions learn about catalog changes.
- Persist/retain a last-known-good catalog. A transient discovery failure must not collapse the picker to an empty catalog.
- Polling cadence is an implementation tuning detail; it should be bounded and modest rather than aggressive.
- Do not infer richer per-model capabilities from an ID alone. Use verified metadata where available and conservative defaults otherwise.

## Out of scope

- changing Codex-LB account/OAuth ownership or routing;
- automatic switching of the user's selected model;
- modifying unrelated Paseo update/distribution work;
- inventing per-model pricing/context/reasoning metadata that Codex-LB does not expose.

## Challenge audit

GREEN. The desired product behavior is unambiguous, existing Pi 0.87.1 APIs support the required integration shape, and no remaining product choice is needed before Definition. Exact timer values and test injection mechanics belong to Planning/Execution.
