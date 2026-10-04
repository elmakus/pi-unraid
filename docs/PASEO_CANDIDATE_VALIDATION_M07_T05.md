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
  boundary. Until then the real gate stays unsatisfied by construction.
