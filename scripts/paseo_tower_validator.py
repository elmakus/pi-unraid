#!/usr/bin/env python3
"""Bounded disposable Tower validation for one immutable Paseo candidate digest."""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^ghcr\.io/[a-z0-9][a-z0-9._/-]*$")
SCHEMA_VERSION = 1
CODEX_SECRET_TARGET = "/run/secrets/pi-unraid-codex-lb"

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

def wait_for_runtime(name, *, timeout=90, poll_interval=2):
    deadline = time.monotonic() + timeout
    while True:
        obj = json.loads(run(["docker","inspect",name]).stdout)[0]
        state = obj.get("State") or {}
        health = state.get("Health")
        if health is not None:
            status = health.get("Status")
            if status == "healthy":
                return obj
            if status == "unhealthy":
                raise ValidationError("candidate runtime health: unhealthy")
        else:
            status = state.get("Status")
            if status == "running":
                return obj
            if status in ("exited","dead"):
                raise ValidationError(f"candidate runtime state: {status}")
        if time.monotonic() >= deadline:
            raise ValidationError(f"candidate runtime readiness timeout: {status}")
        time.sleep(poll_interval)

def validate(*, repository, digest, output, state_root, uid=99, gid=100, network="pi-unraid-validator", codex_secret=None, codex_base_url=None, codex_model=None):
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
                "-v",f"{work/'worktrees'}:/worktrees:rw"]
        if codex_secret is not None:
            secret = Path(codex_secret).resolve()
            if not secret.is_file(): raise ValidationBlocked("dedicated Codex-LB credential file unavailable")
            if not codex_base_url or not codex_base_url.rstrip("/").endswith("/v1"): raise ValidationError("Codex-LB base URL must end in /v1")
            if not codex_model or any(ch.isspace() for ch in codex_model): raise ValidationError("Codex-LB model must be one non-empty model id")
            argv += ["-e",f"PI_CODEX_LB_BASE_URL={codex_base_url.rstrip(chr(47))}","-e",f"PI_CODEX_LB_MODEL={codex_model}","-v",f"{secret}:{CODEX_SECRET_TARGET}:ro"]
        argv.append(ref)
        joined = " ".join(argv)
        for forbidden in ("/var/run/docker.sock","unraid-api.key","/mnt/user/appdata/pi-unraid/paseo-home"):
            if forbidden in joined:
                raise ValidationError(f"forbidden production authority: {forbidden}")
        run(argv)
        obj = wait_for_runtime(name)
        cfg, host, mounts = obj.get("Config") or {}, obj.get("HostConfig") or {}, obj.get("Mounts") or []
        if cfg.get("User") != f"{uid}:{gid}":
            raise ValidationError("UID:GID mismatch")
        if host.get("NetworkMode") != network:
            raise ValidationError("validator network mismatch")
        expected_mounts = {"/home/paseo","/projects","/worktrees"} | ({CODEX_SECRET_TARGET} if codex_secret is not None else set())
        if {m.get("Destination") for m in mounts} != expected_mounts:
            raise ValidationError("unexpected mount surface")
        if any(not str(m.get("Source","")).startswith(str(work)) for m in mounts if m.get("Destination") != CODEX_SECRET_TARGET):
            raise ValidationError("non-disposable host mount detected")
        if codex_secret is not None:
            sm=[m for m in mounts if m.get("Destination") == CODEX_SECRET_TARGET]
            if len(sm) != 1 or sm[0].get("RW") is not False: raise ValidationError("Codex-LB credential mount must be read-only")
        env = "\n".join(cfg.get("Env") or []).upper()
        if any(x in env for x in ("UNRAID_API","CODEX_LB_SECRET","GITHUB_TOKEN")):
            raise ValidationError("production/host secret exposed")
        result["checks"].update({"uid_gid":"PASS","mount_isolation":"PASS","network_isolation":"PASS","secret_isolation":"PASS","runtime":"PASS"})
        if codex_secret is not None:
            smoke_cmd = "key=$(cat /run/secrets/pi-unraid-codex-lb); case $key in CODEX_LB_API_KEY=*) key=${key#CODEX_LB_API_KEY=};; esac; test -n \"$key\" || exit 22; body=$(printf '{\"model\":\"%s\",\"input\":\"Reply with OK.\",\"max_output_tokens\":8}' \"$PI_CODEX_LB_MODEL\"); code=$(curl -sS --connect-timeout 2 --max-time 10 -o /tmp/codex-smoke.json -w '%{http_code}' -H \"Authorization: Bearer $key\" -H 'Content-Type: application/json' --data \"$body\" \"${PI_CODEX_LB_BASE_URL%/}/responses\") || exit 20; test \"$code\" = 200 || { test \"$code\" = 401 -o \"$code\" = 403 && exit 21; exit 23; }; node -e 'const x=JSON.parse(require(\"fs\").readFileSync(\"/tmp/codex-smoke.json\",\"utf8\")); if (!x || typeof x !== \"object\" || Array.isArray(x) || typeof x.id !== \"string\" || !x.id) process.exit(1)' || exit 23"
            smoke = run(["docker","exec",name,"sh","-c",smoke_cmd], timeout=30, check=False)
            if smoke.returncode == 20: raise ValidationBlocked("Codex-LB smoke endpoint unavailable")
            if smoke.returncode == 21: raise ValidationError("Codex-LB smoke authentication rejected")
            if smoke.returncode != 0: raise ValidationError("Codex-LB bounded protocol smoke failed")
            result["checks"]["codex_lb_smoke"] = "PASS"
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
    p.add_argument("--codex-secret", type=Path)
    p.add_argument("--codex-base-url")
    p.add_argument("--codex-model")
    a = p.parse_args()
    result = validate(repository=a.repository,digest=a.digest,output=a.output,state_root=a.state_root,uid=a.uid,gid=a.gid,network=a.network,codex_secret=a.codex_secret,codex_base_url=a.codex_base_url,codex_model=a.codex_model)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else (3 if result["status"] == "BLOCKED" else 2)

if __name__ == "__main__":
    raise SystemExit(main())
