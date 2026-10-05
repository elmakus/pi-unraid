# Candidate validation machinery (M07-T05)

## Status and boundaries

This document describes the current implementation subject, **not** an accepted
Card result, independent review or real validation. Main owns acceptance
classification and workflow reconciliation. Historical repair
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
snapshot workspaceId/cwd/provider/actual runtimeInfo.model/effective thinking
(with no fallback to requested model), parent process
Node identity, /proc process start times and selected executable argv/bytes before
sending. CLI inspect does **not** expose workspaceId; no automatic workspace env
is invented. Private config/reference inode changes fail closed.

The separate external CLI/daemon/Pi fixture now executes the same validator,
guard, loader, bridge, wrapper and observer path (namespace path translation only).
Its daemon selects/spawns a separate fake Pi via the actual pinned buildPiLaunch;
the fake Pi derives selected state from the exact launch argv. The genuine-validator
fixture translates the mounted dedicated-input pointer to that same synthetic
file, never substitutes another credential value. No provider/auth resolver is imported. Actual processes/IDs, rather than canned
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
by the observer before transport. Requested workspaces use the pinned protocol's
`wks_` plus 16 lowercase hex format, independently from UUID agent/request/message
IDs. The external fixture executes the actual pinned DaemonClient, CreationClient
and inbound/outbound protocol parsers; only its request transport is fake. Actual
client selectors reject unrelated receipt requestIds. Connected server-info is
received from the separate daemon socket and parsed by the pinned protocol,
not copied from the expected local status file; subsequent server replacement
updates are exercised before and after the single prompt. Reconnect is disabled
as in the pinned CLI connection implementation, so uncertainty cannot cause an
automatic request replay. Synthetic snapshot neutral
fields do not qualify inference: model/thinking/streaming come from the separately
selected Pi process, while the shipped observer's single correlated completed
exchange remains mandatory. Only one provider exchange is admitted because
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

### Applied-payload interval (continuing producing contribution)

Checkout/source verification is distinct from verification of what the candidate
actually uses. The disposable container now has a separately verified, exact
`/home/paseo/.pi/agent` source→destination **read-only bind** over its otherwise
writable private HOME. Every execution and removal ownership check requires that
bind; a missing, swapped, writable or type-confused mount fails closed. No
upstream startup or healthcheck precedes staging/interval establishment.

Tower retains the complete expected public manifest and private daemon configuration
in its own trusted invocation, independently of writable candidate inputs. It
launches the observer **before initial applied readbacks** using source-frozen
Python `-c` instructions; the acquired child receives the same frozen instructions
and expectations in `-c`, never an applied script/import or a manifest-as-authority.
Startup, child and source-frozen clients use Python `-I -S -B`: no writable-cwd,
PYTHONPATH, user-site or site-customization code, and no bytecode writes. The public
child source is compressed only to bound exec argument size, then executed from
memory with the same isolation; no intermediate writable code file is trusted.
The delivered `bin/m07-t05-applied.py` remains a watched payload member and client,
not a trusted executable startup path. Its ordinary start/serve modes fail closed.
The exclusive private manifest must exactly match independently retained source
content/modes/set/nonce, and private daemon configuration must match the fixed
source-owned configuration. Neither a returned self-hash nor process credentials
can qualify substituted instructions/expectations. It compares actual bytes,
file/directory sets, regular-file types, modes and inode/ctime/mtime identities.
Linux inotify watches members, directories and the root parent before the initial
snapshot. The manifest/configuration files and their parent entries are also
watched and identity-checked; unrelated runtime bookkeeping in their parent
directories is not treated as payload drift. Modification, replacement, chmod,
omission, addition, move, unmount,
watch loss or overflow irreversibly invalidates the interval, including a write
followed by restoration. It watches actual execution files, not another checkout.

The original non-inference observer stays alive independently of later applied
helper bytes. Source-frozen host client code checks `/proc` start identity and
Unix `SO_PEERCRED`, pins the original acquired reference/nonce and reads its fresh
kernel-backed observation at startup, after catalog, immediately before owned
dispatch, after runtime return and at final completion. The manifest identity in
the returned reference is compared to the independently computed host identity;
it is not the authority for startup. Frozen executing code first validates the
actual manifest/configuration and full payload, installs kernel watches, snapshots
and drains pending events before publishing its acquired reference. Modified
expectations or checker bytes cannot requalify drift. Reads-to-acquisition-to-
dispatch-to-request-to-completion remain inside that one observed interval.
A copied digest, private reference replacement or caller PASS is not acceptance.
The bridge checks the interval before native metadata export, at creation and
inspection boundaries, before the one message and after completion. The selected
Pi wrapper checks before exec; the observer checks before provider transport and
completion observations, retaining its existing abort/fail-stop semantics.
Later uncertainty preserves API IDs/private references and leaves the real gate
false, without message replay or unproven resource removal.

This is runtime interval machinery, not another workflow state store, eligibility
ledger or pipeline. The new delivery member and changed bridge/wrapper/observer
bytes naturally change the existing prepare/build/package companion declaration;
old artifacts cannot qualify the changed payload. `m07-t05-applied.py` only
observes Linux files/process metadata and a private Unix socket: frozen startup
and delivered check/stop entrypoints do not cause inference. Tower validation, owned bridge, selected Pi
exec and provider observer remain inference-capable paths and may only be tested
through complete external fakes and disposable synthetic inputs here.

The genuine Tower fixture now uses **one mounted applied tree** for both actual
shipped-program execution and interval observation, instead of a separate
unobserved six-file executable copy. Public content and private path strings are
translated only for the synthetic namespace; no expected success/hash is
manufactured by the fake. The interval algorithm, hashing, kernel watch and peer
checks run unchanged. Synthetic positive real-branch flags remain mechanical
coverage only, never evidence that real fixed-max validation is supported.
The prepared envelope now additionally records the immutable Git commit/tree
and every source file's content/executable-mode identity, plus the exact staged
transformation (only Dockerfile/candidate replacement). Preparation verifies HEAD,
its single discovery parent and ancestor relationship to the declared discovery
branch using read-only Git with replacement objects/ambient Git selectors disabled.
Untracked/ignored extra inputs, symlinks, missing files and changed configuration
are rejected. Buildx verifies the actual staged file set before external build
and retains the prepared snapshot and executed command configuration. Tower
reconstructs prepare/readback and Buildx argv/phase/smoke aggregation, verifies the
executing validation programs, then rereads source/evidence/archive before guarded
dispatch. Non-Git compatibility fixtures remain explicitly unbound and cannot
satisfy the real source gate.

Tower hashes the actual preserved `image.tar` beside the tested evidence, checks
both tested/publication byte links, and inspects docker-save without extracting.
The single manifest must link the tested tag, regular config/layer members and a
configuration whose actual bytes hash to the distinct local image ID. Each actual
uncompressed layer tar must be structurally readable and hash to its linked
rootfs diff-ID. No archive filesystem content is extracted. Pulled runtime Config
must equal that preserved configuration. Publication candidate_ref
must be the publisher-derived `repository:candidate-<full candidate hash>`, never
an arbitrary alias. Real mode requires this proof; omitted archive/source/config
is not success. Fresh downstream artifacts remain required; changed delivery
cannot bless an old digest.

`tests/m07_t05_producer_fixture.py` now reaches actual resolver facts freeze,
handoff.prepare, prepare/readback, Buildx parser/cmd_build/internal smoke dispatch
and aggregation, package hash/format verification, and publisher. Only process,
Docker and registry effects are fake; image save creates synthetic config/layer
bytes for genuine hashing. The resulting unchanged files feed actual Tower
validation and its shipped candidate programs. Negative controls deliberately
mutate and relink evidence to challenge the substantive proofs, not only hashes.

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

Reachable external-fake controls cover supported snapshot omissions/types,
wrong/changed connected server, daemon-selected Pi/auth/ambient bindings,
private config/reference/process-proof replacement/collision, uncertain creation,
lost prompt receipt and post-effect inspection. Network/container acquisition
receipt loss is UNKNOWN with requested names/nonce/private references retained;
no retry or unproven removal follows. Mount RW must be actual booleans (numeric
0/1 cannot prove isolation). Cleanup rejects in-use/foreign/replaced networks,
preserves work and private usable nonce/object references until every external
removal succeeds, and reports failed/unavailable cleanup as unsatisfied rather
than orphaning its references. These observations are synthetic/local; they do
not grant live cleanup or credential authority.

## Synthetic verification

Tests must isolate real Paseo/Pi/Docker/provider resolution and use only disposable
synthetic secrets and localhost/fake transports. Compile or AST-check exact shipped
programs; use a disposable `PYTHONPYCACHEPREFIX` for explicit py_compile. Strong
acceptance coverage must execute exact shipped argv/internal plumbing with only
candidate namespace paths translated, use actual producers with external effects
faked, and use a separate fake daemon selecting/spawning actual fake Pi. The current runtime fixture replaces the old full-validator runtime success path;
the current full-validator producer inputs come from the actual producer fixture.
Legacy hand-authored inputs, where retained as low-level negative data, do not
satisfy the real source gate.
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
