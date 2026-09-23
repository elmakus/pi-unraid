# M01-T02 independent review evidence

- Review owner: Task Board card `M01-T02`
- Review requirement: `RECOMMENDED`
- Reviewer: fresh normal ChatGPT session, independent of implementation
- Exact review subject: `412c9ce143f883f13b885aa93502651184809a10`
- Verdict: **GREEN**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M01-T02.md`
- `planning/MASTER_PLAN.md#M01 — Reproducible non-root development environment`, especially M01-W2 and the M01 verification/recovery obligations
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-001/002/003/006/007/011/013/017/018 and applicable global/data-integrity invariants
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- relevant update/logging boundary from `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- accepted dependency result: terminal GREEN M01-T01
- implementation evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-T02.md`

## Independent checks

- Recovered the exact immutable review subject from the manifest-bound Task Board and inspected the reviewed repository source rather than relying on implementing-session narrative.
- Confirmed review provenance: the evidence records tested source head `c3409913317a29db00e81c1b1064e8d9856fbdf5`; Git comparison to the review subject shows exactly one later commit and only `M01-T02.md` evidence was added. `Dockerfile`, `compose.yaml`, `scripts/container-entrypoint.sh`, and `scripts/verify-compose-foundation.sh` are therefore unchanged from the tested source.
- Confirmed `compose.yaml` declares only the accepted persistent home/projects/worktrees binds, uses `create_host_path: false`, `restart: unless-stopped`, `TZ=Europe/Zurich`, and bounded `json-file` logging at 10 MiB x 3.
- Confirmed the image includes the `pi` account, `gosu`, and sudo, while the entrypoint uses root only for bounded account-ID/mount validation and then replaces PID1 with `gosu pi "$@"` for normal operation.
- Confirmed UID changes temporarily move the passwd home away from `/home/pi` before `usermod --uid`, avoiding the usermod home-ownership rewrite path against the persistent bind.
- Confirmed initialization chowns only an empty `/home/pi` mount root and never recursively chowns existing home content, `/projects`, or `/worktrees`; non-empty incompatible home state fails before service start with an actionable init error.
- Confirmed the fixture verification covers non-root PID1/service identity, working passwordless sudo, persistent marker preservation across restart, retained marker ownership, only the three expected runtime mount targets, non-privileged mode, bounded Docker log settings, absence of `sshd`, and safe changed-identity failure without marker takeover.
- Confirmed the implementation evidence records disposable-Tower execution and no live `/mnt/user/appdata/pi-unraid/home`, projects, or worktrees mutation.
- Confirmed the T01 regression check remained GREEN against the T02 image and the reviewed change does not introduce later OAuth/TUI/operator/update/fallback/rollback responsibilities outside this Card.
- Considered numeric UID/GID collisions with pre-existing image accounts/groups: the entrypoint fails closed rather than repurposing an unrelated container identity. This is a bounded configuration failure, not silent ownership takeover; exact live target IDs remain an M03 JIT/readiness fact.

## Findings

No material correctness, security-boundary, persistence, scope, or evidence defect was found against the M01-T02 contract.

The fixture checks do not claim final live Unraid home ownership, OAuth persistence, repository/worktree write acceptance, or host-restart acceptance; those remain downstream milestones/cards and are not required for this Card verdict.

## Verdict

**GREEN** — the exact subject satisfies the M01-T02 contract and may proceed to deterministic post-review Card finalization.
