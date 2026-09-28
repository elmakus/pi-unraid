import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "managed_component_lifecycle.py"
spec = importlib.util.spec_from_file_location("managed_component_lifecycle", SCRIPT)
lifecycle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(lifecycle)
BASE = json.loads((ROOT / "config" / "environment-capabilities.json").read_text())


class ManagedComponentLifecycleTests(unittest.TestCase):
    def _spec(self, component_id: str, managed_class: str) -> dict:
        common = {
            "id": component_id,
            "class": managed_class,
            "desired": {"kind": "candidate_component", "component": component_id},
            "runtime_location": {"kind": "command", "value": component_id},
            "probe": {"kind": "command_version", "argv": [component_id, "--version"]},
            "installation_locator": f"test:{component_id}",
        }
        if managed_class == "developer_tool":
            common.update({
                "installation_class": "pinned_binary",
                "source_kind": "github_release",
            })
        elif managed_class == "derived_component":
            common.update({
                "installation_class": "child_image_package_graph",
                "derived_owner": "paseo",
            })
        return common

    def test_add_remove_round_trip_for_supported_classes(self) -> None:
        for managed_class in ("pi_extension", "developer_tool", "derived_component"):
            with self.subTest(managed_class=managed_class):
                component_id = f"test_{managed_class}"
                added = lifecycle.add_component(
                    BASE,
                    self._spec(component_id, managed_class),
                )
                self.assertIn(component_id, {x["id"] for x in added["capabilities"]})
                removed = lifecycle.remove_component(added, component_id)
                self.assertEqual(removed, BASE)

    def test_rejects_unsupported_duplicate_and_missing_owner(self) -> None:
        bad = self._spec("bad", "pi_extension")
        bad["class"] = "apt_package"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, bad)

        duplicate = self._spec("specpi", "pi_extension")
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, duplicate)

        missing_owner = self._spec("derived_bad", "derived_component")
        missing_owner["derived_owner"] = "not-present"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, missing_owner)

    def test_rejects_unsupported_or_contradictory_metadata(self) -> None:
        extension_with_unsupported_source = self._spec(
            "bad_extension_metadata",
            "pi_extension",
        )
        extension_with_unsupported_source["source_kind"] = "pip"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, extension_with_unsupported_source)

        unexpected_field = self._spec("bad_extra_metadata", "derived_component")
        unexpected_field["source_kind"] = "derived"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, unexpected_field)

        unsupported_developer_source = self._spec(
            "bad_developer_source",
            "developer_tool",
        )
        unsupported_developer_source["source_kind"] = "oci"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, unsupported_developer_source)

        contradictory_developer_metadata = self._spec(
            "bad_developer_pair",
            "developer_tool",
        )
        contradictory_developer_metadata["source_kind"] = "npm"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, contradictory_developer_metadata)

    def test_invalid_metadata_does_not_replace_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.json"
            path.write_text(json.dumps(BASE, indent=2) + "\n")
            before = path.read_bytes()
            bad = self._spec("bad_persisted_metadata", "pi_extension")
            bad["installation_class"] = "apt_package"

            with self.assertRaises(lifecycle.LifecycleError):
                lifecycle.apply(path, "add", spec=bad)

            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(
                path.with_name(path.name + ".managed-component.tmp").exists()
            )

    def test_rejects_credential_bearing_spec(self) -> None:
        bad = self._spec("bad_secret", "pi_extension")
        bad["secret"] = "do-not-store"
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.add_component(BASE, bad)

    def test_remove_rejects_owner_with_dependents(self) -> None:
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.remove_component(BASE, "playwright")

    def test_dry_run_is_deterministic_and_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.json"
            path.write_text(json.dumps(BASE, indent=2) + "\n")
            before = path.read_bytes()
            first = lifecycle.apply(
                path,
                "add",
                spec=self._spec("dryrun_tool", "developer_tool"),
                dry_run=True,
            )
            second = lifecycle.apply(
                path,
                "add",
                spec=self._spec("dryrun_tool", "developer_tool"),
                dry_run=True,
            )
            self.assertEqual(first, second)
            self.assertEqual(path.read_bytes(), before)

    def test_failed_replace_leaves_original_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.json"
            path.write_text(json.dumps(BASE, indent=2) + "\n")
            before = path.read_bytes()
            updated = lifecycle.add_component(
                BASE,
                self._spec("atomic_tool", "developer_tool"),
            )
            with mock.patch.object(
                lifecycle.os,
                "replace",
                side_effect=OSError("injected replace failure"),
            ):
                with self.assertRaises(OSError):
                    lifecycle._atomic_write(path, updated)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(
                path.with_name(path.name + ".managed-component.tmp").exists()
            )

    def test_existing_registry_intent_classes_are_valid(self) -> None:
        lifecycle.inventory.validate_definition(BASE)
        snapshot = lifecycle.snapshot(BASE)
        by_id = {item["id"]: item for item in snapshot["components"]}
        self.assertEqual(
            by_id["specpi"]["installation_intent"]["class"],
            "pi_extension",
        )
        self.assertEqual(
            by_id["github_cli"]["installation_intent"]["class"],
            "developer_tool",
        )
        self.assertEqual(
            by_id["chromium"]["installation_intent"]["class"],
            "derived_component",
        )


if __name__ == "__main__":
    unittest.main()
