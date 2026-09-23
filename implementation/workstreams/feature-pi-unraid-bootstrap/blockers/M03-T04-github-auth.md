# M03-T04 blocker — GitHub user authentication

- Card: `M03-T04`
- Date: 2026-09-23
- Status: **RESOLVED**
- Resolution: user completed GitHub authentication inside the production Pi home; live SSH and `gh` write/readback acceptance subsequently passed.

## Resolution readback

- `gh auth status`: GREEN for account `elmakus`, Git protocol SSH.
- `ssh -T git@github.com`: successful authentication under strict host-key verification.
- SSH Git write/readback: temporary branch `m03-t04-live-acceptance` pushed, exact SHA read back, then branch deleted and absence verified.
- `gh api` write/readback: separate temporary Git ref created, exact SHA read back, then ref deleted and absence verified.
- Persistent credential check: a later full Compose recreation preserved both `gh` and SSH authentication in the Pi home.
- Disposable local worktree/branch used for acceptance was removed.

No Tower root GitHub credential was copied into Pi.

Canonical completion evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T04.md`.
