from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "pi-agent"
AGENTS = (SOURCE / "AGENTS.md").read_text()
RECOVERY = (SOURCE / "skills" / "project-recovery" / "SKILL.md").read_text()
RECOVERY_REF = (
    SOURCE / "skills" / "project-recovery" / "references" / "bootstrap.md"
).read_text()
UNRAID = (SOURCE / "skills" / "unraid-admin" / "SKILL.md").read_text()
UNRAID_REF = (
    SOURCE / "skills" / "unraid-admin" / "references" / "safety-boundary.md"
).read_text()
WRAPPER = (ROOT / "scripts" / "configure-pi-instruction-plane.sh").read_text()
INSTALLER = (ROOT / "scripts" / "pi_instruction_plane.py").read_text()
SMOKE = (ROOT / "scripts" / "verify-pi-instruction-plane.sh").read_text()
DOC = (ROOT / "docs" / "PI_INSTRUCTION_PLANE.md").read_text()


class PiInstructionPlaneContractTests(unittest.TestCase):
    def test_native_pi_agent_directory_and_progressive_skills(self) -> None:
        self.assertLessEqual(len(AGENTS.splitlines()), 40)
        self.assertIn("project-recovery", AGENTS)
        self.assertIn("unraid-admin", AGENTS)
        self.assertIn("~/.pi/agent", DOC)
        self.assertIn("/home/paseo/.pi/agent", DOC)
        self.assertIn("full SKILL.md content only when needed", DOC)
        for skill in (RECOVERY, UNRAID):
            self.assertTrue(skill.startswith("---\nname: "))
            self.assertIn("\ndescription: ", skill)
            self.assertIn("\n---\n", skill)

    def test_project_selection_and_canonical_recovery_are_explicit(self) -> None:
        self.assertIn("Managed project selection is user-driven", AGENTS)
        self.assertIn("Do not infer or bind", AGENTS)
        self.assertIn("before any managed mutation", AGENTS)
        self.assertIn("elmakus/project_workflow_v2", RECOVERY_REF)
        self.assertIn("workflow/ROUTER.md", RECOVERY_REF)
        self.assertIn("current default branch", RECOVERY_REF)
        self.assertIn("Do not reconstruct missing workflow policy", RECOVERY_REF)

    def test_authority_is_referenced_not_reimplemented(self) -> None:
        self.assertIn("Project Workflow owns managed workflow legality", AGENTS)
        self.assertIn("must not duplicate Project Workflow routing semantics", AGENTS)
        self.assertIn("bootstrap locator, not a copy", RECOVERY)
        corpus = "\n".join(path.read_text() for path in SOURCE.rglob("*") if path.is_file())
        for forbidden in (
            "[[cards]]",
            "execution_status =",
            'status = "in_progress"',
            "premium_b_subject =",
            "review_attempts =",
        ):
            self.assertNotIn(forbidden, corpus)

    def test_unraid_skill_is_knowledge_not_capability_claim(self) -> None:
        self.assertIn("does not itself authorize a mutation", AGENTS)
        self.assertIn("read back live capability first", UNRAID)
        self.assertIn(
            "does not claim that M03 host-control transports are already delivered",
            UNRAID_REF,
        )
        self.assertIn("require explicit user approval", UNRAID_REF)

    def test_installer_is_bounded_and_secret_safe(self) -> None:
        self.assertIn('AGENT_REL = Path(".pi/agent")', INSTALLER)
        self.assertIn('STATE_REL = Path(".pi-unraid/instruction-plane")', INSTALLER)
        self.assertIn('choices=("apply", "rollback", "status")', INSTALLER)
        self.assertIn("/instruction-source:ro", WRAPPER)
        self.assertNotIn("auth.json", INSTALLER)
        self.assertNotIn("settings.json", INSTALLER)
        corpus = "\n".join(path.read_text() for path in SOURCE.rglob("*") if path.is_file())
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

    def test_disposable_smoke_covers_rollback_and_recreation(self) -> None:
        self.assertIn("preexisting-local-instructions", SMOKE)
        self.assertIn(" rollback ", SMOKE)
        self.assertIn("pi --mode rpc --no-session", SMOKE)
        self.assertIn("hash_after", SMOKE)
        self.assertIn('"changed"] is False', SMOKE)
        self.assertIn('"byte_stable_after_recreate":true', SMOKE)
        self.assertIn("Pi v0.87.1", DOC)


if __name__ == "__main__":
    unittest.main()
