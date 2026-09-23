# M03-T04 blocker — GitHub user authentication

- Card: `M03-T04`
- Date: 2026-09-23
- Status: **BLOCKED — user authentication required**
- Origin: live production acceptance after all other currently executable M03-T04 checks passed

## Blocking condition

The production Pi home is new and intentionally does not inherit host/root credentials.

Current readback:
- strict GitHub SSH host verification: configured;
- Git identity: configured persistently;
- canonical project/worktree local commit: GREEN;
- `ssh -T git@github.com`: authentication unavailable (no Pi-user SSH key authorized at GitHub);
- `gh auth status`: no authenticated GitHub CLI account.

Therefore the Card cannot honestly claim the required authenticated SSH Git write and authenticated `gh` operation.

## Required user action

Authenticate GitHub once inside the production Pi home using GitHub CLI with SSH as the Git protocol:

```sh
docker exec -it -u pi pi-unraid-pi-1 gh auth login --hostname github.com --git-protocol ssh --web
```

Complete the browser/device authorization. When prompted about an SSH key, allow `gh` to use/upload or generate the Pi user's own key. Do not copy Tower root credentials into Pi.

After login, workflow continuation should:
1. re-read `gh auth status` and SSH authentication;
2. use the already prepared bounded branch/worktree `m03-t04-live-acceptance` for the authorized SSH push/write test and readback;
3. perform one bounded authenticated `gh` API write/readback and clean up disposable acceptance artifacts;
4. reconcile M03-T04 evidence;
5. freeze the completed exact subject for its RECOMMENDED independent review.
