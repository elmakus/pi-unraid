# Pi on Unraid — Phase 1 Master Plan

Plan revision: `R3`
Plan subject: `pi-unraid-bootstrap-plan@R3`
Status: `approved`
Definition subject: `pi-unraid-bootstrap@R3`
Workstream: `feature-pi-unraid-bootstrap`
Branch: `feat/pi-unraid-bootstrap`
Strategic author: `ChatGPT — Strategic Planning`, authorized by `PIB-ADR-006`
Independent plan review: `RECOMMENDED`
Planner audit: `planning/audits/R3.md`
Independent review record: `planning/reviews/R3.md`
Date: `2026-09-23`

## 1. Revision purpose, authority and verified baseline

R3 narrows only the remaining Phase 1 acceptance path after the user explicitly chose to skip the previously mandatory Docker-wide/host restart exercise. The intended `unless-stopped` restart configuration remains required, but broad restart recovery is no longer a Phase 1 live-test gate; the residual unverified risk is explicitly user-accepted under `PIB-ADR-007`.

This revision preserves all completed implementation/evidence: M01 and M02 remain accepted historical checkpoints; M03-T02/T03/T04 remain completed GREEN; and the already-executed non-disruptive M03-T05 update/fallback/rollback/graceful-stop/Codex-LB recovery evidence remains valid. No Docker-wide or Unraid host restart occurred.

Authoritative inputs:

- `requirements/PI_UNRAID_BOOTSTRAP.md`, revision R3, approved; all 24 requirements and all 21 acceptance-level outcomes remain binding under the R3 restart-verification waiver.
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md` — minimal bootstrap scope and user-owned later evaluation.
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md` — persistent native home, non-root runtime, accepted mounts/tooling and backup boundary.
- `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md` — latest-stable Pi startup, runtime fallback, previous-deployment rollback and one normal update operation.
- `decisions/PIB_ADR_004_WORKFLOW_ROLES.md` — historical role/lifecycle decision, except for the planner-runtime assignment superseded below.
- `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md` — Codex-LB is the required Phase 1 ChatGPT/Codex OAuth/account-routing layer.
- `decisions/PIB_ADR_006_CHATGPT_STRATEGIC_PLANNER_OVERRIDE.md` — current ChatGPT authors this Strategic Planning revision while independent review remains fresh-session separated.
- `decisions/PIB_ADR_007_SKIP_DISRUPTIVE_RESTART_ACCEPTANCE.md` — broad Docker/host restart is not required for Phase 1 acceptance; the unverified restart-path risk is user-accepted.
- `research/PI_UNRAID_BOOTSTRAP_FACTS_R1.md` — verified Pi/runtime/session facts carried by Definition.
- `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md` — verified Pi ↔ Codex-LB protocol, OAuth ownership, routing and Tower dependency facts.
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-acceptance.md` and `.../M02-acceptance.md` — completed integrated implementation checkpoints.
- `implementation/workstreams/feature-pi-unraid-bootstrap/handoffs/M02_HANDOFF.md` — accepted downstream execution baseline.
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-readiness.md` — read-only Tower readiness captured before the R2 architecture change; historical target facts only, not deployment authority.

R1 and R2 independent GREEN reviews remain historical evidence for their exact earlier subjects. Neither approves the new R3 acceptance change.

### Current durable implementation baseline

The following state is already accepted and must be preserved rather than reimplemented:

- M01 is GREEN and complete: reproducible Node/Pi development image, non-root persistent-home Compose foundation, native TUI path, accepted project/worktree mounts, strict GitHub host trust, Git identity and required tool inventory.
- M02 is GREEN and complete: latest-stable Pi candidate selection, persistent LKG/seed fallback, managed native Pi lifecycle with bounded graceful shutdown, one host update operation and previous-deployment rollback.
- The final M02 checkpoint is the implementation baseline for future M03 work.
- M03-T04 established the real production `pi-unraid` deployment and live Codex-LB model path. M03-T05 subsequently proved the authorized non-disruptive production update/recovery matrix; its partial evidence remains authoritative for those completed checks.
- Read-only Tower readiness found the intended projects ownership compatible with UID/GID `99:100`, missing canonical Pi appdata/worktree directories, and a stale live checkout requiring clean fast-forward before eventual production deployment.
- The existing `chatgpt-ce-workstation` was healthy at readiness time and remains an independent system whose configuration/secrets/runtime must not become a Pi dependency.
- Codex-LB research found an independently persistent Tower deployment with active account capacity and proxy-key authentication, but also found that its deployed fork/image baseline must be rechecked and reconciled before it can be accepted as the Phase 1 production dependency.

All target/runtime facts above are evidence snapshots. Execution Prep must refresh facts that can drift before acting on them.

## 2. Scope, non-goals and global invariants

Phase 1 remains the minimal Dockerized Pi bootstrap only. Web UI, Android/PWA, web search, subagents, MCP, browser automation, compaction extensions, notification systems, OpenCodex/new router work, Codex-LB product redesign, Muse, Project Workflow-on-Pi and other later extensions remain outside this plan.

Codex-LB is in scope only as the already-selected external ChatGPT/Codex access dependency required by Definition R3.

Execution must preserve these invariants:

1. `compose.yaml` remains the Pi deployment source of truth.
2. Host `/mnt/user/appdata/pi-unraid/home` maps to `/home/pi`; native `~/.pi/agent` remains Pi's durable config/session root.
3. `/mnt/user/projects` maps to `/projects`; `/mnt/user/pi-worktrees` maps to `/worktrees`; selected repositories/worktrees are not silently remapped or rewritten.
4. Normal Pi/development work remains non-root with configurable UID/GID and working sudo; no sweeping ownership takeover is allowed.
5. Pi exposes no inbound SSH daemon and receives no Docker socket, host-root or unrelated-appdata mount.
6. GitHub SSH host verification remains strict and persistent; `gh` remains available for ordinary authorized API operations.
7. Runtime/image rollback never rolls durable Pi home, repositories or worktrees backward.
8. Normal startup targets latest stable Pi only; failed Pi candidates preserve a usable LKG/seed path where available.
9. Planned stop/update retains the accepted bounded graceful-stop contract.
10. Logs remain bounded and ordinary diagnostics remain readable.
11. `chatgpt-ce-workstation` remains independent and unchanged by this project.
12. Codex-LB remains independently deployed and persistent; Pi does not mount, copy, restore or own Codex-LB appdata/OAuth state.
13. ChatGPT/Codex account OAuth login, encrypted token storage, refresh and pooled-account eligibility/routing are Codex-LB responsibilities, not Pi responsibilities.
14. Pi uses an authenticated OpenAI Responses-compatible client seam to Codex-LB; direct Pi built-in ChatGPT/Codex OAuth is neither required nor performed for Phase 1 acceptance.
15. A dedicated Pi → Codex-LB client credential is secret material: it is not committed, baked into an image or emitted into normal logs/evidence.
16. Multi-account routing/failover is accepted only to the extent Codex-LB supports it; Phase 1 does not promise transparent migration of account-owned continuation state.
17. No production or dependency live-write is implied by planning. Every Tower/dependency mutation remains behind an explicit execution authorization gate.

## 3. R3 completion strategy

R3 keeps the M01 → M02 → M03 milestone chain. M01/M02 are historical completed checkpoints. M03 is already substantially executed; the remaining work is only to reconcile the old M03-T05 contract against the user-authorized R3 acceptance waiver, consolidate final evidence/handoff, obtain the required implementation review for the final production subject, and close the workstream. No broad restart is part of the remaining execution.

The key sequencing change is that Pi may not perform its first real model interaction until the Codex-LB dependency, authenticated client seam and Pi-side integration are ready. Production deployment therefore follows dependency readiness and integration validation rather than deploying Pi first and authenticating Pi directly afterward.

### 3.1 Codex-LB dependency boundary

Codex-LB is an external production dependency, not a component absorbed into the `pi-unraid` image or Compose stack.

Before Pi production model use, M03 must establish:

- the selected Codex-LB deployment identity and health;
- a reviewed/current-enough deployment baseline relative to the accepted Codex-LB source authority;
- persistent Codex-LB OAuth/account state and usable eligible account capacity;
- proxy/client-key authentication enabled for the Pi client path;
- the accepted routing configuration, including the configured multi-account strategy/sticky behavior as applicable;
- a deliberate reachable network path from the eventual Pi container to the Codex-LB `/v1` surface;
- a dedicated Pi client credential supplied through an approved host/runtime secret path.

The existing Tower Codex-LB instance is the intended dependency, but the existing integration research snapshot is not permanent freshness proof. Execution Prep must refresh its fork/image/runtime state before deciding whether it is already acceptable.

If refreshed evidence shows Codex-LB source/deployment changes are required, those changes must be performed under the Codex-LB repository's own accepted authority/workflow or another explicit operator-owned dependency procedure. The `pi-unraid` workstream must not silently mutate another repository's product/source authority merely to clear its own prerequisite.

M03 may consume immutable evidence that this external prerequisite is GREEN. If the dependency remains stale, unhealthy, unauthorized or incompatible, Pi production model acceptance remains blocked; that is not permission to fall back to direct Pi ChatGPT OAuth.

### 3.2 Pi-side Codex-LB integration seam

The least-complex accepted client architecture is:

`Pi → authenticated OpenAI Responses HTTP → Codex-LB /v1 → pooled ChatGPT/Codex OAuth accounts`

The Pi-side implementation must use the generic Pi `openai-responses` compatibility path. It must not feed an opaque Codex-LB client key into Pi's native `openai-codex-responses` JWT/account-id path.

Before production cutover, repository/disposable verification must establish the smallest durable integration needed for normal recreation:

- repository/Compose support for supplying the Codex-LB endpoint and a runtime secret reference without embedding the secret;
- persistent Pi provider/model configuration compatible with normal `/home/pi` preservation;
- safe initialization that does not overwrite an already-valid user configuration;
- no pooled ChatGPT access/refresh tokens copied into Pi;
- a deterministic way to distinguish Pi/runtime health from Codex-LB/model-access failure;
- sanitized diagnostics that never print the client credential or upstream OAuth tokens.

The exact host secret file/environment injection mechanism, network route, model metadata and config materialization command are JIT implementation details. Prefer the option that does not require changing Codex-LB's lifecycle/network topology unless refreshed target evidence proves that necessary.

A behavior/state/security contract spanning Compose, persistent Pi config and secret handling should receive a small OpenSpec contract during Execution Prep before implementation if current source inspection shows ambiguity beyond one bounded Card.

### 3.3 Initial production cutover

Production cutover occurs only after the dependency and Pi-side integration prerequisites are GREEN and the user has authorized the concrete live effects.

The cutover path must:

1. re-read target readiness and verify the live project checkout is clean;
2. fast-forward only to the exact approved implementation source; never reset local work;
3. deliberately create any still-missing canonical Pi paths with the accepted target ownership;
4. install/supply the dedicated Pi Codex-LB client secret through the approved non-Git path;
5. render/read back Compose configuration without exposing secret values;
6. build/start the production Pi service with refreshed target UID/GID and accepted mounts;
7. prove native TUI availability and exact Pi/runtime identity;
8. perform the **first real model interaction through Codex-LB**, with direct Pi ChatGPT/Codex OAuth absent;
9. record sanitized evidence that the request used the intended Codex-LB path and that Codex-LB had usable authorized account capacity.

A running container or successful local Pi RPC probe does not satisfy model-access acceptance. Conversely, a temporary Codex-LB/account failure must not be misreported as loss of Pi session/Git/filesystem persistence.

### 3.4 Integrated persistence, operations and handoff

After initial model access succeeds, M03 must verify the complete Phase 1 target:

- Pi-side Codex-LB endpoint/client configuration survives normal Pi restart and container/image recreation;
- Codex-LB OAuth/account state remains separately persistent and is not imported into Pi;
- a native Pi session can be created, exited, resumed and used after restart/recreation;
- selected project/worktree access, Git SSH and `gh` behavior work with acceptable host ownership;
- required tools/security/isolation remain intact in the live service;
- Codex-LB multi-account routing is observed according to its accepted configuration without claiming transparent migration of account-owned continuation state;
- the existing normal Pi update operation works on the production deployment;
- failed latest-stable Pi recovery remains safe;
- the actual previous deployment candidate can be selected for rollback without changing durable mounts;
- planned restart/update preserves the bounded graceful-stop behavior and persisted-session resume;
- bounded logging remains effective;
- production restart policy/timezone are read back from the live deployment; Docker-wide/host restart recovery is explicitly not exercised in Phase 1 under PIB-ADR-007;
- Codex-LB and `chatgpt-ce-workstation` remain independently deployed and no project-owned changes to the workstation are introduced;
- the final operator/recovery handoff identifies dependency failure versus Pi runtime failure and keeps later real-world coding evaluation user-owned.

## 4. Milestones and planned work packages

Dependency chain remains **M01 → M02 → M03**. Work-package labels are planning references only; they are not Task Cards or mutable execution state.

### M01 — Reproducible non-root development environment

**State:** historical GREEN / complete.

**Outcome retained:** repository-owned image/Compose and native access provide the accepted non-root development environment with persistent home, canonical project/worktree mounts, required tools and strict Git trust.

**Owner requirements retained:** PIB-REQ-001/002/003/006/007/008/009/010/011/012/013/016/018.

**Checkpoint authority:** existing M01 Task Cards, reviews and `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-acceptance.md`.

R3 does not create replacement M01 packages or rerun M01. M03 reuses the already accepted live integrated evidence and performs only the remaining R3 reconciliation/finalization.

### M02 — Recoverable runtime and deployment lifecycle

**State:** historical GREEN / complete.

**Outcome retained:** latest-stable runtime selection/fallback, managed native Pi lifecycle, one host update operation, previous-deployment rollback and bounded logging/graceful-stop behavior are proven on the accepted disposable integration surface.

**Owner requirements retained:** PIB-REQ-014/015/017/020/021, integrating the persistence/security invariants established by M01.

**Checkpoint authority:** existing M02 Task Cards, OpenSpec, reviews, handoff and `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M02-acceptance.md`.

R3 does not reopen M02. M03 keeps the already recorded production evidence for those mechanisms.

### M03 — Codex-LB-integrated on-Unraid acceptance and recoverable handoff

**Outcome:** the complete Phase 1 deployment is proven on the actual Unraid target with Codex-LB as the required ChatGPT/Codex OAuth/account-routing layer from the first real model interaction, while preserving M01/M02 operational guarantees and service independence.

**Owner requirements:** PIB-REQ-004/005/019/022/023/024, plus final integrated target acceptance for PIB-REQ-001..003/006..018/020/021 and all 21 Definition acceptance outcomes.

**Dependencies/gates:**

- accepted M01/M02 checkpoints and recovery runbook;
- refreshed read-only Tower/Pi/Codex-LB facts;
- Codex-LB prerequisite evidence sufficient to show health, compatibility, persistence and current-enough reviewed baseline;
- explicit authorization before any Codex-LB/Tower/source/path/secret/deployment mutation;
- explicit authorization for any external Git/GitHub write acceptance operation;
- no fallback to direct Pi ChatGPT OAuth when Codex-LB prerequisites are blocked.

**Planned packages:**

- **M03-W1 — Codex-LB dependency readiness and client boundary.** Refresh selected Codex-LB source/image/deployment facts; verify health, account/OAuth persistence, routing behavior and proxy authentication; reconcile the dependency through its own authority if required; establish dedicated Pi client credential handling and container-to-Codex-LB reachability without sharing appdata or workstation state.
- **M03-W2 — Pi integration implementation and disposable validation.** Add/reconcile the minimum repository/Compose/provider configuration required for authenticated `openai-responses` access to Codex-LB; validate persistent config initialization, secret redaction, missing/invalid-key behavior and network/provider failure classification on a non-production/disposable surface before cutover.
- **M03-W3 — Authorized production bootstrap and live functional acceptance.** Clean fast-forward the target checkout, create missing canonical paths, build/start production, prove native TUI/runtime identity, complete the first real model interaction through Codex-LB with no direct Pi OAuth, then prove Pi config/session plus project/worktree/Git/`gh` behavior across restart/recreation.
- **M03-W4 — Production recovery and final handoff.** Preserve the completed normal update, safe Pi-runtime fallback, actual retained-image rollback, planned-stop/session resume, bounded logs, Codex-LB routing/dependency separation and workstation-independence evidence; reconcile restart-policy configuration under the R3 waiver and consolidate final acceptance/operator recovery evidence.

**Checkpoint:** every Definition R3 acceptance outcome is satisfied with exact evidence under its current proof obligation. No mock-only substitute counts for the real Codex-LB model interaction, production restart/recreation or real rollback. The broad Docker/host restart must be recorded as intentionally **not executed**, not falsely GREEN. No acceptance evidence may expose the Pi client credential or upstream OAuth/token material.

**Evidence:** immutable Pi source/image/runtime identities; Codex-LB dependency identity and sanitized health/config facts; dedicated-client-key existence without secret value; sanitized provider/endpoint configuration; ordered deployment/restart/recreate/model-call/update/rollback observations; session IDs or fixture markers rather than private transcript content; project/worktree/Git/`gh` results; backup and workstation-independence observations; multi-account routing evidence with continuation-state limitation; final coverage/recovery/operator handoff.

**JIT trigger:** accepted M02 artifacts + refreshed M03 target/dependency readiness make concrete network path, secret injection, provider configuration, dependency reconciliation status, UID/GID, source fast-forward, test repository/worktree and live credential action knowable. Execution Prep then creates new M03 Cards. The superseded R1 `M03-T01` is historical only and must not be revived or edited into a new authority surface.

## 5. Complete requirement coverage

Every authoritative R3 requirement maps to an owner milestone and an execution/evidence path. M01/M02 entries below are historical ownership; M03 re-verifies the live integrated target where required.

| Requirement | Owner / planned path | Required proof |
|---|---|---|
| PIB-REQ-001 | M01 → M03-W3 | Repository-owned Compose/source builds and starts the actual Unraid service. |
| PIB-REQ-002 | M01 → M03-W3/W4 | Exact persistent non-root home/native Pi state survives restart/recreation. |
| PIB-REQ-003 | M01 → M03-W3 | Refreshed target UID/GID, normal non-root writes and working sudo. |
| PIB-REQ-004 | M03-W2/W3 | Real model interaction through authenticated Codex-LB; no direct Pi ChatGPT/Codex OAuth. |
| PIB-REQ-005 | M03-W3/W4 | Native session create/exit/resume across restart/recreation. |
| PIB-REQ-006 | M01 → M03-W3 | Exact `/projects` mount and selected repository read/write with correct ownership. |
| PIB-REQ-007 | M01 → M03-W3 | Exact `/worktrees` mount and explicit existing worktree operation. |
| PIB-REQ-008 | M01 → M03-W3 | Supported Node/Pi and complete accepted tool inventory including Git LFS. |
| PIB-REQ-009 | M01 → M03-W3 | Strict persistent GitHub host verification and authenticated SSH Git operation. |
| PIB-REQ-010 | M01 → M03-W3 | Persistent Git identity, outbound access and ordinary authorized Git/`gh` operation. |
| PIB-REQ-011 | M01 → M03-W3 | Live negative inspection: no Docker socket/root/unrelated-appdata mounts or inbound SSH daemon. |
| PIB-REQ-012 | M01 → M03-W3/W4 | Native terminal/TUI usable for normal operation and recovery. |
| PIB-REQ-013 | M01 → M03-W4 | Europe/Zurich and `unless-stopped` configuration/readback; no Docker-wide/host restart exercise is required in Phase 1 under PIB-ADR-007. |
| PIB-REQ-014 | M02 → M03-W4 | Stable-only runtime selection and failed-candidate fallback preserve live durable state. |
| PIB-REQ-015 | M02 → M03-W4 | Actual prior deployment candidate rollback preserves persistent mounts. |
| PIB-REQ-016 | M01 → M03-W3 | Normal required environment remains repository/image reproducible. |
| PIB-REQ-017 | M02 → M03-W4 | Bounded log rotation/retention and readable production diagnostics. |
| PIB-REQ-018 | M01 → M03-W3/W4 | Pi persistent home remains inside ordinary appdata backup scope without special Pi exclusion. |
| PIB-REQ-019 | M03-W1/W4 | No dependency on or project-owned mutation of `chatgpt-ce-workstation`. |
| PIB-REQ-020 | M02 → M03-W4 | Documented normal update operation runs successfully on production. |
| PIB-REQ-021 | M02 → M03-W4 | Planned stop/update gives bounded graceful opportunity and persisted session resumes. |
| PIB-REQ-022 | M03-W1/W2/W3 | Dedicated authenticated Pi client credential survives required lifecycle without Git/image/log exposure. |
| PIB-REQ-023 | M03-W1/W3/W4 | Codex-LB owns account OAuth/refresh/routing; Pi holds no pooled OAuth tokens; continuation limitation is recorded. |
| PIB-REQ-024 | M03-W1/W3/W4 | Codex-LB remains separately deployed/persistent with verified health/compatibility/current baseline and no Pi appdata mount. |

## 6. Definition acceptance coverage

`A01`–`A21` below are local labels for the numbered Definition R3 acceptance outcomes, not additional requirements.

| Definition outcome | Establishing path | Outcome-level evidence obligation |
|---|---|---|
| A01 (1) | M01 → M03-W3 | Exact repository-owned deployment builds and starts on Unraid. |
| A02 (2) | M01 → M03-W4 | Live production readback proves the accepted `unless-stopped` restart policy and Europe/Zurich configuration; broad Docker/host restart is intentionally not executed under PIB-ADR-007 and that residual risk is explicitly recorded. |
| A03 (3) | M01/M02 → M03-W3 | Native TUI uses supported Node and exact current stable Pi. |
| A04 (4) | M03-W1/W3 | Codex-LB has usable authorized account capacity and Pi completes a real routed model interaction without direct Pi OAuth. |
| A05 (5) | M03-W2/W3/W4 | Pi → Codex-LB access survives Pi restart/recreation while Codex-LB account state remains independently persistent. |
| A06 (6) | M03-W3/W4 | Native Pi session create/exit/resume succeeds after lifecycle events. |
| A07 (7) | M01 → M03-W3 | Selected `/projects` repository read/write has acceptable host ownership. |
| A08 (8) | M01 → M03-W3 | Explicit existing `/worktrees` worktree operates without silent remap. |
| A09 (9) | M01 → M03-W3 | SSH Git read/write and ordinary authenticated `gh` API operation succeed. |
| A10 (10) | M01 → M03-W3 | Strict verified GitHub host trust is active. |
| A11 (11) | M01 → M03-W3 | No prohibited mounts and no dedicated inbound SSH shell service. |
| A12 (12) | M01 → M03-W3 | Required base tools including Git LFS are present and usable. |
| A13 (13) | M02 → M03-W4 | Failed latest-stable Pi update falls back safely without persistent-home loss. |
| A14 (14) | M02 → M03-W4 | Actual prior deployment candidate is selectable without durable-data rollback/loss. |
| A15 (15) | M02 → M03-W4 | Log growth is bounded and diagnostics remain readable. |
| A16 (16) | M02 → M03-W4 | Operator executes the documented normal update path successfully. |
| A17 (17) | M03-W1/W4 | Existing ChatGPT CE workstation remains operational and outside the dependency chain. |
| A18 (18) | M02 → M03-W4 | Planned restart/update uses bounded graceful stop and persisted session resumes. |
| A19 (19) | M03-W4 | Technical acceptance ends without a prescribed coding benchmark; later evaluation remains user-owned. |
| A20 (20) | M03-W1/W3/W4 | Normal Pi requests use Codex-LB's accepted account routing; evidence records that account-owned continuation may not migrate transparently. |
| A21 (21) | M03-W1/W3/W4 | Pi and Codex-LB remain independently persistent/deployed; Pi does not mutate/mount Codex-LB data and workstation remains independent. |

## 7. Verification, failure and recovery strategy

Keep execution evidence in the selected workstream's evidence/handoff area. Every result must identify the tested source/runtime/deployment context, expected versus observed behavior and limitations. Record blocked/skipped checks explicitly. Secrets, OAuth tokens, full client keys and private conversation content must never be committed.

The R3 integrated matrix must cover at least:

| Scenario | Expected safety/result |
|---|---|
| Codex-LB healthy, compatible and authenticated client key valid | Pi can use the accepted `openai-responses` path and complete a real model interaction. |
| Missing/invalid/revoked Pi client key | Model access fails clearly; no secret value is logged; Pi filesystem/session/Git availability is not falsely reported as destroyed. |
| Codex-LB unavailable/unreachable | Model access is unavailable with actionable diagnostics; Pi service/session/config/repository state remains intact. |
| Codex-LB restart/recreation with persistent data | Account/OAuth state remains Codex-LB-owned and returns without importing tokens into Pi. |
| Pi restart/recreation with preserved home/secret path | Provider/client configuration remains usable and no direct Pi OAuth is required. |
| Multiple eligible Codex-LB accounts | Requests follow accepted routing configuration; sticky/continuation limitations are recorded without promising seamless account migration. |
| Codex-LB dependency baseline is stale or incompatible | M03 blocks model acceptance or routes dependency correction through Codex-LB authority; no direct-Pi-OAuth bypass. |
| Empty/populated Pi home; repeated starts; invalid/changed UID/GID | Idempotent initialization; no overwrite/sweeping ownership takeover; actionable failure. |
| Online stable Pi startup; malformed/prerelease candidate; unsupported engine | Only compatible stable runtime admitted; working selection preserved on rejection. |
| Registry/network/install/startup failure | Bounded attempt; LKG/seed remains usable where compatible; persistent state unchanged. |
| Planned stop and deliberately uncooperative process | Graceful path first, bounded escalation, previously persisted session remains resumable. |
| Pi container restart and removal/recreation | Pi sessions/settings/provider config/Git trust and working runtime survive; Codex-LB data is not part of the Pi rollback payload. |
| Normal update plus broken candidate/image | Retained deployment is recoverable without restoring home/projects/worktrees backward. |
| Wrong SSH host key; explicit repository/worktree | Trust mismatch fails safely; correct cwd/ownership; no silent workspace substitution. |
| Sustained logs and live mount/process inspection | Rotation bounded; diagnostics readable; no prohibited privilege/mount/service introduced. |
| Restart-policy configuration / broad-restart waiver | Live Pi deployment reports the accepted restart policy/timezone; Docker-wide/host restart is not executed in Phase 1 and the residual risk is recorded explicitly without claiming runtime proof. |

Operational recovery distinguishes four failure domains:

1. **Pi runtime candidate failure** → accepted M02 LKG/seed recovery.
2. **Pi deployment image/config/startup failure** → accepted previous-deployment rollback.
3. **Codex-LB/model-access dependency failure** → preserve Pi durable state, diagnose/recover the independent dependency under its own authority; do not substitute direct Pi OAuth.
4. **Actual persistent-data damage** → stop writes and use the user's existing backup/restore authority; this is not an automatic binary rollback step.

No recovery path may restore Pi home or Codex-LB account data backward merely to make an older binary run.

## 8. Authorization and migration gates

Strategic Planning performs no live mutations. Future execution must recover existing valid authorization when present and otherwise stop at the smallest required gate.

The expected gate classes are:

- **Dependency live-write gate:** any Codex-LB fork/image/config/network mutation and creation/revocation of the dedicated Pi client credential.
- **Pi production bootstrap gate:** live Tower checkout fast-forward, creation of canonical Pi paths, secret/config placement, production build/start/recreate and deliberate external Git/GitHub write tests.

A single explicit authorization may cover multiple concrete operations when its scope is clear; do not manufacture per-command approval friction. Under PIB-ADR-007 there is no remaining Phase 1 disruptive-restart authorization gate.

No plan approval or prior read-only readiness evidence itself grants these live-write permissions.

## 9. JIT authority, downstream reconciliation and review boundary

Execution Prep owns new M03 Task Cards and may split/merge/reorder not-yet-started Cards within this approved M03 outcome. Strategic Planning does not create them.

After R3 approval, Execution Prep must:

- preserve completed M01/M02 and M03-T02/T03/T04 results plus completed non-disruptive M03-T05 evidence;
- reconcile the now-stale active M03-T05 contract without editing it in place: its remaining restart obligation is superseded by PIB-ADR-007, so mark the old Card appropriately under the explicit decision and create only the smallest replacement/finalization Card needed to bind existing evidence, final coverage/handoff and required review;
- do not replay already completed production recovery checks;
- evaluate a focused OpenSpec contract for the Pi ↔ Codex-LB provider/secret/persistent-config boundary;
- keep dependency correction in the Codex-LB authority domain if it requires changes outside `pi-unraid`;
- preserve all explicit live-write/credential/restart gates.

Delegated authority:

- **L1:** concrete secret injection path, endpoint/network route, provider config representation, probes, test mechanics and bounded implementation detail inside accepted M03 contracts.
- **L2:** split/merge/reorder future M03 Cards and refine technical acceptance from refreshed target/dependency evidence.
- Changed M03 execution strategy/milestone outcome with unchanged Definition returns to Strategic Planning.
- Changed requirements, access-layer architecture, service-separation invariant or authorization boundary returns to Project Definition.
- Missing material evidence routes through the appropriate durable Research obligation rather than guesswork.

R3 changes an accepted Definition outcome and removes an explicit execution gate, so this is not an editorial plan change. Independent Plan Review is **RECOMMENDED** and practical.

The planner's own audit must be GREEN before freeze. The exact R3 plan subject is then frozen as one immutable Git blob, `planning/reviews/R3.md` becomes `pending`, and the selected workstream manifest points `routing.plan_review` to that record.

This authoring session must stop at that fresh independent Plan Review boundary. It must not issue its own independent verdict, approve R3, enter Execution Prep, reconcile/create the remaining M03 Card state or perform any Tower/Codex-LB live-write.
