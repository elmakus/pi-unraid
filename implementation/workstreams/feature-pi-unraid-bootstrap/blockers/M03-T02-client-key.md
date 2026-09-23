# M03-T02 blocker — dedicated Pi Codex-LB client credential

- Card: `M03-T02`
- Date: 2026-09-23
- Status: `active`
- Class: explicit credential/user-action gate
- Resume target: `M03-T02`

## Blocker

Codex-LB `v1.25.0-beta.9` is deployed and healthy, but the execution tool refuses the operation that generates/materializes a new plaintext API credential. This safety control must not be bypassed.

The one unusable key row created before a path failure was deactivated; there is currently no active `pi-unraid-phase1` key and no known plaintext Pi key.

## Smallest user action

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
