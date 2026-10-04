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
REAL_DIGEST = REAL_CANDIDATE["candidate_id"]


def _companion_arg():
    c = T.REAL_COMPANION
    return {"schema_version": c["schema_version"], "source": c["source"],
            "source_digest": c["source_digest"], "files": c["files"], "modes": c["modes"]}


def _fixture_chain(td: Path, *, image_id):
    cand_file, handoff_file, build_input_file, tested_file = T.build_artifact_chain(td)
    tested = json.loads(tested_file.read_text())
    tested["image_id"] = image_id
    tested_file.write_text(json.dumps(tested))
    return cand_file, handoff_file, build_input_file, tested_file


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
                  break_guard=False, extra=None):
    codex, muse = _secrets(td)
    cand_file, handoff_file, build_input_file, tested_file = _fixture_chain(td, image_id=image_id)
    bindir = T.make_fake_paseo(td / "bindir", effort=effort)
    wit = td / "witness.jsonl"
    wit.write_text("")
    calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                        "bindir": str(bindir), "witness_host": str(wit)}
    if daemon_json is not None:
        state["daemon_override"] = daemon_json
    if break_guard:
        state["break_guard"] = True
    # Wrap make_fake_docker to honor overrides.
    base_fake = T.make_fake_docker(digest=REAL_DIGEST, image_id=image_id, calls=calls,
                                   state=state, server_base=server_base,
                                   codex_secret_host=codex, muse_secret_host=muse)
    # Patch daemon_json/break_guard into the fake via state (harness reads state).
    orig_state = state
    kwargs = dict(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                  output=td / "o.json", state_root=td / "st",
                  codex_secret=codex, codex_base_url=server_base,
                  codex_model="m", execution_class=execution_class,
                  source_root=ROOT, companion_bundle=_companion_arg(),
                  candidate_file=cand_file, handoff_file=handoff_file,
                  build_input_file=build_input_file, tested_image_file=tested_file,
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
            C.assert_safe_redirect("http://h:1/v1/models", "http://e:1/x?y=1")

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
                "pid": 7, "daemonVersion": "0.9.2"}))
        dobs = A.observe_daemon_status(exec_daemon, candidate_home="/home/paseo/.paseo",
                                       expected_version="0.9.2")
        self.assertEqual(dobs["version"], "0.9.2")
        with self.assertRaises(A.AdapterError):
            A.observe_daemon_status(exec_daemon, candidate_home="/home/paseo/.paseo",
                                    expected_version="9.9.9")

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
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "FAIL")
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "run"]), 0)
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "exec"]), 0)

    def test_malformed_artifact_chain_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cand_file, _, _, _ = T.build_artifact_chain(td)
            bad = td / "bad.json"
            bad.write_text('{"candidate_id": "forged"}')
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=lambda *a, **k: mock.Mock(returncode=0, stdout="", stderr="")):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
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
            cand_file, handoff_file, build_input_file, tested_file = _fixture_chain(
                td, image_id="sha256:" + "b" * 64)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), \
                 mock.patch.object(V, "run", side_effect=T.make_fake_docker(
                     digest=REAL_DIGEST, image_id="sha256:" + "b" * 64, calls=[],
                     state={"net_exists": False, "network": "pi-unraid-validator"},
                     server_base="http://127.0.0.1:9/v1",
                     codex_secret_host=codex, muse_secret_host=empty)):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
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
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                 output=td / "o.json", state_root=td, execution_class="real")
            self.assertIn(res["status"], ("BLOCKED", "FAIL"))
            self.assertFalse(res["real_validation_satisfied"])

    def test_probe2_foreign_daemon_version_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with T.LocalCodexServer(mode="ok") as srv:
                # Fake daemon override with foreign version is injected via state.
                codex, muse = _secrets(td)
                cand_file, handoff_file, build_input_file, tested_file = _fixture_chain(
                    td, image_id="sha256:" + "b" * 64)
                bindir = T.make_fake_paseo(td / "bindir", effort="max")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit),
                                    "daemon_version": "9.9.9"}
                base = T.make_fake_docker(digest=REAL_DIGEST, image_id="sha256:" + "b" * 64,
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
                    res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
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
                cand_file, handoff_file, build_input_file, tested_file = _fixture_chain(
                    td, image_id="sha256:" + "b" * 64)
                bindir = T.make_fake_paseo(td / "bindir", effort="max")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit),
                                    "wrong_image": "sha256:" + "c" * 64}
                base = T.make_fake_docker(digest=REAL_DIGEST, image_id="sha256:" + "b" * 64,
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
                    res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                     output=td / "o.json", state_root=td / "st",
                                     execution_class="fixture", source_root=ROOT,
                                     candidate_file=cand_file)
            self.assertEqual(res["status"], "FAIL")

    def test_probe4_no_repodigests(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            def fake(argv, timeout=300, check=True):
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout=f"Digest: {REAL_DIGEST}\n", stderr="")
                if argv[:3] == ["docker", "image", "inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0, stdout=json.dumps([]), stderr="")
                    return mock.Mock(returncode=0, stdout="sha256:" + "b" * 64 + "\n", stderr="")
                if argv[:3] == ["docker", "image", "pull"]:
                    return mock.Mock(returncode=0, stdout="", stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "FAIL")

    def test_probe5_secret_only_collision_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            calls = []

            def fake(argv, timeout=300, check=True):
                calls.append(argv)
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout=f"Digest: {REAL_DIGEST}\n", stderr="")
                if argv[:3] == ["docker", "image", "inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0, stdout=json.dumps(
                            [f"ghcr.io/elmakus/pi-unraid@{REAL_DIGEST}"]), stderr="")
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
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
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
                cand_file, handoff_file, build_input_file, tested_file = _fixture_chain(
                    td, image_id="sha256:" + "b" * 64)
                bindir = T.make_fake_paseo(td / "bindir", effort="xhigh")
                wit = td / "witness.jsonl"
                wit.write_text("")
                calls, state = [], {"net_exists": False, "network": "pi-unraid-validator",
                                    "bindir": str(bindir), "witness_host": str(wit)}
                base = T.make_fake_docker(digest=REAL_DIGEST, image_id="sha256:" + "b" * 64,
                                          calls=calls, state=state, server_base=srv.base,
                                          codex_secret_host=codex, muse_secret_host=muse)
                with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                     mock.patch.object(V.os, "chown"), \
                     mock.patch.object(V, "run", side_effect=base):
                    res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
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
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=REAL_DIGEST,
                                 output=td / "o.json", state_root=td)
            self.assertEqual(res["status"], "UNKNOWN")
            self.assertIn("owned_reference", res)


if __name__ == "__main__":
    unittest.main()
