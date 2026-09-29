# M07-T03 — release-readiness reconciliation

Date: 2026-09-29
Implementation subject: `4aa53c4690d75611f8edbc9aa9541351b1a8ebca`

## Dependency reconciliation

- M07-T01 is DONE with required independent review GREEN. Its fresh coherent autonomous rehearsal produced exact final candidate digest `sha256:77e29f0d8fe8b1975725ba8b430ed7f2225dcc55c2074b397d153fcea3da4cf7`; GitHub build/publication, Tower exact-digest validation with fixture-only Codex-LB smoke, representative A -> C -> A, M07-only guard readback and isolated non-production promotion were GREEN.
- M07-T02 is DONE with required independent review GREEN. Its bounded failure/race matrix is 53/53 GREEN; the full repository suite recorded on the unchanged product-code subject is 503/503 GREEN and `git diff --check` GREEN.
- No product implementation changed during M07-T03 launch/reconciliation; changes after the tested M07-T02 product-code subject are workflow/evidence state only.

## Current Tower readback

Active production `pi-unraid-paseo-1` is running/healthy on image ID `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`, configured image `pi-unraid:paseo-codex-lb-env-bc87a92`.

Known-good ledger:
- current: `sha256:05e140da78a5bb092fed20102a855fc6e0eae364935f11cdc75b82969f0f32de`
- previous_1: `sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30`
- previous_2: `sha256:ddb23ca173e47cbd77739e6177a5860190221bc9556eeff561e8b2c9c888f005`

The durable guard-input contract remains explicitly `unarmed` and supplies the current predecessor digest, production configuration digest `sha256:ebc1b352c340e1796f30bdb1b9b0df5424294bd8e5465b027f5dffb7c1f13f89` and rollback-anchor path. The independently retrievable rollback-anchor file is present.

Registry readback:
- production `ghcr.io/elmakus/pi-unraid:accepted`: not found / unchanged;
- exact M07 final candidate `ghcr.io/elmakus/pi-unraid@sha256:77e29f0d8fe8b1975725ba8b430ed7f2225dcc55c2074b397d153fcea3da4cf7`: present with exact digest readback.

## Readiness conclusion

G7 autonomous readiness is satisfied. The exact final candidate, current production predecessor, configuration binding and rollback-anchor material required for M08 are available. The production guard is not armed, production `:accepted` is absent, and the active production runtime has not been restarted, cut over or rolled back. Real Codex-LB smoke, exact final guard arm/readback and production exposure remain M08 obligations.
