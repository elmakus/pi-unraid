# M04-T01 — R02 integration repair evidence

Date: 2026-09-28
Implementation subject: `2cc7554ea54c22e100781a0f279e018450ea7fc0`

## Correction

R02 proved that the bounded `wait_for_runtime()` helper added after R01 was not wired into the actual `validate()` path.

The validator now calls `wait_for_runtime(name)` immediately after the disposable candidate launch and uses the returned inspected object for the UID:GID, mount, network and secret-isolation checks. The obsolete one-shot health rejection in `validate()` was removed.

The existing end-to-end PASS unit test now drives the real `validate()` path through an inherited-healthcheck sequence of `starting -> healthy` and asserts that at least two candidate inspections occurred. Helper-level tests continue to cover `starting -> healthy` and terminal `unhealthy`.

## Verification

Tower worktree `/mnt/user/pi-worktrees/pud-m04t01-review`, reset to remote `feat/paseo-update-distribution` at `2cc7554ea54c22e100781a0f279e018450ea7fc0`:
- `python3 -m unittest tests.test_paseo_tower_validator -q` -> 5/5 GREEN;
- `python3 -m py_compile scripts/paseo_tower_validator.py tests/test_paseo_tower_validator.py` -> GREEN;
- `git diff --check` -> GREEN;
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> 455/455 GREEN.

No production container, production state, accepted tag, transaction guard or rollback state was mutated.
