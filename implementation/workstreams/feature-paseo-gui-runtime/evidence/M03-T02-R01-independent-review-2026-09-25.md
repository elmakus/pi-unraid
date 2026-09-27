# M03-T02 R01 — Independent implementation review

Date: 2026-09-25
Card: `M03-T02`
Attempt: `R01`
Verdict: **RED**

## Reviewed exact subject

- Review subject: `elmakus/pi-unraid@28693747d3c3e6cf87263626fbed437392b38d57:implementation/workstreams/feature-paseo-gui-runtime/results/M03-T02.md@76acc72e0eee4401f09d7f5b48ac3a4d497fc68d`
- Implementation commit named by the result: `ab8096889e8ef5e32626ee995c29166556f06e46`
- Acceptance surface: `implementation/workstreams/feature-paseo-gui-runtime/cards/M03-T02.md`
- Frozen predecessor result: `implementation/workstreams/feature-paseo-gui-runtime/results/M03-T01.md@16e5a14f1f0357b8af40fa23602c6d6c1da24724:1b157d85116b5a9dffab7df7766f62cc8a288f3e`

## Independent checks

- The exact result locator was re-read at commit `28693747d3c3e6cf87263626fbed437392b38d57` and its blob matches the frozen attempt.
- GitHub Actions run `36184714484` is completed/success on exact implementation SHA `ab8096889e8ef5e32626ee995c29166556f06e46`. The workflow revalidates the exact M03-T01 result binding and runs the host-control guard contract suite together with the existing image/build/persistence/instruction-plane smokes.
- The reviewed SSH transport is non-interactive and strict-host-key: BatchMode, disabled password/keyboard-interactive authentication, IdentitiesOnly and a private non-symlink identity file are enforced. GraphQL remains the default readback path, credential/auth/GraphQL application failures do not silently escalate to SSH, and missing SSH configuration no longer breaks a healthy GraphQL primary path.
- The policy enumerates the accepted explicit fallback reasons and contains user-gated entries for host reboot, Docker-engine restart, Unraid OS upgrade, disk format, broad share/appdata deletion and broad network change. Raw SSH command output is reduced to bounded byte-count/digest metadata.
- Credential-backed Tower SSH fallback is correctly not claimed here; approved P2 assigns the real forced bounded SSH fallback plus return-to-GraphQL acceptance to M06-T04.

## Blocking findings

1. **GraphQL mutation execution does not consume the M03-T02 safety classification before side effects.**  
   `config/unraid-host-control/host-safety-policy.json` classifies `graphql_container_start/stop/restart/pause/unpause` as ordinary operations, but `scripts/unraid_graphql_host_control.py` never loads that policy and never calls `operation_rule()` or `evaluate()`. Its `container-action` path performs a pre-readback and then directly executes the GraphQL mutation selected by the independent `ALLOWED_ACTIONS` tuple. Therefore the policy and the actual GraphQL mutator can diverge, and a policy reclassification/denial would not affect execution. This does not satisfy the Card acceptance that host mutation requests are classified before execution through one GraphQL-primary/SSH-fallback safety plane.

2. **The SSH generic mutation path cannot enforce operation-specific classification or rollback applicability.**  
   `scripts/unraid_ssh_fallback.py:gated_exec()` hard-codes every command to `evaluate("ssh_admin_command", ...)`; the specific high-impact policy classes are never selected by that execution path. In addition, whether a rollback anchor is required is controlled by the command-file field `rollback_applicable`. A caller can set that field false and suppress the anchor check even when the real operation is technically rollback-applicable. The external user-authorization gate still makes this conservative with respect to authorization, but it does not meet the Card's mechanical requirement for explicit operation classification and rollback/snapshot anchors where technically applicable.

These are acceptance defects in the current M03-T02 implementation/safety plane, not a request for the deferred live Tower credential exercise.

## Corrective classification

The Task Card contract remains valid and the defect is bounded to the current Card implementation/evidence. Keep `M03-T02` `in_progress` and repair the same Card; do not create a new Card.

Required correction:

1. bind every mutating execution path, including the GraphQL one-container actions, to the shared policy/classification decision before the side effect;
2. make SSH mutation execution bind the concrete operation class to the exact command scope, so specific high-impact classes cannot collapse into a generic class;
3. derive rollback-anchor applicability from the accepted operation policy/classification or otherwise fail closed when applicability is not established; do not allow the command payload alone to opt out;
4. extend contract tests so mutation is rejected when policy classification/permission changes, high-impact commands cannot execute under an ordinary/generic classification, and rollback-anchor requirements are mechanically enforced from the operation class;
5. rerun the exact predecessor binding plus the complete existing image/build/persistence/instruction-plane smoke on the repaired implementation SHA and freeze a new result/review attempt.

**RED** — the exact reviewed subject is not eligible for Card finalization.
