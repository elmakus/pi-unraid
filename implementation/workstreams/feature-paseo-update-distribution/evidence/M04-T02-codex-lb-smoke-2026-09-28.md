# M04-T02 — Codex-LB smoke plumbing evidence

Date: 2026-09-28
Implementation subject: `57237155423dab3359e87c54cd0bddafca2bc2f1`

Implemented the bounded Codex-LB smoke path as an opt-in extension of the existing disposable Tower validator.

- credential source is a caller-selected file mounted read-only at the fixed candidate path `/run/secrets/pi-unraid-codex-lb`;
- the credential value is not passed in argv, environment, result JSON or evidence;
- base URL and model are explicit non-secret inputs and the base URL must terminate in `/v1`;
- the candidate performs one bounded authenticated Responses request to `/responses`;
- endpoint unavailability maps to structured BLOCKED; authentication rejection and malformed/non-success protocol outcomes map to FAIL;
- the no-secret M04-T01 path remains unchanged and valid;
- validator still rejects production Docker socket, Unraid host-control key and production Paseo HOME.

Verification on Tower from the worktree outside the system temporary directory:

- `python3 -m unittest tests.test_paseo_tower_validator -v`: 6/6 GREEN;
- Codex-LB fixture subcases: PASS, endpoint BLOCKED, auth FAIL and protocol FAIL all GREEN;
- secret-value non-leakage assertion GREEN;
- `python3 -m py_compile scripts/paseo_tower_validator.py tests/test_paseo_tower_validator.py`: GREEN;
- `git diff --check`: GREEN;
- `python3 -m unittest discover -s tests -p 'test_*.py' -q`: 456/456 GREEN.

No real Codex-LB user key was read or used. No production container, accepted tag, transaction guard, rollback state or pooled OAuth material was mutated.

## R01 correction

Independent review R01 found that substring-only `"id"` matching could accept malformed HTTP-200 response content. The smoke now parses the response with Node `JSON.parse` inside the disposable candidate and requires a JSON object with a non-empty string `id`; parse/shape failure exits through the existing structured protocol FAIL path. The focused contract test requires structural parsing and forbids the former grep check.

Correction verification on Tower from a fresh non-temporary checkout with full Git history:
- `python3 -m py_compile scripts/paseo_tower_validator.py tests/test_paseo_tower_validator.py`: GREEN;
- `python3 -m unittest tests.test_paseo_tower_validator -v`: 6/6 GREEN;
- `python3 -m unittest discover -s tests -p 'test_*.py' -q`: 456/456 GREEN;
- `git diff --check`: GREEN;
- direct malformed HTTP-200 fixture body `{"id":` against the exact structural parser: fail-closed GREEN (`MALFORMED_FAIL_CLOSED_OK`).
