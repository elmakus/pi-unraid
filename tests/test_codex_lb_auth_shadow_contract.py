from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/reconcile-codex-lb-auth-shadow.py"


class CodexLbAuthShadowContractTests(unittest.TestCase):
    def run_tool(self, action: str, auth: Path, state: Path, *, ok: bool = True):
        proc = subprocess.run(
            ["python3", str(SCRIPT), action, str(auth), str(state)],
            text=True,
            capture_output=True,
        )
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(proc.stdout)
        self.assertNotEqual(proc.returncode, 0)
        return proc

    def test_migrate_removes_only_shadow_and_rolls_back_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            state = root / "state"
            raw = (
                '{\n  "keep": {"type": "api_key", "key": "other-secret"},\n'
                '  "codex-lb": {"type": "api_key", "key": "stale-secret"}\n}\n'
            ).encode()
            auth.write_bytes(raw)
            auth.chmod(0o600)

            migrated = self.run_tool("migrate", auth, state)
            self.assertTrue(migrated["changed"])
            self.assertTrue(migrated["shadow_removed"])
            doc = json.loads(auth.read_text())
            self.assertNotIn("codex-lb", doc)
            self.assertEqual(doc["keep"]["key"], "other-secret")
            self.assertNotIn("stale-secret", json.dumps(migrated))

            status = self.run_tool("status", auth, state)
            self.assertFalse(status["shadow_present"])
            self.assertTrue(status["rollback_available"])

            rolled = self.run_tool("rollback", auth, state)
            self.assertTrue(rolled["restored_prior_state"])
            self.assertEqual(auth.read_bytes(), raw)
            self.assertFalse(state.exists())

    def test_absent_shadow_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            state = root / "state"
            auth.write_text(json.dumps({"keep": {"type": "api_key", "key": "x"}}))
            result = self.run_tool("migrate", auth, state)
            self.assertFalse(result["changed"])
            self.assertFalse(state.exists())

    def test_missing_auth_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_tool("migrate", root / "auth.json", root / "state")
            self.assertFalse(result["changed"])
            self.assertFalse(result["auth_present"])

    def test_invalid_shadow_fails_closed_without_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            state = root / "state"
            raw = b'{"codex-lb":{"type":"oauth","key":"do-not-touch"}}\n'
            auth.write_bytes(raw)
            proc = self.run_tool("migrate", auth, state, ok=False)
            self.assertIn("not an api_key", proc.stderr)
            self.assertEqual(auth.read_bytes(), raw)
            self.assertFalse(state.exists())

    def test_rollback_refuses_post_migration_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "auth.json"
            state = root / "state"
            auth.write_text('{"codex-lb":{"type":"api_key","key":"stale"}}\n')
            self.run_tool("migrate", auth, state)
            auth.write_text('{"unexpected":true}\n')
            proc = self.run_tool("rollback", auth, state, ok=False)
            self.assertIn("changed after migration", proc.stderr)
            self.assertTrue(state.exists())


if __name__ == "__main__":
    unittest.main()
