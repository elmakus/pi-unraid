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


def sanitize_observation(value: Any) -> dict | None:
    if not isinstance(value, dict):
        return None
    safe: dict[str, Any] = {}
    if isinstance(value.get("present"), bool):
        safe["present"] = value["present"]
    if isinstance(value.get("version"), str):
        safe["version"] = value["version"][:256]
    if isinstance(value.get("location"), str):
        safe["location"] = value["location"][:512]
    return safe


def classify(desired: dict, observation: dict | None) -> tuple[str, str]:
    if observation is None:
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

    rendered = []
    known_ids: set[str] = set()
    for capability in sorted(definition["capabilities"], key=lambda item: item["id"]):
        capability_id = capability["id"]
        known_ids.add(capability_id)
        desired = desired_for(capability, candidate, root)
        observed = sanitize_observation(observations.get(capability_id))
        health, drift = classify(desired, observed)
        rendered.append(
            {
                "id": capability_id,
                "approval": capability["approval"],
                "delivery_mode": capability["delivery_mode"],
                "desired": desired,
                "runtime_location": deepcopy(capability["runtime_location"]),
                "probe": deepcopy(capability["probe"]),
                "observed": observed,
                "health": health,
                "drift": drift,
            }
        )

    unexpected = [
        {"id": capability_id, "health": "WARN", "drift": "unexpected"}
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
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    try:
        root = Path(args.root).resolve()
        definition_path = _path_from_arg(root, args.definition)
        definition = load_json(definition_path)
        validate_definition(definition)

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
