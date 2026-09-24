# Decision — Global environment updates are latest-stable, immutable-candidate, staged and rollback-first

- Decision ID: `ADR-PGR-004`
- Date: `2026-09-24`
- Status: `accepted`
- Definition subject: `paseo-gui-runtime@2`

## Decision

A user-approved environment update is a coordinated global maintenance batch: resolve every approved global component to its accepted latest-stable line, freeze one exact candidate resolution, build/test that candidate, then promote atomically from the production user's perspective.

Use immutable image identity/provenance, private GHCR for the child image and secondary registry cache, the exact resolved official Paseo GHCR image as the base, a dedicated persistent local BuildKit builder/cache as the fast path, cache-friendly componentization, pre/post-deploy smoke and automatic rollback to the prior coherent known-good set when safe.

Project-local locked dependencies are outside blanket global updates. Compatibility exceptions from latest require explicit user approval and later recheck.

## Consequences

Routine updates use a warm-cache fast path and proportional validation; first deployment and material control-plane/base/security changes receive broader acceptance. Builds never discover "latest" independently after candidate resolution is frozen.
