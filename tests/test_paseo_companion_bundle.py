from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paseo_candidate_build_companion", ROOT / "scripts" / "paseo_candidate_build.py"
)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def make_source(root: Path) -> Path:
    source = root / "source"
    agent = source / "config" / "pi-agent"
    (agent / "bin").mkdir(parents=True)
    (agent / "policies").mkdir(parents=True)
    (agent / "AGENTS.md").write_text("# fixture companion\n")
    tool = agent / "bin" / "tool.sh"
    tool.write_text("#!/bin/sh\nexit 0\n")
    tool.chmod(0o755)
    (agent / "policies" / "p.json").write_text("{}\n")
    return source


class CompanionBundleBindingTests(unittest.TestCase):
    def test_identity_declares_files_modes_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            self.assertEqual(identity["schema_version"], 1)
            self.assertEqual(identity["source"], "config/pi-agent")
            self.assertEqual(
                identity["files"], ["AGENTS.md", "bin/tool.sh", "policies/p.json"]
            )
            self.assertEqual(
                identity["modes"],
                {"AGENTS.md": "0644", "bin/tool.sh": "0755", "policies/p.json": "0644"},
            )
            self.assertTrue(identity["source_digest"].startswith("sha256:"))
            # Deterministic across calls.
            again = BUILD.companion_bundle_identity(source)
            self.assertEqual(again, identity)

    def test_identity_is_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            text = json.dumps(identity, sort_keys=True)
            for forbidden in ("PRIVATE KEY", "API_KEY=", "GITHUB_TOKEN=", "ghp_"):
                self.assertNotIn(forbidden, text)

    def test_verify_accepts_matching_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            bound = BUILD.verify_companion_binding(source, identity)
            self.assertEqual(bound["status"], "bound")
            self.assertEqual(bound["source_digest"], identity["source_digest"])
            self.assertEqual(bound["files"], 3)

    def test_changed_content_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            (source / "config" / "pi-agent" / "AGENTS.md").write_text("# mutated\n")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, identity)

    def test_removed_file_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            (source / "config" / "pi-agent" / "policies" / "p.json").unlink()
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, identity)

    def test_added_file_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            (source / "config" / "pi-agent" / "EXTRA.md").write_text("# extra\n")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, identity)

    def test_wrong_declared_digest_or_modes_do_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            wrong_digest = dict(identity, source_digest="sha256:" + "0" * 64)
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, wrong_digest)
            wrong_modes = dict(identity, modes=dict(identity["modes"], **{"AGENTS.md": "0755"}))
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.verify_companion_binding(source, wrong_modes)

    def test_malformed_declaration_does_not_preserve_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source = make_source(Path(td))
            identity = BUILD.companion_bundle_identity(source)
            for bad in (
                None,
                [],
                dict(identity, schema_version=2),
                dict(identity, source="config/elsewhere"),
                dict(identity, files="AGENTS.md"),
                dict(identity, modes={}),
            ):
                with self.subTest(bad=repr(bad)[:60]):
                    with self.assertRaises(BUILD.CandidateBuildError):
                        BUILD.verify_companion_binding(source, bad)

    def test_missing_source_and_symlink_are_unverifiable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.companion_bundle_identity(root / "absent")
            source = make_source(root)
            (source / "config" / "pi-agent" / "link.md").symlink_to("AGENTS.md")
            with self.assertRaises(BUILD.CandidateBuildError):
                BUILD.companion_bundle_identity(source)

    def test_real_source_bundle_binds_and_matches_declared_modes(self) -> None:
        identity = BUILD.companion_bundle_identity(ROOT)
        self.assertIn("bin/run-llm-test.sh", identity["files"])
        self.assertEqual(identity["modes"]["bin/run-llm-test.sh"], "0755")
        bound = BUILD.verify_companion_binding(ROOT, identity)
        self.assertEqual(bound["status"], "bound")


if __name__ == "__main__":
    unittest.main()
