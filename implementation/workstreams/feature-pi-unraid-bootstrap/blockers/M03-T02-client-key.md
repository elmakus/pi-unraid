# M03-T02 blocker — dedicated Pi Codex-LB client credential

- Card: `M03-T02`
- Date: 2026-09-23
- Status: `resolved`
- Class: explicit credential/user-action gate
- Resume target: `M03-T02`

## Resolution

The user manually created a dedicated API key named `pi-unraid-phase1` and materialized it on Tower at the documented protected env-file path without exposing the value to ChatGPT or Git.

Execution readback verified:
- the file exists;
- mode is `600`;
- it contains exactly one non-empty `CODEX_LB_API_KEY=...` entry;
- Codex-LB has exactly one active `pi-unraid-phase1` key row;
- authenticated `GET /v1/models` returns HTTP 200 from the Tower host;
- authenticated `GET /v1/models` also returns HTTP 200 from a disposable Docker bridge container using `host-gateway`;
- the key value was not printed or recorded in evidence.

## Historical user action

In the Codex-LB dashboard:

1. create one new API key named `pi-unraid-phase1`;
2. leave account assignment unrestricted/empty so normal Codex-LB pool routing applies;
3. do not paste the key into ChatGPT or commit it to Git;
4. on Tower, save the returned one-time key as a single environment-file line:
   `CODEX_LB_API_KEY=<key>`
   at:
   `/mnt/user/appdata/codex-lb-clean/client-secrets/pi-unraid.env`
5. set that file to mode `600`.

The directory `/mnt/user/appdata/codex-lb-clean/client-secrets` already exists and is mode `700`.

After the user confirms the file exists, execution may verify presence/permissions and continue M03-T02/M03-T03 without reading or exposing the secret value.
