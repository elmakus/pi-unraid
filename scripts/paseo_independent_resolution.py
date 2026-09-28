#!/usr/bin/env python3
"""Independent non-core fallback and deterministic candidate freshness selection."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
OUTCOME_SCHEMA_VERSION = 1


class IndependentResolutionError(RuntimeError):
    pass


class IndependentResolutionBlocked(IndependentResolutionError):
    pass


def _semver(value):
    match = SEMVER.fullmatch(str(value or ""))
    if match is None:
        raise IndependentResolutionError(f"non-stable semantic version: {value!r}")
    return tuple(int(part) for part in match.groups())


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def component_identity(component):
    """Hash the exact frozen component identity, excluding descriptive stable-line text."""
    if not isinstance(component, dict):
        raise IndependentResolutionError("component identity requires an object")
    payload = copy.deepcopy(component)
    payload.pop("stable_line", None)
    version = payload.get("version")
    _semver(version)
    return "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest()


def independent_component_names(definition):
    capabilities = definition.get("capabilities") if isinstance(definition, dict) else None
    if not isinstance(capabilities, list):
        raise IndependentResolutionError("managed capability definition is missing")
    names = set()
    for capability in capabilities:
        if not isinstance(capability, dict):
            raise IndependentResolutionError("managed capability entry must be an object")
        desired = capability.get("desired", {})
        managed = capability.get("managed_update", {})
        if (
            isinstance(desired, dict)
            and desired.get("kind") == "candidate_component"
            and isinstance(managed, dict)
            and managed.get("membership") == "managed"
            and managed.get("update_class") == "independent"
        ):
            component = desired.get("component")
            if not isinstance(component, str) or not component:
                raise IndependentResolutionError("independent managed component name is invalid")
            names.add(component)
    return names


def load_independent_outcomes(path):
    if path is None:
        return {"schema_version": OUTCOME_SCHEMA_VERSION, "outcomes": []}
    try:
        data = json.loads(Path(path).read_text())
    except FileNotFoundError as exc:
        raise IndependentResolutionError(f"independent outcome file is missing: {path}") from exc
    except OSError as exc:
        raise IndependentResolutionError(f"independent outcome file is unreadable: {path}") from exc
    except json.JSONDecodeError as exc:
        raise IndependentResolutionError(f"independent outcome file is not valid JSON: {path}") from exc
    return data


def _validated_outcomes(data, allowed):
    if not isinstance(data, dict) or data.get("schema_version") != OUTCOME_SCHEMA_VERSION:
        raise IndependentResolutionError("independent outcomes use an unsupported schema")
    outcomes = data.get("outcomes")
    if not isinstance(outcomes, list):
        raise IndependentResolutionError("independent outcomes must be a list")
    by_component = {}
    for item in outcomes:
        if not isinstance(item, dict):
            raise IndependentResolutionError("independent outcome record must be an object")
        extra = set(item) - {"component", "identity", "status", "evidence", "reason"}
        if extra:
            raise IndependentResolutionError(
                "independent outcome has unexpected field(s): " + ",".join(sorted(extra))
            )
        component = item.get("component")
        if component not in allowed:
            raise IndependentResolutionError(
                f"independent outcome names non-independent component: {component}"
            )
        if component in by_component:
            raise IndependentResolutionError(f"duplicate independent outcome: {component}")
        identity = item.get("identity")
        if not SHA256.fullmatch(str(identity or "")):
            raise IndependentResolutionError(
                f"independent outcome for {component} lacks exact identity"
            )
        status = item.get("status")
        if status not in {"unavailable", "blocked"}:
            raise IndependentResolutionError(
                f"unsupported independent outcome status for {component}: {status!r}"
            )
        if status == "unavailable":
            evidence = item.get("evidence")
            if not isinstance(evidence, str) or not evidence.strip():
                raise IndependentResolutionError(
                    f"proven unavailable independent outcome for {component} requires evidence"
                )
        if status == "blocked":
            reason = item.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise IndependentResolutionError(
                    f"blocked independent outcome for {component} requires a reason"
                )
        by_component[component] = copy.deepcopy(item)
    return by_component


def resolve_independent_components(
    latest_components,
    accepted_components,
    definition,
    *,
    outcomes=None,
    skip_components=None,
):
    """Resolve each non-core managed component independently.

    Absence of a failure record means the freshly discovered exact version remains selected.
    A proven exact-identity unavailable outcome falls back only to the previous accepted
    exact component. BLOCKED/transient outcomes stop resolution and are never converted
    into incompatibility or a durable known-bad cache.
    """
    if not isinstance(latest_components, dict) or not isinstance(accepted_components, dict):
        raise IndependentResolutionError("independent resolution requires component mappings")
    allowed = independent_component_names(definition)
    skip = set(skip_components or ())
    unknown_skip = skip - allowed
    if unknown_skip:
        raise IndependentResolutionError(
            "independent resolution skip names non-independent component(s): "
            + ",".join(sorted(unknown_skip))
        )
    records = _validated_outcomes(
        outcomes or {"schema_version": OUTCOME_SCHEMA_VERSION, "outcomes": []},
        allowed,
    )
    resolved = copy.deepcopy(latest_components)
    automatic_lag = set()
    decisions = []

    for component in sorted(allowed):
        if component not in latest_components or component not in accepted_components:
            raise IndependentResolutionError(
                f"independent component baseline is missing: {component}"
            )
        latest = latest_components[component]
        accepted = accepted_components[component]
        latest_identity = component_identity(latest)
        accepted_identity = component_identity(accepted)

        if component in skip:
            decisions.append(
                {
                    "component": component,
                    "status": "authority_override",
                    "selected_identity": latest_identity,
                }
            )
            continue

        outcome = records.get(component)
        # Exact-identity binding makes old failure evidence non-poisoning after upstream
        # replaces or advances the component.
        if outcome is not None and outcome["identity"] != latest_identity:
            outcome = None

        if outcome is not None and outcome["status"] == "blocked":
            raise IndependentResolutionBlocked(
                f"independent component {component} BLOCKED: {outcome['reason']}"
            )

        if outcome is not None and outcome["status"] == "unavailable":
            if latest_identity == accepted_identity:
                raise IndependentResolutionError(
                    f"independent component {component} has no usable fallback: "
                    "the proven-unavailable newest identity is already the accepted identity"
                )
            resolved[component] = copy.deepcopy(accepted)
            if latest.get("version") != accepted.get("version"):
                automatic_lag.add(component)
            decisions.append(
                {
                    "component": component,
                    "status": "fallback_previous_accepted",
                    "observed_latest": latest.get("version"),
                    "selected_version": accepted.get("version"),
                    "failed_identity": latest_identity,
                    "evidence": outcome["evidence"],
                }
            )
            continue

        decisions.append(
            {
                "component": component,
                "status": "no_change" if latest_identity == accepted_identity else "selected_latest",
                "selected_version": latest.get("version"),
                "selected_identity": latest_identity,
            }
        )

    return resolved, automatic_lag, decisions


def _candidate_versions(candidate):
    if not isinstance(candidate, dict):
        raise IndependentResolutionError("candidate must be an object")
    components = candidate.get("components", candidate)
    if not isinstance(components, dict):
        raise IndependentResolutionError("candidate components must be an object")
    return components


def candidate_lag_vector(candidate, version_domains):
    """Return equal-weight ordinal lag from newest for each independently versioned unit."""
    components = _candidate_versions(candidate)
    if not isinstance(version_domains, dict) or not version_domains:
        raise IndependentResolutionError("version domains must be a non-empty mapping")
    vector = []
    for component in sorted(version_domains):
        domain = version_domains[component]
        if not isinstance(domain, list) or not domain:
            raise IndependentResolutionError(f"version domain is empty: {component}")
        if len(domain) != len(set(domain)):
            raise IndependentResolutionError(f"version domain has duplicates: {component}")
        for version in domain:
            _semver(version)
        version = components.get(component, {}).get("version")
        if version not in domain:
            raise IndependentResolutionError(
                f"candidate version {component}={version!r} is outside its bounded domain"
            )
        vector.append(domain.index(version))
    return tuple(vector)


def pareto_maximal_candidates(candidates, version_domains):
    if not isinstance(candidates, list) or not candidates:
        raise IndependentResolutionError("complete candidate set is empty")
    vectors = [candidate_lag_vector(candidate, version_domains) for candidate in candidates]
    keep = []
    for idx, vector in enumerate(vectors):
        dominated = False
        for other_idx, other in enumerate(vectors):
            if idx == other_idx:
                continue
            if all(a <= b for a, b in zip(other, vector)) and any(
                a < b for a, b in zip(other, vector)
            ):
                dominated = True
                break
        if not dominated:
            keep.append(copy.deepcopy(candidates[idx]))
    return keep


def _technical_tiebreak(candidate):
    return "sha256:" + hashlib.sha256(_canonical(candidate)).hexdigest()


def select_freshest_complete_candidate(candidates, version_domains):
    """Choose among complete compatible candidates using accepted R8 freshness semantics."""
    frontier = pareto_maximal_candidates(candidates, version_domains)
    ranked = []
    for candidate in frontier:
        vector = candidate_lag_vector(candidate, version_domains)
        ranked.append((sum(vector), _technical_tiebreak(candidate), vector, candidate))
    ranked.sort(key=lambda item: (item[0], item[1]))
    lag, tiebreak, vector, candidate = ranked[0]
    return {
        "candidate": copy.deepcopy(candidate),
        "aggregate_lag": lag,
        "lag_vector": vector,
        "technical_tiebreak": tiebreak,
        "pareto_count": len(frontier),
    }


def candidate_resolution_status(candidate, accepted_candidate):
    """Report deterministic no-op when the exact resolved candidate is unchanged."""
    if not isinstance(candidate, dict) or not isinstance(accepted_candidate, dict):
        raise IndependentResolutionError("candidate status requires two candidate objects")
    current_id = candidate.get("candidate_id")
    accepted_id = accepted_candidate.get("candidate_id")
    if (
        isinstance(current_id, str)
        and isinstance(accepted_id, str)
        and SHA256.fullmatch(current_id)
        and SHA256.fullmatch(accepted_id)
    ):
        return "no_op" if current_id == accepted_id else "update"
    return "no_op" if _canonical(candidate) == _canonical(accepted_candidate) else "update"
