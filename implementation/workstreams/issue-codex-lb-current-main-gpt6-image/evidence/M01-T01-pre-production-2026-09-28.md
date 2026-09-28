# M01-T01 pre-production evidence

Date: 2026-09-28
Repair subject: `repair:codex-lb-current-main-plus-gpt6-128k:v1`

- Exact accepted upstream main: `Soju06/codex-lb@f8ffbac2099a113fba54dfd8d77774f5bca80ffa`.
- Fork main before GPT-6 merge: `elmakus/codex-lb@ccb8d0847529bfe3bf41b5e1dc295230cbe17a4c`; upstream main is an ancestor and fork-only content is the two GHCR publisher workflows.
- Existing GPT-6 contribution head: `elmakus/codex-lb@d64c94338305315d28d1e5899a3aee9c5cb53771` / upstream PR `Soju06/codex-lb#2528`.
- Production before cutover: `codex-lb-clean` on `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1`, image ID `sha256:d4a6d8ddbaff85d9091a18a2b25b1d5df6d60648fc41ed17c5bd2848d6d7b270`, running with restart count 0.
- Unraid template before this scope was already reconciled to `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1`.
- Existing rollback container from the prior scope remains `codex-lb-clean-rollback-gpt6-output-20260928` on official `ghcr.io/soju06/codex-lb:1.25.0-beta.9`.
- This scope will retain the currently running private beta.9 container as the immediate rollback anchor before replacing it.
