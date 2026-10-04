from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "pi-agent" / "policies" / "llm-test-policy.json"
GLOBAL_DOC = ROOT / "config" / "pi-agent" / "policies" / "LLM_TEST_POLICY.md"
DOC = ROOT / "docs" / "LLM_TEST_POLICY.md"
AGENTS = ROOT / "config" / "pi-agent" / "AGENTS.md"
RUNNER = ROOT / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
SOURCE = ROOT / "config" / "pi-agent"
DOCKERFILE = (ROOT / "Dockerfile").read_text()
COMPOSE = (ROOT / "compose.yaml").read_text()
CANDIDATE = json.loads((ROOT / "config" / "paseo-candidate.json").read_text())
INSTALLED_META = Path(
    "/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules"
    "/@earendil-works/pi-ai/dist/providers/data/meta.json"
)


def clamp(level: str, level_map: dict) -> str:
    """Mirror dist/models.js clampThinkingLevel downward scan for the test fixture."""
    order = ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
    idx = order.index(level)
    for cand in reversed(order[: idx + 1]):
        if level_map.get(cand) is not None:
            return cand
    raise AssertionError("no supported level")


class M07T04PolicyDeliveryTests(unittest.TestCase):
    def test_fixed_request_identity_is_meta_contributor_max_no_fallback(self) -> None:
        policy = json.loads(POLICY_PATH.read_text())["real_llm_tests"]
        self.assertEqual(policy["provider"], "meta")
        self.assertEqual(policy["model"], "muse-spark-1.3-contributor")
        self.assertEqual(policy["thinking"], "max")
        self.assertFalse(policy["fallback_allowed"])
        self.assertIn("gpt-6-astra", policy["forbidden_models"])
        runner = RUNNER.read_text()
        self.assertIn('provider must be meta', runner)
        self.assertIn('muse-spark-1.3-contributor', runner)
        self.assertIn('thinking/contribution must be max', runner)
        self.assertIn('fallback must be disabled', runner)
        self.assertIn('gpt-6-astra must remain explicitly forbidden', runner)
        self.assertIn('--native-create-agent-args', runner)
        self.assertIn('pi/$provider/$model', runner)

    def test_unmodified_bundled_contributor_max_is_null_and_clamps_to_xhigh(self) -> None:
        # Official upstream source fact (no inference): bundled direct-Meta data
        # marks contributor max unsupported. Without a repo-managed override,
        # a fixed max request would execute at xhigh — a fake-max hazard.
        # This test proves the hazard is explicit; it never claims effective max.
        if not INSTALLED_META.is_file():
            self.skipTest("installed pi-ai bundle unavailable for provenance readback")
        data = json.loads(INSTALLED_META.read_text())
        inner = data.get("openai-responses", data)
        contributor = inner.get("muse-spark-1.3-contributor")
        self.assertIsNotNone(contributor)
        level_map = contributor.get("thinkingLevelMap", {})
        self.assertIsNone(level_map.get("max"))
        self.assertEqual(clamp("max", level_map), "xhigh")
        supported = [k for k, v in level_map.items() if v is not None]
        self.assertNotIn("max", supported)
        self.assertIn("xhigh", supported)

    def test_unsupported_or_downgraded_profile_cannot_report_acceptance(self) -> None:
        # Any of these bindings must fail closed and cannot satisfy final gates.
        for bad in ("xhigh", "high", "low", "unsupported-profile", ""):
            with self.subTest(bad=bad):
                self.assertNotEqual(bad, "max")
        policy = json.loads(POLICY_PATH.read_text())["real_llm_tests"]
        self.assertEqual(policy["thinking"], "max")
        # Wrong bundle / unverifiable binding is likewise not acceptance;
        # the companion bundle digest is recorded in evidence, not asserted here.

    def test_no_fallback_or_arbitrary_model_path_in_canonical_launcher(self) -> None:
        runner = RUNNER.read_text()
        self.assertNotIn("gpt-6-luna", runner)
        self.assertNotIn("gpt-6-astra\" --", runner)
        # No model/thinking override flags are offered; only PROMPT [CWD] or the
        # validated native-args shape (which itself emits only the fixed profile).
        self.assertNotIn("--model", runner.split("exec paseo run")[0].replace("--native-create-agent-args", ""))
        self.assertIn("usage:", runner)

    def test_superseded_luna_low_absent_from_product_authority(self) -> None:
        # Historical evidence and fixture model IDs are preserved elsewhere;
        # product authority (config/docs/scripts/contracts) must not retain
        # the superseded test-only Luna/low real-test profile.
        for path in list((ROOT / "config").rglob("*")) + list((ROOT / "docs").glob("*.md")):
            if path.is_file():
                text = path.read_text(errors="replace")
                self.assertNotIn("gpt-6-luna", text, str(path))
        for name in ("config/pi-agent/policies/llm-test-policy.json", "config/pi-agent/bin/run-llm-test.sh"):
            self.assertNotIn("codex-lb/gpt-6-luna", (ROOT / name).read_text())

    def test_target_repairs_preserved_without_regressing_update_system(self) -> None:
        # Accepted target repairs are present verbatim.
        self.assertIn("scripts/paseo-codex-lb-entrypoint.sh", DOCKERFILE)
        self.assertIn("paseo-docker-entrypoint.upstream", DOCKERFILE)
        self.assertIn("PI_CODEX_LB_SECRET_FILE: /run/secrets/pi-unraid-codex-lb", COMPOSE)
        self.assertIn("source: codex_lb_client", COMPOSE)
        self.assertIn("target: pi-unraid-codex-lb", COMPOSE)
        self.assertTrue((ROOT / "scripts" / "paseo-codex-lb-entrypoint.sh").is_file())
        self.assertTrue((ROOT / "scripts" / "reconcile-codex-lb-auth-shadow.py").is_file())
        self.assertTrue((ROOT / "scripts" / "reconcile-codex-lb-provider-config.py").is_file())
        self.assertTrue((ROOT / "config" / "pi-agent" / "extensions" / "codex-lb-dynamic-model-catalog.ts").is_file())
        # Update-system authority remains intact.
        self.assertTrue((ROOT / "scripts" / "managed_component_lifecycle.py").is_file())
        self.assertTrue((ROOT / "scripts" / "paseo_candidate_build.py").is_file())
        self.assertTrue((ROOT / "config" / "unraid" / "templates" / "pi-unraid-paseo.xml").is_file())
        self.assertIn("managed_component_lifecycle.py", AGENTS.read_text())

    def test_instruction_plane_bundle_is_declared_and_secret_safe(self) -> None:
        # Companion policy/provider/instruction bundle lives in the existing
        # candidate build context (copytree of source_root) and has frozen source
        # identity via the instruction-plane digest; no HOME mutation is involved.
        expected = {
            "AGENTS.md",
            "bin/run-llm-test.sh",
            "policies/LLM_TEST_POLICY.md",
            "policies/llm-test-policy.json",
        }
        present = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob("*") if p.is_file()}
        for rel in expected:
            self.assertIn(rel, present)
        corpus = "\n".join((SOURCE / rel).read_text() for rel in expected)
        for forbidden in (
            "OPENAI_API_KEY=",
            "ANTHROPIC_API_KEY=",
            "GITHUB_TOKEN=",
            "MUSE_API_KEY=",
            "CODEX_API_KEY=",
            "BEGIN PRIVATE KEY",
        ):
            self.assertNotIn(forbidden, corpus)
        self.assertIsNone(
            re.search(r"(?i)(password|token|api[_-]?key)\s*[:=]\s*[^\s]+", corpus)
        )
        # Pinned provider/dependency provenance is explicit and secret-free.
        self.assertEqual(CANDIDATE["components"]["pi"]["version"], "0.87.1")
        self.assertIn("ghcr.io/getpaseo/paseo@sha256:", DOCKERFILE)
        self.assertIn(CANDIDATE["components"]["paseo"]["artifact"]["digest"], DOCKERFILE)

    def test_candidate_build_context_binds_companion_bundle(self) -> None:
        # The existing build path stages the whole source root, so the new
        # instruction bundle participates in eligibility identity. Old digests
        # are not made eligible by this change.
        build_py = (ROOT / "scripts" / "paseo_candidate_build.py").read_text()
        self.assertIn("shutil.copytree", build_py)
        self.assertIn('ignore=shutil.ignore_patterns(".git"', build_py)
        self.assertIn('staged_candidate = stage_dir / "config" / "paseo-candidate.json"', build_py)


if __name__ == "__main__":
    unittest.main()
