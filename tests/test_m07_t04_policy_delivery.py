from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
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
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "m07t04" / "pi-ai-0.87.1-meta-contributor.json").read_text()
)
PI_AI_ROOT = Path(
    "/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules"
    "/@earendil-works/pi-ai"
)
INSTALLED_META = PI_AI_ROOT / "dist" / "providers" / "data" / "meta.json"
INSTALLED_MODELS_JS = PI_AI_ROOT / "dist" / "models.js"
PINNED_PI_VERSION = "0.87.1"

_spec = importlib.util.spec_from_file_location(
    "paseo_candidate_build_m07t04", ROOT / "scripts" / "paseo_candidate_build.py"
)
assert _spec and _spec.loader
BUILD = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BUILD)


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

    def test_pinned_fixture_records_contributor_max_null_as_metadata_only(self) -> None:
        # Pinned-source catalog metadata (always executes; no inference): the
        # upstream bundle marks contributor max unsupported on the direct-Meta
        # path. Metadata alone proves nothing about wire behavior; effective
        # max acceptance stays deferred to M08-T01 after M07-T05 machinery.
        provenance = FIXTURE["_provenance"]
        self.assertEqual(provenance["package"], "@earendil-works/pi-ai")
        self.assertEqual(provenance["version"], PINNED_PI_VERSION)
        model = FIXTURE["model"]
        self.assertEqual(model["id"], "muse-spark-1.3-contributor")
        level_map = model["thinkingLevelMap"]
        self.assertIsNone(level_map["max"])
        self.assertEqual(level_map["xhigh"], "xhigh")

    def installed_contributor_entry(self):
        # Provenance-gated upstream readback: trust the installed bundle only
        # when its package version matches the frozen Dockerfile/candidate pin.
        # Returns the contributor model object, or skips honestly with reason.
        pkg = PI_AI_ROOT / "package.json"
        if not pkg.is_file():
            self.skipTest("installed pi-ai package unavailable; fixture test above still executed")
        version = json.loads(pkg.read_text()).get("version")
        if version != PINNED_PI_VERSION:
            self.skipTest(
                f"installed pi-ai is {version}, not the pinned {PINNED_PI_VERSION}; "
                "fixture test above still executed"
            )
        if not INSTALLED_META.is_file() or not INSTALLED_MODELS_JS.is_file():
            self.skipTest("installed pi-ai bundle files unavailable; fixture test above still executed")
        data = json.loads(INSTALLED_META.read_text())
        entry = data.get("openai-responses", data).get("muse-spark-1.3-contributor")
        self.assertIsNotNone(entry)
        return entry

    def test_pinned_fixture_matches_installed_bundle_metadata(self) -> None:
        entry = self.installed_contributor_entry()
        self.assertEqual(entry["thinkingLevelMap"], FIXTURE["model"]["thinkingLevelMap"])

    def test_upstream_selection_function_clamps_max_to_xhigh(self) -> None:
        # Executes Pi's ACTUAL bundled selection function (pure, non-inference
        # source readback) against the installed contributor entry: unmodified
        # pinned data excludes max and clamps a max request to xhigh. This is
        # the explicit fake-max hazard, not an acceptance claim; proving the
        # effective profile on-wire remains M07-T05/M08-T01 scope (deferred).
        entry = self.installed_contributor_entry()
        model = {
            "id": entry["id"],
            "provider": entry.get("provider"),
            "reasoning": entry.get("reasoning"),
            "thinkingLevelMap": entry.get("thinkingLevelMap"),
        }
        code = (
            "import {getSupportedThinkingLevels, clampThinkingLevel} "
            f"from '{INSTALLED_MODELS_JS.as_uri()}';\n"
            "const model = JSON.parse(process.argv[1]);\n"
            "console.log(JSON.stringify({supported: getSupportedThinkingLevels(model), "
            "clamped: clampThinkingLevel(model, 'max')}));\n"
        )
        if shutil.which("node") is None:
            self.skipTest("node unavailable for upstream-function readback")
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", code, json.dumps(model)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertNotIn("max", out["supported"])
        self.assertIn("xhigh", out["supported"])
        self.assertEqual(out["clamped"], "xhigh")

    def _run_delivered_launcher(self, policy, argv):
        # Behavioral guard proof on the actual delivered launcher bytes: copy
        # the real launcher into a disposable symlink-free agent root and run
        # it against a fake Paseo executable (no inference possible).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "agent"
            (agent / "bin").mkdir(parents=True)
            (agent / "policies").mkdir(parents=True)
            launcher = agent / "bin" / "run-llm-test.sh"
            launcher.write_bytes(RUNNER.read_bytes())
            launcher.chmod(0o755)
            (agent / "policies" / "llm-test-policy.json").write_text(json.dumps(policy))
            fakebin = root / "fakebin"
            fakebin.mkdir()
            marker = root / "dispatched.txt"
            fake = fakebin / "paseo"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$DISPATCH_MARKER"\n')
            fake.chmod(0o755)
            env = {"PATH": f"{fakebin}:/usr/bin:/bin", "DISPATCH_MARKER": str(marker)}
            proc = subprocess.run(
                [str(launcher)] + argv, env=env,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            return proc, marker

    def test_downgraded_or_native_shape_profile_cannot_become_acceptance(self) -> None:
        # A downgraded effective level must fail closed in both invocation
        # shapes: prompt dispatch never runs, and the native-args shape emits
        # no fixed-shape payload. Neither observation satisfies final gates.
        for thinking in ("xhigh", "high"):
            with self.subTest(thinking=thinking):
                policy = {
                    "schema": 1,
                    "real_llm_tests": {
                        "provider": "meta",
                        "model": "muse-spark-1.3-contributor",
                        "thinking": thinking,
                        "forbidden_models": ["gpt-6-astra"],
                        "fallback_allowed": False,
                    },
                }
                proc, marker = self._run_delivered_launcher(policy, ["SYNTHETIC_PROMPT_NO_INFERENCE"])
                self.assertEqual(proc.returncode, 3, proc.stderr)
                self.assertFalse(marker.exists())
                proc, marker = self._run_delivered_launcher(policy, ["--native-create-agent-args"])
                self.assertEqual(proc.returncode, 3, proc.stderr)
                self.assertFalse(marker.exists())

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
        product = (
            list((ROOT / "config").rglob("*"))
            + list((ROOT / "docs").glob("*.md"))
            + list((ROOT / "contracts").rglob("*"))
            + list((ROOT / "scripts").glob("*.py"))
            + list((ROOT / "scripts").glob("*.sh"))
        )
        for path in product:
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
        # Reconciled product contract preserves non-conflicting target intent
        # with only the superseded test/rollout provisions R2-qualified.
        contract = ROOT / "contracts" / "PASEO_CODEX_LB_RUNTIME_ENV.md"
        self.assertTrue(contract.is_file())
        contract_text = contract.read_text()
        self.assertIn("muse-spark-1.3-contributor", contract_text)
        self.assertNotIn("gpt-6-luna", contract_text)
        for kept in (
            "PI_CODEX_LB_SECRET_FILE",
            "immutable path",
            "supported_reasoning_levels",
            "M08-T01",
        ):
            self.assertIn(kept, contract_text)
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

    def test_prepare_declares_actual_companion_bundle_identity(self) -> None:
        # The existing prepare path must declare the REAL frozen companion
        # identity (files + modes + digest from the installer-owned source),
        # not merely copy bytes. Old digests gain no eligibility from this.
        identity = BUILD.companion_bundle_identity(ROOT)
        self.assertEqual(identity["source"], "config/pi-agent")
        self.assertIn("AGENTS.md", identity["files"])
        self.assertIn("bin/run-llm-test.sh", identity["files"])
        self.assertIn("policies/llm-test-policy.json", identity["files"])
        self.assertEqual(identity["modes"]["bin/run-llm-test.sh"], "0755")
        self.assertEqual(identity["modes"]["AGENTS.md"], "0644")
        self.assertTrue(identity["source_digest"].startswith("sha256:"))
        bound = BUILD.verify_companion_binding(ROOT, identity)
        self.assertEqual(bound["status"], "bound")
        self.assertEqual(bound["source_digest"], identity["source_digest"])


if __name__ == "__main__":
    unittest.main()
