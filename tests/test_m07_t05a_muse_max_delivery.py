"""M07-T05A muse-max delivery tests (bounded stable acceptance).

Classification: synthetic/local fixtures + approved non-inference source
readback ONLY. Fake-only external boundaries; isolated disposable HOME and
temp roots; PATH isolated where executables run; no real inference, no live
provider auth/admission, no ordinary-credential reads, no installed
HOME/catalog/runtime mutation, no live Docker/Tower/host, no CI/build/
publication/push. No endpoint/candidate acceptance from metadata or
diagnostics: catalog presence, launcher shape and fake-wire success are
exercised only as clamp-correctness controls, never as capability proof.

Inference-capable touched entrypoints (all exercised ONLY via fakes):
- scripts/paseo_candidate_muse_adapter.py: dispatch_owned_runtime,
  dispatch_guarded_test, ensure_candidate_daemon, preflight_candidate_profile
  (fake bindirs, disposable roots, synthetic META_API_KEY pointer files only)
- scripts/paseo_tower_validator.py: validate() muse dispatch path (mocked
  docker + fake paseo + local http fixtures + synthetic secrets only)
- config/pi-agent/bin/run-llm-test.sh, m07-t05-owned-runtime.mjs,
  m07-t05-pi-owned.py (executed only via staged local copies with fake
  paseo on PATH, never real provider transport)
- config/pi-agent/bin/paseo-muse-max-merge.py (local subprocess with
  disposable fragment/effective paths only, no HOME mutation)

Pinned composition uses the genuine shipped Pi 0.87.1 files
(provider-composer.js, model-config.js, pi-ai/dist/models.js,
openai-responses.js) with fake in-memory model objects only; no network,
no catalog fetch, no auth, no models-store reliance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


A = _load("muse_adapter_m05a", "scripts/paseo_candidate_muse_adapter.py")
BUILD = _load("candidate_build_m05a", "scripts/paseo_candidate_build.py")
INST = _load("instruction_plane_m05a", "scripts/pi_instruction_plane.py")

FRAG_SRC = ROOT / "config" / "pi-agent" / "models.muse-max-override.json"
MERGE_SRC = ROOT / "config" / "pi-agent" / "bin" / "paseo-muse-max-merge.py"
PI_ROOT = Path("/usr/local/lib/node_modules/@earendil-works/pi-coding-agent")

REQUIRED_FRAG = {
    "providers": {
        "meta": {
            "modelOverrides": {
                "muse-spark-1.3-contributor": {
                    "thinkingLevelMap": {"max": "max"}
                }
            }
        }
    }
}


def _node():
    for d in os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin").split(os.pathsep):
        c = Path(d) / "node"
        if c.is_file() and os.access(c, os.X_OK):
            return str(c)
    for f in ("/usr/local/bin/node", "/usr/bin/node"):
        if Path(f).is_file() and os.access(f, os.X_OK):
            return f
    return None


class FragmentValidationTests(unittest.TestCase):
    def test_frozen_fragment_is_exact_minimal_secret_free(self):
        self.assertTrue(FRAG_SRC.is_file(), "frozen fragment missing")
        self.assertFalse(FRAG_SRC.is_symlink(), "fragment must not be symlink")
        raw = FRAG_SRC.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
        self.assertEqual(doc, REQUIRED_FRAG)
        A.validate_muse_max_fragment(doc)
        ident = A.muse_max_fragment_identity(ROOT)
        self.assertEqual(ident["mode"], "0644")
        self.assertTrue(ident["sha256"].startswith("sha256:"))
        self.assertEqual(ident["sha256"], "sha256:" + hashlib.sha256(raw).hexdigest())
        text = raw.decode("utf-8")
        self.assertNotIn("apiKey", text)
        self.assertNotIn("!", text.split('"max"')[0] if '"max"' in text else text)
        self.assertNotIn("$", text)

    def test_fragment_rejects_extra_providers_models_routing(self):
        base = json.loads(json.dumps(REQUIRED_FRAG))
        # Extra provider in fragment must fail.
        bad = json.loads(json.dumps(base))
        bad["providers"]["codex-lb"] = {"baseUrl": "http://h:1/v1"}
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)
        # Extra model override must fail.
        bad = json.loads(json.dumps(base))
        bad["providers"]["meta"]["modelOverrides"]["other-model"] = {"thinkingLevelMap": {"max": "max"}}
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)
        # Extra thinking key must fail (only max permitted in fragment).
        bad = json.loads(json.dumps(base))
        bad["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["xhigh"] = "xhigh"
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)
        # Null for required key must fail.
        bad = json.loads(json.dumps(base))
        bad["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"] = None
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)
        # Wrong value must fail.
        bad = json.loads(json.dumps(base))
        bad["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"] = "xhigh"
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)

    def test_fragment_rejects_secrets_routing_commands(self):
        for banned, payload in (
            ("apiKey", {"apiKey": "sk-secret"}),
            ("baseUrl", {"baseUrl": "http://h:1/v1"}),
            ("models", {"models": [{"id": "x"}]}),
            ("headers", {"headers": {"X": "y"}}),
        ):
            bad = json.loads(json.dumps(REQUIRED_FRAG))
            bad["providers"]["meta"][banned] = payload[banned]
            with self.subTest(banned=banned), self.assertRaises(A.AdapterError):
                A.validate_muse_max_fragment(bad)
        bad = json.loads(json.dumps(REQUIRED_FRAG))
        bad["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"] = "!cmd"
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)
        bad = json.loads(json.dumps(REQUIRED_FRAG))
        bad["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"] = "${EVIL}"
        with self.assertRaises(A.AdapterError):
            A.validate_muse_max_fragment(bad)

    def test_merge_helper_rejects_same_invalid_fragments(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            eff = td / "models.json"
            eff.write_text('{"providers":{}}')
            eff.chmod(0o600)
            bad = json.loads(json.dumps(REQUIRED_FRAG))
            bad["providers"]["extra"] = {"modelOverrides": {}}
            frag = td / "frag.json"
            frag.write_text(json.dumps(bad))
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pr.returncode, 0)
            # Existing preserved (not overwritten with bad fragment).
            self.assertEqual(json.loads(eff.read_text())["providers"], {})


class MergeSafetyTests(unittest.TestCase):
    def _write(self, path: Path, doc, mode=0o600):
        path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")
        path.chmod(mode)

    def test_minimal_only_override_provider_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            frag = td / "frag.json"
            frag.write_text(json.dumps(REQUIRED_FRAG))
            eff = td / "models.json"
            # No existing file: merge creates minimal effective with only override.
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(pr.returncode, 0, pr.stderr)
            doc = json.loads(eff.read_text())
            A.verify_muse_max_effective(doc)
            self.assertEqual(set(doc["providers"].keys()), {"meta"})
            self.assertEqual(eff.stat().st_mode & 0o777, 0o600)

    def test_unrelated_providers_preserved_verbatim(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            frag = td / "frag.json"
            frag.write_text(json.dumps(REQUIRED_FRAG))
            eff = td / "models.json"
            existing = {
                "providers": {
                    "codex-lb": {
                        "baseUrl": "http://host:1/v1",
                        "api": "openai-responses",
                        "apiKey": "${CODEX_LB_API_KEY}",
                        "models": [{"id": "fixture-model"}],
                    },
                    "openrouter": {
                        "baseUrl": "https://openrouter.ai/api/v1",
                        "apiKey": "${OPENROUTER_API_KEY}",
                        "models": [{"id": "other"}],
                    },
                    "meta": {
                        "modelOverrides": {
                            "some-other-model": {"thinkingLevelMap": {"max": "max"}},
                            "muse-spark-1.3-contributor": {
                                "thinkingLevelMap": {"max": None, "xhigh": "xhigh", "high": "high"}
                            },
                        },
                        "customNote": "preserve-me",
                    },
                }
            }
            self._write(eff, existing)
            before = eff.read_bytes()
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(pr.returncode, 0, pr.stderr)
            after = json.loads(eff.read_text())
            # Unrelated providers byte-identical in semantic content.
            self.assertEqual(after["providers"]["codex-lb"], existing["providers"]["codex-lb"])
            self.assertEqual(after["providers"]["openrouter"], existing["providers"]["openrouter"])
            # Other model override preserved.
            self.assertEqual(after["providers"]["meta"]["modelOverrides"]["some-other-model"],
                             existing["providers"]["meta"]["modelOverrides"]["some-other-model"])
            # Other meta key preserved.
            self.assertEqual(after["providers"]["meta"]["customNote"], "preserve-me")
            # Required key fixed, other thinking keys preserved (shallow merge).
            tlm = after["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]
            self.assertEqual(tlm["max"], "max")
            self.assertEqual(tlm["xhigh"], "xhigh")
            self.assertEqual(tlm["high"], "high")
            self.assertNotEqual(before, eff.read_bytes())

    def test_explicit_null_in_existing_is_fixed_only_for_required_key(self):
        with tempfile.TemporaryDirectory():
            existing_null = {
                "providers": {
                    "meta": {
                        "modelOverrides": {
                            "muse-spark-1.3-contributor": {
                                "thinkingLevelMap": {"max": None}
                            }
                        }
                    }
                }
            }
            merged = A.merge_muse_max_effective(existing_null, REQUIRED_FRAG)
            self.assertEqual(
                merged["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"],
                "max")
            # Without delivery, null remains clamped (composition-level negative
            # covered in PinnedCompositionTests; here verify_muse rejects null).
            with self.assertRaises(A.AdapterError):
                A.verify_muse_max_effective(existing_null)

    def test_invalid_unsafe_symlink_rejected_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            frag = td / "frag.json"
            frag.write_text(json.dumps(REQUIRED_FRAG))
            # Malformed existing preserved.
            eff = td / "models.json"
            eff.write_text("{not json")
            eff.chmod(0o600)
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pr.returncode, 0)
            self.assertEqual(eff.read_text(), "{not json")
            # Non-object root preserved.
            eff.write_text("[]")
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pr.returncode, 0)
            # Symlink fragment rejected.
            real = td / "real.json"
            real.write_text(json.dumps(REQUIRED_FRAG))
            link = td / "link.json"
            try:
                link.symlink_to(real)
            except OSError:
                self.skipTest("symlink unavailable")
            eff2 = td / "e2.json"
            eff2.write_text('{"providers":{}}')
            eff2.chmod(0o600)
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(link), "--models", str(eff2)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pr.returncode, 0)
            # Symlink effective rejected.
            eff_link = td / "efflink.json"
            try:
                eff_link.symlink_to(eff2)
            except OSError:
                self.skipTest("symlink unavailable")
            pr = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff_link)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pr.returncode, 0)

    def test_idempotent_merge_and_bounded_check_restore(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            frag = td / "frag.json"
            frag.write_text(json.dumps(REQUIRED_FRAG))
            eff = td / "models.json"
            self._write(eff, {"providers": {"codex-lb": {"baseUrl": "http://h:1/v1"}}})
            r1 = A.apply_muse_max_merge(td, td) if False else None  # placeholder (unused)
            # First apply via helper CLI.
            p1 = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p1.returncode, 0, p1.stderr)
            d1 = json.loads(p1.stdout)
            self.assertTrue(d1["changed"])
            h1 = eff.read_bytes()
            # Second apply is idempotent (no change, same digest).
            p2 = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p2.returncode, 0, p2.stderr)
            d2 = json.loads(p2.stdout)
            self.assertFalse(d2["changed"])
            self.assertEqual(d2["effective_sha256"], d1["effective_sha256"])
            self.assertEqual(eff.read_bytes(), h1)
            # --check passes when in sync.
            pc = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff), "--check"],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(pc.returncode, 0, pc.stderr)
            # Manual drift breaks --check (write-and-restore to same bytes passes
            # hash but mode drift still fails; content drift fails).
            eff.chmod(0o644)
            pc2 = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff), "--check"],
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pc2.returncode, 0)
            eff.chmod(0o600)
            # Content substitution breaks check.
            doc = json.loads(eff.read_text())
            doc["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"] = None
            self._write(eff, doc)
            pc3 = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff), "--check"],
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(pc3.returncode, 0)
            # Re-apply restores boundedly (only required key, unrelated kept).
            p3 = subprocess.run([sys.executable, str(MERGE_SRC), "--fragment", str(frag), "--models", str(eff)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p3.returncode, 0, p3.stderr)
            self.assertEqual(json.loads(eff.read_text())["providers"]["meta"]["modelOverrides"]
                             ["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"], "max")

    def test_adapter_apply_matches_helper_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "src" / "config" / "pi-agent"
            src.mkdir(parents=True)
            (src / "models.muse-max-override.json").write_text(json.dumps(REQUIRED_FRAG))
            home_agent = td / "home" / ".pi" / "agent"
            home_agent.mkdir(parents=True)
            existing = {"providers": {"codex-lb": {"baseUrl": "http://h:1/v1"}}}
            (home_agent / "models.json").write_text(json.dumps(existing))
            (home_agent / "models.json").chmod(0o600)
            res = A.apply_muse_max_merge(home_agent, td / "src")
            self.assertIn("effective", res)
            eff = json.loads((home_agent / "models.json").read_text())
            self.assertEqual(eff["providers"]["codex-lb"], existing["providers"]["codex-lb"])
            A.verify_muse_max_effective(eff)
            self.assertEqual((home_agent / "models.json").stat().st_mode & 0o777, 0o600)


class PinnedCompositionTests(unittest.TestCase):
    """Genuine pinned Pi 0.87.1 composition with fake model objects only."""

    def _run_node(self, script: str):
        node = _node()
        if node is None:
            self.skipTest("node unavailable")
        pr = subprocess.run([node, "--input-type=module", "-e", script],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return pr

    def test_supported_levels_and_clamp_positive_negative(self):
        script = (
            "import {createRequire} from 'node:module';\n"
            "const require = createRequire(import.meta.url);\n"
            "const m = require('/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/models.js');\n"
            "const base = {id:'muse-spark-1.3-contributor', reasoning:true, thinkingLevelMap:{off:null,minimal:'minimal',low:'low',medium:'medium',high:'high',xhigh:'xhigh',max:null}};\n"
            "const unmod = {supported: m.getSupportedThinkingLevels(base), clamp: m.clampThinkingLevel(base,'max')};\n"
            "const merged = {...base, thinkingLevelMap:{...base.thinkingLevelMap, max:'max'}};\n"
            "const pos = {supported: m.getSupportedThinkingLevels(merged), clamp: m.clampThinkingLevel(merged,'max')};\n"
            "const nulled = {...base, thinkingLevelMap:{...base.thinkingLevelMap, max:null}};\n"
            "const neg = {supported: m.getSupportedThinkingLevels(nulled), clamp: m.clampThinkingLevel(nulled,'max')};\n"
            "console.log(JSON.stringify({unmod, pos, neg}));\n"
        )
        pr = self._run_node(script)
        self.assertEqual(pr.returncode, 0, pr.stderr)
        doc = json.loads(pr.stdout)
        # Unmodified bundled-shape: max unsupported, clamped to xhigh.
        self.assertNotIn("max", doc["unmod"]["supported"])
        self.assertEqual(doc["unmod"]["clamp"], "xhigh")
        # Merged max=max: supported includes max, clamp stays max.
        self.assertIn("max", doc["pos"]["supported"])
        self.assertEqual(doc["pos"]["clamp"], "max")
        # Explicit null stays clamped.
        self.assertNotIn("max", doc["neg"]["supported"])
        self.assertEqual(doc["neg"]["clamp"], "xhigh")

    def test_wire_effort_passthrough_cannot_prove_capability(self):
        script = (
            "const cases = [{map:{max:null}, req:'max'}, {map:{max:'max'}, req:'max'}];\n"
            "const out = cases.map(c => (c.map[c.req] ?? c.req));\n"
            "console.log(JSON.stringify(out));\n"
        )
        pr = self._run_node(script)
        self.assertEqual(pr.returncode, 0, pr.stderr)
        out = json.loads(pr.stdout)
        # Both serialize as 'max' (?? passthrough): wire bytes alone prove nothing.
        self.assertEqual(out, ["max", "max"])

    def test_unknown_override_ignored_and_only_override_shape(self):
        script = (
            "import {readFileSync} from 'node:fs';\n"
            "const src = readFileSync('/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/provider-composer.js','utf8');\n"
            "const hasShallow = src.includes('...model.thinkingLevelMap, ...override.thinkingLevelMap');\n"
            "const hasTopmost = src.includes('topmost user-config layer');\n"
            "const hasOverridesGate = src.includes('hasOverrides');\n"
            "console.log(JSON.stringify({hasShallow, hasTopmost, hasOverridesGate}));\n"
        )
        pr = self._run_node(script)
        self.assertEqual(pr.returncode, 0, pr.stderr)
        doc = json.loads(pr.stdout)
        self.assertTrue(doc["hasShallow"], "shallow key-merge must be documented in pinned source")
        self.assertTrue(doc["hasTopmost"], "topmost-layer order must be documented")
        self.assertTrue(doc["hasOverridesGate"], "only-override shape gate must exist")
        # Unknown IDs ignored is documented in models.md (read in full per Card).
        md = (PI_ROOT / "docs" / "models.md").read_text(encoding="utf-8")
        self.assertIn("Unknown override IDs are ignored", md)

    def test_only_override_provider_shape_validates(self):
        # A provider carrying ONLY modelOverrides satisfies the must-specify
        # gate (hasOverrides) without baseUrl rewrite: minimal fragment is
        # schema/shape-valid per pinned provider-composer.js.
        src = (PI_ROOT / "dist" / "core" / "provider-composer.js").read_text(encoding="utf-8")
        self.assertIn('must specify "baseUrl", "headers", "compat", "modelOverrides", or "models"',
                      src)
        cfg = (PI_ROOT / "dist" / "core" / "model-config.js").read_text(encoding="utf-8")
        self.assertIn("modelOverrides", cfg)
        # Fragment itself validates as a minimal provider record shape.
        frag = json.loads(FRAG_SRC.read_bytes())
        self.assertEqual(set(frag["providers"].keys()), {"meta"})
        self.assertNotIn("baseUrl", frag["providers"]["meta"])
        self.assertNotIn("models", frag["providers"]["meta"])


class EffectiveBindingTests(unittest.TestCase):
    def test_fragment_and_effective_identities_modes(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "src" / "config" / "pi-agent"
            src.mkdir(parents=True)
            (src / "models.muse-max-override.json").write_text(json.dumps(REQUIRED_FRAG))
            (src / "models.muse-max-override.json").chmod(0o644)
            (src / "bin").mkdir()
            (src / "bin" / "m07-t05-applied.py").write_text(
                (ROOT / "config" / "pi-agent" / "bin" / "m07-t05-applied.py").read_text())
            home_agent = td / "home" / ".pi" / "agent"
            home_agent.mkdir(parents=True)
            res = A.apply_muse_max_merge(home_agent, td / "src")
            frag_ident = A.muse_max_fragment_identity(td / "src")
            self.assertEqual(frag_ident["mode"], "0644")
            eff_raw = (home_agent / "models.json").read_bytes()
            eff_ident = A.muse_max_effective_identity(eff_raw, 0o600)
            self.assertEqual(eff_ident["mode"], "0600")
            self.assertEqual(res["effective"]["sha256"], eff_ident["sha256"])
            # Secret-safe: identities carry digests/modes/paths only.
            for ident in (frag_ident, eff_ident):
                self.assertNotIn("META_API_KEY", json.dumps(ident))
                self.assertNotIn("CODEX_LB_API_KEY", json.dumps(ident))

    def test_interval_rows_include_effective_when_staged(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = ROOT / "config" / "pi-agent"
            ident = BUILD.companion_bundle_identity(ROOT)
            self.assertIn("models.muse-max-override.json", ident["files"])
            self.assertIn("bin/paseo-muse-max-merge.py", ident["files"])
            self.assertEqual(ident["modes"]["models.muse-max-override.json"], "0644")
            self.assertEqual(ident["modes"]["bin/paseo-muse-max-merge.py"], "0755")
            # Home without effective: rows equal companion files.
            home = td / "home1"
            (home / ".m07-t05").mkdir(parents=True)
            auth1 = A.stage_applied_interval(home, src, ident, nonce="n1", uid=os.getuid(), gid=os.getgid())
            self.assertEqual(set(auth1["manifest"]["files"].keys()), set(ident["files"]))
            self.assertNotIn("models.json", auth1["manifest"]["files"])
            # Home with staged effective: rows include derived file at 0600.
            home2 = td / "home2"
            (home2 / ".pi" / "agent").mkdir(parents=True)
            (home2 / ".m07-t05").mkdir(parents=True)
            # Copy companion bytes host-side (same as validator staging).
            for rel in ident["files"]:
                dst = home2 / ".pi" / "agent" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes((src / rel).read_bytes())
            A.apply_muse_max_merge(home2 / ".pi" / "agent", ROOT)
            (home2 / ".pi" / "agent" / "models.json").chmod(0o600)
            auth2 = A.stage_applied_interval(home2, src, ident, nonce="n2", uid=os.getuid(), gid=os.getgid())
            self.assertIn("models.json", auth2["manifest"]["files"])
            self.assertEqual(auth2["manifest"]["files"]["models.json"]["mode"], "0600")
            eff_doc = json.loads((home2 / ".pi" / "agent" / "models.json").read_text())
            A.verify_muse_max_effective(eff_doc)

    def test_post_preflight_mutations_reject_before_transport(self):
        # Changed/missing/substituted/restored fragment or derived config,
        # wrong model/provider/profile, ambiguous config, fixture-as-real and
        # fallback cannot dispatch or satisfy final validation.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "src" / "config" / "pi-agent"
            src.mkdir(parents=True)
            (src / "models.muse-max-override.json").write_text(json.dumps(REQUIRED_FRAG))
            home_agent = td / "home" / ".pi" / "agent"
            home_agent.mkdir(parents=True)
            A.apply_muse_max_merge(home_agent, td / "src")
            good = (home_agent / "models.json").read_bytes()
            # Changed derived content rejects.
            bad_doc = json.loads(good.decode())
            bad_doc["providers"]["meta"]["modelOverrides"]["muse-spark-1.3-contributor"]["thinkingLevelMap"]["max"] = None
            with self.assertRaises(A.AdapterError):
                A.verify_muse_max_effective(bad_doc)
            # Missing derived rejects.
            with self.assertRaises(A.AdapterError):
                A.verify_muse_max_effective({"providers": {}})
            # Wrong model rejects.
            with self.assertRaises(A.AdapterError):
                A.validate_requested_profile("meta", "muse-spark-1.3", "max")
            # Wrong provider rejects.
            with self.assertRaises(A.AdapterError):
                A.validate_requested_profile("openrouter", "muse-spark-1.3-contributor", "max")
            # Wrong thinking (xhigh clamp) rejects.
            with self.assertRaises(A.AdapterError):
                A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "xhigh")
            # Fallback rejects.
            with self.assertRaises(A.AdapterError):
                A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "max", fallback_allowed=True)
            # Fixture-as-real never satisfies (outcome_for_fixture always false).
            req = A.fixed_profile()
            snap = {"dispatched": True, "returncode": 0, "timeout": False}
            out = A.outcome_for_fixture(requested=req, dispatch_snapshot=snap,
                                        observed_effective={"provider": "meta", "model": "muse-spark-1.3-contributor", "thinking": "max"})
            self.assertFalse(out["real_validation_satisfied"])
            self.assertEqual(out["execution_class"], "fixture")
            # Uncertainty after dispatch retains non-replay outcome.
            snap_timeout = {"dispatched": False, "returncode": None, "timeout": True}
            out2 = A.outcome_for_fixture(requested=req, dispatch_snapshot=snap_timeout, observed_effective=None)
            self.assertEqual(out2["terminal_class"], "unknown")
            self.assertIn("no replay", out2["reason"])
            self.assertFalse(out2["real_validation_satisfied"])
            # Write-and-restore of derived file: even restored bytes would have
            # required a failing interval event; here the merge check catches
            # the intermediate null before restore.
            (home_agent / "models.json").write_bytes(
                json.dumps(bad_doc, sort_keys=True, indent=2).encode() + b"\n")
            with self.assertRaises(A.AdapterError):
                A.verify_muse_max_effective(json.loads((home_agent / "models.json").read_text()))
            # Restore via re-merge is bounded (only required key).
            A.apply_muse_max_merge(home_agent, td / "src")
            A.verify_muse_max_effective(json.loads((home_agent / "models.json").read_text()))

    def test_fixed_profile_no_fallback_preserved(self):
        prof = A.fixed_profile()
        self.assertEqual((prof["provider"], prof["model"], prof["thinking"]),
                         ("meta", "muse-spark-1.3-contributor", "max"))
        self.assertFalse(prof["fallback_allowed"])
        self.assertIn("gpt-6-astra", prof["forbidden_models"])
        A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "max")
        with self.assertRaises(A.AdapterError):
            A.validate_requested_profile("meta", "muse-spark-1.3-contributor", "max", fallback_allowed=True)


class CompanionInstructionPlaneTests(unittest.TestCase):
    def test_real_companion_includes_new_delivery(self):
        ident = BUILD.companion_bundle_identity(ROOT)
        self.assertIn("models.muse-max-override.json", ident["files"])
        self.assertIn("bin/paseo-muse-max-merge.py", ident["files"])
        self.assertEqual(ident["modes"]["models.muse-max-override.json"], "0644")
        self.assertEqual(ident["modes"]["bin/paseo-muse-max-merge.py"], "0755")
        self.assertTrue(ident["source_digest"].startswith("sha256:"))
        # Old 17-member digest is historical input, never retained after change.
        self.assertNotEqual(ident["source_digest"],
                            "sha256:41d5d8fdd37fa5c76b8e3ee925cf6468b0e5040132066a585da11dfd397b9705")
        bound = BUILD.verify_companion_binding(ROOT, ident)
        self.assertEqual(bound["source_digest"], ident["source_digest"])
        # Secret-free: no credential values in identity.
        self.assertNotIn("META_API_KEY", json.dumps(ident))
        self.assertNotIn("CODEX_LB_API_KEY", json.dumps(ident))

    def test_instruction_plane_delivers_new_files(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = ROOT / "config" / "pi-agent"
            home = td / "home"
            home.mkdir()
            res = INST.apply(src, home)
            self.assertTrue(res["in_sync"])
            agent = home / ".pi" / "agent"
            self.assertTrue((agent / "models.muse-max-override.json").is_file())
            self.assertTrue((agent / "bin" / "paseo-muse-max-merge.py").is_file())
            self.assertEqual((agent / "models.muse-max-override.json").stat().st_mode & 0o777, 0o644)
            self.assertEqual((agent / "bin" / "paseo-muse-max-merge.py").stat().st_mode & 0o777, 0o755)
            self.assertEqual(json.loads((agent / "models.muse-max-override.json").read_text()), REQUIRED_FRAG)
            st = INST.status(src, home)
            self.assertTrue(st["in_sync"])
            # Symlink in source fails closed (never delivered).
            with tempfile.TemporaryDirectory() as td2:
                td2 = Path(td2)
                s2 = td2 / "src"
                shutil.copytree(src, s2)
                (s2 / "evil-link").symlink_to(s2 / "AGENTS.md")
                with self.assertRaises(SystemExit):
                    INST.safe_files(s2)

    def test_old_artifact_never_eligible(self):
        ident = BUILD.companion_bundle_identity(ROOT)
        old = dict(ident, source_digest="sha256:" + "0" * 64)
        with self.assertRaises(BUILD.CandidateBuildError):
            BUILD.verify_companion_binding(ROOT, old)


if __name__ == "__main__":
    unittest.main()
