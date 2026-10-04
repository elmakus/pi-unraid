# M07-T05 — Main contribution validation and bounded correction

Date: 2026-10-04
Owner: common Execution. This is return classification/correction input, NOT an independent Review verdict or a second workflow state store.

## First contribution — incomplete reachable machinery

Incoming implementation: elmakus/pi-unraid@9abd0fcbb3e1ba4a7f3cf50d3b76d734d4aa19cc.
Incoming report: elmakus/pi-unraid@5942df3ec5ac73817f94a000ab86affc83fffbf6:implementation/workstreams/feature-paseo-update-distribution/evidence/M07-T05-validator-implementation-2026-10-04.md@12e7f82056d236d043aa7ba834e5393037c6c28c.

Main refreshed clean legal feature Git, unchanged main@e9476b4987290767a195a9de2ecd655de5f09605, unchanged default-branch workflow d3ab917f02e4de91b7dbb17915c2287c2387333e, PROJECT/router/Execution, stable Card and selective technical contract. Exactly six product/test/doc paths plus one report were contributed. No forbidden Card/contract/authority/state/history writes occurred. The separate main worktree is clean. Board remains 119, M07-T05 in_progress, 22 prior DONE Cards unchanged, M08-T01 planned; no M07-T05 result or attempt exists. Canonical route remains execution/M07-T05.

Classification: contract remains valid, but this contribution is incomplete/incorrect. Keep the SAME Card in_progress and correct it. Do not freeze a result/Review, mark DONE, materialize M07-T06 or claim real readiness. This is not an independent RED or a real user stop. Preserve contribution/report bytes in Git history.

### Evidence actually obtained by Main

Main classified and read the touched tests before execution. PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_paseo_tower_validator tests.test_m07_t05_validator_adapter executed 41 tests, exit 0, OK. They use fake-only guard executables, mocked Docker and injected HTTP; no real inference/auth/credential admission/HOME/Tower/image/CI action occurred. The reported 72 affected/594 full/node counts remain worker-observed, not Main's rerun or acceptance.

Main then executed seven additional probes through the genuine validator/guard helper with all Docker/Paseo subprocess boundaries fake, only disposable synthetic credentials and preserved direct exit status (probe program exit 0 because it reproduced the defects). Observed:

| Probe | Actual result at this subject | Required correction |
|---|---|---|
| real mode with required binding/credential/profile omitted | overall PASS; companion/policy/Codex/profile SKIP; zero exec; real flag false | classify missing required inputs as unsatisfied BLOCKED/FAIL, not successful complete validation |
| caller-supplied max plus foreign daemon home/endpoint/version and foreign Pi path/version | daemon_binding PASS, pi_binding PASS, profile PASS, overall PASS; zero exec | obtain/verify actual candidate observations; never trust caller labels |
| actual inspected container Image differs from pulled expected local image ID | overall PASS | inspect and compare actual running container/image mapping |
| RepoDigests mapping absent | image_mapping SKIP and overall PASS | required typed mapping fails closed |
| preexisting foreign container with only Codex-secret mount on matching network | docker rm -f issued BEFORE this attempt's docker run | immutable acquisition/current-ownership proof; preserve ALL unowned collisions |
| subprocess echoes an unlabelled opaque synthetic token | token retained in ValidationError | avoid arbitrary tails/values, not only regex-labelled token redaction |
| guard helper's policy source absent | fabricated fixed policy; exit 0 and fake dispatch observed | missing exact delivered policy fails closed; no invented substitute |

No real external Docker/Paseo/provider call occurred in these seven probes. Synthetic token values and raw call/output blobs are not retained in this evidence.

### A. Implement and reach the actual future-authorized candidate Muse path

Locations: scripts/paseo_candidate_muse_adapter.py:182-387; scripts/paseo_tower_validator.py:468-505; CLI at 553 onward; product doc's supported-realization/limits sections.

run_guard_dispatch is a temporary-root test helper; it fabricates a missing policy, has no actual candidate/home/daemon selector or lifecycle witness, accepts an arbitrary bindir/extra PATH and returns raw stdout/stderr. Neither it nor validate_candidate_home/validate_daemon_binding/validate_pi_binding is called by the validator. The validator only accepts arbitrary dictionaries and stamps daemon/Pi PASS according to a claimed thinking string; even these dictionaries cannot be supplied through its CLI. real_validation_satisfied is unconditionally false in every product path. There is no real future-authorized dispatch/completion/observation path to exercise under fakes.

No real inference may be RUN in M07-T05, but its supported, dormant-until-authorized implementation MUST exist NOW. M08-T01 owns obtaining actual real observations, not writing the missing adapter after the fresh artifact. Integrate the actual guarded candidate-local path and supported scoped inspection, precise effective execution/request observations, bounded dispatch/completion and exact test-object readback. Exercise the SAME production path with only external boundaries faked. Fixture/rehearsal remains explicitly unsatisfied; success cannot come from caller-provided max, version labels, expected argv or ordinary workflow return. Timeouts/uncertain occurrence must preserve usable owned object references and prohibit blind replay.

Pinned Contributor max-null/max-to-xhigh facts remain negatives, not a proved general impossibility of supported observation or implementation. Main's non-inference source readback found before_provider_request/after_provider_response declarations in installed official pi-coding-agent@0.87.1 and onPayload-related sdk/extension-runner callsites; pi-ai is also 0.87.1. This is a SOURCE LEAD ONLY, not proof of final on-wire max or a directive to invent an observer. Inspect the pinned supported code/docs and qualify observation semantics. If supported realization genuinely cannot be established, return precise agent-findable facts/unsupported boundary for proportional Research/Planning; do not declare complete or defer missing machinery to M08. No unofficial provider or direct provider inference bypass is permitted.

Implement dedicated Muse credential source plumbing/private mechanism in addition to Codex plumbing; prose-only OAuth deferral is not the required executable secret boundary. Actual input/admission remains later and no ordinary credential may be read/copied now.

### B. Bind the actual consumed frozen artifacts and runtime

Locations: validator signature/CLI, lines 241-333 and 408-432; optional source_root/companion inputs and source-side policy checks.

The validator does not accept/validate the existing frozen candidate/build/publication handoff; source/build/handoff/configuration provenance is absent. Optional host source inspection neither stages/applies the companion in the candidate HOME nor proves the launcher/Pi that runs. The default path accepts missing required bindings. It checks a pulled image ID but not obj.Image/actual running identity; missing RepoDigests is SKIP.

Consume and strictly bind the EXISTING artifact records and declared companion, carry their provenance into output, stage/apply/read back the actual candidate policy/launcher/payload, verify running OCI-to-local identity, process/endpoint/Pi provenance and relevant configuration. Reject omission/malformed/mutated/mismatched input at the real entrypoint. Expected versions must derive from frozen candidate/resolution provenance; installed 0.9.2/0.87.1 metadata is not a permanent pin for all future candidates. Do not re-resolve/build/publish or invent another pipeline/ledger. Any guard/delivery change needs newly computed companion identity in the existing path; no old-digest eligibility by HOME mutation.

### C. Use one reachable Codex non-inference/secret-safe implementation

Locations: scripts/paseo_codex_noninference.py:59-356 and validator:161-191, 375-406, 432-466. The helper is NOT imported/called by the Tower path, which uses a second weaker shell implementation.

The shipped curl templates pass literal %{{http_code}} (never formatted) instead of curl's %{http_code}; a mock returncode or standalone malformed Node parser does not execute this transport. The shell expands Bearer $key into token-bearing curl argv inside the container, contrary to the contract, and writes full bodies to /tmp/codex-catalog.json and health.json despite documentation claiming no body persistence. Such disposable processing needs explicitly private/bounded handling and must not retain/output bodies as evidence. Tower does not use strict URL/secret-content validation; raw_hint actually reads credential content and discards it despite the adjacent contrary comment. Regex sanitizers still retain opaque echoed values. The urllib default follows redirects without validating their destination, risking forbidden inference URL traversal/auth forwarding. Required credential/catalog/auth/profile failures/missing inputs are skipped and/or aggregate PASS; false real flag alone is insufficient.

Integrate the robust non-inference transport/validation at the actual entrypoint (not an unused companion helper), validate supported endpoint/shape semantics, private file mode/ownership/content/confinement and redirects, keep credentials in private memory/file references rather than argv, avoid persisted provider bodies and arbitrary dependency tails, and propagate each required missing/negative/unknown gate honestly. Fixtures may model successful complete checks but must not bless incomplete SKIP as complete PASS. Document facts actually implemented, not declared pseudo-behavior.

### D. Immutable disposable acquisition and safe unknown/cleanup handling

Locations: validator:64-76, 126-155, 342-373, 519-546; ownership helper and work/network cleanup.

_container_owned_by_attempt returns true for a foreign object whose only mount is the exempt secret destination. Prefix string checks permit siblings and do not verify exact canonical mounts/modes, container identity or acquisition nonce. Creation ignores the returned container ID; preexisting objects may be reclaimed without proof this attempt acquired them. Existing networks are not proven isolated. Network cleanup uses only a boolean/name without fresh identity/ownership readback. Work is deleted even when container ownership changed or an unknown test needs readback; merely candidate-* under a caller root is not durable ownership. run converts subprocess timeout into generic BLOCKED so the later UNKNOWN handler does not establish uncertain inference behavior.

Use actual immutable object identities plus acquired/current ownership and exact confined mounts/network; reject foreign preexisting/collision/replacement/partial-setup surfaces before mutation. Preserve all unowned objects and operator inputs. On unknown occurrence preserve the precise owned test/runtime state necessary for bounded readback and never resend blindly; later cleanup may remove only verified owned resources. No global cache/HOME or broad state-root cleanup.

### E. Replace false-positive coverage and inaccurate completion wording

Reachable negative tests must assert the validator's required failure/classification and absence of disallowed calls, not merely real_validation_satisfied=false while status/binding stays PASS. Existing tests test helper dictionaries or premanufactured timeout snapshots, not candidate scoped dispatch/observation. Positive guards must prove the complete shared subject through the real validator entrypoint. Execute the actual non-inference transport/parser under fake/local boundaries, and inject opaque token echoes, redirects, wrong running image/Pi/daemon, missing frozen input, false caller witness, ownership collisions/replacements and uncertain dispatch through that same path.

Re-run corrected targeted, affected and full classified synthetic suites, applicable node tests, diff/secret-safe checks with honest exits/skips. Update product docs and contribution report to distinguish implemented machinery, default unsupported profile, synthetic mechanics and unverified later real outcome. No required gate may be waived. If a necessary source fact truly remains missing, provide the bounded return-owner facts rather than compensating with more helper-only GREEN counts.

## Next authorized action

One fresh implementation/repair context may correct the above inside the SAME unchanged M07-T05 Card/technical contract. It reads canonical authority independently and returns source/evidence only, unpushed, without further delegation or state writes. Main retains classification/result/review/Board ownership and reroutes after the next semantic return. Real credentials, inference, image/CI/live/production and successors remain excluded. No user input is needed for these demonstrated remediable defects.
