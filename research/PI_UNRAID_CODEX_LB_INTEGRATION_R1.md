# Research — Pi → Codex-LB Phase 1 integration facts

Research ID: `pi-unraid-codex-lb-integration-r1`
Status: `complete`
Origin role: `project_definition`
Origin subject: `pi-unraid-bootstrap@R2`
Return target: `project_definition:pi-unraid-bootstrap@R2`
Research question: `Determine the current, source-grounded Pi → Codex-LB integration contract needed for Phase 1: provider/protocol compatibility, OAuth persistence and refresh ownership, multi-account behavior, failure/fallback semantics, and the correct Unraid deployment topology from the first real production start, including whether/how the existing Tower Codex-LB deployment can be used without violating Pi persistence/security/workstation-independence invariants.`
Return reconciliation: `applied`
Return reconciliation result: `requirements/PI_UNRAID_BOOTSTRAP.md@R2; decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md; PROJECT.md definition subject pi-unraid-bootstrap@R2; implementation/workstreams/feature-pi-unraid-bootstrap/WORKSTREAM.yaml authority; Task Board M03 decision_state=review`

## Trigger / authority

The user explicitly changed Phase 1 product/system authority before the first production deployment:

- Phase 1 must use Codex-LB as the ChatGPT/Codex OAuth access layer from the first real Pi run.
- Direct Pi → built-in ChatGPT OAuth is no longer the required or intended bootstrap path.
- Codex-LB is no longer a Phase 1 non-goal.
- Existing completed M01/M02 checkpoints and evidence remain historical truth and must not be rewritten.
- No production deployment may proceed under the old M03-T01 authority.

## Sources / exact current subjects

Primary/upstream evidence checked 2026-09-23:

- Pi current main, including:
  - `packages/coding-agent/docs/models.md`
  - `packages/coding-agent/docs/custom-provider.md`
  - `packages/ai/src/api/openai-codex-responses.ts`
- codex-lb upstream `Soju06/codex-lb` main at `3d23d53f89dbbaa2353040a30451cf90ca48ee92`, including:
  - `README.md`
  - `docs/client-setup.md`
  - `docs/routing.md`
  - `docs/api-keys.md`
  - `docs/deployment/docker.md`
  - `.env.example`
  - OAuth/account/token persistence and refresh implementation/specs.
- project fork `elmakus/codex-lb` main at `0b673d84316c33dd166e6bffbe6b66444379a895`.
- read-only Tower inspection of the existing `codex-lb-clean` deployment and its persistent database/configuration. No credential/token values were read or recorded.
- Current public docs:
  - https://pi.dev/docs/latest/models
  - https://pi.dev/docs/latest/custom-provider
  - https://soju06.github.io/codex-lb/client-setup/
  - https://github.com/Soju06/codex-lb/blob/main/docs/api-keys.md

## Verified findings

### 1. Pi can use Codex-LB without a Pi provider extension

Pi explicitly recommends `~/.pi/agent/models.json` when the target is an API it already supports. Pi supports the OpenAI Responses API and permits an arbitrary `baseUrl` plus API-key interpolation.

codex-lb exposes an OpenAI-compatible `/v1` surface and documents Responses-compatible clients using it. Its own current compatibility documentation specifically names clients using `api: openai-responses` against `/v1`.

Therefore the least-complex Phase 1 integration is a Pi provider entry backed by:
- Codex-LB base URL ending in `/v1`;
- Pi API type `openai-responses`;
- a Codex-LB proxy API key;
- selected model metadata supplied in Pi config, with live model discovery deferred unless later required.

No custom Pi extension is required merely to proxy model traffic through Codex-LB.

### 2. Do not use Pi's native `openai-codex-responses` path with a Codex-LB API key

Pi's native ChatGPT/Codex implementation expects its bearer material to be an actual ChatGPT/Codex token and extracts `chatgpt_account_id` from the JWT before building the upstream request.

A Codex-LB client key is an opaque `sk-clb-...` proxy credential, not that ChatGPT JWT. Pointing Pi's native Codex transport at Codex-LB while supplying a Codex-LB API key would therefore violate Pi's native auth assumptions.

The safe compatibility seam is the generic OpenAI Responses client path against Codex-LB `/v1`, where the opaque Codex-LB key is ordinary downstream bearer authentication and Codex-LB owns upstream account identity.

### 3. OAuth ownership moves completely to Codex-LB

codex-lb performs ChatGPT/Codex OAuth itself. Its account store contains encrypted access, refresh and ID-token material and ChatGPT account identity. Its refresh subsystem proactively exchanges refresh tokens and marks permanently invalid/revoked credentials as requiring reauthentication.

For Phase 1 this means:
- ChatGPT/Codex account login is performed in Codex-LB, not in Pi;
- Codex-LB persists OAuth/account material under its own persistent data directory;
- Pi must not import/export or persist the pooled accounts' ChatGPT access/refresh tokens;
- Pi needs only the Codex-LB endpoint/client credential plus its ordinary native Pi settings/session state.

The old R1 requirement that Pi's `~/.pi/agent/auth.json` hold the ChatGPT OAuth session is therefore obsolete for Phase 1.

### 4. Multi-account behavior is a Codex-LB concern, not a Pi concern

Current codex-lb provides multiple routing strategies and per-request account eligibility. Its recommended normal strategies include capacity-weighted and relative-availability routing; sticky threads preserve locality where possible.

A hard limitation is material: continuation state can be owned by one account. When a continuation cannot safely move, a turn may fail even though another pooled account is healthy. Starting a fresh conversation routes normally. Phase 1 must not claim transparent cross-account continuation in every failure case.

Tower read-only state currently shows:
- 3 Codex-LB accounts, all active;
- routing strategy `capacity_weighted`;
- sticky threads enabled;
- proxy API-key authentication enabled;
- 3 active API keys, none currently restricted to an account subset.

No account identifiers, e-mail addresses or token values were recorded.

### 5. A dedicated Pi client key is the correct downstream credential

codex-lb protects `/v1/*` and `/backend-api/codex/*` with dashboard-created API keys when proxy-key auth is enabled. Keys can carry expiry, model/rate restrictions and optional account scoping.

Pi should use a dedicated Codex-LB API key rather than reusing a ChatGPT OAuth token or another client's key. The full key is secret and must not be committed.

Exact secret placement can remain an implementation choice, but it must survive normal Pi recreation and must not place a raw key in Git/evidence/logs. Using a host/runtime secret passed as `CODEX_LB_API_KEY` and referenced from persistent Pi `models.json` by environment interpolation is compatible with Pi's documented config model.

### 6. Existing Tower Codex-LB is already a separate persistent service

Read-only Tower facts:

- container: `codex-lb-clean`;
- status: running;
- restart policy: `unless-stopped`;
- image: `ghcr.io/elmakus/codex-lb:main`, image revision `0b673d84316c33dd166e6bffbe6b66444379a895`;
- host ports: `2455` proxy/dashboard and `1455` OAuth callback;
- persistent bind: `/mnt/user/appdata/codex-lb-clean` → `/var/lib/codex-lb`;
- data directory contains the SQLite store and encryption key;
- `GET /health` returns 200;
- unauthenticated `GET /v1/models` returns 401, confirming proxy-key enforcement;
- container is attached to existing network `ibraproxy`.

This deployment already owns OAuth persistence independently of `pi-unraid`; duplicating Codex-LB inside the Pi container would couple lifecycles and duplicate secret state without a Phase 1 need.

### 7. The deployed fork is materially behind current upstream

The project fork preserves one local delta: GHCR publishing for `ghcr.io/elmakus/codex-lb:main`. Its main currently contains upstream through `0f6a31c56ac30804ca1c0fac27ca02c6f59bf2b0` plus that publishing commit.

Current upstream main is `3d23d53f89dbbaa2353040a30451cf90ca48ee92`. GitHub comparison reports upstream has advanced by 92 commits while the fork has one local commit beyond the common base.

The existing service is therefore suitable evidence that the architecture exists and already has persistent active accounts, but M03 must refresh/reconcile the fork/current image before treating it as the accepted production dependency. This is a planning/execution prerequisite, not a reason to revert to direct Pi OAuth.

### 8. Deployment topology supported by current facts

The simplest Phase 1 topology is two independent services on Tower:

`Pi container → authenticated OpenAI Responses HTTP → existing Codex-LB service → pooled ChatGPT/Codex OAuth accounts`

Codex-LB remains independently deployed and backed up under its own appdata. Pi retains its own `/home/pi`, projects and worktrees. Pi does not mount Codex-LB data and Codex-LB does not mount Pi data.

Pi should reach the existing Codex-LB listener through a deliberate host/network route; it does not need to join the workstation or consume workstation secrets. Exact Docker reachability mechanics (host-gateway versus an explicitly shared network) are implementation-level and must be verified before production start. Prefer the option that changes no Codex-LB lifecycle/configuration unless target testing proves it inadequate.

### 9. Definition changes required

R2 must at minimum:

- replace PIB-REQ-004 direct Pi ChatGPT OAuth with Codex-LB-backed ChatGPT/Codex access from first real use;
- keep Pi native state persistence but stop treating Pi `auth.json` as the owner of ChatGPT OAuth for Phase 1;
- add Codex-LB availability/persistence/client-credential requirements and failure semantics;
- require a dedicated Pi→Codex-LB client credential with no secret in Git/evidence;
- define multi-account routing as Codex-LB-owned and avoid promising seamless failover of owner-bound continuation state;
- remove Codex-LB/multi-account routing from Phase 1 non-goals while keeping broader router/orchestration work out of scope;
- revise acceptance so first real Pi model interaction proves traffic through Codex-LB and no direct Pi ChatGPT OAuth is performed;
- preserve M01/M02 completed checkpoints as historical implementation/evidence while replanning M03 around the new dependency.

## Research conclusion

The requested architecture is feasible without a Pi extension and without undoing M01/M02.

Recommended Definition/Planning boundary:
- Definition R2 freezes Codex-LB as the required OAuth/account-routing layer and the two-service separation/invariants.
- Strategic Planning R2 decides the safe prerequisite order: reconcile/update the existing Codex-LB dependency, establish a dedicated Pi client key and verified reachability, then deploy/configure Pi and perform M03 acceptance through Codex-LB.
- M03 must not reuse the superseded R1 deployment Card.

No unresolved product choice is required to establish this R2 target. Exact networking/secret injection commands remain delegated implementation detail subject to JIT verification and explicit live-write gates.

Research is evidence, not accepted requirement/decision/plan authority.
