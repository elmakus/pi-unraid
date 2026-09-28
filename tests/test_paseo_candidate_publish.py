from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paseo_candidate_publish.py"
WORKFLOW = ROOT / ".github" / "workflows" / "paseo-candidate-build.yml"

spec = importlib.util.spec_from_file_location("paseo_candidate_publish", SCRIPT)
PUBLISH = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(PUBLISH)


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class CandidatePublishTests(unittest.TestCase):
    def fixture(self, root: Path):
        candidate = {"candidate_id": "sha256:" + "a" * 64}
        candidate_raw = (json.dumps(candidate, sort_keys=True) + "\n").encode()
        (root / "candidate.json").write_bytes(candidate_raw)

        handoff = {
            "candidate_id": candidate["candidate_id"],
            "accepted_candidate_id": "sha256:" + "b" * 64,
            "source_sha": "c" * 40,
            "source_ref": "refs/heads/main",
        }
        handoff_raw = (json.dumps(handoff, sort_keys=True) + "\n").encode()
        (root / "handoff.json").write_bytes(handoff_raw)

        artifact = root / "artifact"
        artifact.mkdir()
        image_id = "sha256:" + "d" * 64
        record = {
            "candidate": {"candidate_id": candidate["candidate_id"]},
            "tag": "pi-unraid:paseo-test",
            "image": {"id": image_id},
        }
        record_raw = (json.dumps(record, sort_keys=True) + "\n").encode()
        (artifact / "build-record.json").write_bytes(record_raw)
        archive_raw = b"preserved-tested-image"
        (artifact / "image.tar").write_bytes(archive_raw)
        source_head = "e" * 40
        tested = {
            "schema_version": 1,
            "status": "tested_image_preserved",
            "candidate_id": candidate["candidate_id"],
            "accepted_candidate_id": handoff["accepted_candidate_id"],
            "candidate_file_sha256": digest(candidate_raw),
            "handoff_evidence_sha256": digest(handoff_raw),
            "build_record_sha256": digest(record_raw),
            "image_id": image_id,
            "image_archive_sha256": digest(archive_raw),
            "source_head": source_head,
            "discovery_source_sha": handoff["source_sha"],
            "discovery_source_ref": handoff["source_ref"],
        }
        tested_raw = (json.dumps(tested, sort_keys=True) + "\n").encode()
        (artifact / "tested-image-evidence.json").write_bytes(tested_raw)
        return candidate, handoff, artifact, image_id, source_head


    def test_publish_reuses_exact_archive_and_reads_back_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidate, _, artifact, image_id, source_head = self.fixture(root)
            registry_digest = "sha256:" + "f" * 64
            outputs = [
                "",
                image_id + "\n",
                "",
                "",
                f"Name: test\nDigest: {registry_digest}\n",
                f"Name: immutable\nDigest: {registry_digest}\n",
            ]

            def fake_run(argv):
                return mock.Mock(returncode=0, stdout=outputs.pop(0), stderr="")

            output = root / "publication.json"
            with mock.patch.object(PUBLISH, "run_checked", side_effect=fake_run) as runner:
                result = PUBLISH.publish(
                    artifact_dir=artifact,
                    candidate_path=root / "candidate.json",
                    handoff_path=root / "handoff.json",
                    source_head=source_head,
                    repository="ghcr.io/elmakus/pi-unraid",
                    output_path=output,
                )

            self.assertEqual(result["candidate_id"], candidate["candidate_id"])
            self.assertEqual(result["image_id"], image_id)
            self.assertEqual(result["digest"], registry_digest)
            self.assertEqual(result["immutable_ref"], f"ghcr.io/elmakus/pi-unraid@{registry_digest}")
            self.assertIn(":candidate-" + "a" * 64, result["candidate_ref"])
            calls = [call.args[0] for call in runner.call_args_list]
            self.assertEqual(sum(cmd[:3] == ["docker", "image", "load"] for cmd in calls), 1)
            self.assertEqual(sum(cmd[:3] == ["docker", "image", "push"] for cmd in calls), 1)
            self.assertEqual(sum(cmd[:3] == ["docker", "buildx", "imagetools"] for cmd in calls), 2)
            self.assertTrue(output.is_file())


    def test_archive_hash_mismatch_fails_before_docker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, artifact, _, source_head = self.fixture(root)
            (artifact / "image.tar").write_bytes(b"tampered")
            with mock.patch.object(PUBLISH, "run_checked") as runner:
                with self.assertRaises(PUBLISH.CandidatePublishError):
                    PUBLISH.publish(
                        artifact_dir=artifact,
                        candidate_path=root / "candidate.json",
                        handoff_path=root / "handoff.json",
                        source_head=source_head,
                        repository="ghcr.io/elmakus/pi-unraid",
                        output_path=root / "publication.json",
                    )
            runner.assert_not_called()


    def test_source_head_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, artifact, _, _ = self.fixture(root)
            with self.assertRaises(PUBLISH.CandidatePublishError):
                PUBLISH.verify_inputs(
                    artifact_dir=artifact,
                    candidate_path=root / "candidate.json",
                    handoff_path=root / "handoff.json",
                    source_head="1" * 40,
                )


class CandidatePublishWorkflowTests(unittest.TestCase):
    def test_workflow_publishes_only_preserved_artifact_with_bounded_permissions(self):
        text = WORKFLOW.read_text()
        self.assertEqual(text.count("paseo_buildx.py build"), 1)
        self.assertIn("publish:", text)
        self.assertIn("needs: build", text)
        self.assertIn("packages: write", text)
        self.assertIn("actions/download-artifact@v4", text)
        self.assertIn("paseo_candidate_publish.py publish", text)
        self.assertIn("docker login ghcr.io", text)
        self.assertIn("secrets.GITHUB_TOKEN", text)
        self.assertIn("publication-evidence.json", text)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", text)
        self.assertNotIn(":accepted", text)
        self.assertNotIn("ssh ", text)
        publish_text = text.split("\n  publish:\n", 1)[1]
        self.assertNotIn("paseo_buildx.py build", publish_text)
        self.assertNotIn("docker build", publish_text)
        self.assertNotIn("resolve-paseo-candidate.py", publish_text)


if __name__ == "__main__":
    unittest.main()
