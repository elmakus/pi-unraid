from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECONCILER_PATH = ROOT / "scripts" / "reconcile-codex-lb-provider-config.py"
EXTENSION = ROOT / "config" / "pi-agent" / "extensions" / "codex-lb-dynamic-model-catalog.ts"
CORE = ROOT / "config" / "pi-agent" / "extensions" / "lib" / "codex-lb-dynamic-model-catalog-core.mjs"
NODE_TEST = ROOT / "tests" / "codex_lb_dynamic_model_catalog_core_test.mjs"

spec = importlib.util.spec_from_file_location("codex_lb_provider_config", RECONCILER_PATH)
assert spec and spec.loader
reconciler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconciler)


def provider_doc() -> dict:
    return {
        "customMarker": "preserve-me",
        "providers": {
            "keep-me": {
                "api": "openai-completions",
                "apiKey": "dummy-placeholder",
                "baseUrl": "http://example.invalid/v1",
                "models": [{"id": "preserve-model"}],
            },
            "codex-lb": {
                "baseUrl": "http://host.docker.internal:2455/v1",
                "api": "openai-responses",
                "apiKey": "${CODEX_LB_API_KEY}",
                "models": [{"id": "seed-model"}],
            },
        },
    }


class CodexLbDynamicModelCatalogContractTests(unittest.TestCase):
    def test_node_core_contract(self) -> None:
        completed = subprocess.run(
            ["node", str(NODE_TEST)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("core tests: GREEN", completed.stdout)

    def test_reconciler_preserves_unrelated_config_and_exact_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models.json"
            state = root / "state"
            original = (json.dumps(provider_doc(), indent=2) + "\n").encode()
            models.write_bytes(original)
            os.chmod(models, 0o600)

            result = reconciler.migrate(models, state)
            self.assertTrue(result["changed"])
            migrated = json.loads(models.read_text())
            self.assertEqual(migrated["customMarker"], "preserve-me")
            self.assertEqual(
                migrated["providers"]["keep-me"],
                provider_doc()["providers"]["keep-me"],
            )
            self.assertNotIn("models", migrated["providers"]["codex-lb"])
            self.assertEqual(
                migrated["providers"]["codex-lb"]["baseUrl"],
                "http://host.docker.internal:2455/v1",
            )
            self.assertEqual(migrated["providers"]["codex-lb"]["api"], "openai-responses")
            self.assertEqual(migrated["providers"]["codex-lb"]["apiKey"], "${CODEX_LB_API_KEY}")
            self.assertEqual(models.stat().st_mode & 0o777, 0o600)
            self.assertEqual((state / "models.json.before").stat().st_mode & 0o777, 0o600)

            second = reconciler.migrate(models, state)
            self.assertFalse(second["changed"])
            restored = reconciler.rollback(models, state)
            self.assertTrue(restored["restored_prior_state"])
            self.assertEqual(models.read_bytes(), original)
            self.assertEqual(models.stat().st_mode & 0o777, 0o600)
            self.assertFalse(state.exists())

    def test_reconciler_fails_closed_on_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models.json"
            state = root / "state"
            doc = provider_doc()
            doc["providers"]["codex-lb"]["api"] = "openai-completions"
            original = (json.dumps(doc, indent=2) + "\n").encode()
            models.write_bytes(original)

            with self.assertRaises(reconciler.ReconcileError):
                reconciler.migrate(models, state)
            self.assertEqual(models.read_bytes(), original)
            self.assertFalse(state.exists())

    def test_reconciler_fails_closed_on_invalid_base_url(self) -> None:
        for base_url in (
            "ftp://host.invalid/v1",
            "not-a-url/v1",
            "http://user:pass@host.invalid/v1",
            "http://host.invalid:abc/v1",
            "http://host.invalid:99999/v1",
            "http://:123/v1",
        ):
            with self.subTest(base_url=base_url), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                models = root / "models.json"
                state = root / "state"
                doc = provider_doc()
                doc["providers"]["codex-lb"]["baseUrl"] = base_url
                original = (json.dumps(doc, indent=2) + "\n").encode()
                models.write_bytes(original)

                with self.assertRaises(reconciler.ReconcileError):
                    reconciler.migrate(models, state)
                self.assertEqual(models.read_bytes(), original)
                self.assertFalse(state.exists())

    def test_reconciler_rejects_control_character_model_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models.json"
            state = root / "state"
            doc = provider_doc()
            doc["providers"]["codex-lb"]["models"] = [{"id": "bad\u0000id"}]
            original = (json.dumps(doc, indent=2) + "\n").encode()
            models.write_bytes(original)

            with self.assertRaises(reconciler.ReconcileError):
                reconciler.migrate(models, state)
            self.assertEqual(models.read_bytes(), original)
            self.assertFalse(state.exists())

    def test_rollback_refuses_post_migration_user_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models.json"
            state = root / "state"
            models.write_text(json.dumps(provider_doc()) + "\n")
            reconciler.migrate(models, state)
            changed = json.loads(models.read_text())
            changed["afterMigration"] = True
            models.write_text(json.dumps(changed) + "\n")

            with self.assertRaises(reconciler.ReconcileError):
                reconciler.rollback(models, state)
            self.assertTrue(state.exists())
            self.assertTrue(json.loads(models.read_text())["afterMigration"])

    def test_extension_uses_supported_refresh_lifecycle_without_model_switch(self) -> None:
        extension = EXTENSION.read_text()
        core = CORE.read_text()
        self.assertIn('pi.registerProvider(PROVIDER_ID', extension)
        self.assertIn('pi.on("session_start"', extension)
        self.assertIn('pi.on("session_shutdown"', extension)
        self.assertIn("ctx.modelRegistry.refresh({", core)
        self.assertIn("providers: [providerId]", core)
        self.assertNotIn("setModel", extension + core)
        for hardcoded in (
            "gpt-6-astra",
            "gpt-6-sol",
            "gpt-6-luna",
            "gpt-reserve",
            "gpt-5.6-sol",
            "gpt-5.6-terra",
            "gpt-5.6-luna",
            "gpt-5.5",
            "codex-auto-review",
        ):
            self.assertNotIn(hardcoded, extension + core)


if __name__ == "__main__":
    unittest.main()