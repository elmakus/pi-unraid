# Research — Current Pi facts for Phase 1 bootstrap

Date: `2026-09-22`
Research question: `Verify the current official Pi installation/runtime/container guidance, ChatGPT Plus/Pro OAuth support and persistence behavior, and session persistence/resume behavior required by the Phase 1 Unraid bootstrap definition.`

## Durable continuation metadata

Research ID: `pi-bootstrap-facts-r1`
Status: `complete`
Origin role: `brainstorming`
Origin subject: `pi-unraid-bootstrap@R1`
Return target: `brainstorming:pi-unraid-bootstrap@R1`
Return reconciliation: `pending`
Return reconciliation result: `none`

## Scope

Verified only implementation-shaping current facts required before Project Definition can safely formalize the Phase 1 bootstrap. Web UI and extension selection were explicitly excluded.

## Sources / evidence

| Source | Class / evidentiary weight | What it supports | Freshness / limitations |
|---|---|---|---|
| https://pi.dev/docs/latest/quickstart | official current Pi documentation | install package, Node requirement, working-directory model, login flow, auto-saved sessions and continue behavior | checked 2026-09-22 |
| https://pi.dev/docs/latest/containerization | official current Pi documentation | Plain Docker as supported whole-process isolation; official sample image/package/mount pattern | checked 2026-09-22 |
| https://pi.dev/docs/latest/providers | official current Pi documentation | interactive OAuth/provider auth, ChatGPT Plus/Pro (Codex), credential persistence/refresh | checked 2026-09-22 |
| https://pi.dev/docs/latest/sessions | official current Pi documentation | session auto-save, storage organization, resume/continue commands | checked 2026-09-22 |
| https://pi.dev/docs/latest/environment-variables | official current Pi documentation | `PI_CODING_AGENT_DIR`, `PI_CODING_AGENT_SESSION_DIR` and default config/session locations | checked 2026-09-22 |

## Verified findings

1. **Current installation/runtime**
   - Pi can be installed through the official installer or npm.
   - The current npm package is `@earendil-works/pi-coding-agent`.
   - Current npm installation documentation requires **Node.js 22.19 or newer**.
   - The official Plain Docker example uses `node:24-bookworm-slim`, so the accepted richer Node 24 Debian-based container remains aligned with current official guidance.

2. **Whole-process Docker is an officially supported pattern**
   - Pi documents Plain Docker as a straightforward whole-process isolation option.
   - The official example persists `/root/.pi/agent` with a volume and bind-mounts the working directory.
   - The documentation explicitly states that the agent directory contains credentials, settings and sessions.
   - The official example running as root is an example, not a stated requirement; no current documentation found requires root operation. The accepted non-root service-user design therefore remains a project implementation choice rather than a contradiction of Pi requirements.

3. **ChatGPT Plus/Pro OAuth remains built in**
   - Interactive `/login` supports **ChatGPT Plus/Pro (Codex)**.
   - Pi stores interactive credentials in `~/.pi/agent/auth.json`.
   - Stored OAuth credentials are refreshed as needed.
   - On a headless/remote machine, Pi supports completing OAuth by pasting the final redirect URL or authorization code back into the process.
   - Persisting the service user's full home therefore preserves the accepted Pi credential store.

4. **Session persistence/resume is native Pi behavior**
   - Sessions are automatically saved by default.
   - Default session storage is beneath `~/.pi/agent/sessions/`, organized by working directory.
   - `pi --continue`/equivalent continue behavior resumes the most recent session for the working folder, while `/resume` / session-picker behavior exposes prior sessions.
   - Persisting the Pi home is sufficient to preserve ordinary session history unless the project intentionally overrides the session directory.

5. **Config/session directory controls match the accepted persistence design**
   - `PI_CODING_AGENT_DIR` overrides the default config directory, whose default is `~/.pi/agent`.
   - `PI_CODING_AGENT_SESSION_DIR` can separately override session storage.
   - Because G13/G45 intentionally preserve Pi's native user-home layout, Phase 1 does not need to relocate these paths merely for persistence.

## Repository/current-state findings

- The historical brainstorming text contains several early candidate/deferred sections that were later superseded by numbered Grill decisions. The completion audit correctly treats later explicit choices as the current exploratory state without rewriting the old exploration.
- No current Pi documentation finding requires reopening a Phase 1 user/product decision.
- The current Node minimum is more precise than the early generic assumption; use the current documented runtime constraint during Definition/planning rather than copying stale text.

## Assumptions / uncertainties

- The exact mechanism for the user-requested **update-to-latest-stable on every service start with fallback to the last working runtime** is not prescribed by Pi documentation and remains project-owned implementation/planning work.
- Exact non-root UID/GID/sudo implementation is also project-owned; current Pi documentation does not provide an Unraid-specific recipe.
- Neither item changes accepted product intent or blocks Project Definition.

## Analysis

Current official Pi behavior supports the Phase 1 concept:

- a persistent Dockerized Pi runtime on Unraid is viable;
- one ChatGPT Plus/Pro account can authenticate through built-in Pi OAuth;
- persisting the Pi user's home preserves the native config/auth/session state model;
- session create/exit/resume behavior required by G86 is native;
- no verified current fact contradicts the accepted Phase 1 architecture.

No additional user/product decision is required from this Research result.

## Project Definition candidates

- Constraint candidate: use a Pi-supported Node runtime satisfying the current documented minimum; current official Docker guidance uses Node 24.
- Constraint candidate: install the current `@earendil-works/pi-coding-agent` package through a reproducible image/startup mechanism.
- Requirement candidate: persistent Pi home must preserve `~/.pi/agent` state including auth and sessions.
- Requirement candidate: Phase 1 must support built-in ChatGPT Plus/Pro (Codex) login on the headless Unraid deployment.
- Requirement candidate: Phase 1 must demonstrate native session creation and later resume from persisted state.
- Planning implication: update/fallback and non-root Unraid ownership mechanics are project-owned implementation design, not unresolved product authority.

Research is evidence, not accepted requirement/decision/plan authority.
