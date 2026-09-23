# M01-T03 independent re-review evidence

- Review owner: Task Board card `M01-T03`
- Review requirement: `RECOMMENDED`
- Reviewer: fresh normal ChatGPT session, independent of the corrected implementation
- Exact review subject: `d016731a276e33f09b9a23df682951e89b21c8dc`
- Verdict: **GREEN**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M01-T03.md`
- `planning/MASTER_PLAN.md#M01 — Reproducible non-root development environment`, especially M01-W3 and the workspace/SSH rules
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-006/007/009/010/012/018 plus applicable invariants
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- accepted dependency result: terminal GREEN M01-T02
- implementation evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-T03.md`
- prior RED evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-T03-review.md`

## Independent checks

- Recovered the immutable subject `d016731a276e33f09b9a23df682951e89b21c8dc` from the manifest-bound Task Board and inspected the exact reviewed source.
- Rechecked GitHub's current official SSH fingerprint/key page on 2026-09-23. The tracked Ed25519, ECDSA and RSA keys/fingerprints match the official values.
- Confirmed the prior F1 correction places the managed `Host github.com` block before preserved user SSH configuration, consistent with OpenSSH first-obtained-value behavior.
- Confirmed the regression fixture seeds a conflicting `Host github.com` stanza with `StrictHostKeyChecking no` and an alternate known-hosts path, then verifies effective `ssh -G github.com` remains strict and points to persistent `/home/pi/.ssh/known_hosts`.
- Confirmed unrelated SSH configuration is preserved and checked independently by the fixture.
- Confirmed explicit `/projects` and `/worktrees` cwd selection, linked-worktree metadata resolution, non-root writes, persistent Git identity, `gh` availability and persistence across recreation remain covered.
- Confirmed operator documentation keeps SSH transport distinct from `gh` API authentication, records ordinary whole-home appdata backup scope, and does not claim live OAuth/GitHub credential or host-restart acceptance.

## Independent runtime verification

Surface: `Tower`, disposable Docker container and unique `/tmp` fixtures only.

Exact command subject:

`d016731a276e33f09b9a23df682951e89b21c8dc`

Image:

`sha256:7ef10cfe06313730505dda1e4ae33227eace1f3bfa5d5a48fe592cb7f5866e6f`

Command:

`bash scripts/verify-git-worktree-foundation.sh pi-unraid:local`

Observed result:

`M01-T03 fixture verification: GREEN`

Exit code: `0`.

No live ChatGPT OAuth/GitHub credential, live project repository or live worktree was used.

## Verdict

**GREEN** — the corrected exact subject satisfies the M01-T03 acceptance surface. The prior strict-host-verification defect is covered by a direct regression fixture and no new review defect was found.
