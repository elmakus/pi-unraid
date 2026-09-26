# Planning re-entry input — consolidated human acceptance

- Workstream: `feature-paseo-gui-runtime`.
- Decision date: 2026-09-26.
- Source: explicit user decision for continuation after terminal M05-T03. This is planning input, not an approved plan revision or permission to rewrite P3 without PWv2 transitions.
- Prior approved plan: `planning/PASEO_GUI_RUNTIME_P3.md`, immutable subject `elmakus/pi-unraid@b1c5d4c3f340afb96bfb2f3ae44f694069bd6a63:planning/PASEO_GUI_RUNTIME_P3.md@fb071b96e5e7b54187bfaa7040640f5f3eb59b89`.
- Entry classification: material milestone/order/gate strategy correction within accepted Definition R2, routed to a new Strategic Planning cycle. P3 explicitly puts real phone Relay pairing and authenticated GraphQL mutation in M06 before integrated GREEN, then repeats cold/warm acceptance in M07. These are substantive planning changes, not execution-detail or editorial refinements.

## Requested strategy for the new plan

1. Complete all technically independent automatic implementation and acceptance first. Group user-presence actions as late as technically possible into one Human Acceptance wave. These include secret supply/approval, first OAuth or device flow, account choice, 2FA, manual login approval, phone Relay pairing, interactive GitHub authentication, Unraid GraphQL credential materialization and authenticated mutation proof when user involvement is needed, manual UI/UX judgment, and any other physical-presence check. Stop earlier only for a demonstrated minimal technical dependency or an existing accepted authorization gate.
2. M05-T03 and its exact result/review remain unchanged. Replan only not-yet-materialized M06/M07 and later acceptance dependencies. Automatic Pi RPC, workspace, browser/Playwright/Chromium headed/Xvfb, capability, doctor and integration checks should precede interactive checks. Relay/mobile pairing and authenticated GraphQL live acceptance should move to the late Human Acceptance wave when static, implementation and read-only evidence supports safe prior progress.
3. Keep the legacy standalone Pi as a rollback/safety anchor through full final GREEN. Final sequence intended: autonomous work, technically ready Paseo/Pi, one consolidated Human Acceptance session, final production acceptance, legacy Pi retirement, Close.
4. Reuse exact M05-T02B cold/warm Buildx and local retention evidence in M07 if the frozen candidate, build inputs, Dockerfile and pipeline remain materially unchanged. Re-run only when that evidence is invalidated. M07 still must prove production-relevant cutover, rollback and restart/recovery. Likewise reuse full GREEN M06 integration evidence for a bounded production post-deploy smoke unless intervening changes invalidate it.
5. Keep Chromium, Playwright and headed/Xvfb in scope. SpecPi core remains part of the final environment and its exact pair compatibility requirement remains; optional improvement/wishlist may be activated after base Paseo/Pi deployment, followed by compatibility smoke and only then reproducible desired-state persistence. Optional wishlist activation must not block first base startup.
6. Do not rebuild or re-resolve the accepted candidate merely to remove Docker CLI/Compose. They do not become the Unraid host-control architecture: GraphQL remains primary, SSH fallback. Their removal may be later cleanup and is not a current-path prerequisite.
7. Private project GHCR, project registry cache and self-hosted GitHub runner remain outside the required path.

## Authority and acceptance constraints to preserve

The new plan must retain Definition R2 requirements and ADR-PGR-001–004, including first production acceptance coverage in PGR-REQ-079, cold/warm proof in PGR-REQ-070, SpecPi core and exact-pair compatibility before promotion in PGR-REQ-086, user-gated high-impact host actions, secret handling, staged production cutover and valid HOME preservation. Reusing exact prior evidence is an acceptance method only when its identity and behavioral coverage still apply; it does not waive a requirement. Any genuine accepted product-authority conflict must return to Definition rather than being silently planned away.
