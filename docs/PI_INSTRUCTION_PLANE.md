# Pi native instruction/config plane

M02-T03 manages only the non-secret global Pi instruction surface for the frozen candidate. It does not install SpecPi, pi-mcp-adapter, provider credentials, or a second workflow state store.

## Exact Pi 0.87.1 native surface

Verified against earendil-works/pi at v0.87.1:

- packages/coding-agent/docs/configuration.md at blob 40fdb0ef78a60b0bc7eb566f0f57aa215ac3c6be: the user agent directory defaults to ~/.pi/agent; global AGENTS.md, skills/, extensions/, settings.json, and auth.json are native surfaces there.
- packages/coding-agent/docs/skills.md at blob 19d2bf28910ce49caaaf4dde86d1e96330ca7b31: Pi advertises skill metadata at startup and loads the full SKILL.md content only when needed.
- packages/coding-agent/src/core/resource-loader.ts at blob 6babd017839f87cad8ca16ff1fa3c163aae7bde6: the exact code loads the global context file from agentDir and loads skills through the native resource loader.

The accepted runtime keeps HOME=/home/paseo, so the native global agent directory is /home/paseo/.pi/agent.

This repository manages only:

- AGENTS.md
- skills/project-recovery/**
- skills/unraid-admin/**

It deliberately does not generate or overwrite auth.json, provider credentials, or user settings.json. Actual SpecPi/pi-mcp-adapter/global capability delivery remains M04-T03 scope.

## Apply, read back and rollback

Use the exact frozen child image and a HOME host path already prepared for the runtime UID/GID:

    scripts/configure-pi-instruction-plane.sh apply IMAGE HOME_HOST 99 100
    scripts/configure-pi-instruction-plane.sh status IMAGE HOME_HOST 99 100
    scripts/configure-pi-instruction-plane.sh rollback IMAGE HOME_HOST 99 100

apply computes a content digest, snapshots only the managed target files before a real change, writes the version-controlled source atomically, and becomes a no-op when the installed bytes already match. rollback restores the immediately previous managed state. Snapshot metadata is private under /home/paseo/.pi-unraid/instruction-plane and contains paths/digests only, not credentials.

## Authority behavior

The compact global AGENTS.md requires explicit user-driven project selection. Once a project is selected, the project-recovery skill is a locator-only bootstrap: it reads the selected repository's durable project pointer, then the current-default-branch workflow/ROUTER.md from elmakus/project_workflow_v2, and progressively follows canonical pointers. It does not copy router semantics.

The unraid-admin skill carries accepted host-safety knowledge but explicitly does not claim that M03 host-control transports are already available.

## Disposable acceptance

scripts/verify-pi-instruction-plane.sh uses only a temporary HOME. It proves:

- adoption snapshots and rollback restore a pre-existing global instruction file;
- the managed source is re-applied with numeric runtime ownership;
- a second apply is byte-stable/no-op;
- two fresh Pi v0.87.1 RPC processes in separate disposable containers start successfully against the same persisted HOME;
- the managed instruction tree remains byte-identical across that recreation boundary;
- cleanup removes the temporary HOME and leaves production/Tower untouched.
