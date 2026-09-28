from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CANDIDATE_WORKFLOW = WORKFLOWS / "paseo-candidate-resolver.yml"
HELPER = ROOT / "scripts" / "paseo_candidate_handoff.py"
SPEC = importlib.util.spec_from_file_location("paseo_candidate_handoff", HELPER)
HANDOFF = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(HANDOFF)


def candidate(identity: str) -> dict:
    return {"schema_version": 1, "candidate_id": identity, "components": {}}


class OperationalWorkflowTopologyTests(unittest.TestCase):
    def test_candidate_discovery_is_default_branch_daily_and_manual(self):
        text = CANDIDATE_WORKFLOW.read_text()
        self.assertIn("schedule:", text)
        self.assertIn('cron: "17 3 * * *"', text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("github.event.repository.default_branch", text)
        self.assertNotIn("\n  push:\n", text)

    def test_closed_feature_push_triggers_are_retired_everywhere(self):
        for path in WORKFLOWS.glob("*.yml"):
            text = path.read_text()
            self.assertNotIn("feat/paseo-gui-runtime", text, path.name)
            self.assertNotIn("\n  push:\n", text, path.name)
            self.assertIn("workflow_dispatch:", text, path.name)

    def test_candidate_handoff_is_serialized_and_material_change_gated(self):
        text = CANDIDATE_WORKFLOW.read_text()
        self.assertIn("concurrency:", text)
        self.assertIn("cancel-in-progress: true", text)
        self.assertEqual(text.count("resolve-paseo-candidate.py --output"), 1)
        self.assertIn("steps.prepare.outputs.status == 'update'", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("automation/paseo-update-candidate", text)
        self.assertIn("git push --force-with-lease", text)
        self.assertIn("gh pr create", text)

    def test_candidate_workflow_has_only_handoff_write_permissions(self):
        text = CANDIDATE_WORKFLOW.read_text()
        self.assertIn("contents: write", text)
        self.assertIn("pull-requests: write", text)
        for forbidden in (
            "docker/login-action", "docker/build-push-action", "ghcr.io",
            ":accepted", "ssh ", "docker tag", "docker push",
        ):
            self.assertNotIn(forbidden, text)
        for path in WORKFLOWS.glob("*.yml"):
            if path == CANDIDATE_WORKFLOW:
                continue
            self.assertIn("contents: read", path.read_text(), path.name)


class CandidateHandoffTests(unittest.TestCase):
    def write_json(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")

    def test_no_op_creates_no_handoff_directory(self):
        identity = "sha256:" + "1" * 64
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            newest, accepted = root / "new.json", root / "accepted.json"
            self.write_json(newest, candidate(identity))
            self.write_json(accepted, candidate(identity))
            stage = root / "stage"
            result = HANDOFF.prepare(newest, accepted, stage, "abc", "refs/heads/main")
            self.assertEqual(result["status"], "no_op")
            self.assertFalse(stage.exists())

    def test_update_preserves_exact_candidate_and_evidence(self):
        newest_id = "sha256:" + "2" * 64
        accepted_id = "sha256:" + "1" * 64
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            newest = root / "new.json"
            accepted = root / "accepted.json"
            self.write_json(newest, candidate(newest_id))
            self.write_json(accepted, candidate(accepted_id))
            expected_bytes = newest.read_bytes()
            stage = root / "stage"
            result = HANDOFF.prepare(newest, accepted, stage, "sourcecommit", "refs/heads/main")
            self.assertEqual(result["status"], "update")
            self.assertEqual((stage / "candidate.json").read_bytes(), expected_bytes)
            evidence = json.loads((stage / "evidence.json").read_text())
            self.assertEqual(evidence["candidate_id"], newest_id)
            self.assertEqual(evidence["accepted_candidate_id"], accepted_id)
            self.assertEqual(evidence["source_sha"], "sourcecommit")
            self.assertEqual(evidence["source_ref"], "refs/heads/main")
            self.assertRegex(evidence["candidate_file_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_invalid_candidate_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            newest = root / "new.json"
            accepted = root / "accepted.json"
            self.write_json(newest, {"candidate_id": "latest"})
            self.write_json(accepted, candidate("sha256:" + "1" * 64))
            with self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.prepare(newest, accepted, root / "stage", "source", "refs/heads/main")


if __name__ == "__main__":
    unittest.main()
