---
name: project-recovery
description: Recover and enter a managed project from canonical Git/Project Workflow state after the user explicitly selects the project. Use for managed project start, continuation, recovery, or handoff before mutation.
---

# Project recovery

This skill is a bootstrap locator, not a copy of Project Workflow semantics.

1. Confirm that the user explicitly selected the repository/project. Do not derive selection from related conversation, Paseo history, session labels, or memory.
2. Read references/bootstrap.md.
3. Recover the selected repository's current durable project/workstream pointers.
4. Read the canonical workflow router from its current default branch and follow only the module/authority/evidence it requires.
5. Before mutation, verify the current legal branch/worktree and exact durable state. Treat stale session text only as a hint.
6. Continue deterministic authorized transitions until the canonical workflow reaches a real stop.

Do not persist runtime/provider/model/session identity as workflow authority. Do not reproduce router rules in this skill.
