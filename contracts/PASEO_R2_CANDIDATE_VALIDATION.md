# R2 candidate validation — selective technical contract

Owner: M07-T05 (validator producer); M07-T06 consumes the independently reviewed producer semantics in the existing trusted Tower final-gate path.
Authority: requirements/PASEO_UPDATE_DISTRIBUTION.md R2, ADR-PUD-004, approved P4.

This is a narrow product validation/security interface, not a workflow Task Board, approval store, runtime role catalog, universal schema, or new pipeline. It does not authorize credentials, inference, artifact publication or host mutation during M07-T05. All M07-T05 execution evidence is synthetic/local. Real final validation remains M08-T01.

## 1. Bound validation subject

The validator accepts the existing frozen candidate/build/publication handoff and companion declaration, not merely a mutable image tag or a caller's PASS string. Its secret-safe output retains an explicit typed binding to:

- the expected immutable OCI manifest digest and repository;
- the observed local/platform image identity, distinctly typed and actually mapped to that OCI candidate;
- the frozen source/build/handoff provenance;
- the actually staged/applied instruction/provider/policy companion's declared file/mode/content identity;
- applicable policy/launcher and relevant validation configuration identity.

Recompute/read back what the adapter uses. A declaration, version label, same SHA-shaped syntax, copied context, unrelated HOME or caller-provided report cannot prove this binding. Missing, malformed, changed or mismatched input fails closed before inference. A guard extension changes the companion identity and must propagate through the existing prepare/build/package path; never attach modified HOME to an old eligible digest. M07-T07 owns the fresh artifact, not this Card.

## 2. Outcome interface and trust

The producer must expose machine-readable schema/version, execution classification (fixture/rehearsal versus real), typed subject binding, explicit per-required-check outcomes, bounded terminal/pending/unknown classification, and a real-validation-satisfied indicator. Concrete field names may remain local to the existing validator, but their parser/consumer semantics must be explicit and tested.

- Fixture/rehearsal can report mechanical success; it ALWAYS leaves the real-smoke/final-validation gate unsatisfied.
- Real success requires completed successful guarded inference, observed exact effective fixed profile and candidate/daemon/Pi/policy binding, and successful required authenticated non-inference Codex-LB checks.
- Missing credentials or profile, unsupported realization, absent witness, pending/uncertain occurrence, timeout, negative terminal result or mismatch is not real success.
- An execution-mode flag, arbitrary JSON, generic PASS/GREEN, expected launch arguments, a catalog override or an ordinary workflow return cannot manufacture real evidence.
- Preserve a bounded exact owned test-object/readback reference when occurrence is uncertain so a later authorized caller can inspect rather than blindly resend. Do not output raw prompts, response bodies, tokens, private pairing offers or credential-bearing URLs.

This report alone does not grant final eligibility. M07-T06's trusted assembler/writer must verify the complete required gates, current baseline and exact bindings; M08 supplies real observations. No second promotion writer or ledger is introduced here.

## 3. Candidate-local guarded Muse adapter

The preferred adapter invokes the repository-delivered canonical run-llm-test.sh from the disposable candidate's own environment using its own local Paseo daemon/home. Any necessary supported guard extension MUST preserve the fixed meta/muse-spark-1.3-contributor / max profile, gpt-6-astra prohibition and no fallback, while preserving the existing ordinary guarded interface.

Explicitly bind and inspect the daemon endpoint/process, candidate container/image, invoked Pi executable/provider path and policy/launcher. Ambient host, workspace, production daemon/caller, endpoint, environment or PATH settings cannot redirect the smoke. Working directory and requested model/thinking are not provenance proof. Use supported interfaces discovered in the pinned implementation; do not invent flags or an unofficial provider implementation.

A validated native-create-agent-args alternative is permissible only with the same independently proven disposable caller/child execution binding. A child of the active production daemon is never candidate smoke. Workflow workers are not test evidence.

Verify actual resolved/effective profile and the candidate's execution/request observations; metadata and claimed settings alone are insufficient. The pinned Contributor max-null metadata and unmodified max-to-xhigh clamp are known negative facts. A supported configuration fragment, if needed, remains secret-free, frozen and merge-safe and is not capability proof. Unsupported/unobservable effective max must fail closed, not be relabeled or substituted. If the supported realization cannot be established, return the precise Research/Planning boundary rather than a direct provider-call bypass.

Bound dispatch, completion and inspection. A timeout or unknown occurrence must retain an unsatisfied gate and must not cause automatic prompt replay.

## 4. Codex-LB — authenticated NON-INFERENCE only

Replace the existing direct /responses smoke. Required checks use supported authenticated catalog/metadata/auth/health readback, structural validation and deterministic protocol fixtures. Never send a prompt, call /responses, /chat/completions or another inference endpoint, or select another model as a real test. Ordinary/catalog/fixture model IDs remain legitimate data.

Check required HTTP/auth/shape outcomes; missing, unauthorized, malformed or unreachable readback cannot be silently skipped or called PASS. Read response data only as necessary in memory/disposable processing; retain bounded sanitized outcomes, not provider response bodies. Denied/unavailable results are proportionally classified without leaking stderr, headers or tokens.

## 5. Dedicated-secret plumbing

Implement source plumbing/procedure only; do not request or admit real credentials during M07-T05. Only dedicated operator-controlled validation input is permitted. Use supported private local file/read-only mount/OAuth mechanisms and provider-specific restrictions where available. Validate private permissions/ownership and confinement; preserve human participation for account choice/device flow. Provider availability/restrictions are operator inputs, not claims inferred from public metadata.

No ordinary-agent HOME/auth/credential clone or read, credential in CI/image/Git/evidence, token-bearing argv, raw secret --env KEY=value, auth export, debug trace or provider-output echo. Nonsecret configuration environment remains allowed. Only synthetic credentials in disposable fixtures may be supplied now. Failures and subprocess exceptions must remain secret-safe even when dependencies echo supplied data.

## 6. Disposable ownership and cleanup

Candidate code receives no production Docker socket, host administration key, live production HOME or ordinary credentials. Check exact UID:GID, mount sources/destinations/modes, network and actual image identity. Cleanup may remove only objects whose creation/acquisition and current ownership are verified for this validation attempt; a name/digest-shaped suffix alone is not ownership.

Never unconditionally remove a same-name preexisting container/network, another attempt's object, global cache/HOME, broad state root or production object. Handle creation failure, collision, partial setup and interruption without extending authority; re-read uncertain object ownership before cleanup. Preserve unrelated objects and private operator-provisioned inputs.

## 7. Required evidence

Use reachable adapter/CLI tests, not only helper assertions. Positive synthetic controls must observe actual fake-only guarded dispatch and bound outcome propagation. Negatives must reject before disallowed calls and prove their absence while resources still exist.

Cover wrong/missing OCI/local mapping, source/bundle/policy, daemon/endpoint/Pi path, model/effective contribution, fallback/bypass, missing credential/private mode, generic fake PASS, fixture-as-real, auth denial/malformed/unreachable metadata, attempted inference endpoints, timeout/unknown/negative completion, leaked-token output and cleanup collisions/partial failures. Re-run affected guard/instruction-plane/build-binding/runtime contracts and full classified synthetic regression with honest executed/skipped counts and preserved exit status. No real test inference, live provider auth, Docker/Tower operation or CI triggering is permitted for this Card.
