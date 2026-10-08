# ADR-PUD-005 — Proportionate validation metadata policy

Status: accepted
Definition: R3, paseo-update-distribution@12
Supersedes: metadata-only invalidation implications of the existing applied-interval implementation, not unrelated R2 safeguards.

## User decision

The user explicitly approved correcting the project's overly conservative validator rather than maintaining a Paseo patch. The accepted tradeoff is loss of an absolute guarantee against transient metadata changes restored between observations. This approval does not authorize inference, credential admission, publication or production mutation outside their existing gates.

## Required behavior

Validate exact immutable image/source/build/companion/policy bindings and continuously observe protected file identity and content. Detect content writes, replacement, deletion and meaningful owner/mode changes. At acquisition, relevant validation boundaries and completion, verify the declared private mode, expected owner and bound content/file identity. Missing, unreadable, mismatched or persistently changed inputs fail closed.

A metadata event or changed ctime alone is not a failed gate. Revalidate identity/content/owner/mode on metadata notifications; accept an event only if those observed protected properties remain valid. This is not proof of a particular syscall or trusted actor. Transient metadata mutation-and-restore between observations may escape detection and is explicitly accepted. Do not claim detection equivalence with the previous blanket IN_ATTRIB/ctime tripwire.

Do not discard content/replacement/deletion events or mask missing watches, watcher failure or queue overflow. Observation uncertainty unrelated to the explicitly accepted transient metadata limitation remains fail-closed. Do not tolerate an actual observed permission/owner/content/identity delta because the final state was later restored. Test benign normalization and observed harmful mutations separately, including content mutate-restore and replacement controls.

## Unchanged boundaries

No global chmod 777, relaxed credential ownership/private-mode requirements, candidate patch/fork, model/provider/thinking fallback, live HOME provenance, fabricated real eligibility, accepted-channel update or production cutover. Guarded Muse/max and authenticated non-inference Codex-LB requirements remain unchanged. Changes to validator source invalidate old validation-source binding and require a new frozen subject and applicable exact artifact tests/build/publication before eligibility.

## Downstream work

Main must create a material replacement plan with independent exact-subject review and normal premium gates. Execution Prep must refresh the active Card and affected accepted machinery without rewriting historical DONE results. Implementation and safety acceptance are not established by this ADR.
