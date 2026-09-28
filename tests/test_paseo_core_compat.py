#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import paseo_core_compat as core

RESOLVER_PATH = SCRIPTS / "resolve-paseo-candidate.py"
spec = importlib.util.spec_from_file_location("m02_t02_resolver", RESOLVER_PATH)
resolver = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(resolver)

FIXTURE = ROOT / "tests" / "fixtures" / "paseo-candidate" / "facts.json"
DEFINITION = ROOT / "config" / "environment-capabilities.json"


class CoreCompatibilitySearchTests(unittest.TestCase):
    def setUp(self):
        self.definition = json.loads(DEFINITION.read_text())
        self.components = json.loads(FIXTURE.read_text())["components"]

    def paseo_option(self, version, node_version="22.23.3", marker="1"):
        paseo = copy.deepcopy(self.components["paseo"])
        paseo["version"] = version
        paseo["source"]["tag"] = "v" + version
        paseo["source"]["commit"] = marker * 40
        digest = "sha256:" + marker * 64
        manifest = "sha256:" + ("a" if marker != "a" else "b") * 64
        config = "sha256:" + ("c" if marker != "c" else "d") * 64
        paseo["artifact"].update(
            {
                "image": f"ghcr.io/getpaseo/paseo:{version}",
                "digest": digest,
                "reference": f"ghcr.io/getpaseo/paseo@{digest}",
                "linux_amd64_manifest": manifest,
                "config_digest": config,
                "node_version": node_version,
            }
        )
        node = copy.deepcopy(self.components["node"])
        node["version"] = node_version
        node["immutable_parent"] = paseo["artifact"]["reference"]
        return {"paseo": paseo, "node": node}

    def pi_option(self, version, marker="2", node_range=">=22.19.0"):
        pi = copy.deepcopy(self.components["pi"])
        pi["version"] = version
        pi["source"]["tag"] = "v" + version
        pi["source"]["commit"] = marker * 40
        pi["npm"]["integrity"] = "sha512-" + marker * 80
        pi["npm"]["shasum"] = marker * 40
        return {"pi": pi, "node_range": node_range}

    def search(self, paseo_options, pi_options, **kwargs):
        return core.search_core_pairs(
            paseo_options,
            pi_options,
            definition=self.definition,
            node_floor=resolver.NODE_FLOOR,
            platform_fingerprint="linux-amd64-test",
            **kwargs,
        )

    def test_newest_first_backtracks_only_core_pair_and_records_exact_nogood(self):
        paseo = [
            self.paseo_option("0.10.0", marker="1"),
            self.paseo_option("0.9.2", marker="2"),
        ]
        pi = [
            self.pi_option("0.88.0", marker="3"),
            self.pi_option("0.87.1", marker="4"),
        ]
        calls = []

        def gate(p, n, candidate_pi):
            calls.append((p["version"], candidate_pi["version"]))
            if candidate_pi["version"] == "0.88.0":
                return {
                    "status": "incompatible",
                    "evidence": "evidence/core-gate/paseo-0.10.0_pi-0.88.0.json",
                }
            return {"status": "compatible"}

        cache = core.empty_nogood_cache()
        selected = self.search(paseo, pi, gate=gate, nogoods=cache)
        self.assertEqual(
            (selected["paseo"]["version"], selected["pi"]["version"]),
            ("0.10.0", "0.87.1"),
        )
        self.assertEqual(calls, [("0.10.0", "0.88.0"), ("0.10.0", "0.87.1")])
        self.assertEqual(len(cache["entries"]), 1)
        self.assertEqual(cache["entries"][0]["failure_class"], "incompatible")
        self.assertEqual(cache["entries"][0]["identity"]["components"], ["paseo", "pi"])

    def test_same_pair_and_gate_fingerprint_reuses_cache_but_changed_gate_rechecks(self):
        paseo = [self.paseo_option("0.10.0", marker="1")]
        pi = [
            self.pi_option("0.88.0", marker="3"),
            self.pi_option("0.87.1", marker="4"),
        ]
        cache = core.empty_nogood_cache()
        gate_hash = "sha256:" + "a" * 64

        def first_gate(p, n, candidate_pi):
            if candidate_pi["version"] == "0.88.0":
                return {"status": "incompatible", "evidence": "evidence/exact-failure.json"}
            return {"status": "compatible"}

        first = self.search(
            paseo,
            pi,
            gate=first_gate,
            nogoods=cache,
            gate_definition_hash=gate_hash,
        )
        self.assertEqual(first["pi"]["version"], "0.87.1")

        calls = []
        second = self.search(
            paseo,
            pi,
            gate=lambda p, n, candidate_pi: (
                calls.append(candidate_pi["version"]) or {"status": "compatible"}
            ),
            nogoods=cache,
            gate_definition_hash=gate_hash,
        )
        self.assertEqual(second["pi"]["version"], "0.87.1")
        self.assertEqual(calls, ["0.87.1"])

        calls.clear()
        changed = self.search(
            paseo,
            pi,
            gate=lambda p, n, candidate_pi: (
                calls.append(candidate_pi["version"]) or {"status": "compatible"}
            ),
            nogoods=cache,
            gate_definition_hash="sha256:" + "b" * 64,
        )
        self.assertEqual(changed["pi"]["version"], "0.88.0")
        self.assertEqual(calls, ["0.88.0"])

    def test_changed_exact_identity_does_not_match_stale_nogood(self):
        paseo = [self.paseo_option("0.10.0", marker="1")]
        bad = self.pi_option("0.88.0", marker="3")
        fallback = self.pi_option("0.87.1", marker="4")
        cache = core.empty_nogood_cache()

        self.search(
            paseo,
            [bad, fallback],
            nogoods=cache,
            gate=lambda p, n, candidate_pi: (
                {"status": "incompatible", "evidence": "evidence/bad.json"}
                if candidate_pi["version"] == "0.88.0"
                else {"status": "compatible"}
            ),
        )
        changed = copy.deepcopy(bad)
        changed["pi"]["source"]["commit"] = "9" * 40
        changed["pi"]["npm"]["shasum"] = "9" * 40
        calls = []
        result = self.search(
            paseo,
            [changed, fallback],
            nogoods=cache,
            gate=lambda p, n, candidate_pi: (
                calls.append(candidate_pi["source"]["commit"]) or {"status": "compatible"}
            ),
        )
        self.assertEqual(result["pi"]["version"], "0.88.0")
        self.assertEqual(calls, ["9" * 40])

    def test_blocked_gate_never_poison_caches_pair(self):
        cache = core.empty_nogood_cache()
        with self.assertRaisesRegex(core.CoreResolutionBlocked, "registry unavailable"):
            self.search(
                [self.paseo_option("0.10.0", marker="1")],
                [self.pi_option("0.88.0", marker="3")],
                nogoods=cache,
                gate=lambda p, n, candidate_pi: {
                    "status": "blocked",
                    "reason": "registry unavailable",
                },
            )
        self.assertEqual(cache["entries"], [])

    def test_node_is_exactly_paseo_derived_and_pi_range_is_enforced(self):
        invalid = self.paseo_option("0.10.0", node_version="22.18.0", marker="1")
        valid = self.paseo_option("0.9.2", node_version="22.23.3", marker="2")
        pi = [self.pi_option("0.88.0", marker="3", node_range=">=22.19.0 <23.0.0")]
        result = self.search([invalid, valid], pi)
        self.assertEqual(result["paseo"]["version"], "0.9.2")
        self.assertEqual(result["node"]["version"], "22.23.3")

        mismatched = copy.deepcopy(valid)
        mismatched["node"]["immutable_parent"] = "ghcr.io/getpaseo/paseo@sha256:" + "f" * 64
        with self.assertRaisesRegex(core.CoreResolutionError, "no compatible"):
            self.search([mismatched], pi)

        rejecting = self.pi_option("0.88.0", marker="3", node_range=">=23.0.0")
        with self.assertRaisesRegex(core.CoreResolutionError, "no compatible"):
            self.search([valid], [rejecting])

    def test_operational_budget_exhaustion_is_resolution_incomplete(self):
        with self.assertRaisesRegex(core.CoreResolutionIncomplete, "RESOLUTION_INCOMPLETE"):
            self.search(
                [self.paseo_option("0.10.0", marker="1")],
                [
                    self.pi_option("0.88.0", marker="3"),
                    self.pi_option("0.87.1", marker="4"),
                ],
                budget=1,
                gate=lambda p, n, candidate_pi: {
                    "status": "incompatible",
                    "evidence": "evidence/proven.json",
                },
            )

    def test_nogood_cache_persists_only_proven_incompatibility(self):
        paseo = self.paseo_option("0.10.0", marker="1")["paseo"]
        pi = self.pi_option("0.88.0", marker="3")["pi"]
        gate_hash = core.default_gate_definition_hash(resolver.NODE_FLOOR)
        contract_hash = core.core_contract_fingerprint(self.definition, resolver.NODE_FLOOR)
        key, identity = core.nogood_key(
            paseo,
            pi,
            gate_id=core.CORE_GATE_ID,
            gate_definition_hash=gate_hash,
            contract_hash=contract_hash,
            platform_fingerprint="linux-amd64-test",
        )
        cache = core.empty_nogood_cache()
        self.assertTrue(
            core.record_nogood(
                cache,
                key=key,
                identity=identity,
                evidence="evidence/persisted.json",
            )
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nogoods.json"
            core.save_nogood_cache(path, cache)
            self.assertEqual(core.load_nogood_cache(path), cache)

        poisoned = copy.deepcopy(cache)
        poisoned["entries"][0]["failure_class"] = "blocked"
        with self.assertRaisesRegex(core.CoreResolutionError, "only proven incompatibility"):
            core.validate_nogood_cache(poisoned)

    def test_live_core_fallback_changes_only_paseo_node_pi(self):
        latest = copy.deepcopy(self.components)
        latest["paseo"] = self.paseo_option("0.10.0", marker="1")["paseo"]
        latest["node"] = self.paseo_option("0.10.0", marker="1")["node"]
        latest["pi"] = self.pi_option("0.88.0", marker="3")["pi"]

        cache = core.empty_nogood_cache()
        self.search(
            [{"paseo": latest["paseo"], "node": latest["node"]}],
            [
                {"pi": latest["pi"], "node_range": ">=22.19.0"},
                self.pi_option("0.87.1", marker="4"),
            ],
            nogoods=cache,
            gate=lambda p, n, candidate_pi: (
                {"status": "incompatible", "evidence": "evidence/latest-bad.json"}
                if candidate_pi["version"] == "0.88.0"
                else {"status": "compatible"}
            ),
        )

        older_pi = self.pi_option("0.87.1", marker="4")
        with mock.patch.object(
            resolver,
            "_core_options_to_baseline",
            return_value=(
                [{"paseo": latest["paseo"], "node": latest["node"]}],
                [{"pi": latest["pi"], "node_range": ">=22.19.0"}, older_pi],
            ),
        ):
            resolved, lag = resolver.resolve_core_live_components(
                latest,
                self.definition,
                nogoods=cache,
                platform_fingerprint="linux-amd64-test",
            )
        self.assertEqual(resolved["paseo"]["version"], "0.10.0")
        self.assertEqual(resolved["pi"]["version"], "0.87.1")
        self.assertEqual(lag, {"pi"})
        for component in resolver.REQUIRED_COMPONENTS - {"paseo", "node", "pi"}:
            self.assertEqual(resolved[component], latest[component])

    def test_transient_transport_failure_is_blocked_not_incompatible(self):
        with mock.patch.object(
            resolver.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("temporary DNS failure"),
        ):
            with self.assertRaisesRegex(core.CoreResolutionBlocked, "BLOCKED"):
                resolver.http("https://example.invalid/test")


class NodeRangeTests(unittest.TestCase):
    def test_supported_range_forms(self):
        self.assertTrue(core.node_range_allows("22.23.3", ">=22.19.0 <23.0.0"))
        self.assertTrue(core.node_range_allows("22.23.3", "^22.19.0"))
        self.assertTrue(core.node_range_allows("22.23.3", "22.23.x"))
        self.assertTrue(core.node_range_allows("22.23.3", ">=24.0.0 || >=22.19.0 <23.0.0"))
        self.assertFalse(core.node_range_allows("22.18.0", ">=22.19.0"))
        with self.assertRaisesRegex(core.CoreResolutionError, "unsupported Node semver range"):
            core.node_range_allows("22.23.3", "workspace:*")


if __name__ == "__main__":
    unittest.main()
