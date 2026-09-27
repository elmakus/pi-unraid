# M07-T02 provider/session UI preparation — 2026-09-27

The user's first manual UI check accepted the staged Paseo interface as generally acceptable and native; there were no sessions at that moment, so session-label usability was not yet observable.

A bounded staged-only provider/auth completion then reused the previously approved Tower Codex-LB configuration and credential without exposing the secret:

- existing approved model config source: legacy Pi `codex-lb/gpt-6-sol`;
- existing secret source remains outside Git at `/mnt/user/appdata/pi-unraid/secrets/codex-lb.env`, mode `0600`, owner `99:100`;
- staged runtime mounts that secret read-only at `/run/secrets/pi-unraid-codex-lb`;
- staged `models.json` contains only the provider endpoint/model metadata and the existing environment-reference contract;
- staged `auth.json` contains no credential value; it stores a native Pi `!command` credential resolver that reads the mounted secret at runtime;
- both staged Pi config files are mode `0600`, owner `99:100`;
- `pi auth check --provider codex-lb --model gpt-6-sol --json --no-refresh` => `status=ready`, `authType=api_key`;
- `pi --list-models codex-lb` exposes `gpt-6-sol`;
- `paseo provider models pi --json` exposes `codex-lb/gpt-6-sol`.

The earlier deliberately-created label probe had failed only because model auth had not yet been materialized; it was deleted.

A replacement real staged session was created through Paseo with:

- title: `HA session label check`;
- provider/model: `pi/codex-lb/gpt-6-sol`;
- working directory: `/projects`;
- prompt requested the marker-only reply `HA session ready`;
- observed reply: `HA session ready`;
- final agent state: `idle`.

No production Paseo or legacy Pi runtime was mutated by this session test.

Remaining user judgment: view this now-visible real session from the already-paired phone UI and confirm that its session label and notification behavior are sensible.
