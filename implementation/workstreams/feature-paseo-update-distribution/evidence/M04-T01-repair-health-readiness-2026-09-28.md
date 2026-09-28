# M04-T01 — health-readiness repair evidence

Date: 2026-09-28
Implementation subject: `c09e0312df658d68a5e71437fe5f8d036c1fbf83`

## Correction

R01 found that the validator inspected the inherited Paseo healthcheck only once immediately after `docker run -d`, causing a valid `starting` candidate to be classified FAIL before it could become healthy.

The validator now performs a bounded readiness poll. For images with a healthcheck it waits through `starting` until `healthy`, rejects terminal `unhealthy`, and fails deterministically on readiness timeout. The no-healthcheck fallback continues to require container state `running`.

Focused tests now cover the production-shaped `starting -> healthy` transition and terminal `unhealthy` rejection.

## Verification

Tower worktree `/mnt/user/pi-worktrees/pud-m04t01-review`, after fast-forward to the repaired branch:
- `python3 -m unittest tests.test_paseo_tower_validator -q` -> 5/5 GREEN;
- `python3 -m py_compile scripts/paseo_tower_validator.py tests/test_paseo_tower_validator.py` -> GREEN;
- `git diff --check` -> GREEN;
- `python3 -m unittest discover -s tests -p "test_*.py" -q` -> 455/455 GREEN.

No production container, production state, accepted tag, transaction guard or rollback state was mutated.
