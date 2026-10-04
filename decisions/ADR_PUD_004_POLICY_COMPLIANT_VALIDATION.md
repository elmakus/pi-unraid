# Decision — Policy-compliant real Muse validation and non-inference Codex-LB checks

- Decision ID: `ADR-PUD-004`
- Date: `2026-10-04`
- Status: `accepted`
- Definition subject: `paseo-update-distribution@11`
- Requirements: `requirements/PASEO_UPDATE_DISTRIBUTION.md`, R2
- Supersedes for this scope: real Codex-LB inference and configurable/low-cost smoke-model provisions in earlier PUD/PGR validation authority and ADR-PUD-003 R1; no other production/rollback decision is changed

## Decision

Final disposable Tower validation comprises:

1. the production-shaped runtime/invariant and exact direct `A -> C -> A` state-transition checks;
2. one bounded real smoke through the exact immutable candidate's Paseo/Pi/provider path using the mandatory guarded LLM-test launcher and its fixed `meta/muse-spark-1.3-contributor` / `max` profile;
3. authenticated Codex-LB catalog/metadata/auth/health integration readback without inference, plus deterministic protocol fixtures where needed.

No alternative real-test model, contribution level, fallback or direct inference request may substitute for the mandated launcher/profile. Codex-LB is not used to execute a second inference. The policy-approved CLI and validated caller-scoped native invocation shapes are mechanisms only: effective profile and exact disposable candidate runtime binding must independently be proven before their result is consumed as final candidate acceptance.

Only dedicated operator-controlled validation credentials may enter the disposable validator/runtime. Ordinary agent credentials are not supplied to the update pipeline. GitHub CI, candidate image content, repository, logs and evidence remain credential-free. Secret provisioning and supported provider-side restrictions remain operator responsibilities; no new credential value is authorized for copying from the existing agent environment.

The candidate must reproducibly carry/enforce the applicable mandatory policy and guarded launcher rather than restoring older permissive test behavior. Missing profile, policy, launcher, credential, candidate binding or required non-inference readback leaves acceptance RED/BLOCKED. Fixtures, launcher metadata, an unrelated Muse test or the previous M07 rehearsal cannot satisfy the new real-smoke gate.

## Preserved production boundaries

The order remains: all exact-candidate final validation GREEN, then exact transaction-guard arm/readback, then serialized production accepted-channel exposure, then the user-chosen Unraid cutover. No scope approval, candidate discovery, build success or accepted tag movement restarts production.

The exact predecessor/configuration/rollback anchor, current plus two previous known-good identities, immediate RED rollback, and cessation of automatic rollback after immediate GREEN remain mandatory. Any changed candidate requires its own immutable build/publish identity and affected exact-gate evidence; historical GREEN subjects are not rewritten.

## Consequences

This is a material Definition/acceptance amendment. The original P3 plan/review remains historical and does not cover this changed validation contract. A new Planning cycle with exact A/B/C gates must establish requirement coverage and selective revalidation before implementation/Card refinement resumes.

The fixed profile is an environment/test invariant only. It does not select Project Workflow roles, change the interactive Main model or introduce runtime/provider/session identity into workflow state. This decision neither implements the new smoke mechanism nor claims credential availability, real inference, final validation or production completion.
