# M01-T01 — Candidate resolver implementation verification

Date: 2026-09-25
Card: `M01-T01`
Verdict: implementation acceptance evidence GREEN; independent review still REQUIRED.

## Immutable implementation subject

- Candidate commit: `d7ba943acb7511d945634dbe14539b3aef703e63`
- Frozen candidate: `config/paseo-candidate.json`
- Candidate blob: `6c85d33722c67781cc19eb2382c08919e4884cc9`
- Candidate ID: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
- Resolver blob at candidate commit: `scripts/resolve-paseo-candidate.py@09d3f85ef6e20d0928b2e83b1adf39fb2e4ced09`
- Tests blob at candidate commit: `tests/test_paseo_candidate_resolver.py@0abec51347dd01e7bc41d96ac0306f97b4779561`
- CI workflow blob: `.github/workflows/paseo-candidate-resolver.yml@afe83b5b3e6d9d0bbb352f2bde9c28e3236ad02b`

## Live resolution

GitHub Actions run `36141698006` completed GREEN on resolver/test commit `b3d49f6c9b9455bc82c0c29798c129296237192e`.

The live read-only resolver produced the exact JSON later frozen at the candidate subject above. It resolved:

- Paseo `0.9.2`, source commit `c67b7158b441bb09026b38d86ae335cc4b49190a`, exact official GHCR index digest `sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`, linux/amd64 manifest `sha256:79bf8774b0d71ab3afed3d0f4dc556b160de9d2e15841786eb92b446540dc791`;
- Node `22.23.3` inherited from that immutable Paseo image and satisfying Pi's `>=22.19.0` prerequisite;
- Pi `0.87.1` with exact Git commit plus npm sha512 integrity/shasum;
- Playwright `1.63.0` with exact Git commit plus npm integrity and Chromium revision `1243` / browser `153.0.8010.12`;
- SpecPi `0.34.0` with exact Git commit plus npm integrity;
- pi-mcp-adapter `2.37.0` with exact Git commit plus npm integrity and a declared Pi-AI `^0.87.0` compatibility range;
- GitHub CLI `2.101.0` with exact source commit and release-asset sha256;
- Docker CLI `29.8.1` with exact source tag/commit; upstream exposes no GitHub release asset, so the candidate records the exact source-commit identity and the reason the artifact digest is not applicable at this stage;
- Docker Compose `5.5.1` with exact source commit and release-asset sha256.

No compatibility exception from latest-stable was introduced. SpecPi/Pi and pi-mcp-adapter/Pi runtime compatibility smoke remains explicitly deferred to the later image/integrated acceptance Cards, as required by Definition rather than guessed here.

## Tests and fail-closed behavior

The GREEN run executed four fixture tests:

1. repeated unchanged resolution is byte-for-byte deterministic and has the full mandatory component set;
2. a resolved candidate round-trips through standalone validation;
3. removing a mandatory component exits non-zero and leaves an already accepted candidate file untouched;
4. invalid npm integrity exits non-zero.

The live step then resolved current upstream state, validated the resulting candidate, printed the exact frozen JSON, and completed GREEN.

An earlier run `36141630196` failed before exercising resolver logic because the unittest helper was accidentally named `run`, shadowing `unittest.TestCase.run`. Commit `b3d49f6c9b9455bc82c0c29798c129296237192e` corrected only that test-harness naming defect; the subsequent run is the acceptance evidence.

## Safety / scope readback

- Resolver operation is read-only with respect to upstream services.
- Candidate write uses temp-file + atomic replace only after full resolution/validation.
- Failed resolution does not replace the prior accepted candidate.
- Candidate contains no raw credential fields.
- Builds are instructed to consume the frozen candidate and not independently resolve latest.
- No child image was built.
- No temporary or production Paseo runtime was deployed.
- No Relay/auth, Unraid host-control, OR, or future PW extension work was performed.
