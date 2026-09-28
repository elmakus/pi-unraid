#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEFINITION = ROOT / "config" / "environment-capabilities.json"

FORBIDDEN_DEFINITION_KEYS = {
    "role_ceiling",
    "role_ceilings",
    "action_classification",
    "action_classifications",
    "bundle",
    "bundles",
    "role_default_bundle",
    "role_default_bundles",
    "assignment_eligibility",
    "task_grant",
    "task_grants",
    "task_scoped_grant",
    "task_scoped_grants",
    "task_board",
    "workflow_state",
}
SAFE_PROVENANCE_KEYS = {
    "artifact",
    "artifact_identity",
    "delivery",
    "immutable_parent",
    "npm",
    "source",
    "stable_line_source",
}

MANAGED_REGISTRY_AUTHORITY = "managed_update_membership_only"
MANAGED_SOURCE_KINDS = {
    "derived",
    "github_release",
    "github_tag",
    "npm",
    "oci",
    "repository_tree",
}
MANAGED_STABLE_CHANNELS = {"latest-stable", "derived-from-owner", "repository-state"}
MANAGED_INSTALL_CLASSES = {
    "upstream_parent_image",
    "npm_global",
    "playwright_managed_browser",
    "pinned_binary",
    "pinned_cli_plugin",
    "pi_global_extension",
    "child_image_package_graph",
    "repository_managed_home_install",
}
MANAGED_UPDATE_CLASSES = {"core_pair", "independent", "derived", "repository_managed"}
MANAGED_IDENTITY_KINDS = {
    "oci_digest",
    "npm_integrity",
    "release_asset_digest",
    "git_commit",
    "owner_immutable_identity",
    "repo_tree_sha256",
}
MANAGED_UPDATE_KEYS = {
    "membership",
    "source",
    "stable_channel",
    "immutable_identity",
    "install_class",
    "update_class",
    "derived_owner",
    "probe_ref",
    "installation_intent",
}


class InventoryError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"invalid JSON input: {path}") from exc


def nested_get(value: Any, path: list[str]) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise InventoryError("candidate field is missing")
        current = current[key]
    return current


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_definition(definition: dict) -> None:
    if not isinstance(definition, dict):
        raise InventoryError("inventory definition must be an object")
    if definition.get("schema_version") != 1:
        raise InventoryError("unsupported inventory schema")
    if definition.get("authority") != "environment_availability_only":
        raise InventoryError("inventory authority must remain environment availability only")

    registry = definition.get("managed_component_registry")
    if not isinstance(registry, dict):
        raise InventoryError("managed_component_registry metadata is missing")
    if registry.get("schema_version") != 1:
        raise InventoryError("unsupported managed-component registry schema")
    if registry.get("authority") != MANAGED_REGISTRY_AUTHORITY:
        raise InventoryError("managed-component registry authority is invalid")
    if registry.get("membership_field") != "managed_update":
        raise InventoryError("managed-component registry membership field is invalid")
    if set(registry) != {"schema_version", "authority", "membership_field"}:
        raise InventoryError("managed-component registry metadata contains unexpected fields")

    offenders = sorted(set(_walk_keys(definition)) & FORBIDDEN_DEFINITION_KEYS)
    if offenders:
        raise InventoryError(
            "inventory definition contains forbidden OR/PW policy fields: "
            + ", ".join(offenders)
        )

    source = definition.get("candidate_source")
    if not isinstance(source, str) or not source:
        raise InventoryError("candidate_source must be a repository-relative path")

    capabilities = definition.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise InventoryError("capabilities must be a non-empty list")

    seen: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, dict):
            raise InventoryError("capability entries must be objects")
        capability_id = capability.get("id")
        if not isinstance(capability_id, str) or not capability_id:
            raise InventoryError("capability id must be non-empty")
        if capability_id in seen:
            raise InventoryError(f"duplicate capability id: {capability_id}")
        seen.add(capability_id)
        if capability.get("approval") != "accepted":
            raise InventoryError(f"capability is not accepted: {capability_id}")
        if not isinstance(capability.get("delivery_mode"), str):
            raise InventoryError(f"delivery_mode is missing: {capability_id}")
        desired = capability.get("desired")
        if not isinstance(desired, dict) or desired.get("kind") not in {
            "candidate_component",
            "candidate_field",
            "repo_tree",
        }:
            raise InventoryError(f"unsupported desired-state selector: {capability_id}")
        runtime_location = capability.get("runtime_location")
        if (
            not isinstance(runtime_location, dict)
            or not isinstance(runtime_location.get("kind"), str)
            or not isinstance(runtime_location.get("value"), str)
        ):
            raise InventoryError(f"runtime_location is invalid: {capability_id}")
        if not isinstance(capability.get("probe"), dict):
            raise InventoryError(f"probe metadata is missing: {capability_id}")

        managed = capability.get("managed_update")
        if not isinstance(managed, dict) or set(managed) != MANAGED_UPDATE_KEYS:
            raise InventoryError(f"managed_update metadata is invalid: {capability_id}")
        if managed.get("membership") != "managed":
            raise InventoryError(f"capability is not managed for updates: {capability_id}")

        source_meta = managed.get("source")
        if (
            not isinstance(source_meta, dict)
            or set(source_meta) != {"kind"}
            or source_meta.get("kind") not in MANAGED_SOURCE_KINDS
        ):
            raise InventoryError(f"managed source kind is invalid: {capability_id}")

        stable_channel = managed.get("stable_channel")
        if stable_channel not in MANAGED_STABLE_CHANNELS:
            raise InventoryError(f"managed stable channel is invalid: {capability_id}")

        identity_meta = managed.get("immutable_identity")
        if (
            not isinstance(identity_meta, dict)
            or set(identity_meta) != {"kind"}
            or identity_meta.get("kind") not in MANAGED_IDENTITY_KINDS
        ):
            raise InventoryError(f"managed immutable identity is invalid: {capability_id}")

        install_class = managed.get("install_class")
        if install_class not in MANAGED_INSTALL_CLASSES:
            raise InventoryError(f"managed install class is invalid: {capability_id}")
        if install_class != capability["delivery_mode"]:
            raise InventoryError(f"managed install class disagrees with delivery_mode: {capability_id}")

        update_class = managed.get("update_class")
        if update_class not in MANAGED_UPDATE_CLASSES:
            raise InventoryError(f"managed update class is invalid: {capability_id}")
        if managed.get("probe_ref") != "probe":
            raise InventoryError(f"managed probe reference is invalid: {capability_id}")

        intent = managed.get("installation_intent")
        if (not isinstance(intent, dict) or set(intent) != {"class", "locator"} or intent.get("class") not in {"core_component", "pi_extension", "developer_tool", "derived_component", "repository_managed"} or not isinstance(intent.get("locator"), str) or not intent["locator"]):
            raise InventoryError(f"managed installation intent is invalid: {capability_id}")
        intent_class = intent["class"]
        if intent_class == "derived_component" and managed.get("update_class") != "derived":
            raise InventoryError(f"derived installation intent disagrees with update class: {capability_id}")
        if intent_class == "pi_extension" and (
            managed.get("install_class") != "pi_global_extension"
            or managed.get("source", {}).get("kind") != "npm"
            or managed.get("update_class") != "independent"
        ):
            raise InventoryError(f"Pi extension installation intent is inconsistent: {capability_id}")
        if intent_class == "developer_tool" and (
            managed.get("update_class") != "independent"
            or managed.get("source", {}).get("kind") == "derived"
        ):
            raise InventoryError(f"developer-tool installation intent is inconsistent: {capability_id}")
        if intent_class == "core_component" and managed.get("update_class") != "core_pair":
            raise InventoryError(f"core installation intent disagrees with update class: {capability_id}")
        if intent_class == "repository_managed" and managed.get("update_class") != "repository_managed":
            raise InventoryError(f"repository installation intent disagrees with update class: {capability_id}")

        owner = managed.get("derived_owner")
        if update_class == "derived":
            if not isinstance(owner, str) or not owner:
                raise InventoryError(f"derived managed capability lacks owner: {capability_id}")
            if source_meta["kind"] != "derived":
                raise InventoryError(f"derived managed capability must use derived source: {capability_id}")
            if stable_channel != "derived-from-owner":
                raise InventoryError(f"derived managed capability has invalid channel: {capability_id}")
            if identity_meta["kind"] != "owner_immutable_identity":
                raise InventoryError(f"derived managed capability has invalid identity: {capability_id}")
        else:
            if owner is not None:
                raise InventoryError(f"non-derived managed capability has derived_owner: {capability_id}")
            if source_meta["kind"] == "derived":
                raise InventoryError(f"non-derived managed capability uses derived source: {capability_id}")
            expected_channel = "repository-state" if update_class == "repository_managed" else "latest-stable"
            if stable_channel != expected_channel:
                raise InventoryError(f"managed stable channel does not match update class: {capability_id}")

    by_id = {capability["id"]: capability for capability in capabilities}
    for capability in capabilities:
        capability_id = capability["id"]
        owner = capability["managed_update"]["derived_owner"]
        if owner is not None:
            if owner == capability_id or owner not in by_id:
                raise InventoryError(f"derived managed capability owner is invalid: {capability_id}")


def _resolve_under_root(root: Path, relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise InventoryError("repository path must be relative")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative_path).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise InventoryError("repository path escapes root")
    return resolved


def repo_tree_identity(root: Path, relative_path: str) -> str:
    base = _resolve_under_root(root, relative_path)
    if not base.exists():
        raise InventoryError(f"repository path does not exist: {relative_path}")

    digest = hashlib.sha256()
    if base.is_symlink():
        raise InventoryError(f"repository path must not be a symlink: {relative_path}")

    if base.is_file():
        entries = [base]
    else:
        entries = []
        for entry in sorted(base.rglob("*")):
            if entry.is_symlink():
                raise InventoryError(f"repository tree contains a symlink: {relative_path}")
            if entry.is_file():
                entries.append(entry)

    for entry in entries:
        rel = entry.relative_to(root.resolve()).as_posix()
        digest.update(b"file\0")
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(entry.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _bounded_component_provenance(component: dict) -> dict:
    return {
        key: deepcopy(component[key])
        for key in sorted(SAFE_PROVENANCE_KEYS)
        if key in component
    }


def candidate_component(candidate: dict, component_id: str) -> tuple[str, dict]:
    components = candidate.get("components")
    if not isinstance(components, dict):
        raise InventoryError("candidate components are missing")
    component = components.get(component_id)
    if not isinstance(component, dict):
        raise InventoryError(f"candidate component is missing: {component_id}")
    version = component.get("version")
    if not isinstance(version, str) or not version:
        raise InventoryError(f"candidate component has no version: {component_id}")
    provenance = {
        "candidate_id": candidate.get("candidate_id"),
        "component": component_id,
        **_bounded_component_provenance(component),
    }
    return version, provenance


def desired_for(capability: dict, candidate: dict, root: Path) -> dict:
    selector = capability["desired"]
    kind = selector["kind"]

    if kind == "candidate_component":
        component_id = selector.get("component")
        if not isinstance(component_id, str) or not component_id:
            raise InventoryError("candidate component selector is invalid")
        version, provenance = candidate_component(candidate, component_id)
        return {"version": version, "provenance": provenance}

    if kind == "candidate_field":
        path = selector.get("path")
        if not isinstance(path, list) or not path or not all(isinstance(x, str) for x in path):
            raise InventoryError("candidate field path is invalid")
        value = nested_get(candidate, path)
        if not isinstance(value, str) or not value:
            raise InventoryError("candidate field must resolve to a non-empty string")
        desired = {
            "version": value,
            "provenance": {
                "candidate_id": candidate.get("candidate_id"),
                "candidate_path": path,
            },
        }
        provenance_component = selector.get("provenance_component")
        if provenance_component is not None:
            if not isinstance(provenance_component, str):
                raise InventoryError("provenance_component must be a string")
            _, component_provenance = candidate_component(candidate, provenance_component)
            desired["provenance"]["component"] = component_provenance
        members_path = selector.get("members_path")
        if members_path is not None:
            if (
                not isinstance(members_path, list)
                or not members_path
                or not all(isinstance(x, str) for x in members_path)
            ):
                raise InventoryError("members_path is invalid")
            members = nested_get(candidate, members_path)
            if not isinstance(members, list) or not all(isinstance(x, str) for x in members):
                raise InventoryError("members_path must resolve to a string list")
            desired["members"] = list(members)
        return desired

    if kind == "repo_tree":
        relative_path = selector.get("path")
        if not isinstance(relative_path, str):
            raise InventoryError("repo_tree path is invalid")
        return {
            "version": repo_tree_identity(root, relative_path),
            "provenance": {"repository_path": relative_path},
        }

    raise InventoryError("unsupported desired-state selector")


def _observation_fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def sanitize_observation(
    value: Any,
    desired: dict,
    runtime_location: dict,
) -> dict | None:
    if not isinstance(value, dict):
        return None

    safe: dict[str, Any] = {}
    if isinstance(value.get("present"), bool):
        safe["present"] = value["present"]

    observed_version = value.get("version")
    if isinstance(observed_version, str):
        if observed_version == desired["version"]:
            safe["version"] = desired["version"]
        else:
            safe["version_fingerprint"] = _observation_fingerprint(observed_version)

    observed_location = value.get("location")
    expected_location = runtime_location.get("value")
    if isinstance(observed_location, str):
        if isinstance(expected_location, str) and observed_location == expected_location:
            safe["location"] = expected_location
        else:
            safe["location_fingerprint"] = _observation_fingerprint(observed_location)

    return safe


def classify(desired: dict, observation: dict | None) -> tuple[str, str]:
    if not isinstance(observation, dict):
        return "WARN", "unobserved"
    if observation.get("present") is False:
        return "RED", "missing"
    if observation.get("present") is not True:
        return "WARN", "presence_unknown"
    observed_version = observation.get("version")
    if not isinstance(observed_version, str):
        return "WARN", "version_unknown"
    if observed_version != desired["version"]:
        return "RED", "version_mismatch"
    return "GREEN", "none"


def managed_registry_snapshot(definition: dict) -> dict:
    validate_definition(definition)
    registry = definition["managed_component_registry"]
    return {
        "schema_version": registry["schema_version"],
        "authority": registry["authority"],
        "components": [
            {
                "id": capability["id"],
                **deepcopy(capability["managed_update"]),
            }
            for capability in sorted(definition["capabilities"], key=lambda item: item["id"])
        ],
    }


def derive_inventory(
    definition: dict,
    candidate: dict,
    root: Path,
    observations: dict | None = None,
) -> dict:
    validate_definition(definition)
    if not isinstance(candidate, dict) or candidate.get("schema_version") != 1:
        raise InventoryError("unsupported candidate schema")
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise InventoryError("candidate identity is missing")

    if observations is None:
        observations = {}
    if not isinstance(observations, dict):
        raise InventoryError("observations must be an object keyed by capability id")
    if not all(isinstance(capability_id, str) for capability_id in observations):
        raise InventoryError("observation capability ids must be strings")

    rendered = []
    known_ids: set[str] = set()
    for capability in sorted(definition["capabilities"], key=lambda item: item["id"]):
        capability_id = capability["id"]
        known_ids.add(capability_id)
        desired = desired_for(capability, candidate, root)
        raw_observation = observations.get(capability_id)
        health, drift = classify(desired, raw_observation)
        observed = sanitize_observation(
            raw_observation,
            desired,
            capability["runtime_location"],
        )
        rendered.append(
            {
                "id": capability_id,
                "approval": capability["approval"],
                "delivery_mode": capability["delivery_mode"],
                "managed_update": deepcopy(capability["managed_update"]),
                "desired": desired,
                "runtime_location": deepcopy(capability["runtime_location"]),
                "probe": deepcopy(capability["probe"]),
                "observed": observed,
                "health": health,
                "drift": drift,
            }
        )

    unexpected = [
        {
            "id_fingerprint": _observation_fingerprint(capability_id),
            "health": "WARN",
            "drift": "unexpected",
        }
        for capability_id in sorted(set(observations) - known_ids)
    ]

    health_values = [item["health"] for item in rendered] + [
        item["health"] for item in unexpected
    ]
    if "RED" in health_values:
        state = "RED"
    elif "WARN" in health_values:
        state = "WARN"
    else:
        state = "GREEN"

    return {
        "schema_version": 1,
        "authority": "environment_availability_only",
        "managed_component_registry": deepcopy(definition["managed_component_registry"]),
        "candidate_id": candidate_id,
        "state": state,
        "capabilities": rendered,
        "unexpected_observations": unexpected,
    }


def _path_from_arg(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else _resolve_under_root(root, value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--definition", default=str(DEFAULT_DEFINITION.relative_to(ROOT)))
    parser.add_argument("--candidate")
    parser.add_argument("--observations")
    parser.add_argument("--managed-registry", action="store_true")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    try:
        root = Path(args.root).resolve()
        definition_path = _path_from_arg(root, args.definition)
        definition = load_json(definition_path)
        validate_definition(definition)

        if args.managed_registry:
            print(json.dumps(managed_registry_snapshot(definition), sort_keys=True, separators=(",", ":")))
            return 0

        candidate_value = args.candidate or definition["candidate_source"]
        candidate = load_json(_path_from_arg(root, candidate_value))
        observations = (
            load_json(_path_from_arg(root, args.observations))
            if args.observations
            else None
        )
        result = derive_inventory(definition, candidate, root, observations)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except InventoryError as exc:
        print(
            json.dumps(
                {"ok": False, "error": "inventory", "message": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())