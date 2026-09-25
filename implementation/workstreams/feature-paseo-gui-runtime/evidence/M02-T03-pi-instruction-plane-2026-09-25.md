# M02-T03 — Pi-native instruction/config plane evidence

Date: 2026-09-25
Card: M02-T03
Implementation commit: 3fd15db893eaa89a522d21beba355368973acf02
Frozen candidate: sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69

## Exact predecessor

- M02-T02 result: implementation/workstreams/feature-paseo-gui-runtime/results/M02-T02.md@d70e95292c561ad7ca5491027a221a7c22177574:7b8574df581ace7e62125b8dc79fb48c1e491e7d
- GitHub Actions exact predecessor-binding step: GREEN in run 36156374624.

## Exact Pi 0.87.1 native interface readback

Frozen candidate resolves Pi 0.87.1 from earendil-works/pi tag v0.87.1, source commit f07218c4d4bbc12bef056a7058c3dd49dfe41abe.

Exact upstream v0.87.1 evidence used by the implementation:

- packages/coding-agent/docs/configuration.md@40fdb0ef78a60b0bc7eb566f0f57aa215ac3c6be — default agent directory ~/.pi/agent and native global AGENTS.md, skills/, extensions/, settings.json and auth.json surfaces.
- packages/coding-agent/docs/skills.md@19d2bf28910ce49caaaf4dde86d1e96330ca7b31 — skill metadata is advertised at startup while full SKILL.md instructions load on demand.
- packages/coding-agent/src/core/resource-loader.ts@6babd017839f87cad8ca16ff1fa3c163aae7bde6 — exact resource loader reads the global context file from agentDir and loads skills through the native resource path.

With the accepted HOME=/home/paseo contract, the native global agent directory is /home/paseo/.pi/agent.

## Exact implementation surface

- config/pi-agent/AGENTS.md@9e2f3ca220d405daaa1ab0fd30825568958d22b7
- config/pi-agent/skills/project-recovery/SKILL.md@2777bcc3c221ea7ef913feba4862a47884b7cdba
- config/pi-agent/skills/project-recovery/references/bootstrap.md@cfb87ca4d33485a4808ec2ec80ac8677d84cc052
- config/pi-agent/skills/unraid-admin/SKILL.md@32eda3ad6111b544d93bc98e139a611028acfe64
- config/pi-agent/skills/unraid-admin/references/safety-boundary.md@09f51d2313ff47f8ad09bfd9503f7e7bd607f8c1
- scripts/pi_instruction_plane.py@25a175724fb51eca73899d1e5a27532f13e4a468
- scripts/configure-pi-instruction-plane.sh@a2b571178989e901362eda557bfa258a5d018cdc
- scripts/verify-pi-instruction-plane.sh@5cefce47871be697ed11c0ddaf6b5ccd0be3e3c7
- tests/test_pi_instruction_plane_contract.py@5db6e8b243a012a16532d8c381cfaf5cda454a1d
- docs/PI_INSTRUCTION_PLANE.md@d2833697f16b454c4d8bfde3c019c081aeab7061
- .github/workflows/paseo-child-image.yml@63d11999b5dd3f7fac23c3e9d436d3f1c4ecac80

The managed source contains only AGENTS.md plus project-recovery and unraid-admin skills/references. The installer does not generate or overwrite auth.json or settings.json and does not install SpecPi/pi-mcp-adapter; their capability delivery remains M04-T03 scope.

## Project/authority boundary

The compact global AGENTS entrypoint requires explicit user-driven project selection. The project-recovery skill is locator-only: after explicit selection it reads the selected repository durable project pointer and the current-default-branch workflow/ROUTER.md from elmakus/project_workflow_v2, then progressively follows canonical pointers. It does not copy Task Board records or router semantics.

The unraid-admin skill carries bounded accepted host-safety knowledge but explicitly does not claim that M03 GraphQL/SSH host-control transports are already delivered. Pi/Paseo/HOME/session state is not introduced as a workflow authority.

## Reproducibility, snapshot and rollback

The repository-owned installer uses apply/status/rollback. It computes a content digest, manages only the declared native agent files, snapshots the immediately previous managed targets inside the sensitive persistent HOME before a real change, writes atomically, rejects symlink targets, and is a no-op when installed bytes match. Unknown auth/settings/provider files are outside the managed set.

## Exact CI/readback

GitHub Actions run 36156374624 on exact implementation SHA 3fd15db893eaa89a522d21beba355368973acf02 completed SUCCESS. Job 108141789807 completed all steps GREEN:

- exact predecessor bindings;
- candidate/image/runtime and M02-T03 contract tests;
- frozen Paseo child-image build;
- disposable image/provenance smoke;
- disposable persistence/ownership smoke;
- disposable Pi instruction-plane smoke;
- immutable foundation metadata readback.

Built image identity in that run: sha256:bad304bf314db6d8ea86b8acde5b94beae46fb6a84ebb4d66cee4fa0f8e93ce7.

Instruction-plane smoke emitted:

    {"card":"M02-T03","agent_dir":"/home/paseo/.pi/agent","global_agents":true,"progressive_skills":2,"snapshot_rollback":true,"fresh_rpc_first":true,"fresh_rpc_recreated":true,"byte_stable_after_recreate":true,"runtime_uid":99,"runtime_gid":100,"result":"GREEN"}

The smoke first proves adoption rollback restores a pre-existing AGENTS file, reapplies the managed source, verifies numeric ownership and mode, starts two fresh Pi RPC processes in separate disposable containers against the same persisted HOME, proves the managed tree is byte-stable after recreation, verifies a repeat apply is a no-op and status is in-sync, then cleans the temporary HOME.

No Tower/production path, real provider credential, real device pairing, SpecPi/MCP delivery, or host-control transport was mutated.
