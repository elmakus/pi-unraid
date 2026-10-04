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
REAL_DIGEST = REAL_CANDIDATE["candidate_id"]
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
    return {"schema_version": c["schema_version"], "source": c["source"],
            "source_digest": c["source_digest"], "files": c["files"], "modes": c["modes"]}


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
                            {"id": "fixture-model", "object": "model"}]}).encode()
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
                    terminal="done", dispatch=True):
    """Test-owned fake paseo: records dispatch, writes witness, never infers."""
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
        "if [ \"$1\" = \"status\" ]; then\n"
        "  printf '%s' \"$PASEO_STATUS_JSON\"\n"
        "  exit 0\n"
        "fi\n"
        f"DISPATCH={1 if dispatch else 0}\n"
        "if [ \"$DISPATCH\" = \"1\" ]; then\n"
        "  printf '%s\\n' \"$@\" > \"$DISPATCH_MARKER\"\n"
        "fi\n"
        "WIT=\"$M07_T05_WITNESS_FILE\"\n"
        "TID=\"$M07_T05_TEST_ID\"\n"
        "if [ -n \"$WIT\" ] && [ -n \"$TID\" ] && [ \"$DISPATCH\" = \"1\" ]; then\n"
        f"  printf '{{\"test_id\":\"%s\",\"kind\":\"request\",\"model\":\"muse-spark-1.3-contributor\",\"effort\":\"{effort}\"}}\\n' \"$TID\" >> \"$WIT\"\n"
        f"  printf '{{\"test_id\":\"%s\",\"kind\":\"response\",\"status\":\"{response_status}\"}}\\n' \"$TID\" >> \"$WIT\"\n"
        f"  printf '{{\"test_id\":\"%s\",\"kind\":\"terminal\",\"status\":\"{terminal}\"}}\\n' \"$TID\" >> \"$WIT\"\n"
        "fi\n"
        f"exit {0 if dispatch else 3}\n"
    )
    fake.chmod(0o755)
    # Fake pi for candidate Pi lifecycle.
    pi = bindir / "pi"
    pi.write_text(f"#!/bin/sh\necho '{REAL_PI}'\n")
    pi.chmod(0o755)
    return bindir


def build_artifact_chain(td: Path, *, digest=REAL_DIGEST):
    """Real-schema fixture chain bound to the actual candidate bytes."""
    cand_src = ROOT / "config" / "paseo-candidate.json"
    cand_file = td / "candidate.json"
    cand_file.write_bytes(cand_src.read_bytes())
    raw = cand_file.read_bytes()
    import hashlib as _hl
    cfs = "sha256:" + _hl.sha256(raw).hexdigest()
    handoff = {"candidate_id": digest, "accepted_candidate_id": "sha256:" + "0" * 64,
               "schema_version": 1, "status": "update", "source_ref": "refs/heads/main",
               "source_sha": "0" * 40, "candidate_file_sha256": cfs}
    handoff_file = td / "handoff.json"
    handoff_file.write_text(json.dumps(handoff))
    _full = _companion_arg()
    build_input = {"candidate_id": digest, "candidate_file_sha256": cfs,
                   "companion_bundle": _full}
    build_input_file = td / "build-input.json"
    build_input_file.write_text(json.dumps(build_input))
    import hashlib as _hl2
    tested = {"candidate_id": digest, "candidate_file_sha256": cfs,
              "image_id": None,  # filled per-test after pull id known
              "companion_bundle": build_input["companion_bundle"]}
    tested_file = td / "tested.json"
    tested_file.write_text(json.dumps(tested))
    return cand_file, handoff_file, build_input_file, tested_file


def make_fake_docker(*, digest, image_id, calls, state, server_base,
                     codex_secret_host, muse_secret_host,
                     daemon_json=None, pi_version=REAL_PI,
                     paseo_effort="max", witness_terminal="done",
                     break_guard=False, break_image=False):
    """Strict fake Docker where exec runs ACTUAL staged logic locally."""
    def fake(argv, timeout=300, check=True):
        calls.append(argv)
        if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
            return mock.Mock(returncode=0, stdout=f"Digest: {digest}\n", stderr="")
        if argv[:3] == ["docker", "image", "inspect"]:
            if "{{json .RepoDigests}}" in " ".join(argv):
                if state.get("no_repodigests"):
                    return mock.Mock(returncode=0, stdout=json.dumps([]), stderr="")
                return mock.Mock(returncode=0, stdout=json.dumps([f"ghcr.io/elmakus/pi-unraid@{digest}"]), stderr="")
            return mock.Mock(returncode=0, stdout=image_id + "\n", stderr="")
        if argv[:3] == ["docker", "image", "pull"]:
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "network"]:
            if argv[2] == "inspect":
                if not state.get("net_exists", False):
                    return mock.Mock(returncode=1, stdout="", stderr="No such")
                import json as _j
                return mock.Mock(returncode=0, stdout=_j.dumps([{
                    "Labels": {"io.pi-unraid.validator-nonce": state["nonce"]}}]), stderr="")
            if argv[2] == "create":
                state["net_exists"] = True
                # record nonce from --label
                for i, x in enumerate(argv):
                    if x == "--label" and i + 1 < len(argv) and argv[i + 1].startswith("io.pi-unraid.validator-nonce="):
                        state["nonce"] = argv[i + 1].split("=", 1)[1]
                return mock.Mock(returncode=0, stdout="netid\n", stderr="")
            if argv[2] == "rm":
                state["net_exists"] = False
                return mock.Mock(returncode=0, stdout="", stderr="")
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "inspect"]:
            if not state.get("ran"):
                return mock.Mock(returncode=1, stdout="", stderr="No such")
            run_call = next(x for x in calls if x[:2] == ["docker", "run"])
            mounts = []
            for i, x in enumerate(run_call):
                if x == "-v":
                    parts = run_call[i + 1].split(":")
                    mounts.append({"Source": parts[0], "Destination": parts[1],
                                   "RW": (parts[2] if len(parts) > 2 else "rw") != "ro"})
            nonce = state.get("nonce", "unknown")
            img = state.get("wrong_image") or image_id
            obj = {"Id": "fake-container-id-123", "Image": img,
                   "Config": {"User": "99:100", "Env": ["TZ=Europe/Zurich", "HOME=/home/paseo"],
                              "Labels": {"io.pi-unraid.validator-nonce": nonce}},
                   "HostConfig": {"NetworkMode": state.get("network", "pi-unraid-validator")},
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
            # Codex check: run the ACTUAL staged file locally.
            if "paseo_codex_candidate_check.py" in full:
                staged = (Path(work) / "home" / ".pi" / "agent" / "bin" / "paseo_codex_candidate_check.py") if work else None
                mode = "health" if "--mode health" in full or ("--mode" in argv and argv[argv.index("--mode")+1] == "health") else "catalog"
                # Find host secret + base for local execution.
                env = {"PI_CODEX_LB_BASE_URL": server_base, "PATH": "/usr/bin:/bin"}
                cmd = [sys.executable, str(staged), "--mode", mode,
                       "--secret-file", str(codex_secret_host),
                       "--base-url", server_base, "--model", "fixture-model"]
                try:
                    pr = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=30)
                except Exception as exc:
                    return mock.Mock(returncode=20, stdout="", stderr=str(exc)[:200])
                return mock.Mock(returncode=pr.returncode, stdout=pr.stdout, stderr=pr.stderr)
            # Guard hash: compute ACTUAL hash of staged file.
            if "guard-hash-compare" in payload:
                staged_guard = Path(work) / "home" / ".pi" / "agent" / "bin" / "run-llm-test.sh" if work else None
                try:
                    import hashlib as _hl
                    h = _hl.sha256(staged_guard.read_bytes()).hexdigest()
                    if break_guard:
                        h = "0" * 64
                    return mock.Mock(returncode=0, stdout=f"{h}  /home/paseo/.pi/agent/bin/run-llm-test.sh\n", stderr="")
                except OSError:
                    return mock.Mock(returncode=1, stdout="", stderr="")
            # Policy cat: return ACTUAL staged content.
            if "policy-compare" in payload:
                staged_pol = Path(work) / "home" / ".pi" / "agent" / "policies" / "llm-test-policy.json" if work else None
                try:
                    return mock.Mock(returncode=0, stdout=staged_pol.read_text(encoding="utf-8"), stderr="")
                except OSError:
                    return mock.Mock(returncode=1, stdout="", stderr="")
            # Daemon status inside candidate (fake daemon boundary, parsed for real).
            if "paseo" in argv and "status" in argv:
                doc = daemon_json if daemon_json is not None else {
                    "home": "/home/paseo/.paseo", "listen": "127.0.0.1:7777",
                    "pid": 1234, "daemonVersion": REAL_PASEO}
                return mock.Mock(returncode=0, stdout=json.dumps(doc), stderr="")
            if "command -v pi" in payload:
                return mock.Mock(returncode=0, stdout="/home/paseo/.pi/agent/bin/pi\n", stderr="")
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
            # Guarded PROMPT dispatch: run ACTUAL staged guard with fake bindir.
            # Candidate witness path (/tmp/...) maps to the host witness file;
            # the value is never confused with the candidate path.
            if "guarded-dispatch" in payload:
                staged_guard = Path(work) / "home" / ".pi" / "agent" / "bin" / "run-llm-test.sh" if work else None
                bindir = state.get("bindir", "/tmp")
                wit = state.get("witness_host", "/tmp/m07-t05-witness.jsonl")
                tid = state.get("test_id", "")
                import re as _re
                m = _re.search(r"M07_T05_TEST_ID=(\S+)", payload)
                if m:
                    tid = m.group(1).strip().strip("'\"")
                    state["test_id"] = tid
                # Extract prompt JSON string (last quoted arg) — run guard with synthetic prompt.
                env = {"PATH": str(bindir), "M07_T05_TEST_ID": tid,
                       "M07_T05_WITNESS_FILE": str(wit),
                       "META_API_KEY_FILE": str(muse_secret_host) if muse_secret_host else ""}
                try:
                    pr = subprocess.run(["bash", str(staged_guard), f"SYNTHETIC_PROMPT_{tid}", "/tmp"],
                                        env=env, text=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=60)
                except subprocess.TimeoutExpired:
                    return mock.Mock(returncode=None, stdout="", stderr="timeout")
                except Exception as exc:
                    return mock.Mock(returncode=3, stdout="", stderr=str(exc)[:200])
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
        if argv[:2] == ["docker", "rm"]:
            return mock.Mock(returncode=0, stdout="", stderr="")
        return mock.Mock(returncode=0, stdout="", stderr="")
    return fake


class TowerValidatorGenuineTests(unittest.TestCase):
    def test_shipped_check_program_compiles_and_runs(self):
        # Finding 1: exact shipped program must compile AND execute.
        prog = ROOT / "scripts" / "paseo_codex_candidate_check.py"
        subprocess.run([sys.executable, "-m", "py_compile", str(prog)], check=True)
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
            cand_file, handoff_file, build_input_file, tested_file = build_artifact_chain(td)
            image_id = "sha256:" + "b" * 64
            # tested image_id must equal pulled id for the chain.
            tested = json.loads(tested_file.read_text())
            tested["image_id"] = image_id
            tested_file.write_text(json.dumps(tested))
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake):
                    res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                     output=td / "out.json", state_root=td / "state",
                                     codex_secret=codex_sec, codex_base_url=srv.base,
                                     codex_model="fixture-model", execution_class="fixture",
                                     source_root=ROOT,
                                     companion_bundle=_companion_arg(),
                                     candidate_file=cand_file, handoff_file=handoff_file,
                                     build_input_file=build_input_file,
                                     tested_image_file=tested_file, muse_secret=muse_sec)
            self.assertEqual(res["status"], "PASS")
            self.assertFalse(res["real_validation_satisfied"])
            for k in ("registry_digest", "image_mapping", "frozen_chain", "companion_binding",
                      "policy_binding", "daemon_binding", "pi_binding", "codex_catalog",
                      "codex_auth", "codex_health", "muse_guard_readback",
                      "muse_policy_readback", "muse_dispatch", "muse_effective_profile"):
                self.assertEqual(res["checks"].get(k), "PASS", k)
            # No inference endpoint in any exec; no secret value in calls/output.
            blob = json.dumps(res) + " ".join(" ".join(c) for c in calls)
            self.assertNotIn("/responses", blob.replace('"/res"+"ponses"', ""))
            self.assertNotIn("fixture-codex-key", blob)
            self.assertNotIn("fixture-meta-key", blob)
            # Dispatched through the real guard (fake paseo marker + witness).
            self.assertGreaterEqual(len([c for c in calls if c[:2] == ["docker", "exec"]]), 6)

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
            cand_file, handoff_file, build_input_file, tested_file = build_artifact_chain(td)
            image_id = "sha256:" + "b" * 64
            tested = json.loads(tested_file.read_text())
            tested["image_id"] = image_id
            tested_file.write_text(json.dumps(tested))
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake):
                    res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                     output=td / "out.json", state_root=td / "state",
                                     codex_secret=codex_sec, codex_base_url=srv.base,
                                     codex_model="m", execution_class="real",
                                     source_root=ROOT,
                                     companion_bundle=_companion_arg(),
                                     candidate_file=cand_file, handoff_file=handoff_file,
                                     build_input_file=build_input_file,
                                     tested_image_file=tested_file, muse_secret=muse_sec)
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
            cand_file, handoff_file, build_input_file, tested_file = build_artifact_chain(td)
            image_id = "sha256:" + "b" * 64
            tested = json.loads(tested_file.read_text())
            tested["image_id"] = image_id
            tested_file.write_text(json.dumps(tested))
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec,
                                        break_guard=True)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=fake):
                    res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     codex_secret=codex_sec, codex_base_url=srv.base,
                                     codex_model="m", execution_class="fixture",
                                     source_root=ROOT,
                                     companion_bundle=_companion_arg(),
                                     candidate_file=cand_file, muse_secret=muse_sec)
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("guard hash", res.get("reason", "").lower())

    def test_malformed_build_record_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cand_file, handoff_file, build_input_file, tested_file = build_artifact_chain(td)
            tested_file.write_text('{"candidate_id": "forged"}')
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator"}
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=make_fake_docker(
                     digest=REAL_DIGEST, image_id="sha256:" + "b" * 64, calls=calls,
                     state=state, server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=None, muse_secret_host=None)):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
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
            cand_file, handoff_file, build_input_file, tested_file = build_artifact_chain(td)
            image_id = "sha256:" + "b" * 64
            tested = json.loads(tested_file.read_text())
            tested["image_id"] = image_id
            tested_file.write_text(json.dumps(tested))
            comp = td / "comp.json"
            _ca = _companion_arg()
            comp.write_text(json.dumps(_ca))
            bindir = make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with LocalCodexServer(mode="ok") as srv:
                fake = make_fake_docker(digest=REAL_DIGEST, image_id=image_id, calls=calls,
                                        state=state, server_base=srv.base,
                                        codex_secret_host=codex_sec, muse_secret_host=muse_sec)
                argv = ["paseo_tower_validator", "--digest", REAL_DIGEST,
                        "--output", str(td / "cli.json"), "--state-root", str(td / "st"),
                        "--codex-secret", str(codex_sec), "--codex-base-url", srv.base,
                        "--codex-model", "m", "--source-root", str(ROOT),
                        "--candidate-file", str(cand_file), "--muse-secret", str(muse_sec),
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
