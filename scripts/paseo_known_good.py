#!/usr/bin/env python3
"""Typed known-good ledger: current plus exactly two previous anchors.

Every slot carries an explicit predecessor kind (``oci``/``local``/``legacy``)
so OCI manifest digests never conflate with platform-local image IDs as the
set migrates. Legacy entries additionally bind their independently
recoverable archive/configuration/state anchor digests. Historical
single-string ledgers (bare OCI digests) migrate coherently through
``migrate_legacy_ledger``; ambiguous or multi-typed records fail closed.
Rotation still occurs only on terminal GREEN/committed transactions.
"""
import argparse
import json
import os
import re
import tempfile
from pathlib import Path

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SLOTS = ("current", "previous_1", "previous_2")
KINDS = ("oci", "local", "legacy")


def digest(v):
    if not isinstance(v, str) or not DIGEST_RE.fullmatch(v):
        raise ValueError(f"invalid immutable digest: {v!r}")
    return v


def validate_entry(value):
    """Validate one typed ledger entry, returning its normalized form."""
    if not isinstance(value, dict):
        raise ValueError("ledger entry must be a typed object")
    kind = value.get("kind")
    if kind not in KINDS:
        raise ValueError(f"unsupported ledger entry kind: {kind!r}")
    if kind == "oci":
        out = {"kind": "oci", "digest": digest(value.get("digest"))}
        if value.get("repository") is not None:
            repo = str(value["repository"]).strip().lower()
            if not repo:
                raise ValueError("ledger OCI repository is missing")
            out["repository"] = repo
        if set(value) - {"kind", "digest", "repository"}:
            raise ValueError("ledger OCI entry carries ambiguous extra identity")
        return out
    if kind == "local":
        out = {"kind": "local", "image_id": digest(value.get("image_id"))}
        if set(value) - {"kind", "image_id"}:
            raise ValueError("ledger local entry carries ambiguous extra identity")
        return out
    out = {"kind": "legacy", "image_id": digest(value.get("image_id")),
           "archive_sha256": digest(value.get("archive_sha256")),
           "config_digest": digest(value.get("config_digest"))}
    state = value.get("state_identity")
    if not isinstance(state, str) or not state:
        raise ValueError("ledger legacy state identity is missing")
    out["state_identity"] = state
    if set(value) - {"kind", "image_id", "archive_sha256", "config_digest",
                     "state_identity"}:
        raise ValueError("ledger legacy entry carries ambiguous extra identity")
    return out


def _entry_key(entry):
    if entry["kind"] == "oci":
        return ("oci", entry["digest"])
    return (entry["kind"], entry["image_id"])


def load(path):
    data = json.loads(Path(path).read_text())
    if set(data) != set(SLOTS):
        raise ValueError("ledger must contain exactly current, previous_1, previous_2")
    ledger = {k: validate_entry(data[k]) for k in SLOTS}
    if len({_entry_key(ledger[k]) for k in SLOTS}) != 3:
        raise ValueError("known-good identities must be distinct")
    return ledger


def atomic_write(path, data):
    data = {k: validate_entry(data[k]) for k in SLOTS}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", dir=p.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, sort_keys=True, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def migrate_legacy_ledger(data):
    """Coherently migrate a historical bare-digest ledger to typed form.

    Historical slots held single OCI digest strings with no kind. They
    migrate as ``oci`` entries (repository unknown at this layer; the
    writer's typed mapping enforces the repository binding). Anything
    else fails closed.
    """
    if not isinstance(data, dict) or set(data) != set(SLOTS):
        raise ValueError("legacy ledger must contain exactly current, previous_1, previous_2")
    return {k: {"kind": "oci", "digest": digest(data[k])} for k in SLOTS}


def rotate(ledger, new):
    new = validate_entry(new)
    if _entry_key(new) == _entry_key(ledger["current"]):
        return dict(ledger)
    if _entry_key(new) in (_entry_key(ledger["previous_1"]), _entry_key(ledger["previous_2"])):
        raise ValueError("stale known-good identity cannot become a new current")
    return {"current": new, "previous_1": ledger["current"], "previous_2": ledger["previous_1"]}


def commit_on_terminal(ledger, new, *, transaction_status):
    """Rotate the one coherent ledger only on terminal GREEN/committed.

    Rejected (RED/recovered), uncertain (UNKNOWN/BLOCKED) or any
    non-terminal transaction never rotates: the current plus exactly two
    previous anchors are protected and no second ledger is introduced.
    """
    status = str(transaction_status or "").strip().upper()
    if status in ("GREEN", "COMMITTED"):
        return rotate(ledger, new)
    if status in ("RED", "RECOVERED", "UNKNOWN", "BLOCKED", "FAIL"):
        raise ValueError(f"ledger never rotates on {status} transactions")
    raise ValueError(f"unknown transaction status: {transaction_status!r}")


def migrate_with_predecessor(ledger, new, *, predecessor_mapping,
                             transaction_status):
    """Coherently migrate existing records with a typed predecessor.

    The typed mapping (oci/local/legacy) must bind the ledger current
    entry by kind and value; the kind distinguishes the OCI manifest
    namespace from the platform image-ID namespace. Unknown, multiple
    or wrong-repository mappings fail closed. Rotation still occurs
    only on terminal GREEN via commit_on_terminal.
    """
    if not isinstance(predecessor_mapping, dict):
        raise ValueError("predecessor mapping must be an object")
    kind = predecessor_mapping.get("kind")
    if kind not in KINDS:
        raise ValueError("unsupported predecessor kind")
    current = ledger["current"]
    if current["kind"] != kind:
        raise ValueError("predecessor kind mismatch vs ledger current")
    if kind == "oci":
        value = predecessor_mapping.get("digest")
        if value != current["digest"]:
            raise ValueError("predecessor mapping mismatch vs ledger current")
        if predecessor_mapping.get("repository") is not None and current.get("repository") is not None:
            if str(predecessor_mapping["repository"]).strip().lower() != str(current["repository"]).strip().lower():
                raise ValueError("predecessor repository mismatch vs ledger current")
    else:
        value = predecessor_mapping.get("image_id")
        if value != current["image_id"]:
            raise ValueError("predecessor mapping mismatch vs ledger current")
    if kind == "legacy":
        for key in ("archive_sha256", "config_digest"):
            digest(predecessor_mapping.get(key))
            if predecessor_mapping.get(key) != current.get(key):
                raise ValueError(f"legacy {key} mismatch vs ledger current")
        if not predecessor_mapping.get("state_identity"):
            raise ValueError("legacy predecessor anchor/state is missing")
        if predecessor_mapping.get("state_identity") != current.get("state_identity"):
            raise ValueError("legacy state identity mismatch vs ledger current")
    return commit_on_terminal(ledger, new, transaction_status=transaction_status)


def guard_input(candidate, ledger, config_sha256, rollback_anchor):
    digest(candidate)
    digest(ledger["current"].get("digest", ledger["current"].get("image_id")))
    current_value = ledger["current"].get("digest", ledger["current"].get("image_id"))
    if candidate == current_value:
        raise ValueError("candidate equals current")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", config_sha256):
        raise ValueError("invalid config digest")
    anchor = Path(rollback_anchor)
    if not anchor.is_file():
        raise ValueError("rollback anchor is not independently retrievable")
    return {"state": "unarmed", "candidate_digest": candidate, "predecessor_digest": current_value,
            "configuration_digest": config_sha256, "rollback_anchor": str(anchor.resolve())}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("ledger")
    r = sub.add_parser("rotate")
    r.add_argument("ledger")
    r.add_argument("entry")
    r.add_argument("--write", action="store_true")
    g = sub.add_parser("guard-input")
    g.add_argument("ledger")
    g.add_argument("candidate")
    g.add_argument("configuration_digest")
    g.add_argument("rollback_anchor")
    g.add_argument("--output")
    m = sub.add_parser("migrate-legacy")
    m.add_argument("ledger")
    m.add_argument("--write", action="store_true")
    a = p.parse_args()
    if a.cmd == "migrate-legacy":
        raw = json.loads(Path(a.ledger).read_text())
        out = migrate_legacy_ledger(raw)
        if a.write:
            atomic_write(a.ledger, out)
    else:
        ledger = load(a.ledger)
        if a.cmd == "validate":
            out = ledger
        elif a.cmd == "rotate":
            out = rotate(ledger, json.loads(a.entry))
            if a.write:
                atomic_write(a.ledger, out)
        else:
            out = guard_input(a.candidate, ledger, a.configuration_digest, a.rollback_anchor)
            if a.output:
                atomic_write(a.output, out)
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
