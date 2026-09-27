# M06-T04 R01 independent review — GREEN

- Task ID: PASEO-P4-M06-T04-R01
- Exact subject: `elmakus/pi-unraid@9ba5ea11a2510f265a962b7870c8a3a09cb1cf4c:implementation/workstreams/feature-paseo-gui-runtime/results/M06-T04.md`, blob `fc2bb31f794480e3fc954d28a47ac09086f2734e`.
- Implementation subject: `6d9e13018eaaf3da331d93d9a6d91bdf7f758464`.
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M06-T04.md` (review required).
- Independence: this review context did not author or repair the exact implementation, result, or worker evidence.
- Verdict: **GREEN**. No blocking acceptance gap was found. The permitted claim is M06 automatic technical GREEN only; Human Acceptance remains outstanding and no full GREEN is implied.

## Exact identity and authority reconciliation

- Remote branch HEAD was revalidated at `17c55d24a7d35ad2fc17167f18d31f33192d12b8` before the review write; R01 remains bound to the unchanged result blob above.
- Every exact dependency binding named by the Card was re-read at its pinned commit and matched byte-for-byte:
  - M06-T03 `a140f95fef4cd99a433d3b7b08f3e482e4c4dbc2`
  - M03-T01 `1b157d85116b5a9dffab7df7766f62cc8a288f3e`
  - M03-T02 `a5c8a0c3a84b5c7f6da3d147896ee60995860800`
  - M03-T03 `db16908476e2f081669c65a4ff8e8e7062579f71`
  - M05-T03 `b526cf4717ea6d353fc6d23f082b1c726e7f55ed`.
- Approved requirements plus ADR-PGR-002/003/004 and frozen P4 were re-read. P4 explicitly moves credential-backed GraphQL readback/live mutation to staged HA and permits M07-T02 to own a forced bounded SSH-fallback confirmation when M06-T04 leaves a credentialed witness gap.
- The worker evidence files are present at the frozen result lineage and remain unchanged at current HEAD: markdown blob `7ca8e070a993e5eb6178dd705edc96c2f0c2c7e0`, JSON blob `90fe04efe67c6e62b6fe37dfb75496a84df33330`.

## Independent exact-SHA verification

- Tower has an isolated worktree at exact implementation SHA `6d9e13018eaaf3da331d93d9a6d91bdf7f758464`; tracked status was clean.
- Independent full-suite rerun on that exact SHA executed all 18 test modules: **378 tests in 4.182 s, OK, exit 0**.
- Code review confirmed:
  - GraphQL mutation allowlist is exactly start/stop/restart/pause/unpause;
  - each mutation performs pre-readback and must pass the ordinary GraphQL safety classification before side effect;
  - primary routing falls back automatically only for transport failure or HTTP 502/503/504, while credential/auth/application/protocol failures fail closed;
  - explicit SSH fallback is bounded to accepted reasons and is non-sticky, so the next normal invocation returns to GraphQL;
  - SSH uses BatchMode, IdentitiesOnly, strict host-key checking, and disables password and keyboard-interactive authentication;
  - gated SSH mutations require exact-scope pre-readback, private external-user authorization, and rollback anchor evidence;
  - unknown operations deny by default;
  - doctor is read-only, secret-safe, reports structured GREEN/WARN/RED, and does not invoke mutation paths.

## Independent live read-only Tower readback

Fresh review-time checks, with no credential materialization and no mutation, confirmed:
- Unraid `7.2.4`;
- native `unraid-api` `4.37.4+ad268301`, status `online`;
- unauthenticated POST to `/graphql` returns HTTP 200 with GraphQL error code `UNAUTHENTICATED` and `data:null`;
- SSH listens on the Tower LAN address only and returns an `SSH-2.0` banner.

Repository configuration independently matches the accepted least-practical host-control surface:
- no broad role;
- permissions exactly `INFO:READ_ANY`, `DOCKER:READ_ANY`, `DOCKER:UPDATE_ANY`;
- GraphQL remains primary;
- accepted fallback reasons are `api_gap`, `api_outage`, `os_plugin_filesystem_recovery`, and `forced_test`;
- high-impact reboot/engine-restart/OS-upgrade/format/broad-delete/broad-network classes remain externally user-gated.

## Boundary and residual-risk assessment

- No authenticated GraphQL call, live GraphQL/SSH mutation, high-impact action, production Paseo mutation, or secret materialization was performed during the review.
- No already-approved Tower SSH identity exists in the M06 automatic slice, so the credentialed forced-fallback witness cannot be performed without violating the Card's no-new-secret/no-user-presence boundary.
- This is not a blocking M06-T04 gap because the Card and P4 explicitly require fail-closed deferral of that credential-only witness to M07-T02.
- The remaining staged HA obligations are authenticated least-privilege GraphQL readback, permission-sufficiency proof, one safe reversible mutation/restoration, credentialed forced SSH-fallback confirmation, and manual/phone acceptance.
