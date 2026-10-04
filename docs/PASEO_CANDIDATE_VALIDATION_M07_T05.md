# Candidate validation machinery (M07-T05)

## Status and boundaries

**Implementation remains incomplete.** This document describes current source,
not an accepted result, independent review or real validation. Historical repair
claims are preserved in workstream evidence, not repeated as current guarantees.
M07-T05 permits source and synthetic/local tests only. No real credential
admission, provider authentication, inference, installed HOME change, Docker/Tower
operation, image build/publication or production authorization is established.

Entry points are `scripts/paseo_tower_validator.py` (CLI and `validate`),
`scripts/paseo_candidate_muse_adapter.py`, and the staged
`paseo_codex_candidate_check.py` / `paseo_codex_noninference.py`.
The validator's `real` branch is inference-capable: never execute it with real
transports during implementation testing. Fixture/rehearsal classification always
leaves `real_validation_satisfied=false`. Structurally exercising a real-mode
branch under external fakes is not real evidence.

## Profile safety before dispatch

The canonical delivered guard fixes `meta/muse-spark-1.3-contributor`, `max`,
no fallback. Before prompt dispatch the validator now calls the candidate daemon's
`paseo provider models pi --thinking --json --home /home/paseo/.paseo` and requires
one exact `meta/muse-spark-1.3-contributor` model with `max` in
`thinkingOptionIds`. Missing/malformed/unavailable/ambiguous catalog or absent max
blocks dispatch. This is a necessary non-inference preflight, **not sufficient
proof of effective execution**.

Pinned public Paseo 0.9.2 source:
- CLI `dist/commands/provider/models.js`: output `id`, `thinkingOptionIds`,
  `defaultThinkingOptionId` from daemon model metadata.
- Server `dist/server/server/agent/providers/pi/agent.js`:
  `resolvePiThinkingConfig` excludes null thinking mappings;
  `fetchCatalog` invokes Pi `getAvailableModels(null)` without a prompt.
- `cli-runtime.js`: `getAvailableModels`/`getState` are RPC readbacks;
  `prompt` is the inference operation and is excluded from source inspection.

Official Pi 0.87.1 Contributor data has max=null, and its unmodified clamp maps
max to xhigh. That configuration must be blocked **before** inference, not tested
by making an xhigh request and rejecting it afterward. No max override, mapping
substitution or new provider has been adopted. A positive synthetic max catalog is
mechanical coverage only, not evidence that the pinned real profile supports max.

## Startup and observations

The adapter now requires successful typed `daemon start --json` output with
`action=started`, exact home/pid/listen agreement with status, and explicit local
running/connected reachable states, worker PID, server identity, Node path and
provider details. Failed startup and `already_running` cannot prove private auth
inheritance. Dedicated Meta input is a private file reference, read by the
candidate-env shell loader into supported `META_API_KEY`, not a raw key in argv
or `--env`. Nonsecret correlation/file pointers use the guard's supported
`--env` forwarding.

**Remaining startup gap:** Docker currently starts the image before staging;
this can start an upstream daemon outside the loader. Fail-closed rejection of
already_running prevents acceptance, but controlled pre-staging startup and
source-qualified daemon-selected Pi/process provenance are not yet implemented.
`command -v pi` and version equality alone are not daemon selection proof.
The existing positive fake reconstructs parts of startup/dispatch; it is not a
source-faithful separate daemon selecting and spawning Pi.

Pi 0.87.1 extension types distinguish provider response (before stream consumption),
qualified `turn_end.outcome`, low-level `agent_end.messages` and neutral final
`agent_settled`. The generated observer records neutral `ended` for nonnegative
agent_end, never success for an empty messages array. The aggregator requires one
ordered request/response exchange, exact model/max, valid 2xx, qualified completed
turn and settlement. Mixed, duplicate, contradictory or out-of-order exchanges
fail; missing qualified completion remains UNKNOWN, without replay. Abort/error
is not overwritten by settlement. Arbitrary done/success labels are not qualified
completion. **Remaining observation gap:** independently bound selected provider,
per-call identity and complete process/agent/workspace proof are not yet established.

## Frozen binding

The validator consumes candidate, handoff, prepared input, build, tested-image and
publication records. Candidate ID, OCI digest and local image ID are distinct.
It checks publication's tested-image byte digest, requires tested candidate byte
links, checks builder_ensure with the other successful build phases, and verifies
actual pulled image candidate label and candidate Env. In real mode an omitted
CLI companion declaration derives from the prepared record and is verified,
never silently skipped.

**Remaining binding gap:** full existing producer/source linkage, frozen
behavior-changing helper/loader/observer delivery and actual complete file-set,
content and actual-mode readback are not finished. Current generated helpers are
staged from validator source outside the declared instruction companion. Hashing
after staging is not frozen source binding. Fresh downstream artifacts remain
required; no changed HOME can bless an older image digest.

## Codex-LB: non-inference only

The shipped candidate program reads a dedicated private synthetic/operator file
in memory and performs authenticated GET `/v1/models` and GET `/health` structural
checks. No prompt or provider inference endpoint is used. Transport permits only
these exact destinations and rejects redirects that change check path or origin
(scheme/host/port), including normalized encoded inference paths, before following.
Bodies are bounded in memory and not evidence; output is bounded typed summaries.
Required missing/denied/malformed/unreachable checks fail or block. Opaque dependency
output is not retained as evidence. No ordinary auth file/HOME is copied or read.
Credential admission and actual authentication are later operations, not claims here.

## Ownership, unknown occurrence and cleanup

Acquired container/network IDs now require equality, not arbitrary prefixes.
Current container checks require exact private-secret and workspace bind mounts,
no duplicate/extra destinations, exact UID:GID, readonly root and required
`/tmp`/`/run` tmpfs properties. Each candidate exec rechecks acquired IDs and
ownership, then addresses the immutable container ID. Owned test references are
written before possible guarded dispatch. UNKNOWN preserves inspection state and
never automatically resends.

**Remaining ownership gap:** positive absence versus failed inspection, partial
acquisition recovery, complete network/work identity and honest incomplete cleanup
classification remain unfinished. Unverified/replaced resources and potentially
mounted work must be preserved. Do not interpret a PASS report as proof of clean
resource release while these gates remain open.

## Synthetic verification

Tests must isolate real Paseo/Pi/Docker/provider resolution and use only disposable
synthetic secrets and localhost/fake transports. Compile or AST-check exact shipped
programs; use a disposable `PYTHONPYCACHEPREFIX` for explicit py_compile. Strong
acceptance coverage must execute exact shipped argv/internal plumbing with only
candidate namespace paths translated, use actual producers with external effects
faked, and use a separate fake daemon selecting/spawning actual fake Pi. Current
legacy harness coverage does not satisfy all these requirements. Do not equate
passing unit counts or a fake-tested real branch with full Card acceptance.
