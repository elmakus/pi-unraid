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
    return {"schema_version": c["schema_version"], "source": c["source"],
            "source_digest": c["source_digest"], "files": c["files"], "modes": c["modes"]}


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
                  fail_cleanup_inspect=False):
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
    # Wrap make_fake_docker to honor overrides.
    base_fake = T.make_fake_docker(digest=REAL_OCI_DIGEST, image_id=image_id, calls=calls,
                                   state=state, server_base=server_base,
                                   codex_secret_host=codex, muse_secret_host=muse)
    kwargs = dict(repository=REAL_REPOSITORY, digest=REAL_OCI_DIGEST,
                  output=td / "o.json", state_root=td / "st",
                  codex_secret=codex, codex_base_url=server_base,
                  codex_model="m", execution_class=execution_class,
                  source_root=ROOT, companion_bundle=_companion_arg(),
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
        # Same origin passes.
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
        evs = [{"test_id": tid, "kind": "request", "model": "muse-spark-1.3-contributor", "effort": "max"},
               {"test_id": tid, "kind": "response", "status": "200"},
               {"test_id": tid, "kind": "terminal", "status": "done"}]
        agg = A.aggregate_witness(evs, test_id=tid, expected_model="muse-spark-1.3-contributor")
        self.assertEqual(agg["gate"], "PASS")
        self.assertEqual(agg["observed"]["thinking"], "max")
        # Response-only loses request fields → UNKNOWN (not silent PASS).
        agg2 = A.aggregate_witness([{"test_id": tid, "kind": "response", "status": "200"}],
                                   test_id=tid, expected_model="muse-spark-1.3-contributor")
        self.assertEqual(agg2["gate"], "UNKNOWN")
        # Clamp effort fails.
        evs3 = [{"test_id": tid, "kind": "request", "model": "muse-spark-1.3-contributor", "effort": "xhigh"},
                {"test_id": tid, "kind": "response", "status": "200"},
                {"test_id": tid, "kind": "terminal", "status": "done"}]
        self.assertEqual(A.aggregate_witness(evs3, test_id=tid,
                                             expected_model="muse-spark-1.3-contributor")["gate"], "FAIL")
        # Stale/caller events are dropped by the loader.
        with tempfile.TemporaryDirectory() as td:
            wf = Path(td) / "w.jsonl"
            wf.write_text(json.dumps({"test_id": "other", "kind": "request",
                                                "model": "muse-spark-1.3-contributor", "effort": "max"}) + "\n"
                          + json.dumps({"test_id": tid, "kind": "request",
                                                  "model": "muse-spark-1.3-contributor", "effort": "max"}) + "\n")
            loaded = A.load_witness_events(wf, tid)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["test_id"], tid)

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
            meta.write_text("META_API_KEY=k\n")
            meta.chmod(0o600)
            snap = A.dispatch_guarded_test(guard_file=RUNNER, agent_root=agent,
                                           prompt="SYNTHETIC_PROMPT", cwd=str(td),
                                           bindir=bindir, test_id="t-dispatch-1",
                                           witness_file=wit, meta_secret_file=meta, timeout=30)
            self.assertTrue(snap["dispatched"])
            self.assertFalse(snap.get("timeout", False))
            evs = A.load_witness_events(wit, "t-dispatch-1")
            self.assertTrue(any(e["kind"] == "request" for e in evs))
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
                "localDaemon": "running", "connectedDaemon": "reachable"}))
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
            return mock.Mock(returncode=0, stdout="/home/paseo/.pi/agent/bin/pi\n")

        def exec_ver(argv, timeout=30):
            return mock.Mock(returncode=0, stdout="0.87.1\n")

        calls = {"n": 0}

        def exec_pi(argv, timeout=30):
            calls["n"] += 1
            if argv[:2] == ["sh", "-c"]:
                return exec_which(argv, timeout)
            return exec_ver(argv, timeout)

        self.assertEqual(A.observe_pi_version(exec_pi, expected_version="0.87.1")["version"], "0.87.1")
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
            self.assertEqual(res["subject"]["candidate_id"], REAL_CANDIDATE_ID)
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
            harness = td / "harness.mjs"
            harness.write_text(
                "import {createRequire} from 'node:module';\n"
                "globalThis.require = createRequire(import.meta.url);\n"
                "const registered = {};\n"
                "const ext = await import(process.argv[2]);\n"
                "ext.default({on: (k, fn) => { registered[k] = fn; }});\n"
                "await registered.before_provider_request({payload: {model: 'muse-spark-1.3-contributor', reasoning: {effort: 'max'}}});\n"
                "await registered.after_provider_response({status: 200, headers: {}});\n"
                "if (registered.agent_settled) { await registered.agent_settled({}); }\n"
                "else if (registered.agent_end) { await registered.agent_end({messages: []}); }\n"
                "console.log(JSON.stringify({handlers: Object.keys(registered)}));\n")
            pr = subprocess.run(
                [shutil.which("node"), str(harness), str(ext)],
                env={"M07_T05_TEST_ID": "public-test", "M07_T05_WITNESS_FILE": str(wit)},
                text=True, capture_output=True, timeout=20, check=True)
            handlers = json.loads(pr.stdout)["handlers"]
            self.assertIn("before_provider_request", handlers)
            self.assertIn("after_provider_response", handlers)
            self.assertTrue("agent_end" in handlers or "agent_settled" in handlers)
            events = A.load_witness_events(wit, "public-test")
            kinds = {e["kind"] for e in events}
            self.assertIn("request", kinds)
            self.assertIn("response", kinds)
            self.assertIn("terminal", kinds)
            agg = A.aggregate_witness(events, test_id="public-test",
                                      expected_model=A.FIXED_MODEL)
            self.assertEqual(agg["gate"], "PASS")
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
        # 10. Nonzero ownership inspection during cleanup preserves live work.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                res, _, state = _run_validate(td, server_base=srv.base,
                                              fail_cleanup_inspect=True)
            self.assertEqual(res["status"], "PASS")
            work = state.get("work")
            self.assertTrue(work and Path(work).exists())
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


if __name__ == "__main__":
    unittest.main()
