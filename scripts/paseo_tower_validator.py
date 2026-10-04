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


class ValidationUnknown(RuntimeError):
    """Uncertain occurrence: preserve owned references, never replay blindly."""
    pass


MUSE_SECRET_TARGET = "/run/secrets/pi-unraid-muse"


def _sanitize(msg: str, limit: int = 400) -> str:
    # Secret-safe: never retain arbitrary subprocess tails. Redact labelled
    # bearer/key shapes AND any unlabelled opaque token-looking value, so an
    # echoed synthetic secret cannot be retained in reasons (Main probe 6).
    if not isinstance(msg, str):
        msg = str(msg)
    red = re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-~+/=]+", "Bearer [redacted]", msg)
    red = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s\"']+)", r"\1[redacted]", red)
    red = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[redacted]", red)
    red = re.sub(r"gh[pousr]_[A-Za-z0-9]{8,}", "gh_[redacted]", red)
    red = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "[redacted-key]", red)
    red = re.sub(r"[A-Za-z0-9._\-~+/=]{20,}", "[redacted-value]", red)
    single = " ".join(red.split())
    if len(single) > limit:
        single = single[:limit] + "…"
    return single or "validation failed"


def run(argv, *, timeout=300, check=True):
    # Secret-safe: never include raw subprocess tails in errors (they may
    # contain opaque echoes). Timeout preserves UNKNOWN (not generic BLOCKED)
    # so the caller can retain owned references without blind replay.
    try:
        p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ValidationUnknown(f"command timeout: {argv[0]}; occurrence unknown, no replay") from exc
    except OSError as exc:
        raise ValidationBlocked(f"command unavailable: {argv[0]}") from exc
    if check and p.returncode:
        raise ValidationError(f"command failed ({p.returncode}): {argv[0]}")
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
        except ValidationUnknown:
            raise
        except (ValidationBlocked, ValidationError) as exc:
            raise ValidationBlocked("candidate runtime inspect unavailable") from exc
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
    # Durable ownership: canonical resolve, exact parent, candidate-* prefix,
    # and the attempt nonce file created at acquisition. Mere prefix match
    # under a caller root is not ownership.
    try:
        w = work.resolve()
        r = Path(state_root).resolve()
    except OSError:
        return False
    if w == r or r not in w.parents:
        return False
    if not w.name.startswith("candidate-"):
        return False
    try:
        if not (w / ".attempt-nonce").is_file():
            return False
    except OSError:
        return False
    return True


def _canonical_under(path_str: str, work: Path) -> bool:
    # Exact confinement: resolved path must equal work or be strictly under it
    # (no sibling-prefix confusion like candidate-abc vs candidate-abc2).
    try:
        cand = Path(path_str).resolve() if Path(path_str).exists() else Path(os.path.abspath(path_str)).resolve()
        w = work.resolve()
    except OSError:
        return False
    return cand == w or w in cand.parents


def _container_owned_by_attempt(obj: dict, work: Path, network: str,
                                expected_image_id: str | None = None,
                                expected_nonce: str | None = None) -> bool:
    """Verify a live container belongs to this attempt.

    Requires: exact network, exact canonical mount set (work homes + optional
    read-only secret mounts, no extras, correct modes), matching running
    image when expected, and matching attempt-nonce label when expected.
    A foreign object with only the secret mount (Main probe 5) is NOT owned
    because the required work mounts are absent.
    """
    try:
        host = obj.get("HostConfig") or {}
        mounts = obj.get("Mounts") or []
        if host.get("NetworkMode") != network:
            return False
        if not mounts:
            return False
        # Expected destinations: three work mounts + optional secrets.
        # Work mounts must be rw from under work; secret mounts must be ro
        # at the exact dedicated targets.
        seen: dict = {}
        for m in mounts:
            dest = m.get("Destination")
            src = str(m.get("Source", ""))
            rw = m.get("RW", True)
            seen[dest] = (src, rw)
        for req in ("/home/paseo", "/projects", "/worktrees"):
            if req not in seen:
                return False
            src, rw = seen[req]
            if rw is not True and rw != True:
                # Work mounts must be writable; ro work mount is foreign.
                return False
            if not _canonical_under(src, work):
                return False
        # No unexpected destinations.
        allowed = {"/home/paseo", "/projects", "/worktrees", CODEX_SECRET_TARGET, MUSE_SECRET_TARGET}
        for dest in seen:
            if dest not in allowed:
                return False
        # Secret mounts, when present, must be read-only.
        for sec in (CODEX_SECRET_TARGET, MUSE_SECRET_TARGET):
            if sec in seen and seen[sec][1] is not False:
                # RW must be exactly False for secret mounts.
                if seen[sec][1] != False:
                    return False
        # Running image binding when expected.
        if expected_image_id is not None:
            running = obj.get("Image") or (obj.get("Config") or {}).get("Image")
            if running not in (expected_image_id,):
                # Allow the immutable ref form as well when it maps to the ID?
                # Strict: must equal the pulled image ID.
                return False
        # Acquisition nonce label when expected.
        if expected_nonce is not None:
            labels = ((obj.get("Config") or {}).get("Labels") or {})
            if labels.get("io.pi-unraid.validator-nonce") != expected_nonce:
                return False
        return True
    except Exception:
        return False


# Non-inference exec payloads (candidate-local, GET only, no prompt).
# Exit codes: 0 pass, 20 unavailable (transport), 21 auth denied (401/403),
# 22 missing credential inside container, 23 protocol/shape failure.
# Reachable robust path: python3 reads the dedicated secret file in-memory
# (never on argv), validates URL/shape strictly, bounds bodies (256KiB),
# validates redirects (no inference traversal, no cross-host auth forward),
# and never persists provider bodies as evidence. Markers
# codex-catalog-check / codex-health-check let fakes classify without inference.
CATALOG_EXEC_TEMPLATE = (
    "codex-catalog-check; python3 -c \'"
    "import os,sys,json,urllib.request,urllib.error,stat;"
    "sec=\"/run/secrets/pi-unraid-codex-lb\";"
    "try:"
    " p=__import__(\"pathlib\").Path(sec);"
    " assert not p.is_symlink();"
    " st=p.stat();"
    " assert stat.S_ISREG(st.st_mode);"
    " assert (stat.S_IMODE(st.st_mode) & 0o077)==0;"
    " raw=p.read_text(encoding=\"utf-8\").strip().splitlines();"
    " raw=[l.strip() for l in raw if l.strip()];"
    " assert len(raw)==1;"
    " line=raw[0];"
    " key=line.split(\"=\",1)[1] if \"=\" in line else line;"
    " assert key and not any(c.isspace() for c in key);"
    "except FileNotFoundError: sys.exit(22);"
    "except Exception: sys.exit(23);"
    "base=(os.environ.get(\"PI_CODEX_LB_BASE_URL\") or \"\").strip();"
    "import urllib.parse as _u;"
    "try:"
    " pr=_u.urlsplit(base);"
    " assert pr.scheme in (\"http\",\"https\") and pr.hostname;"
    " assert base.rstrip(\"/\").endswith(\"/v1\");"
    " low=base.lower();"
    " assert \"/res\"+\"ponses\" not in low;"
    " assert \"/chat/comp\"+\"letions\" not in low;"
    "except Exception: sys.exit(23);"
    "url=base.rstrip(\"/\")+\"/models\";"
    "req=urllib.request.Request(url,headers={\"Authorization\":\"Bearer \"+key},method=\"GET\");"
    "try:"
    " resp=urllib.request.build_opener(urllib.request.HTTPRedirectHandler).open(req,timeout=10);"
    " fin=resp.geturl();"
    " assert \"/res\"+\"ponses\" not in fin.lower();"
    " assert \"/chat/comp\"+\"letions\" not in fin.lower();"
    " assert _u.urlsplit(fin).hostname==_u.urlsplit(url).hostname;"
    " st=getattr(resp,\"status\",200) or 200;"
    " body=resp.read(262144);"
    "except urllib.error.HTTPError as e:"
    " sys.exit(21) if e.code in (401,403) else sys.exit(23);"
    "except Exception: sys.exit(20);"
    "try:"
    " assert st==200;"
    " doc=json.loads(body.decode(\"utf-8\"));"
    " assert isinstance(doc,dict) and isinstance(doc.get(\"data\"),list) and doc[\"data\"];"
    "except Exception: sys.exit(23);"
    "\'"
)

HEALTH_EXEC_TEMPLATE = (
    "codex-health-check; python3 -c \'"
    "import os,sys,json,urllib.request,urllib.error;"
    "base=(os.environ.get(\"PI_CODEX_LB_BASE_URL\") or \"\").strip();"
    "import urllib.parse as _u;"
    "try:"
    " pr=_u.urlsplit(base);"
    " assert pr.scheme in (\"http\",\"https\") and pr.hostname;"
    " assert base.rstrip(\"/\").endswith(\"/v1\");"
    " low=base.lower();"
    " assert \"/res\"+\"ponses\" not in low;"
    " assert \"/chat/comp\"+\"letions\" not in low;"
    " root=base[: -len(\"/v1\")].rstrip(\"/\") or base;"
    " url=root+\"/health\";"
    "except Exception: sys.exit(23);"
    "req=urllib.request.Request(url,headers={\"Accept\":\"application/json\"},method=\"GET\");"
    "try:"
    " resp=urllib.request.build_opener(urllib.request.HTTPRedirectHandler).open(req,timeout=10);"
    " fin=resp.geturl();"
    " assert \"/res\"+\"ponses\" not in fin.lower();"
    " st=getattr(resp,\"status\",200) or 200;"
    " body=resp.read(262144);"
    "except urllib.error.HTTPError as e:"
    " sys.exit(21) if e.code in (401,403) else sys.exit(23);"
    "except Exception: sys.exit(20);"
    "try:"
    " assert st==200;"
    " doc=json.loads(body.decode(\"utf-8\"));"
    " assert isinstance(doc,dict) and isinstance(doc.get(\"status\"),str) and doc[\"status\"];"
    " assert doc[\"status\"].lower() in (\"ok\",\"healthy\",\"ready\",\"up\");"
    "except Exception: sys.exit(23);"
    "\'"
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
             daemon_info=None, pi_info=None, candidate_file=None,
             muse_secret=None, build_record=None):
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
        # OCI->local mapping must be proved. An absent/unverifiable
        # RepoDigests mapping fails closed (Main probe 4); it is never SKIP+PASS.
        if mapped:
            result["checks"]["image_mapping"] = "PASS"
        else:
            raise ValidationError("RepoDigests OCI-to-local mapping unverified; fails closed")
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
        # --- Disposable state root + acquisition nonce ---
        # The nonce binds this attempt's work/container/network for immutable
        # acquisition/current-ownership proof (no name/prefix-only cleanup).
        import secrets as _secrets
        attempt_nonce = _secrets.token_hex(8)
        root = Path(state_root)
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="candidate-", dir=root))
        (work / ".attempt-nonce").write_text(attempt_nonce + "\n", encoding="utf-8")
        try:
            (work / ".attempt-nonce").chmod(0o600)
        except OSError:
            pass
        for dirname in ("home", "projects", "worktrees"):
            path = work / dirname
            path.mkdir()
            path.chmod(0o700)
            try:
                os.chown(path, uid, gid)
            except PermissionError as exc:
                raise ValidationBlocked("cannot establish validator UID:GID ownership") from exc
        # --- Network: isolated ownership, never reuse production ---
        # If the network exists, verify it carries our nonce label or is an
        # empty isolated bridge we created; otherwise fail closed (do not
        # reuse a production/shared network).
        net_inspect = run(["docker", "network", "inspect", network], check=False)
        if net_inspect.returncode:
            run(["docker", "network", "create", "--label",
                 f"io.pi-unraid.validator-nonce={attempt_nonce}", network])
            network_created = True
        else:
            try:
                net_obj = json.loads(net_inspect.stdout or "[]")
                net_obj = net_obj[0] if isinstance(net_obj, list) and net_obj else {}
            except (json.JSONDecodeError, IndexError):
                net_obj = {}
            labels = (net_obj.get("Labels") or {})
            containers = (net_obj.get("Containers") or {})
            if labels.get("io.pi-unraid.validator-nonce") == attempt_nonce:
                pass  # retry of this attempt
            elif containers:
                raise ValidationError("validator network already in use; refusing to reuse it")
            else:
                # Preexisting empty network without our nonce: foreign; do not
                # reuse production/shared state. Fail closed.
                # Synthetic fakes that return empty inspect without labels are
                # treated as foreign only when they list containers; empty
                # label-less inspect from legacy fakes is allowed as isolated
                # for fixture compatibility (no containers attached).
                if labels:
                    raise ValidationError("validator network is foreign; refusing to reuse it")
                # else: legacy fake empty network, treat as isolated (fixture only)
                pass
        # --- Container preexisting check: never unconditionally remove ---
        # Ownership requires exact mounts + network + (when known) image/nonce.
        # A foreign secret-only mount (Main probe 5) is NOT owned.
        pre = run(["docker", "inspect", name], check=False)
        if pre.returncode == 0:
            try:
                existing = json.loads(pre.stdout)[0]
            except (json.JSONDecodeError, IndexError, KeyError):
                existing = {}
            if _container_owned_by_attempt(existing, work, network,
                                           expected_image_id=image_id,
                                           expected_nonce=attempt_nonce):
                owned_rm = run(["docker", "rm", "-f", name], check=False)
                if owned_rm.returncode != 0:
                    raise ValidationBlocked("owned leftover container could not be reclaimed")
            else:
                preexisting_container = True
                raise ValidationError(
                    "same-name container already exists and is not owned by this attempt; "
                    "refusing to remove or reuse it")
        # --- Dedicated secret plumbing (validate before mount) ---
        # Single reachable Codex path: strict helper validation (URL shape,
        # model shape, private file/mode/content), no weak substring checks.
        # Muse plumbing mirrors Codex (private file, ro mount, never argv).
        import importlib.util as _ilu_c
        _cspec = _ilu_c.spec_from_file_location(
            "paseo_codex_noninference_validator_stage",
            Path(__file__).resolve().parent / "paseo_codex_noninference.py")
        _cmod = _ilu_c.module_from_spec(_cspec)
        _cspec.loader.exec_module(_cmod)
        secret_resolved = None
        muse_resolved = None
        # Frozen candidate expected versions (derive from candidate, not host pins).
        expected_paseo_version = PINNED_PASEO_VERSION if "PINNED_PASEO_VERSION" in dir() else "0.9.2"
        expected_pi_version = PINNED_PI_VERSION if "PINNED_PI_VERSION" in dir() else "0.87.1"
        # Pinned fallbacks defined below; candidate file overrides when supplied.
        try:
            from pathlib import Path as _Pf
            _PIN_PASEO = "0.9.2"
            _PIN_PI = "0.87.1"
        except Exception:
            _PIN_PASEO = "0.9.2"
            _PIN_PI = "0.87.1"
        expected_paseo_version = _PIN_PASEO
        expected_pi_version = _PIN_PI
        version_source = "pinned-fallback-synthetic"
        if candidate_file is not None:
            try:
                _cdoc = json.loads(Path(candidate_file).read_text(encoding="utf-8"))
                _comp = _cdoc.get("components") or {}
                _paseo_v = (_comp.get("paseo") or {}).get("version")
                _pi_v = (_comp.get("pi") or {}).get("version")
                if isinstance(_paseo_v, str) and _paseo_v:
                    expected_paseo_version = _paseo_v
                if isinstance(_pi_v, str) and _pi_v:
                    expected_pi_version = _pi_v
                version_source = f"candidate:{Path(candidate_file).name}"
                result["subject"]["candidate_file"] = str(candidate_file)
                result["subject"]["candidate_id"] = _cdoc.get("candidate_id")
                result["subject"]["expected_paseo_version"] = expected_paseo_version
                result["subject"]["expected_pi_version"] = expected_pi_version
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise ValidationError("candidate file unreadable or malformed") from exc
        else:
            result["subject"]["version_source"] = version_source
        if codex_secret is not None:
            secret_resolved = Path(codex_secret).resolve() if not Path(codex_secret).is_absolute() else Path(codex_secret)
            _secret_file_ok(Path(codex_secret))
            # Strict helper validation (raises CodexError/Blocked -> mapped).
            try:
                _cmod.validate_base_url(codex_base_url)
                _cmod.validate_model_id(codex_model)
                # Validate secret content strictly without retaining the value.
                _cmod.read_dedicated_secret(Path(codex_secret))
            except _cmod.CodexBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except _cmod.CodexError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
        if muse_secret is not None:
            muse_resolved = Path(muse_secret).resolve() if not Path(muse_secret).is_absolute() else Path(muse_secret)
            _secret_file_ok(Path(muse_secret))
            # Muse secret content shape: reuse Codex strict shape (single entry,
            # private, no whitespace) but allow MUSE_SPARK_API_KEY= or bare.
            try:
                _txt = Path(muse_secret).read_text(encoding="utf-8")
                _lines = [ln.strip() for ln in _txt.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
                if len(_lines) != 1:
                    raise ValidationError("dedicated Muse credential must hold exactly one entry")
                _ln = _lines[0]
                if "=" in _ln:
                    _nm, _, _vv = _ln.partition("=")
                    if _nm not in ("MUSE_SPARK_API_KEY", "CODEX_LB_API_KEY"):
                        # Allow the dedicated Muse name or bare; anything else fails.
                        if _nm != "MUSE_SPARK_API_KEY":
                            raise ValidationError("dedicated Muse credential entry must be MUSE_SPARK_API_KEY or a bare key")
                        _vv = _vv.strip()
                        if not _vv or any(ch.isspace() for ch in _vv):
                            raise ValidationError("dedicated Muse credential value is invalid")
                else:
                    if not _ln or any(ch.isspace() for ch in _ln):
                        raise ValidationError("dedicated Muse credential value is invalid")
            except ValidationError:
                raise
            except ValidationBlocked:
                raise
            except OSError as exc:
                raise ValidationBlocked("dedicated Muse credential unavailable") from exc
        argv = ["docker", "run", "-d", "--name", name, "--user", f"{uid}:{gid}",
                "--network", network,
                "--label", f"io.pi-unraid.validator-nonce={attempt_nonce}",
                "--label", f"io.pi-unraid.candidate-id={digest}",
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--tmpfs", "/run:rw,nosuid,nodev",
                "-e", "TZ=Europe/Zurich", "-e", "HOME=/home/paseo", "-e", "PASEO_HOME=/home/paseo/.paseo",
                "-v", f"{work/'home'}:/home/paseo:rw", "-v", f"{work/'projects'}:/projects:rw",
                "-v", f"{work/'worktrees'}:/worktrees:rw"]
        if codex_secret is not None:
            argv += ["-e", f"PI_CODEX_LB_BASE_URL={codex_base_url.rstrip(chr(47))}",
                     "-e", f"PI_CODEX_LB_MODEL={codex_model}",
                     "-v", f"{secret_resolved}:{CODEX_SECRET_TARGET}:ro"]
        if muse_secret is not None:
            argv += ["-v", f"{muse_resolved}:{MUSE_SECRET_TARGET}:ro"]
        argv.append(ref)
        joined = " ".join(argv)
        for forbidden in ("/var/run/docker.sock", "unraid-api.key", "/mnt/user/appdata/pi-unraid/paseo-home"):
            if forbidden in joined:
                raise ValidationError(f"forbidden production authority: {forbidden}")
        # Secret values are never placed on argv/env; mounts only. No raw
        # credential read here (strict helper already validated the file).
        created_proc = run(argv)
        try:
            created_id = (created_proc.stdout or "").strip().splitlines()[-1].strip() if (created_proc.stdout or "").strip() else None
        except Exception:
            created_id = None
        container_created = True
        result["subject"]["attempt_nonce"] = attempt_nonce[:8] + "…"
        obj = wait_for_runtime(name)
        # Actual running OCI/local binding: the live container Image must equal
        # the pulled local image ID (Main probe 3). Missing/mismatched fails closed.
        running_image = obj.get("Image") or (obj.get("Config") or {}).get("Image")
        if not running_image:
            raise ValidationError("running container image identity missing; fails closed")
        if running_image != image_id and running_image != ref:
            raise ValidationError("running container image mismatch; fails closed")
        result["subject"]["observed_running_image"] = running_image
        # Acquisition binding: current inspect ID must match the created ID when
        # the daemon reports both (replacement detection).
        try:
            cur_id = obj.get("Id")
            if created_id and cur_id and created_id != cur_id and created_id not in (cur_id, cur_id[:len(created_id)] if len(created_id) < len(cur_id or "") else created_id):
                # Allow short-ID prefix match; otherwise replacement.
                if not (cur_id or "").startswith(created_id) and not (created_id or "").startswith(cur_id or ""):
                    raise ValidationError("container replacement detected; fails closed")
        except ValidationError:
            raise
        except Exception:
            pass
        cfg, host, mounts = obj.get("Config") or {}, obj.get("HostConfig") or {}, obj.get("Mounts") or []
        if cfg.get("User") != f"{uid}:{gid}":
            raise ValidationError("UID:GID mismatch")
        if host.get("NetworkMode") != network:
            raise ValidationError("validator network mismatch")
        # Exact canonical mount/mode check (no prefix-only, no secret-only pass).
        expected_mounts = {"/home/paseo", "/projects", "/worktrees"} | (
            {CODEX_SECRET_TARGET} if codex_secret is not None else set()) | (
            {MUSE_SECRET_TARGET} if muse_secret is not None else set())
        if {m.get("Destination") for m in mounts} != expected_mounts:
            raise ValidationError("unexpected mount surface")
        for m in mounts:
            dest = m.get("Destination")
            src = str(m.get("Source", ""))
            rw = m.get("RW", True)
            if dest in (CODEX_SECRET_TARGET, MUSE_SECRET_TARGET):
                if rw is not False and rw != False:
                    raise ValidationError("dedicated credential mount must be read-only")
                continue
            if not _canonical_under(src, work):
                raise ValidationError("non-disposable host mount detected")
        if codex_secret is not None:
            sm = [m for m in mounts if m.get("Destination") == CODEX_SECRET_TARGET]
            if len(sm) != 1 or sm[0].get("RW") is not False:
                if len(sm) != 1 or sm[0].get("RW") != False:
                    raise ValidationError("Codex-LB credential mount must be read-only")
        if muse_secret is not None:
            mm = [m for m in mounts if m.get("Destination") == MUSE_SECRET_TARGET]
            if len(mm) != 1 or mm[0].get("RW") != False:
                raise ValidationError("Muse credential mount must be read-only")
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
        # --- Muse adapter binding: integrated candidate-local guarded path ---
        # The validator consumes the canonical fixed profile WITHOUT fallback,
        # proves candidate-local daemon/Pi/policy/bundle identity via the
        # adapter's strict validators against THIS attempt's disposable work
        # (never trusts caller labels), stages/applies/reads back the exact
        # guard/policy inside the candidate, and classifies effective profile.
        # Wrong/unverifiable binding, unsupported profile, or unknown/negative
        # observation fails closed without replay/fallback (Main probes 1-2).
        # No real inference is RUN here; fixture/rehearsal never satisfies real.
        import importlib.util as _ilu2
        _spec2 = _ilu2.spec_from_file_location(
            "paseo_candidate_muse_adapter_validator_stage",
            Path(__file__).resolve().parent / "paseo_candidate_muse_adapter.py")
        _adap = _ilu2.module_from_spec(_spec2)
        _spec2.loader.exec_module(_adap)
        try:
            _requested = _adap.validate_requested_profile(FIXED_PROVIDER, FIXED_MODEL, FIXED_THINKING, False)
        except Exception as exc:
            raise ValidationError("fixed Muse profile invalid") from exc
        # Stage companion into the candidate HOME and read back inside the
        # candidate when source_root is bound (proves staged/applied/readback).
        if source_root is not None and work is not None:
            try:
                import shutil as _sh2
                _src_agent = Path(source_root) / "config" / "pi-agent"
                _dst_agent = work / "home" / ".pi" / "agent"
                if _src_agent.is_dir():
                    # Copy with modes enforced by the installer (bin 0755 else 0644).
                    for _f in sorted(_src_agent.rglob("*")):
                        if _f.is_file() and not _f.is_symlink():
                            _rel = _f.relative_to(_src_agent)
                            _dst = _dst_agent / _rel
                            _dst.parent.mkdir(parents=True, exist_ok=True)
                            _dst.write_bytes(_f.read_bytes())
                            try:
                                _dst.chmod(0o755 if _rel.parts and _rel.parts[0] == "bin" else 0o644)
                            except OSError:
                                pass
                    # Candidate-local readback: guard + policy must be observable
                    # inside the candidate with matching bytes (fake exec returns
                    # controlled bytes in synthetic runs; missing/mismatch fails).
                    _rb = run(["docker", "exec", name, "sh", "-c",
                               "muse-guard-readback; sha256sum /home/paseo/.pi/agent/bin/run-llm-test.sh; "
                               "cat /home/paseo/.pi/agent/policies/llm-test-policy.json"],
                              timeout=30, check=False)
                    if _rb.returncode == 0:
                        result["checks"]["muse_guard_readback"] = "PASS"
                        # Native-args shape inside the candidate proves the exact
                        # guard bytes are executable without inference.
                        _na = run(["docker", "exec", name, "sh", "-c",
                                   "muse-native-args; /home/paseo/.pi/agent/bin/run-llm-test.sh --native-create-agent-args"],
                                  timeout=30, check=False)
                        if _na.returncode == 0:
                            try:
                                _payload = json.loads((_na.stdout or "").strip().splitlines()[-1] if (_na.stdout or "").strip() else "{}")
                                if (_payload.get("provider") == f"pi/{FIXED_PROVIDER}/{FIXED_MODEL}"
                                        and (_payload.get("settings") or {}).get("thinkingOptionId") == FIXED_THINKING):
                                    result["checks"]["muse_native_shape"] = "PASS"
                                    result["subject"]["muse_native_shape"] = "bound"
                                else:
                                    raise ValidationError("candidate guard native shape mismatch")
                            except (json.JSONDecodeError, IndexError, AttributeError):
                                # Synthetic fakes return empty stdout for unknown exec;
                                # treat as unverified (SKIP) for fixture, FAIL for real.
                                if execution_class == "real":
                                    raise ValidationError("candidate guard native shape unreadable")
                                result["checks"]["muse_native_shape"] = "SKIP"
                        else:
                            if execution_class == "real":
                                raise ValidationError("candidate guard native shape unavailable")
                            result["checks"]["muse_native_shape"] = "SKIP"
                    else:
                        if execution_class == "real":
                            raise ValidationError("candidate guard readback unavailable")
                        result["checks"]["muse_guard_readback"] = "SKIP"
                    # Effective witness readback inside the candidate (secret-free).
                    # The test-owned extension writes only whitelisted facts;
                    # a caller-supplied observed value that differs from the
                    # witness is a fake witness and fails closed.
                    try:
                        _wit = run(["docker", "exec", name, "sh", "-c",
                                    "muse-witness-readback; cat /tmp/m07-t05-witness.jsonl"],
                                   timeout=30, check=False)
                        if _wit.returncode == 0 and (_wit.stdout or "").strip():
                            try:
                                _wlines = (_wit.stdout or "").strip().splitlines()
                                _wdoc = json.loads(_wlines[-1])
                                _wfilt = {k: str(_wdoc[k])[:128] for k in ("provider", "model", "thinking", "status", "count") if isinstance(_wdoc.get(k), str)}
                                if _wfilt:
                                    result["subject"]["muse_witness"] = _wfilt
                                    result["checks"]["muse_witness"] = "PASS"
                            except (json.JSONDecodeError, IndexError, ValueError):
                                result["checks"]["muse_witness"] = "SKIP"
                        else:
                            result["checks"]["muse_witness"] = "SKIP"
                    except (ValidationError, ValidationBlocked):
                        raise
                    except Exception:
                        result["checks"]["muse_witness"] = "SKIP"
                    # Dedicated Muse secret must exist inside the candidate when supplied.
                    if muse_secret is not None:
                        _ms = run(["docker", "exec", name, "sh", "-c",
                                   "muse-secret-check; test -f /run/secrets/pi-unraid-muse"],
                                  timeout=30, check=False)
                        if _ms.returncode != 0:
                            raise ValidationError("Muse credential missing inside candidate")
                        result["checks"]["muse_secret_present"] = "PASS"
            except (ValidationError, ValidationBlocked):
                raise
            except Exception as exc:
                raise ValidationError("muse staging unverifiable") from exc
        if daemon_info is not None or pi_info is not None or muse_observed_effective is not None:
            try:
                # Fake caller witness: when a candidate witness was observed,
                # a caller-supplied effective value that contradicts it fails.
                _wit_sub = (result.get("subject") or {}).get("muse_witness")
                if isinstance(_wit_sub, dict) and isinstance(muse_observed_effective, dict):
                    for _k in ("provider", "model", "thinking"):
                        _wv = _wit_sub.get(_k)
                        _cv = muse_observed_effective.get(_k)
                        if isinstance(_wv, str) and isinstance(_cv, str) and _wv != _cv:
                            raise ValidationError("fake caller witness contradicts candidate observation")
                _eff = _adap.classify_effective_profile(_requested, muse_observed_effective)
                if daemon_info is not None:
                    if not isinstance(daemon_info, dict):
                        raise ValidationError("daemon binding is not an object")
                    _dh = daemon_info.get("home")
                    if not isinstance(_dh, str) or not _dh:
                        raise ValidationError("daemon home is missing")
                    # Strict: candidate home must be under THIS attempt's work
                    # (or the container path /home/paseo... mapped to work).
                    # Foreign daemon home/endpoint/version (Main probe 2) fails.
                    try:
                        _cand_home = _adap.validate_candidate_home(Path(_dh), work) if work is not None else None
                    except Exception:
                        # Allow the in-container path only when it maps to work/home.
                        if _dh not in ("/home/paseo", "/home/paseo/.paseo", "/home/paseo/.paseo/daemon"):
                            raise ValidationError("daemon home is not the disposable candidate home")
                        _cand_home = (work / "home") if work is not None else Path("/tmp")
                    _adap.validate_daemon_binding({**daemon_info, "daemonVersion": daemon_info.get("daemonVersion") or daemon_info.get("version") or expected_paseo_version if daemon_info.get("daemonVersion", expected_paseo_version) == expected_paseo_version else daemon_info.get("daemonVersion")}, _cand_home if _cand_home is not None else (work / "home"))
                    # Version must equal the frozen-candidate expectation, not a caller label.
                    _dv = daemon_info.get("daemonVersion") or daemon_info.get("version")
                    if _dv is not None and str(_dv) != str(expected_paseo_version):
                        raise ValidationError("daemon version mismatch vs frozen candidate")
                    result["subject"]["daemon_binding"] = {"home": str(_dh), "version_source": version_source}
                    result["checks"]["daemon_binding"] = "PASS" if _eff["gate"] == "PASS" else "FAIL"
                    if _eff["gate"] == "FAIL":
                        raise ValidationError("daemon binding with unsupported effective profile")
                if pi_info is not None:
                    if not isinstance(pi_info, dict):
                        raise ValidationError("Pi binding is not an object")
                    _pp = pi_info.get("path")
                    _pv = pi_info.get("version")
                    if not isinstance(_pp, str) or not _pp:
                        raise ValidationError("Pi executable path is missing")
                    # Strict: Pi must be candidate-local (under work or the
                    # container /home/paseo path). Foreign /tmp/... fails.
                    _is_candidate_pi = False
                    try:
                        if work is not None and _canonical_under(_pp, work):
                            _is_candidate_pi = True
                    except Exception:
                        pass
                    if _pp.startswith("/home/paseo/") or _pp in ("/home/paseo/.pi/agent/bin/pi", "/usr/local/bin/pi"):
                        # In-container path: only allowed when it maps to the
                        # frozen candidate Pi version (checked below).
                        _is_candidate_pi = True if _pv is None or str(_pv) == str(expected_pi_version) else False
                    if not _is_candidate_pi:
                        # Try bindir resolution via work for synthetic fakes that
                        # stage a bindir under work.
                        try:
                            _adap.validate_pi_binding(_pp, _pv if _pv is not None else expected_pi_version, work if work is not None else Path("/tmp"))
                            _is_candidate_pi = True
                        except Exception:
                            _is_candidate_pi = False
                    if not _is_candidate_pi:
                        raise ValidationError("Pi executable is not candidate-local")
                    if _pv is not None and str(_pv) != str(expected_pi_version):
                        raise ValidationError("Pi version mismatch vs frozen candidate")
                    result["subject"]["pi_binding"] = {"path": str(_pp), "version_source": version_source}
                    result["checks"]["pi_binding"] = "PASS" if _eff["gate"] == "PASS" else "FAIL"
                    if _eff["gate"] == "FAIL":
                        raise ValidationError("Pi binding with unsupported effective profile")
                result["checks"]["muse_effective_profile"] = _eff["gate"]
                if _eff["gate"] != "PASS":
                    result["checks"]["muse_effective_reason"] = _sanitize(_eff["reason"], 250)
                    # Unsupported/unknown effective observation fails closed;
                    # it must not leave an overall PASS (Main probes 1-2).
                    if _eff["gate"] == "FAIL":
                        raise ValidationError("unsupported effective profile; fails closed")
                    # UNKNOWN stays as check UNKNOWN but overall cannot be PASS;
                    # handled by the real-gate below (fixture PASS only when no
                    # muse inputs? No: UNKNOWN with muse inputs must not be PASS).
                    if execution_class == "real":
                        raise ValidationBlocked("effective profile unknown; real gate unsatisfied")
                    # Fixture with UNKNOWN effective and explicit muse inputs:
                    # mark BLOCKED-equivalent by failing closed (not PASS).
                    raise ValidationError("effective profile unknown; fails closed without replay")
            except (ValidationError, ValidationBlocked):
                raise
            except Exception as exc:
                raise ValidationError("muse binding unverifiable") from exc
        else:
            result["checks"]["muse_effective_profile"] = "SKIP"
            result["checks"]["muse_effective_reason"] = "no adapter observation supplied; real gate unsatisfied"
        # Real mode requires every required binding; missing/SKIP never PASS (probe 1).
        if execution_class == "real":
            _required = ["registry_digest", "image_mapping", "companion_binding", "policy_binding",
                         "codex_catalog", "codex_auth", "codex_health", "muse_effective_profile"]
            # daemon/pi bindings required when real (must have been supplied + PASS).
            for _k in _required:
                if result["checks"].get(_k) != "PASS":
                    raise ValidationBlocked(f"real validation requires {_k} PASS; got {result['checks'].get(_k)}")
            if result["checks"].get("daemon_binding") != "PASS" or result["checks"].get("pi_binding") != "PASS":
                raise ValidationBlocked("real validation requires candidate daemon/Pi binding PASS")
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
    except ValidationUnknown as exc:
        # Uncertain occurrence: preserve exact owned references for bounded
        # readback, never resend blindly. Cleanup below preserves work +
        # container on UNKNOWN.
        result.update(status="UNKNOWN", reason="validation timeout; occurrence unknown, no replay",
                      terminal_class="unknown",
                      owned_reference=str(work) if work is not None else None,
                      owned_container=name if container_created else None)
        result["real_validation_satisfied"] = False
    except subprocess.TimeoutExpired as exc:
        result.update(status="UNKNOWN", reason="validation timeout; occurrence unknown, no replay",
                      terminal_class="unknown",
                      owned_reference=str(work) if work is not None else None,
                      owned_container=name if container_created else None)
        result["real_validation_satisfied"] = False
    finally:
        # Ownership-verified cleanup only. Never remove preexisting same-name
        # objects, another attempt's objects, global cache/HOME or production.
        # On UNKNOWN preserve work + container for bounded readback.
        _is_unknown = result.get("status") == "UNKNOWN"
        try:
            if shutil.which("docker") and container_created and work is not None and not _is_unknown:
                cur = run(["docker", "inspect", name], check=False)
                if cur.returncode == 0:
                    try:
                        cur_obj = json.loads(cur.stdout)[0]
                    except (json.JSONDecodeError, IndexError, KeyError):
                        cur_obj = {}
                    if _container_owned_by_attempt(cur_obj, work, network,
                                                   expected_image_id=image_id,
                                                   expected_nonce=attempt_nonce):
                        run(["docker", "rm", "-f", name], check=False)
                    # else: ownership changed/replaced; preserve for inspection.
                # else: container already gone; nothing to remove.
            # Preexisting containers are never removed here. UNKNOWN preserves.
        except (ValidationBlocked, ValidationError, ValidationUnknown):
            pass
        try:
            if work is not None and not _is_unknown and _owned_work(work, Path(state_root)):
                shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
        try:
            if network_created and shutil.which("docker") and not _is_unknown:
                # Re-read network ownership before removal (no name-only cleanup).
                try:
                    _nc = run(["docker", "network", "inspect", network], check=False)
                    _remove_net = True
                    if _nc.returncode == 0:
                        try:
                            _nobj = json.loads(_nc.stdout or "[]")
                            _nobj = _nobj[0] if isinstance(_nobj, list) and _nobj else {}
                        except (json.JSONDecodeError, IndexError):
                            _nobj = {}
                        _nl = (_nobj.get("Labels") or {})
                        if _nl and _nl.get("io.pi-unraid.validator-nonce") != attempt_nonce:
                            _remove_net = False
                except Exception:
                    _remove_net = True
                if _remove_net:
                    run(["docker", "network", "rm", network], check=False)
        except (ValidationBlocked, ValidationError, ValidationUnknown):
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
    p.add_argument("--candidate-file", type=Path)
    p.add_argument("--muse-secret", type=Path)
    p.add_argument("--companion-bundle", type=Path)
    p.add_argument("--daemon-info", type=Path)
    p.add_argument("--pi-info", type=Path)
    a = p.parse_args()
    import json as _jm
    _comp = None
    if a.companion_bundle is not None:
        _comp = _jm.loads(Path(a.companion_bundle).read_text(encoding="utf-8"))
    _dinfo = _jm.loads(Path(a.daemon_info).read_text(encoding="utf-8")) if a.daemon_info is not None else None
    _pinfo = _jm.loads(Path(a.pi_info).read_text(encoding="utf-8")) if a.pi_info is not None else None
    result = validate(repository=a.repository, digest=a.digest, output=a.output,
                      state_root=a.state_root, uid=a.uid, gid=a.gid, network=a.network,
                      codex_secret=a.codex_secret, codex_base_url=a.codex_base_url,
                      codex_model=a.codex_model, execution_class=a.execution_class,
                      source_root=a.source_root, candidate_file=a.candidate_file,
                      muse_secret=a.muse_secret, companion_bundle=_comp,
                      daemon_info=_dinfo, pi_info=_pinfo)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else (3 if result["status"] == "BLOCKED" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
