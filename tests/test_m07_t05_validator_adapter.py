"""M07-T05 adapter/matrix/probe tests (coherent rewrite).

Classification: synthetic/local fixtures + approved non-inference source
readback ONLY. Fake ONLY external Docker/Paseo/provider boundaries; PATH
isolated to test-owned bindirs with fake paseo (never real inference).
No real credential/admission, ordinary-auth reads, HOME/runtime mutation,
live Docker/Tower, image build, or CI occurs.

- Codex helper: injected http fixtures + temp secret files (no provider).
- Adapter: fake bindirs, disposable roots, synthetic META_API_KEY files.
- Validator matrix/probes: genuine validator API with the executing fake
  Docker harness (imported from test_paseo_tower_validator): the staged
  Codex check program and guard PROMPT form are REALLY executed locally;
  daemon/Pi outputs are canned at the fake-daemon boundary and parsed for
  real. Negatives assert required failure + no disallowed calls BEFORE
  cleanup (calls list). Positive observes real guard bytes + aggregated
  witness through the integrated path.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _load("paseo_tower_validator_m07t05", "scripts/paseo_tower_validator.py")
C = _load("paseo_codex_noninference_m07t05", "scripts/paseo_codex_noninference.py")
A = _load("paseo_candidate_muse_adapter_m07t05", "scripts/paseo_candidate_muse_adapter.py")
T = _load("paseo_tower_validator_harness", "tests/test_paseo_tower_validator.py")

RUNNER = ROOT / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
REAL_CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text(encoding="utf-8"))
REAL_CANDIDATE_ID = REAL_CANDIDATE["candidate_id"]
REAL_OCI_DIGEST = T.REAL_OCI_DIGEST
REAL_REPOSITORY = T.REAL_REPOSITORY


def _companion_arg():
    c = T.REAL_COMPANION
    return dict(c)


def _fixture_chain(td: Path, *, image_id):
    cand, handoff, build_input, tested, build_record, publication = T.build_artifact_chain(
        td, image_id=image_id)
    return cand, handoff, build_input, tested, build_record, publication


def _secrets(td: Path):
    codex = td / "codex.env"
    codex.write_text("CODEX_LB_API_KEY=fixture-codex\n")
    codex.chmod(0o600)
    muse = td / "muse.env"
    muse.write_text("META_API_KEY=fixture-meta\n")
    muse.chmod(0o600)
    return codex, muse


def _run_validate(td: Path, *, server_base, image_id="sha256:" + "b" * 64,
                  execution_class="fixture", effort="max", daemon_json=None,
                  break_guard=False, extra=None, omit_terminal=False,
                  pi_path=None, replaced_id=None, inspect_failure=False,
                  fail_cleanup_inspect=False, witness_response=None,
                  witness_turn=None, omit_witness=False, agent_thinking=None,
                  agent_status=None, extra_state=None):
    codex, muse = _secrets(td)
    cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = _fixture_chain(td, image_id=image_id)
    bindir = T.make_fake_paseo(td / "bindir", effort=effort)
    wit = td / "witness.jsonl"
    wit.write_text("")
    calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                        "bindir": str(bindir), "witness_host": str(wit)}
    if daemon_json is not None:
        state["daemon_override"] = daemon_json
    if break_guard:
        state["break_guard"] = True
    if omit_terminal:
        state["omit_terminal"] = True
    if pi_path is not None:
        state["pi_path"] = pi_path
    if replaced_id is not None:
        state["replaced_id"] = replaced_id
    if inspect_failure:
        state["inspect_failure"] = True
    if fail_cleanup_inspect:
        state["fail_cleanup_inspect"] = True
    if witness_response is not None:
        state["witness_response"] = witness_response
    if witness_turn is not None:
        state["witness_turn"] = witness_turn
    if omit_witness:
        state["omit_witness"] = True
    if agent_thinking is not None:
        state["agent_thinking"] = agent_thinking
    if agent_status is not None:
        state["agent_status"] = agent_status
    if extra_state:
        state.update(extra_state)
    # Wrap make_fake_docker to honor overrides.
    base_fake = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id=image_id, calls=calls,
                                   state=state, server_base=server_base,
                                   codex_secret_host=codex, muse_secret_host=muse)
    kwargs = dict(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                  output=td / "o.json", state_root=td / "st",
                  codex_secret=codex, codex_base_url=server_base,
                  codex_model="m", execution_class=execution_class,
                  source_root=T.fixture_source(td), companion_bundle=_companion_arg(),
                  candidate_file=cand_file, handoff_file=handoff_file,
                  build_input_file=build_input_file, tested_image_file=tested_file,
                  build_record=build_record_file, publication_file=publication_file,
                  muse_secret=muse)
    if extra:
        kwargs.update(extra)
    with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
         mock.patch.object(V.os, "chown"), \
         mock.patch.object(V, "run", side_effect=base_fake):
        res = V.validate(**kwargs)
    return res, calls, state


class CodexHelperTests(unittest.TestCase):
    def test_base_url_and_model_shapes(self):
        self.assertEqual(C.validate_base_url("http://h:1/v1"), "http://h:1/v1")
        for bad in ("http://h:1/v1/responses", "http://h:1/api", "not a url", ""):
            with self.subTest(bad=bad), self.assertRaises(C.CodexError):
                C.validate_base_url(bad)
        self.assertEqual(C.validate_model_id("m"), "m")
        for bad in ("", "a b", None):
            with self.subTest(bad=bad), self.assertRaises(C.CodexError):
                C.validate_model_id(bad)

    def test_secret_private_and_redirect_safe(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            good = td / "s.env"
            good.write_text("CODEX_LB_API_KEY=k\n")
            good.chmod(0o600)
            self.assertEqual(C.read_dedicated_secret(good), "k")
            world = td / "w.env"
            world.write_text("CODEX_LB_API_KEY=k\n")
            world.chmod(0o644)
            with self.assertRaises(C.CodexError):
                C.read_dedicated_secret(world)
        with self.assertRaises(C.CodexError):
            C.assert_safe_redirect("http://h:1/v1/models", "http://h:1/v1/responses")
        with self.assertRaises(C.CodexError):
            C.assert_safe_redirect("http://h:1/v1/models", "http://h:1/v1/models?y=1")
        # Cross-port localhost is a foreign origin: rejected before any request
        # with credentials (same-hostname comparison is insufficient).
        with self.assertRaises(C.CodexError):
            C.assert_safe_redirect("http://127.0.0.1:11/v1/models", "http://127.0.0.1:22/catalog")
        # Same origin is necessary, not sufficient: only the exact check path passes.
        C.assert_safe_redirect("http://127.0.0.1:11/v1/models", "http://127.0.0.1:11/v1/models")
        with self.assertRaises(C.CodexError):
            C.assert_safe_redirect("http://127.0.0.1:11/v1/models", "http://127.0.0.1:11/v1/other")

    def test_parsers_and_transport_against_local_server(self):
        with T.LocalCodexServer(mode="ok") as srv:
            body = json.dumps({"object": "list", "data": [{"id": "m", "object": "model"}]}).encode()
            self.assertEqual(C.parse_catalog_body(body), ["m"])
            with self.assertRaises(C.CodexError):
                C.parse_catalog_body(b'{"data":')
            g = T.LocalCodexServer  # noqa (fixture reference)
            import urllib.request as _u
            # Real transport through the helper against the local server.
            res = C.check_catalog(srv.base, "k")
            self.assertEqual(res["status"], "PASS")
            resh = C.check_health(srv.base)
            self.assertEqual(resh["status"], "PASS")
        with T.LocalCodexServer(mode="auth-denied") as srv2:
            with self.assertRaises(C.CodexAuthDenied):
                C.check_catalog(srv2.base, "k")

    def test_sanitize_never_echoes_opaque(self):
        tok = "opaque-synthetic-token-XYZ987654321abcdef"
        self.assertNotIn(tok, C.sanitize_message(f"echoed {tok}"))
        self.assertNotIn(tok, V._sanitize(f"failed {tok}"))

    def test_shipped_codex_rejects_cross_port_auth_forward(self):
        # Exact shipped transport against two localhost origins: a redirect to
        # another port must fail closed AND the foreign receiver must never
        # observe Authorization.
        import http.server as _hs
        import threading as _th
        seen = []

        class Receiver(_hs.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                seen.append(bool(self.headers.get("Authorization")))
                body = b'{"data":[{"id":"fixture-model"}]}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        recv = _hs.HTTPServer(("127.0.0.1", 0), Receiver)
        _th.Thread(target=recv.serve_forever, daemon=True).start()

        class Redirect(_hs.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(302)
                self.send_header("Location",
                                 f"http://127.0.0.1:{recv.server_port}/catalog")
                self.end_headers()

        origin = _hs.HTTPServer(("127.0.0.1", 0), Redirect)
        _th.Thread(target=origin.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as td:
                sec = Path(td) / "codex.env"
                sec.write_text("CODEX_LB_API_KEY=public-synthetic-nonsecret\n")
                sec.chmod(0o600)
                pr = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "paseo_codex_candidate_check.py"),
                     "--mode", "catalog", "--secret-file", str(sec),
                     "--base-url", f"http://127.0.0.1:{origin.server_port}/v1"],
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                    capture_output=True, text=True, timeout=15)
                self.assertNotEqual(pr.returncode, 0)
                self.assertEqual(len(seen), 0)
        finally:
            origin.shutdown()
            origin.server_close()
            recv.shutdown()
            recv.server_close()
        tok = "opaque-synthetic-token-XYZ987654321abcdef"
        self.assertNotIn(tok, C.sanitize_message(f"echoed {tok}"))
        self.assertNotIn(tok, V._sanitize(f"failed {tok}"))


class MuseAdapterTests(unittest.TestCase):
    def test_fixed_profile_and_guard_policy(self):
        A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "max", False)
        for args in [("codex-lb", "muse-spark-1.3-contributor", "max", False),
                     ("meta", "muse-spark-1.3-contributor", "xhigh", False),
                     ("meta", "muse-spark-1.3-contributor", "max", True)]:
            with self.subTest(args=args), self.assertRaises(A.AdapterError):
                A.validate_requested_profile(*args)
        self.assertTrue(A.guard_identity(ROOT)["sha256"].startswith("sha256:"))
        self.assertEqual(A.policy_identity(ROOT)["profile"]["model"], "muse-spark-1.3-contributor")

    def test_meta_secret_strict_rejects_empty(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            good = td / "m.env"
            good.write_text("META_API_KEY=fixture-meta-key\n")
            good.chmod(0o600)
            self.assertEqual(A.read_dedicated_muse_secret(good), "fixture-meta-key")
            bare = td / "b.env"
            bare.write_text("fixture-bare-meta-key\n")
            bare.chmod(0o400)
            self.assertEqual(A.read_dedicated_muse_secret(bare), "fixture-bare-meta-key")
            empty = td / "e.env"
            empty.write_text("META_API_KEY=\n")
            empty.chmod(0o600)
            with self.assertRaises(A.AdapterError):
                A.read_dedicated_muse_secret(empty)
            wrong = td / "w.env"
            wrong.write_text("MUSE_SPARK_API_KEY=x\n")
            wrong.chmod(0o600)
            with self.assertRaises(A.AdapterError):
                A.read_dedicated_muse_secret(wrong)

    def test_witness_aggregate_request_response_terminal(self):
        tid = "t-aggregate-1"
        evs = [{"test_id": tid, "kind": "request", "provider": "meta", "thinking": "max", "model": "muse-spark-1.3-contributor", "effort": "max"},
               {"test_id": tid, "kind": "response", "status": "200"},
               {"test_id": tid, "kind": "terminal", "status": "completed"},
               {"test_id": tid, "kind": "terminal", "status": "settled"}]
        agg = A.aggregate_witness(evs, test_id=tid, expected_model="muse-spark-1.3-contributor")
        self.assertEqual(agg["gate"], "PASS")
        self.assertEqual(agg["observed"]["thinking"], "max")
        # Response-only loses request fields → UNKNOWN (not silent PASS).
        agg2 = A.aggregate_witness([{"test_id": tid, "kind": "response", "status": "200"}],
                                   test_id=tid, expected_model="muse-spark-1.3-contributor")
        self.assertEqual(agg2["gate"], "UNKNOWN")
        # Clamp effort fails.
        evs3 = [{"test_id": tid, "kind": "request", "provider": "meta", "thinking": "xhigh", "model": "muse-spark-1.3-contributor", "effort": "xhigh"},
                {"test_id": tid, "kind": "response", "status": "200"},
                {"test_id": tid, "kind": "terminal", "status": "done"}]
        self.assertEqual(A.aggregate_witness(evs3, test_id=tid,
                                             expected_model="muse-spark-1.3-contributor")["gate"], "FAIL")
        # Stale/caller events invalidate the ENTIRE private readback.
        with tempfile.TemporaryDirectory() as td:
            wf = Path(td) / "w.jsonl"
            wf.write_text(json.dumps({"test_id": "other", "kind": "request",
                                                "model": "muse-spark-1.3-contributor", "effort": "max"}) + "\n"
                          + json.dumps({"test_id": tid, "kind": "request",
                                                  "model": "muse-spark-1.3-contributor", "effort": "max"}) + "\n")
            with self.assertRaises(A.AdapterError):
                A.load_witness_events(wf, tid)

    def test_dispatch_guarded_test_prompt_form(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            agent = td / "agent"
            (agent / "policies").mkdir(parents=True)
            (agent / "policies" / "llm-test-policy.json").write_bytes(
                (ROOT / "config" / "pi-agent" / "policies" / "llm-test-policy.json").read_bytes())
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            wit = td / "w.jsonl"
            wit.write_text("")
            meta = td / "m.env"
            meta.write_text("META_API_KEY=synthetic-local-key-abc123\n")
            meta.chmod(0o600)
            snap = A.dispatch_guarded_test(guard_file=RUNNER, agent_root=agent,
                                           prompt="SYNTHETIC_PROMPT", cwd=str(td),
                                           bindir=bindir, test_id="t-dispatch-1",
                                           witness_file=wit, meta_secret_file=meta, timeout=30)
            self.assertTrue(snap["dispatched"])
            self.assertFalse(snap.get("timeout", False))
            # No Pi/daemon exists locally: no witness events occur here. The
            # transmitted --env contract is asserted from the recorded argv
            # (first-`=` split, exactly the three nonsecret names, no secret).
            argv = snap.get("dispatch_argv") or []
            self.assertTrue(argv and argv[0] == "run")
            names = []
            prev = None
            for a in argv:
                if prev == "--env":
                    names.append(a.split("=", 1)[0])
                    prev = None
                elif a == "--env":
                    prev = "--env"
                elif a.startswith("--env="):
                    names.append(a[len("--env="):].split("=", 1)[0])
                else:
                    prev = None
            self.assertEqual(sorted(names),
                             ["M07_T05_TEST_ID", "M07_T05_WITNESS_FILE", "META_API_KEY_FILE"])
            # The raw secret value never travels argv (pointer only).
            self.assertNotIn("synthetic-local-key-abc123", " ".join(argv))
            # Missing policy fails closed (no fabrication).
            agent2 = td / "agent2"
            (agent2 / "policies").mkdir(parents=True)
            with self.assertRaises(A.AdapterBlocked):
                A.dispatch_guarded_test(guard_file=RUNNER, agent_root=agent2,
                                        prompt="X", cwd=str(td), bindir=bindir,
                                        test_id="t-missing", witness_file=td / "w2.jsonl",
                                        timeout=10)

    def test_observe_daemon_pi_via_exec(self):
        def exec_daemon(argv, timeout=30):
            self.assertIn("status", argv)
            return mock.Mock(returncode=0, stdout=json.dumps({
                "home": "/home/paseo/.paseo", "listen": "127.0.0.1:1",
                "pid": 7, "daemonVersion": "0.9.2",
                "localDaemon": "running", "connectedDaemon": "reachable",
                "workerPid": 8, "serverId": "synthetic-server", "daemonNode": "/usr/bin/node",
                "providers": ["pi"]}))
        dobs = A.observe_daemon_status(exec_daemon, candidate_home="/home/paseo/.paseo",
                                       expected_version="0.9.2")
        self.assertEqual(dobs["version"], "0.9.2")
        with self.assertRaises(A.AdapterError):
            A.observe_daemon_status(exec_daemon, candidate_home="/home/paseo/.paseo",
                                    expected_version="9.9.9")
        # Stopped/unreachable/remote/null-pid observations fail closed.
        bad_docs = [
            {"home": "/home/paseo/.paseo", "listen": "127.0.0.1:1", "pid": 7,
             "daemonVersion": "0.9.2", "localDaemon": "stopped",
             "connectedDaemon": "unreachable"},
            {"home": "/home/paseo/.paseo", "listen": "203.0.113.10:9999", "pid": None,
             "daemonVersion": "0.9.2", "localDaemon": "stopped",
             "connectedDaemon": "unreachable"},
            {"home": "/home/paseo/.paseo", "listen": "127.0.0.1:1", "pid": None,
             "daemonVersion": "0.9.2"},
            {"home": "/home/paseo/.paseo", "listen": "127.0.0.1:1", "pid": 0,
             "daemonVersion": "0.9.2"},
            {"home": "/foreign/daemon", "listen": "127.0.0.1:1", "pid": 7,
             "daemonVersion": "0.9.2"},
            {"home": "/home/paseo/.paseo", "listen": "", "pid": 7,
             "daemonVersion": "0.9.2"},
        ]
        for doc in bad_docs:
            with self.subTest(doc=doc):
                def _exec(argv, timeout=30, _d=doc):
                    return mock.Mock(returncode=0, stdout=json.dumps(_d))
                with self.assertRaises((A.AdapterError, A.AdapterBlocked)):
                    A.observe_daemon_status(_exec, candidate_home="/home/paseo/.paseo",
                                            expected_version="0.9.2")

        def exec_which(argv, timeout=30):
            return mock.Mock(returncode=0, stdout="/usr/local/bin/pi\n")

        def exec_ver(argv, timeout=30):
            return mock.Mock(returncode=0, stdout="0.87.1\n")

        calls = {"n": 0}

        def exec_pi(argv, timeout=30):
            calls["n"] += 1
            if argv[:2] == ["sh", "-c"]:
                return exec_which(argv, timeout)
            return exec_ver(argv, timeout)

        # Version/PATH strings alone no longer qualify executable bytes.
        with self.assertRaises(A.AdapterBlocked):
            A.observe_pi_version(exec_pi, expected_version="0.87.1")
        # Foreign Pi paths fail closed even with the right version.
        def exec_foreign(argv, timeout=30):
            if argv[:2] == ["sh", "-c"]:
                return mock.Mock(returncode=0, stdout="/foreign/provider/pi\n")
            return mock.Mock(returncode=0, stdout="0.87.1\n")
        with self.assertRaises(A.AdapterError):
            A.observe_pi_version(exec_foreign, expected_version="0.87.1")


class ValidatorMatrixTests(unittest.TestCase):
    def test_wrong_oci_digest_before_disallowed_calls(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            calls = []

            def fake(argv, timeout=300, check=True):
                calls.append(argv)
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout="Digest: sha256:" + "c" * 64 + "\n", stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "FAIL")
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "run"]), 0)
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "exec"]), 0)

    def test_malformed_artifact_chain_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cand_file, _, _, _, _, _ = T.build_artifact_chain(td)
            bad = td / "bad.json"
            bad.write_text('{"candidate_id": "forged"}')
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=lambda *a, **k: mock.Mock(returncode=0, stdout="", stderr="")):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td, execution_class="real",
                                 source_root=ROOT, candidate_file=cand_file, tested_image_file=bad)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))

    def test_native_export_without_dispatch_is_not_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, _ = _run_validate(td, server_base=srv.base)
            self.assertEqual(res["status"], "PASS")
            # Native shape is recorded as export-only; dispatch came from the
            # PROMPT form (muse_dispatch PASS), not the export.
            self.assertEqual(res["subject"].get("muse_native_shape"), "export-only (not dispatch)")
            self.assertEqual(res["checks"].get("muse_dispatch"), "PASS")

    def test_empty_muse_secret_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, _ = _secrets(td)
            empty = td / "empty.env"
            empty.write_text("META_API_KEY=\n")
            empty.chmod(0o600)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = _fixture_chain(
                td, image_id="sha256:" + "b" * 64)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=T.make_fake_docker(
                     digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=[],
                     state={"net_exists": False, "network": "pi-unraid-validator"},
                     server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=codex, muse_secret_host=empty)):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td / "st",
                                 source_root=ROOT, candidate_file=cand_file, muse_secret=empty)
            self.assertEqual(res["status"], "FAIL")

    def test_leaked_token_never_in_output_or_calls(self):
        tok = "fixture-token-xyz-987654321"
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, _ = _run_validate(td, server_base=srv.base)
            blob = json.dumps(res) + " ".join(" ".join(c) for c in calls)
            self.assertNotIn(tok, blob)
            self.assertNotIn("fixture-codex", blob)
            self.assertNotIn("fixture-meta", blob)


class ProbeRegressionTests(unittest.TestCase):
    """Seven old probes stay closed + new finding coverage."""

    def test_probe1_real_missing_inputs_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=lambda *a, **k: mock.Mock(returncode=1, stdout="", stderr="")):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td, execution_class="real")
            self.assertIn(res["status"], ("BLOCKED", "FAIL"))
            self.assertFalse(res["real_validation_satisfied"])

    def test_probe2_foreign_daemon_version_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                # Fake daemon override with foreign version is injected via state.
                codex, muse = _secrets(td)
                cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = _fixture_chain(
                    td, image_id="sha256:" + "b" * 64)
                bindir = T.make_fake_paseo(td / "bindir", effort="max")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit),
                                    "daemon_version": "9.9.9"}
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)

                def wrapped(argv, timeout=300, check=True):
                    if argv[:2] == ["docker", "exec"] and "paseo" in argv and "status" in argv:
                        return mock.Mock(returncode=0, stdout=json.dumps({
                            "home": "/home/paseo/.paseo", "listen": "9.9.9.9:9",
                            "pid": 1, "daemonVersion": "9.9.9"}))
                    return base(argv, timeout=timeout, check=check)

                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=wrapped):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                                     execution_class="fixture", source_root=ROOT,
                                     companion_bundle=_companion_arg(), candidate_file=cand_file,
                                     muse_secret=muse)
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])

    def test_probe3_wrong_running_image(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                codex, muse = _secrets(td)
                cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = _fixture_chain(
                    td, image_id="sha256:" + "b" * 64)
                bindir = T.make_fake_paseo(td / "bindir", effort="max")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit),
                                    "wrong_image": "sha256:" + "c" * 64}
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)

                def wrapped(argv, timeout=300, check=True):
                    if argv[:2] == ["docker", "inspect"] and state.get("ran"):
                        r = base(argv, timeout=timeout, check=check)
                        obj = json.loads(r.stdout)[0]
                        obj["Image"] = "sha256:" + "c" * 64
                        return mock.Mock(returncode=0, stdout=json.dumps([obj]))
                    return base(argv, timeout=timeout, check=check)

                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=wrapped):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     execution_class="fixture", source_root=ROOT,
                                     candidate_file=cand_file)
            self.assertEqual(res["status"], "FAIL")

    def test_probe4_no_repodigests(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            def fake(argv, timeout=300, check=True):
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout=f"Digest: {REAL_OCI_DIGEST}\n", stderr="")
                if argv[:3] == ["docker", "image", "inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0, stdout=json.dumps([]), stderr="")
                    return mock.Mock(returncode=0, stdout="sha256:" + "b" * 64 + "\n", stderr="")
                if argv[:3] == ["docker", "image", "pull"]:
                    return mock.Mock(returncode=0, stdout="", stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "FAIL")

    def test_probe5_secret_only_collision_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            calls = []

            def fake(argv, timeout=300, check=True):
                calls.append(argv)
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout=f"Digest: {REAL_OCI_DIGEST}\n", stderr="")
                if argv[:3] == ["docker", "image", "inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0, stdout=json.dumps(
                            [f"ghcr.io/elmakus/pi-unraid@{REAL_OCI_DIGEST}"]), stderr="")
                    return mock.Mock(returncode=0, stdout="sha256:" + "b" * 64 + "\n", stderr="")
                if argv[:3] == ["docker", "image", "pull"]:
                    return mock.Mock(returncode=0, stdout="", stderr="")
                if argv[:2] == ["docker", "network"]:
                    return mock.Mock(returncode=0, stdout=json.dumps(
                        [{"Labels": {"io.pi-unraid.validator-nonce": "other"}}]), stderr="")
                if argv[:2] == ["docker", "inspect"]:
                    obj = {"Id": "foreign", "Image": "sha256:" + "b" * 64,
                           "Config": {"User": "99:100", "Env": [], "Labels": {}},
                           "HostConfig": {"NetworkMode": "pi-unraid-validator"},
                           "Mounts": [{"Source": "/x", "Destination": V.CODEX_SECRET_TARGET, "RW": False}],
                           "State": {"Status": "running"}}
                    return mock.Mock(returncode=0, stdout=json.dumps([obj]), stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "FAIL")
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "run"]), 0)
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "rm"]), 0)

    def test_probe6_opaque_redacted(self):
        tok = "opaque-fixture-token-XYZ987654321abcdef"
        self.assertNotIn(tok, V._sanitize(f"echoed {tok}"))
        self.assertNotIn(tok, C.sanitize_message(f"echoed {tok}"))

    def test_probe7_missing_policy_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            agent = td / "agent"
            (agent / "policies").mkdir(parents=True)
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            with self.assertRaises(A.AdapterBlocked):
                A.dispatch_guarded_test(guard_file=RUNNER, agent_root=agent, prompt="X",
                                        cwd=str(td), bindir=bindir, test_id="t",
                                        witness_file=td / "w.jsonl", timeout=10)

    def test_clamp_effort_fails_and_unknown_preserves(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                codex, muse = _secrets(td)
                chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
                cand_file = chain[0]
                bindir = T.make_fake_paseo(td / "bindir", effort="xhigh")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit)}
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=base):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                                     execution_class="fixture", source_root=ROOT,
                                     companion_bundle=_companion_arg(), candidate_file=cand_file,
                                     muse_secret=muse)
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])
        # Timeout UNKNOWN keeps exact refs, no resend.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            def fake(argv, timeout=300, check=True):
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    raise V.ValidationUnknown("timeout")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "UNKNOWN")
            self.assertIn("owned_reference", res)

    def test_third_return_regressions(self):
        """Main third-return 11 probes as committed regression coverage.

        Each subtest drives the genuine validator/adapter/observer/transport
        entrypoint with fake-only external boundaries and asserts the required
        failure/classification plus absence of disallowed calls before cleanup.
        """
        # 1. Distinct candidate_id vs OCI digest bind via the publication record.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, _ = _run_validate(td, server_base=srv.base,
                                              execution_class="real")
            self.assertEqual(res["status"], "PASS")
            self.assertTrue(res["real_validation_satisfied"])
            self.assertEqual(res["subject"]["candidate_id"], json.loads((T.fixture_source(td) / 'candidates/paseo-update/candidate.json').read_bytes())['candidate_id'])
            self.assertEqual(res["digest"], REAL_OCI_DIGEST)
            self.assertNotEqual(REAL_CANDIDATE_ID, REAL_OCI_DIGEST)
        # 1b. Publication digest mismatch fails before Docker run/exec.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            pub = json.loads(Path(publication_file).read_text())
            pub["digest"] = "sha256:" + "e" * 64
            Path(publication_file).write_text(json.dumps(pub))
            calls = []
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=T.make_fake_docker(
                     digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=calls,
                     state={"net_exists": False, "network": "pi-unraid-validator"},
                     server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=codex, muse_secret_host=muse)):
                res = V.validate(
                    repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                    output=td / "o.json", state_root=td / "st", execution_class="real",
                    source_root=ROOT, candidate_file=cand_file, handoff_file=handoff_file,
                    build_input_file=build_input_file, tested_image_file=tested_file,
                    build_record=build_record_file, publication_file=publication_file)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "run"]), 0)
        # 2. Tested-only minimal record cannot satisfy real validation.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file = chain[0]
            minimal = td / "minimal.json"
            minimal.write_text(json.dumps({"candidate_id": REAL_CANDIDATE_ID}))
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=T.make_fake_docker(
                     digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=[],
                     state={"net_exists": False, "network": "pi-unraid-validator"},
                     server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=codex, muse_secret_host=muse)):
                res = V.validate(
                    repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                    output=td / "o.json", state_root=td / "st", execution_class="real",
                    source_root=ROOT, candidate_file=cand_file,
                    tested_image_file=minimal, muse_secret=muse)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertFalse(res["real_validation_satisfied"])
        # 3. Forged handoff/prepared provenance fails (build record validated).
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            Path(handoff_file).write_text(json.dumps({
                "candidate_id": REAL_CANDIDATE_ID, "schema_version": 77,
                "status": "failed", "source_sha": "forged", "source_ref": "forged",
                "candidate_file_sha256": "forged"}))
            bad_br = td / "bad-br.json"
            bad_br.write_text("{malformed public fixture")
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=T.make_fake_docker(
                     digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=[],
                     state={"net_exists": False, "network": "pi-unraid-validator"},
                     server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=codex, muse_secret_host=muse)):
                res = V.validate(
                    repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                    output=td / "o.json", state_root=td / "st", execution_class="real",
                    source_root=ROOT, candidate_file=cand_file, handoff_file=handoff_file,
                    build_input_file=build_input_file, tested_image_file=tested_file,
                    build_record=bad_br, publication_file=publication_file,
                    muse_secret=muse)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertFalse(res["real_validation_satisfied"])
        # 4. Stopped/unreachable/remote/null-pid daemon + foreign Pi fails.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, _ = _run_validate(
                    td, server_base=srv.base,
                    daemon_json={"home": "/home/paseo/.paseo",
                               "listen": "203.0.113.10:9999", "pid": None,
                               "daemonVersion": T.REAL_PASEO, "localDaemon": "stopped",
                               "connectedDaemon": "unreachable"},
                    pi_path="/foreign/provider/pi")
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])
            self.assertEqual(sum(1 for c in calls if "guarded-dispatch" in " ".join(c)), 0)
        # 5. Staged loader provisions META_API_KEY (fake requires it, exit 42).
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            dest = td / "loader.sh"
            A.stage_meta_loader(dest)
            subprocess.run([sys.executable, "-m", "py_compile",
                            str(ROOT / "scripts" / "paseo_candidate_muse_adapter.py")],
                           check=True)
            # Missing pointer fails closed before dispatch.
            pr = subprocess.run(
                ["bash", str(dest), "PROMPT", "/tmp"],
                env={"PATH": "/usr/bin:/bin",
                     "META_API_KEY_FILE": str(td / "absent.env")},
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            self.assertEqual(pr.returncode, 42)
            # Empty value fails closed.
            empty = td / "empty.env"
            empty.write_text("META_API_KEY=\n")
            empty.chmod(0o600)
            pr2 = subprocess.run(
                ["bash", str(dest), "PROMPT", "/tmp"],
                env={"PATH": "/usr/bin:/bin", "META_API_KEY_FILE": str(empty)},
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            self.assertEqual(pr2.returncode, 42)
        # 6. Actual staged observer produces the terminal event (node harness).
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            ext = A.stage_witness_extension(td / "observer.mjs")
            wit = td / "w.jsonl"
            wit.write_text("")
            wit.chmod(0o600)
            harness = td / "harness.mjs"
            harness.write_text(
                "import {createRequire} from 'node:module';\n"
                "globalThis.require = createRequire(import.meta.url);\n"
                "const registered = {};\n"
                "const ext = await import(process.argv[2]);\n"
                "ext.default({on: (k, fn) => { registered[k] = fn; }});\n"
                "const controller = new AbortController();\n"
                "await registered.before_provider_request({payload: {model: 'muse-spark-1.3-contributor', reasoning: {effort: 'max'}}}, {model:{provider:'meta', id:'muse-spark-1.3-contributor'}, thinkingLevel:'max', signal:controller.signal, abort:()=>controller.abort()});\n"
                "await registered.after_provider_response({status: 200, headers: {}});\n"
                "await registered.turn_end({outcome: 'completed', turnIndex: 0, message: {}, toolResults: []});\n"
                "await registered.agent_end({messages: [{role: 'assistant', stopReason: 'stop', content: []}]});\n"
                "if (registered.agent_settled) { await registered.agent_settled({}); }\n"
                "console.log(JSON.stringify({handlers: Object.keys(registered)}));\n")
            pr = subprocess.run(
                [shutil.which("node"), str(harness), str(ext)],
                env={"M07_T05_TEST_ID": "public-test", "M07_T05_WITNESS_FILE": str(wit)},
                text=True, capture_output=True, timeout=20, check=True)
            handlers = json.loads(pr.stdout)["handlers"]
            self.assertIn("before_provider_request", handlers)
            self.assertIn("after_provider_response", handlers)
            self.assertIn("turn_end", handlers)
            self.assertIn("agent_end", handlers)
            self.assertIn("agent_settled", handlers)
            events = A.load_witness_events(wit, "public-test")
            kinds = {e["kind"] for e in events}
            self.assertIn("request", kinds)
            self.assertIn("response", kinds)
            self.assertIn("terminal", kinds)
            agg = A.aggregate_witness(events, test_id="public-test",
                                      expected_model=A.FIXED_MODEL)
            self.assertEqual(agg["gate"], "PASS")
            # Settled-only (no turn/agent_end outcome) never proves success.
            agg_settled = A.aggregate_witness(
                [e for e in events if e["kind"] != "terminal"] +
                [e for e in events if e["kind"] == "terminal" and e.get("status") == "settled"],
                test_id="public-test", expected_model=A.FIXED_MODEL)
            self.assertEqual(agg_settled["gate"], "UNKNOWN")
        # 7. Missing terminal stays UNKNOWN; container preserved; refs usable.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, state = _run_validate(td, server_base=srv.base,
                                                  omit_terminal=True)
            self.assertEqual(res["status"], "UNKNOWN")
            self.assertEqual(res["terminal_class"], "unknown")
            self.assertFalse(res["real_validation_satisfied"])
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "rm"]), 0)
            ref = res.get("owned_reference")
            self.assertTrue(ref and Path(ref).is_file())
            self.assertIsNotNone(res.get("owned_container"))
        # 8. UNKNOWN retains an existing owned test file (written pre-dispatch).
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, _, _ = _run_validate(td, server_base=srv.base,
                                          omit_terminal=True,
                                          execution_class="real")
            self.assertEqual(res["status"], "UNKNOWN")
            ref = res.get("owned_reference")
            self.assertTrue(ref and Path(ref).is_file())
            doc = json.loads(Path(ref).read_text())
            self.assertIn("test_id", doc)
            self.assertIn("container", doc)
        # 9. Replaced container Id fails; foreign object never removed by name.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, _ = _run_validate(td, server_base=srv.base,
                                              execution_class="real",
                                              replaced_id="replaced-foreign-object")
            # The initial acquisition check sees the replaced Id (fake returns it
            # for every inspect after run): replacement detected before exec.
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertFalse(res["real_validation_satisfied"])
            rms = [c for c in calls if c[:2] == ["docker", "rm"]]
            for rm in rms:
                self.assertNotIn("replaced-foreign-object", " ".join(rm))
        # 10. Nonzero ownership inspection after dispatch blocks readback
        # (ownership unverifiable) while preserving work/container.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, state = _run_validate(td, server_base=srv.base,
                                                  fail_cleanup_inspect=True)
            self.assertEqual(res["status"], "BLOCKED")
            self.assertFalse(res["real_validation_satisfied"])
            work = state.get("work")
            self.assertTrue(work and Path(work).exists())
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "rm"]), 0)
        # 11. Cross-origin Codex redirect covered in CodexHelperTests
        # (test_shipped_codex_rejects_cross_port_auth_forward).
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                codex, muse = _secrets(td)
                cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = _fixture_chain(
                    td, image_id="sha256:" + "b" * 64)
                bindir = T.make_fake_paseo(td / "bindir", effort="xhigh")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit)}
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=base):
                    res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                                     execution_class="fixture", source_root=ROOT,
                                     companion_bundle=_companion_arg(), candidate_file=cand_file,
                                     muse_secret=muse)
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])
        # Timeout UNKNOWN keeps exact refs, no resend.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            def fake(argv, timeout=300, check=True):
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    raise V.ValidationUnknown("timeout")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "UNKNOWN")
            self.assertIn("owned_reference", res)


class FourthReturnRegressionTests(unittest.TestCase):
    """Main fourth-return probes as committed regression coverage.

    Each trial drives the genuine validator/adapter/observer/transport
    entrypoint with fake-only external boundaries. Positives run the actual
    staged guard/loader/observer bytes plus the supported `--env` argv
    contract, daemon bring-up, and owned-child ls/inspect binding. Negatives
    assert required failure/classification plus absence of disallowed calls
    before cleanup. No real inference, auth, or live effects occur.
    """

    def test_forged_producer_chain_fails(self):
        import hashlib as _hl
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            hand = json.loads(Path(handoff_file).read_text())
            hand.update(source_sha="not-a-git-sha", source_ref="not-an-approved-ref")
            hand.pop("candidate_file_sha256")
            Path(handoff_file).write_text(json.dumps(hand))
            hfs = "sha256:" + _hl.sha256(Path(handoff_file).read_bytes()).hexdigest()
            bi = json.loads(Path(build_input_file).read_text())
            bi.update(source_head="not-current-source", source_parent="other-parent",
                      source_ref="other-ref", accepted_candidate_id="wrong-accepted")
            bi.pop("candidate_file_sha256")
            bi["handoff_evidence_sha256"] = hfs
            bi["companion_bundle"]["modes"]["bin/run-llm-test.sh"] = "0644"
            Path(build_input_file).write_text(json.dumps(bi))
            br = json.loads(Path(build_record_file).read_text())
            br.update(schema_version=99, command="not-a-build")
            br["phases"]["test"]["status"] = "failed"
            br["image"]["candidate_label"] = "wrong-candidate"
            Path(build_record_file).write_text(json.dumps(br))
            tested = json.loads(Path(tested_file).read_text())
            tested.update(schema_version=99, source_head="other-head",
                          discovery_source_sha="other-source", discovery_source_ref="other-ref")
            tested.pop("candidate_file_sha256")
            tested["handoff_evidence_sha256"] = hfs
            tested["build_record_sha256"] = "sha256:" + _hl.sha256(Path(build_record_file).read_bytes()).hexdigest()
            Path(tested_file).write_text(json.dumps(tested))
            pub = json.loads(Path(publication_file).read_text())
            pub.update(schema_version=99, candidate_file_sha256="forged",
                       build_record_sha256="forged", tested_image_evidence_sha256="forged",
                       source_head="wrong-head", discovery_source_sha="wrong-parent")
            Path(publication_file).write_text(json.dumps(pub))
            calls = []
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=T.make_fake_docker(
                     digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64, calls=calls,
                     state={"net_exists": False, "network": "pi-unraid-validator"},
                     server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=codex, muse_secret_host=muse)):
                res = V.validate(
                    repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                    output=td / "o.json", state_root=td / "st", execution_class="real",
                    source_root=T.fixture_source(td), candidate_file=cand_file, handoff_file=handoff_file,
                    build_input_file=build_input_file, tested_image_file=tested_file,
                    build_record=build_record_file, publication_file=publication_file,
                    muse_secret=muse)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertFalse(res["real_validation_satisfied"])
            for check, outcome in (res.get("checks") or {}).items():
                self.assertNotEqual(outcome, "PASS", check)
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "run"]), 0)
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "exec"]), 0)

    def test_separate_cli_daemon_boundary_transmits_env(self):
        # Faithful split: the CLI fake parses --env exactly like pinned
        # run.js and ignores ambient env. Isolation lives at the container
        # boundary (docker run -e carries no M07_T05_*; only the validator's
        # exec command sets them for the guard): with none set, nothing is
        # transmitted and no dispatch occurs; with the exec-supplied triple,
        # exactly the three nonsecret names transmit, never a raw secret.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            disp = td / "argv.txt"
            env = {"PATH": str(bindir), "DISPATCH_MARKER": str(disp)}
            pr = subprocess.run(
                ["bash", str(ROOT / "config" / "pi-agent" / "bin" / "run-llm-test.sh"),
                 "SYNTHETIC_PROMPT", "/tmp"],
                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30)
            self.assertEqual(pr.returncode, 42)
            self.assertEqual(T.transmitted_env_names(disp), [])
            env2 = dict(env, META_API_KEY="synthetic-loader-key",
                        M07_T05_TEST_ID="t-sep-1",
                        M07_T05_WITNESS_FILE="/tmp/m07-t05-witness.jsonl",
                        META_API_KEY_FILE="/run/secrets/pi-unraid-meta")
            pr2 = subprocess.run(
                ["bash", str(ROOT / "config" / "pi-agent" / "bin" / "run-llm-test.sh"),
                 "SYNTHETIC_PROMPT", "/tmp"],
                env=env2, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30)
            self.assertEqual(pr2.returncode, 0)
            self.assertEqual(sorted(T.transmitted_env_names(disp)),
                             ["M07_T05_TEST_ID", "M07_T05_WITNESS_FILE", "META_API_KEY_FILE"])
            self.assertNotIn("synthetic-loader-key", disp.read_text())

    def test_aborted_completion_fails_despite_settled(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, _, _ = _run_validate(td, server_base=srv.base,
                                          execution_class="real",
                                          witness_turn="aborted")
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])

    def test_garbage_response_status_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, _, _ = _run_validate(td, server_base=srv.base,
                                          execution_class="real",
                                          witness_response="garbage")
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])
        # Direct aggregator contract: malformed status never proves success.
        ev = [{"test_id": "t-g", "kind": "request", "provider": "meta", "thinking": "max", "model": A.FIXED_MODEL, "effort": "max"},
              {"test_id": "t-g", "kind": "response", "status": "garbage"},
              {"test_id": "t-g", "kind": "terminal", "status": "done"}]
        self.assertEqual(A.aggregate_witness(ev, test_id="t-g",
                                             expected_model=A.FIXED_MODEL)["gate"], "FAIL")

    def test_staged_policy_drift_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with T.LocalCodexServer(mode="ok") as srv:
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)

                drifted = {"done": False}

                def wrapped(argv, timeout=300, check=True):
                    if argv[:2] == ["docker", "exec"] and "file-readback" in argv[-1] and not drifted["done"]:
                        pol = Path(state["work"] + "/home/.pi/agent/policies/llm-test-policy.json")
                        doc = json.loads(pol.read_text())
                        doc["unbound_synthetic_field"] = True
                        pol.write_text(json.dumps(doc))
                        pol.chmod(0o666)
                        drifted["done"] = True
                    return base(argv, timeout=timeout, check=check)

                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=wrapped):
                    res = V.validate(
                        repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                        output=td / "o.json", state_root=td / "st", execution_class="real",
                        source_root=T.fixture_source(td), companion_bundle=_companion_arg(),
                        candidate_file=cand_file, handoff_file=handoff_file,
                        build_input_file=build_input_file, tested_image_file=tested_file,
                        build_record=build_record_file, publication_file=publication_file,
                        codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                        muse_secret=muse)
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])

    def test_replacement_after_observation_blocks_all_later_execs(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            with T.LocalCodexServer(mode="ok") as srv:
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)

                def wrapped(argv, timeout=300, check=True):
                    if argv[:2] == ["docker", "exec"] and state.get("replaced_id"):
                        state["post_replacement_execs"] = state.get("post_replacement_execs", 0) + 1
                    result = base(argv, timeout=timeout, check=check)
                    if argv[:2] == ["docker", "exec"] and argv[-2:] == ["pi", "--version"]:
                        state["replaced_id"] = "different-foreign-object"
                    return result

                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=wrapped):
                    res = V.validate(
                        repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                        output=td / "o.json", state_root=td / "st", execution_class="real",
                        source_root=T.fixture_source(td), companion_bundle=_companion_arg(),
                        candidate_file=cand_file, handoff_file=handoff_file,
                        build_input_file=build_input_file, tested_image_file=tested_file,
                        build_record=build_record_file, publication_file=publication_file,
                        codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                        muse_secret=muse)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertFalse(res["real_validation_satisfied"])
            # Execs after replacement are blocked by per-exec ID verification:
            # the foreign object receives zero successful execs and no rm.
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "rm"]), 0)

    def test_foreign_secret_source_fails_ownership(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit)}
            other = td / "different-operator-input.env"
            other.write_text("CODEX_LB_API_KEY=other-synthetic\n")
            other.chmod(0o600)
            with T.LocalCodexServer(mode="ok") as srv:
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)

                def wrapped(argv, timeout=300, check=True):
                    result = base(argv, timeout=timeout, check=check)
                    if argv[:2] == ["docker", "inspect"] and state.get("ran") and result.returncode == 0:
                        docs = json.loads(result.stdout)
                        for mnt in docs[0]["Mounts"]:
                            if mnt["Destination"] in (V.CODEX_SECRET_TARGET, V.MUSE_SECRET_TARGET):
                                mnt["Source"] = str(other)
                        result.stdout = json.dumps(docs)
                    return result

                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=wrapped):
                    res = V.validate(
                        repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                        output=td / "o.json", state_root=td / "st", execution_class="real",
                        source_root=T.fixture_source(td), companion_bundle=_companion_arg(),
                        candidate_file=cand_file, handoff_file=handoff_file,
                        build_input_file=build_input_file, tested_image_file=tested_file,
                        build_record=build_record_file, publication_file=publication_file,
                        codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                        muse_secret=muse)
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertFalse(res["real_validation_satisfied"])
            self.assertEqual(sum(1 for c in calls if "guarded-dispatch" in " ".join(c)), 0)

    def test_replaced_network_id_is_never_removed(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            codex, muse = _secrets(td)
            chain = _fixture_chain(td, image_id="sha256:" + "b" * 64)
            cand_file, handoff_file, build_input_file, tested_file, build_record_file, publication_file = chain
            bindir = T.make_fake_paseo(td / "bindir", effort="max")
            wit = td / "witness.jsonl"
            wit.write_text("")
            calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                "bindir": str(bindir), "witness_host": str(wit),
                                "replaced_network_id": "different-foreign-network"}
            with T.LocalCodexServer(mode="ok") as srv:
                base = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=base):
                    res = V.validate(
                        repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                        output=td / "o.json", state_root=td / "st", execution_class="real",
                        source_root=T.fixture_source(td), companion_bundle=_companion_arg(),
                        candidate_file=cand_file, handoff_file=handoff_file,
                        build_input_file=build_input_file, tested_image_file=tested_file,
                        build_record=build_record_file, publication_file=publication_file,
                        codex_secret=codex, codex_base_url=srv.base, codex_model="m",
                        muse_secret=muse)
            self.assertFalse(res["real_validation_satisfied"])
            self.assertIn(res["status"], ("FAIL", "BLOCKED"))
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "exec"]), 0)
            rms = [c for c in calls if c[:2] == ["docker", "network", "rm"]]
            self.assertEqual(rms, [])

    def test_nonnumeric_endpoint_and_pseudo_pi_path(self):
        # 127.attacker.invalid is not an IP literal: rejected without DNS.
        with self.assertRaises(A.AdapterError):
            A._require_candidate_local_endpoint("127.attacker.invalid:9")
        # A well-formed absolute Pi path passes the structural predicate;
        # it is recorded as observed-not-proven (binding comes from the
        # bring-up/version/agent-inspect chain, never the string alone).
        A._require_candidate_local_pi_path("/operator/providers/pi")
        with self.assertRaises(A.AdapterError):
            A._require_candidate_local_pi_path("/foreign/provider/pi")
        # Remote daemon + foreign Pi through the genuine entrypoint FAILS.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, _ = _run_validate(
                    td, server_base=srv.base, execution_class="real",
                    daemon_json={"home": "/home/paseo/.paseo", "listen": "203.0.113.10:9999",
                               "pid": None, "daemonVersion": T.REAL_PASEO,
                               "localDaemon": "stopped", "connectedDaemon": "unreachable"},
                    pi_path="/foreign/provider/pi")
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])
            self.assertEqual(sum(1 for c in calls if "guarded-dispatch" in " ".join(c)), 0)

    def test_clamped_actual_snapshot_prevents_prompt_and_preserves_ids(self):
        # Native creation has no initialPrompt. A clamped actual snapshot
        # fails before any prompt/witness; acquired IDs remain usable.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, calls, state = _run_validate(td, server_base=srv.base,
                                          execution_class="real",
                                          agent_thinking="xhigh")
            self.assertEqual(res["status"], "UNKNOWN")
            self.assertNotIn('prompt', state['_owned_runtime'].calls())
            self.assertFalse(any(c[:2] == ['docker', 'rm'] for c in calls))
            self.assertFalse(res["real_validation_satisfied"])

    def test_encoded_inference_redirect_reaches_nothing(self):
        import http.server as _hs
        import threading as _th
        seen = []

        class H(_hs.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path == "/v1/models":
                    self.send_response(302)
                    self.send_header("Location", "/v1/%72esponses")
                    self.end_headers()
                    return
                seen.append((self.path, bool(self.headers.get("Authorization"))))
                body = b'{"data":[{"id":"fixture-model"}]}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = _hs.HTTPServer(("127.0.0.1", 0), H)
        _th.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as td:
                sec = Path(td) / "c.env"
                sec.write_text("CODEX_LB_API_KEY=public-synthetic-nonsecret\n")
                sec.chmod(0o600)
                pr = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "paseo_codex_candidate_check.py"),
                     "--mode", "catalog", "--secret-file", str(sec),
                     "--base-url", f"http://127.0.0.1:{server.server_port}/v1"],
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                    capture_output=True, text=True, timeout=15)
                self.assertNotEqual(pr.returncode, 0)
                self.assertEqual(json.loads(pr.stdout)["status"], "FAIL")
                self.assertEqual(seen, [])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
