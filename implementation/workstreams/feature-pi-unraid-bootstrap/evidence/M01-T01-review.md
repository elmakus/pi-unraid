# M01-T01 independent review evidence

- Review owner: Task Board card `M01-T01`
- Review requirement: `RECOMMENDED`
- Reviewer: fresh normal ChatGPT session, independent of implementation
- Exact review subject: `bd25b5317d9b53cd9d2d17d21adfc75e9c86beb3`
- Verdict: **GREEN**
- Date: 2026-09-23

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M01-T01.md`
- `planning/MASTER_PLAN.md#M01 — Reproducible non-root development environment`, especially M01-W1 and section 3.1
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-001, PIB-REQ-008, PIB-REQ-016 and applicable global invariants
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- stable-seed compatibility boundary from `decisions/PIB_ADR_003_UPDATE_ROLLBACK.md`
- implementation evidence: `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M01-T01.md`

## Independent checks

- Inspected the exact immutable review subject and its repository source rather than relying on implementing-session narrative.
- Confirmed the reviewed image source is repository-owned and uses a digest-pinned Node 24 Bookworm base.
- Confirmed the Pi seed is explicitly pinned to `0.87.1`, installed with the upstream-supported `--ignore-scripts` pattern, and verified by `pi --version` during the image build.
- Confirmed the Dockerfile contains the accepted development-tool inventory and does not copy repository content, credentials or unrelated host state into the image.
- Confirmed `.dockerignore` and source structure do not introduce later Web UI/extension/MCP/subagent/browser scope.
- Confirmed `scripts/verify-base-image.sh` checks the required Node/Pi/Python/Git/SSH/gh/curl/jq/rg/fd/find/archive/build/Git-LFS tool surface and the Pi seed metadata.
- Confirmed implementation evidence records immutable base/image identities, selected Pi seed/package integrity, representative tool versions and resolved Debian package identities, and reports the required disposable-Tower build/readback checks.
- Independently compared the tested source head `1817ce3038cf2edc3ac10d79f6249d49d396e256` with the review subject: `Dockerfile`, `.dockerignore` and `scripts/verify-base-image.sh` have identical blob SHAs at both refs.
- Confirmed T01 does not claim or implement T02/T03/M02 responsibilities such as non-root Compose operation, persistent-home initialization, native TUI/operator setup, latest-stable-on-start/LKG lifecycle or image rollback.

## Findings

No material correctness, scope, security-boundary or evidence defect was found against the M01-T01 contract.

The image remains root-operated at this Card boundary by design; the accepted non-root runtime/UID/GID/persistent-home behavior is explicitly assigned to M01-T02 and therefore is not a T01 review failure.

## Verdict

**GREEN** — the exact subject satisfies the M01-T01 contract and may proceed to deterministic post-review Card finalization.
