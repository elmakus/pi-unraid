# Paseo GUI Runtime — Definition Research R1

Date: 2026-09-24
Origin: `definition:R1|paseo-gui-runtime@2|current-runtime-integration-facts`
Return target: Definition R1
Status: complete

## Executive finding

The promoted product/authority choices are technically coherent with current upstream Paseo, Pi, Unraid API, Docker BuildKit and Playwright.

Research supports the intended architecture with bounded refinements rather than reopening product scope:

1. use the official Paseo stable Docker image as the child-image base and install Pi/tooling on top;
2. use Unraid's native GraphQL API as the preferred structured host-control path with SSH as fallback for gaps/failure/recovery;
3. keep server-side Chromium/Playwright browser capability independent from Paseo's current desktop-hosted Browser Tools;
4. preserve Unraid-compatible host filesystem ownership without hard-coding Paseo's internal daemon UID if that conflicts with the official image entrypoint;
5. require live compatibility smoke for SpecPi and pi-mcp-adapter on the exact resolved Pi/Paseo candidate because both ecosystems are moving quickly.

No material user/product choice was discovered.

## Official/upstream evidence

### Paseo

- Current stable release observed: Paseo `v0.9.1` (2026-09-22).
- Official stable Docker images are published as `ghcr.io/getpaseo/paseo:<version>` and `:latest`; beta tags do not move `:latest`.
- Official Docker docs explicitly recommend extending the base image with required agent CLIs; the base image intentionally does not bundle Pi.
- Paseo's Pi provider is process-backed: it requires the `pi` binary and launches/talks to it through `pi --mode rpc`; Paseo does not embed Pi's runtime SDK.
- Official Docker state lives under `/home/paseo`; `HOME=/home/paseo`, `PASEO_HOME=/home/paseo/.paseo`. The base daemon/agents run non-root as the `paseo` user; official docs describe uid/gid 1000:1000 and allow host ownership adjustment or a container `--user` strategy.
- Paseo worktrees default below `PASEO_HOME/worktrees`, but `worktrees.root` is configurable. Therefore this project can keep worktrees outside protected HOME while still using native Paseo worktree management.
- Relay is the recommended remote path, uses outbound daemon connectivity and end-to-end encryption, and requires no open inbound port. Relay is opt-in on fresh installations and pairing can explicitly enable it.
- The official Docker image enables the bundled web UI and listens on port 6767 inside the container. Therefore the Relay-only design must avoid publishing that port to the host/network; if direct/network publication is later enabled, upstream recommends password protection.
- Paseo has native workspace/worktree and orchestration surfaces. These are runtime substrate capabilities, not justification to move PW/OR semantics into Paseo.
- Paseo Browser Tools currently require a connected Paseo desktop browser host; the daemon itself does not run the browser. Therefore they cannot be the sole browser mechanism for a headless Unraid deployment or Android-only use.

Primary upstream references:
- https://github.com/getpaseo/paseo/blob/main/public-docs/docker.md
- https://github.com/getpaseo/paseo/blob/main/docs/providers.md
- https://github.com/getpaseo/paseo/blob/main/public-docs/security.md
- https://github.com/getpaseo/paseo/blob/main/public-docs/worktrees.md
- https://github.com/getpaseo/paseo/blob/main/public-docs/browser.md
- https://github.com/getpaseo/paseo/releases

### Pi

- Current stable observed: Pi `v0.87.1`.
- Current canonical package/repository are `@earendil-works/pi-coding-agent` and `earendil-works/pi`; the older Mario Zechner npm scope is deprecated.
- Pi requires Node.js 22.19+ for the current npm installation path.
- Pi has native RPC mode, user-level `AGENTS.md`, extensions and skills under the agent directory, project-local resources, project trust and a package manager.
- Global Pi package/update commands exist, but this project's deterministic update design should resolve exact versions first and install the frozen versions rather than let an in-build `pi update --all` silently re-resolve latest.
- Skills use progressive disclosure: metadata is available at startup and full `SKILL.md` content loads on demand.

Primary upstream references:
- https://pi.dev/docs/latest/quickstart
- https://pi.dev/docs/latest/configuration
- https://pi.dev/docs/latest/cli
- https://pi.dev/docs/latest/extensions
- https://pi.dev/docs/latest/security
- https://github.com/earendil-works/pi/releases

### SpecPi

- Current package observed: `specpi 0.31.0` (2026-09-23).
- Scope control and the human-selected improvement/wishlist loop are separate behavioral concerns in the package.
- `/scope clear` turns scope monitoring off. This is sufficient as a semantic requirement: production must keep SpecPi scope monitoring inactive because PW owns project scope.
- The current SpecPi documentation states testing against Pi 0.84.4, while current Pi observed is 0.87.1. Compatibility with the exact latest Pi candidate is therefore not proven by documentation and requires live smoke before promotion.

References:
- https://pi.dev/packages/specpi
- https://tannermidd.github.io/SpecPi/wiki/

### pi-mcp-adapter

- Current Pi catalog version observed: `pi-mcp-adapter 2.36.0`.
- The adapter uses lazy MCP server startup and cached metadata, with standard shared MCP files preferred and Pi-owned override files for adapter-specific settings.
- Paseo's current Pi provider documentation explicitly depends on pi-mcp-adapter for Pi MCP support and describes generated per-agent MCP config behavior.
- Tracker history shows real compatibility/config regressions across rapidly moving Pi/MCP versions. This supports an exact-candidate compatibility smoke and rollback, not a fixed long-term pin.

References:
- https://pi.dev/packages/pi-mcp-adapter
- https://github.com/nicobailon/pi-mcp-adapter
- https://github.com/nicobailon/pi-mcp-adapter/issues

### Unraid

- Unraid 7.2+ includes the GraphQL API natively.
- The API supports API-key authentication with roles/permissions and covers system information, array operations, Docker, networks and other core resources.
- Programmatic API key creation/revocation is supported, including granular permissions.
- Some host-level/maintenance/plugin functionality is not a complete GraphQL surface; official CLI/OS administration remains relevant.
- Therefore the accepted "structured first, fallback when needed" intent can be concretized as:
  - primary: Unraid GraphQL API using a dedicated API key and appropriate permissions;
  - fallback: non-interactive SSH for operations not represented safely by the API, API outage, OS/plugin/filesystem/recovery work;
  - after fallback/recovery, prefer returning to the structured API path when healthy.

References:
- https://docs.unraid.net/API/
- https://docs.unraid.net/API/how-to-use-the-api/
- https://docs.unraid.net/API/programmatic-api-key-management/
- https://docs.unraid.net/unraid-os/system-administration/advanced-tools/command-line-interface/

### Docker BuildKit / registry cache

- Docker officially supports persistent package cache mounts, deliberate layer ordering and external registry-backed build cache.
- Registry cache uses `--cache-to type=registry` / `--cache-from type=registry`.
- `COPY --link` can preserve/rebase reusable layers when earlier/base layers change.
- These findings validate the existing persistent dedicated Buildx builder + bounded local cache + secondary registry cache + cache-friendly layer design.

References:
- https://docs.docker.com/build/cache/optimize/
- https://docs.docker.com/build/cache/backends/registry/
- https://docs.docker.com/reference/dockerfile/

### Playwright / Chromium

- Playwright documents container-specific browser dependencies and requires Playwright package/browser versions to match.
- The official docs recommend init/PID handling and sufficient Chromium shared-memory handling for container stability.
- The project can retain its 1 GiB shared-memory target and should use an init/reaping strategy; exact Compose mechanism is Planning detail.
- Paseo desktop Browser Tools are complementary and must not replace the server-side Chromium/Playwright baseline.

Reference:
- https://playwright.dev/docs/docker

## Project/runtime evidence

- `elmakus/pi-unraid` current Phase-1 Dockerfile is a standalone Pi bootstrap based on Node 24 with Pi 0.87.1. It is not the target Paseo child image and contains old bootstrap choices (including sudo and `/home/pi`) that must not be carried forward accidentally.
- Current Phase-1 Compose proves the established Unraid appdata/workspace mounting pattern and bounded json-file log rotation.
- `elmakus/chatgpt-ce-workstation/scripts/buildkit-cache.sh` already proves the dedicated persistent `docker-container` Buildx builder pattern with bounded prune controls (24 GB max-used, 8 GB reserved defaults).
- `elmakus/orchestration-runtime` remains durably blocked on the missing real Paseo/Pi deployment, confirming that OR live compatibility evidence must follow this deployment rather than be guessed now.
- No live Paseo/Pi production deployment exists yet; exact runtime integration/permissions/Relay/browser/host-control acceptance remains an implementation acceptance obligation.

## Tracker/discussion evidence

Recent Paseo issue history shows that Pi integration can regress at RPC/protocol/command-discovery/model-state boundaries even when broad integration exists. Recent examples include Pi RPC frame/protocol, command/skill discovery, thinking-state synchronization and agent RPC timeout issues. Several have been fixed; their value here is to justify exact-candidate live smoke rather than assume all future latest versions are compatible.

Recent pi-mcp-adapter history likewise shows config-merge and peer-version compatibility defects across versions. This supports the already-selected controlled update/smoke/rollback model.

No tracker evidence contradicts the core architecture; it strengthens the need for compatibility gates.

## Practitioner/community evidence

Unraid community use of the GraphQL API in dashboards/n8n integrations confirms it is practical for Docker/array/system automation. Community reports also include occasional API/plugin outage cases. This supports GraphQL as primary structured control while retaining SSH recovery/fallback instead of making GraphQL the only administrative path.

Community evidence is supporting only and does not override official Unraid API authority.

## Reconciliation into Definition

The following Definition refinements are justified without reopening user/product scope:

1. **Host control:** select Unraid GraphQL API as structured primary and SSH as fallback.
2. **Paseo base:** use official stable `ghcr.io/getpaseo/paseo:<resolved-version>` as the child-image base.
3. **UID/GID:** require effective Unraid-compatible host ownership; do not hard-code an internal daemon UID when the official image has its own non-root entrypoint. Exact mapping must pass live volume/read-write smoke.
4. **Worktree placement:** configure Paseo worktree root outside protected HOME to preserve the accepted HOME/code separation.
5. **Browser:** keep in-container Chromium/Playwright as the headless baseline; current Paseo Browser Tools are optional complementary capability only when a desktop browser host is connected.
6. **SpecPi:** scope monitoring must remain inactive; exact latest SpecPi/Pi pair must pass smoke before promotion.
7. **MCP:** current pi-mcp-adapter remains the preferred initial adapter if exact latest compatibility smoke passes; its config/readback must be included in doctor/full acceptance.
8. **Build:** use official Paseo GHCR base plus private GHCR child images and BuildKit registry cache, while retaining local persistent BuildKit cache as the fast path.

## Limitations

- No live Paseo/Pi target exists yet, so real provider launch, Relay pairing persistence, filesystem ownership, browser execution, MCP behavior and host-control fallback cannot be claimed as proven until implementation acceptance.
- Exact Unraid OS version/API enablement on Tower was not read from the live host in this Definition Research pass.
- SpecPi documentation lags current Pi by several minor releases; live compatibility is deliberately required.
- The exact browser MCP/control surface above raw Playwright is not product authority and remains a Planning/implementation choice; no additional global browser extension is required by Definition.
- The future PWv2.1 Pi extension is deliberately outside this Research until PWv2.1's final contract is stable.

## Conflict summary

No material conflict between accepted user/product authority and current upstream facts.

Three implementation assumptions required narrowing:
- internal UID/GID must not be frozen independently of the official Paseo entrypoint;
- Paseo's native Browser Tools cannot satisfy headless Unraid browser automation alone;
- latest SpecPi/pi-mcp-adapter/Paseo/Pi combinations require exact live compatibility smoke because upstreams evolve quickly.

These are bounded implementation refinements, not new user decisions.
