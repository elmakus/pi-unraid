#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile
from pathlib import Path

DIGEST=re.compile(r"^sha256:[0-9a-f]{64}$")
STATES=("armed","observed","validating","committed","rolling-back","recovered")
TRANSITIONS={"armed":{"observed"},"observed":{"validating","rolling-back"},"validating":{"committed","rolling-back"},"rolling-back":{"recovered"},"committed":set(),"recovered":set()}

class GuardError(RuntimeError): pass

def req_digest(v,label):
    if not isinstance(v,str) or not DIGEST.fullmatch(v): raise GuardError(f"{label} must be immutable sha256 digest")
    return v

def req_anchor(v):
    p=Path(v)
    if not p.is_file(): raise GuardError("rollback anchor is not independently retrievable")
    return str(p.resolve())

def binding(candidate,previous,config,anchor):
    raw=json.dumps({"candidate_digest":candidate,"previous_digest":previous,"config_digest":config,"rollback_anchor":anchor},sort_keys=True,separators=(",",":"))
    return "sha256:"+hashlib.sha256(raw.encode()).hexdigest()

def atomic_write(path,data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+".",dir=p.parent)
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,sort_keys=True,indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def validate(g):
    if not isinstance(g,dict) or g.get("state") not in STATES: raise GuardError("invalid guard state")
    c=req_digest(g.get("candidate_digest"),"candidate"); p=req_digest(g.get("previous_digest"),"previous")
    cfg=req_digest(g.get("config_digest"),"configuration"); a=req_anchor(g.get("rollback_anchor"))
    req_digest(g.get("rollback_digest"),"rollback")
    if g["rollback_digest"] != p: raise GuardError("rollback identity must equal exact predecessor")
    b=binding(c,p,cfg,a)
    if g.get("binding_digest") != b: raise GuardError("guard binding digest mismatch")
    return dict(g)

def load(path): return validate(json.loads(Path(path).read_text()))

def arm(path,candidate,previous,config,anchor):
    candidate=req_digest(candidate,"candidate"); previous=req_digest(previous,"previous"); config=req_digest(config,"configuration"); anchor=req_anchor(anchor)
    wanted={"state":"armed","candidate_digest":candidate,"previous_digest":previous,"config_digest":config,"rollback_anchor":anchor,"rollback_digest":previous}
    wanted["binding_digest"]=binding(candidate,previous,config,anchor)
    p=Path(path)
    if p.exists():
        current=load(p)
        if current == wanted: return current
        if current["state"] not in ("committed","recovered"): raise GuardError("existing active guard cannot be rebound")
    atomic_write(p,wanted); return wanted

def transition(path,target,expected_binding):
    current=load(path)
    if current["binding_digest"] != expected_binding: raise GuardError("stale guard binding")
    if target == current["state"]: return current
    if target not in TRANSITIONS[current["state"]]: raise GuardError("invalid transition %s -> %s" % (current["state"], target))
    out=dict(current); out["state"]=target; atomic_write(path,out); return load(path)

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("arm"); a.add_argument("path",type=Path); a.add_argument("candidate"); a.add_argument("previous"); a.add_argument("config"); a.add_argument("anchor")
    t=s.add_parser("transition"); t.add_argument("path",type=Path); t.add_argument("target",choices=STATES); t.add_argument("binding")
    r=s.add_parser("readback"); r.add_argument("path",type=Path)
    x=p.parse_args()
    try:
        out=arm(x.path,x.candidate,x.previous,x.config,x.anchor) if x.cmd=="arm" else transition(x.path,x.target,x.binding) if x.cmd=="transition" else load(x.path)
        print(json.dumps(out,sort_keys=True)); return 0
    except (GuardError,OSError,ValueError,json.JSONDecodeError) as e:
        print(f"guard failed: {e}",file=__import__("sys").stderr); return 2
if __name__=="__main__": raise SystemExit(main())
