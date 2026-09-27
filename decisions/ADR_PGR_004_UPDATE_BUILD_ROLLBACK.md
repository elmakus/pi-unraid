# Decision — Global environment updates are latest-stable, immutable-candidate, staged and rollback-first

- Decision ID: `ADR-PGR-004`
- Date: `2026-09-24`
- Amended: `2026-09-26`
- Status: `accepted`
- Definition subject: `paseo-gui-runtime@3`

## Decision

A user-approved environment update is a coordinated global maintenance batch: resolve every approved global component to its accepted latest-stable line, freeze one exact candidate resolution, build/test that candidate, then promote atomically from the production user's perspective.

Use immutable image identity/provenance, the exact resolved official Paseo GHCR image as the base, a dedicated persistent Tower-local BuildKit builder/cache as the primary build path, bounded retention of local immutable known-good child images for staged deployment/rollback, cache-friendly componentization, pre/post-deploy smoke and automatic rollback to the prior coherent known-good set when safe. Private project GHCR publication, registry-backed recovery cache and a self-hosted GitHub runner are optional deferred enhancements rather than prerequisites for the current deployment.

Project-local locked dependencies are outside blanket global updates. Compatibility exceptions from latest require explicit user approval and later recheck.

## Consequences

Routine updates use a Tower-local warm-cache fast path and proportional validation; first deployment and material control-plane/base/security changes receive broader acceptance. Builds never discover "latest" independently after candidate resolution is frozen. Complete loss of local Docker/BuildKit state is recovered by rebuilding from canonical Git plus the frozen candidate/provenance unless a separately approved remote-registry enhancement exists.
