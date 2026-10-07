#!/usr/bin/env python3
import argparse, json, os, re, tempfile
from pathlib import Path

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SLOTS = ("current", "previous_1", "previous_2")

def digest(v):
    if not isinstance(v, str) or not DIGEST_RE.fullmatch(v):
        raise ValueError(f"invalid immutable digest: {v!r}")
    return v

def load(path):
    data = json.loads(Path(path).read_text())
    if set(data) != set(SLOTS):
        raise ValueError("ledger must contain exactly current, previous_1, previous_2")
    for k in SLOTS: digest(data[k])
    if len(set(data.values())) != 3:
        raise ValueError("known-good identities must be distinct")
    return data

def atomic_write(path, data):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+".", dir=p.parent)
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,sort_keys=True,indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def rotate(ledger, new):
    digest(new)
    if new == ledger["current"]:
        return dict(ledger)
    if new in (ledger["previous_1"], ledger["previous_2"]):
        raise ValueError("stale known-good identity cannot become a new current")
    return {"current":new,"previous_1":ledger["current"],"previous_2":ledger["previous_1"]}


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
    value by value equality; the kind distinguishes the OCI manifest
    namespace from the platform image-ID namespace. Unknown, multiple
    or wrong-repository mappings fail closed. Rotation still occurs
    only on terminal GREEN via commit_on_terminal.
    """
    if not isinstance(predecessor_mapping, dict):
        raise ValueError("predecessor mapping must be an object")
    kind = predecessor_mapping.get("kind")
    if kind not in ("oci", "local", "legacy"):
        raise ValueError("unsupported predecessor kind")
    if kind == "oci":
        value = predecessor_mapping.get("digest")
    else:
        value = predecessor_mapping.get("image_id")
    digest(value)
    if value != ledger["current"]:
        raise ValueError("predecessor mapping mismatch vs ledger current")
    if kind == "legacy":
        for key in ("archive_sha256", "config_digest"):
            digest(predecessor_mapping.get(key))
        if not predecessor_mapping.get("archive_path") or not predecessor_mapping.get("state_identity"):
            raise ValueError("legacy predecessor anchor/state is missing")
    return commit_on_terminal(ledger, new, transaction_status=transaction_status)

def guard_input(candidate, ledger, config_sha256, rollback_anchor):
    digest(candidate); digest(ledger["current"])
    if candidate == ledger["current"]: raise ValueError("candidate equals current")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", config_sha256): raise ValueError("invalid config digest")
    anchor=Path(rollback_anchor)
    if not anchor.is_file(): raise ValueError("rollback anchor is not independently retrievable")
    return {"state":"unarmed","candidate_digest":candidate,"predecessor_digest":ledger["current"],
            "configuration_digest":config_sha256,"rollback_anchor":str(anchor.resolve())}

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate"); v.add_argument("ledger")
    r=sub.add_parser("rotate"); r.add_argument("ledger"); r.add_argument("digest"); r.add_argument("--write",action="store_true")
    g=sub.add_parser("guard-input"); g.add_argument("ledger"); g.add_argument("candidate"); g.add_argument("configuration_digest"); g.add_argument("rollback_anchor"); g.add_argument("--output")
    a=p.parse_args()
    ledger=load(a.ledger)
    if a.cmd=="validate": out=ledger
    elif a.cmd=="rotate":
        out=rotate(ledger,a.digest)
        if a.write: atomic_write(a.ledger,out)
    else:
        out=guard_input(a.candidate,ledger,a.configuration_digest,a.rollback_anchor)
        if a.output: atomic_write(a.output,out)
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
