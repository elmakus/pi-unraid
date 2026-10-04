"""Bounded synthetic regression, NOT full acceptance or real-test evidence.

Product validate is reached with Docker entirely mocked by the existing harness;
that harness is still incomplete for separate daemon/Pi realization. Observer
payload is executed under Node with only the SDK boundary fake. HTTP safety tests
are localhost only. No real binaries/providers/Docker or ordinary auth are used.
"""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import test_m07_t05_validator_adapter as H

A, C, V, T = H.A, H.C, H.V, H.T


class FailClosedRegression(unittest.TestCase):
    def validate(self, **kw):
        with tempfile.TemporaryDirectory() as td, T.LocalCodexServer(mode="ok") as srv:
            return H._run_validate(Path(td), server_base=srv.base,
                                   execution_class="real", **kw)

    def assert_no_dispatch(self, calls):
        self.assertFalse(any(c[:2] == ["docker", "exec"] and
                             "guarded-dispatch" in " ".join(c) for c in calls))

    def test_max_null_catalog_blocks_before_prompt(self):
        res, calls, _ = self.validate(extra_state={"model_catalog": [
            {"id": "meta/muse-spark-1.3-contributor", "thinkingOptionIds": ["high", "xhigh"]}]})
        self.assertEqual(res["status"], "BLOCKED")
        self.assertFalse(res["real_validation_satisfied"])
        self.assert_no_dispatch(calls)
        preflight = [c for c in calls if "models" in c and "provider" in c]
        self.assertEqual(len(preflight), 1)
        self.assertEqual(preflight[0][3:], ["paseo", "provider", "models", "pi", "--thinking", "--json",
                                         "--home", "/home/paseo/.paseo"])

    def test_missing_or_ambiguous_catalog_blocks_before_prompt(self):
        for catalog in ([], {}, [{"id": "meta/muse-spark-1.3-contributor"}],
                        [{"id": "meta/muse-spark-1.3-contributor", "thinkingOptionIds": ["max"]}] * 2):
            with self.subTest(catalog=catalog):
                res, calls, _ = self.validate(extra_state={"model_catalog": catalog})
                self.assertIn(res["status"], ("FAIL", "BLOCKED"))
                self.assert_no_dispatch(calls)

    def test_failed_or_already_running_start_blocks_before_prompt(self):
        for change in ({"daemon_start_exit": 42}, {"daemon_start_action": "already_running"}):
            with self.subTest(change=change):
                res, calls, _ = self.validate(extra_state=change)
                self.assertIn(res["status"], ("FAIL", "BLOCKED"))
                self.assert_no_dispatch(calls)

    def test_missing_live_status_details_blocks_before_prompt(self):
        good = {"home": "/home/paseo/.paseo", "listen": "127.0.0.1:7777", "pid": 1234,
                "daemonVersion": T.REAL_PASEO, "localDaemon": "running", "connectedDaemon": "reachable",
                "workerPid": 1235, "serverId": "test-server", "daemonNode": "/usr/bin/node", "providers": ["pi"]}
        for key in ("localDaemon", "connectedDaemon", "workerPid", "serverId", "daemonNode", "providers"):
            bad = dict(good)
            del bad[key]
            with self.subTest(key=key):
                res, calls, _ = self.validate(daemon_json=bad)
                self.assertEqual(res["status"], "FAIL")
                self.assert_no_dispatch(calls)

    def test_producer_byte_link_omission_and_mutation_before_external_calls(self):
        # Deliberately retain the legacy chain helper here; this tests strict
        # consumers, not the still-missing actual-producer positive acceptance.
        original = T.build_artifact_chain
        import hashlib
        for defect in ("publication-tested-hash", "tested-candidate-hash", "builder-phase", "build-companion"):
            def changed(*args, **kwargs):
                chain = original(*args, **kwargs)
                candidate, handoff, prepared, tested_path, build_path, published_path = chain
                tested = json.loads(tested_path.read_text())
                build = json.loads(build_path.read_text())
                published = json.loads(published_path.read_text())
                if defect == "publication-tested-hash":
                    published["tested_image_evidence_sha256"] = "sha256:" + "0" * 64
                elif defect == "tested-candidate-hash":
                    del tested["candidate_file_sha256"]
                elif defect == "builder-phase":
                    build["phases"]["builder_ensure"]["status"] = "failed"
                else:
                    build["companion_bundle"]["modes"]["AGENTS.md"] = "0666"
                if defect in ("builder-phase", "build-companion"):
                    build_path.write_text(json.dumps(build))
                    build_hash = "sha256:" + hashlib.sha256(build_path.read_bytes()).hexdigest()
                    tested["build_record_sha256"] = published["build_record_sha256"] = build_hash
                if defect != "publication-tested-hash":
                    tested_path.write_text(json.dumps(tested))
                    published["tested_image_evidence_sha256"] = "sha256:" + hashlib.sha256(tested_path.read_bytes()).hexdigest()
                published_path.write_text(json.dumps(published))
                return chain
            with self.subTest(defect=defect), mock.patch.object(T, "build_artifact_chain", side_effect=changed):
                res, calls, _ = self.validate()
                self.assertIn(res["status"], ("FAIL", "BLOCKED"))
                self.assertFalse(res["real_validation_satisfied"])
                self.assertEqual(calls, [])

    def test_omitted_companion_derives_frozen_declaration(self):
        res, calls, _ = self.validate(extra={"companion_bundle": None})
        self.assertEqual(res["checks"]["companion_binding"], "PASS")
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(any("guarded-dispatch" in " ".join(c) for c in calls))
        # This is structural fake execution only, never real validation evidence.

    def test_arbitrary_container_prefix_never_executes(self):
        res, calls, _ = self.validate(replaced_id="f")
        self.assertEqual(res["status"], "FAIL")
        self.assertFalse(any(c[:2] == ["docker", "exec"] for c in calls))
        self.assertFalse(any(c[:2] == ["docker", "rm"] for c in calls))

    def test_strict_current_container_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            for sub, _ in V.EXPECTED_MOUNT_PAIRS:
                (work / sub).mkdir()
            good = {"Id": "full-acquired-id", "Image": "image-id",
                    "Config": {"User": "99:100", "Labels": {"io.pi-unraid.validator-nonce": "nonce"}},
                    "HostConfig": {"NetworkMode": "net", "ReadonlyRootfs": True,
                                   "Tmpfs": {"/tmp": "rw,nosuid,nodev", "/run": "rw,nosuid,nodev"}},
                    "Mounts": [{"Type": "bind", "Source": str(work / sub), "Destination": dest, "RW": True}
                               for sub, dest in V.EXPECTED_MOUNT_PAIRS]}
            def owned(obj):
                return V._container_owned(obj, work, "net", expected_image_id="image-id",
                                          expected_nonce="nonce", expected_container_id="full-acquired-id")
            self.assertTrue(owned(good))
            negatives = []
            for key, value in (("ReadonlyRootfs", False), ("Tmpfs", {})):
                obj = copy.deepcopy(good); obj["HostConfig"][key] = value; negatives.append(obj)
            obj = copy.deepcopy(good); obj["Config"]["User"] = "0:0"; negatives.append(obj)
            obj = copy.deepcopy(good); obj["Mounts"][0]["Type"] = "volume"; negatives.append(obj)
            obj = copy.deepcopy(good); obj["Mounts"].append(obj["Mounts"][0]); negatives.append(obj)
            obj = copy.deepcopy(good); obj["Id"] = "f"; negatives.append(obj)
            for obj in negatives:
                self.assertFalse(owned(obj))

    def events(self):
        return [{"test_id": "t", "kind": "request", "model": A.FIXED_MODEL, "effort": "max"},
                {"test_id": "t", "kind": "response", "status": "200"},
                {"test_id": "t", "kind": "terminal", "status": "completed"},
                {"test_id": "t", "kind": "terminal", "status": "settled"}]

    def aggregate(self, events):
        return A.aggregate_witness(events, test_id="t", expected_model=A.FIXED_MODEL)["gate"]

    def test_ordered_single_exchange_positive(self):
        self.assertEqual(self.aggregate(self.events()), "PASS")

    def test_mixed_duplicate_malformed_negative_and_reversed_fail(self):
        events = self.events()
        for changed in (list(reversed(events)), events[:2] + [dict(events[1], status="500")] + events[2:],
                        events[:2] + [dict(events[1], status="garbage")] + events[2:],
                        events + [dict(events[0], test_id="stale")], events + [events[0]]):
            self.assertEqual(self.aggregate(changed), "FAIL")

    def test_unqualified_terminal_is_unknown(self):
        for status in ("done", "success", "ended", "settled", "unknown"):
            events = self.events(); events[2]["status"] = status
            self.assertEqual(self.aggregate(events), "UNKNOWN")
        self.assertEqual(self.aggregate(self.events()[:-1]), "UNKNOWN")

    def test_actual_observer_empty_agent_end_cannot_manufacture_success(self):
        node = T._find_node()
        if node is None:
            self.skipTest("Node unavailable: actual observer execution not performed")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); ext = td / "observer.mjs"; witness = td / "witness.jsonl"
            A.stage_witness_extension(ext)
            # Fake SDK only; all registration and witness emission is shipped code.
            js = """import {createRequire} from 'node:module';
            globalThis.require = createRequire(import.meta.url);
            const h = {}; const e = await import(process.argv[1]);
            e.default({on: (k, f) => {h[k] = f;}});
            h.before_provider_request({payload: {model: 'muse-spark-1.3-contributor', reasoning: {effort: 'max'}}});
            h.after_provider_response({status: 200}); h.agent_end({messages: []}); h.agent_settled({});
            """
            pr = subprocess.run([node, "--input-type=module", "-e", js, str(ext)],
                                env={"M07_T05_TEST_ID": "t", "M07_T05_WITNESS_FILE": str(witness)},
                                capture_output=True, text=True, timeout=10)
            self.assertEqual(pr.returncode, 0)
            events = A.load_witness_events(witness, "t")
            self.assertEqual([e.get("status") for e in events[2:]], ["ended", "settled"])
            self.assertEqual(self.aggregate(events), "UNKNOWN")

    def test_arbitrary_v1_destination_rejected_before_transport(self):
        for path in ("/v1/generate", "/v1/invoke", "/v1/unknown", "/v1/models/../generate"):
            with self.subTest(path=path), mock.patch.object(C.urllib.request, "build_opener") as transport:
                with self.assertRaises(C.CodexError):
                    C._http_get("http://127.0.0.1:1" + path, {}, 1)
                transport.assert_not_called()
                with self.assertRaises(C.CodexError):
                    C.assert_safe_redirect("http://127.0.0.1:1/v1/models", "http://127.0.0.1:1" + path)


if __name__ == "__main__":
    unittest.main()
