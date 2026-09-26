# M05-T02B R01 independent review — GREEN

- Exact result subject: `elmakus/pi-unraid@b7aa565649d14168e0d4b2d2d06044c08aac46a0:implementation/workstreams/feature-paseo-gui-runtime/results/M05-T02B.md@7bdb9fffcbada5f0dc6475f3bb2b7be92d8e1d20` (rev-parse + ls-tree + hash-object verified; HEAD `43815c7` adds only review-queue/pointer commits).
- Acceptance: `implementation/workstreams/feature-paseo-gui-runtime/cards/M05-T02B.md`.
- Implementation subject named by result: `elmakus/pi-unraid@4fd87cd0b3e8c72f211ed14f66dfc18b00e1b0e8` (exists; `scripts/` + `tests/` identical between impl SHA and HEAD, hash-verified).
- Attempt: `implementation/workstreams/feature-paseo-gui-runtime/reviews/M05-T02B-R01.toml` (pending, exact subject binding verified).
- Independence: reviewing context did not produce, reconcile or repair this result or implementation; it designed and ran its own probes and rechecked the verdict.

## Verdict: GREEN

All locally verifiable acceptance is met on the exact subject. Tower-live claims are
reviewed as prior-execution evidence (no safe Tower connection exists here) and are
internally consistent with each other and with independently verified code paths.

## Independently observed facts

- Bindings: result blob/commit, impl SHA, predecessor `M05-T02A-R02@d6643ffc:4273708d` (review verdict green), and P3 blob `fb071b96` (matches evidence claim) all verified via rev-parse/ls-tree/hash-object. Authority: requirements R2 approved, ADR-PGR-004 accepted, P3 frozen.
- Suites reproduced: full `python3 -m unittest discover -s tests` 147/147 OK; focused `test_paseo_buildx_contract + test_paseo_tower_build_contract` 50/50 OK (39+11). Expected argparse-negative output only.
- 51 adversarial probes (`/tmp/m05t02b_r01_probes.py`), 0 failures: builder isolation rejects `default` case variants, `*workstation*`, `paseo`, empty; path boundary rejects outside/boundary-equal/symlink-escape; storage parser accepts `8GB/1KB/1.5MB`, rejects `all/8/-1GB/8GiB`; record gates reject failed build/test, non-`pi-unraid:paseo-*` tags, missing image/candidate identity; retention bound rejects 0/21; live-image and candidate-label mismatches rejected; retention schema/corrupt rejected; cache GC removes only unreachable blobs and fails closed on corrupt index; no registry/runner tokens in Tower source.
- CLI fail-closed: missing candidate exits 2 with build/test/prune skipped; out-of-boundary root exits 2; `prune` requires `--record` (exit 2). `cmd_build` returns before retention/cleanup on inner failure (contract + probe).
- Real-input check: `verify_build_inputs` passes on working-tree Dockerfile + frozen candidate `sha256:b4e0…5069`; derived tag `pi-unraid:paseo-b4e0c1e7c276`, Paseo 0.9.2 / Pi 0.87.1, base `ghcr.io/getpaseo/paseo@sha256:d413ff…` all match evidence.
- Current prune path: `--max-used-space` with size-only bound, post-success-only, builder-matched record gating in both `paseo_buildx.py` and Tower wrapper; portable-cache 8 GiB hard cap with OCI reachability GC and `cache-policy.json` record.
- Machine-readable surfaces in code: build record (immutable candidate/image identity, per-phase `duration_ms`, `finished_at`), `retention.json` (bounded, default max 3), `cache-policy.json`, `tower-readback.json` (builder visibility, paths, `cache_bytes`, protected-image presence).
- Hygiene: zero secret-token hits in evidence + result; no push/login/registry-cache/runner/cutover/reboot/engine-restart code (two benign comment matches only); floating-channel and legacy-Pi deny lists enforced in `verify_build_inputs`.

## Prior-execution claims (not independently re-observed)

Cold build (108143 ms, 0 cached, image `sha256:4bf8…`), final-SHA warm build
(8 cached steps, 7945 ms, image `sha256:a8ea…`, 4 smokes GREEN), portable cache
933087833 B under 8 GiB, retention protection of `pi-unraid:paseo-b4e0c1e7c276`,
disposable-runtime survival with unchanged builder/production container IDs, and
fail-closed retention-hash stability come solely from the implementation evidence
file. No safe existing Tower connection exists here (no SSH config/keys/host,
no `tower` DNS, no Docker, no Tower env; Tower is outside CI), so live
re-readback was impossible without new access, which is out of scope for this
review. Claims are specific, internally consistent (tag derivation, version
identity, distinct cold/final images explained by label-only update), and each
maps to a code path verified locally.

## Residual / limitations

- Tower live state was not re-observed; acceptance of the Tower-live half rests on implementation-authored evidence plus verified code/tests. A later Tower readback (dedicated builder running, appdata paths, protected image inspectable) would close this gap.
- Same-substring class from M05-T02A-R02 (non-FROM Dockerfile fields) persists by design; trusted paths verified correct here. Not blocking.
- Forged local records could release prune (operator-local trust, no Card attestation). Not blocking.
