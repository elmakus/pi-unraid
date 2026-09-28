# Codex-LB current-main + GPT-6 image research R1

- Upstream repository: `Soju06/codex-lb`.
- Exact current upstream `main`: `f8ffbac2099a113fba54dfd8d77774f5bca80ffa`.
- Nearest release tag: `v1.25.0-beta.9`; current main is 42 commits after it.
- Existing GPT-6 patch behavior: add Astra/Sol/Luna `128_000` max-output fallbacks while explicit integer upstream `max_output_tokens` retains precedence.
- Current production before this repair: `ghcr.io/elmakus/codex-lb:v1.25.0-beta.9-private.1`.
- Safe publication identity for this untagged upstream snapshot: immutable SHA-addressed container tag derived from the fork commit that contains exact upstream main plus the bounded GPT-6 patch.
- Production must pin the immutable tag, not mutable `:main`, and retain the existing production image/container as rollback.
