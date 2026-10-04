"""M07-T05 validator/adapter synthetic matrix (no real inference).

Classification: every touched inference-capable entrypoint is exercised
only through fake-only executables, disposable temp roots, or approved
non-inference source readback. No test here causes provider inference,
reads ordinary-agent credentials, mutates installed HOME/runtime, touches
live Docker/Tower/host/production, builds/publishes images, triggers CI,
or performs PR/Issue work.

- config/pi-agent/bin/run-llm-test.sh PROMPT [CWD]: NEVER executed with a
  real prompt; only invoked with synthetic markers through a test-owned
  bindir holding a fake `paseo` (records dispatch, never calls a provider).
  Negative cases assert absence of dispatch BEFORE temp cleanup.
- config/pi-agent/bin/run-llm-test.sh --native-create-agent-args: executed
  without inference; emits caller-scoped shape only, never dispatches.
- paseo run / paseo status / paseo daemon / pi --model / pi --list-models:
  NEVER executed as real binaries; only faked in bindir or mocked.
- scripts/paseo_tower_validator.validate: exercised via mocked `docker`
  (stateful fake) and disposable state roots; no daemon is contacted.
- scripts/paseo_codex_noninference.*: exercised via injected `http_get`
  fixtures and temp secret files with synthetic keys; no provider is contacted.
- scripts/verify-codex-lb-integration.sh, live RPC/activation harnesses,
  docker builds, Tower live state: NOT executed, NOT imported.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
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

RUNNER = ROOT / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
POLICY_FILE = ROOT / "config" / "pi-agent" / "policies" / "llm-test-policy.json"


def stateful_docker(digest, image_id, *, catalog_rc=0, health_rc=0, calls=None):
    calls_list = calls if calls is not None else []
    state = {"ran": False}
    def fake(argv, timeout=300, check=True):
        calls_list.append(argv)
        if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
            return mock.Mock(returncode=0, stdout=f"Digest: {digest}\n", stderr="")
        if argv[:3] == ["docker", "image", "inspect"]:
            if "{{json .RepoDigests}}" in " ".join(argv):
                return mock.Mock(returncode=0, stdout=json.dumps([f"ghcr.io/elmakus/pi-unraid@{digest}"]), stderr="")
            return mock.Mock(returncode=0, stdout=image_id + "\n", stderr="")
        if argv[:3] == ["docker", "image", "pull"]:
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "network"]:
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "inspect"]:
            if not state["ran"]:
                return mock.Mock(returncode=1, stdout="", stderr="No such object")
            run_call = next(x for x in calls_list if x[:2] == ["docker", "run"])
            mounts = []
            for i, x in enumerate(run_call):
                if x == "-v":
                    parts = run_call[i+1].split(":")
                    mounts.append({"Source": parts[0], "Destination": parts[1], "RW": (parts[2] if len(parts) > 2 else "rw") != "ro"})
            obj = {"Config": {"User": "99:100", "Env": ["HOME=/home/paseo"]},
                   "HostConfig": {"NetworkMode": "pi-unraid-validator"},
                   "Mounts": mounts, "State": {"Status": "running", "Health": {"Status": "healthy"}}}
            return mock.Mock(returncode=0, stdout=json.dumps([obj]), stderr="")
        if argv[:2] == ["docker", "run"]:
            state["ran"] = True
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "exec"]:
            if "/tmp/codex-catalog.json" in argv[-1]:
                return mock.Mock(returncode=catalog_rc, stdout="", stderr="")
            if "/tmp/codex-health.json" in argv[-1]:
                return mock.Mock(returncode=health_rc, stdout="", stderr="")
            return mock.Mock(returncode=0, stdout="", stderr="")
        if argv[:2] == ["docker", "rm"]:
            return mock.Mock(returncode=0, stdout="", stderr="")
        return mock.Mock(returncode=0, stdout="", stderr="")
    return fake, calls_list, state


def fake_http(mapping):
    """mapping: url_substring -> (status, body_bytes) or Exception instance."""
    calls = []
    def getter(url, headers, timeout):
        calls.append((url, dict(headers)))
        # Inference must never be requested.
        low = url.lower()
        assert "/responses" not in low and "/chat/completions" not in low, f"inference attempted: {url}"
        for key, val in mapping.items():
            if key in url:
                if isinstance(val, Exception):
                    raise val
                return val
        raise AssertionError(f"unexpected url: {url}")
    getter.calls = calls
    return getter


class CodexNonInferenceTests(unittest.TestCase):
    def test_base_url_must_end_in_v1_and_reject_inference(self):
        self.assertEqual(C.validate_base_url("http://host:1/v1"), "http://host:1/v1")
        self.assertEqual(C.validate_base_url("https://x.example/v1/"), "https://x.example/v1")
        for bad in ("http://host:1/v1/responses", "http://host:1/v1/chat/completions",
                    "http://host:1/api", "not a url", "http://host:1/v1?x=1", ""):
            with self.subTest(bad=bad), self.assertRaises(C.CodexError):
                C.validate_base_url(bad)

    def test_model_id_rejects_whitespace(self):
        self.assertEqual(C.validate_model_id("fixture-model"), "fixture-model")
        for bad in ("", "  ", "a b", "a\nb", None):
            with self.subTest(bad=bad), self.assertRaises(C.CodexError):
                C.validate_model_id(bad)

    def test_secret_requires_private_regular_file(self):
        with tempfile.TemporaryDirectory() as td:
            good = Path(td) / "s.env"
            good.write_text("CODEX_LB_API_KEY=fixture-key-123\n"); good.chmod(0o600)
            self.assertEqual(C.read_dedicated_secret(good), "fixture-key-123")
            bare = Path(td) / "b.env"
            bare.write_text("fixture-bare-key\n"); bare.chmod(0o400)
            self.assertEqual(C.read_dedicated_secret(bare), "fixture-bare-key")
            world = Path(td) / "w.env"
            world.write_text("CODEX_LB_API_KEY=x\n"); world.chmod(0o644)
            with self.assertRaises(C.CodexError):
                C.read_dedicated_secret(world)
            missing = Path(td) / "absent.env"
            with self.assertRaises(C.CodexBlocked):
                C.read_dedicated_secret(missing)
            multi = Path(td) / "m.env"
            multi.write_text("a\nb\n"); multi.chmod(0o600)
            with self.assertRaises(C.CodexError):
                C.read_dedicated_secret(multi)

    def test_catalog_pass_and_auth_denied_and_malformed(self):
        body = json.dumps({"object": "list", "data": [{"id": "fixture-model", "object": "model"}]}).encode()
        g = fake_http({"/v1/models": (200, body)})
        res = C.check_catalog("http://h:1/v1", "k", http_get=g)
        self.assertEqual(res["status"], "PASS")
        self.assertNotIn("/responses", g.calls[0][0])
        # Auth denied
        g2 = fake_http({"/v1/models": (401, b"")})
        with self.assertRaises(C.CodexAuthDenied):
            C.check_catalog("http://h:1/v1", "k", http_get=g2)
        # Malformed
        g3 = fake_http({"/v1/models": (200, b'{"data":')})
        with self.assertRaises(C.CodexError):
            C.check_catalog("http://h:1/v1", "k", http_get=g3)
        # Empty list
        g4 = fake_http({"/v1/models": (200, json.dumps({"object": "list", "data": []}).encode())})
        with self.assertRaises(C.CodexError):
            C.check_catalog("http://h:1/v1", "k", http_get=g4)
        # Unreachable
        g5 = fake_http({"/v1/models": C.CodexBlocked("down")})
        with self.assertRaises(C.CodexBlocked):
            C.check_catalog("http://h:1/v1", "k", http_get=g5)

    def test_health_structural_and_unreachable(self):
        g = fake_http({"/health": (200, json.dumps({"status": "ok"}).encode())})
        res = C.check_health("http://h:1/v1", http_get=g)
        self.assertEqual(res["status"], "PASS")
        g2 = fake_http({"/health": (200, b"not json")})
        with self.assertRaises(C.CodexError):
            C.check_health("http://h:1/v1", http_get=g2)
        g3 = fake_http({"/health": C.CodexBlocked("down")})
        with self.assertRaises(C.CodexBlocked):
            C.check_health("http://h:1/v1", http_get=g3)

    def test_run_all_skips_without_credential_and_never_calls_inference(self):
        g = fake_http({"/health": (200, json.dumps({"status": "ok"}).encode())})
        out = C.run_all(base_url="http://h:1/v1", secret_file=None, http_get=g)
        self.assertEqual(out["codex_catalog"], "SKIP")
        self.assertEqual(out["codex_no_inference"], "PASS")
        for url, _ in g.calls:
            self.assertNotIn("/responses", url.lower())

    def test_run_all_classifies_denied_vs_unreachable_secret_safe(self):
        secret_val = "fixture-secret-abc123"
        with tempfile.TemporaryDirectory() as td:
            sf = Path(td) / "s.env"
            sf.write_text(f"CODEX_LB_API_KEY={secret_val}\n"); sf.chmod(0o600)
            g = fake_http({"/health": (200, json.dumps({"status": "ok"}).encode()),
                           "/v1/models": (403, b"")})
            out = C.run_all(base_url="http://h:1/v1", secret_file=sf, http_get=g)
            self.assertEqual(out["codex_catalog"], "FAIL")
            self.assertNotIn(secret_val, json.dumps(out))

    def test_sanitize_redacts_tokens(self):
        msg = C.sanitize_message("failed Bearer abcdef123456 and CODEX key sk-1234567890abcdef")
        self.assertNotIn("abcdef123456", msg)
        self.assertNotIn("sk-1234567890abcdef", msg)


class MuseAdapterTests(unittest.TestCase):
    def test_fixed_profile_rejects_wrong_identity(self):
        A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "max", False)
        for prov, model, think, fb in [
            ("codex-lb", "muse-spark-1.3-contributor", "max", False),
            ("meta", "gpt-6-astra", "max", False),
            ("meta", "gpt-6-luna", "max", False),
            ("meta", "muse-spark-1.3-contributor", "xhigh", False),
            ("meta", "muse-spark-1.3-contributor", "low", False),
            ("meta", "muse-spark-1.3-contributor", "max", True),
        ]:
            with self.subTest(prov=prov, model=model, think=think), self.assertRaises(A.AdapterError):
                A.validate_requested_profile(prov, model, think, fb)

    def test_guard_and_policy_readback_are_pinned(self):
        g = A.guard_identity(ROOT)
        self.assertTrue(g["sha256"].startswith("sha256:"))
        self.assertIn("run-llm-test.sh", g["path"])
        p = A.policy_identity(ROOT)
        self.assertEqual(p["profile"]["model"], "muse-spark-1.3-contributor")
        self.assertEqual(p["profile"]["thinking"], "max")

    def test_candidate_home_rejects_production(self):
        with tempfile.TemporaryDirectory() as td:
            disp = Path(td)
            cand = disp / "daemon-home"
            cand.mkdir()
            self.assertEqual(A.validate_candidate_home(cand, disp), cand.resolve())
            for prod in (Path.home() / ".paseo", "/home/paseo/.paseo"):
                with self.subTest(prod=str(prod)), self.assertRaises(A.AdapterError):
                    A.validate_candidate_home(prod, disp)
            outside = Path("/tmp/outside-candidate-home-fixture")
            with self.assertRaises(A.AdapterError):
                A.validate_candidate_home(outside, disp)

    def test_daemon_binding_requires_candidate_home(self):
        with tempfile.TemporaryDirectory() as td:
            disp = Path(td)
            cand = disp / "home"; cand.mkdir()
            good = {"home": str(cand.resolve()), "listen": "127.0.0.1:7777", "pid": 1234, "daemonVersion": "0.9.2"}
            self.assertEqual(A.validate_daemon_binding(good, cand.resolve())["endpoint"], "127.0.0.1:7777")
            wrong = dict(good, home=str(disp / "other"))
            with self.assertRaises(A.AdapterError):
                A.validate_daemon_binding(wrong, cand.resolve())
            prod = dict(good, home=str(Path.home() / ".paseo"))
            with self.assertRaises(A.AdapterError):
                A.validate_daemon_binding(prod, cand.resolve())

    def test_effective_profile_clamp_and_unknown_fail_closed_without_replay(self):
        req = A.fixed_profile()
        ok = A.classify_effective_profile(req, {"provider": "meta", "model": "muse-spark-1.3-contributor", "thinking": "max"})
        self.assertEqual(ok["gate"], "PASS")
        clamped = A.classify_effective_profile(req, {"provider": "meta", "model": "muse-spark-1.3-contributor", "thinking": "xhigh"})
        self.assertEqual(clamped["gate"], "FAIL")
        self.assertIn("M08-T01", clamped["reason"])
        self.assertFalse(clamped["replay"])
        unknown = A.classify_effective_profile(req, None)
        self.assertEqual(unknown["gate"], "UNKNOWN")
        self.assertFalse(unknown["replay"])
        wrong = A.classify_effective_profile(req, {"provider": "meta", "model": "gpt-6-astra", "thinking": "max"})
        self.assertEqual(wrong["gate"], "FAIL")

    def _bindir_with_fake_paseo(self, root: Path, *, with_paseo=True):
        bindir = root / "bindir"
        bindir.mkdir(exist_ok=True)
        for tool in ("dirname", "jq", "bash"):
            target = shutil.which(tool)
            self.assertIsNotNone(target)
            link = bindir / tool
            if not link.exists():
                os.symlink(target, link)
        if with_paseo:
            fake = bindir / "paseo"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$DISPATCH_MARKER"\n')
            fake.chmod(0o755)
        return bindir

    def test_guard_dispatch_positive_observed_before_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agent = root / "agent-src"
            (agent / "policies").mkdir(parents=True)
            (agent / "policies" / "llm-test-policy.json").write_text(json.dumps({
                "schema": 1, "real_llm_tests": {"provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": "max", "forbidden_models": ["gpt-6-astra"], "fallback_allowed": False}}))
            bindir = self._bindir_with_fake_paseo(root, with_paseo=True)
            snap = A.run_guard_dispatch(guard_file=RUNNER, agent_root=agent,
                                        prompt="SYNTHETIC_MARKER_NO_INFERENCE", cwd=str(root),
                                        bindir=bindir, timeout=15)
            self.assertEqual(snap["returncode"], 0)
            self.assertTrue(snap["dispatched"])
            self.assertIn("meta/muse-spark-1.3-contributor", snap["dispatch_lines"])
            self.assertIn("max", snap["dispatch_lines"])

    def test_guard_dispatch_negative_absent_before_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agent = root / "agent-src"
            (agent / "policies").mkdir(parents=True)
            # Bad profile must not dispatch.
            (agent / "policies" / "llm-test-policy.json").write_text(json.dumps({
                "schema": 1, "real_llm_tests": {"provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": "xhigh", "forbidden_models": ["gpt-6-astra"], "fallback_allowed": False}}))
            bindir = self._bindir_with_fake_paseo(root, with_paseo=True)
            snap = A.run_guard_dispatch(guard_file=RUNNER, agent_root=agent,
                                        prompt="SYNTHETIC_MARKER_NO_INFERENCE", cwd=str(root),
                                        bindir=bindir, timeout=15)
            self.assertNotEqual(snap["returncode"], 0)
            self.assertFalse(snap["dispatched"])
            # Unavailable execution (no paseo in bindir) must not dispatch.
            agent2 = root / "agent-src2"
            (agent2 / "policies").mkdir(parents=True)
            (agent2 / "policies" / "llm-test-policy.json").write_text(json.dumps({
                "schema": 1, "real_llm_tests": {"provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": "max", "forbidden_models": ["gpt-6-astra"], "fallback_allowed": False}}))
            bindir2 = self._bindir_with_fake_paseo(root / "nb", with_paseo=False) if (root / "nb").mkdir(exist_ok=True) else None
            # Build an isolated bindir without paseo.
            nb = root / "nobin"; nb.mkdir(exist_ok=True)
            for tool in ("dirname", "jq", "bash"):
                os.symlink(shutil.which(tool), nb / tool)
            snap2 = A.run_guard_dispatch(guard_file=RUNNER, agent_root=agent2,
                                         prompt="SYNTHETIC_MARKER_NO_INFERENCE", cwd=str(root),
                                         bindir=nb, timeout=15)
            self.assertFalse(snap2["dispatched"])

    def test_native_args_shape_emits_fixed_payload_without_inference(self):
        proc = subprocess.run([str(RUNNER), "--native-create-agent-args"],
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["provider"], "pi/meta/muse-spark-1.3-contributor")
        self.assertEqual(payload["settings"]["thinkingOptionId"], "max")

    def test_fixture_outcome_never_satisfies_real(self):
        req = A.fixed_profile()
        snap = {"returncode": 0, "dispatched": True, "dispatch_lines": ["meta/muse-spark-1.3-contributor", "max"]}
        out = A.outcome_for_fixture(requested=req, dispatch_snapshot=snap,
                                    observed_effective={"provider": "meta", "model": "muse-spark-1.3-contributor", "thinking": "max"})
        self.assertEqual(out["execution_class"], "fixture")
        self.assertFalse(out["real_validation_satisfied"])
        # Timeout/unknown keeps unsatisfied without replay.
        tout = A.outcome_for_fixture(requested=req, dispatch_snapshot={"timeout": True, "dispatched": False},
                                     observed_effective=None)
        self.assertEqual(tout["terminal_class"], "unknown")
        self.assertFalse(tout["real_validation_satisfied"])


class ValidatorMatrixTests(unittest.TestCase):
    def test_wrong_oci_digest_fails_closed_before_disallowed_calls(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            calls = []
            def fake(argv, timeout=300, check=True):
                calls.append(argv)
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout="Digest: sha256:" + "c" * 64 + "\n", stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td))
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("registry", res.get("reason", ""))
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "run"]), 0)
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "exec"]), 0)

    def test_wrong_bundle_and_policy_fail_closed(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                # Real source root binds; a forged companion must fail.
                import importlib.util as ilu
                spec = ilu.spec_from_file_location("bmod", ROOT / "scripts" / "paseo_candidate_build.py")
                bm = ilu.module_from_spec(spec); spec.loader.exec_module(bm)
                real = bm.companion_bundle_identity(ROOT)
                forged = dict(real, source_digest="sha256:" + "0" * 64)
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td),
                                 source_root=ROOT, companion_bundle=forged)
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("companion", res.get("reason", "").lower())

    def test_fixture_pass_is_not_real_and_fake_pass_rejected(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td),
                                 execution_class="fixture")
            self.assertEqual(res["status"], "PASS")
            self.assertFalse(res["real_validation_satisfied"])
            # A caller-supplied generic PASS string cannot manufacture real evidence:
            # the typed outcome still reports fixture with real unsatisfied.
            self.assertNotEqual(res.get("execution_class"), "real")
            self.assertIn("fixture", json.dumps(res).lower())

    def test_inference_endpoint_never_called(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            secret = Path(td) / "s.env"
            secret.write_text("CODEX_LB_API_KEY=fixture-k\n"); secret.chmod(0o600)
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st",
                                 codex_secret=secret, codex_base_url="http://h:1/v1", codex_model="m")
            for c in calls:
                if c[:2] == ["docker", "exec"]:
                    low = c[-1].lower()
                    self.assertNotIn("/responses", low)
                    self.assertNotIn("/chat/completions", low)
            self.assertEqual(res["checks"].get("codex_no_inference"), "PASS")

    def test_timeout_unknown_preserves_reference_without_replay(self):
        # Adapter-level timeout fixture: no replay, unknown terminal, unsatisfied.
        req = A.fixed_profile()
        out = A.outcome_for_fixture(requested=req, dispatch_snapshot={"timeout": True, "dispatched": False},
                                    observed_effective=None)
        self.assertEqual(out["terminal_class"], "unknown")
        self.assertFalse(out["real_validation_satisfied"])

    def test_leaked_token_never_in_output_or_calls(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        token = "fixture-token-xyz-987654321"
        with tempfile.TemporaryDirectory() as td:
            secret = Path(td) / "s.env"
            secret.write_text(f"CODEX_LB_API_KEY={token}\n"); secret.chmod(0o600)
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st",
                                 codex_secret=secret, codex_base_url="http://h:1/v1", codex_model="m")
            blob = json.dumps(res) + " ".join(" ".join(c) for c in calls)
            self.assertNotIn(token, blob)

    def test_cleanup_collision_partial_setup_preserves_foreign(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            calls = []
            def fake(argv, timeout=300, check=True):
                calls.append(argv)
                if argv[:4] == ["docker", "buildx", "imagetools", "inspect"]:
                    return mock.Mock(returncode=0, stdout=f"Digest: {digest}\n", stderr="")
                if argv[:3] == ["docker", "image", "inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0, stdout=json.dumps([f"ghcr.io/elmakus/pi-unraid@{digest}"]), stderr="")
                    return mock.Mock(returncode=0, stdout=image_id + "\n", stderr="")
                if argv[:3] == ["docker", "image", "pull"]:
                    return mock.Mock(returncode=0, stdout="", stderr="")
                if argv[:2] == ["docker", "network"]:
                    return mock.Mock(returncode=0, stdout="", stderr="")
                if argv[:2] == ["docker", "inspect"]:
                    obj = {"Config": {"User": "99:100", "Env": []},
                           "HostConfig": {"NetworkMode": "pi-unraid-validator"},
                           "Mounts": [{"Source": "/other/attempt", "Destination": "/home/paseo"}],
                           "State": {"Status": "running", "Health": {"Status": "healthy"}}}
                    return mock.Mock(returncode=0, stdout=json.dumps([obj]), stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td))
            self.assertEqual(res["status"], "FAIL")
            self.assertEqual(sum(1 for c in calls if c[:2] == ["docker", "rm"]), 0)

    def test_malformed_unreachable_codex_classified_secret_safe(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        # Malformed base URL fails closed before any exec.
        with tempfile.TemporaryDirectory() as td:
            secret = Path(td) / "s.env"
            secret.write_text("CODEX_LB_API_KEY=k\n"); secret.chmod(0o600)
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st",
                                 codex_secret=secret, codex_base_url="http://h:1/api", codex_model="m")
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("v1", res.get("reason", ""))

    def test_secret_safe_exception_redacts_dependency_echo(self):
        msg = V._sanitize("command failed Bearer abcdef1234567890 and sk-1234567890abcdef tail")
        self.assertNotIn("abcdef1234567890", msg)
        self.assertNotIn("sk-1234567890abcdef", msg)


class ExtendedMatrixTests(unittest.TestCase):
    def test_fallback_and_bypass_rejected(self):
        with self.assertRaises(A.AdapterError):
            A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "max", True)
        # Native shape with downgraded policy must not emit a payload.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agent = root / "ag"
            (agent / "policies").mkdir(parents=True)
            (agent / "policies" / "llm-test-policy.json").write_text(json.dumps({
                "schema": 1, "real_llm_tests": {"provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": "max", "forbidden_models": ["gpt-6-astra"], "fallback_allowed": True}}))
            bindir = root / "bin"; bindir.mkdir()
            for tool in ("dirname", "jq", "bash"):
                os.symlink(shutil.which(tool), bindir / tool)
            fake = bindir / "paseo"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$DISPATCH_MARKER"\n')
            fake.chmod(0o755)
            snap = A.run_guard_dispatch(guard_file=RUNNER, agent_root=agent,
                                        prompt="--native-create-agent-args", cwd=str(root),
                                        bindir=bindir, timeout=10)
            # Fallback-allowed policy is rejected by the guard (exit 3), no dispatch.
            self.assertNotEqual(snap["returncode"], 0)
            self.assertFalse(snap["dispatched"])

    def test_wrong_daemon_endpoint_and_pi_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            disp = Path(td)
            cand = disp / "home"; cand.mkdir()
            # Wrong endpoint version fails.
            bad_ver = {"home": str(cand.resolve()), "listen": "127.0.0.1:1", "daemonVersion": "0.0.0"}
            with self.assertRaises(A.AdapterError):
                A.validate_daemon_binding(bad_ver, cand.resolve())
            # Missing endpoint fails.
            with self.assertRaises(A.AdapterError):
                A.validate_daemon_binding({"home": str(cand.resolve())}, cand.resolve())
            # Pi outside bindir fails; inside bindir with wrong version fails.
            bindir = disp / "bindir"; bindir.mkdir()
            with self.assertRaises(A.AdapterError):
                A.validate_pi_binding("/usr/local/bin/pi", "0.87.1", bindir)
            pi_fake = bindir / "pi"; pi_fake.write_text("#!/bin/sh\n"); pi_fake.chmod(0o755)
            with self.assertRaises(A.AdapterError):
                A.validate_pi_binding(str(pi_fake), "9.9.9", bindir)
            ok = A.validate_pi_binding(str(pi_fake), "0.87.1", bindir)
            self.assertEqual(ok["version"], "0.87.1")

    def test_wrong_source_policy_fails_validator(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            # Fixture source with fallback-allowed policy must fail policy binding.
            src = Path(td) / "src"
            agent = src / "config" / "pi-agent"
            (agent / "bin").mkdir(parents=True)
            (agent / "policies").mkdir(parents=True)
            (agent / "AGENTS.md").write_text("# f\n")
            tool = agent / "bin" / "run-llm-test.sh"
            tool.write_text(RUNNER.read_text()); tool.chmod(0o755)
            (agent / "policies" / "llm-test-policy.json").write_text(json.dumps({
                "schema": 1, "real_llm_tests": {"provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": "max", "forbidden_models": ["gpt-6-astra"], "fallback_allowed": True}}))
            # Minimal companion identity needs installer files; reuse real companion
            # shape by copying the real config tree for file set, then swapping policy.
            import shutil as _sh
            real_agent = ROOT / "config" / "pi-agent"
            for p in real_agent.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(real_agent)
                    if rel == Path("policies/llm-test-policy.json"):
                        continue
                    dst = agent / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    _sh.copyfile(p, dst)
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st",
                                 source_root=src)
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("fallback", res.get("reason", "").lower())

    def test_negative_terminal_and_uncertain_occurrence(self):
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        # Negative Codex protocol failure (23) is terminal FAIL, not PASS.
        with tempfile.TemporaryDirectory() as td:
            secret = Path(td) / "s.env"
            secret.write_text("CODEX_LB_API_KEY=k\n"); secret.chmod(0o600)
            fake, calls, _ = stateful_docker(digest, image_id, catalog_rc=23)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st",
                                 codex_secret=secret, codex_base_url="http://h:1/v1", codex_model="m")
            self.assertEqual(res["status"], "FAIL")
            self.assertFalse(res["real_validation_satisfied"])
        # Clamped effective observation fails the Muse gate.
        with tempfile.TemporaryDirectory() as td:
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st2",
                                 muse_observed_effective={"provider": "meta", "model": "muse-spark-1.3-contributor", "thinking": "xhigh"},
                                 daemon_info={"home": "/tmp/x"}, pi_info={"path": "/tmp/y"})
            self.assertEqual(res["checks"].get("muse_effective_profile"), "FAIL")
            self.assertFalse(res["real_validation_satisfied"])

    def test_oauth_and_mount_procedure_shape(self):
        # Dedicated plumbing uses private file + read-only mount; OAuth/device
        # flow remains human-participated (no automated credential admission).
        # This asserts the validator's mount/env shape, not a live OAuth flow.
        digest = "sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        with tempfile.TemporaryDirectory() as td:
            secret = Path(td) / "s.env"
            secret.write_text("CODEX_LB_API_KEY=k\n"); secret.chmod(0o600)
            fake, calls, _ = stateful_docker(digest, image_id)
            with mock.patch.object(V.shutil, "which", return_value="/usr/bin/docker"), \
                 mock.patch.object(V.os, "chown"), mock.patch.object(V, "run", side_effect=fake):
                res = V.validate(repository="ghcr.io/elmakus/pi-unraid", digest=digest,
                                 output=Path(td) / "o.json", state_root=Path(td) / "st",
                                 codex_secret=secret, codex_base_url="http://h:1/v1", codex_model="m")
            run_call = next(c for c in calls if c[:2] == ["docker", "run"])
            # No raw --env KEY=value with a secret value; only nonsecret config env.
            for i, tok in enumerate(run_call):
                if tok == "-e" and i + 1 < len(run_call):
                    self.assertNotIn("CODEX_LB_API_KEY=", run_call[i+1].replace("PI_CODEX_LB_MODEL", "").replace("PI_CODEX_LB_BASE_URL", ""))
            self.assertIn(f"{secret.resolve()}:{V.CODEX_SECRET_TARGET}:ro", run_call)


if __name__ == "__main__":
    unittest.main()
