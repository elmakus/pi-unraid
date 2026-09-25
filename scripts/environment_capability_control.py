#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import environment_capability_inventory as inventory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEFINITION = ROOT / "config" / "environment-capabilities.json"

QUICK_PROBE_KINDS = {
    "command_version",
    "command_set",
    "http_health",
    "managed_tree_identity",
}
RECONCILABLE_DRIFT = {"missing", "version_mismatch"}


class CapabilityControlError(RuntimeError):
    pass


def _state(values: list[str]) -> str:
    if "RED" in values:
        return "RED"
    if "WARN" in values:
        return "WARN"
    return "GREEN"


def _validate_inventory_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise CapabilityControlError("inventory payload must be an object")
    if payload.get("schema_version") != 1:
        raise CapabilityControlError("unsupported inventory payload schema")
    if payload.get("authority") != "environment_availability_only":
        raise CapabilityControlError("inventory authority drift")
    candidate_id = payload.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CapabilityControlError("inventory candidate identity is missing")
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise CapabilityControlError("inventory capabilities are missing")
    seen: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, dict):
            raise CapabilityControlError("inventory capability must be an object")
        capability_id = capability.get("id")
        if not isinstance(capability_id, str) or not capability_id:
            raise CapabilityControlError("inventory capability id is invalid")
        if capability_id in seen:
            raise CapabilityControlError(f"duplicate inventory capability id: {capability_id}")
        seen.add(capability_id)
        if capability.get("approval") != "accepted":
            raise CapabilityControlError(f"capability is not already approved: {capability_id}")
        if capability.get("health") not in {"GREEN", "WARN", "RED"}:
            raise CapabilityControlError(f"invalid capability health: {capability_id}")
        if not isinstance(capability.get("drift"), str):
            raise CapabilityControlError(f"invalid capability drift: {capability_id}")
        desired = capability.get("desired")
        if not isinstance(desired, dict) or not isinstance(desired.get("version"), str):
            raise CapabilityControlError(f"invalid desired state: {capability_id}")
        if not isinstance(capability.get("delivery_mode"), str):
            raise CapabilityControlError(f"invalid delivery mode: {capability_id}")
        runtime_location = capability.get("runtime_location")
        if not isinstance(runtime_location, dict):
            raise CapabilityControlError(f"invalid runtime location: {capability_id}")
        probe = capability.get("probe")
        if not isinstance(probe, dict) or not isinstance(probe.get("kind"), str):
            raise CapabilityControlError(f"invalid probe metadata: {capability_id}")
    unexpected = payload.get("unexpected_observations")
    if not isinstance(unexpected, list):
        raise CapabilityControlError("unexpected observation set is invalid")


def _capability_view(capability: dict) -> dict:
    return {
        "id": capability["id"],
        "delivery_mode": capability["delivery_mode"],
        "desired_version": capability["desired"]["version"],
        "runtime_location": deepcopy(capability["runtime_location"]),
        "probe_kind": capability["probe"]["kind"],
        "observed": deepcopy(capability.get("observed")),
        "health": capability["health"],
        "drift": capability["drift"],
    }


def doctor(payload: dict, *, depth: str) -> dict:
    _validate_inventory_payload(payload)
    if depth not in {"quick", "full"}:
        raise CapabilityControlError("doctor depth must be quick or full")

    selected = []
    deferred = []
    for capability in payload["capabilities"]:
        if depth == "full" or capability["probe"]["kind"] in QUICK_PROBE_KINDS:
            selected.append(capability)
        else:
            deferred.append(capability["id"])

    if not selected:
        raise CapabilityControlError("doctor depth selected no capability checks")

    unexpected = deepcopy(payload["unexpected_observations"])
    values = [item["health"] for item in selected] + [
        item.get("health", "WARN") for item in unexpected
    ]
    state = _state(values)
    counts = {
        level: sum(1 for item in selected if item["health"] == level)
        for level in ("GREEN", "WARN", "RED")
    }
    summary = (
        f"{state}: environment_capabilities depth={depth} "
        f"green={counts['GREEN']} warn={counts['WARN']} red={counts['RED']} "
        f"unexpected={len(unexpected)}"
    )
    return {
        "schema_version": 1,
        "authority": "environment_availability_only",
        "doctor": "environment_capabilities",
        "candidate_id": payload["candidate_id"],
        "depth": depth,
        "state": state,
        "checks": [_capability_view(item) for item in selected],
        "deferred_capabilities": sorted(deferred),
        "unexpected_observations": unexpected,
        "counts": counts,
        "summary": summary,
    }


def _capability_map(payload: dict) -> dict[str, dict]:
    return {item["id"]: item for item in payload["capabilities"]}


def build_reconcile_plan(
    payload: dict,
    *,
    requested_ids: list[str] | None = None,
) -> dict:
    _validate_inventory_payload(payload)
    by_id = _capability_map(payload)

    if requested_ids is None:
        selected_ids = sorted(by_id)
    else:
        if not isinstance(requested_ids, list) or not all(
            isinstance(item, str) and item for item in requested_ids
        ):
            raise CapabilityControlError("requested capability ids must be non-empty strings")
        if len(requested_ids) != len(set(requested_ids)):
            raise CapabilityControlError("requested capability ids must be unique")
        unknown = sorted(set(requested_ids) - set(by_id))
        if unknown:
            raise CapabilityControlError(
                "reconcile cannot target unapproved capability ids: " + ", ".join(unknown)
            )
        selected_ids = sorted(requested_ids)

    actions = []
    blocked = []
    for capability_id in selected_ids:
        capability = by_id[capability_id]
        drift = capability["drift"]
        if drift in RECONCILABLE_DRIFT:
            actions.append(
                {
                    "capability_id": capability_id,
                    "operation": "restore_desired_state",
                    "reason": drift,
                    "delivery_mode": capability["delivery_mode"],
                    "desired_version": capability["desired"]["version"],
                    "runtime_location": deepcopy(capability["runtime_location"]),
                }
            )
        elif drift != "none":
            blocked.append(
                {
                    "capability_id": capability_id,
                    "reason": drift,
                    "status": "observation_required",
                }
            )

    unexpected = deepcopy(payload["unexpected_observations"])
    if actions:
        plan_state = "action_required"
    elif blocked:
        plan_state = "observation_required"
    else:
        plan_state = "clean"

    return {
        "schema_version": 1,
        "authority": "environment_availability_only",
        "reconcile": "restore_current_desired_state",
        "candidate_id": payload["candidate_id"],
        "plan_state": plan_state,
        "actions": actions,
        "blocked": blocked,
        "unexpected_observations": unexpected,
        "unexpected_policy": "report_only_never_delete",
        "desired_state_mutation": False,
        "summary": (
            f"{plan_state}: reconcile actions={len(actions)} "
            f"blocked={len(blocked)} unexpected={len(unexpected)}"
        ),
    }


def _ensure_desired_state_unchanged(before: dict, after: dict) -> None:
    before_by_id = _capability_map(before)
    after_by_id = _capability_map(after)
    if set(before_by_id) != set(after_by_id):
        raise CapabilityControlError("reconcile readback changed approved capability identity")

    for capability_id in sorted(before_by_id):
        left = before_by_id[capability_id]
        right = after_by_id[capability_id]
        for key in ("approval", "delivery_mode", "desired", "runtime_location", "probe"):
            if left.get(key) != right.get(key):
                raise CapabilityControlError(
                    f"reconcile readback changed desired authority for {capability_id}"
                )


def verify_reconcile_readback(before: dict, after: dict, plan: dict) -> dict:
    _validate_inventory_payload(before)
    _validate_inventory_payload(after)
    if before["candidate_id"] != after["candidate_id"]:
        raise CapabilityControlError("reconcile cannot change the frozen candidate identity")
    if plan.get("candidate_id") != before["candidate_id"]:
        raise CapabilityControlError("reconcile plan is not bound to the current candidate")
    if plan.get("desired_state_mutation") is not False:
        raise CapabilityControlError("reconcile plan may not mutate desired state")

    _ensure_desired_state_unchanged(before, after)
    after_by_id = _capability_map(after)

    action_results = []
    unresolved = False
    for action in plan.get("actions", []):
        capability_id = action.get("capability_id")
        if capability_id not in after_by_id:
            raise CapabilityControlError("reconcile action is not bound to an approved capability")
        capability = after_by_id[capability_id]
        restored = capability["health"] == "GREEN" and capability["drift"] == "none"
        unresolved = unresolved or not restored
        action_results.append(
            {
                "capability_id": capability_id,
                "status": "restored" if restored else "unresolved",
                "health": capability["health"],
                "drift": capability["drift"],
            }
        )

    before_unexpected = {
        item.get("id_fingerprint")
        for item in before["unexpected_observations"]
        if isinstance(item, dict) and isinstance(item.get("id_fingerprint"), str)
    }
    after_unexpected = {
        item.get("id_fingerprint")
        for item in after["unexpected_observations"]
        if isinstance(item, dict) and isinstance(item.get("id_fingerprint"), str)
    }
    disappeared = sorted(before_unexpected - after_unexpected)

    full_doctor = doctor(after, depth="full")
    if unresolved or disappeared:
        state = "RED"
    else:
        state = full_doctor["state"]

    summary = (
        f"{state}: reconcile restored="
        f"{sum(1 for item in action_results if item['status'] == 'restored')} "
        f"unresolved={sum(1 for item in action_results if item['status'] == 'unresolved')} "
        f"unexpected_disappeared={len(disappeared)}"
    )
    return {
        "schema_version": 1,
        "authority": "environment_availability_only",
        "reconcile": "readback",
        "candidate_id": after["candidate_id"],
        "state": state,
        "actions": action_results,
        "unexpected_observations": deepcopy(after["unexpected_observations"]),
        "unexpected_disappeared": disappeared,
        "desired_state_mutation": False,
        "summary": summary,
    }


def derive(
    *,
    root: Path,
    definition_path: Path,
    candidate_path: Path,
    observations_path: Path | None,
) -> dict:
    definition = inventory.load_json(definition_path)
    inventory.validate_definition(definition)
    candidate = inventory.load_json(candidate_path)
    observations = inventory.load_json(observations_path) if observations_path else None
    return inventory.derive_inventory(definition, candidate, root, observations)


def _path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else inventory._resolve_under_root(root, value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--definition", default=str(DEFAULT_DEFINITION.relative_to(ROOT)))
    parser.add_argument("--candidate")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("--depth", choices=("quick", "full"), default="quick")
    doctor_parser.add_argument("--observations")

    reconcile_parser = sub.add_parser("reconcile")
    reconcile_parser.add_argument("--before-observations", required=True)
    reconcile_parser.add_argument("--after-observations")
    reconcile_parser.add_argument("--capability", action="append", dest="capabilities")

    args = parser.parse_args()
    try:
        root = Path(args.root).resolve()
        definition_path = _path(root, args.definition)
        definition = inventory.load_json(definition_path)
        inventory.validate_definition(definition)
        candidate_path = _path(
            root,
            args.candidate or definition["candidate_source"],
        )

        if args.command == "doctor":
            payload = derive(
                root=root,
                definition_path=definition_path,
                candidate_path=candidate_path,
                observations_path=_path(root, args.observations) if args.observations else None,
            )
            result = doctor(payload, depth=args.depth)
        else:
            before = derive(
                root=root,
                definition_path=definition_path,
                candidate_path=candidate_path,
                observations_path=_path(root, args.before_observations),
            )
            plan = build_reconcile_plan(before, requested_ids=args.capabilities)
            if args.after_observations:
                after = derive(
                    root=root,
                    definition_path=definition_path,
                    candidate_path=candidate_path,
                    observations_path=_path(root, args.after_observations),
                )
                result = verify_reconcile_readback(before, after, plan)
            else:
                result = plan

        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        print(result["summary"], file=sys.stderr)
        return 1 if result.get("state") == "RED" else 0
    except (inventory.InventoryError, CapabilityControlError) as exc:
        print(
            json.dumps(
                {"ok": False, "error": "environment_capability_control", "message": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
