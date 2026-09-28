#!/usr/bin/env python3
"""Bounded disposable Tower validation for one immutable Paseo candidate digest."""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, tempfile
from pathlib import Path

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^ghcr\.io/[a-z0-9][a-z0-9._/-]*$")
SCHEMA_VERSION = 1

class ValidationError(RuntimeError): pass
class ValidationBlocked(RuntimeError): pass

def run(argv, *, timeout=300, check=True):
    try:
        p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValidationBlocked(f"command unavailable: {argv[0]}") from exc
    if check and p.returncode:
        raise ValidationError(f"command failed ({p.returncode}): {' '.join(argv)}: {(p.stderr or p.stdout)[-1200:]}")
    return p

def immutable_ref(repository, digest):
    repository = repository.strip().lower()
    if not REPOSITORY.fullmatch(repository):
        raise ValidationError("GHCR repository path required")
    if not DIGEST.fullmatch(digest):
        raise ValidationError("exact sha256 OCI digest required")
    return f"{repository}@{digest}"

def validate(*, repository, digest, output, state_root, uid=99, gid=100, network="pi-unraid-validator"):
    ref = immutable_ref(repository, digest)
    name = f"paseo-validator-{digest[7:19]}"
    result = {"schema_version": SCHEMA_VERSION, "status": "BLOCKED", "immutable_ref": ref, "digest": digest, "checks": {}}
    work = None
    try:
        if not shutil.which("docker"):
            raise ValidationBlocked("docker CLI unavailable")
        readback = run(["docker","buildx","imagetools","inspect",ref]).stdout
        if f"Digest: {digest}" not in readback:
            raise ValidationError("registry immutable digest readback mismatch")
        result["checks"]["registry_digest"] = "PASS"
        run(["docker","image","pull",ref], timeout=900)
        image_id = run(["docker","image","inspect",ref,"--format","{{.Id}}"]).stdout.strip()
        if not DIGEST.fullmatch(image_id):
            raise ValidationError("pulled local image ID missing")
        result["image_id"] = image_id
        root = Path(state_root)
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="candidate-", dir=root))
        for dirname in ("home","projects","worktrees"):
            path = work / dirname
            path.mkdir()
            path.chmod(0o700)
            try:
                os.chown(path, uid, gid)
            except PermissionError as exc:
                raise ValidationBlocked("cannot establish validator UID:GID ownership") from exc
        if run(["docker","network","inspect",network], check=False).returncode:
            run(["docker","network","create",network])
        run(["docker","rm","-f",name], check=False)
        argv = ["docker","run","-d","--name",name,"--user",f"{uid}:{gid}","--network",network,
                "--read-only","--tmpfs","/tmp:rw,nosuid,nodev","--tmpfs","/run:rw,nosuid,nodev",
                "-e","TZ=Europe/Zurich","-e","HOME=/home/paseo","-e","PASEO_HOME=/home/paseo/.paseo",
                "-v",f"{work/'home'}:/home/paseo:rw","-v",f"{work/'projects'}:/projects:rw",
                "-v",f"{work/'worktrees'}:/worktrees:rw",ref]
        joined = " ".join(argv)
        for forbidden in ("/var/run/docker.sock","unraid-api.key","codex-lb","/mnt/user/appdata/pi-unraid/paseo-home"):
            if forbidden in joined:
                raise ValidationError(f"forbidden production authority: {forbidden}")
        run(argv)
        obj = json.loads(run(["docker","inspect",name]).stdout)[0]
        cfg, host, mounts = obj.get("Config") or {}, obj.get("HostConfig") or {}, obj.get("Mounts") or []
        state = obj.get("State") or {}
        health = (state.get("Health") or {}).get("Status") or state.get("Status")
        if cfg.get("User") != f"{uid}:{gid}":
            raise ValidationError("UID:GID mismatch")
        if host.get("NetworkMode") != network:
            raise ValidationError("validator network mismatch")
        if {m.get("Destination") for m in mounts} != {"/home/paseo","/projects","/worktrees"}:
            raise ValidationError("unexpected mount surface")
        if any(not str(m.get("Source","")).startswith(str(work)) for m in mounts):
            raise ValidationError("non-disposable host mount detected")
        env = "\n".join(cfg.get("Env") or []).upper()
        if any(x in env for x in ("UNRAID_API","CODEX_LB_SECRET","GITHUB_TOKEN")):
            raise ValidationError("production/host secret exposed")
        if health not in ("healthy","running"):
            raise ValidationError(f"candidate runtime state: {health}")
        result["checks"].update({"uid_gid":"PASS","mount_isolation":"PASS","network_isolation":"PASS","secret_isolation":"PASS","runtime":"PASS"})
        result["status"] = "PASS"
    except ValidationBlocked as exc:
        result.update(status="BLOCKED", reason=str(exc))
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        result.update(status="FAIL", reason=str(exc))
    finally:
        if shutil.which("docker"):
            run(["docker","rm","-f",name], check=False)
        if work is not None:
            shutil.rmtree(work, ignore_errors=True)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repository", default="ghcr.io/elmakus/pi-unraid")
    p.add_argument("--digest", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--state-root", type=Path, required=True)
    p.add_argument("--uid", type=int, default=99)
    p.add_argument("--gid", type=int, default=100)
    p.add_argument("--network", default="pi-unraid-validator")
    a = p.parse_args()
    result = validate(repository=a.repository,digest=a.digest,output=a.output,state_root=a.state_root,uid=a.uid,gid=a.gid,network=a.network)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else (3 if result["status"] == "BLOCKED" else 2)

if __name__ == "__main__":
    raise SystemExit(main())
