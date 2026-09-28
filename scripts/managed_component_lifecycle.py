#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import environment_capability_inventory as inventory

DEFAULT_DEFINITION = ROOT / "config/environment-capabilities.json"
SUPPORTED_CLASSES = {"pi_extension", "developer_tool", "derived_component"}
MANAGED_INSTALLATION_READBACK_AUTHORITY = "managed_installation_readback_only"
MANAGED_INSTALLATION_CONSISTENCY_AUTHORITY = "managed_installation_registry_consistency"
SOURCE_IDENTITIES = {
    "npm": "npm_integrity",
    "github_release": "release_asset_digest",
    "github_tag": "git_commit",
    "oci": "oci_digest",
    "repository_tree": "repo_tree_sha256",
}
DEVELOPER_INSTALL_SOURCES = {
    "npm_global": {"npm"},
    "pinned_binary": {"github_release", "github_tag"},
    "pinned_cli_plugin": {"github_release", "github_tag"},
}
DERIVED_INSTALL_CLASSES = {
    "upstream_parent_image",
    "playwright_managed_browser",
    "child_image_package_graph",
}
COMMON_SPEC_KEYS = {
    "id",
    "class",
    "desired",
    "runtime_location",
    "probe",
    "installation_locator",
}
CLASS_SPEC_KEYS = {
    "pi_extension": set(),
    "developer_tool": {"installation_class", "source_kind"},
    "derived_component": {"installation_class", "derived_owner"},
}
FORBIDDEN_SPEC_KEYS = {
    "password",
    "authorization",
    "access_token",
    "private_key",
    "secret",
    "token",
}


class LifecycleError(RuntimeError):
    pass


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).lower()
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"invalid managed inventory: {path}") from exc
    inventory.validate_definition(value)
    return value


def _validate_common_spec(spec: dict) -> tuple[str, str]:
    if not isinstance(spec, dict):
        raise LifecycleError("add spec must be an object")
    bad_keys = sorted(set(_walk_keys(spec)) & FORBIDDEN_SPEC_KEYS)
    if bad_keys:
        raise LifecycleError("credential-bearing fields are forbidden")
    component_id = spec.get("id")
    managed_class = spec.get("class")
    if not isinstance(component_id, str) or not component_id:
        raise LifecycleError("component id must be non-empty")
    if managed_class not in SUPPORTED_CLASSES:
        raise LifecycleError("unsupported managed component class")

    allowed_keys = COMMON_SPEC_KEYS | CLASS_SPEC_KEYS[managed_class]
    unexpected_keys = sorted(set(spec) - allowed_keys)
    if unexpected_keys:
        raise LifecycleError(
            "unsupported metadata fields for "
            + managed_class
            + ": "
            + ",".join(unexpected_keys)
        )

    for key in ("desired", "runtime_location", "probe", "installation_locator"):
        if key not in spec:
            raise LifecycleError(f"missing add spec field: {key}")
    if not isinstance(spec["installation_locator"], str) or not spec["installation_locator"]:
        raise LifecycleError("installation_locator must be non-empty")
    return component_id, managed_class


def _managed_metadata(
    spec: dict,
    managed_class: str,
    existing_ids: set[str],
) -> tuple[str, dict]:
    owner = None
    if managed_class == "pi_extension":
        install_class = "pi_global_extension"
        source_kind = "npm"
        identity_kind = "npm_integrity"
        update_class = "independent"
        channel = "latest-stable"
    elif managed_class == "developer_tool":
        install_class = spec.get("installation_class")
        source_kind = spec.get("source_kind")
        if install_class not in DEVELOPER_INSTALL_SOURCES:
            raise LifecycleError("unsupported developer tool installation class")
        if source_kind not in DEVELOPER_INSTALL_SOURCES[install_class]:
            raise LifecycleError(
                "unsupported developer tool source/install metadata combination"
            )
        identity_kind = SOURCE_IDENTITIES[source_kind]
        update_class = "independent"
        channel = "latest-stable"
    else:
        install_class = spec.get("installation_class")
        owner = spec.get("derived_owner")
        if install_class not in DERIVED_INSTALL_CLASSES:
            raise LifecycleError("unsupported derived component installation class")
        if not isinstance(owner, str) or owner not in existing_ids:
            raise LifecycleError("derived component owner is missing")
        source_kind = "derived"
        identity_kind = "owner_immutable_identity"
        update_class = "derived"
        channel = "derived-from-owner"
    return install_class, {
        "membership": "managed",
        "source": {"kind": source_kind},
        "stable_channel": channel,
        "immutable_identity": {"kind": identity_kind},
        "install_class": install_class,
        "update_class": update_class,
        "derived_owner": owner,
        "probe_ref": "probe",
        "installation_intent": {
            "class": managed_class,
            "locator": spec["installation_locator"],
        },
    }


def add_component(definition: dict, spec: dict) -> dict:
    result = deepcopy(definition)
    component_id, managed_class = _validate_common_spec(spec)
    existing_ids = {item["id"] for item in result["capabilities"]}
    if component_id in existing_ids:
        raise LifecycleError(f"managed component already exists: {component_id}")
    install_class, managed = _managed_metadata(spec, managed_class, existing_ids)
    capability = {
        "id": component_id,
        "approval": "accepted",
        "delivery_mode": install_class,
        "desired": deepcopy(spec["desired"]),
        "runtime_location": deepcopy(spec["runtime_location"]),
        "probe": deepcopy(spec["probe"]),
        "managed_update": managed,
    }
    result["capabilities"].append(capability)
    inventory.validate_definition(result)
    return result


def remove_component(definition: dict, component_id: str) -> dict:
    result = deepcopy(definition)
    matches = [item for item in result["capabilities"] if item["id"] == component_id]
    if len(matches) != 1:
        raise LifecycleError(f"managed component not found: {component_id}")
    intent_class = matches[0]["managed_update"]["installation_intent"]["class"]
    if intent_class not in SUPPORTED_CLASSES:
        raise LifecycleError(
            f"component class is not removable by managed helper: {intent_class}"
        )
    dependents = [
        item["id"]
        for item in result["capabilities"]
        if item["managed_update"].get("derived_owner") == component_id
    ]
    if dependents:
        raise LifecycleError(
            "managed component still owns derived components: "
            + ",".join(sorted(dependents))
        )
    result["capabilities"] = [
        item for item in result["capabilities"] if item["id"] != component_id
    ]
    inventory.validate_definition(result)
    return result


def _atomic_write(path: Path, payload: dict) -> None:
    inventory.validate_definition(payload)
    tmp = path.with_name(path.name + ".managed-component.tmp")
    try:
        with tmp.open("w") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def snapshot(definition: dict) -> dict:
    return inventory.managed_registry_snapshot(definition)


def _component_id_set(value, label: str) -> set[str]:
    if not isinstance(value, list):
        raise LifecycleError(f"{label} must be a list")
    if not all(isinstance(item, str) and item for item in value):
        raise LifecycleError(f"{label} must contain non-empty component ids")
    if len(value) != len(set(value)):
        raise LifecycleError(f"{label} must not contain duplicate component ids")
    return set(value)


def validate_installation_readback(definition: dict, readback: dict) -> dict:
    inventory.validate_definition(definition)
    if not isinstance(readback, dict):
        raise LifecycleError("managed installation readback must be an object")
    if set(readback) != {
        "schema_version",
        "authority",
        "installed_component_ids",
        "temporary_component_ids",
    }:
        raise LifecycleError("managed installation readback contains unexpected fields")
    if readback.get("schema_version") != 1:
        raise LifecycleError("unsupported managed installation readback schema")
    if readback.get("authority") != MANAGED_INSTALLATION_READBACK_AUTHORITY:
        raise LifecycleError("managed installation readback authority is invalid")

    installed = _component_id_set(
        readback.get("installed_component_ids"),
        "installed_component_ids",
    )
    temporary = _component_id_set(
        readback.get("temporary_component_ids"),
        "temporary_component_ids",
    )
    overlap = sorted(installed & temporary)
    if overlap:
        raise LifecycleError(
            "component ids cannot be both managed-installed and temporary"
        )

    registered = {
        item["id"]
        for item in definition["capabilities"]
        if item["managed_update"]["membership"] == "managed"
        and isinstance(item["managed_update"].get("installation_intent"), dict)
    }
    missing_registered = sorted(registered - installed)
    installed_unregistered = sorted(installed - registered)

    output = {
        "schema_version": 1,
        "authority": MANAGED_INSTALLATION_CONSISTENCY_AUTHORITY,
        "registry_authority": inventory.MANAGED_REGISTRY_AUTHORITY,
        "state": "RED" if missing_registered or installed_unregistered else "GREEN",
        "registered_count": len(registered),
        "installed_managed_count": len(installed),
        "temporary_count": len(temporary),
        "missing_registered": missing_registered,
        "installed_unregistered": [
            inventory._observation_fingerprint(component_id)
            for component_id in installed_unregistered
        ],
        "temporary_installations": [
            inventory._observation_fingerprint(component_id)
            for component_id in sorted(temporary)
        ],
        "temporary_policy": "report_only_not_adopted",
    }
    return output


def apply(
    path: Path,
    action: str,
    *,
    spec: dict | None = None,
    component_id: str | None = None,
    dry_run: bool = False,
) -> dict:
    definition = _load(path)
    if action == "add":
        if spec is None:
            raise LifecycleError("add requires spec")
        updated = add_component(definition, spec)
    elif action == "remove":
        if not component_id:
            raise LifecycleError("remove requires id")
        updated = remove_component(definition, component_id)
    else:
        raise LifecycleError("unsupported lifecycle action")
    if not dry_run:
        _atomic_write(path, updated)
    return snapshot(updated)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--definition", default=str(DEFAULT_DEFINITION))
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    add = sub.add_parser("add")
    add.add_argument("--spec", required=True)
    add.add_argument("--dry-run", action="store_true")
    remove = sub.add_parser("remove")
    remove.add_argument("--id", required=True)
    remove.add_argument("--dry-run", action="store_true")
    readback = sub.add_parser("validate-readback")
    readback.add_argument("--readback", required=True)
    args = parser.parse_args()
    path = Path(args.definition)
    try:
        if args.action == "list":
            output = snapshot(_load(path))
        elif args.action == "add":
            spec = json.loads(Path(args.spec).read_text())
            output = apply(path, "add", spec=spec, dry_run=args.dry_run)
        elif args.action == "remove":
            output = apply(path, "remove", component_id=args.id, dry_run=args.dry_run)
        else:
            readback = json.loads(Path(args.readback).read_text())
            output = validate_installation_readback(_load(path), readback)
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 1 if output.get("state") == "RED" else 0
    except (LifecycleError, inventory.InventoryError, OSError, json.JSONDecodeError) as exc:
        print(f"managed-component lifecycle error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
