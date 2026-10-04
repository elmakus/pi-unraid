# M08-T01 — authority and non-inference preflight

Date: 2026-10-04
Outcome: **BLOCKED — unresolved acceptance authority, not a completed real smoke**

## Durable recovery and remaining scope

The continuation recovered `feature-paseo-update-distribution` from source head `8b7b0858d05153754f95bc5f5e4bac0d164e18cf`, with integration target `main` at `e9476b4987290767a195a9de2ecd655de5f09605`.

The current canonical PWv2 router at `elmakus/project_workflow_v2@d3ab917f02e4de91b7dbb17915c2287c2387333e` initially failed closed because the workstream manifest lacked a Plan Review locator. Existing `PLAN_REVIEW.toml` already records exact P3 independent GREEN coverage of `planning/PASEO_UPDATE_DISTRIBUTION_P3.md` at commit `88feb2ba8d9f2b18ac58b9c57a465759277efa60`, blob `043ad95bf300dee7c0289f44fc6547684f82b664`. The manifest-only repair at `524a7f9` links that existing record; it does not author, change or verdict the plan.

Fresh rerouting selected Close because all 21 currently materialized M01-M07 Cards are DONE. The approved P3 scope still includes M08 human/production acceptance and M09 operationalization. The canonical Close continuation helper therefore returns `continue_deterministically`, not end of scope. Main-owned Execution Prep materializes only the currently knowable M08-T01 contract and preserves the downstream M08-T02 dependency as a waiting JIT trigger.

The exact DONE predecessor is M07-T03 result at commit `c9d18c3f1c159684128221a6569496630d7fcbce`, blob `21dea73b5f663125cce8642486abc7cbffb506e3`. Its GREEN review and historical release-readiness evidence remain unchanged. They do not satisfy the deferred real-smoke or production gates.

## Fresh bounded readback

- Full host-control doctor: **GREEN**, GraphQL primary GREEN, strict non-interactive SSH fallback GREEN, safety policy GREEN. No host-control mutation was invoked.
- Active production `pi-unraid-paseo-1`: running, healthy, restart count 0; configured image `pi-unraid:paseo-codex-lb-env-bc87a92`; image ID `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`.
- Exact M07 candidate manifest: HTTP 200, registry digest readback equals `sha256:77e29f0d8fe8b1975725ba8b430ed7f2225dcc55c2074b397d153fcea3da4cf7`.
- Production `ghcr.io/elmakus/pi-unraid:accepted` manifest: HTTP 404 / absent.
- Local Docker daemon and buildx are unavailable in the calling container. This was not treated as missing host access: host metadata was read through the accepted transports, and registry identity was verified through the read-only OCI Registry API.
- Focused `test_paseo_tower_validator.py` verification: **8/8 PASS**, mocked Docker/Codex fixtures and structural parser checks only; no real inference.
- The installed guarded launcher `--native-create-agent-args` validated its fixed policy without inference.

No raw credential, key bytes, registry bearer token, provider response or session/worker identity is retained in this evidence. No dedicated smoke credential was admitted or repurposed from ordinary agent credentials.

## Exact policy conflict

Accepted requirements PUD-REQ-020 and PUD-REQ-021, ADR-PUD-003, and approved P3 M08-T01 require a real Codex-LB smoke using only a dedicated operator-supplied API key. Fixtures and metadata/auth/health readback cannot be substituted for that real acceptance evidence.

The mandatory installed environment real-LLM test policy requires provider `meta`, model `muse-spark-1.3-contributor`, thinking/contribution `max`, no fallback, and the canonical guarded launcher. Its native child argument validation confirms provider `pi/meta/muse-spark-1.3-contributor`, thinking `max`, and completion notification. These are observed test-policy constraints, not Project Workflow role-routing authority.

The current `scripts/paseo_tower_validator.py` real-smoke path directly executes `curl` against Codex-LB `/responses` with a caller-selected model. It bypasses the mandatory launcher and does not establish the required fixed test profile. No invocation of that path was attempted. An unrelated native Muse test would not by itself satisfy the exact candidate's accepted real Codex-LB gate.

## Recovery classification and next step

The blocker is `human_authority`: an explicit accepted-scope decision is needed before Definition can reconcile PUD-REQ-020/021 and associated acceptance/credential boundaries with the mandatory test policy. The decision cannot authorize a forbidden test profile or a launcher bypass. A policy-compliant revision may change the real-smoke provider and retain appropriate non-inference Codex-LB checks, but that is not silently adopted through Execution Prep or this evidence.

After an explicit scope decision, recover the exact blocked Card and use the canonical Definition/Planning routes for any required accepted-authority or strategy change. Do not rewrite historical GREEN evidence, claim this Card DONE, advance production eligibility, or skip the separate user-triggered production cutover requirement.

This continuation performed no real LLM test, candidate deployment, dedicated secret installation, production guard arm, accepted-channel write, production restart, cutover or rollback. The production guard's current binding and persistent rollback state have not been freshly validated by this preflight; their final verification remains a later obligation.
