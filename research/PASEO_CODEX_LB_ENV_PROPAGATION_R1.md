# Research — Paseo Codex-LB runtime environment propagation

Status: `complete`
Origin role: `intake`
Origin subject: `repair:paseo-codex-lb-runtime-env-and-llm-test-policy:v1`

## Finding

The dynamic Codex-LB catalog implementation is healthy. The production defect is at the Paseo daemon process boundary: the dedicated Codex-LB secret is mounted as `/run/secrets/pi-unraid-codex-lb`, but `CODEX_LB_API_KEY` is not exported into the Paseo daemon environment. Pi RPC processes launched by Paseo therefore cannot resolve the provider credential.

The minimal durable repair is to restore a repository-managed secret-to-environment bridge at container startup, before the upstream Paseo entrypoint starts the daemon. The bridge should parse only the dedicated secret file, export `CODEX_LB_API_KEY` in-process, never echo the value, and then `exec` the untouched upstream entrypoint. Canonical Compose must also declare the dedicated secret mount and host-gateway dependency so a normal repository deployment reproduces the accepted runtime boundary without a hand-written production override.

The user's LLM-test policy should be durable and machine-checkable: any test that intentionally performs a real LLM inference must use model `gpt-6-luna` with thinking/reasoning effort `low`; `gpt-6-astra` is forbidden for real LLM test execution. This does not prohibit mentioning Astra as fixture/catalog data or selecting Astra interactively outside test execution.

## Direct project/runtime evidence

- Production container `pi-unraid-paseo-1` has a read-only bind from `/mnt/user/appdata/pi-unraid/secrets/codex-lb.env` to `/run/secrets/pi-unraid-codex-lb`.
- The same container has `CODEX_LB_API_KEY` absent from its configured/runtime environment inherited by the Paseo daemon.
- A persisted Paseo agent record reports: `Failed to resolve API key for provider "codex-lb" from environment variable: CODEX_LB_API_KEY`.
- Direct Pi RPC with the same mounted secret explicitly sourced returns all nine current Codex-LB models, proving the catalog/provider implementation itself is functional.
- `/home/paseo/.pi/agent/models-store.json` contains the same nine-model last-known-good catalog.
- Production has `host.docker.internal:host-gateway`; the canonical current `compose.yaml` does not, so the checked-in deployment source is not sufficient to reproduce the live provider boundary.

## Official/upstream evidence

Installed official Paseo 0.9.2 server code uses the Pi CLI runtime as follows:

- `PiProvider.fetchCatalog()` starts a Pi runtime session and calls `get_available_models`.
- `PiCliRuntime.startSession()` passes `buildPiLaunch(...).env` to the spawned Pi process.
- `buildPiLaunch()` leaves `env` undefined unless an explicit runtime/session override exists; ordinary Node child-process behavior therefore inherits the Paseo daemon process environment.
- The upstream Docker entrypoint exports the standard Paseo/HOME/XDG environment and then execs the daemon; it does not know about the project-specific Codex-LB secret.

Therefore a project-owned wrapper around the pinned upstream entrypoint is sufficient to make both catalog-refresh and normal Pi agent child processes inherit the credential without modifying upstream Paseo internals.

## Repository history / prior art

Before the Paseo migration, `compose.yaml` declared a file-backed `codex_lb_client` secret sourced from `PI_CODEX_LB_SECRET_SOURCE` and mounted it at `/run/secrets/pi-unraid-codex-lb`. Commit `384a14675e3fb034c8c86c88219e53196c721ed1` replaced the legacy Pi service with Paseo and intentionally removed the old Codex-LB Compose surface. Later production acceptance reintroduced the secret only through an M07 production override, which explains why the file exists live while the checked-in Compose and daemon environment remain incomplete.

The existing secret reader in `scripts/pi-unraid-provider` already establishes the accepted parsing rules: exactly one non-comment credential record, optional `CODEX_LB_API_KEY=` prefix, no whitespace/NUL, no secret logging. The new entrypoint bridge should reuse equivalent fail-closed parsing semantics rather than inventing a weaker format.

## LLM test-policy placement

No current repository-wide durable rule fixes real LLM test execution to one model/effort. Historical evidence includes a prior real model call using another model, so an explicit new rule is necessary. A robust durable shape is:

1. dedicated human-readable policy document with exact scope/exceptions;
2. concise mandatory rule in `config/pi-agent/AGENTS.md` so Pi sessions see it globally;
3. machine-readable policy config consumed by a test launcher/validator;
4. contract tests that assert exact `gpt-6-luna` + `low` and reject `gpt-6-astra` for real LLM test execution.

## Source-class accounting

- Official/upstream: checked, primary — pinned Paseo 0.9.2 runtime/entrypoint implementation inspected directly.
- Project/runtime: checked, direct — production mounts/env/session error, direct Pi RPC and repository history inspected.
- Tracker/discussion: not relevant — the failure is fully reproduced and localized by exact runtime/code evidence; no unresolved upstream behavioral ambiguity requires issue-tracker interpretation.
- Practitioner/community: not relevant — no workaround selection or contested behavior depends on community evidence.

## Limitations

The repair is not yet built or deployed at this research stage. Candidate-image updates can change the upstream entrypoint file, so build/contract tests must verify the expected upstream entrypoint exists before installing the wrapper. Production activation must verify that the secret remains absent from Docker configured environment/committed evidence while Pi children can authenticate and the Paseo picker exposes the live catalog.

## Conflicts

None. Direct runtime evidence, repository history and pinned upstream implementation agree on the failure mechanism and repair seam.
