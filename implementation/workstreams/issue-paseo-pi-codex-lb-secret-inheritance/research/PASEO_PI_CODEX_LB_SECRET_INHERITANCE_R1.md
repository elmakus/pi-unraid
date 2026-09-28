# Research — Paseo → Pi Codex-LB secret inheritance

Subject: `repair:paseo-pi-codex-lb-secret-inheritance:v1`

## Finding

The production defect is not in dynamic model discovery. Pi can load the current nine-model Codex-LB catalog, and Paseo 0.9.2 can enumerate the same nine models through its provider catalog API. The failure is the Pi child-process launch path used by Paseo sessions: the Paseo daemon process does not have `CODEX_LB_API_KEY`, and it launches the stock `pi` binary directly, so a real session fails API-key resolution.

Paseo 0.9.2 provides a supported launch seam for this exact case. Its Pi provider resolves the binary from `PI_COMMAND` (falling back to `pi`) and uses that command for both catalog and session RPC launches. The runtime preserves the normal Pi CLI arguments (`--mode`, `--model`, `--thinking`, session arguments, MCP config and extension paths). Therefore a repository-managed wrapper selected through non-secret `PI_COMMAND` is sufficient; no Paseo patch is required.

The repository already owns `scripts/pi-unraid-provider`, which validates the dedicated read-only secret file, exports `CODEX_LB_API_KEY` only into the child process and never logs the value. The permanent path should reuse that parser rather than place the secret in Compose environment or Docker metadata.

## Exact production/runtime evidence

- Production container: `pi-unraid-paseo-1`, Paseo 0.9.2.
- Dedicated secret is mounted read-only from `/mnt/user/appdata/pi-unraid/secrets/codex-lb.env` to `/run/secrets/pi-unraid-codex-lb`.
- Container environment has `PI_CODEX_LB_SECRET_FILE=/run/secrets/pi-unraid-codex-lb` but `CODEX_LB_API_KEY` is absent.
- Production `/usr/local/bin/pi` resolves directly to the Pi 0.87.1 npm CLI; `pi-unraid-provider` is not installed in the current Paseo image.
- A real recorded Paseo Pi session reports `API key auth failed ... CODEX_LB_API_KEY`.
- Direct Pi RPC succeeds and returns nine Codex-LB models when the mounted secret is explicitly sourced.
- `paseo provider models pi --thinking` currently lists all nine catalog models, proving catalog transport/cache is not the blocking defect.
- Current production was recreated from a temporary appdata compose/image under `appdata/pi-unraid/codex-lb-env-fix`; that hotfix mounts the secret but does not install/select a Pi launcher, so it does not solve child-process authentication.

## Exact upstream evidence

From the installed official Paseo 0.9.2 server package:

- Pi provider default command is `process.env.PI_COMMAND ?? process.env.PI_ACP_PI_COMMAND ?? "pi"`.
- `buildPiLaunch` preserves provider/session environment overlays and appends the normal Pi RPC/model/thinking/session arguments to the selected command.
- Pi catalog refresh and real sessions use the same runtime abstraction/command resolution.

This makes `PI_COMMAND=/usr/local/bin/pi-unraid-paseo-launcher` an upstream-supported integration seam.

## Required permanent repair shape

1. Install the repository-owned secret helper into the Paseo child image.
2. Install a small dedicated Paseo Pi launcher that calls the helper to load the mounted secret and then execs the real stock `/usr/local/bin/pi`.
3. Set only non-secret `PI_COMMAND` and `PI_CODEX_LB_SECRET_FILE` in Compose.
4. Make the existing read-only Codex-LB secret mount and host-gateway route part of repository Compose instead of the appdata hotfix copy.
5. Update the provider helper so the accepted dynamic provider config (no static `models` array) is considered compatible and is never rewritten back to a static catalog.
6. Acceptance must exercise the real Paseo provider/session path rather than manually sourcing the secret before launching Pi.
7. Any acceptance step that sends a real LLM inference request must use `codex-lb/gpt-6-luna` with thinking `low`, never Astra, under `PIB-ADR-008`.

## Limitations

This research does not claim that the mobile app will immediately repaint a previously open cached model-picker sheet; UI refresh/cache behavior is separate from the authenticated Pi child-process defect. The backend Paseo provider catalog already enumerates all nine models.

## Conflicts

None. The proposed repair reuses the existing project secret boundary and Paseo's supported command override. It avoids exposing the client key in Compose environment and does not change Codex-LB OAuth/account routing.
