# M01-T03 independent review evidence

- Review owner: Task Board card `M01-T03`
- Review requirement: `RECOMMENDED`
- Reviewer: fresh normal ChatGPT session, independent of implementation
- Exact review subject: `e5355016eb217b6b4260208de523f5e32d20f08e`
- Verdict: **RED**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M01-T03.md`
- `planning/MASTER_PLAN.md#M01 — Reproducible non-root development environment`, especially M01-W3 and section 3.1
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-006/007/009/010/012/018 plus applicable global/security invariants
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- accepted dependency result: terminal GREEN M01-T02
- implementation evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-T03.md`

## Independent checks

- Recovered the exact immutable subject from the manifest-bound Task Board and inspected the reviewed source at that SHA.
- Confirmed the tracked GitHub.com Ed25519/ECDSA/RSA host keys and fingerprints match the current official GitHub Docs SSH fingerprint page.
- Confirmed the fixture covers explicit `/projects` and `/worktrees` cwd selection, linked-worktree metadata resolution, non-root writes, persistent Git identity, `gh` availability and persistence across recreation.
- Confirmed operator documentation keeps SSH transport distinct from `gh` API authentication, preserves ordinary appdata backup scope, and does not claim live OAuth/GitHub credential acceptance.
- Checked the SSH configuration merge behavior against current OpenSSH `ssh_config(5)` semantics: for each directive, the first obtained value is used, so more-specific declarations must precede general/default declarations when they need to win.

## Finding

**F1 — strict GitHub host verification is not enforced when a matching earlier SSH stanza already exists.**

`scripts/configure-operator.sh` removes only its own prior managed block and then appends the new managed `Host github.com` block to the end of `~/.ssh/config`, preserving all earlier user configuration.

Under OpenSSH's first-value-wins semantics, an earlier matching `Host github.com` or `Host *` stanza can already set `StrictHostKeyChecking` and/or `UserKnownHostsFile`. The later managed block then cannot override those values. For example, a pre-existing earlier `Host github.com` with `StrictHostKeyChecking no` leaves effective GitHub host checking disabled after the setup script reports success.

The current fixture starts with an empty SSH config, so its `ssh -G github.com` checks do not cover this preserved-existing-config case. This conflicts with PIB-REQ-009, the M01 section 3.1 rule not to disable checking to make setup pass, and the Task Card's explicit requirement that strict GitHub host checking be configured while unrelated SSH config is preserved.

## Corrective classification

Bounded L1/L2 implementation correction inside accepted authority.

The correction must make the effective GitHub configuration enforce the accepted strict values even when pre-existing matching SSH configuration is present, while continuing to preserve unrelated user SSH configuration. Add a regression fixture with a conflicting earlier matching stanza and verify the final effective `ssh -G github.com` values remain strict and point at the persistent known_hosts file.

No requirement, accepted decision, milestone strategy or product decision needs to change.

## Verdict

**RED** — the exact subject does not yet satisfy the strict GitHub host-verification acceptance boundary. M01-T03 remains non-terminal pending bounded correction and a new independent review subject.
