#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import paseo_independent_resolution as independent

RESOLVER_PATH = SCRIPTS / "resolve-paseo-candidate.py"
spec = importlib.util.spec_from_file_location("m02_t03_resolver", RESOLVER_PATH)
resolver = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(resolver)

FIXTURE = ROOT / "tests" / "fixtures" / "paseo-candidate" / "facts.json"
DEFINITION = ROOT / "config" / "environment-capabilities.json"


class IndependentFallbackTests(unittest.TestCase):
    def setUp(self):
        self.definition = json.loads(DEFINITION.read_text())
        self.accepted = json.loads(FIXTURE.read_text())["components"]

    def latest(self):
        return copy.deepcopy(self.accepted)

    def bump(self, components, component, version, marker):
        value = components[component]
        value["version"] = version
        if "source" in value:
            value["source"]["tag"] = (
                f"docker-v{version}" if component == "docker_cli" else f"v{version}"
            )
            value["source"]["commit"] = marker * 40
        if "npm" in value:
            value["npm"]["integrity"] = "sha512-" + marker * 80
            value["npm"]["shasum"] = marker * 40
        if "artifact" in value and component != "playwright":
            value["artifact"]["digest"] = "sha256:" + marker * 64
        return value

    def outcome(self, components, component, status="unavailable"):
        item = {
            "component": component,
            "identity": independent.component_identity(components[component]),
            "status": status,
        }
        if status == "unavailable":
            item["evidence"] = f"evidence/{component}-unavailable.json"
        else:
            item["reason"] = "registry/build infrastructure unavailable"
        return {"schema_version": 1, "outcomes": [item]}

    def test_extension_fallback_does_not_hold_back_unrelated_tool(self):
        latest = self.latest()
        self.bump(latest, "specpi", "0.35.0", "a")
        self.bump(latest, "github_cli", "2.102.0", "b")
        resolved, lag, decisions = independent.resolve_independent_components(
            latest,
            self.accepted,
            self.definition,
            outcomes=self.outcome(latest, "specpi"),
        )
        self.assertEqual(resolved["specpi"]["version"], "0.34.0")
        self.assertEqual(resolved["github_cli"]["version"], "2.102.0")
        self.assertEqual(lag, {"specpi"})
        self.assertEqual(
            next(d for d in decisions if d["component"] == "specpi")["status"],
            "fallback_previous_accepted",
        )

    def test_developer_tool_fallback_does_not_hold_back_extension(self):
        latest = self.latest()
        self.bump(latest, "docker_compose", "5.6.0", "c")
        self.bump(latest, "specpi", "0.35.0", "d")
        resolved, lag, _ = independent.resolve_independent_components(
            latest,
            self.accepted,
            self.definition,
            outcomes=self.outcome(latest, "docker_compose"),
        )
        self.assertEqual(resolved["docker_compose"]["version"], "5.5.1")
        self.assertEqual(resolved["specpi"]["version"], "0.35.0")
        self.assertEqual(lag, {"docker_compose"})

    def test_playwright_and_chromium_fallback_as_one_unit(self):
        latest = self.latest()
        self.bump(latest, "playwright", "1.64.0", "e")
        latest["playwright"]["chromium"] = {
            "revision": "1300",
            "browser_version": "154.0.9000.0",
        }
        resolved, lag, _ = independent.resolve_independent_components(
            latest,
            self.accepted,
            self.definition,
            outcomes=self.outcome(latest, "playwright"),
        )
        self.assertEqual(resolved["playwright"]["version"], "1.63.0")
        self.assertEqual(
            resolved["playwright"]["chromium"],
            self.accepted["playwright"]["chromium"],
        )
        self.assertEqual(lag, {"playwright"})

    def test_blocked_is_not_downgraded_or_poisoned(self):
        latest = self.latest()
        self.bump(latest, "specpi", "0.35.0", "f")
        with self.assertRaisesRegex(
            independent.IndependentResolutionBlocked, "BLOCKED"
        ):
            independent.resolve_independent_components(
                latest,
                self.accepted,
                self.definition,
                outcomes=self.outcome(latest, "specpi", status="blocked"),
            )
        resolved, lag, _ = independent.resolve_independent_components(
            latest, self.accepted, self.definition
        )
        self.assertEqual(resolved["specpi"]["version"], "0.35.0")
        self.assertEqual(lag, set())

    def test_stale_failure_identity_does_not_poison_replaced_latest(self):
        latest = self.latest()
        self.bump(latest, "specpi", "0.35.0", "1")
        stale = self.outcome(latest, "specpi")
        latest["specpi"]["source"]["commit"] = "2" * 40
        latest["specpi"]["npm"]["integrity"] = "sha512-" + "2" * 80
        latest["specpi"]["npm"]["shasum"] = "2" * 40
        resolved, lag, _ = independent.resolve_independent_components(
            latest, self.accepted, self.definition, outcomes=stale
        )
        self.assertEqual(resolved["specpi"]["version"], "0.35.0")
        self.assertEqual(lag, set())

    def test_live_resolver_applies_exact_independent_outcome(self):
        latest = self.latest()
        self.bump(latest, "specpi", "0.35.0", "9")
        accepted_candidate = {"components": copy.deepcopy(self.accepted)}
        with mock.patch.object(
            resolver, "discover_live_components", return_value=copy.deepcopy(latest)
        ), mock.patch.object(
            resolver,
            "resolve_core_live_components",
            return_value=(copy.deepcopy(latest), set()),
        ), mock.patch.object(
            resolver, "load_json_file", return_value=accepted_candidate
        ):
            candidate = resolver.resolve_live(
                self.definition,
                [],
                independent_outcomes=self.outcome(latest, "specpi"),
            )
        self.assertEqual(candidate["components"]["specpi"]["version"], "0.34.0")
        self.assertEqual(candidate["policy"]["compatibility_exceptions"], [])

    def test_automatic_independent_lag_needs_no_manual_exception(self):
        components = self.latest()
        candidate = resolver.assemble_candidate(
            components,
            [],
            {"specpi": "0.35.0"},
            [],
            self.definition,
            automatic_lag={"specpi"},
        )
        self.assertEqual(candidate["components"]["specpi"]["version"], "0.34.0")
        self.assertEqual(candidate["policy"]["compatibility_exceptions"], [])

    def test_extension_peer_metadata_is_not_a_core_gate(self):
        components = self.latest()
        components["pi_mcp_adapter"]["declared_pi_ai_peer"] = "^0.80.0"
        candidate = resolver.assemble_candidate(
            components, [], {}, [], self.definition
        )
        self.assertEqual(candidate["components"]["pi"]["version"], "0.87.1")
        self.assertEqual(
            candidate["components"]["pi_mcp_adapter"]["declared_pi_ai_peer"],
            "^0.80.0",
        )


class CandidateFreshnessTests(unittest.TestCase):
    def candidate(self, a, b, c, marker):
        return {
            "marker": marker,
            "components": {
                "a": {"version": a},
                "b": {"version": b},
                "c": {"version": c},
            },
        }

    def test_pareto_filter_and_equal_weight_aggregate_lag(self):
        domains = {
            "a": ["2.0.0", "1.0.0"],
            "b": ["2.0.0", "1.0.0"],
            "c": ["3.0.0", "2.0.0", "1.0.0"],
        }
        high_a = self.candidate("2.0.0", "2.0.0", "1.0.0", "high-a")
        fresher_total = self.candidate("1.0.0", "2.0.0", "3.0.0", "fresher-total")
        dominated = self.candidate("1.0.0", "1.0.0", "1.0.0", "dominated")
        selected = resolver.select_complete_candidate(
            [high_a, dominated, fresher_total], domains
        )
        self.assertEqual(selected["candidate"]["marker"], "fresher-total")
        self.assertEqual(selected["aggregate_lag"], 1)
        self.assertEqual(selected["pareto_count"], 2)

    def test_deterministic_technical_tie_break_is_order_independent(self):
        domains = {
            "a": ["2.0.0", "1.0.0"],
            "b": ["2.0.0", "1.0.0"],
            "c": ["3.0.0", "2.0.0", "1.0.0"],
        }
        left = self.candidate("2.0.0", "1.0.0", "3.0.0", "left")
        right = self.candidate("1.0.0", "2.0.0", "3.0.0", "right")
        first = resolver.select_complete_candidate([left, right], domains)
        second = resolver.select_complete_candidate([right, left], domains)
        self.assertEqual(first["aggregate_lag"], 1)
        self.assertEqual(first["candidate"], second["candidate"])
        self.assertEqual(first["technical_tiebreak"], second["technical_tiebreak"])

    def test_exact_unchanged_candidate_reports_no_op(self):
        cid = "sha256:" + "a" * 64
        accepted = {"candidate_id": cid, "components": {}}
        same = copy.deepcopy(accepted)
        changed = {"candidate_id": "sha256:" + "b" * 64, "components": {}}
        self.assertEqual(
            independent.candidate_resolution_status(same, accepted), "no_op"
        )
        self.assertEqual(
            independent.candidate_resolution_status(changed, accepted), "update"
        )


if __name__ == "__main__":
    unittest.main()
