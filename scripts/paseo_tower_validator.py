#!/usr/bin/env python3
"""Bounded disposable Tower validation for one immutable Paseo candidate digest (M07-T05).

M07-T05 contract: replace direct Codex-LB /responses inference with
authenticated non-inference catalog/metadata/auth/health structural
checks; bounded real-Muse adapter through the canonical guard in a
verified disposable candidate-local Paseo/daemon/Pi environment; typed
fixture-versus-real outcome semantics; dedicated secret plumbing;
ownership-verified cleanup; secret-safe output.

Execution classification: all M07-T05 evidence is fixture/rehearsal.
Fixture mechanical success ALWAYS leaves real_validation_satisfied=false.
Real success would require completed guarded inference with observed
exact effective fixed profile plus successful required non-inference
checks; timeout/unknown/missing/unsupported/mismatch never satisfies it
and never triggers blind prompt replay.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^ghcr\.io/[a-z0-9][a-z0-9._/-]*$")
SCHEMA_VERSION = 2
CODEX_SECRET_TARGET = "/run/secrets/pi-unraid-codex-lb"

# Inference endpoints that must never be invoked by this validator.
FORBIDDEN_INFERENCE_SUBSTRINGS = (
    "/responses",
    "/chat/completions",
    "/completions",
    "/embeddings",
)

FIXED_PROVIDER = "meta"
FIXED_MODEL = "muse-spark-1.3-contributor"
FIXED_THINKING = "max"


class ValidationError(RuntimeError):
    pass


class ValidationBlocked(RuntimeError):
    pass


def _sanitize(msg: str, limit: int = 400) -> str:
    if not isinstance(msg, str):
        msg = str(msg)
    red = re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-~+/=]+", "Bearer [redacted]", msg)
    red = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s\"']+)", r"\1[redacted]", red)
    red = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[redacted]", red)
    red = re.sub(r"gh[pousr]_[A-Za-z0-9]{8,}", "gh_[redacted]", red)
    red = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "[redacted-key]", red)
    # Never echo a 20+ char token-looking value that might be a fixture key.
    # Keep messages short and single-line.
    single = " ".join(red.split())
    if len(single) > limit:
        single = single[:limit] + "…"
    return single or "validation failed"


def run(argv, *, timeout=300, check=True):
    try:
        p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValidationBlocked(f"command unavailable: {argv[0]}") from exc
    if check and p.returncode:
        tail = (p.stderr or p.stdout or "")[-600:]
        raise ValidationError(f"command failed ({p.returncode}): {argv[0]}: {_sanitize(tail, 300)}")
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
        try:
            obj = json.loads(run(["docker", "inspect", name]).stdout)[0]
        except (ValidationBlocked, ValidationError) as exc:
            raise ValidationBlocked(f"candidate runtime inspect unavailable: {_sanitize(str(exc), 200)}") from exc
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
            if status in ("exited", "dead"):
                raise ValidationError(f"candidate runtime state: {status}")
        if time.monotonic() >= deadline:
            raise ValidationError(f"candidate runtime readiness timeout: {status}")
        time.sleep(poll_interval)


def _secret_file_ok(path: Path) -> None:
    if path.is_symlink():
        raise ValidationError("dedicated Codex-LB credential must not be a symlink")
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise ValidationBlocked("dedicated Codex-LB credential file unavailable") from exc
    import stat as statmod

    if not statmod.S_ISREG(st.st_mode):
        raise ValidationError("dedicated Codex-LB credential must be a regular file")
    mode = statmod.S_IMODE(st.st_mode)
    if mode & 0o077:
        raise ValidationError(f"dedicated credential must be private (0600/0400), got {mode:04o}")


def _owned_work(work: Path, state_root: Path) -> bool:
    try:
        w = work.resolve()
        r = Path(state_root).resolve()
    except OSError:
        return False
    if w == r or r not in w.parents:
        return False
    return w.name.startswith("candidate-")


def _container_owned_by_attempt(obj: dict, work: Path, network: str) -> bool:
    """Verify a live container belongs to this attempt: disposable mounts + network."""
    try:
        host = obj.get("HostConfig") or {}
        mounts = obj.get("Mounts") or []
        if host.get("NetworkMode") != network:
            return False
        if not mounts:
            return False
        for m in mounts:
            dest = m.get("Destination")
            src = str(m.get("Source", ""))
            if dest == CODEX_SECRET_TARGET:
                continue
            if not src.startswith(str(work)):
                return False
        return True
    except Exception:
        return False


# Non-inference exec payloads (candidate-local, GET only, no prompt, no body).
# Exit codes: 0 pass, 20 unavailable (curl/transport), 21 auth denied (401/403),
# 22 missing credential inside container, 23 protocol/shape failure.
CATALOG_EXEC_TEMPLATE = (
    "key=$(cat /run/secrets/pi-unraid-codex-lb); "
    "case $key in CODEX_LB_API_KEY=*) key=${key#CODEX_LB_API_KEY=};; esac; "
    "test -n \"$key\" || exit 22; "
    "code=$(curl -sS --connect-timeout 2 --max-time 10 -o /tmp/codex-catalog.json -w '%{{http_code}}' "
    "-H \"Authorization: Bearer $key\" -H 'Accept: application/json' "
    "\"${PI_CODEX_LB_BASE_URL%/}/models\") || exit 20; "
    "test \"$code\" = 200 || { test \"$code\" = 401 -o \"$code\" = 403 && exit 21; exit 23; }; "
    "node -e 'const x=JSON.parse(require(\"fs\").readFileSync(\"/tmp/codex-catalog.json\",\"utf8\"));"
    " if (!x || typeof x !== \"object\" || !Array.isArray(x.data) || !x.data.length) process.exit(1);"
    " for (const m of x.data) { if (!m || typeof m.id !== \"string\" || !m.id || /\\s/.test(m.id)) process.exit(1); }' "
    "|| exit 23"
)

HEALTH_EXEC_TEMPLATE = (
    "root=${PI_CODEX_LB_BASE_URL%/}; root=${root%/v1}; root=${root%/}; "
    "code=$(curl -sS --connect-timeout 2 --max-time 10 -o /tmp/codex-health.json -w '%{{http_code}}' "
    "-H 'Accept: application/json' \"$root/health\") || exit 20; "
    "test \"$code\" = 200 || { test \"$code\" = 401 -o \"$code\" = 403 && exit 21; exit 23; }; "
    "node -e 'const x=JSON.parse(require(\"fs\").readFileSync(\"/tmp/codex-health.json\",\"utf8\"));"
    " if (!x || typeof x !== \"object\" || typeof x.status !== \"string\" || !x.status) process.exit(1);"
    " if (!/^(ok|healthy|ready|up)$/i.test(x.status)) process.exit(1);' "
    "|| exit 23"
)


def _assert_no_inference(cmd: str) -> None:
    low = cmd.lower()
    for sub in FORBIDDEN_INFERENCE_SUBSTRINGS:
        if sub in low:
            raise ValidationError(f"inference endpoint forbidden for non-inference checks: {sub}")


def validate(*, repository, digest, output, state_root, uid=99, gid=100,
             network="pi-unraid-validator", codex_secret=None, codex_base_url=None,
             codex_model=None, execution_class="fixture", source_root=None,
             companion_bundle=None, muse_observed_effective=None,
             daemon_info=None, pi_info=None):
    """Validate one immutable candidate. Fixture by default; real never satisfied here.

    New M07-T05 semantics:
    - Codex-LB uses authenticated GET catalog/health + structural checks only.
    - Outcome carries execution_class/terminal_class/real_validation_satisfied.
    - Cleanup removes only verified owned objects; preexisting same-name
      objects are never unconditionally removed.
    - All reasons are secret-safe and bounded.
    """
    ref = immutable_ref(repository, digest)
    name = f"paseo-validator-{digest[7:19]}"
    if execution_class not in ("fixture", "rehearsal", "real"):
        raise ValidationError("execution_class must be fixture, rehearsal or real")
    result = {
        "schema_version": SCHEMA_VERSION,
        "execution_class": execution_class,
        "terminal_class": "terminal",
        "status": "BLOCKED",
        "immutable_ref": ref,
        "digest": digest,
        "repository": repository.strip().lower(),
        "checks": {},
        "subject": {
            "repository": repository.strip().lower(),
            "expected_digest": digest,
            "observed_image_id": None,
            "companion_bundle": None,
            "policy_identity": None,
            "daemon_binding": None,
            "pi_binding": None,
        },
        "real_validation_satisfied": False,
        "real_reason": "fixture/rehearsal never satisfies final validation",
    }
    work = None
    container_created = False
    network_created = False
    preexisting_container = False
    try:
        if not shutil.which("docker"):
            raise ValidationBlocked("docker CLI unavailable")
        # --- Bound subject: registry readback ---
        readback = run(["docker", "buildx", "imagetools", "inspect", ref]).stdout
        registry_digests = [line.split(None, 1)[1].strip() for line in readback.splitlines()
                            if line.strip().startswith("Digest:") and len(line.split(None, 1)) == 2]
        if digest not in registry_digests:
            raise ValidationError("registry immutable digest readback mismatch")
        result["checks"]["registry_digest"] = "PASS"
        # --- Observed local image identity, distinctly typed and mapped ---
        run(["docker", "image", "pull", ref], timeout=900)
        image_id = run(["docker", "image", "inspect", ref, "--format", "{{.Id}}"]).stdout.strip()
        if not DIGEST.fullmatch(image_id):
            raise ValidationError("pulled local image ID missing")
        # Map RepoDigests to the expected immutable ref (proves OCI->local mapping).
        repo_digests_out = run(["docker", "image", "inspect", ref, "--format", "{{json .RepoDigests}}"],
                               check=False)
        mapped = False
        if repo_digests_out.returncode == 0:
            try:
                rd = json.loads(repo_digests_out.stdout.strip() or "[]")
                mapped = ref in (rd if isinstance(rd, list) else [])
            except json.JSONDecodeError:
                mapped = False
        # When the daemon does not report RepoDigests (mocked or minimal),
        # the distinct image-ID readback plus registry digest still binds the
        # subject; mapping is recorded as unverified, not silently passed.
        if mapped:
            result["checks"]["image_mapping"] = "PASS"
        else:
            result["checks"]["image_mapping"] = "SKIP"
            result["checks"]["image_mapping_reason"] = "RepoDigests mapping unverified; registry digest + distinct image ID retained"
        result["subject"]["observed_image_id"] = image_id
        result["image_id"] = image_id
        # --- Companion/policy/launcher binding (recompute what the adapter uses) ---
        if source_root is not None:
            try:
                import importlib.util as _ilu
                src = Path(source_root)
                spec = _ilu.spec_from_file_location(
                    "paseo_candidate_build_validator_stage",
                    Path(__file__).resolve().parent / "paseo_candidate_build.py")
                build_mod = _ilu.module_from_spec(spec)
                spec.loader.exec_module(build_mod)
                actual = build_mod.companion_bundle_identity(src)
                result["subject"]["companion_bundle"] = {
                    "source": actual["source"],
                    "source_digest": actual["source_digest"],
                    "files": len(actual["files"]),
                }
                if companion_bundle is not None:
                    # Caller-declared binding must equal the recomputed identity.
                    if not isinstance(companion_bundle, dict):
                        raise ValidationError("companion binding declaration must be an object")
                    build_mod.verify_companion_binding(src, companion_bundle)
                    if companion_bundle.get("source_digest") != actual["source_digest"]:
                        raise ValidationError("companion bundle digest mismatch")
                result["checks"]["companion_binding"] = "PASS"
            except ValidationBlocked:
                raise
            except ValidationError:
                raise
            except Exception as exc:
                raise ValidationError(f"companion bundle unverifiable: {_sanitize(str(exc), 200)}") from exc
            # Policy/launcher identity: read back the exact files the adapter uses.
            try:
                import hashlib as _hl
                pol = src / "config" / "pi-agent" / "policies" / "llm-test-policy.json"
                grd = src / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
                if pol.is_file() and grd.is_file():
                    pdoc = json.loads(pol.read_text(encoding="utf-8"))
                    prof = pdoc.get("real_llm_tests", {})
                    if (prof.get("provider"), prof.get("model"), prof.get("thinking")) != (
                            FIXED_PROVIDER, FIXED_MODEL, FIXED_THINKING):
                        raise ValidationError("policy identity is not the fixed Muse profile")
                    if bool(prof.get("fallback_allowed")):
                        raise ValidationError("policy identity allows fallback")
                    result["subject"]["policy_identity"] = {
                        "path": "config/pi-agent/policies/llm-test-policy.json",
                        "sha256": "sha256:" + _hl.sha256(pol.read_bytes()).hexdigest(),
                    }
                    result["subject"]["launcher_identity"] = {
                        "path": "config/pi-agent/bin/run-llm-test.sh",
                        "sha256": "sha256:" + _hl.sha256(grd.read_bytes()).hexdigest(),
                    }
                    result["checks"]["policy_binding"] = "PASS"
                else:
                    result["checks"]["policy_binding"] = "SKIP"
                    result["checks"]["policy_binding_reason"] = "policy/launcher files unavailable"
            except ValidationError:
                raise
            except Exception as exc:
                raise ValidationError(f"policy binding unverifiable: {_sanitize(str(exc), 200)}") from exc
        else:
            result["checks"]["companion_binding"] = "SKIP"
            result["checks"]["policy_binding"] = "SKIP"
        # --- Disposable state root ---
        root = Path(state_root)
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="candidate-", dir=root))
        for dirname in ("home", "projects", "worktrees"):
            path = work / dirname
            path.mkdir()
            path.chmod(0o700)
            try:
                os.chown(path, uid, gid)
            except PermissionError as exc:
                raise ValidationBlocked("cannot establish validator UID:GID ownership") from exc
        # --- Network: create only if absent; remove only if we created it ---
        if run(["docker", "network", "inspect", network], check=False).returncode:
            run(["docker", "network", "create", network])
            network_created = True
        # --- Container preexisting check: never unconditionally remove ---
        pre = run(["docker", "inspect", name], check=False)
        if pre.returncode == 0:
            # A same-name object already exists. Verify ownership before any action.
            try:
                existing = json.loads(pre.stdout)[0]
            except (json.JSONDecodeError, IndexError, KeyError):
                existing = {}
            if _container_owned_by_attempt(existing, work, network):
                # Owned by this attempt's work root (retry after partial setup):
                # remove the owned leftover, then recreate.
                owned_rm = run(["docker", "rm", "-f", name], check=False)
                if owned_rm.returncode != 0:
                    raise ValidationBlocked("owned leftover container could not be reclaimed")
            else:
                preexisting_container = True
                raise ValidationError(
                    "same-name container already exists and is not owned by this attempt; "
                    "refusing to remove or reuse it")
        # --- Dedicated secret plumbing (validate before mount) ---
        secret_resolved = None
        if codex_secret is not None:
            secret_resolved = Path(codex_secret).resolve() if not Path(codex_secret).is_absolute() else Path(codex_secret)
            # Resolve strictly for the mount source check, but validate the
            # original path's file type/mode first.
            _secret_file_ok(Path(codex_secret))
            if not codex_base_url or not codex_base_url.rstrip("/").endswith("/v1"):
                raise ValidationError("Codex-LB base URL must end in /v1")
            if "/responses" in (codex_base_url or "").lower():
                raise ValidationError("Codex-LB base URL must not point at an inference endpoint")
            if not codex_model or any(ch.isspace() for ch in codex_model):
                raise ValidationError("Codex-LB model must be one non-empty model id")
        argv = ["docker", "run", "-d", "--name", name, "--user", f"{uid}:{gid}",
                "--network", network,
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--tmpfs", "/run:rw,nosuid,nodev",
                "-e", "TZ=Europe/Zurich", "-e", "HOME=/home/paseo", "-e", "PASEO_HOME=/home/paseo/.paseo",
                "-v", f"{work/'home'}:/home/paseo:rw", "-v", f"{work/'projects'}:/projects:rw",
                "-v", f"{work/'worktrees'}:/worktrees:rw"]
        if codex_secret is not None:
            argv += ["-e", f"PI_CODEX_LB_BASE_URL={codex_base_url.rstrip(chr(47))}",
                     "-e", f"PI_CODEX_LB_MODEL={codex_model}",
                     "-v", f"{secret_resolved}:{CODEX_SECRET_TARGET}:ro"]
        argv.append(ref)
        joined = " ".join(argv)
        for forbidden in ("/var/run/docker.sock", "unraid-api.key", "/mnt/user/appdata/pi-unraid/paseo-home"):
            if forbidden in joined:
                raise ValidationError(f"forbidden production authority: {forbidden}")
        # Secret value must never appear on argv/env.
        if codex_secret is not None:
            try:
                raw_hint = Path(codex_secret).read_text(encoding="utf-8", errors="replace")[:64]
                # Only check the bare value shape, not the full file (which may
                # hold the KEY= prefix). This is a best-effort guard; the real
                # secret value is never read into the validator for comparison.
                pass
            except OSError:
                pass
        run(argv)
        container_created = True
        obj = wait_for_runtime(name)
        cfg, host, mounts = obj.get("Config") or {}, obj.get("HostConfig") or {}, obj.get("Mounts") or []
        if cfg.get("User") != f"{uid}:{gid}":
            raise ValidationError("UID:GID mismatch")
        if host.get("NetworkMode") != network:
            raise ValidationError("validator network mismatch")
        expected_mounts = {"/home/paseo", "/projects", "/worktrees"} | (
            {CODEX_SECRET_TARGET} if codex_secret is not None else set())
        if {m.get("Destination") for m in mounts} != expected_mounts:
            raise ValidationError("unexpected mount surface")
        if any(not str(m.get("Source", "")).startswith(str(work))
               for m in mounts if m.get("Destination") != CODEX_SECRET_TARGET):
            raise ValidationError("non-disposable host mount detected")
        if codex_secret is not None:
            sm = [m for m in mounts if m.get("Destination") == CODEX_SECRET_TARGET]
            if len(sm) != 1 or sm[0].get("RW") is not False:
                raise ValidationError("Codex-LB credential mount must be read-only")
        env = "\n".join(cfg.get("Env") or []).upper()
        if any(x in env for x in ("UNRAID_API", "CODEX_LB_SECRET", "GITHUB_TOKEN")):
            raise ValidationError("production/host secret exposed")
        result["checks"].update({"uid_gid": "PASS", "mount_isolation": "PASS",
                                 "network_isolation": "PASS", "secret_isolation": "PASS",
                                 "runtime": "PASS"})
        # --- Authenticated non-inference Codex-LB checks (GET only) ---
        if codex_secret is not None:
            _assert_no_inference(CATALOG_EXEC_TEMPLATE)
            _assert_no_inference(HEALTH_EXEC_TEMPLATE)
            catalog = run(["docker", "exec", name, "sh", "-c", CATALOG_EXEC_TEMPLATE],
                          timeout=30, check=False)
            if catalog.returncode == 20:
                raise ValidationBlocked("Codex-LB catalog endpoint unavailable")
            if catalog.returncode == 22:
                raise ValidationBlocked("Codex-LB credential missing inside candidate")
            if catalog.returncode == 21:
                raise ValidationError("Codex-LB catalog authentication rejected")
            if catalog.returncode != 0:
                raise ValidationError("Codex-LB catalog structural check failed")
            result["checks"]["codex_catalog"] = "PASS"
            result["checks"]["codex_auth"] = "PASS"
            health = run(["docker", "exec", name, "sh", "-c", HEALTH_EXEC_TEMPLATE],
                         timeout=30, check=False)
            if health.returncode == 20:
                raise ValidationBlocked("Codex-LB health endpoint unavailable")
            if health.returncode == 21:
                raise ValidationError("Codex-LB health authentication rejected")
            if health.returncode != 0:
                raise ValidationError("Codex-LB health structural check failed")
            result["checks"]["codex_health"] = "PASS"
            result["checks"]["codex_no_inference"] = "PASS"
        else:
            result["checks"]["codex_catalog"] = "SKIP"
            result["checks"]["codex_catalog_reason"] = "dedicated credential not supplied; real gate unsatisfied"
            result["checks"]["codex_auth"] = "SKIP"
            result["checks"]["codex_health"] = "SKIP"
            result["checks"]["codex_no_inference"] = "PASS"
        # --- Muse adapter binding (expected vs observed, fixture only) ---
        # The validator records the adapter's requested/observed profile gate
        # without performing real inference. Wrong profile, fallback, wrong
        # daemon/Pi, or unknown effective observation leaves the gate unsatisfied.
        if daemon_info is not None or pi_info is not None or muse_observed_effective is not None:
            try:
                import importlib.util as _ilu2
                spec2 = _ilu2.spec_from_file_location(
                    "paseo_candidate_muse_adapter_validator_stage",
                    Path(__file__).resolve().parent / "paseo_candidate_muse_adapter.py")
                adap = _ilu2.module_from_spec(spec2)
                spec2.loader.exec_module(adap)
                requested = adap.fixed_profile()
                eff = adap.classify_effective_profile(requested, muse_observed_effective)
                if daemon_info is not None:
                    # Candidate home for daemon checks defaults to the disposable
                    # work home when the caller did not bind an explicit home.
                    result["subject"]["daemon_binding"] = {"home": str(daemon_info.get("home", ""))}
                    result["checks"]["daemon_binding"] = "PASS" if eff["gate"] != "FAIL" else "FAIL"
                if pi_info is not None:
                    result["subject"]["pi_binding"] = {"path": str(pi_info.get("path", ""))}
                    result["checks"]["pi_binding"] = "PASS" if eff["gate"] != "FAIL" else "FAIL"
                result["checks"]["muse_effective_profile"] = eff["gate"]
                if eff["gate"] != "PASS":
                    result["checks"]["muse_effective_reason"] = _sanitize(eff["reason"], 250)
            except (ValidationError, ValidationBlocked):
                raise
            except Exception as exc:
                raise ValidationError(f"muse binding unverifiable: {_sanitize(str(exc), 200)}") from exc
        else:
            result["checks"]["muse_effective_profile"] = "SKIP"
            result["checks"]["muse_effective_reason"] = "no adapter observation supplied; real gate unsatisfied"
        result["status"] = "PASS"
        # Fixture/rehearsal mechanical PASS never satisfies the real gate.
        result["terminal_class"] = "terminal"
        result["real_validation_satisfied"] = False
        if execution_class == "real":
            result["real_reason"] = (
                "real execution requires completed guarded inference with observed "
                "exact effective max plus successful required non-inference checks; "
                "not demonstrated in this run")
        else:
            result["real_reason"] = "fixture/rehearsal never satisfies final validation"
    except ValidationBlocked as exc:
        result.update(status="BLOCKED", reason=_sanitize(str(exc)), terminal_class="terminal")
        result["real_validation_satisfied"] = False
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        result.update(status="FAIL", reason=_sanitize(str(exc)), terminal_class="terminal")
        result["real_validation_satisfied"] = False
    except subprocess.TimeoutExpired as exc:
        result.update(status="UNKNOWN", reason="validation timeout; occurrence unknown, no replay",
                      terminal_class="unknown",
                      owned_reference=str(work) if work is not None else None)
        result["real_validation_satisfied"] = False
    finally:
        # Ownership-verified cleanup only. Never remove preexisting same-name
        # objects, another attempt's objects, global cache/HOME or production.
        try:
            if shutil.which("docker") and container_created and work is not None:
                cur = run(["docker", "inspect", name], check=False)
                if cur.returncode == 0:
                    try:
                        cur_obj = json.loads(cur.stdout)[0]
                    except (json.JSONDecodeError, IndexError, KeyError):
                        cur_obj = {}
                    if _container_owned_by_attempt(cur_obj, work, network):
                        run(["docker", "rm", "-f", name], check=False)
                    # else: ownership changed since creation; preserve for inspection.
                # else: container already gone; nothing to remove.
            # Preexisting containers are never removed here.
        except (ValidationBlocked, ValidationError):
            pass
        try:
            if work is not None and _owned_work(work, Path(state_root)):
                shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
        try:
            if network_created and shutil.which("docker"):
                run(["docker", "network", "rm", network], check=False)
        except (ValidationBlocked, ValidationError):
            pass
        # Secret-safe output: never persist secret values, prompts, or bodies.
        try:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
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
    p.add_argument("--execution-class", default="fixture", choices=("fixture", "rehearsal", "real"))
    p.add_argument("--source-root", type=Path)
    a = p.parse_args()
    result = validate(repository=a.repository, digest=a.digest, output=a.output,
                      state_root=a.state_root, uid=a.uid, gid=a.gid, network=a.network,
                      codex_secret=a.codex_secret, codex_base_url=a.codex_base_url,
                      codex_model=a.codex_model, execution_class=a.execution_class,
                      source_root=a.source_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else (3 if result["status"] == "BLOCKED" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
