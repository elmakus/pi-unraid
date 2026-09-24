# Paseo/Pi Runtime on Unraid — Requirements

Revision: `R1`
Status: `approved`
Updated: `2026-09-24`
Definition subject: `paseo-gui-runtime@2`
Source Brainstorming: `brainstorming/PASEO_GUI_RUNTIME.md`

## Goal

Provide Paseo as the normal Android/PC GUI and execution surface for Pi on Unraid while keeping Git/Project Workflow canonical for project legality, keeping Orchestration Runtime responsible for runtime orchestration rather than deployment policy, and making the environment reproducible, recoverable, fast to update and safe to administer.

## Runtime and UX

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-001 | Paseo MUST be the normal user-facing entrypoint for Pi on Android/PC; terminal Pi is not the normal operating path. | MUST |
| PGR-REQ-002 | Project selection MUST remain user-driven; Main MUST NOT infer/bind a project solely from conversational context. | MUST |
| PGR-REQ-003 | After a project is selected, Main MUST recover current canonical PW/Git state before mutating work. | MUST |
| PGR-REQ-004 | The production shape MUST use one active Paseo container containing the Pi CLI/runtime needed by Paseo; a separate standalone Pi runtime MUST NOT remain an independent production authority. | MUST |
| PGR-REQ-005 | Paseo MAY spawn Pi RPC processes on demand; no permanent Pi RPC process is required. | SHOULD |
| PGR-REQ-006 | The deployment MUST produce Unraid-compatible ownership on host-mounted files (initial host target 99:100) and SHOULD autostart with Unraid. It MUST NOT hard-code Paseo's internal daemon UID/GID contrary to the official image contract; the exact mapping/user strategy is a Planning choice validated by live read/write smoke. | MUST |
| PGR-REQ-007 | The production container MUST NOT impose arbitrary CPU/RAM caps initially; shared memory MUST be sufficient for browser workloads (initial target 1 GiB). | MUST |
| PGR-REQ-008 | Native Paseo UI/session/history capabilities SHOULD be reused rather than replaced by a second custom dashboard absent a proven gap. | SHOULD |
| PGR-REQ-009 | Session/agent labels SHOULD be short and operationally meaningful; completed sessions MAY leave the active view while remaining history. | SHOULD |
| PGR-REQ-010 | Session/UI state MUST remain convenience state and MUST NOT become workflow/project authority. | MUST |

## Filesystem, persistence, access and secrets

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-011 | Native upstream HOME/config paths MUST be preserved where practical; persistent HOME is `/home/paseo` and Pi uses native `~/.pi/...` paths. | MUST |
| PGR-REQ-012 | The whole persistent Paseo HOME MUST be backed up as sensitive state; Git workspaces/worktrees MUST live outside appdata/HOME under a canonical workspace root, and Paseo's configurable worktree root MUST be pointed there rather than leaving canonical worktrees under protected HOME. | MUST |
| PGR-REQ-013 | The environment MUST expose only the intended workspace/repository roots rather than broad arbitrary Unraid storage by default. | MUST |
| PGR-REQ-014 | Paseo Relay MUST be the initial remote-access path; raw Paseo ports MUST NOT be exposed directly to the Internet in the initial design. | MUST |
| PGR-REQ-015 | Relay/pairing state MUST survive routine rebuild/restart, and device revocation SHOULD be individually manageable where upstream supports it. | SHOULD |
| PGR-REQ-016 | No alternate direct-LAN/tunnel access path is part of this scope; any future break-glass path requires a separate explicit design decision. | MUST |
| PGR-REQ-017 | Capability inventories, repository files and logs MUST NOT contain raw credentials. | MUST |
| PGR-REQ-018 | Prefer native secret files/mounts/OAuth/device-flow/token mechanisms over plaintext passwords where supported; unavoidable credential-bearing HOME state MUST be treated as secret-bearing. | MUST |
| PGR-REQ-019 | First-time account/service authentication requiring account choice or human interaction MUST require deliberate user participation; routine refresh/reuse of already-approved sessions MAY be automatic. | MUST |
| PGR-REQ-020 | Doctor/log/evidence surfaces MUST redact or avoid raw secrets and MAY expose only bounded auth-health/fingerprint metadata. | MUST |

## Tooling and browser capability

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-021 | The image MUST provide a practical general development baseline including shell/Git/network/build/Python/Node capabilities sufficient for normal repository work. | MUST |
| PGR-REQ-022 | Server-side Chromium + Playwright runtime support MUST be available inside the Unraid execution environment, including screenshot/PDF generation and both headless and headed/Xvfb operation without requiring a full desktop/noVNC stack. Paseo's current desktop-hosted Browser Tools MAY be complementary but MUST NOT be the sole browser mechanism. | MUST |
| PGR-REQ-023 | Browser automation MUST use a dedicated persistent automation profile rather than a personal desktop-browser profile. | MUST |
| PGR-REQ-024 | Browser downloads SHOULD default to temporary/task workspace storage; only workflow/task-required artifacts become durable evidence. | SHOULD |
| PGR-REQ-025 | `gh`, Docker CLI and Docker Compose MUST be available as global baseline tools; mounting the host Docker socket into the Paseo runtime is NOT required by default. | MUST |
| PGR-REQ-026 | Internal development servers MAY be started for authorized work but MUST NOT be publicly exposed by default. | MUST |

## Environment Capability Inventory and instruction plane

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-027 | pi-unraid MUST maintain one declarative **Environment Capability Inventory** for global environment availability, source/provenance, delivery mode, desired/observed version, runtime location and health/drift. | MUST |
| PGR-REQ-028 | The Environment Capability Inventory MUST NOT own OR role ceilings, runtime tool/action classification, role-default bundles, assignment eligibility or task-scoped runtime grants. | MUST |
| PGR-REQ-029 | OR's Tool Registry MAY consume stable capability identifiers and observed installed versions from the environment, but OR MUST NOT become the global installer/updater and pi-unraid MUST NOT duplicate OR runtime-use policy. | MUST |
| PGR-REQ-030 | New or removed durable global environment capabilities require explicit user approval; routine updates of already-approved capabilities do not require repeated capability approval. | MUST |
| PGR-REQ-031 | Unexpected/missing capabilities MUST be reported as drift; reconcile MAY restore missing already-approved state but MUST NOT silently delete unknown extra capabilities. | MUST |
| PGR-REQ-032 | Global AGENTS.md/skills/extensions MUST be reproducible from version-controlled source and installed into Pi-native locations; instruction-plane updates MUST support snapshot, rollback and fresh-session smoke. | MUST |
| PGR-REQ-033 | Global AGENTS.md MUST remain compact and route to progressively loaded skills/references rather than duplicate large policy documents. | MUST |
| PGR-REQ-034 | Unraid administration knowledge SHOULD live in a dedicated global skill/reference set; project-local AGENTS.md MUST NOT duplicate global Unraid or Project Workflow semantics. | MUST |
| PGR-REQ-035 | A future PWv2.1 Pi extension, once separately defined and released, remains PW-owned semantically; pi-unraid owns installation/update/configuration of the released artifact only. | MUST |

## PW / OR / Git authority boundaries

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-036 | Project Workflow remains the sole authority for managed workflow legality, accepted durable state, branch/write scope, reviews and real user stops. | MUST |
| PGR-REQ-037 | Orchestration Runtime owns concrete worker/session scheduling, runtime concurrency, role/tool assignment and worker/worktree realization subject to PW legality. | MUST |
| PGR-REQ-038 | pi-unraid owns the workspace/filesystem substrate and MUST provide safe worktree-capable storage, permissions, persistence and readback, but MUST NOT freeze OR's worker topology. | MUST |
| PGR-REQ-039 | Repository/PW durable state MUST remain sufficient to recover legal project continuation after loss of chat, OR runtime state, Paseo sessions and HOME convenience state. | MUST |
| PGR-REQ-040 | Runtime/Paseo/OR state MUST NOT become a second Task Board or workflow authority. | MUST |
| PGR-REQ-041 | Direct Main/Pi ad-hoc mutation MUST locally enforce no-write-on-main and creation/use of a legal branch/worktree before first write. | MUST |
| PGR-REQ-042 | pi-unraid MUST NOT claim universal semantic ownership of the generic cross-runtime ad-hoc Git mutation rule; the canonical cross-runtime owner remains unresolved and MUST be settled separately before universal promotion. | MUST |
| PGR-REQ-043 | Managed PW mutations MUST follow current PW authority even when local environment safety rules are stricter or more permissive. | MUST |
| PGR-REQ-044 | A Main/Pi policy guard MAY mechanically enforce environment-owned host safety gates only; PW gates and OR runtime policy MUST be consumed from their owning contracts rather than copied into pi-unraid. | MUST |

## Unraid administration and host safety

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-045 | Main MUST receive full administrative capability over the Unraid host with the native Unraid GraphQL API as the preferred structured primary control path and non-interactive SSH as fallback for API gaps, API outage and OS/plugin/filesystem/recovery work; after fallback, normal operation SHOULD return to the structured API when healthy. | MUST |
| PGR-REQ-046 | Normal Main/Pi process identity SHOULD remain non-root/no-sudo inside the application runtime; host administration SHOULD use explicit host-control transports/credentials. | SHOULD |
| PGR-REQ-047 | Ordinary bounded host/container/service operations within accepted task authority MAY proceed without per-command user confirmation. | MUST |
| PGR-REQ-048 | Whole-host reboot, whole Docker-engine restart, Unraid OS upgrade, disk formatting, deletion of broad shares/appdata and comparable high-impact operations MUST require explicit user approval. | MUST |
| PGR-REQ-049 | Broad routing/firewall/default-gateway/DNS changes MUST require a user gate; ordinary single-application/container port changes MAY proceed within accepted task scope. | MUST |
| PGR-REQ-050 | Before host mutation Main MUST perform bounded readback; broad changes MUST have a rollback/snapshot anchor where technically applicable. | MUST |
| PGR-REQ-051 | Safe/unambiguous rollback MAY be automatic after a failed accepted change, but an operation that itself requires a user gate (for example host reboot) remains gated during recovery. | MUST |
| PGR-REQ-052 | Host-control credentials MUST remain outside Git, persist across rebuilds through the secret strategy, and support controlled rotation/readback. | MUST |
| PGR-REQ-053 | Derived host inventory (containers/shares/appdata/networks/storage/dependencies) MAY be regenerated from live state and MUST NOT become a manually maintained canonical truth store. | MUST |
| PGR-REQ-054 | Host doctor and Paseo deployment doctor MUST remain distinct from PW Recovery and OR orchestration doctor. | MUST |

## Update, build, cache and rollback

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-055 | Every user-approved environment maintenance update MUST attempt to bring all approved global environment components to their latest accepted stable lines together, excluding project-local dependencies governed by repository lockfiles/manifests; an approved compatibility exception is the only allowed deliberate lag. | MUST |
| PGR-REQ-056 | "Latest" MUST mean the accepted stable line for each component (for example Node latest LTS where that is the accepted line), not arbitrary prerelease/nightly channels. | MUST |
| PGR-REQ-057 | Update orchestration MUST resolve latest first, freeze an exact immutable candidate resolution, and only then build/test; builds MUST NOT independently re-resolve latest. | MUST |
| PGR-REQ-058 | Candidate resolution SHOULD include exact versions and digest/SHA/integrity where upstream provides them, and the exact resolution MUST be recoverable from the built artifact/evidence. | MUST |
| PGR-REQ-059 | If any mandatory component cannot be resolved or the coordinated latest set is incompatible, promotion MUST fail closed rather than silently produce an arbitrary partial environment. | MUST |
| PGR-REQ-060 | A temporary compatibility exception from latest MAY be proposed but requires explicit user approval, durable rationale and automatic re-evaluation on later maintenance. | MUST |
| PGR-REQ-061 | Build/publish SHOULD use the self-hosted Unraid runner and private GHCR for the project child image and remote BuildKit cache. The child image MUST derive from the exact resolved official stable `ghcr.io/getpaseo/paseo:<version-or-digest>` base. | SHOULD |
| PGR-REQ-062 | Every promoted image MUST have immutable identity/provenance; floating `latest` is only an alias for a successfully promoted candidate. | MUST |
| PGR-REQ-063 | Production cutover MUST use a staged build → fast checks → temporary runtime smoke → promote/cutover → post-deploy smoke flow. | MUST |
| PGR-REQ-064 | A failed pre-deploy smoke MUST leave production untouched; a failed post-deploy smoke SHOULD automatically roll back to the prior coherent known-good set when safe/unambiguous. | MUST |
| PGR-REQ-065 | Rollback MUST normally preserve valid persistent user/session/browser/pairing state; HOME rollback requires proven migration/state corruption and destructive restore requires user approval. | MUST |
| PGR-REQ-066 | Paseo+Pi builds MUST use a dedicated persistent Buildx/BuildKit builder/cache independent of runtime replacement and independent from the Workstation cache namespace. | MUST |
| PGR-REQ-067 | Build cache MUST be bounded, retained across ordinary updates, pruned after successful work rather than before needed builds, and MAY use registry-backed cache as secondary/recovery cache. | MUST |
| PGR-REQ-068 | Dockerfile/build graph MUST be designed for minimal invalidation and SHOULD use componentized stages/cache mounts/rebase techniques where measured evidence shows benefit. | MUST |
| PGR-REQ-069 | Build timing MUST be observable by material phase; repeated unnecessary broad rebuilds MUST be treated as a build-design defect. | MUST |
| PGR-REQ-070 | Acceptance MUST demonstrate both a cold build and a representative warm update with real cache reuse; no arbitrary hard time SLA is required before measurement. | MUST |

## Health, observability, recovery and acceptance

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-071 | Docker healthcheck MUST be lightweight; doctor/readiness provides deeper checks and MUST remain read-only. | MUST |
| PGR-REQ-072 | Provide quick and full doctor depths; exact check matrix remains downstream design, but results MUST be machine-readable plus concise GREEN/WARN/RED human summary. | MUST |
| PGR-REQ-073 | `doctor` MUST diagnose only; `reconcile` restores current desired state and `update` intentionally changes version lines. | MUST |
| PGR-REQ-074 | Optional capability failure SHOULD degrade to WARN unless required by the current task; core control-plane failure MUST be RED. | MUST |
| PGR-REQ-075 | Runtime/worker logs MUST be bounded/rotated, while PW durable evidence remains governed by Git/PW rather than runtime retention. | MUST |
| PGR-REQ-076 | Main SHOULD consume bounded structured results/status by default and inspect full logs only when blocked/RED/ambiguous or debugging. | SHOULD |
| PGR-REQ-077 | User notifications SHOULD be limited to meaningful completion, errors and action-required states; routine worker progress may remain in native Paseo UI without push spam. | SHOULD |
| PGR-REQ-078 | Crash/restart recovery MUST read canonical Git/PW state before trusting stale session convenience state and MUST NOT blindly replay uncertain side effects. | MUST |
| PGR-REQ-079 | First production acceptance MUST include Pi RPC, Relay path from the user's phone, browser, GitHub auth/workflow access, doctor/capability checks, cold/warm build, rollback/recovery and loss-of-runtime/session-state recovery. | MUST |
| PGR-REQ-080 | Routine updates MUST use time-proportional fast-path validation; materially broader base/security/Relay/control-plane changes require wider validation. | MUST |

## Deferred/integration boundaries

| ID | Requirement | Priority |
|---|---|---|
| PGR-REQ-081 | Orchestration Runtime MUST NOT be deployed as part of the initial Paseo+Pi bring-up; it integrates only after the base environment is GREEN. | MUST |
| PGR-REQ-082 | The future PWv2.1 Pi-extension packaging/bootstrap is a separate later integration scope after PWv2.1's final contract stabilizes. | MUST |
| PGR-REQ-083 | Secret materialization plus exact-candidate Paseo/Pi/Relay, SpecPi, pi-mcp-adapter, browser-runtime, filesystem-ownership and registry/cache behavior MUST be verified by implementation readback/smoke rather than guessed; Definition Research has selected GraphQL-primary/SSH-fallback host control and the official Paseo GHCR base. | MUST |
| PGR-REQ-084 | Research/Planning MAY choose concrete schemas, command names, package lists, cache sizes, doctor check lists and transport implementations only if they preserve these authority and product constraints. | MUST |
| PGR-REQ-085 | The legacy standalone Pi bootstrap runtime/appdata SHOULD be retired only after Paseo reaches GREEN and rollback/recovery are verified. | MUST |
| PGR-REQ-086 | SpecPi core MUST be installed as an approved global capability with SpecPi scope monitoring inactive because PW owns project scope; its improvement/wishlist capability MAY remain enabled. The exact resolved SpecPi/Pi pair MUST pass compatibility smoke before promotion. | MUST |
| PGR-REQ-087 | `pi-mcp-adapter` SHOULD be installed as the initial Pi MCP adapter when the exact resolved Pi/Paseo/adapter combination passes compatibility smoke; its config/readback and failure state MUST be covered by full doctor/acceptance. | MUST |
