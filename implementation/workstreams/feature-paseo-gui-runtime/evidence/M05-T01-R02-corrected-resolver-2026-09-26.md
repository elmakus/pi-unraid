# M05-T01 corrected resolver evidence after R01 RED

- Corrected implementation subject: `elmakus/pi-unraid@2d87d9f396e99749ecd13dbfa3ec5c2cbeea600a`.
- Prior result and review remain immutable: `results/M05-T01.md@456a795737cf981d7297daa45549a9fd78d3e74a:783e1f2696f228a94be26ebc1ac9b1ea9d8a1af3` and `reviews/M05-T01-R01.toml` RED. The correction stays inside M05-T01 authority and changes only `scripts/resolve-paseo-candidate.py` and `tests/test_paseo_candidate_resolver.py`.

## R01 finding closure evidence

- F1: schema allowlists now reject unexpected top-level, policy, component and nested provenance/exception fields. The `token` key is also covered by the secret-name barrier. Negative tests show `--check`, `--output`, `--validate` and `--readback` reject token-bearing candidate input with empty output, no staged candidate and no injected value in errors. Legacy accepted candidate and valid live-shaped fixtures remain valid.
- F2: the output guard reads the canonical inventory independently of any supplied `--inventory`, protects both canonical and supplied accepted-candidate paths and the canonical inventory itself, and fails closed when canonical state cannot be read. A negative test with an alternate inventory and accepted output path verifies refusal and byte-identical accepted candidate preservation.

## Verification

- Local resolver suite: 27 tests passed. Complete contract regression: 11 files, 97 tests passed. The accepted candidate and inventory were unchanged; no project-local locks, image definition or production state were modified.
- [Candidate resolver CI run 36218718757](https://github.com/elmakus/pi-unraid/actions/runs/36218718757): GREEN on exact corrected SHA, including fixture tests and live read-only resolution.
- [Child image foundation CI run 36218718765](https://github.com/elmakus/pi-unraid/actions/runs/36218718765): GREEN on exact corrected SHA, including predecessor bindings, full contract tests, frozen image build, disposable image/provenance, persistence, instruction plane and global capability smokes.

No compatibility exception was approved or adopted. Future exception authority remains an explicit user/workflow decision. No new candidate was promoted and no Tower or production mutation was performed.
