#!/usr/bin/env python3
"""Bounded Paseo/Pi compatibility search and exact nogood-cache primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
CACHE_SCHEMA_VERSION = 1
CORE_GATE_ID = "paseo-pi-core"
CORE_GATE_CONTRACT_VERSION = 1


class CoreResolutionError(RuntimeError):
    pass


class CoreResolutionBlocked(CoreResolutionError):
    pass


class CoreResolutionIncomplete(CoreResolutionError):
    pass


class CoreIncompatible(CoreResolutionError):
    pass


def semver_tuple(value):
    match = SEMVER.fullmatch(str(value or ""))
    if match is None:
        raise CoreResolutionError(f"non-stable semantic version: {value!r}")
    return tuple(int(part) for part in match.groups())


def _cmp(version, operator, target):
    value = semver_tuple(version)
    bound = semver_tuple(target)
    if operator == ">=":
        return value >= bound
    if operator == ">":
        return value > bound
    if operator == "<=":
        return value <= bound
    if operator == "<":
        return value < bound
    if operator in ("", "="):
        return value == bound
    raise CoreResolutionError(f"unsupported semver comparator: {operator}")


def _caret_upper(version):
    major, minor, patch = semver_tuple(version)
    if major:
        return (major + 1, 0, 0)
    if minor:
        return (0, minor + 1, 0)
    return (0, 0, patch + 1)


def _tilde_upper(version):
    major, minor, _ = semver_tuple(version)
    return (major, minor + 1, 0)


def node_range_allows(version, expression):
    """Evaluate the bounded Node engine syntax used by managed Pi packages.

    Supported forms intentionally stay small and fail closed: exact versions,
    comparator conjunctions, caret/tilde ranges, wildcards and || alternatives.
    """
    if expression is None:
        return True
    expression = str(expression).strip()
    if not expression or expression == "*":
        return True

    value = semver_tuple(version)
    for alternative in (part.strip() for part in expression.split("||")):
        if not alternative:
            continue
        ok = True
        tokens = alternative.replace(",", " ").split()
        for token in tokens:
            if token in {"*", "x", "X"}:
                continue
            if token.startswith("^"):
                base = token[1:]
                lower = semver_tuple(base)
                ok = ok and value >= lower and value < _caret_upper(base)
                continue
            if token.startswith("~"):
                base = token[1:]
                lower = semver_tuple(base)
                ok = ok and value >= lower and value < _tilde_upper(base)
                continue
            wildcard = re.fullmatch(r"(\d+)\.(\d+)\.(?:x|X|\*)", token)
            if wildcard:
                ok = ok and value[:2] == (int(wildcard.group(1)), int(wildcard.group(2)))
                continue
            wildcard = re.fullmatch(r"(\d+)\.(?:x|X|\*)", token)
            if wildcard:
                ok = ok and value[0] == int(wildcard.group(1))
                continue
            match = re.fullmatch(r"(>=|<=|>|<|=)?(\d+\.\d+\.\d+)", token)
            if match is None:
                raise CoreResolutionError(f"unsupported Node semver range token: {token!r}")
            ok = ok and _cmp(version, match.group(1) or "", match.group(2))
        if ok:
            return True
    return False


def core_contract_fingerprint(definition, node_floor):
    capabilities = []
    for capability in definition.get("capabilities", []):
        desired = capability.get("desired", {}) if isinstance(capability, dict) else {}
        component = desired.get("component")
        if component not in {"paseo", "node", "pi"}:
            continue
        managed = capability.get("managed_update", {})
        capabilities.append(
            {
                "component": component,
                "source": managed.get("source"),
                "immutable_identity": managed.get("immutable_identity"),
                "derived_owner": managed.get("derived_owner"),
            }
        )
    payload = {
        "contract_version": CORE_GATE_CONTRACT_VERSION,
        "node_floor": ".".join(str(part) for part in node_floor),
        "capabilities": sorted(capabilities, key=lambda item: item["component"]),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def default_gate_definition_hash(node_floor):
    payload = {
        "gate_id": CORE_GATE_ID,
        "contract_version": CORE_GATE_CONTRACT_VERSION,
        "checks": [
            "node-derived-from-exact-paseo-image",
            "node-project-floor",
            "pi-node-engine-range",
        ],
        "node_floor": ".".join(str(part) for part in node_floor),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _source_identity(component):
    source = component.get("source", {})
    return {
        "repository": source.get("repository"),
        "tag": source.get("tag"),
        "commit": source.get("commit"),
    }


def exact_pair_identity(paseo, pi):
    artifact = paseo.get("artifact", {})
    npm = pi.get("npm", {})
    return {
        "paseo": {
            "version": paseo.get("version"),
            "source": _source_identity(paseo),
            "oci_digest": artifact.get("digest"),
            "linux_amd64_manifest": artifact.get("linux_amd64_manifest"),
            "config_digest": artifact.get("config_digest"),
        },
        "pi": {
            "version": pi.get("version"),
            "source": _source_identity(pi),
            "npm_integrity": npm.get("integrity"),
            "npm_shasum": npm.get("shasum"),
        },
    }


def nogood_key(
    paseo,
    pi,
    *,
    gate_id,
    gate_definition_hash,
    contract_hash,
    platform_fingerprint,
):
    if not gate_id or not platform_fingerprint:
        raise CoreResolutionError("nogood identity requires gate_id and platform_fingerprint")
    for name, value in (
        ("gate_definition_hash", gate_definition_hash),
        ("contract_hash", contract_hash),
    ):
        if not SHA256.fullmatch(str(value or "")):
            raise CoreResolutionError(f"nogood identity requires exact {name}")
    payload = {
        "components": ["paseo", "pi"],
        "identities": exact_pair_identity(paseo, pi),
        "failure_class": "incompatible",
        "gate_id": gate_id,
        "gate_definition_hash": gate_definition_hash,
        "contract_hash": contract_hash,
        "platform_fingerprint": platform_fingerprint,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest(), payload


def empty_nogood_cache():
    return {"schema_version": CACHE_SCHEMA_VERSION, "entries": []}


def validate_nogood_cache(cache):
    if not isinstance(cache, dict) or cache.get("schema_version") != CACHE_SCHEMA_VERSION:
        raise CoreResolutionError("core nogood cache has unsupported schema")
    entries = cache.get("entries")
    if not isinstance(entries, list):
        raise CoreResolutionError("core nogood cache entries must be a list")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise CoreResolutionError("core nogood cache entry must be an object")
        key = entry.get("key")
        if not SHA256.fullmatch(str(key or "")) or key in seen:
            raise CoreResolutionError("core nogood cache entry key is invalid or duplicated")
        seen.add(key)
        if entry.get("failure_class") != "incompatible":
            raise CoreResolutionError("only proven incompatibility may be stored as a core nogood")
        if not isinstance(entry.get("evidence"), str) or not entry["evidence"].strip():
            raise CoreResolutionError("core nogood cache entry requires durable evidence")
        identity = entry.get("identity")
        if not isinstance(identity, dict):
            raise CoreResolutionError("core nogood cache entry identity is missing")
        raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        expected = "sha256:" + hashlib.sha256(raw).hexdigest()
        if key != expected:
            raise CoreResolutionError("core nogood cache key does not match its exact identity")
    return cache


def load_nogood_cache(path):
    if path is None:
        return empty_nogood_cache()
    path = Path(path)
    if not path.exists():
        return empty_nogood_cache()
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise CoreResolutionError(f"core nogood cache is unreadable: {path}") from exc
    return validate_nogood_cache(data)


def save_nogood_cache(path, cache):
    validate_nogood_cache(cache)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(cache, sort_keys=True, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def record_nogood(cache, *, key, identity, evidence):
    validate_nogood_cache(cache)
    if not SHA256.fullmatch(str(key or "")):
        raise CoreResolutionError("cannot record a nogood without an exact key")
    if not isinstance(evidence, str) or not evidence.strip():
        raise CoreResolutionError("cannot record a nogood without durable evidence")
    if any(item["key"] == key for item in cache["entries"]):
        return False
    cache["entries"].append(
        {
            "key": key,
            "identity": identity,
            "failure_class": "incompatible",
            "evidence": evidence,
        }
    )
    cache["entries"].sort(key=lambda item: item["key"])
    return True


def _static_core_check(paseo, node, pi, pi_node_range, node_floor):
    node_version = node.get("version")
    if semver_tuple(node_version) < tuple(node_floor):
        raise CoreIncompatible(
            f"Paseo Node {node_version} is below the Pi floor "
            + ".".join(str(part) for part in node_floor)
        )
    artifact = paseo.get("artifact", {})
    if node_version != artifact.get("node_version"):
        raise CoreIncompatible("Node version is not derived from the exact Paseo image")
    if node.get("immutable_parent") != artifact.get("reference"):
        raise CoreIncompatible("Node parent is not the exact Paseo image")
    if pi_node_range and not node_range_allows(node_version, pi_node_range):
        raise CoreIncompatible(
            f"Pi {pi.get('version')} Node range {pi_node_range!r} rejects Paseo Node {node_version}"
        )


def _normalize_gate_outcome(outcome):
    if outcome is None:
        return {"status": "compatible"}
    if isinstance(outcome, str):
        outcome = {"status": outcome}
    if not isinstance(outcome, dict):
        raise CoreResolutionError("core gate outcome must be a status string or object")
    status = outcome.get("status")
    if status not in {"compatible", "incompatible", "blocked"}:
        raise CoreResolutionError(f"unsupported core gate status: {status!r}")
    if status == "incompatible":
        evidence = outcome.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise CoreResolutionError("proven incompatible core gate outcome requires evidence")
    return outcome


def search_core_pairs(
    paseo_options,
    pi_options,
    *,
    definition,
    node_floor,
    nogoods=None,
    gate=None,
    gate_id=CORE_GATE_ID,
    gate_definition_hash=None,
    platform_fingerprint="linux-amd64",
    budget=None,
):
    """Return the first newest-first compatible Paseo/Pi pair.

    Options are exact immutable records. Paseo options have keys paseo,node;
    Pi options have keys pi,node_range. The search never considers non-core
    components and never searches below the supplied domains.
    """
    cache = validate_nogood_cache(nogoods or empty_nogood_cache())
    if budget is not None and (not isinstance(budget,int) or isinstance(budget,bool) or budget<=0):
        raise CoreResolutionError("core compatibility search budget must be a positive integer")
    gate_definition_hash = gate_definition_hash or default_gate_definition_hash(node_floor)
    contract_hash = core_contract_fingerprint(definition, node_floor)

    p_opts = sorted(
        list(paseo_options),
        key=lambda item: semver_tuple(item["paseo"].get("version")),
        reverse=True,
    )
    pi_opts = sorted(
        list(pi_options),
        key=lambda item: semver_tuple(item["pi"].get("version")),
        reverse=True,
    )
    if not p_opts or not pi_opts:
        raise CoreResolutionError("core compatibility search domain is empty")
    paseo_versions=[item["paseo"].get("version") for item in p_opts]
    pi_versions=[item["pi"].get("version") for item in pi_opts]
    if len(set(paseo_versions))!=len(paseo_versions) or len(set(pi_versions))!=len(pi_versions):
        raise CoreResolutionError("core compatibility search domain contains duplicate versions")

    cached = {entry["key"] for entry in cache["entries"]}
    attempts = 0
    for paseo_option in p_opts:
        for pi_option in pi_opts:
            attempts += 1
            if budget is not None and attempts > budget:
                raise CoreResolutionIncomplete(
                    "RESOLUTION_INCOMPLETE: core compatibility search budget exhausted"
                )
            paseo = paseo_option["paseo"]
            node = paseo_option["node"]
            pi = pi_option["pi"]
            try:
                _static_core_check(
                    paseo,
                    node,
                    pi,
                    pi_option.get("node_range"),
                    node_floor,
                )
            except CoreIncompatible:
                continue

            key, identity = nogood_key(
                paseo,
                pi,
                gate_id=gate_id,
                gate_definition_hash=gate_definition_hash,
                contract_hash=contract_hash,
                platform_fingerprint=platform_fingerprint,
            )
            if key in cached:
                continue

            outcome = _normalize_gate_outcome(
                gate(paseo, node, pi) if gate is not None else None
            )
            if outcome["status"] == "compatible":
                return {
                    "paseo": paseo,
                    "node": node,
                    "pi": pi,
                    "nogood_cache": cache,
                    "attempts": attempts,
                    "key": key,
                }
            if outcome["status"] == "blocked":
                raise CoreResolutionBlocked(
                    str(outcome.get("reason") or "core compatibility gate is BLOCKED")
                )
            if record_nogood(
                cache,
                key=key,
                identity=identity,
                evidence=outcome["evidence"],
            ):
                cached.add(key)

    raise CoreResolutionError(
        "no compatible core Paseo/Pi pair remains in the bounded domain"
    )


def search_core_candidates(
    paseo_options,
    pi_options,
    *,
    definition,
    node_floor,
    nogoods=None,
    gate=None,
    gate_id=CORE_GATE_ID,
    gate_definition_hash=None,
    platform_fingerprint="linux-amd64",
    budget=None,
):
    """Enumerate every compatible Paseo/Pi pair in the bounded core domains.

    This is the exhaustive companion to search_core_pairs(). It preserves the
    same exact nogood, BLOCKED and budget semantics but does not stop at the
    first compatible pair, allowing the caller to apply complete-candidate
    Pareto/aggregate-lag selection.
    """
    cache = validate_nogood_cache(nogoods or empty_nogood_cache())
    if budget is not None and (
        not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0
    ):
        raise CoreResolutionError("core compatibility search budget must be a positive integer")
    gate_definition_hash = gate_definition_hash or default_gate_definition_hash(node_floor)
    contract_hash = core_contract_fingerprint(definition, node_floor)

    p_opts = sorted(
        list(paseo_options),
        key=lambda item: semver_tuple(item["paseo"].get("version")),
        reverse=True,
    )
    pi_opts = sorted(
        list(pi_options),
        key=lambda item: semver_tuple(item["pi"].get("version")),
        reverse=True,
    )
    if not p_opts or not pi_opts:
        raise CoreResolutionError("core compatibility search domain is empty")
    paseo_versions = [item["paseo"].get("version") for item in p_opts]
    pi_versions = [item["pi"].get("version") for item in pi_opts]
    if len(set(paseo_versions)) != len(paseo_versions) or len(set(pi_versions)) != len(pi_versions):
        raise CoreResolutionError("core compatibility search domain contains duplicate versions")

    cached = {entry["key"] for entry in cache["entries"]}
    compatible = []
    attempts = 0
    for paseo_option in p_opts:
        for pi_option in pi_opts:
            attempts += 1
            if budget is not None and attempts > budget:
                raise CoreResolutionIncomplete(
                    "RESOLUTION_INCOMPLETE: core compatibility search budget exhausted"
                )
            paseo = paseo_option["paseo"]
            node = paseo_option["node"]
            pi = pi_option["pi"]
            try:
                _static_core_check(
                    paseo,
                    node,
                    pi,
                    pi_option.get("node_range"),
                    node_floor,
                )
            except CoreIncompatible:
                continue

            key, identity = nogood_key(
                paseo,
                pi,
                gate_id=gate_id,
                gate_definition_hash=gate_definition_hash,
                contract_hash=contract_hash,
                platform_fingerprint=platform_fingerprint,
            )
            if key in cached:
                continue

            outcome = _normalize_gate_outcome(
                gate(paseo, node, pi) if gate is not None else None
            )
            if outcome["status"] == "compatible":
                compatible.append(
                    {
                        "paseo": paseo,
                        "node": node,
                        "pi": pi,
                    }
                )
                continue
            if outcome["status"] == "blocked":
                raise CoreResolutionBlocked(
                    str(outcome.get("reason") or "core compatibility gate is BLOCKED")
                )
            if record_nogood(
                cache,
                key=key,
                identity=identity,
                evidence=outcome["evidence"],
            ):
                cached.add(key)

    if not compatible:
        raise CoreResolutionError(
            "no compatible core Paseo/Pi pair remains in the bounded domain"
        )
    return {
        "candidates": compatible,
        "nogood_cache": cache,
        "attempts": attempts,
    }
