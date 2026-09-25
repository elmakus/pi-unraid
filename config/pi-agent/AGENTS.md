# Pi-Unraid global routing

These instructions define the global Pi environment boundary. They are not project workflow state.

## Project binding

- Managed project selection is user-driven. Do not infer or bind a repository/project solely from conversation, session history, Paseo state, or memory.
- After the user explicitly selects a project, load the project-recovery skill before any managed mutation and reconstruct the current canonical Git/Project Workflow state from durable sources.
- Durable repository/Project Workflow state outranks Paseo UI/session/history and other convenience state.
- For direct Main/Pi ad-hoc mutation in this environment, do not write on the integration/main branch; use an appropriate legal branch/worktree.

## Progressive skills

- Use project-recovery for managed project entry, continuation, recovery, or handoff. It is a locator/bootstrap skill; it must not duplicate Project Workflow routing semantics.
- Use unraid-admin for Unraid environment/host-administration context. Its knowledge does not itself authorize a mutation.
- Detailed guidance belongs in skill references so this global file stays compact.

## Authority and secrets

- Project Workflow owns managed workflow legality, durable state, review semantics, branch/write scope, and real user stops.
- Orchestration Runtime owns concrete runtime scheduling and worker/session realization when that product is in scope.
- pi-unraid owns the environment, installed capability delivery, filesystem/workspace substrate, deployment, and host-administration mechanisms.
- Do not create a second Task Board or workflow state store in Pi, Paseo, HOME, session metadata, or extension state.
- Never place raw credentials, tokens, private keys, pairing offers, or provider secrets in Git, instructions, logs, or evidence.
