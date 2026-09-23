# M03-T02 independent review evidence

- Review owner: Task Board card `M03-T02`
- Review requirement: `RECOMMENDED`
- Reviewer: fresh normal ChatGPT session, independent of implementation subject
- Exact review subject: `4267f707ae121d54625e537fb7e8e3820c654997`
- Verdict: **GREEN**
- Date: 2026-09-23
- Secret handling: no API key, OAuth token, account identifier or encryption-key value was read into this evidence.

## Authority reviewed

- `implementation/workstreams/feature-pi-unraid-bootstrap/cards/M03-T02.md`
- `planning/MASTER_PLAN.md#M03 — Codex-LB-integrated on-Unraid acceptance and recoverable handoff`, especially M03-W1
- `requirements/PI_UNRAID_BOOTSTRAP.md`: PIB-REQ-004, PIB-REQ-019, PIB-REQ-022, PIB-REQ-023, PIB-REQ-024
- `decisions/PIB_ADR_001_PHASE1_SCOPE.md`
- `decisions/PIB_ADR_002_RUNTIME_LAYOUT.md`
- `decisions/PIB_ADR_005_CODEX_LB_ACCESS_LAYER.md`
- `decisions/PIB_ADR_006_CHATGPT_STRATEGIC_PLANNER_OVERRIDE.md`
- `research/PI_UNRAID_CODEX_LB_INTEGRATION_R1.md`
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-R2-prep-readiness.md`
- `implementation/workstreams/feature-pi-unraid-bootstrap/evidence/M03-T02.md`
- completed M01/M02 checkpoints

## Exact-subject and upstream identity review

The immutable implementation subject was reviewed rather than the moving workstream HEAD.

Independent upstream readback confirmed:
- Git tag `v1.25.0-beta.9` is an annotated tag whose target commit is `69f128afcbc616d9f8e924ca6583f7031d75cf82`;
- the published GitHub release is `Release v1.25.0-beta.9` and documents Docker image `ghcr.io/Soju06/codex-lb:1.25.0-beta.9`;
- Tower runs `ghcr.io/soju06/codex-lb:1.25.0-beta.9`;
- running image ID is `sha256:867eeb726bf3d8141ed18ac35a827d3a3d0f49e6a6cca285567adf1f98102f0f`;
- local repository digest is `sha256:093344377e618acab906a36a4ed23d23e4b2f0fd2882e38df545b170d4278832`.

This matches the implementation evidence and the user-selected exact upstream dependency.

## Independent Tower readback

Fresh read-only verification confirmed:
- `codex-lb-clean` is running the exact versioned upstream image;
- restart policy is `unless-stopped`;
- the service remains on network `ibraproxy`;
- persistent bind remains `/mnt/user/appdata/codex-lb-clean -> /var/lib/codex-lb`, read/write;
- `GET /health` returns HTTP 200;
- unauthenticated `GET /v1/models` returns HTTP 401;
- active ChatGPT/Codex accounts: 3;
- routing strategy: `capacity_weighted`;
- sticky threads: enabled;
- proxy API-key authentication: enabled.

The accepted routing limitation remains explicit in canonical research/decision authority: sticky routing preserves locality where possible, but account-owned continuation state is not guaranteed to migrate transparently to another account; a fresh conversation may route through another eligible account.

## Dedicated Pi credential and route

Secret-safe independent readback confirmed:
- protected file `/mnt/user/appdata/codex-lb-clean/client-secrets/pi-unraid.env` exists with mode `600`;
- it contains exactly one non-empty `CODEX_LB_API_KEY=...` entry;
- Codex-LB has exactly one active key row named `pi-unraid-phase1`;
- authenticated host `GET /v1/models` returns HTTP 200 and a list-shaped model payload;
- a disposable ordinary Docker `bridge` container using only `host-gateway` reaches `/health` with HTTP 200;
- the same disposable route reaches authenticated `/v1/models` with HTTP 200.

The credential value was not printed, copied into Git, embedded in an image or recorded in evidence. The route does not require Pi to join Codex-LB's network or mount its appdata.

## Rollback and workstation independence

Independent readback confirmed:
- the prior fork-derived rollback container remains stopped and available;
- pre-upstream backup directories remain present under the existing Codex-LB backup area;
- `chatgpt-ce-workstation` remains healthy;
- workstation container ID remains `ba960b239bd29c1908e314ea64b9d44c8883f238feaa4367e6d889227713d5a7`;
- workstation image ID remains `sha256:9ede8f1f522a710707acac32d01fd8c4d7671b91912791e299d1c635d964b893`.

No direct-Pi OAuth path, pooled OAuth-token transfer, workstation dependency or Pi production deployment was introduced by this Card.

## Verdict

**GREEN.** All M03-T02 acceptance items are supported by the exact implementation subject plus independent upstream/runtime readback. The Codex-LB dependency is ready for the Pi-side integration Card, while final real Pi model interaction remains correctly deferred to later M03 acceptance.
