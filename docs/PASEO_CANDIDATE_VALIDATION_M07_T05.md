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
or `--env`. Host input must be privately owned by the candidate UID; ordinary
`.pi`/`.paseo` and production HOME input roots are rejected before content reads.
Ordinary prompt-form guard use retains supported `--env` forwarding. The
candidate-only `--candidate-owned PRIVATE_CONFIG` guard extension uses the same
fixed policy, then invokes the frozen private runtime bridge. It is not an
unguarded root/native inference launcher: native-argument export inside the
bridge is metadata validation only; every candidate effect is reached through
the guard extension. No profile override or fallback is accepted.

Docker now overrides the upstream entrypoint with a non-daemon hold process
(`/bin/sh -c 'exec sleep infinity'`, upstream healthcheck disabled). No upstream
startup runs before private staging. A controlled PATH and absolute PI_COMMAND
are supplied to this disposable container; Pi resolution must match
`/usr/local/bin/pi`. Missing selected Pi in daemon status fails before dispatch.
The private `config.json` uses supported `agents.providers.pi.command`
replacement to select the frozen `m07-t05-pi-owned.py` wrapper, not PI_COMMAND
expectations. Relay, MCP injection, browser tools and plugins are disabled. Every
runtime CLI invocation uses `env -i` with a small nonsecret HOME/PATH/TMP whitelist;
ambient daemon/caller/workspace/Node/Pi selectors cannot select another process.
The wrapper compares inherited Meta auth in memory against the dedicated private
pointer, exclusively records PID/PPID/start-time/executable-byte facts under the
actual supported PASEO_AGENT_ID, then execs the fixed Pi executable. It never
exports an auth value/fingerprint or reads a credential-bearing /proc environment.
The bridge verifies the connected client's supported server-info, actual agent
snapshot workspaceId/cwd/provider/runtime model/effective thinking, parent process
Node identity, /proc process start times and selected executable argv/bytes before
sending. CLI inspect does **not** expose workspaceId; no automatic workspace env
is invented. Private config/reference inode changes fail closed.

The separate external CLI/daemon/Pi fixture now executes the same validator,
guard, loader, bridge, wrapper and observer path (namespace path translation only).
Its daemon selects/spawns a separate fake Pi via the actual pinned buildPiLaunch.
No provider/auth resolver is imported. Actual processes/IDs, rather than canned
PID/title/usage metadata, supply the runtime controls. This qualifies bounded
synthetic runtime behavior, not an actual daemon/provider or artifact chain.
A new, separately classified source-qualification fixture uses the **actual**
pinned Paseo PiRpcAgentClient/PiCliRuntime/JSONL process code in an isolated
synthetic daemon to select/spawn a separate metadata-only fake Pi. Official
Meta model data, official clamp calculation, official catalog transformation and
actual created-session runtime readback all exclude effective fixed max. Auth
inheritance is tested only with a disposable synthetic value. No prompt RPC is
sent. This qualifies that bounded source behavior, not full candidate binding.

The frozen observer is opt-in: without an explicit test ID and absolute private
witness reference it registers no handlers and observes no ordinary agents.
The actual shipped observer reads the supported handler's **actual**
`ctx.model.provider` and `ctx.thinkingLevel`, separately from wire model/effort.
Both context and wire must match. It aborts on mismatch or observation failure;
throwing alone is not relied on because official ExtensionRunner catches errors.
If supported abort cannot synchronously prove an aborted signal (missing/stale/
broken context), it fail-stops only that explicitly opted-in test Pi process with
exit 42. This is a local transport fuse, not model fallback, successful completion
or a workflow stop.
Witness output is a bounded vocabulary, and opening it rejects symlinks,
nonregular/wrong-owner/nonprivate files. Generated helper staging now copies
this frozen delivery member rather than maintaining a second observer generator.

Pi 0.87.1 extension types distinguish provider response (before stream consumption),
qualified `turn_end.outcome`, low-level `agent_end.messages` and neutral final
`agent_settled`. The shipped observer records neutral `ended` for nonnegative
agent_end, never success for an empty messages array. The aggregator requires one
ordered request/response exchange, exact actual provider/thinking and wire model/max, valid 2xx, qualified completed
turn and settlement. Mixed, duplicate, contradictory or out-of-order exchanges
fail; strict readback rejects every malformed, wrong-subject or unknown-field row
before aggregation rather than filtering it away. Missing qualified completion
remains UNKNOWN, without replay. Abort/error
is not overwritten by settlement. Arbitrary done/success labels are not qualified
completion. Candidate-path events additionally bind every row to actual Pi PID,
agent ID, API-observed workspace ID and connected server ID. The immutable private
binding includes its acquired inode; an identical-byte replacement is rejected
by the observer before transport. Only one provider exchange is admitted because
the pinned hooks expose no universal request ID. API workspace/agent creation
request IDs, idempotency keys and the supported messageId are retained separately
from that single-exchange process binding, never misrepresented as provider IDs.

## Frozen binding

The validator consumes candidate, handoff, prepared input, build, tested-image and
publication records. Candidate ID, OCI digest and local image ID are distinct.
It checks publication's tested-image byte digest, requires tested candidate byte
links, checks builder_ensure with the other successful build phases, and verifies
actual pulled image candidate label and candidate Env. In real mode an omitted
CLI companion declaration derives from the prepared record and is verified,
never silently skipped.

The loader, observer, private runtime bridge/Pi wrapper and shared Codex programs are repository-managed
`config/pi-agent` files in the existing companion file/mode/content declaration.
The prepare/build/package companion also freezes the nine used validation source
files as `validation_sources`; verification compares them to the executing
validator/helper sources, not hashes first manufactured after staging. Staging
requires the exact declaration file set and actual file modes. Candidate readback
compares every declared file's hash and actual mode, not only guard/policy fields.
**Remaining binding gap:** complete producer/source/configuration linkage and
positive artifact chains from actual producers are not yet qualified. The legacy
hand-authored chain is not full evidence. Fresh downstream artifacts remain
required; changed delivery cannot bless an old digest.

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
written before any network/container acquisition and updated with acquired IDs.
Host references are private atomic updates with inode checks and directory fsync.
The private runtime bridge allocates supported requested workspaceId/agentId and
requestId before acquisition, then separately retains actually acknowledged IDs.
Creation has no initialPrompt. Snapshot/process proof precedes the only send, and
supported messageId is retained before that effect. Uncertain creation/inspection
keeps requested readback IDs and acknowledged workspace/agent IDs without a retry.
UNKNOWN preserves inspection state and never automatically resends. Failed inspect
is not absence: only the exact Docker no-such-object diagnostic qualifies absence
before creation; generic permission/transport errors block. Work device/inode and
nonce are rechecked before exec/deletion. Current bridge-network properties,
endpoint membership and the container's acquired NetworkID are checked before
exec. Failed removal/uncertain cleanup is explicit (`cleanup=INCOMPLETE`) and
cannot coexist with complete PASS or `real_validation_satisfied=true`.

**Remaining ownership gap:** source-faithful collision/race/partial/uncertain
acquisition and cleanup verification is not complete. In particular uncertain
creation without an acquired ID retains locators but still needs bounded exact
readback/reconciliation coverage; no blind retry is permitted. Unverified/replaced
resources and possibly mounted work are preserved.

## Synthetic verification

Tests must isolate real Paseo/Pi/Docker/provider resolution and use only disposable
synthetic secrets and localhost/fake transports. Compile or AST-check exact shipped
programs; use a disposable `PYTHONPYCACHEPREFIX` for explicit py_compile. Strong
acceptance coverage must execute exact shipped argv/internal plumbing with only
candidate namespace paths translated, use actual producers with external effects
faked, and use a separate fake daemon selecting/spawning actual fake Pi. The current runtime fixture replaces the old full-validator runtime success path;
legacy hand-authored producer inputs still do not satisfy producer provenance.
No synthetic success is evidence of real fixed-max availability. Do not equate
passing unit counts or a fake-tested real branch with full Card acceptance.

`test_m07_t05_transport_qualification.py` uses the actual pinned official
ExtensionRunner, Agent and OpenAI Responses implementation with an in-memory
fake fetch for every request and no auth-store resolution. The throw-only
negative control reaches fake fetch; the shipped observer's supported abort
prevents even fake fetch despite the runner catching the error. Missing-signal
and broken-abort controls instead exit the opted-in child with 42 before the
fake-transport entry marker; the throw-only control proves that marker reachable.
Unprivate/symlink witness controls abort without altering their targets. Separate
supported-context diagnostics reject codex-lb/max and meta/xhigh when payload
labels say max. These are synthetic source qualifications, **not** real inference,
full daemon/agent/workspace proof or a general impossibility verdict. The known
pinned max-null boundary is not used to waive the remaining remediable Card work.
