# M07-T05 candidate validator — supported interfaces, provenance, limitations

Status: implementation (synthetic/local fixtures only; real gate unsatisfied).
Authority: `requirements/PASEO_UPDATE_DISTRIBUTION.md` R2,
`decisions/ADR-PUD-004`, approved P4 M07-T05, selective contract
`contracts/PASEO_R2_CANDIDATE_VALIDATION.md`. This document is product
delivery documentation, not a workflow result or review verdict.

## Supported realization (candidate-local guarded CLI)

The bounded Muse adapter invokes the repository-delivered canonical guard
`config/pi-agent/bin/run-llm-test.sh` from the disposable candidate's own
environment using its own local Paseo daemon/home. No guard modification
was required for M07-T05; the shipped guard bytes are used verbatim.

- Guard: `config/pi-agent/bin/run-llm-test.sh`
  (`sha256:7fd922da42fcebfb6ed9e83f1f3471ed5365ea7961bec2ca25cdc9fd62827e33`,
  mode `0755`). Fixed `meta/muse-spark-1.3-contributor` / `max`, no
  fallback, `gpt-6-astra` forbidden. Invocation shapes only
  `PROMPT [CWD]` and `--native-create-agent-args`. No `--model`,
  `--thinking`, or fallback flags are offered.
- Policy: `config/pi-agent/policies/llm-test-policy.json`
  (`sha256:943ba67c3b23ca3d40f745ed4c4f653964898a460b94ec83c3cc7aebeec01d40`).
  Fixed profile `meta` / `muse-spark-1.3-contributor` / `max`,
  `fallback_allowed: false`, `forbidden_models` includes `gpt-6-astra`.
- Paseo: `0.9.2` (`ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
  Supported selectors are global `--home <path>` / `--host <endpoint>`
  and `run --provider/--model/--thinking/--cwd/--wait-timeout`. Help text
  and arguments are interface metadata only; they do not prove execution
  binding or effective profile. The adapter proves binding by resolving
  the invoked `paseo` executable only through the explicitly bound
  candidate bindir, observing `paseo status --home <candidate>` home /
  endpoint / pid / version, and rejecting ambient production homes
  (`~/.paseo`, `/home/paseo/.paseo`, production appdata home).
- Pi: `0.87.1` (`@earendil-works/pi-coding-agent@0.87.1`,
  `dist.integrity sha512-m8ArJUtVcQMSe1lLE/Ei7vX/JV7O39sWmWBsXV2NOU70F0qCp8GubA24pT3LnwTmM6LL2xV80/h6sQg85n69ew==`).
  The invoked `pi` executable must resolve through the same candidate
  bindir; version must equal the pin. `pi --help` thinking levels and
  catalog metadata are not capability proof.
- Native alternative: `--native-create-agent-args` emits only
  `provider: pi/meta/muse-spark-1.3-contributor`,
  `settings.thinkingOptionId: max`, `notifyOnFinish: true`. It is allowed
  only with the same independently proven disposable caller/child binding
  (caller daemon is the candidate daemon; child inherits the caller
  workspace; model/contribution/parent read back through normal lifecycle
  tools). A child of the active production daemon is never candidate smoke.
  Workflow workers are not test evidence.
- Docker: `docker buildx imagetools inspect`, `image pull/inspect`
  (including `RepoDigests` mapping readback), `network inspect/create/rm`,
  `run`, `inspect`, `exec`, `rm`. No socket mount, no production HOME,
  no host key is ever attached to the candidate.

A narrow guard extension preserving the same fixed profile and no
fallback remains permitted by the contract but was not adopted here; any
future extension changes the companion identity below and must propagate
through the existing prepare/build/package path, never attaching modified
HOME to an old eligible digest.

## Provenance (recomputed, not declared)

- Candidate: `sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69`
  (Paseo `0.9.2`, Pi `0.87.1`, parent
  `ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136`).
- Companion bundle: `config/pi-agent` (10 files, `bin/*→0755` else `0644`),
  `source_digest sha256:a51036c56f67012758457ade0c01770e355767ce566cc2fd9e2a84a9cc437119`.
  Recomputed via the installer's own `safe_files`/`managed_mode`/
  `digest_source`; the validator re-verifies the staged payload and the
  declared digest before any external action. Unchanged from the M07-T04
  baseline; no new artifact is claimed.
- Upstream negative facts (explicit, not waived): pinned Contributor
  `thinkingLevelMap.max=null`; unmodified `max→xhigh` clamp in installed
  `pi-ai@0.87.1 dist/models.js`. No metadata override, ordinary workflow
  return, catalog label, or launcher arguments prove real `max`. Fixture
  machinery cannot waive this gate.

## Codex-LB non-inference checks (no prompt, no inference endpoint)

- `GET {base}/models` with `Authorization: Bearer <dedicated-key>`,
  `Accept: application/json`. Requires `200`, OpenAI-compatible
  `{object, data[]}` with non-empty valid ids. `401/403` → auth-denied
  FAIL; unreachable/timeout → BLOCKED; malformed/empty/unexpected status
  → FAIL. Only ids/count retained; bodies never persisted.
- `GET {root}/health` without auth (`root` is `base` minus `/v1`).
  Requires `200` with `{status: ok|healthy|ready|up}` (case-insensitive).
  Same proportional classification.
- Forbidden: `POST` or `GET` to `/responses`, `/chat/completions`,
  `/completions`, `/embeddings`, or any URL containing those substrings;
  sending a prompt or selecting another model as a real test. The validator
  asserts absence of those substrings in every exec payload and every test
  asserts no such call occurred before cleanup.
- Transport uses in-memory headers (urllib inside the helper; `curl` with
  header args only inside the disposable candidate, never a token-bearing
  argv on the host). Failures are sanitized to ≤300-char single-line
  messages with bearer/key shapes redacted.

## Dedicated secret plumbing (procedure only, no admission now)

Only dedicated operator-controlled validation input is permitted, supplied
after all independent machinery is GREEN (M08-T01 scope, not this Card).
Supported mechanisms: private local file read as `CODEX_LB_API_KEY=<value>`
or a bare key (single line, no whitespace), mounted read-only at
`/run/secrets/pi-unraid-codex-lb` (`:ro`), plus provider-side restrictions
where available. Human participation is preserved for account choice and
device flow; provider availability is an operator input, not inferred from
public metadata.

Enforced now in source and fixtures:

- Regular file, not a symlink; mode `0600`/`0400` (any group/other bit
  fails closed); single entry; value non-empty, no whitespace, ≤4096 chars.
- Mounted `:ro` exactly once; `User` is `99:100`; network is the disposable
  validator network; no `/var/run/docker.sock`, no production HOME, no
  `UNRAID_API`/`CODEX_LB_SECRET`/`GITHUB_TOKEN` in the container env.
- No raw `--env KEY=value` with a secret value, no token-bearing argv, no
  auth export, no debug trace, no provider-output echo, no credential in
  CI/image/Git/evidence/logs. Nonsecret config env (`PI_CODEX_LB_BASE_URL`,
  `PI_CODEX_LB_MODEL`, `TZ`, `HOME`, `PASEO_HOME`) remains allowed.
- Only synthetic fixture keys in disposable temp files are supplied in
  tests. Subprocess tails are truncated to ≤600 chars and redacted before
  being placed in reasons; result JSON is scanned for fixture tokens in
  tests.

OAuth/device-flow and account-choice UX remain manual operator steps; no
automated credential request or admission occurs in M07-T05.

## Disposable ownership and cleanup

Candidate code receives no production Docker socket, host administration
key, live production HOME, or ordinary credentials. The validator checks
exact `UID:GID`, mount sources/destinations/modes, network, and actual
image identity.

Cleanup removes only objects whose creation/acquisition and current
ownership are verified for this attempt:

- Container: created by this attempt (`docker run` succeeded) AND current
  `docker inspect` still shows disposable mounts under this attempt's work
  root plus the expected network. Preexisting same-name objects, foreign
  mounts, or changed ownership are preserved, never `rm -f`.
- Work dir: under the configured `state_root` with `candidate-*` prefix.
- Network: only if this attempt created it (`inspect` missed before `create`).
- Creation failure, collision, partial setup, and interruption preserve
  unrelated objects and private operator inputs; uncertain ownership is
  re-read before any removal. No global cache/HOME deletion, no broad
  state-root wipe, no production removal.

## Outcome interface and trust

Machine-readable validator output (`schema_version: 2`):

- `execution_class`: `fixture` (this Card), `rehearsal`, or `real`.
- `status`: `PASS` (mechanical), `FAIL`, `BLOCKED`, or `UNKNOWN`;
  `terminal_class`: `terminal`, `pending`, or `unknown`.
- `subject`: typed binding (`repository`, `expected_digest`,
  `observed_image_id`, `companion_bundle`, `policy_identity`,
  `launcher_identity`, `daemon_binding`, `pi_binding`).
- `checks`: explicit per-required-check outcomes
  (`registry_digest`, `image_mapping`, `companion_binding`,
  `policy_binding`, `uid_gid`, `mount_isolation`, `network_isolation`,
  `secret_isolation`, `runtime`, `codex_catalog`, `codex_auth`,
  `codex_health`, `codex_no_inference`, `muse_effective_profile`, …).
- `real_validation_satisfied`: always `false` for `fixture`/`rehearsal`.
  Real success would require completed guarded inference, observed exact
  effective fixed profile, candidate/daemon/Pi/policy binding, and
  successful required non-inference checks. Missing/unsupported/pending/
  uncertain/timeout/negative/mismatch never satisfies it. An
  execution-mode flag, generic `PASS`, expected launch arguments, catalog
  override, or ordinary workflow return cannot manufacture real evidence.
- On timeout/unknown occurrence the validator retains `UNKNOWN` with a
  bounded owned reference for later inspection and never replays the prompt
  automatically. Raw prompts, response bodies, tokens, pairing offers, and
  credential-bearing URLs are never emitted.

The existing trusted Tower final-gate consumer (M07-T06) must verify the
complete required gates, current baseline, and exact bindings; this report
alone grants no eligibility. No second promotion writer or ledger is
introduced here.

## Remaining real-gate limitations (not satisfied by fixtures)

- Effective `max` on the direct-Meta path is unobservable with the pinned
  bundle (Contributor `max:null` + `max→xhigh` clamp). A supported
  configuration fragment, if ever adopted, would be secret-free, frozen,
  and merge-safe provenance/request delivery only — never capability proof.
  Unsupported/unobservable effective `max` fails closed to
  Research/Planning (owner M08-T01 after autonomous machinery/rehearsal).
  No fallback, downgraded level, unofficial provider, or direct
  provider-call bypass is adopted.
- Real inference, dedicated credential admission, candidate-local daemon
  bring-up, and exact-candidate wire/inference proof belong to M08-T01.
  Fixture dispatch observed in this Card (fake `paseo` records
  `meta/muse-spark-1.3-contributor` + `max`) proves the dispatch path is
  observable, not that real inference occurred.
- A changed candidate or companion requires a new immutable build identity
  and exact affected-gate evidence (M07-T07 scope); the old digest gains no
  eligibility from this validator.
- `paseo status`/`daemon`/`provider` lifecycle readback for a real
  candidate daemon, real `pi --version` inside the candidate image, and
  real Codex-LB `GET /v1/models` + `GET /health` against operator-supplied
  endpoints remain to be exercised with real credentials in the disposable
  boundary. Until then the real gate stays unsatisfied by construction.\n
## Correction (2026-10-04) — Main return-validation A-E + seven probes

This section is appended by the fresh implementation/repair context. It does
not replace the above; old bytes remain in Git history. It distinguishes
implemented machinery, synthetic mechanics, and unverified later real outcome.

### What was incomplete and is now corrected

- **A. Actual candidate-local Muse path is now integrated in the Tower
  validator/CLI** (`scripts/paseo_tower_validator.validate` calls
  `scripts/paseo_candidate_muse_adapter` strict validators + stages +
  candidate-local readback via `docker exec`). `run_guard_dispatch` is no
  longer an unused helper: the validator stages the exact guard/policy into
  `work/home/.pi/agent`, reads back `sha256sum` + `cat` + `--native-create-agent-args`
  inside the candidate, and classifies effective profile via the adapter.
  Fixture/rehearsal still leaves `real_validation_satisfied=false`; missing/
  malformed/mutated/unverifiable binding, unsupported profile, and
  negative/pending/timeout/unknown fail closed without replay/fallback.
  No real inference is RUN in M07-T05; only the dormant-until-authorized
  implementation exists. M08-T01 owns actual real observations/admission.
- **B. Frozen artifact/runtime binding is now strict.** The validator consumes
  the existing `config/paseo-candidate.json` handoff when `--candidate-file`
  is supplied (expected Paseo/Pi versions derive from the frozen candidate,
  not host pins; `version_source` records provenance). Companion/policy/
  launcher are recomputed via `paseo_candidate_build` + staged/applied/read
  back inside the candidate. Running `Image` must equal the pulled local
  image ID; `RepoDigests` absent now FAILs (was SKIP+PASS). Omission/
  malformed/mutated/mismatched input at the real entrypoint fails closed.
  No re-resolution/build/publication or new pipeline/ledger was introduced;
  companion digest remains `sha256:a51036c5…` (guard unchanged).
- **C. One reachable Codex non-inference path.** The Tower path now uses the
  robust Python payload (not shell `curl` + `node`): secret file read
  in-memory (never on argv), strict URL/model/secret validation via
  `paseo_codex_noninference`, bounded 256KiB bodies (never persisted as
  evidence), redirect validation (no inference traversal, no cross-host auth
  forward), and fixed secret-safe errors (no arbitrary tails). Fixed invalid
  `curl -w '%{{http_code}}'` placeholder (was never formatted; now no `curl`
  in the candidate path), token-bearing `Bearer $key` argv (now header dict
  in-memory), world-readable `/tmp/codex-*.json` bodies (now in-memory only),
  weak URL/secret checks (now strict helper), redirect auth forwarding (now
  validated/stripped), and SKIP-as-PASS (now honest FAIL/BLOCKED/SKIP with
  real gate unsatisfied). Dedicated Muse (`/run/secrets/pi-unraid-muse`,
  `MUSE_SPARK_API_KEY=`, private file, `:ro` mount, never argv) and Codex
  (`/run/secrets/pi-unraid-codex-lb`) plumbing both exist; only synthetic
  credentials in disposable fixtures are used now.
- **D. Immutable acquisition/ownership + UNKNOWN preservation.** Container
  ownership now requires exact canonical mounts/modes (work homes `rw` under
  `work`, secrets `:ro` at exact targets, no extras), exact network, running
  image match, and attempt-nonce label (`io.pi-unraid.validator-nonce`).
  A foreign secret-only mount is NOT owned (was `true`). No `rm` occurs
  before own `create` for foreign objects; creation records the container ID
  and verifies it on readback (replacement detection). Networks are never
  reused production: preexisting non-empty/foreign networks fail closed.
  Work requires `.attempt-nonce` + `candidate-*` under `state_root` (no
  prefix-only). `run` timeout now raises `ValidationUnknown` (was generic
  BLOCKED); UNKNOWN preserves work + container + `owned_reference` for
  bounded readback and never replays; cleanup skips UNKNOWN removals and
  re-reads network ownership before removal. No global cache/HOME or broad
  state-root deletion.
- **E. False-positive coverage replaced.** New `MainSevenProbesTests` (10
  tests) exercise the genuine validator/adapter entrypoints with fake-only
  boundaries and assert required failure + absence of disallowed calls BEFORE
  cleanup: real-mode missing → BLOCKED/FAIL; foreign daemon/Pi + caller max →
  FAIL; wrong running image → FAIL; absent RepoDigests → FAIL; foreign
  secret-only → preserved (0 run/rm); opaque token echo → redacted; missing
  policy → AdapterBlocked (no fabrication); redirects/parsers/timeout/
  candidate-file versions/Muse secret all covered. Positive synthetic dispatch
  observes real guard bytes through the integrated product path
  (`--native-create-agent-args` shape + `meta/muse-spark-1.3-contributor/max`
  marker via fake `paseo`); negatives assert failure + no inference.

### Supported source-lead qualification (not proof)

- Installed `pi-coding-agent@0.87.1` (`pi-ai@0.87.1`) declares
  `before_provider_request` / `after_provider_response` in
  `dist/core/sdk.js` + `dist/core/extensions/types.d.ts`, wired via
  `onPayload` / `onResponse` in compat chunks (`openai-responses`,
  `azure-openai-responses`, `pi-messages`). They fire ONLY when a test-owned
  extension registers a handler; without a handler nothing is observed. They
  do NOT prove on-wire max and are not used as proof here.
- Pinned `meta.json`: `muse-spark-1.3-contributor` `thinkingLevelMap.max=null`
  (unsupported), `muse-spark-1.3` `max=max`. `clampThinkingLevel(max)` on the
  contributor therefore downgrades `max→xhigh` (`pi-ai/dist/models.js`). A
  metadata label, requested `max` flag, or ordinary workflow return is not
  effective-max proof. The staged witness extension
  (`write_effective_witness_extension`) records ONLY nonsecret
  `provider/model/thinking/status/count`; raw headers/body/prompt/tokens are
  never recorded. Absent/unknown witness stays UNKNOWN and fails closed to
  M08-T01/Research-Planning; no observer, flags, or unofficial provider were
  invented. Whitelist: `EFFECTIVE_WITNESS_ALLOWLIST`.
- Pinned Contributor `max-null` + unmodified `max→xhigh` clamp remain negative
  facts, not a proved general impossibility. If supported realization
  genuinely cannot be established for real max, the precise unsupported
  boundary returns to Main for proportional Research/Planning (owner M08-T01
  after autonomous machinery/rehearsal).

### Provenance / counts / exits (synthetic only)

- Targeted: `tests.test_paseo_tower_validator` + `tests.test_m07_t05_validator_adapter`
  → 51 tests OK (41 preserved + 10 new probes), exit 0, 0 skips.
- Affected: guarded-policy/instruction-plane/companion/build/runtime (8 modules)
  → 72 tests OK, exit 0.
- Full: `discover -s tests` → 604 tests OK (594 + 10 new), exit 0, 0 skips.
- Node: `codex_lb_dynamic_model_catalog_core_test.mjs` → GREEN, exit 0.
- Companion digest recomputed `sha256:a51036c5…` (unchanged); guard/policy
  bytes verbatim; no image build/publication, CI, PR/Issue, push, live action.
- All execution fake-only (`PATH` isolated to test bindirs, mocked Docker,
  injected HTTP, synthetic credentials); no real inference/credential/HOME/
  Tower/image action. Worker inference is not candidate smoke evidence.

### Remaining real-gate limitations (not waived)

- Effective `max` on the direct-Meta contributor path remains unobservable
  with the pinned bundle; fixtures always leave `real_validation_satisfied=false`.
  Real guarded inference with observed exact effective `max`, candidate/
  daemon/Pi/policy binding, and successful required non-inference checks
  belongs to M08-T01 after autonomous machinery/rehearsal + dedicated
  credential admission. No fallback, downgraded level, unofficial provider,
  or direct provider bypass is adopted.
- Real candidate-local daemon bring-up, real `pi --version`/provider path
  inside the candidate image, real Codex-LB `GET /v1/models` + `GET /health`
  against operator endpoints, and real witness-observed effective `max`
  remain to be exercised with dedicated credentials in the disposable boundary.
- A changed candidate/companion requires a new immutable build identity + exact
  affected-gate evidence (M07-T07); old digests gain no eligibility here.
  M07-T06/M08 work is excluded. No eligibility/production authorization claimed.
