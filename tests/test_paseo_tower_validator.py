"""Genuine Tower validator tests (M07-T05 coherent rewrite).

Classification: every inference-capable entrypoint is exercised ONLY via
fake-only boundaries with executable-resolution/transport isolation so a
real test inference can NEVER occur:
- Docker CLI: mocked ``V.run``/``V.shutil.which``/``V.os.chown`` (no daemon).
- Paseo/Pi lifecycle: canned ``docker exec`` outputs for ``paseo status``,
  ``pi --version`` (fake daemon boundary, parsed+validated for real).
- Codex transport: the ACTUAL staged ``paseo_codex_candidate_check.py``
  is compiled and executed locally via subprocess against a local
  ``http.server`` fixture on 127.0.0.1 (synthetic secret files only).
- Muse dispatch: the ACTUAL staged guard PROMPT form is executed locally
  with ``PATH`` isolated to a test-owned bindir holding a fake ``paseo``
  (records dispatch + witness, never calls a provider).
- No real inference, provider auth/admission, ordinary-credential reads,
  HOME/runtime mutation, live Docker/Tower, image build, or CI occurs.

The fake ``docker exec`` exercises actual program logic (staged file
execution, real hash computation, real guard gates) — never
marker-to-returncode success. Negatives assert required failure AND
absence of disallowed calls BEFORE cleanup (recorded calls list).
"""
from __future__ import annotations

import http.server
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_tower_validator.py"
spec = importlib.util.spec_from_file_location("paseo_tower_validator", SCRIPT)
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

ADAP_SPEC = importlib.util.spec_from_file_location(
    "paseo_candidate_muse_adapter_t", ROOT / "scripts" / "paseo_candidate_muse_adapter.py")
A = importlib.util.module_from_spec(ADAP_SPEC)
ADAP_SPEC.loader.exec_module(A)

REAL_CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text(encoding="utf-8"))
# DISTINCT TYPES (publisher schema): candidate_id is the resolver's component-
# resolution identity; the OCI digest is the registry manifest identity.
# scripts/paseo_candidate_publish.py outputs both separately — equating them
# is a type error. Fixtures use the REAL candidate bytes (real candidate_id)
# with a clearly synthetic OCI digest.
REAL_CANDIDATE_ID = REAL_CANDIDATE["candidate_id"]
REAL_OCI_DIGEST = "sha256:" + "d" * 64
REAL_REPOSITORY = "ghcr.io/elmakus/pi-unraid"
REAL_PASEO = REAL_CANDIDATE["components"]["paseo"]["version"]
REAL_PI = REAL_CANDIDATE["components"]["pi"]["version"]


def _companion_bundle():
    bspec = importlib.util.spec_from_file_location(
        "paseo_candidate_build_t", ROOT / "scripts" / "paseo_candidate_build.py")
    bm = importlib.util.module_from_spec(bspec)
    bspec.loader.exec_module(bm)
    ident = bm.companion_bundle_identity(ROOT)
    return ident


def _companion_arg():
    c = dict(REAL_COMPANION)
    return c


REAL_COMPANION = _companion_bundle()


class LocalCodexServer:
    """Local http.server fixture (127.0.0.1 only) for the check program."""

    def __init__(self, *, mode="ok"):
        self.mode = mode  # ok|auth-denied|malformed|empty|redirect-inference
        self.httpd = None
        self.thread = None
        self.port = None

    def __enter__(self):
        parent = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path == "/v1/models":
                    if parent.mode == "auth-denied":
                        self.send_response(401)
                        self.end_headers()
                        return
                    if parent.mode == "malformed":
                        body = b'{"data":'
                    elif parent.mode == "empty":
                        body = json.dumps({"object": "list", "data": []}).encode()
                    elif parent.mode == "redirect-inference":
                        self.send_response(302)
                        self.send_header("Location", "/v1/responses")
                        self.end_headers()
                        return
                    else:
                        body = json.dumps({"object": "list", "data": [
                            {"id": "fixture-model", "object": "model"},
                            {"id": "m", "object": "model"}]}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if self.path == "/health":
                    body = json.dumps({"status": "ok"}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(404)
                self.end_headers()

        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        self.port = sock.getsockname()[1]
        sock.close()
        self.httpd = http.server.HTTPServer(("127.0.0.1", self.port), H)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *a):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
        return False

    @property
    def base(self):
        return f"http://127.0.0.1:{self.port}/v1"


def make_fake_paseo(bindir: Path, *, effort="max", response_status="200",
                    dispatch=True):
    """Test-owned fake paseo CLI: source-faithful argv parsing, never infers.

    Faithful to pinned Paseo 0.9.2 ``run.js`` ``parseKeyValueFlags``: only
    ``--env K=V`` / ``--env=K=V`` pairs (first-``=`` split) constitute
    transmitted agent env; the ambient CLI process environment is NEVER
    consulted for agent delivery (``M07_T05_*``/``META_API_KEY`` ambient
    values are ignored, exactly like the real daemon boundary). ``run``
    requires loader-delivered ``META_API_KEY`` (real shell inheritance,
    as in the candidate container) plus transmitted correlation/pointer
    names; otherwise exit 42/3 with no dispatch. Records full argv to
    ``DISPATCH_MARKER`` so tests assert the transmitted ``--env`` contract.
    Writes NOTHING to any witness file: all witness bytes flow through the
    actual staged observer under node (see ``_emit_full_sequence``).
    """
    bindir.mkdir(parents=True, exist_ok=True)
    for tool in ("dirname", "jq", "bash", "sh", "sha256sum", "cat", "command"):
        tgt = shutil.which(tool)
        if tgt and not (bindir / tool).exists():
            try:
                os.symlink(tgt, bindir / tool)
            except OSError:
                pass
    fake = bindir / "paseo"
    fake.write_text(
        "#!/bin/sh\n"
        "# Source-faithful subset of pinned run.js parseKeyValueFlags:\n"
        "# first-equals split; `--env K=V` and `--env=K=V` forms.\n"
        "# Ambient CLI env is NEVER consulted for agent delivery.\n"
        "T_ID=\"\"\n"
        "T_WIT=\"\"\n"
        "T_PTR=\"\"\n"
        "T_PREV=\"\"\n"
        "for _a in \"$@\"; do\n"
        "  if [ \"$T_PREV\" = \"--env\" ]; then _kv=\"$_a\"; T_PREV=\"\"\n"
        "  elif [ \"$_a\" = \"--env\" ]; then T_PREV=\"--env\"; continue\n"
        "  else case \"$_a\" in --env=*) _kv=\"${_a#--env=}\" ;; *) T_PREV=\"\"; continue ;; esac\n"
        "  fi\n"
        "  _k=\"${_kv%%=*}\"; _v=\"${_kv#*=}\"\n"
        "  case \"$_k\" in\n"
        "    M07_T05_TEST_ID) T_ID=\"$_v\" ;;\n"
        "    M07_T05_WITNESS_FILE) T_WIT=\"$_v\" ;;\n"
        "    META_API_KEY_FILE) T_PTR=\"$_v\" ;;\n"
        "  esac\n"
        "done\n"
        "if [ \"$1\" = \"status\" ]; then\n"
        "  printf '%s' \"$PASEO_STATUS_JSON\"\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"run\" ]; then\n"
        "  if [ -z \"$META_API_KEY\" ]; then\n"
        "    echo 'fake-paseo: META_API_KEY unavailable' >&2\n"
        "    exit 42\n"
        "  fi\n"
        "  if [ -z \"$T_ID\" ] || [ -z \"$T_PTR\" ]; then\n"
        "    echo 'fake-paseo: correlation/pointer not transmitted via --env' >&2\n"
        "    exit 3\n"
        "  fi\n"
        f"  DISPATCH={1 if dispatch else 0}\n"
        "  if [ \"$DISPATCH\" = \"1\" ]; then\n"
        "    printf '%s\\n' \"$@\" > \"${DISPATCH_MARKER:-/dev/null}\"\n"
        "  fi\n"
        f"  exit {0 if dispatch else 3}\n"
        "fi\n"
        "echo 'fake-paseo: unsupported command' >&2\n"
        "exit 2\n"
    )
    fake.chmod(0o755)
    # Witness profile for the node full-sequence step (read via bindir):
    # the shell fake never writes witness bytes itself.
    (bindir / "fake-profile.json").write_text(json.dumps(
        {"effort": effort, "response_status": response_status}))
    # Fake pi for candidate Pi lifecycle.
    pi = bindir / "pi"
    pi.write_text(f"#!/bin/sh\necho '{REAL_PI}'\n")
    pi.chmod(0o755)
    return bindir


def _find_node():
    """Locate the node executable without shutil.which.

    The validator tests mock shutil.which (docker-CLI isolation); a which-
    based lookup inside the patched context would return the docker stub.
    Scan PATH directly for an executable node binary instead. """
    import os as _os
    seen = []
    for directory in _os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin").split(_os.pathsep):
        candidate = Path(directory) / "node"
        if candidate.is_file() and _os.access(candidate, _os.X_OK):
            return str(candidate)
    for fallback in ("/usr/local/bin/node", "/usr/bin/node"):
        if fallback not in seen and Path(fallback).is_file() and _os.access(fallback, _os.X_OK):
            return fallback
    return None


def _emit_full_sequence_via_observer(*, staged_ext: Path, witness_host: str, test_id: str,
                                     effort: str = "max", response_status: str = "200",
                                     turn_outcome: str | None = "completed",
                                     fire_agent_end: bool = True,
                                     fire_settled: bool = True) -> bool:
    """Emit the FULL provider/turn/settlement sequence through the ACTUAL staged observer.

    Loads the shipped ``m07-t05-witness.js`` bytes under node with a fake SDK
    event boundary that fires the supported sequence — ``before_provider_request``
    (model/effort payload), ``after_provider_response`` (status), ``turn_end``
    (qualified ``outcome``), ``agent_end`` (assistant messages with stopReason),
    ``agent_settled`` (neutral) — using the owned test's correlation env.
    Every witness byte is produced by shipped observer code; the shell fake
    writes none. Parameters let negatives control the sequence (aborted turn,
    malformed response, omitted terminal). Returns True when at least one
    terminal event for test_id was appended.
    """
    node = _find_node()
    if node is None:
        return False
    # This host-side file stands in for the private candidate tmpfs witness;
    # legacy fixtures precreate it, unlike real open(O_CREAT, 0600).
    if Path(witness_host).exists():
        Path(witness_host).chmod(0o600)
    agent_end_arg = "aborted" if turn_outcome in ("aborted", "error") else "stop"
    harness = (
        "import {createRequire} from 'node:module';\n"
        "globalThis.require = createRequire(import.meta.url);\n"
        "const registered = {};\n"
        "const ext = await import(process.argv[1]);\n"
        "ext.default({on: (k, fn) => { registered[k] = fn; }});\n"
        "const cfg = JSON.parse(process.argv[2]);\n"
        "const controller = new AbortController();\n"
        "const ctx = {model: {provider:'meta', id:'muse-spark-1.3-contributor'}, thinkingLevel:cfg.effort, signal:controller.signal, abort:()=>controller.abort()};\n"
        "if (registered.before_provider_request) {\n"
        "  try { await registered.before_provider_request({payload: {model: 'muse-spark-1.3-contributor', reasoning: {effort: cfg.effort}}}, ctx); } catch {}\n"
        "}\n"
        "if (!controller.signal.aborted && registered.after_provider_response) {\n"
        "  await registered.after_provider_response({status: cfg.response, headers: {}});\n"
        "}\n"
        "if (cfg.turn !== null && registered.turn_end) {\n"
        "  await registered.turn_end({outcome: controller.signal.aborted ? 'aborted' : cfg.turn, turnIndex: 0, message: {}, toolResults: []});\n"
        "}\n"
        "if (cfg.agentEnd && registered.agent_end) {\n"
        "  await registered.agent_end({messages: [{role: 'assistant', stopReason: cfg.agentEnd, content: []}]});\n"
        "}\n"
        "if (cfg.settled && registered.agent_settled) { await registered.agent_settled({}); }\n"
    )
    cfg = {"effort": effort, "response": response_status,
           "turn": turn_outcome, "agentEnd": agent_end_arg if fire_agent_end else None,
           "settled": fire_settled}
    try:
        pr = subprocess.run(
            [node, "--input-type=module", "-e", harness, str(staged_ext), json.dumps(cfg)],
            env={"M07_T05_TEST_ID": test_id, "M07_T05_WITNESS_FILE": witness_host,
                 "PATH": "/usr/bin:/bin"},
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if pr.returncode != 0:
        return False
    try:
        lines = Path(witness_host).read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for ln in lines:
        try:
            doc = json.loads(ln)
        except (json.JSONDecodeError, ValueError):
            continue
        if doc.get("test_id") == test_id and doc.get("kind") == "terminal":
            return True
    return False


# Backwards-compatible alias (older probes import this name).
def _emit_terminal_via_observer(*, staged_ext: Path, witness_host: str, test_id: str) -> bool:
    return _emit_full_sequence_via_observer(staged_ext=staged_ext,
                                            witness_host=witness_host, test_id=test_id)


def transmitted_env_names(marker_path: Path) -> list:
    """Parse transmitted --env names from recorded dispatch argv (first-`=` split)."""
    names = []
    try:
        argv = Path(marker_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return names
    prev = None
    for a in argv:
        if prev == "--env":
            kv, prev = a, None
        elif a == "--env":
            prev = "--env"
            continue
        elif a.startswith("--env="):
            kv = a[len("--env="):]
        else:
            prev = None
            continue
        names.append(kv.split("=", 1)[0])
    return names


from tests.m07_t05_producer_fixture import IMAGE_ID, produce, source_root as producer_source_root


def fixture_source(td):
    source = producer_source_root(td)
    return source if source.exists() else ROOT


def build_artifact_chain(td: Path, *, image_id=IMAGE_ID):
    return produce(td, repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST)


def make_fake_docker(*, digest, image_id, calls, state, server_base,
                     codex_secret_host, muse_secret_host,
                     daemon_json=None, pi_version=REAL_PI,
                     paseo_effort="max", witness_terminal="done",
                     break_guard=False, break_image=False):
    """Strict fake Docker where exec runs ACTUAL staged logic locally."""
    image_id = IMAGE_ID
    # Resolver freeze adds stable-line facts; use the actual produced identity
    # observed by this external fake, not the older integrated baseline label.
    from tests.m07_t05_producer_fixture import load as _load_fixture
    _resolver = _load_fixture('external_candidate_metadata', 'scripts/resolve-paseo-candidate.py')
    state.setdefault('candidate_id', _resolver.facts_to_candidate(
        {'components': REAL_CANDIDATE['components']},
        json.loads((ROOT / 'config/environment-capabilities.json').read_bytes()))['candidate_id'])
    def fake(argv, timeout=300, check=True):
        calls.append(argv)
        if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
            return mock.Mock(returncode=0, stdout=f"Digest: {digest}\n", stderr="")
        if argv[:3] == ["docker", "image", "inspect"]:
            if "{{json .RepoDigests}}" in " ".join(argv):
                if state.get("no_repodigests"):
                    return mock.Mock(returncode=0, stdout=json.dumps([]), stderr="")
                return mock.Mock(returncode=0, stdout=json.dumps([f"ghcr.io/elmakus/pi-unraid@{digest}"]), stderr="")
            if "{{json .Config}}" in " ".join(argv):
                if state.get("wrong_image_config"):
                    return mock.Mock(returncode=0, stdout=json.dumps(
                        {"Env": ["PI_UNRAID_PI_VERSION=9.9.9"],
                         "Labels": {"io.pi-unraid.pi-version": "9.9.9"}}), stderr="")
                return mock.Mock(returncode=0, stdout=json.dumps(
                    {"Env": ["PATH=/usr/local/bin:/usr/bin:/bin",
                             f"PI_UNRAID_PI_VERSION={REAL_PI}",
                             "PI_UNRAID_CANDIDATE_ID=" + state.get('candidate_id', REAL_CANDIDATE_ID)],
                     "Labels": {"io.pi-unraid.pi-version": REAL_PI,
                                "io.pi-unraid.candidate-id": state.get('candidate_id', REAL_CANDIDATE_ID)}}), stderr="")
            return mock.Mock(returncode=0, stdout=image_id + "\n", stderr="")
        if argv[:3] == ["docker", "image", "pull"]:
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "network"]:
            if argv[2] == "inspect":
                if not state.get('net_exists', False):
                    return mock.Mock(returncode=1, stdout='',
                                     stderr=f'Error response from daemon: network {argv[-1]} not found')
                import json as _j
                return mock.Mock(returncode=0, stdout=_j.dumps([{
                    "Id": state.get("replaced_network_id") or state.get("acquired_network_id") or "fake-net-id-1",
                    'Driver': 'bridge', 'Scope': 'local', 'Internal': False,
                    'Ingress': False, 'Attachable': False, 'Options': {},
                    'Containers': {'fake-container-id-123': {}} if state.get('ran') else {},
                    "Labels": {"io.pi-unraid.validator-nonce": state["nonce"]}}]), stderr="")
            if argv[2] == "create":
                state["net_exists"] = True
                state["acquired_network_id"] = "fake-net-id-1"
                # record nonce from --label
                for i, x in enumerate(argv):
                    if x == "--label" and i + 1 < len(argv) and argv[i + 1].startswith("io.pi-unraid.validator-nonce="):
                        state["nonce"] = argv[i + 1].split("=", 1)[1]
                return mock.Mock(returncode=0, stdout="fake-net-id-1\n", stderr="")
            if argv[2] == "rm":
                state["net_exists"] = False
                return mock.Mock(returncode=0, stdout="", stderr="")
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "inspect"]:
            if not state.get('ran'):
                return mock.Mock(returncode=1, stdout='', stderr=f'Error: No such object: {argv[-1]}')
            if state.get("inspect_failure"):
                return mock.Mock(returncode=1, stdout="", stderr="synthetic inspect transport failure")
            if state.get("fail_cleanup_inspect") and state.get("dispatch_complete"):
                return mock.Mock(returncode=1, stdout="", stderr="synthetic inspect transport failure")
            run_call = next(x for x in calls if x[:2] == ["docker", "run"])
            mounts = []
            for i, x in enumerate(run_call):
                if x == "-v":
                    parts = run_call[i + 1].split(":")
                    mounts.append({"Type": "bind", "Source": parts[0], "Destination": parts[1],
                                   "RW": (parts[2] if len(parts) > 2 else "rw") != "ro"})
            nonce = state.get("nonce", "unknown")
            img = state.get("wrong_image") or image_id
            cid = state.get("replaced_id") or "fake-container-id-123"
            obj = {"Id": cid, "Image": img,
                   "Config": {"User": "99:100", "Env": ["TZ=Europe/Zurich", "HOME=/home/paseo"],
                              "Labels": {"io.pi-unraid.validator-nonce": nonce}},
                   "HostConfig": {"NetworkMode": state.get("network", "pi-unraid-validator"),
                                  "ReadonlyRootfs": True,
                                  "Tmpfs": {"/tmp": "rw,nosuid,nodev", "/run": "rw,nosuid,nodev"}},
                   'NetworkSettings': {'Networks': {state.get('network', 'pi-unraid-validator'):
                       {'NetworkID': state.get('acquired_network_id')}}},
                   "Mounts": mounts, "State": {"Status": "running", "Health": {"Status": "healthy"}}}
            return mock.Mock(returncode=0, stdout=json.dumps([obj]), stderr="")
        if argv[:2] == ["docker", "run"]:
            state["ran"] = True
            for i, x in enumerate(argv):
                if x == "--label" and i + 1 < len(argv) and argv[i + 1].startswith("io.pi-unraid.validator-nonce="):
                    state["nonce"] = argv[i + 1].split("=", 1)[1]
            # capture work root from first -v (source is <work>/home)
            for i, x in enumerate(argv):
                if x == "-v" and argv[i + 1].endswith(":/home/paseo:rw"):
                    src = argv[i + 1].split(":")[0]
                    state["work"] = src.rsplit("/", 1)[0]
                    state["work_home"] = src
            return mock.Mock(returncode=0, stdout="fake-container-id-123\n", stderr="")
        if argv[:2] == ["docker", "exec"]:
            payload = argv[-1] if isinstance(argv[-1], str) else ""
            full = " ".join(argv)
            work = state.get("work", "")
            # Runtime success must come from separate actual fake processes,
            # not the historical canned PID/title/usage success path below.
            if argv[3:5] == ['env', '-i']:
                from tests.test_m07_t05_owned_runtime import OwnedRuntimeFixture
                runtime = state.get('_owned_runtime')
                if runtime is None:
                    root = Path(work) / 'external-runtime'
                    root.mkdir()
                    profile_path = Path(state.get('bindir', '')) / 'fake-profile.json'
                    profile = json.loads(profile_path.read_text()) if profile_path.is_file() else {}
                    faults = {'thinking': paseo_effort != 'max' or state.get('agent_thinking', 'max') != 'max',
                              'completion': state.get('agent_status', 'completed') not in ('completed', 'idle'),
                              'omit_witness': bool(state.get('omit_witness') or state.get('omit_terminal')),
                              'omit_settled': bool(state.get('omit_settled')),
                              'turn': state.get('witness_turn', 'completed'),
                              'response': state.get('witness_response', '200'),
                              'effort': state.get('witness_effort', profile.get('effort', paseo_effort)), 'version': pi_version}
                    faults.update(state.get('runtime_fault', {}))
                    runtime = OwnedRuntimeFixture(root, faults, secret_file=muse_secret_host)
                    state['_owned_runtime'] = runtime
                    for rel in ('bin/run-llm-test.sh', 'bin/m07-t05-candidate-env.sh',
                                'bin/m07-t05-pi-owned.py', 'bin/m07-t05-owned-runtime.mjs',
                                'policies/llm-test-policy.json', 'extensions/m07-t05-witness.js'):
                        (runtime.agent / rel).write_text(runtime.translate(
                            (Path(work) / 'home/.pi/agent' / rel).read_text()))
                result = runtime.execute(argv[3:], timeout=timeout)
                if 'daemon-bringup' in payload:
                    if state.get('daemon_start_exit'):
                        result.returncode = state['daemon_start_exit']
                    if state.get('daemon_start_action'):
                        doc = json.loads(result.stdout); doc['action'] = state['daemon_start_action']
                        result.stdout = json.dumps(doc)
                if 'status' in argv:
                    override = state.get('daemon_override') or daemon_json
                    if override:
                        result.stdout = json.dumps(override)
                        if override.get('__unavailable'):
                            result.returncode = 1
                if 'models' in argv and 'model_catalog' in state:
                    result.stdout = json.dumps(state['model_catalog'])
                if 'command -v pi' in payload and state.get('pi_path'):
                    result.stdout = state['pi_path'] + '\n'
                if '--candidate-owned' in payload:
                    state['dispatch_complete'] = 'prompt' in runtime.calls()
                    state['test_id'] = json.loads(result.stdout).get('test_id', '') if result.stdout else ''
                    state['witness_host'] = json.loads((runtime.home / '.m07-t05/launch.json').read_text())['witness']
                    for filename in ('owned.json', 'binding.json'):
                        source = runtime.home / '.m07-t05' / filename
                        if source.exists():
                            target = Path(work) / 'home/.m07-t05' / filename
                            target.write_text(runtime.restore(source.read_text()))
                            target.chmod(0o600)
                return result
            # Codex check: run the ACTUAL staged file locally.
            if argv[3:5] == ['python3', '/home/paseo/.pi/agent/bin/paseo_codex_candidate_check.py']:
                staged = (Path(work) / "home" / ".pi" / "agent" / "bin" / "paseo_codex_candidate_check.py") if work else None
                # Execute the shipped argv unchanged except namespace mappings.
                # Derive mounts from docker run; never substitute helper arguments.
                run_call = next(c for c in calls if c[:2] == ["docker", "run"])
                namespaces = {}
                for i, arg in enumerate(run_call):
                    if arg == "-v":
                        source, destination, _mode = run_call[i + 1].split(":")
                        namespaces[destination] = source
                def translate(arg):
                    for destination in sorted(namespaces, key=len, reverse=True):
                        if arg == destination or arg.startswith(destination + "/"):
                            return namespaces[destination] + arg[len(destination):]
                    return arg
                cmd = [sys.executable] + [translate(arg) for arg in argv[4:]]
                try:
                    pr = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=30)
                except Exception as exc:
                    return mock.Mock(returncode=20, stdout="", stderr=str(exc)[:200])
                return mock.Mock(returncode=pr.returncode, stdout=pr.stdout, stderr=pr.stderr)
            # File readback: compute ACTUAL hash+mode of staged files locally.
            # The validator compares both (bytes AND mode); returncode 0 alone
            # never passes. Only the in-candidate path prefix is translated.
            if "file-readback" in payload:
                import hashlib as _hl
                toks = payload.split()
                cand_path = ""
                if "sha256sum" in toks:
                    cand_path = toks[toks.index("sha256sum") + 1].rstrip(";") if len(toks) > toks.index("sha256sum") + 1 else ""
                host_path = cand_path.replace("/home/paseo", (work + "/home") if work else "/nonexistent", 1)
                try:
                    data = Path(host_path).read_bytes()
                    h = _hl.sha256(data).hexdigest()
                    if break_guard or state.get("break_guard"):
                        h = "0" * 64
                    import stat as _sm
                    mode = oct(_sm.S_IMODE(Path(host_path).stat().st_mode))[2:]
                    if state.get("policy_drift") and cand_path.endswith("llm-test-policy.json"):
                        mode = "666"
                    return mock.Mock(returncode=0, stdout=f"{h}  {cand_path}\n{mode}\n", stderr="")
                except OSError:
                    return mock.Mock(returncode=1, stdout="", stderr="")
            # Policy cat: return ACTUAL staged content (drifted when the probe mutates it).
            if "policy-compare" in payload:
                staged_pol = Path(work) / "home" / ".pi" / "agent" / "policies" / "llm-test-policy.json" if work else None
                try:
                    return mock.Mock(returncode=0, stdout=staged_pol.read_text(encoding="utf-8"), stderr="")
                except OSError:
                    return mock.Mock(returncode=1, stdout="", stderr="")
            # Daemon status inside candidate (fake daemon boundary, parsed for real).
            # state["daemon_override"] lets negatives inject stopped/unreachable/
            # remote/null-pid/foreign observations through the genuine entrypoint.
            # Daemon bring-up (idempotent start, shell-wrapped): succeeds when
            # the daemon is startable; the subsequent status observation decides.
            # Matched on the marker substring (shell-wrapped argv), ordered before
            # the generic status branch below.
            if "daemon-bringup" in payload:
                state["daemon_started"] = True
                return mock.Mock(returncode=state.get("daemon_start_exit", 0), stdout=json.dumps({
                    "action": state.get("daemon_start_action", "started"),
                    "home": "/home/paseo/.paseo", "pid": 1234, "listen": "127.0.0.1:7777"}), stderr="")
            # Owned-child listing: exactly the agents this fake daemon created.
            if "paseo" in argv and "agent" in argv and "ls" in argv:
                agents = state.get("agents", [])
                return mock.Mock(returncode=0, stdout=json.dumps(agents), stderr="")
            # Owned-child inspection: only recorded agents resolve.
            if "paseo" in argv and "agent" in argv and "inspect" in argv:
                want = argv[argv.index("inspect") + 1] if "inspect" in argv else ""
                for a in state.get("agents", []):
                    if a.get("id") == want or str(a.get("id", "")).startswith(want) or want.startswith(str(a.get("id", ""))):
                        return mock.Mock(returncode=0, stdout=json.dumps(a), stderr="")
                return mock.Mock(returncode=1, stdout="", stderr="No such agent")
            if "paseo" in argv and "status" in argv:
                doc = state.get("daemon_override")
                if doc is None:
                    doc = daemon_json if daemon_json is not None else {
                        "home": "/home/paseo/.paseo", "listen": "127.0.0.1:7777",
                        "pid": 1234, "daemonVersion": REAL_PASEO,
                        "localDaemon": "running", "connectedDaemon": "reachable",
                        "workerPid": 1235, "serverId": "synthetic-server", "daemonNode": "/usr/bin/node",
                        "providers": ["pi"]}
                if isinstance(doc, dict) and doc.get("__unavailable"):
                    return mock.Mock(returncode=1, stdout="", stderr="")
                if state.get("daemon_started") and isinstance(doc, dict) and doc.get("localDaemon") == "stopped":
                    # Bring-up flips a stopped-but-otherwise-valid daemon to
                    # running; broken endpoint/pid/version observations persist
                    # and still fail the strict observer below.
                    doc = dict(doc, localDaemon="running", connectedDaemon="reachable")
                return mock.Mock(returncode=0, stdout=json.dumps(doc), stderr="")
            if argv[3:7] == ["paseo", "provider", "models", "pi"]:
                models = state.get("model_catalog", [{"id": "meta/muse-spark-1.3-contributor",
                                                       "thinkingOptionIds": ["max"]}])
                return mock.Mock(returncode=0, stdout=json.dumps(models), stderr="")
            if "command -v pi" in payload:
                return mock.Mock(returncode=0, stdout=(state.get("pi_path") or "/usr/local/bin/pi") + "\n", stderr="")
            if argv[-2:] == ["pi", "--version"] or payload.strip() == "pi --version":
                return mock.Mock(returncode=0, stdout=pi_version + "\n", stderr="")
            # Native export: run ACTUAL staged guard with --native-create-agent-args.
            if "native-export-check" in payload:
                staged_guard = Path(work) / "home" / ".pi" / "agent" / "bin" / "run-llm-test.sh" if work else None
                try:
                    pr = subprocess.run([str(staged_guard), "--native-create-agent-args"],
                                        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                except Exception as exc:
                    return mock.Mock(returncode=2, stdout="", stderr=str(exc)[:200])
                return mock.Mock(returncode=pr.returncode, stdout=pr.stdout, stderr=pr.stderr)
            # Guarded PROMPT dispatch: run the ACTUAL staged candidate-env
            # loader (namespace-translated paths only) execing the ACTUAL
            # staged guard; the shell fake parses --env exactly like pinned
            # run.js and requires loader-delivered META_API_KEY. Then the FULL
            # provider/turn/settlement sequence runs through the ACTUAL staged
            # observer under node (never shell-fabricated witness bytes), and
            # the dispatched agent is recorded for ls/inspect binding.
            if "guarded-dispatch" in payload:
                staged_env = Path(work) / "home" / ".pi" / "agent" / "bin" / "m07-t05-candidate-env.sh" if work else None
                staged_guard = Path(work) / "home" / ".pi" / "agent" / "bin" / "run-llm-test.sh" if work else None
                staged_ext = Path(work) / "home" / ".pi" / "agent" / "extensions" / "m07-t05-witness.js" if work else None
                bindir = state.get("bindir", "/tmp")
                wit = state.get("witness_host", "/tmp/m07-t05-witness.jsonl")
                tid = state.get("test_id", "")
                import re as _re
                m = _re.search(r"M07_T05_TEST_ID=(\S+)", payload)
                if m:
                    tid = m.group(1).strip().strip("'\"")
                    state["test_id"] = tid
                try:
                    env_text = staged_env.read_text(encoding="utf-8")
                except OSError as exc:
                    return mock.Mock(returncode=42, stdout="", stderr=str(exc)[:200])
                local_env = Path(work) / f"candidate-env-{tid}.sh"
                local_env.write_text(env_text, encoding="utf-8")
                local_env.chmod(0o755)
                marker_path = Path(bindir).parent / "dispatch-argv.txt"
                env = {"PATH": str(bindir), "M07_T05_TEST_ID": tid,
                       "M07_T05_WITNESS_FILE": str(wit),
                       "DISPATCH_MARKER": str(marker_path),
                       "META_API_KEY_FILE": str(muse_secret_host) if muse_secret_host else ""}
                try:
                    pr = subprocess.run(["bash", str(local_env), str(staged_guard),
                                         f"SYNTHETIC_PROMPT_{tid}", "/tmp"],
                                        env=env, text=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=60)
                except subprocess.TimeoutExpired:
                    return mock.Mock(returncode=None, stdout="", stderr="timeout")
                except Exception as exc:
                    return mock.Mock(returncode=3, stdout="", stderr=str(exc)[:200])
                if pr.returncode == 0:
                    state["dispatch_complete"] = True
                    agent_id = f"agent-{tid[:12]}"
                    # Legacy omit_terminal flag also suppresses witness emission
                    # (no terminal event exists to aggregate).
                    if state.get("omit_terminal"):
                        state["omit_witness"] = True
                    title = f"LLM-TEST:muse-spark-1.3-contributor:max:{tid}"
                    state.setdefault("agents", []).append({
                        "id": agent_id, "name": title, "title": title,
                        "provider": "pi", "model": "meta/muse-spark-1.3-contributor",
                        "thinking": state.get("agent_thinking", "max"),
                        "status": state.get("agent_status", "completed"),
                        "LastUsage": {"InputTokens": 120, "OutputTokens": 60,
                                      "CachedTokens": 0, "CostUsd": 0.001}})
                    if not state.get("omit_witness"):
                        try:
                            profile = json.loads((Path(bindir) / "fake-profile.json").read_text())
                        except (OSError, ValueError):
                            profile = {}
                        _emit_full_sequence_via_observer(
                            staged_ext=staged_ext, witness_host=str(wit), test_id=tid,
                            effort=state.get("witness_effort") or profile.get("effort", "max"),
                            response_status=state.get("witness_response") or profile.get("response_status", "200"),
                            turn_outcome=state.get("witness_turn", "completed"),
                            fire_agent_end=not state.get("omit_agent_end", False),
                            fire_settled=not state.get("omit_settled", False))
                return mock.Mock(returncode=pr.returncode, stdout=pr.stdout, stderr=pr.stderr)
            # Witness read: return ACTUAL witness file.
            if "witness-read" in payload:
                wit = state.get("witness_host", "/tmp/m07-t05-witness.jsonl")
                try:
                    return mock.Mock(returncode=0, stdout=Path(wit).read_text(encoding="utf-8"), stderr="")
                except OSError:
                    return mock.Mock(returncode=1, stdout="", stderr="")
            # Muse secret check.
            if "muse-secret-check" in payload:
                if muse_secret_host and Path(muse_secret_host).is_file():
                    return mock.Mock(returncode=0, stdout="", stderr="")
                return mock.Mock(returncode=1, stdout="", stderr="")
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ['docker', 'rm']:
            if state.get('_owned_runtime'):
                runtime = state['_owned_runtime']
                state['runtime_calls_before_cleanup'] = runtime.calls()
                trace = runtime.home / 'fake-calls.jsonl'
                state['runtime_requests_before_cleanup'] = ([json.loads(line) for line in
                    trace.read_text().splitlines()] if trace.exists() else [])
            if state.get('remove_failure'):
                return mock.Mock(returncode=1, stdout='', stderr='synthetic removal failed')
            if state.get('_owned_runtime'):
                state['_owned_runtime'].close()
            state['ran'] = False
            return mock.Mock(returncode=0, stdout='', stderr='')
        return mock.Mock(returncode=0, stdout="", stderr="")
    return fake


class TowerValidatorGenuineTests(unittest.TestCase):
    def test_shipped_check_program_compiles_and_runs(self):
        # Finding 1: exact shipped program must compile AND execute.
        prog = ROOT / "scripts" / "paseo_codex_candidate_check.py"
        compile(prog.read_bytes(), str(prog), "exec")
        with tempfile.TemporaryDirectory() as td:
            sec = Path(td) / "codex.env"
            sec.write_text("CODEX_LB_API_KEY=fixture-check-key\n")
            sec.chmod(0o600)
            with LocalCodexServer(mode="ok") as srv:
                pr = subprocess.run(
                    [sys.executable, str(prog), "--mode", "catalog",
                     "--secret-file", str(sec), "--base-url", srv.base,
                     "--model", "fixture-model"],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(pr.returncode, 0, pr.stderr)
                self.assertEqual(json.loads(pr.stdout)["status"], "PASS")
                pr2 = subprocess.run(
                    [sys.executable, str(prog), "--mode", "health",
                     "--secret-file", str(sec), "--base-url", srv.base],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(pr2.returncode, 0, pr2.stderr)
            # Syntax failure is a failure, not success.
            bad = Path(td) / "bad.py"
            bad.write_text("def broken(:\n")
            pb = subprocess.run([sys.executable, "-m", "py_compile", str(bad)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pb.returncode, 0)

    def test_positive_fixture_through_genuine_api(self):
        # MANDATORY POSITIVE: genuine validator API, staged guard + programs,
        # fake Paseo/Pi lifecycle, completed shared-subject mechanical result.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex_sec = td / "codex.env"
            codex_sec.write_text("CODEX_LB_API_KEY=fixture-codex-key\n")
            codex_sec.chmod(0o600)
            muse_sec = td / "muse.env"
            muse_sec.write_text("META_API_KEY=fixture-meta-key\n")
            muse_sec.chmod(0o600)
            image_id = "sha256:" + "b" * 64
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = build_artifact_chain(td, image_id=image_id)
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_OCI_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "out.json", state_root=td / "state",
                                     codex_secret=codex_sec, codex_base_url=srv.base,
                                     codex_model="fixture-model", execution_class="fixture",
                                     source_root=fixture_source(td),
                                     companion_bundle=_companion_arg(),
                                     candidate_file=cand_file, handoff_file=handoff_file,
                                     build_input_file=build_input_file,
                                     tested_image_file=tested_file, build_record=build_record_file,
                                     publication_file=publication_file, muse_secret=muse_sec)
            self.assertEqual(res["status"], "PASS")
            self.assertFalse(res["real_validation_satisfied"])
            for k in ("registry_digest", "image_mapping", "image_config", "frozen_chain",
                      "companion_binding", "policy_binding", "daemon_binding", "pi_binding",
                      "codex_catalog", "codex_auth", "codex_health", "muse_guard_readback",
                      "muse_policy_readback", "muse_dispatch", "muse_effective_profile",
                      "muse_owned_child"):
                self.assertEqual(res["checks"].get(k), "PASS", k)
            # No inference endpoint in any exec; no secret value in calls/output.
            blob = json.dumps(res) + " ".join(" ".join(c) for c in calls)
            self.assertNotIn("/responses", blob.replace('"/res"+"ponses"', ""))
            self.assertNotIn("fixture-codex-key", blob)
            self.assertNotIn("fixture-meta-key", blob)
            # Dispatched through the real guard (fake paseo marker + witness).
            self.assertGreaterEqual(len([c for c in calls if c[:2] == ["docker", "exec"]]), 6)
            # Candidate-only guard now reaches supported native creation with
            # NO initialPrompt. Capture actual request keys/IDs in the separate
            # fake daemon before cleanup, not a legacy shell argv/title/usage bag.
            requests = state['runtime_requests_before_cleanup']
            create = [row for row in requests if row['method'] == 'create-env']
            self.assertEqual(len(create), 1)
            self.assertFalse(create[0]['initial_prompt'])
            self.assertEqual(create[0]['names'], sorted([
                'M07_T05_TEST_ID', 'M07_T05_WITNESS_FILE', 'META_API_KEY_FILE',
                'M07_T05_RUNTIME_BINDING', 'M07_T05_PROCESS_DIR']))
            self.assertNotIn('fixture-meta-key', json.dumps(requests))
            subj = res.get('subject') or {}
            child = subj.get('muse_owned_child')
            runtime = subj['owned_runtime']
            self.assertEqual(child['thinking'], 'max')
            self.assertEqual(child['id'], create[0]['agent_id'])
            self.assertEqual(child['workspace_id'], create[0]['workspace_id'])
            self.assertEqual(child['process']['pid'], runtime['process']['pid'])
            self.assertEqual(child['process']['ppid'], subj['daemon_binding']['worker_pid'])
            self.assertEqual(state['runtime_calls_before_cleanup'].count('prompt'), 1)
            self.assertEqual(state['runtime_calls_before_cleanup'].count('fake-transport'), 1)
            envelopes = [row for row in requests if row['method'] == 'prompt-envelope']
            self.assertEqual(len(envelopes), 1)
            self.assertEqual(envelopes[0]['agent_id'], child['id'])
            self.assertEqual(envelopes[0]['message_id'], runtime['message_id'])

    def test_real_mode_structurally_succeeds_under_fakes(self):
        # Real path exists (not hardcoded false): same fakes, real class.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex_sec = td / "codex.env"
            codex_sec.write_text("CODEX_LB_API_KEY=k\n")
            codex_sec.chmod(0o600)
            muse_sec = td / "muse.env"
            muse_sec.write_text("META_API_KEY=k\n")
            muse_sec.chmod(0o600)
            image_id = "sha256:" + "b" * 64
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = build_artifact_chain(td, image_id=image_id)
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_OCI_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "out.json", state_root=td / "state",
                                     codex_secret=codex_sec, codex_base_url=srv.base,
                                     codex_model="m", execution_class="real",
                                     source_root=fixture_source(td),
                                     companion_bundle=_companion_arg(),
                                     candidate_file=cand_file, handoff_file=handoff_file,
                                     build_input_file=build_input_file,
                                     tested_image_file=tested_file, build_record=build_record_file,
                                     publication_file=publication_file, muse_secret=muse_sec)
            self.assertEqual(res["status"], "PASS")
            self.assertTrue(res["real_validation_satisfied"])

    def test_false_guard_readback_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex_sec = td / "codex.env"
            codex_sec.write_text("CODEX_LB_API_KEY=k\n")
            codex_sec.chmod(0o600)
            muse_sec = td / "muse.env"
            muse_sec.write_text("META_API_KEY=k\n")
            muse_sec.chmod(0o600)
            image_id = "sha256:" + "b" * 64
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = build_artifact_chain(td, image_id=image_id)
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_OCI_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec,
                                        break_guard=True)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     codex_secret=codex_sec, codex_base_url=srv.base,
                                     codex_model="m", execution_class="fixture",
                                     source_root=fixture_source(td),
                                     companion_bundle=_companion_arg(),
                                     candidate_file=cand_file, muse_secret=muse_sec)
            self.assertEqual(res["status"], "FAIL")
            self.assertIn('content readback mismatch', res.get('reason', '').lower())

    def test_malformed_build_record_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = build_artifact_chain(td)
            tested_file.write_text('{"candidate_id": "forged"}')
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator"}
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=make_fake_docker(
                     digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=calls,
                     state=state, server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=None, muse_secret_host=None)):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td / "st",
                                 execution_class="real", source_root=ROOT,
                                 candidate_file=cand_file, tested_image_file=tested_file)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))

    def test_cli_genuine_path(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex_sec = td / "codex.env"
            codex_sec.write_text("CODEX_LB_API_KEY=k\n")
            codex_sec.chmod(0o600)
            muse_sec = td / "muse.env"
            muse_sec.write_text("META_API_KEY=k\n")
            muse_sec.chmod(0o600)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = build_artifact_chain(td, image_id="sha256:" + "b" * 64)
            comp = td / "comp.json"
            _ca = _companion_arg()
            comp.write_text(json.dumps(_ca))
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec)
                argv = ["paseo_tower_validator", "--digest", REAL_OCI_DIGEST,
                        "--output", str(td / "cli.json"), "--state-root", str(td / "st"),
                        "--codex-secret", str(codex_sec), "--codex-base-url", srv.base,
                        "--codex-model", "m", "--source-root", str(fixture_source(td)),
                        "--candidate-file", str(cand_file), "--handoff-file", str(handoff_file),
                        "--build-input-file", str(build_input_file),
                        "--tested-image-file", str(tested_file),
                        "--build-record", str(build_record_file),
                        "--publication-file", str(publication_file),
                        "--muse-secret", str(muse_sec),
                        "--companion-bundle", str(comp)]
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake), \
                     mock.patch.object(sys, "argv", argv):
                    rc = V.main()
            self.assertEqual(rc, 0)
            doc = json.loads((td / "cli.json").read_text())
            self.assertEqual(doc["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
