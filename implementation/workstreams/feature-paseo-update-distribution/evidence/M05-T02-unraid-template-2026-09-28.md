# M05-T02 execution evidence — Unraid template and Update Ready fixture

Date: 2026-09-28
Branch: feat/paseo-update-distribution

## Tower readback
- Unraid: 7.2.4.
- DockerMan implementation: /usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerClient.php.
- Installed DockerMan update logic normalizes the image tag, obtains local identity from RepoDigests, obtains the remote registry digest, and reports update available when the two non-empty digests differ.
- Active production container before/after readback: pi-unraid-paseo-1, container id 9477662964b187f85b3f9e1a59e0ecd7143f4069e646472d7872a3cebef981af, image id sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de, configured image pi-unraid:paseo-codex-lb-env-bc87a92.
- Production ghcr.io/elmakus/pi-unraid:accepted read-only registry inspect returned not found. No tag write was attempted.

## Implemented
- Added config/unraid/templates/pi-unraid-paseo.xml for the future DockerMan-managed production surface.
- Repository is ghcr.io/elmakus/pi-unraid:accepted. The tag is explicitly signaling metadata; immutable OCI digest remains deployment/rollback authority.
- Template preserves production UID:GID 99:100, 1 GiB shm, custom network, persistent home/projects/worktrees and read-only secret mounts.
- No custom dashboard or DockerMan core patch is introduced.
- Added focused contract tests that parse the template and exercise the installed DockerMan digest comparison rule with isolated immutable digest fixtures.

## Verification
- Focused template tests: 3/3 GREEN.
- XML parse: GREEN.
- Full repository unit suite: 474/474 GREEN on Tower from /mnt/user/pw-m05-t01-checkout, outside the system temporary directory.
- git diff --check: GREEN.
- No production container restart/cutover/rollback, transaction-guard mutation, or production accepted-channel movement occurred.
