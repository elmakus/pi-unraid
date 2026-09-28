#!/usr/bin/env python3
"""Disposable persistent-state compatibility proof for Paseo runtime images."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
IMAGE_ID=re.compile(r"^sha256:[0-9a-f]{64}$")
class ProofError(RuntimeError): pass
class ProofBlocked(RuntimeError): pass
def run(argv, timeout=120, check=True):
    try: p=subprocess.run(argv,text=True,capture_output=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc: raise ProofBlocked(f"command unavailable: {argv[0]}") from exc
    if check and p.returncode: raise ProofError(f"command failed ({p.returncode}): {(p.stderr or p.stdout)[-1000:]}")
    return p
def digest_file(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def clone_representative(src,dst):
    paseo=src/".paseo"
    if not paseo.is_dir(): raise ProofBlocked("accepted baseline .paseo state unavailable")
    dstp=dst/".paseo"; dstp.mkdir(parents=True)
    required=["config.json","daemon-keypair.json","server-id"]
    copied=[]
    for rel in required:
        p=paseo/rel
        if not p.is_file(): raise ProofBlocked(f"accepted baseline missing {rel}")
        shutil.copy2(p,dstp/rel); copied.append(rel)
    for rel in ("projects/projects.json","projects/workspaces.json"):
        p=paseo/rel
        if p.is_file():
            (dstp/rel).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dstp/rel); copied.append(rel)
    return {"source":str(src.resolve()),"files":{r:digest_file(dstp/r) for r in copied}}
def image_readback(image):
    if not IMAGE_ID.fullmatch(image): raise ProofError("exact immutable local image ID required")
    got=run(["docker","image","inspect",image,"--format","{{.Id}}"]).stdout.strip()
    if got!=image: raise ProofError("immutable image ID readback mismatch")
    return got
def runtime_probe(image,home,name):
    run(["docker","rm","-f",name],check=False)
    argv=["docker","run","-d","--name",name,"--user","99:100","--network","none",
          "--read-only","--tmpfs","/tmp:rw,nosuid,nodev","--tmpfs","/run:rw,nosuid,nodev",
          "-e","HOME=/home/paseo","-e","PASEO_HOME=/home/paseo/.paseo",
          "-v",f"{home}:/home/paseo:rw",image]
    if "/mnt/user/appdata/pi-unraid/paseo-home" in " ".join(argv): raise ProofError("production HOME mount forbidden")
    run(argv)
    deadline=time.time()+30
    while time.time()<deadline:
        obj=json.loads(run(["docker","inspect",name]).stdout)[0]
        state=obj.get("State") or {}
        if state.get("Status")=="running": break
        if state.get("Status") in ("exited","dead"): raise ProofError(f"runtime exited under {image}")
        time.sleep(1)
    else: raise ProofError("runtime readiness timeout")
    probe=run(["docker","exec",name,"sh","-lc","paseo daemon status --home /home/paseo/.paseo --json >/tmp/status.json 2>/dev/null || paseo ls --home /home/paseo/.paseo --json >/tmp/status.json 2>/dev/null; test -s /tmp/status.json"])
    run(["docker","rm","-f",name],check=False)
    return probe.returncode==0
def prove(*,baseline,candidate,previous,state_root,output,inject_irreversible=False):
    result={"schema_version":1,"status":"BLOCKED","checks":{}}
    work=None; names=[]
    try:
        if not shutil.which("docker"): raise ProofBlocked("docker CLI unavailable")
        result["candidate_image_id"]=image_readback(candidate); result["previous_image_id"]=image_readback(previous)
        root=Path(state_root); root.mkdir(parents=True,exist_ok=True)
        work=Path(tempfile.mkdtemp(prefix="state-roundtrip-",dir=root)); home=work/"home"; home.mkdir()
        prov=clone_representative(Path(baseline),home); result["baseline_provenance"]=prov
        if Path(baseline).resolve() in home.resolve().parents: raise ProofError("clone nested in production baseline")
        os.chown(home,99,100)
        for p in home.rglob("*"):
            try: os.chown(p,99,100)
            except PermissionError: pass
        result["checks"]["baseline_clone_isolated"]="PASS"
        if inject_irreversible:
            (home/".paseo"/".ordinary-channel-incompatible").write_text("fixture-v2\n")
            result.update(status="BLOCKED",reason="irreversible/incompatible persistent-state transition detected")
            result["checks"]["irreversible_transition"]="BLOCKED"; return result
        n1="paseo-state-candidate-"+candidate[7:15]; names.append(n1)
        if not runtime_probe(candidate,home,n1): raise ProofError("candidate could not open accepted baseline clone")
        marker=home/".paseo"/"state-roundtrip-candidate.json"
        marker.write_text(json.dumps({"producer_image_id":candidate,"kind":"representative-candidate-state"})+"\n")
        os.chown(marker,99,100)
        result["candidate_state_sha256"]=digest_file(marker); result["checks"]["candidate_state_mutation"]="PASS"
        n2="paseo-state-previous-"+previous[7:15]; names.append(n2)
        if not runtime_probe(previous,home,n2): raise ProofError("previous runtime could not reopen candidate-modified state")
        if not marker.is_file() or digest_file(marker)!=result["candidate_state_sha256"]: raise ProofError("candidate state marker lost on previous-runtime reopen")
        result["checks"]["previous_runtime_reopen"]="PASS"; result["checks"]["direct_skip_path"]="PASS"; result["status"]="PASS"
    except ProofBlocked as exc: result.update(status="BLOCKED",reason=str(exc))
    except (ProofError,ValueError,json.JSONDecodeError) as exc: result.update(status="FAIL",reason=str(exc))
    finally:
        for n in names:
            if shutil.which("docker"): run(["docker","rm","-f",n],check=False)
        if work is not None: shutil.rmtree(work,ignore_errors=True)
        Path(output).parent.mkdir(parents=True,exist_ok=True); Path(output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    return result
def main():
    p=argparse.ArgumentParser(); p.add_argument("--baseline",type=Path,required=True); p.add_argument("--candidate",required=True); p.add_argument("--previous",required=True); p.add_argument("--state-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--inject-irreversible",action="store_true")
    a=p.parse_args(); r=prove(baseline=a.baseline,candidate=a.candidate,previous=a.previous,state_root=a.state_root,output=a.output,inject_irreversible=a.inject_irreversible); print(json.dumps(r,sort_keys=True)); return 0 if r["status"]=="PASS" else (3 if r["status"]=="BLOCKED" else 2)
if __name__=="__main__": raise SystemExit(main())
