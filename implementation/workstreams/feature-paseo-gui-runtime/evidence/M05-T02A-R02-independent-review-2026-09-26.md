# M05-T02A R02 independent review — GREEN

- Exact result subject: `elmakus/pi-unraid@d6643ffcdf202add37a39bc7653d6192cde36637:implementation/workstreams/feature-paseo-gui-runtime/results/M05-T02A-R02.md@4273708d8f1cc8fb5eb33b3a7582fd0b21e143f4` (rev-parse + hash-object verified).
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M05-T02A.md`.
- Implementation subject named by result: `elmakus/pi-unraid@d4523248b8025d65649d4b734e58e89a894e03d9` (exists; HEAD `a7bf814` adds only R02 attempt freeze; scripts/tests/Dockerfile identical to impl SHA).
- Prior RED: `reviews/M05-T02A-R01.toml` + `evidence/M05-T02A-R01-independent-review-2026-09-26.md` (RED-1 effective FROM, RED-2 default builder).
- Independence: reviewing context did not produce, reconcile or repair this result or implementation; it designed and ran its own probes and rechecked the verdict.

## Verdict: GREEN

Both R01 findings are corrected on the exact subject; full Card acceptance is met on trusted paths.

## Evidence checked

- Bindings: R02 blob/commit verified; predecessors `M05-T01-R02@40ad9529:7b385523` and `M01-T03@bbc862c3:3772f647` verified via rev-parse + hash-object locally and in CI `Verify exact predecessor bindings`; frozen candidate revalidated (resolver + id hash + FROM + label).
- Fix scope: `d452324` touches only `scripts/paseo_buildx.py` + `tests/test_paseo_buildx_contract.py` (194+/6-); no candidate/Dockerfile/workflow/result/board change.
- RED-1: `effective_from_images` (skips full-line comments/directives, joins continuations, case-insensitive, strips `--platform`/`AS`) + strict all-FROM equality. Independent mocked probes: wrong digest + expected in 4 comment shapes rejected via `verify_build_inputs` and via `--context` with zero Docker calls (`EXIT_VALIDATION`, resolution `failed`); multi-stage second-wrong rejected; continuation/case/flag/tab/ARG-var/inline-wrong covered; real Dockerfile passes.
- RED-2: shared `validate_builder_name` (empty/`paseo`/`*workstation*`/case-insensitive `default`) used by `ensure_builder` and `cmd_prune`; `cmd_build` reuses validated name. Probes: `default` case/space/tab variants rejected on build (flag+env, `EXIT_BUILD`, zero calls, `builder_ensure failed`/`build skipped`, no `default` invocation) and prune (flag+env, `EXIT_VALIDATION`, record untouched); padded valid name invokes stripped `pi-unraid-paseo`; distinct `my-default-builder` correctly accepted.
- Contracts: local `python3 -m unittest discover -s tests` 136/136 OK; exact-SHA CI run 36238131162 (`headSha d452324…`, `success`, 1 job GREEN) logs 39+27+6+5+5+6+4+9+10+7+5+13=136 OK with no FAILED.
- Cold/warm (CI artifact `paseo-buildx-evidence`, downloaded + inspected): cold fresh builder `reused:false`, tag `pi-unraid:paseo-b4e0c1e7c276`, image `sha256:c75d…`, 0 cached, phases ok (23/366/121924/46996/93 ms); warm-same reused, same image, 8 cached (`#3,#7-#13 CACHED` in log+record), 5136 ms; warm bounded-label reused, distinct `sha256:e187…`, 8 cached, 4950 ms; metadata digest `sha256:dfa0…`.
- Smoke/prune: 4 smokes GREEN on cold record (provenance with pi 0.87.1/chromium 153.0.8010.12, persistence, instruction-plane, global-capabilities); prune `pi-unraid-paseo --keep-storage 8GB` gated on build+test ok, `buildx du` 11263 B before+after, image still inspectable with candidate label; negative gating (failed test, builder mismatch, invalid bound) covered by contracts + probes.
- Exclusions: workflow `contents:read`, no docker push/login/registry/Tower/self-hosted (only `on: push:` trigger); script has no push/login/registry/network/legacy surface outside deny lists; Dockerfile has no `:latest`/`@latest`/legacy tokens (only benign `"latest"` in comment); no candidate/GHCR/Tower/production mutation; persistent Tower survival remains M05-T02B per repair evidence.

## Residual / limitations

- No local Docker (`docker: not found`); real build/smoke/prune observed via exact-SHA CI artifact + logs, local behavior via mocked probes. No Tower/production/GHCR mutation attempted.
- Same-substring class remains for non-FROM Dockerfile fields: wrong effective `ENV`/`LABEL` with expected string in a comment still passes `verify_build_inputs` (demonstrated). Post-build label check and version-sensitive smokes catch the label/PI cases after Docker; gh/docker-version drift without smoke assertion is theoretically undetected. R01 scoped comment-proofing to FROM; trusted CI paths are correct. Recommend future effective-instruction hardening, not blocking for this Card.
- Forged local record could release prune (operator-local trust, no Card attestation; R01 non-blocking). Ephemeral CI proves reuse within one job; persistent-host survival is the documented M05-T02B obligation. `—keep-storage` deprecation notice in prune output is benign (`keep_storage:8GB`, `ok`).
