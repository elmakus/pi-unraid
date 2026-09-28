# M01-T01 pre-production evidence

Date: 2026-09-28
Repair subject: `repair:codex-lb-gpt6-max-output-128k:v1`

## Upstream contribution

- Fork branch: `elmakus/codex-lb:fix/gpt6-max-output-tokens`.
- Upstream base at implementation start: `Soju06/codex-lb@f8ffbac2099a113fba54dfd8d77774f5bca80ffa`.
- Code/test patch commit: `641b4f30eee138eefad06e014f2087c30f61e4d5`.
- Current contribution head after OpenSpec completion: `d64c94338305315d28d1e5899a3aee9c5cb53771`.
- Upstream pull request: `Soju06/codex-lb#2528`.
- Behavior: add `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna` at `128_000` to `_V1_MAX_OUTPUT_TOKEN_OVERRIDES`; preserve explicit integer raw `max_output_tokens` precedence.
- OpenSpec change: `advertise-gpt6-max-output-tokens`, strict validation GREEN.
- `tests/integration/test_v1_models.py`: 62/62 GREEN on the contribution branch.

## Canonical private production artifact

- Accepted upstream release lineage: `Soju06/codex-lb@v1.25.0-beta.9`, peeled commit `69f128afcbc616d9f8e924ca6583f7031d75cf82`.
- Private patch commit: `43afbc34b003da3be2485299092bbcf871b492a1` with parent exactly `69f128afcbc616d9f8e924ca6583f7031d75cf82`.
- Private release tag: `v1.25.0-beta.9-private.1`, peeled commit `43afbc34b003da3be2485299092bbcf871b492a1`.
- Published image: `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1`.
- OCI index digest: `sha256:6202eb5867a87028e7ac9b4c2a29131f2f275fe610d6a556beaf695f8b360ded`.
- linux/amd64 manifest digest: `sha256:215819235c53c8a17bd7fca68bdaf2d1caa9ac4e5bd492ba41aa5f8c641c0957`.
- Pulled local image ID: `sha256:d4a6d8ddbaff85d9091a18a2b25b1d5df6d60648fc41ed17c5bd2848d6d7b270`.
- Image `/app/app/modules/proxy/api.py` SHA-256 equals exact private source file SHA-256: `905e2539d426f2a05f5b7558116b64f984546378c21b6111d3947e5dd02bfa76`.
- Exact private source `tests/integration/test_v1_models.py`: 62/62 GREEN.

## Production pre-state and rollback anchor

Production container before cutover:
- name: `codex-lb-clean`;
- image reference: `ghcr.io/soju06/codex-lb:1.25.0-beta.9`;
- image ID: `sha256:867eeb726bf3d8141ed18ac35a827d3a3d0f49e6a6cca285567adf1f98102f0f`;
- running: true; restart count: 0;
- network: `ibraproxy`;
- ports: host `1455 -> 1455/tcp`, host `2455 -> 2455/tcp`;
- bind: `/mnt/user/appdata/codex-lb-clean -> /var/lib/codex-lb` read/write;
- environment contract: `CODEX_LB_ENCRYPTION_KEY_FILE=/var/lib/codex-lb/encryption.key`, `TZ=Europe/Berlin`;
- restart policy: `unless-stopped`.

Cutover uses a stopped renamed copy of the exact old container as the immediate rollback anchor. No appdata migration or database rewrite is part of this repair. If post-cutover acceptance fails, the new container is removed, the old rollback container is renamed back to `codex-lb-clean`, and the exact old image/config is restarted.
