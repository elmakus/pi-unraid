# M04-T01 — narrow Tower validator evidence

Date: 2026-09-28
Implementation subject: `6bec81ca3317bb82af3424c98a9692efe2b542b8`

## Tower readiness/readback

Read-only inspection of active `pi-unraid-paseo-1` established the production-shaped facts used by the validator contract:
- runtime UID:GID: `99:100`;
- production network: `pi-unraid_default`;
- production mount destinations: `/home/paseo`, `/projects`, `/worktrees`;
- production additionally carries host-control/Codex-LB secret mounts, which the disposable validator explicitly does not pass through.

The validator uses a separate `pi-unraid-validator` network and validator-owned temporary host directories for the three production-shaped mount destinations. It admits only `ghcr.io/...@sha256:<64hex>`, performs immutable registry readback before pull, launches the candidate read-only with tmpfs for `/tmp` and `/run`, verifies UID:GID/network/mount/runtime identity, rejects production/host secret exposure, emits PASS/FAIL/BLOCKED JSON, and always removes the disposable container and state directory.

No active production container, production mount, accepted tag, transaction guard or rollback state was mutated during M04-T01 verification.

## Verification

Clean Tower checkout outside the system temporary directory at exact subject `6bec81ca3317bb82af3424c98a9692efe2b542b8`:
- `python3 -m unittest tests.test_paseo_tower_validator -q` -> 3/3 GREEN;
- `python3 -m py_compile scripts/paseo_tower_validator.py tests/test_paseo_tower_validator.py` -> GREEN;
- `git diff --check` -> GREEN;
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> 453/453 GREEN.

The first targeted run exposed an invalid `Path.chown()` call; execution corrected it to `os.chown()` before result reconciliation and reran all verification GREEN.
