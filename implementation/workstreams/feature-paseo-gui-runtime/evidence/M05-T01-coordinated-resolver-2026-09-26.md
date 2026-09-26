# M05-T01 coordinated resolver evidence

- Card: `M05-T01`, Task Board revision 68 at launch.
- Implementation subject: `elmakus/pi-unraid@0e073c125d8bd57bd593c269d081fec079fd791e`.
- Exact predecessor: `results/M04-T03.md@fb6195831d047ede2f359146b69ede2690e84ef3:e31658fda900d748010bedc6caa0bb3aacf8c430`, DONE with independent R01 GREEN.
- Changed implementation: `scripts/resolve-paseo-candidate.py` and `tests/test_paseo_candidate_resolver.py`; the accepted `config/paseo-candidate.json`, capability inventory, project-local locks, image definition and production state were not changed.

## Verification

- Resolver fixture/contract suite: 23 tests passed, covering full approved component set, stable-line and derived provenance, exact candidate identity, repeatability, missing source/prerelease/substitution/incompatible set rejection, exception authority binding and re-evaluation, verified live older pin and unverifiable-pin failure, no partial write, secret-safe output, capability-set drift, frozen build input and unchanged local locks.
- Full local contract regression: 11 test files, 93 tests passed. A shallow-checkout-only test failure on implementation commit `2c0a80ccf9ee965f6b2a7a9ca6c19f4bbb667889` was corrected without changing product behavior; the corrected test verifies the checked-out predecessor result's exact blob with `git hash-object`.
- [Candidate resolver CI run 36217220455](https://github.com/elmakus/pi-unraid/actions/runs/36217220455): GREEN at exact implementation SHA, including fixture tests and read-only live resolution.
- [Child image foundation CI run 36217220470](https://github.com/elmakus/pi-unraid/actions/runs/36217220470): GREEN at exact implementation SHA, including predecessor binding, full contracts, frozen child-image build, image/provenance smoke, persistence/ownership, Pi instruction-plane, global capability smoke and immutable metadata inspection.
- Read-only live resolution returned a valid complete candidate without adopting it. A separate read-only live test resolved SpecPi `0.33.0` from exact upstream provenance against observed latest `0.34.0`, recorded `still_required`, and rejected unverifiable `0.99.0` with no candidate output. These probes used temporary synthetic exception-authority records for testing; they did not approve or install an exception in the project.

## Semantics and boundary

The resolver now consumes the accepted inventory component set, selects all approved stable lines together, records exact identity/provenance and stable-line rationale, and fails closed on mandatory resolution, channel, identity, compatibility, capability-set or exception-authority mismatch. `--check` and the no-output form are read-only; explicit output stages to a separate path and rejects the accepted candidate and input paths. Builds continue to consume the frozen accepted candidate. Doctor/reconcile and production cutover remain separate later work.

An exception record carries an exact component, pin, scope and rationale bound to a content digest of a separate authority record, and each resolution records whether the pin still lags observed latest. No actual user-approved compatibility exception exists in this workstream. Supplying a future record remains subject to real user approval in the workflow; the resolver's content check alone is not a grant of that approval.

Runtime compatibility of any newly resolved or pinned candidate remains gated by subsequent image and integrated smoke. No Tower or production mutation was performed.
