#!/usr/bin/env python3
"""Bounded disposable Tower validation for one immutable Paseo candidate (M07-T05, coherent rewrite).

Product path (validator CALLS the adapter/helper — AST-verifiable):
  frozen artifact chain → strict acquisition → staging → candidate-local
  execs (Codex check script, daemon/Pi lifecycle, guard hash compare,
  guarded PROMPT dispatch, witness read) → aggregated outcome → strict cleanup.

Codex-LB: the staged ``paseo_codex_candidate_check.py`` (ONE shared path
with ``paseo_codex_noninference.py``) is executed inside the candidate via
``docker exec``. The fake candidate exec in tests runs the ACTUAL staged
file locally (compile + subprocess against a local ``http.server``
fixture); marker-to-returncode mocks are rejected.

Muse: the validator calls ``dispatch_guarded_test`` semantics through a
candidate-local ``docker exec`` of the staged guard PROMPT form (NOT
``--native-create-agent-args`` export), plus ``observe_daemon_status`` /
``observe_pi_version`` on exec-observed JSON, plus staged witness
extension ``stage_witness_extension`` with ``load_witness_events`` /
``aggregate_witness`` per-owned-test correlation. Export without dispatch,
caller witness, stale witness, and clamp all fail closed.

Frozen binding: the EXISTING real schemas are consumed —
``config/paseo-candidate.json`` (candidate_id/components/policy),
prepare ``.pi-unraid-candidate-build-input.json``
(candidate_id/accepted/candidate_file_sha256/handoff_evidence_sha256/
source_head/parent/ref/companion_bundle), the build record
(``candidate.candidate_id``/``image.id``/phases), tested-image evidence
(candidate_id/candidate_file_sha256/build_record_sha256/image_id/
source/companion_bundle), and the publication record (``candidate_id`` ↔
OCI ``digest`` ↔ ``image_id`` binding from ``paseo_candidate_publish``).
candidate_id, OCI digest and local image ID are DISTINCT types; equating
them fails closed. In-candidate ``sha256sum``/``cat`` outputs are
COMPARED to expected hashes/policy (returncode 0 alone is not readback).
``build_record``/``tested`` input is REQUIRED for real mode (no longer
unused). Missing/malformed/mismatched input fails closed before inference.
Expected Paseo/Pi versions derive from the frozen candidate; there is no
host-pin fallback for real mode. OCI manifest digest and local image ID
stay distinct; a missing actual ``Image`` never falls back to
``Config.Image``/registry ref as running-ID proof.

Dedicated secrets: Codex file (``CODEX_LB_API_KEY=``/bare, private, ro at
``/run/secrets/pi-unraid-codex-lb``) and Meta file (``META_API_KEY=``/bare,
private, ro at ``/run/secrets/pi-unraid-meta``, pointer
``META_API_KEY_FILE``, never value on argv/env). Empty values fail closed.
Only synthetic files in M07-T05; no ordinary-auth borrowing, no admission.

Ownership (no fixture exceptions): work requires ``.attempt-nonce``
content ``nonce\\n`` + ``.attempt-id`` (nonce/candidate_id); container
requires exact Id + Image + nonce label + network + exact
source→destination/mode pairs
(``work/home→/home/paseo``, ``work/projects→/projects``,
``work/worktrees→/worktrees``, secrets ro at exact targets, no extras);
network requires the nonce label (label-less always FAIL, fixture or
real). Verification runs BEFORE exec and BEFORE cleanup. UNKNOWN preserves
the exact owned test file + container name/ID + daemon refs for bounded
readback without resend. Cleanup removes only verified-owned objects;
unknown/missing ownership preserves; work is never erased while a live
container still mounts it; no global/root/cache/foreign removal.

Outcome: fixture/rehearsal ALWAYS leaves ``real_validation_satisfied``
false. The real-mode path EXISTS structurally: real success requires
completed PROMPT dispatch + aggregated witness PASS + every required
binding PASS + successful Codex checks; it is testable under fakes (not
hardcoded false). Timeouts/unknown retain UNKNOWN with exact refs and
never replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^ghcr\.io/[a-z0-9][a-z0-9._/-]*$")
SCHEMA_VERSION = 2
CODEX_SECRET_TARGET = "/run/secrets/pi-unraid-codex-lb"
MUSE_SECRET_TARGET = "/run/secrets/pi-unraid-meta"
MUSE_SECRET_ENV = "META_API_KEY"
MUSE_POINTER_ENV = "META_API_KEY_FILE"
WITNESS_CANDIDATE_PATH = "/tmp/m07-t05-witness.jsonl"

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
    pass


def _sanitize(msg: str, limit: int = 400) -> str:
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


def _load_adapter():
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location(
        "paseo_candidate_muse_adapter_product",
        Path(__file__).resolve().parent / "paseo_candidate_muse_adapter.py",
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_codex_helper():
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location(
        "paseo_codex_noninference_product",
        Path(__file__).resolve().parent / "paseo_codex_noninference.py",
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _secret_file_ok(path: Path, *, what: str) -> None:
    if path.is_symlink():
        raise ValidationError(f"dedicated {what} credential must not be a symlink")
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise ValidationBlocked(f"dedicated {what} credential file unavailable") from exc
    import stat as statmod

    if not statmod.S_ISREG(st.st_mode):
        raise ValidationError(f"dedicated {what} credential must be a regular file")
    if statmod.S_IMODE(st.st_mode) & 0o077:
        raise ValidationError(f"dedicated {what} credential must be private (0600/0400)")


def _read_secret_value(path: Path, *, allowed_names: tuple, what: str) -> str:
    """Strict secret content read (value never returned to callers that log).

    Used only to VALIDATE shape here; the value itself is never placed on
    argv/env or in output. Empty values fail closed.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationBlocked(f"dedicated {what} credential unreadable") from exc
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if len(lines) != 1:
        raise ValidationError(f"dedicated {what} credential must hold exactly one entry")
    line = lines[0]
    if "=" in line:
        name, _, value = line.partition("=")
        if name not in allowed_names:
            raise ValidationError(f"dedicated {what} credential entry must be {'/'.join(allowed_names)} or a bare key")
        value = value.strip()
    else:
        value = line.strip()
    if not value or any(ch.isspace() for ch in value) or "\x00" in value:
        raise ValidationError(f"dedicated {what} credential value is invalid")
    if len(value) > 4096:
        raise ValidationError(f"dedicated {what} credential value is too long")
    return value


def _owned_work(work: Path, state_root: Path, *, nonce: str, candidate_id: str) -> bool:
    """Work is owned only with matching nonce + candidate identity (not mere file)."""
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
        if (w / ".attempt-nonce").read_text(encoding="utf-8").strip() != nonce:
            return False
        if (w / ".attempt-id").read_text(encoding="utf-8").strip() != candidate_id:
            return False
    except OSError:
        return False
    return True


def _canonical(path_str: str) -> Path | None:
    try:
        p = Path(path_str)
        return p.resolve() if p.exists() else Path(os.path.abspath(path_str)).resolve()
    except OSError:
        return None


EXPECTED_MOUNT_PAIRS = (
    ("home", "/home/paseo"),
    ("projects", "/projects"),
    ("worktrees", "/worktrees"),
)


def _container_owned(obj: dict, work: Path, network: str, *,
                     expected_image_id: str, expected_nonce: str,
                     expected_container_id: str | None = None,
                     expected_secret_sources: dict | None = None,
                     expected_user: str = "99:100") -> bool:
    """Exact acquisition+current ownership: Id, Image, nonce label, network,
    exact source→destination/mode pairs. All required, no exceptions.

    When expected_container_id is supplied (post-acquisition boundaries),
    the live object Id must equal the full acquired ID; a replaced container with preserved
    mounts/nonce but a different Id is foreign and fails.

    When expected_secret_sources maps a secret destination to its exact
    required host source, a swapped operator-input source fails even when
    the destination/mode look right. """
    try:
        if not isinstance(obj, dict) or not obj.get("Id"):
            return False
        if expected_container_id:
            live = str(obj.get("Id") or "")
            want = str(expected_container_id or "")
            if not live or not want:
                return False
            if live != want:
                return False
        host = obj.get("HostConfig") or {}
        if host.get("NetworkMode") != network:
            return False
        if (obj.get("Config") or {}).get("User") != expected_user:
            return False
        if host.get("ReadonlyRootfs") is not True:
            return False
        tmpfs = host.get("Tmpfs")
        if not isinstance(tmpfs, dict) or set(tmpfs) != {"/tmp", "/run"}:
            return False
        for options in tmpfs.values():
            if not isinstance(options, str) or not {"rw", "nosuid", "nodev"}.issubset(set(options.split(","))):
                return False
        # Actual running image must be the pulled local image ID. No fallback
        # to Config.Image/registry ref: a missing Image field fails.
        if not obj.get("Image") or obj.get("Image") != expected_image_id:
            return False
        labels = ((obj.get("Config") or {}).get("Labels") or {})
        if labels.get("io.pi-unraid.validator-nonce") != expected_nonce:
            return False
        mounts = obj.get("Mounts") or []
        if not mounts:
            return False
        if any(not isinstance(m, dict) or m.get("Type") != "bind" for m in mounts):
            return False
        by_dest = {m.get("Destination"): m for m in mounts}
        if len(by_dest) != len(mounts):
            return False
        required_destinations = {d for _, d in EXPECTED_MOUNT_PAIRS} | set(expected_secret_sources or {})
        if set(by_dest) != required_destinations:
            return False
        w = work.resolve()
        for sub, dest in EXPECTED_MOUNT_PAIRS:
            m = by_dest.get(dest)
            if m is None or m.get("RW") is not True:
                if m is None or m.get("RW") != True:
                    return False
            src = _canonical(str(m.get("Source", "")))
            want = (w / sub).resolve() if (w / sub).exists() else Path(os.path.abspath(str(w / sub))).resolve()
            if src != want:
                return False
        allowed = {d for _, d in EXPECTED_MOUNT_PAIRS} | {CODEX_SECRET_TARGET, MUSE_SECRET_TARGET}
        if set(by_dest) - allowed:
            return False
        for sec in (CODEX_SECRET_TARGET, MUSE_SECRET_TARGET):
            if sec in by_dest and by_dest[sec].get("RW") != False:
                return False
        if expected_secret_sources:
            for dest, want_src in expected_secret_sources.items():
                m = by_dest.get(dest)
                if m is None:
                    return False
                got = _canonical(str(m.get("Source", "")))
                want = _canonical(str(want_src))
                if got is None or want is None or got != want:
                    return False
        return True
    except Exception:
        return False


def _network_owned(net_obj: dict, *, expected_nonce: str,
                   expected_network_id: str | None = None) -> bool:
    """Network is owned only with the attempt nonce label. Label-less FAILs.

    When expected_network_id is supplied (post-acquisition boundary), the
    live network Id must equal the acquired ID; a replaced same-nonce
    network is foreign and fails. """
    try:
        labels = (net_obj.get("Labels") or {})
        if labels.get("io.pi-unraid.validator-nonce") != expected_nonce:
            return False
        if expected_network_id:
            live = str(net_obj.get("Id") or "")
            want = str(expected_network_id or "")
            if not live or not want:
                return False
            if live != want:
                return False
        return True
    except Exception:
        return False


def _assert_no_inference(text: str) -> None:
    low = text.lower()
    for sub in FORBIDDEN_INFERENCE_SUBSTRINGS:
        if sub in low:
            raise ValidationError(f"inference endpoint forbidden: {sub}")


def _load_json_file(path: Path | None, *, what: str, required: bool):
    if path is None:
        if required:
            raise ValidationBlocked(f"{what} is required; omission fails closed")
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{what} unreadable or malformed") from exc


def validate(*, repository, digest, output, state_root, uid=99, gid=100,
             network="pi-unraid-validator", codex_secret=None, codex_base_url=None,
             codex_model=None, execution_class="fixture", source_root=None,
             companion_bundle=None, candidate_file=None, handoff_file=None,
             build_input_file=None, tested_image_file=None, muse_secret=None,
             muse_observed_effective=None, daemon_info=None, pi_info=None,
             build_record=None, publication_file=None):
    """Validate one immutable candidate (see module docstring for product path)."""
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
            "candidate_id": None,
            "companion_bundle": None,
            "policy_identity": None,
            "daemon_binding": None,
            "pi_binding": None,
        },
        "real_validation_satisfied": False,
        "real_reason": "fixture/rehearsal never satisfies final validation",
    }
    work = None
    container_created: bool = False
    created_id: str | None = None
    network_created = False
    attempt_nonce: str | None = None
    test_id: str | None = None
    owned_test_path: str | None = None
    daemon_ref: dict | None = None
    try:
        adap = _load_adapter()
        chelp = _load_codex_helper()
        if not shutil.which("docker"):
            raise ValidationBlocked("docker CLI unavailable")
        # --- Frozen artifact chain (EXISTING real schemas, no invented envelopes) ---
        # Types are distinct: candidate_id is the resolver's component-resolution
        # identity (candidate/build/handoff/tested/publication records); digest is
        # the OCI manifest digest (registry/immutable_ref); image_id is the local
        # platform image identity (docker inspect .Id). scripts/paseo_candidate_publish.py
        # publish() outputs candidate_id and digest as separate fields; equating them
        # is a type error and fails closed.
        real_mode = execution_class == "real"
        cand = _load_json_file(candidate_file, what="candidate file", required=real_mode)
        handoff = _load_json_file(handoff_file, what="handoff evidence", required=real_mode)
        build_input = _load_json_file(build_input_file, what="build-input record", required=real_mode)
        tested = _load_json_file(tested_image_file, what="tested-image record", required=real_mode)
        build_rec = _load_json_file(build_record, what="build record", required=real_mode)
        publication = _load_json_file(publication_file, what="publication record", required=real_mode)
        if real_mode and (cand is None or handoff is None or build_input is None
                           or tested is None or build_rec is None or publication is None):
            raise ValidationBlocked(
                "real validation requires candidate + handoff + build-input + "
                "tested-image + build record + publication records")
        if real_mode and companion_bundle is None:
            if not isinstance(build_input, dict) or not isinstance(build_input.get("companion_bundle"), dict):
                raise ValidationBlocked("frozen companion declaration required")
            companion_bundle = build_input["companion_bundle"]
        candidate_id = None
        candidate_raw = None
        handoff_raw = None
        build_rec_raw = None
        if cand is not None:
            if not isinstance(cand, dict):
                raise ValidationError("candidate file must be an object")
            candidate_id = cand.get("candidate_id")
            if not isinstance(candidate_id, str) or not DIGEST.fullmatch(candidate_id):
                raise ValidationError("candidate file candidate_id is not an immutable sha256 identity")
            # EXACT producer validation (resolver): schema/status/types,
            # component provenance, compatibility, policy, candidate_id hash.
            import importlib.util as _ilu2
            import sys as _sys2
            _scripts_dir = str(Path(__file__).resolve().parent)
            _added_path = _scripts_dir not in _sys2.path
            if _added_path:
                _sys2.path.insert(0, _scripts_dir)
            try:
                _rspec = _ilu2.spec_from_file_location(
                    "resolve_paseo_candidate_product",
                    Path(__file__).resolve().parent / "resolve-paseo-candidate.py")
                _rmod = _ilu2.module_from_spec(_rspec)
                _rspec.loader.exec_module(_rmod)
            finally:
                if _added_path:
                    try:
                        _sys2.path.remove(_scripts_dir)
                    except ValueError:
                        pass
            try:
                _rmod.validate(cand)
            except Exception as exc:
                raise ValidationError(f"candidate failed producer validation: {exc}") from exc
            comp = cand.get("components") or {}
            if not isinstance(comp, dict):
                raise ValidationError("candidate components malformed")
            paseo_c = comp.get("paseo") or {}
            pi_c = comp.get("pi") or {}
            expected_paseo = paseo_c.get("version")
            expected_pi = pi_c.get("version")
            if not expected_paseo or not expected_pi:
                raise ValidationError("candidate components lack frozen Paseo/Pi versions")
            result["subject"]["candidate_id"] = candidate_id
            result["subject"]["expected_paseo_version"] = expected_paseo
            result["subject"]["expected_pi_version"] = expected_pi
            result["subject"]["version_source"] = f"candidate:{Path(candidate_file).name}"
            candidate_raw = Path(candidate_file).read_bytes()
            result["subject"]["candidate_file_sha256"] = "sha256:" + hashlib.sha256(candidate_raw).hexdigest()
            if handoff_file is not None:
                handoff_raw = Path(handoff_file).read_bytes()
            if isinstance(build_record, (str, Path)):
                build_rec_raw = Path(build_record).read_bytes()
        else:
            expected_paseo = expected_pi = None
            result["subject"]["version_source"] = "absent (real gate unsatisfied)"
        # Publication binds the distinct types: candidate_id <-> OCI digest <-> image.
        if publication is not None:
            if not isinstance(publication, dict):
                raise ValidationError("publication record must be an object")
            if publication.get("schema_version") != 1:
                raise ValidationError("publication record uses an unsupported schema")
            if publication.get("status") != "published":
                raise ValidationError("publication record is not a published binding")
            if publication.get("digest") != digest:
                raise ValidationError("publication digest mismatch vs validated OCI digest")
            if str(publication.get("repository", "")).strip().lower() != repository.strip().lower():
                raise ValidationError("publication repository mismatch")
            if candidate_id is not None and publication.get("candidate_id") != candidate_id:
                raise ValidationError("publication candidate_id mismatch vs candidate file")
            if publication.get("immutable_ref") != ref:
                raise ValidationError("publication immutable_ref mismatch vs validated reference")
            result["subject"]["publication_image_id"] = publication.get("image_id")
            # Publication byte claims are verified against actual record bytes:
            # forged hashes fail closed even when linkage fields match.
            if candidate_raw is not None and publication.get("candidate_file_sha256") != result["subject"].get("candidate_file_sha256"):
                raise ValidationError("publication candidate hash mismatch vs candidate bytes")
            if handoff_raw is not None and publication.get("handoff_evidence_sha256") != "sha256:" + hashlib.sha256(handoff_raw).hexdigest():
                raise ValidationError("publication handoff hash mismatch vs handoff bytes")
            if build_rec_raw is not None and publication.get("build_record_sha256") != "sha256:" + hashlib.sha256(build_rec_raw).hexdigest():
                raise ValidationError("publication build-record hash mismatch vs build bytes")
            if tested_image_file is not None:
                tested_hash = "sha256:" + hashlib.sha256(Path(tested_image_file).read_bytes()).hexdigest()
                if publication.get("tested_image_evidence_sha256") != tested_hash:
                    raise ValidationError("publication tested-image byte digest mismatch")
            if build_input is not None and publication.get("source_head") != build_input.get("source_head"):
                raise ValidationError("publication source-head mismatch vs prepared record")
            if handoff is not None:
                if publication.get("discovery_source_sha") != handoff.get("source_sha"):
                    raise ValidationError("publication discovery source mismatch vs handoff")
                if publication.get("discovery_source_ref") != handoff.get("source_ref"):
                    raise ValidationError("publication discovery ref mismatch vs handoff")
        elif real_mode:
            raise ValidationBlocked("real validation requires the publication binding")
        GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
        if handoff is not None:
            if not isinstance(handoff, dict):
                raise ValidationError("handoff evidence must be an object")
            if candidate_id is not None and handoff.get("candidate_id") != candidate_id:
                raise ValidationError("handoff candidate_id mismatch vs candidate file")
            if handoff.get("schema_version") != 1 or handoff.get("status") != "update":
                raise ValidationError("handoff evidence is not a material-change record")
            if not handoff.get("source_sha") or not handoff.get("source_ref"):
                raise ValidationError("handoff evidence lacks discovery source provenance")
            if not GIT_SHA.fullmatch(str(handoff.get("source_sha") or "")):
                raise ValidationError("handoff source_sha is not an exact Git SHA")
            if not str(handoff.get("source_ref") or "").startswith(("refs/heads/", "refs/tags/")):
                raise ValidationError("handoff source_ref is not an approved ref")
            if not handoff.get("accepted_candidate_id") or not DIGEST.fullmatch(str(handoff.get("accepted_candidate_id"))):
                raise ValidationError("handoff accepted-candidate identity is invalid")
            if real_mode and not handoff.get("candidate_file_sha256"):
                raise ValidationBlocked("real validation requires the handoff candidate byte link")
            if handoff_raw is not None:
                expect_hfs = "sha256:" + hashlib.sha256(handoff_raw).hexdigest()
                for rec, what in ((build_input, "build-input"), (tested, "tested-image")):
                    if isinstance(rec, dict) and rec.get("handoff_evidence_sha256") != expect_hfs:
                        raise ValidationError(f"{what} handoff byte digest mismatch vs handoff evidence")
            if candidate_raw is not None and handoff.get("candidate_file_sha256") != result["subject"].get("candidate_file_sha256"):
                raise ValidationError("handoff candidate byte digest mismatch vs candidate file")
        for rec, what in ((build_input, "build-input"), (tested, "tested-image")):
            if rec is None:
                continue
            if not isinstance(rec, dict):
                raise ValidationError(f"{what} record must be an object")
            if candidate_id is not None and rec.get("candidate_id") != candidate_id:
                raise ValidationError(f"{what} candidate_id mismatch vs candidate file")
            cfs = rec.get("candidate_file_sha256")
            if real_mode and not cfs:
                raise ValidationBlocked(f"{what} candidate byte digest required")
            if candidate_raw is not None and cfs != result["subject"].get("candidate_file_sha256"):
                raise ValidationError(f"{what} candidate byte digest mismatch")
            cdp = rec.get("companion_bundle") or rec.get("companion_declared")
            if companion_bundle is not None and cdp is not None:
                if (cdp.get("source_digest") != companion_bundle.get("source_digest")
                        or cdp.get("files") != companion_bundle.get("files")):
                    raise ValidationError(f"{what} companion conflicts with declared binding")
        if build_input is not None:
            if build_input.get("schema_version") != 1 or build_input.get("status") != "prepared":
                raise ValidationError("build-input record is not a prepared binding")
            if not isinstance(build_input.get("companion_bundle"), dict):
                raise ValidationError("build-input record lacks the companion bundle declaration")
            if real_mode and not build_input.get("candidate_file_sha256"):
                raise ValidationBlocked("real validation requires the prepared candidate byte link")
            if real_mode and not build_input.get("handoff_evidence_sha256"):
                raise ValidationBlocked("real validation requires the prepared handoff byte link")
            if handoff is not None:
                if build_input.get("source_parent") != handoff.get("source_sha"):
                    raise ValidationError("build-input source-parent mismatch vs handoff source")
                if build_input.get("source_ref") != handoff.get("source_ref"):
                    raise ValidationError("build-input source-ref mismatch vs handoff source")
                if build_input.get("accepted_candidate_id") != handoff.get("accepted_candidate_id"):
                    raise ValidationError("build-input accepted-candidate mismatch vs handoff")
                if not GIT_SHA.fullmatch(str(build_input.get("source_head") or "")):
                    raise ValidationError("build-input source-head is not an exact Git SHA")
            _bcd = build_input.get("companion_bundle") or {}
            if companion_bundle is not None and isinstance(_bcd, dict):
                if (_bcd.get("source_digest") != companion_bundle.get("source_digest")
                        or _bcd.get("files") != companion_bundle.get("files")
                        or _bcd.get("modes") != companion_bundle.get("modes")):
                    raise ValidationError("build-input companion conflicts with declared binding")
        if tested is not None:
            if tested.get("schema_version") != 1:
                raise ValidationError("tested-image record uses an unsupported schema")
            if tested.get("status") != "tested_image_preserved":
                raise ValidationError("tested-image record is not a preserved tested image")
            if build_rec_raw is not None and tested.get("build_record_sha256") != "sha256:" + hashlib.sha256(build_rec_raw).hexdigest():
                raise ValidationError("tested-image build record digest mismatch vs build record")
            if real_mode and build_rec_raw is not None and not tested.get("build_record_sha256"):
                raise ValidationBlocked("real validation requires the tested build-record digest")
            if real_mode and not tested.get("handoff_evidence_sha256"):
                raise ValidationBlocked("real validation requires the tested handoff digest")
            if real_mode and not tested.get("image_id"):
                raise ValidationBlocked("real validation requires the tested image identity")
            if handoff is not None:
                if tested.get("discovery_source_sha") != handoff.get("source_sha"):
                    raise ValidationError("tested discovery source mismatch vs handoff")
                if tested.get("discovery_source_ref") != handoff.get("source_ref"):
                    raise ValidationError("tested discovery ref mismatch vs handoff")
            if build_input is not None and tested.get("source_head") != build_input.get("source_head"):
                raise ValidationError("tested source-head mismatch vs prepared record")
        if build_rec is not None:
            if not isinstance(build_rec, dict):
                raise ValidationError("build record must be an object")
            if build_rec.get("schema_version") != 1:
                raise ValidationError("build record uses an unsupported schema")
            rec_cand = (build_rec.get("candidate") or {})
            if candidate_id is not None and rec_cand.get("candidate_id") != candidate_id:
                raise ValidationError("build record candidate mismatch vs candidate file")
            rec_img = (build_rec.get("image") or {})
            if not rec_img.get("id"):
                raise ValidationError("build record lacks the built image identity")
            if rec_img.get("candidate_label") != candidate_id and candidate_id is not None:
                raise ValidationError("build record image label mismatch vs candidate")
            _phases = build_rec.get("phases") or {}
            for _phase in ("resolution_readback", "builder_ensure", "build", "test"):
                if (_phases.get(_phase) or {}).get("status") != "ok":
                    raise ValidationError(f"build record phase is not GREEN: {_phase}")
        if handoff is not None:
            for rec, what in ((build_input, "prepared"), (tested, "tested"), (publication, "publication")):
                if rec is not None and rec.get("accepted_candidate_id") != handoff.get("accepted_candidate_id"):
                    raise ValidationError(f"{what} accepted-candidate identity mismatch")
        if companion_bundle is not None:
            for rec, what in ((build_input, "prepared"), (build_rec, "build"), (tested, "tested")):
                if rec is not None and rec.get("companion_bundle") != companion_bundle:
                    raise ValidationError(f"{what} complete companion declaration mismatch")
        if build_rec is not None and build_rec.get("command") != "build":
            raise ValidationError("build record is not a build command result")
        result["checks"]["frozen_chain"] = "PASS" if cand is not None else "SKIP"
        # --- Registry + local image (distinct, mapped) ---
        readback = run(["docker", "buildx", "imagetools", "inspect", ref]).stdout
        registry_digests = [line.split(None, 1)[1].strip() for line in readback.splitlines()
                            if line.strip().startswith("Digest:") and len(line.split(None, 1)) == 2]
        if digest not in registry_digests:
            raise ValidationError("registry immutable digest readback mismatch")
        result["checks"]["registry_digest"] = "PASS"
        run(["docker", "image", "pull", ref], timeout=900)
        image_id = run(["docker", "image", "inspect", ref, "--format", "{{.Id}}"]).stdout.strip()
        if not DIGEST.fullmatch(image_id):
            raise ValidationError("pulled local image ID missing")
        repo_out = run(["docker", "image", "inspect", ref, "--format", "{{json .RepoDigests}}"], check=False)
        mapped = False
        if repo_out.returncode == 0:
            try:
                rd = json.loads(repo_out.stdout.strip() or "[]")
                mapped = ref in (rd if isinstance(rd, list) else [])
            except json.JSONDecodeError:
                mapped = False
        if not mapped:
            raise ValidationError("RepoDigests OCI-to-local mapping unverified; fails closed")
        result["checks"]["image_mapping"] = "PASS"
        result["subject"]["observed_image_id"] = image_id
        # Image config provenance: the pulled image's own Env must carry the
        # frozen Pi version (Dockerfile PI_UNRAID_PI_VERSION is rendered from
        # the candidate), binding image bytes to Pi independently of any
        # container claim.
        if expected_pi is not None:
            cfg_out = run(["docker", "image", "inspect", ref, "--format", "{{json .Config}}"], check=False)
            if cfg_out.returncode != 0:
                raise ValidationBlocked("pulled image config unavailable")
            try:
                cfg_doc = json.loads((cfg_out.stdout or "").strip())
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValidationError("pulled image config unreadable") from exc
            cfg_env = cfg_doc.get("Env") or []
            if f"PI_UNRAID_PI_VERSION={expected_pi}" not in cfg_env:
                raise ValidationError("pulled image config lacks the frozen Pi version")
            result["checks"]["image_config"] = "PASS"
            _lbls = cfg_doc.get("Labels") or {}
            if (_lbls.get("io.pi-unraid.candidate-id") != candidate_id or
                    f"PI_UNRAID_CANDIDATE_ID={candidate_id}" not in cfg_env):
                raise ValidationError("pulled image candidate configuration mismatch")
            if _lbls.get("io.pi-unraid.pi-version") not in (None, str(expected_pi)):
                raise ValidationError("pulled image Pi label contradicts frozen candidate")
            result["subject"]["image_pi_label"] = _lbls.get("io.pi-unraid.pi-version")
        if publication is not None and publication.get("image_id") not in (None, image_id):
            raise ValidationError("publication image_id mismatch vs pulled local ID")
        if tested is not None and tested.get("image_id") not in (None, image_id):
            raise ValidationError("tested-image image_id mismatch vs pulled local ID")
        if build_rec is not None and (build_rec.get("image") or {}).get("id") not in (None, image_id):
            raise ValidationError("build record image mismatch vs pulled local ID")
        # --- Companion/policy/launcher from frozen source (recompute what runs) ---
        if source_root is not None:
            import importlib.util as _ilu

            src = Path(source_root)
            spec = _ilu.spec_from_file_location(
                "paseo_candidate_build_product",
                Path(__file__).resolve().parent / "paseo_candidate_build.py")
            build_mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(build_mod)
            actual = build_mod.companion_bundle_identity(src)
            result["subject"]["companion_bundle"] = {
                "source": actual["source"], "source_digest": actual["source_digest"],
                "files": len(actual["files"]),
            }
            if companion_bundle is not None:
                if not isinstance(companion_bundle, dict):
                    raise ValidationError("companion binding declaration must be an object")
                build_mod.verify_companion_binding(src, companion_bundle)
                if companion_bundle.get("source_digest") != actual["source_digest"]:
                    raise ValidationError("companion bundle digest mismatch")
            for rec in (build_input, tested):
                if rec is not None and rec.get("companion_bundle") is not None:
                    cb = rec["companion_bundle"]
                    if cb.get("source_digest") != actual["source_digest"]:
                        raise ValidationError("artifact companion digest mismatch vs source")
            result["checks"]["companion_binding"] = "PASS"
            pol = src / "config" / "pi-agent" / "policies" / "llm-test-policy.json"
            grd = src / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
            if not pol.is_file() or not grd.is_file():
                raise ValidationError("policy/launcher files unavailable")
            pdoc = json.loads(pol.read_text(encoding="utf-8"))
            prof = pdoc.get("real_llm_tests", {})
            if (prof.get("provider"), prof.get("model"), prof.get("thinking")) != (
                    FIXED_PROVIDER, FIXED_MODEL, FIXED_THINKING):
                raise ValidationError("policy identity is not the fixed Muse profile")
            if bool(prof.get("fallback_allowed")):
                raise ValidationError("policy identity allows fallback")
            expected_guard_sha = "sha256:" + hashlib.sha256(grd.read_bytes()).hexdigest()
            expected_policy_sha = "sha256:" + hashlib.sha256(pol.read_bytes()).hexdigest()
            result["subject"]["policy_identity"] = {"path": "config/pi-agent/policies/llm-test-policy.json", "sha256": expected_policy_sha}
            result["subject"]["launcher_identity"] = {"path": "config/pi-agent/bin/run-llm-test.sh", "sha256": expected_guard_sha}
            result["checks"]["policy_binding"] = "PASS"
            adap.validate_requested_profile(prof.get("provider"), prof.get("model"), prof.get("thinking"), bool(prof.get("fallback_allowed")))
        else:
            if real_mode:
                raise ValidationBlocked("real validation requires source_root binding")
            result["checks"]["companion_binding"] = "SKIP"
            result["checks"]["policy_binding"] = "SKIP"
            expected_guard_sha = expected_policy_sha = None
        # --- Secrets (strict shape now; values never on argv/env/output) ---
        secret_resolved = muse_resolved = None
        if codex_secret is not None:
            secret_resolved = Path(codex_secret).resolve()
            _secret_file_ok(Path(codex_secret), what="Codex-LB")
            try:
                chelp.validate_base_url(codex_base_url)
                chelp.validate_model_id(codex_model)
                chelp.read_dedicated_secret(Path(codex_secret))
            except chelp.CodexBlocked as exc:
                raise ValidationBlocked(chelp.sanitize_message(str(exc), 200)) from exc
            except chelp.CodexError as exc:
                raise ValidationError(chelp.sanitize_message(str(exc), 200)) from exc
        elif real_mode:
            raise ValidationBlocked("real validation requires dedicated Codex credential")
        if muse_secret is not None:
            muse_resolved = Path(muse_secret).resolve()
            _secret_file_ok(Path(muse_secret), what="Muse")
            try:
                adap.read_dedicated_muse_secret(Path(muse_secret))
            except adap.AdapterBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except adap.AdapterError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
        elif real_mode:
            raise ValidationBlocked("real validation requires dedicated Muse credential")
        # --- Disposable acquisition (nonce + identity BEFORE any mutation) ---
        import secrets as _secrets

        attempt_nonce = _secrets.token_hex(8)
        test_id = f"m07t05-{attempt_nonce}"
        root = Path(state_root)
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="candidate-", dir=root))
        (work / ".attempt-nonce").write_text(attempt_nonce + "\n", encoding="utf-8")
        (work / ".attempt-id").write_text(digest + "\n", encoding="utf-8")
        try:
            (work / ".attempt-nonce").chmod(0o600)
            (work / ".attempt-id").chmod(0o600)
        except OSError:
            pass
        for dirname in ("home", "projects", "worktrees"):
            pth = work / dirname
            pth.mkdir()
            pth.chmod(0o700)
            try:
                os.chown(pth, uid, gid)
            except PermissionError as exc:
                raise ValidationBlocked("cannot establish validator UID:GID ownership") from exc
        owned_test_path = str(work / f"test-{attempt_nonce}.json")
        acquired_network_id: str | None = None
        mounted_secrets: dict = {}
        # Network: nonce label REQUIRED (label-less always FAIL, fixture or real).
        net_inspect = run(["docker", "network", "inspect", network], check=False)
        if net_inspect.returncode:
            created_net = run(["docker", "network", "create", "--label",
                               f"io.pi-unraid.validator-nonce={attempt_nonce}", network])
            try:
                acquired_network_id = (created_net.stdout or "").strip().splitlines()[-1].strip() or None
            except Exception:
                acquired_network_id = None
            if not acquired_network_id:
                raise ValidationBlocked("network acquisition identity unavailable; failing closed")
            network_created = True
        else:
            try:
                nobj = json.loads(net_inspect.stdout or "[]")
                nobj = nobj[0] if isinstance(nobj, list) and nobj else {}
            except (json.JSONDecodeError, IndexError):
                nobj = {}
            if not _network_owned(nobj, expected_nonce=attempt_nonce):
                raise ValidationError("validator network is not owned by this attempt; refusing reuse")
            # A pre-existing owned network cannot carry this attempt's fresh
            # nonce; reaching here means label confusion — refuse reuse.
            raise ValidationError("validator network already exists; refusing reuse without acquisition proof")
        # Preexisting container: exact ownership or fail (never rm foreign).
        pre = run(["docker", "inspect", name], check=False)
        if pre.returncode == 0:
            try:
                existing = json.loads(pre.stdout)[0]
            except (json.JSONDecodeError, IndexError, KeyError):
                existing = {}
            if not _container_owned(existing, work, network, expected_image_id=image_id, expected_nonce=attempt_nonce):
                raise ValidationError("same-name container already exists and is not owned by this attempt; refusing it")
            owned_rm = run(["docker", "rm", "-f", name], check=False)
            if owned_rm.returncode != 0:
                raise ValidationBlocked("owned leftover container could not be reclaimed")
        # --- Container create (secret values NEVER on argv/env; pointers only) ---
        argv = ["docker", "run", "-d", "--name", name, "--user", f"{uid}:{gid}",
                "--network", network,
                "--label", f"io.pi-unraid.validator-nonce={attempt_nonce}",
                "--label", f"io.pi-unraid.candidate-id={digest}",
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--tmpfs", "/run:rw,nosuid,nodev",
                "-e", "TZ=Europe/Zurich", "-e", "HOME=/home/paseo", "-e", "PASEO_HOME=/home/paseo/.paseo",
                "-v", f"{work / 'home'}:/home/paseo:rw",
                "-v", f"{work / 'projects'}:/projects:rw",
                "-v", f"{work / 'worktrees'}:/worktrees:rw"]
        if codex_secret is not None:
            argv += ["-e", f"PI_CODEX_LB_BASE_URL={codex_base_url.rstrip('/')}",
                     "-e", f"PI_CODEX_LB_MODEL={codex_model}",
                     "-v", f"{secret_resolved}:{CODEX_SECRET_TARGET}:ro"]
            mounted_secrets[CODEX_SECRET_TARGET] = str(secret_resolved)
        if muse_secret is not None:
            argv += ["-v", f"{muse_resolved}:{MUSE_SECRET_TARGET}:ro",
                     "-e", f"{MUSE_POINTER_ENV}={MUSE_SECRET_TARGET}"]
            mounted_secrets[MUSE_SECRET_TARGET] = str(muse_resolved)
        argv.append(ref)
        joined = " ".join(argv)
        for forbidden in ("/var/run/docker.sock", "unraid-api.key", "/mnt/user/appdata/pi-unraid/paseo-home"):
            if forbidden in joined:
                raise ValidationError("forbidden production authority")
        created_proc = run(argv)
        try:
            created_id = (created_proc.stdout or "").strip().splitlines()[-1].strip() or None
        except Exception:
            created_id = None
        if not created_id:
            raise ValidationBlocked("container acquisition identity unavailable; failing closed")
        container_created = True
        obj = wait_for_runtime(name)
        # Running image MUST be the pulled ID (no Config.Image/registry fallback).
        if not obj.get("Image") or obj.get("Image") != image_id:
            raise ValidationError("running container image mismatch; fails closed")
        result["subject"]["observed_running_image"] = image_id
        if not obj.get("Id"):
            raise ValidationBlocked("running container identity unavailable; failing closed")
        _live_id, _want_id = str(obj.get("Id")), str(created_id)
        if _live_id != _want_id:
            raise ValidationError("container replacement detected; fails closed")
        # Re-verify exact current ownership BEFORE any exec (ID-bound).
        cur0 = run(["docker", "inspect", name], check=False)
        if cur0.returncode != 0:
            raise ValidationBlocked("container vanished before exec")
        try:
            cur0obj = json.loads(cur0.stdout)[0]
        except (json.JSONDecodeError, IndexError, KeyError):
            cur0obj = {}
        if not _container_owned(cur0obj, work, network, expected_image_id=image_id, expected_nonce=attempt_nonce,
                                expected_container_id=created_id,
                                expected_secret_sources=mounted_secrets or None,
                                expected_user=f"{uid}:{gid}"):
            raise ValidationError("container ownership unverified before exec; preserving")
        cfg, host, mounts = cur0obj.get("Config") or {}, cur0obj.get("HostConfig") or {}, cur0obj.get("Mounts") or []
        if cfg.get("User") != f"{uid}:{gid}":
            raise ValidationError("UID:GID mismatch")
        env = "\n".join(cfg.get("Env") or []).upper()
        if any(x in env for x in ("UNRAID_API", "CODEX_LB_SECRET", "GITHUB_TOKEN")):
            raise ValidationError("production/host secret exposed")
        result["checks"].update({"uid_gid": "PASS", "mount_isolation": "PASS",
                                 "network_isolation": "PASS", "secret_isolation": "PASS", "runtime": "PASS"})
        # --- Stage what the candidate uses (BEFORE candidate code needs it) ---
        if source_root is not None:
            import shutil as _sh

            src_agent = Path(source_root) / "config" / "pi-agent"
            dst_agent = work / "home" / ".pi" / "agent"
            if src_agent.is_dir():
                for f in sorted(src_agent.rglob("*")):
                    if f.is_file() and not f.is_symlink():
                        rel = f.relative_to(src_agent)
                        dst = dst_agent / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_bytes(f.read_bytes())
                        try:
                            dst.chmod(0o755 if rel.parts and rel.parts[0] == "bin" else 0o644)
                        except OSError:
                            pass
            # Stage the ONE check program + shared helper + witness extension.
            here = Path(__file__).resolve().parent
            for fname in ("paseo_codex_noninference.py", "paseo_codex_candidate_check.py"):
                s = here / fname
                d = dst_agent / "bin" / fname
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_bytes(s.read_bytes())
                try:
                    d.chmod(0o644)
                except OSError:
                    pass
            adap.stage_witness_extension(dst_agent / "extensions" / "m07-t05-witness.js")
            adap.stage_candidate_env(dst_agent / "bin" / "m07-t05-candidate-env.sh")
            (work / "home" / ".pi" / "agent" / "bin" / "run-llm-test.sh").chmod(0o755)
            # Bind staged bytes to reviewed validator source (host-side): every
            # staged behavior-changing file must byte-match its repo source.
            # Generated observer/loader/Codex helpers are bound here to exact
            # source bytes — a changed validator source stages changed bytes
            # and the recorded identities change with it, never silently.
            import hashlib as _hl2
            staged_identities = {}
            for fname, dst in (("paseo_codex_noninference.py", dst_agent / "bin" / "paseo_codex_noninference.py"),
                               ("paseo_codex_candidate_check.py", dst_agent / "bin" / "paseo_codex_candidate_check.py")):
                src_bytes = (here / fname).read_bytes()
                if dst.read_bytes() != src_bytes:
                    raise ValidationError(f"staged {fname} differs from validator source")
                staged_identities[fname] = "sha256:" + _hl2.sha256(src_bytes).hexdigest()
            for gen, dst in (("witness", dst_agent / "extensions" / "m07-t05-witness.js"),
                             ("candidate-env", dst_agent / "bin" / "m07-t05-candidate-env.sh")):
                staged_identities[gen] = "sha256:" + _hl2.sha256(dst.read_bytes()).hexdigest()
            # Staged companion payload (exact declared file set only) must
            # match the declared binding from host-side bytes and modes.
            if companion_bundle is not None:
                import importlib.util as _ilu3
                _ispec = _ilu3.spec_from_file_location(
                    "pi_instruction_plane_staged_check",
                    Path(__file__).resolve().parent / "pi_instruction_plane.py")
                _inst = _ilu3.module_from_spec(_ispec)
                _ispec.loader.exec_module(_inst)
                try:
                    _decl_files = sorted(companion_bundle.get("files", []))
                    _staged_all = sorted([p.as_posix() for p in _inst.safe_files(dst_agent)])
                    _staged_decl = [p for p in _staged_all if p in set(_decl_files)]
                    if _staged_decl != _decl_files:
                        raise ValidationError("staged companion file set differs from declared binding")
                    _staged_modes = {p: f"{_inst.managed_mode(Path(p)):04o}" for p in _decl_files}
                    if _staged_modes != companion_bundle.get("modes"):
                        raise ValidationError("staged companion modes differ from declared binding")
                    _staged_digest = _inst.digest_source(
                        dst_agent, [Path(p) for p in _decl_files])
                    if _staged_digest != companion_bundle.get("source_digest"):
                        raise ValidationError("staged companion digest differs from declared binding")
                except ValidationError:
                    raise
                except Exception as exc:
                    raise ValidationBlocked(f"staged companion unreadable: {exc}") from exc
            result["subject"]["staged_identities"] = staged_identities
        # --- Candidate-local execs (each compared, not just returncode) ---
        # Exec by IMMUTABLE acquired container ID, never the mutable name: a
        # replaced same-name foreign object receives zero execs. Ownership is
        # re-verified before EVERY exec (execution boundary), so a container
        # replaced after the initial check cannot receive later execs.
        def _exec(args, **kw):
            _verify_current_ownership("exec")
            return run(["docker", "exec", created_id or name] + args, **kw)

        def _verify_current_ownership(stage: str) -> dict:
            cur = run(["docker", "inspect", created_id or name], check=False)
            if cur.returncode != 0:
                raise ValidationBlocked(f"container vanished before {stage}")
            try:
                cur_obj = json.loads(cur.stdout)[0]
            except (json.JSONDecodeError, IndexError, KeyError):
                cur_obj = {}
            if not _container_owned(cur_obj, work, network, expected_image_id=image_id,
                                    expected_nonce=attempt_nonce,
                                    expected_container_id=created_id,
                                    expected_secret_sources=mounted_secrets or None,
                                    expected_user=f"{uid}:{gid}"):
                raise ValidationError(f"container ownership unverified before {stage}; preserving")
            # Network acquisition identity is also an execution boundary: a
            # replaced same-nonce network fails before further execs.
            if network_created and acquired_network_id is not None:
                ncur = run(["docker", "network", "inspect", network], check=False)
                if ncur.returncode != 0:
                    raise ValidationBlocked(f"network vanished before {stage}")
                try:
                    ncur_obj = json.loads(ncur.stdout or "[]")
                    ncur_obj = ncur_obj[0] if isinstance(ncur_obj, list) and ncur_obj else {}
                except (json.JSONDecodeError, IndexError):
                    ncur_obj = {}
                if not _network_owned(ncur_obj, expected_nonce=attempt_nonce,
                                       expected_network_id=acquired_network_id):
                    raise ValidationError(f"network ownership unverified before {stage}; preserving")
            return cur_obj

        # File readback helper: hash AND mode are compared (returncode 0 is
        # NOT readback). Used for guard/policy/launcher bytes below.
        def _readback_file(cand_path: str, *, what: str):
            r = _exec(["sh", "-c",
                       f"# file-readback\nsha256sum {cand_path}; stat -c %a {cand_path}"],
                      timeout=30, check=False)
            if r.returncode != 0:
                raise ValidationError(f"candidate {what} readback unavailable")
            toks = (r.stdout or "").strip().split()
            if len(toks) < 3:
                raise ValidationError(f"candidate {what} readback malformed")
            return toks[0], toks[-1]

        # Guard hash+mode compare (bytes AND mode; profile fields alone prove
        # nothing — a staged policy/guard with identical fields but different
        # bytes or world-writable mode fails here).
        if expected_guard_sha is not None:
            g_hash, g_mode = _readback_file("/home/paseo/.pi/agent/bin/run-llm-test.sh", what="guard")
            if ("sha256:" + g_hash if not g_hash.startswith("sha256:") else g_hash) != expected_guard_sha \
                    and g_hash != expected_guard_sha[7:]:
                raise ValidationError("candidate guard hash mismatch vs frozen source")
            if g_mode != "755":
                raise ValidationError("candidate guard mode is not 0755")
            result["checks"]["muse_guard_readback"] = "PASS"
            p_hash, p_mode = _readback_file("/home/paseo/.pi/agent/policies/llm-test-policy.json", what="policy")
            if ("sha256:" + p_hash if not p_hash.startswith("sha256:") else p_hash) != expected_policy_sha \
                    and p_hash != expected_policy_sha[7:]:
                raise ValidationError("candidate policy hash mismatch vs frozen source")
            if p_mode != "644":
                raise ValidationError("candidate policy mode is not 0644")
            p = _exec(["sh", "-c", "# policy-compare\ncat /home/paseo/.pi/agent/policies/llm-test-policy.json"], timeout=30, check=False)
            if p.returncode != 0:
                raise ValidationError("candidate policy readback unavailable")
            try:
                pdoc = json.loads((p.stdout or "").strip())
                pp = pdoc.get("real_llm_tests", pdoc)
                if (pp.get("provider"), pp.get("model"), pp.get("thinking")) != (FIXED_PROVIDER, FIXED_MODEL, FIXED_THINKING) or bool(pp.get("fallback_allowed")):
                    raise ValidationError("candidate policy mismatch vs frozen fixed profile")
            except (json.JSONDecodeError, IndexError, AttributeError) as exc:
                raise ValidationError("candidate policy unreadable") from exc
            result["checks"]["muse_policy_readback"] = "PASS"
        # Daemon + Pi lifecycle INSIDE the candidate namespace (validator CALLS
        # the adapter observers; AST-verifiable product path, never caller labels).
        # Supported interfaces (pinned Paseo 0.9.2 dist/commands/daemon/status.js):
        # localDaemon/connectedDaemon/serverId/workerPid/daemonNode/providers
        # plus home/listen/version. Pinned Pi types.d.ts terminal semantics:
        # agent_end/agent_settled (observer) — see adapter.aggregate_witness.
        def _candidate_exec(argv, timeout=30):
            return _exec(argv, timeout=timeout, check=False)

        if expected_paseo is not None:
            # Source-qualified local bring-up first: `paseo daemon start
            # --home` (pinned daemon/start.js: started|already_running +
            # pid/listen) runs under the staged candidate-env loader, so the
            # daemon process inherits META_API_KEY (read in-candidate from
            # the private pointer) — the supported route into the actual
            # daemon-selected Pi subprocess env. Raw values never travel
            # argv/--env/evidence.
            try:
                daemon_ref = adap.ensure_candidate_daemon(
                    _candidate_exec, candidate_home="/home/paseo/.paseo",
                    expected_version=str(expected_paseo),
                    env_loader="/home/paseo/.pi/agent/bin/m07-t05-candidate-env.sh",
                    meta_pointer=MUSE_SECRET_TARGET if muse_secret is not None else None)
            except adap.AdapterBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except adap.AdapterError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
            result["subject"]["daemon_binding"] = daemon_ref
            result["checks"]["daemon_binding"] = "PASS"
            try:
                pi_ref = adap.observe_pi_version(
                    _candidate_exec, expected_version=str(expected_pi))
            except adap.AdapterBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except adap.AdapterError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
            result["subject"]["pi_binding"] = pi_ref
            result["checks"]["pi_binding"] = "PASS"
        # Codex checks via the staged ONE program (actual execution in tests).
        if codex_secret is not None:
            for mode in ("catalog", "health"):
                c = _exec(["python3", "/home/paseo/.pi/agent/bin/paseo_codex_candidate_check.py",
                           "--mode", mode, "--secret-file", CODEX_SECRET_TARGET,
                           "--base-url", codex_base_url.rstrip("/"), "--model", codex_model],
                          timeout=30, check=False)
                try:
                    summary = json.loads((c.stdout or "").strip().splitlines()[-1] if (c.stdout or "").strip() else "")
                except (json.JSONDecodeError, IndexError):
                    summary = {}
                if c.returncode == 0 and summary.get("status") == "PASS":
                    continue
                if c.returncode == 20:
                    raise ValidationBlocked(f"Codex-LB {mode} unavailable")
                if c.returncode == 22:
                    raise ValidationBlocked(f"Codex-LB credential missing inside candidate ({mode})")
                if c.returncode == 21:
                    raise ValidationError(f"Codex-LB {mode} authentication rejected")
                raise ValidationError(f"Codex-LB {mode} structural check failed")
            result["checks"]["codex_catalog"] = "PASS"
            result["checks"]["codex_auth"] = "PASS"
            result["checks"]["codex_health"] = "PASS"
            result["checks"]["codex_no_inference"] = "PASS"
        else:
            result["checks"]["codex_catalog"] = "SKIP"
            result["checks"]["codex_auth"] = "SKIP"
            result["checks"]["codex_health"] = "SKIP"
            result["checks"]["codex_no_inference"] = "PASS"
        # Muse PROMPT dispatch inside the candidate (NOT native-args export).
        # Native export without dispatch is explicitly rejected below.
        nexp = _exec(["sh", "-c", "# native-export-check\n/home/paseo/.pi/agent/bin/run-llm-test.sh --native-create-agent-args"], timeout=30, check=False)
        if nexp.returncode == 0:
            try:
                npay = json.loads((nexp.stdout or "").strip().splitlines()[-1] if (nexp.stdout or "").strip() else "{}")
            except (json.JSONDecodeError, IndexError):
                npay = {}
            # Export shape is interface metadata only; it is NOT dispatch.
            result["subject"]["muse_native_shape"] = "export-only (not dispatch)"
        dispatch_summary = None
        if muse_secret is not None and source_root is not None:
            try:
                profile_preflight = adap.preflight_candidate_profile(
                    _candidate_exec, candidate_home="/home/paseo/.paseo")
            except adap.AdapterBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except adap.AdapterError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
            result["subject"]["muse_profile_preflight"] = profile_preflight
            result["checks"]["muse_profile_preflight"] = "PASS"
            # Record the owned test BEFORE possible dispatch so UNKNOWN occurrence
            # retains a usable exact reference (bounded readback, never blind resend).
            Path(owned_test_path).write_text(json.dumps({
                "schema_version": SCHEMA_VERSION, "test_id": test_id,
                "attempt_nonce": attempt_nonce,
                "container": {"name": name, "id": created_id},
                "daemon": daemon_ref, "image_id": image_id,
                "dispatch": {"state": "pending"},
            }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            prompt = f"M07-T05 synthetic smoke {test_id} (no inference claim)"
            # Candidate-local dispatch through the staged candidate-env loader
            # (reads META_API_KEY_FILE inside the candidate, exports
            # META_API_KEY for the guard/Pi process) execing the canonical
            # guard PROMPT form. The extended guard forwards ONLY the three
            # nonsecret correlation/pointer vars via supported `paseo run
            # --env` (pinned run.js parseRunEnv → createAgent.env →
            # launchContext → Pi subprocess env); CLI-inherited variables are
            # never relied upon. Exact daemon-internal delivery is simulated
            # by the fake boundary; the argv contract is asserted in tests.
            # Re-observe the connected daemon immediately before the effect.
            # A same-home replacement is not the daemon whose startup/catalog
            # was verified; never silently reconnect and dispatch into it.
            try:
                current_daemon = adap.observe_daemon_status(
                    _candidate_exec, candidate_home="/home/paseo/.paseo",
                    expected_version=str(expected_paseo))
            except adap.AdapterBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except adap.AdapterError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
            if current_daemon != daemon_ref:
                raise ValidationError("candidate daemon changed before guarded dispatch")
            dg = _exec(["bash", "-c",
                        f"# guarded-dispatch\nM07_T05_TEST_ID={test_id} M07_T05_WITNESS_FILE={WITNESS_CANDIDATE_PATH} "
                        f"{MUSE_POINTER_ENV}={MUSE_SECRET_TARGET} "
                        f"bash /home/paseo/.pi/agent/bin/m07-t05-candidate-env.sh "
                        f"/home/paseo/.pi/agent/bin/run-llm-test.sh {json.dumps(prompt)} /tmp"],
                       timeout=120, check=False)
            if dg.returncode is None:
                raise ValidationUnknown("guarded dispatch occurrence unknown; preserving test object")
            # Witness aggregation for THIS owned test (request+response+terminal).
            wr = _exec(["sh", "-c", f"# witness-read\ncat {WITNESS_CANDIDATE_PATH}"], timeout=30, check=False)
            events = []
            if wr.returncode == 0 and (wr.stdout or "").strip():
                for ln in (wr.stdout or "").strip().splitlines():
                    try:
                        doc = json.loads(ln)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if isinstance(doc, dict) and doc.get("test_id") == test_id:
                        events.append(doc)
            # Caller-supplied observed dicts are untrusted claims, never proof.
            if isinstance(muse_observed_effective, dict) and events:
                for e in [x for x in events if x.get("kind") == "request"]:
                    if e.get("model") and muse_observed_effective.get("model") and e["model"] != muse_observed_effective["model"]:
                        raise ValidationError("fake caller witness contradicts candidate observation")
                    if e.get("effort") and muse_observed_effective.get("thinking") and e["effort"] != muse_observed_effective["thinking"]:
                        raise ValidationError("fake caller witness contradicts candidate observation")
            agg = adap.aggregate_witness(events, test_id=test_id, expected_model=FIXED_MODEL)
            result["subject"]["muse_witness_events"] = len(events)
            # Aggregate UNKNOWN stays UNKNOWN (preserves owned refs, no rm, no
            # resend); only terminal FAIL becomes a validation failure.
            if agg["gate"] == "UNKNOWN":
                raise ValidationUnknown("guarded dispatch occurrence unknown; preserving test object")
            if dg.returncode != 0 or agg["gate"] != "PASS":
                raise ValidationError(f"guarded dispatch failed: {agg['reason']}")
            result["checks"]["muse_dispatch"] = "PASS"
            result["checks"]["muse_effective_profile"] = "PASS"
            result["subject"]["muse_observed_effective"] = agg.get("observed")
            dispatch_summary = {"test_id": test_id, "events": len(events)}
            # Owned-child inspection through supported agent commands: the
            # dispatched agent is the exactly-one agent titled with this
            # owned test_id (guard appends it to the fixed title). Inspect
            # corroborates provider/model/EFFECTIVE thinking/usage against
            # the witness; a clamped/downgraded effective profile or zero
            # token consumption observed here fails even with witness PASS.
            try:
                child = adap.inspect_owned_agent(
                    _candidate_exec, candidate_home="/home/paseo/.paseo",
                    expected_title=f"LLM-TEST:{FIXED_MODEL}:{FIXED_THINKING}:{test_id}")
            except adap.AdapterBlocked as exc:
                raise ValidationBlocked(_sanitize(str(exc), 200)) from exc
            except adap.AdapterError as exc:
                raise ValidationError(_sanitize(str(exc), 200)) from exc
            if child.get("thinking") != (agg.get("observed") or {}).get("thinking"):
                raise ValidationError("owned child effective profile contradicts witness")
            result["subject"]["muse_owned_child"] = child
            result["checks"]["muse_owned_child"] = "PASS"
            dispatch_summary["agent"] = child.get("id")
        elif muse_observed_effective is not None or daemon_info is not None or pi_info is not None:
            raise ValidationError("caller-supplied daemon/Pi/effective claims are not candidate observations")
        else:
            result["checks"]["muse_dispatch"] = "SKIP"
            result["checks"]["muse_effective_profile"] = "SKIP"
        # Owned test object (exact refs for bounded readback without resend).
        owned_test = {
            "schema_version": SCHEMA_VERSION, "test_id": test_id, "attempt_nonce": attempt_nonce,
            "container": {"name": name, "id": created_id}, "daemon": daemon_ref,
            "image_id": image_id, "dispatch": dispatch_summary,
        }
        Path(owned_test_path).write_text(json.dumps(owned_test, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        result["subject"]["owned_test"] = owned_test_path
        # Real-mode gate: the path EXISTS structurally (not hardcoded false).
        if real_mode:
            required = ["registry_digest", "image_mapping", "image_config", "frozen_chain", "companion_binding",
                        "policy_binding", "daemon_binding", "pi_binding", "codex_catalog",
                        "codex_auth", "codex_health", "muse_guard_readback",
                        "muse_policy_readback", "muse_dispatch", "muse_effective_profile",
                        "muse_owned_child", "muse_profile_preflight"]
            for k in required:
                if result["checks"].get(k) != "PASS":
                    raise ValidationBlocked(f"real validation requires {k} PASS")
            result["status"] = "PASS"
            result["terminal_class"] = "terminal"
            result["real_validation_satisfied"] = True
            result["real_reason"] = "completed guarded dispatch with aggregated witness + all bindings PASS"
        else:
            result["status"] = "PASS"
            result["terminal_class"] = "terminal"
            result["real_validation_satisfied"] = False
            result["real_reason"] = "fixture/rehearsal never satisfies final validation"
    except ValidationBlocked as exc:
        result.update(status="BLOCKED", reason=_sanitize(str(exc)), terminal_class="terminal")
        result["real_validation_satisfied"] = False
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        result.update(status="FAIL", reason=_sanitize(str(exc)), terminal_class="terminal")
        result["real_validation_satisfied"] = False
    except ValidationUnknown as exc:
        result.update(status="UNKNOWN", reason="guarded occurrence unknown; no replay",
                      terminal_class="unknown",
                      owned_reference=owned_test_path or (str(work) if work is not None else None),
                      owned_container={"name": name, "id": created_id} if container_created else None,
                      owned_daemon=daemon_ref)
        result["real_validation_satisfied"] = False
    except subprocess.TimeoutExpired as exc:
        result.update(status="UNKNOWN", reason="guarded occurrence unknown; no replay",
                      terminal_class="unknown",
                      owned_reference=owned_test_path or (str(work) if work is not None else None),
                      owned_container={"name": name, "id": created_id} if container_created else None,
                      owned_daemon=daemon_ref)
        result["real_validation_satisfied"] = False
    finally:
        _is_unknown = result.get("status") == "UNKNOWN"
        try:
            if shutil.which("docker") and container_created and work is not None and attempt_nonce is not None and not _is_unknown:
                cur = run(["docker", "inspect", created_id or name], check=False)
                if cur.returncode == 0:
                    try:
                        cur_obj = json.loads(cur.stdout)[0]
                    except (json.JSONDecodeError, IndexError, KeyError):
                        cur_obj = {}
                    if _container_owned(cur_obj, work, network, expected_image_id=image_id,
                                        expected_nonce=attempt_nonce,
                                        expected_container_id=created_id,
                                        expected_secret_sources=mounted_secrets or None,
                                        expected_user=f"{uid}:{gid}"):
                        # Remove by immutable ID, never a mutable name: a replaced
                        # same-name foreign object is never removed here.
                        run(["docker", "rm", "-f", created_id or name], check=False)
            # else: UNKNOWN preserves the container; foreign never removed.
        except (ValidationBlocked, ValidationError, ValidationUnknown):
            pass
        try:
            # Never erase work while a live container still mounts it. A nonzero
            # or failed ownership inspection is UNCERTAIN (not verified absence):
            # preserve the work so a later authorized caller can inspect.
            _live_mounts_work = False
            _inspect_uncertain = False
            try:
                if work is not None and shutil.which("docker"):
                    _lc = run(["docker", "inspect", name], check=False)
                    if _lc.returncode != 0:
                        _inspect_uncertain = True
                    else:
                        try:
                            _lobj = json.loads(_lc.stdout)[0]
                        except (json.JSONDecodeError, IndexError, KeyError):
                            _lobj = {}
                        for _m in (_lobj.get("Mounts") or []):
                            _s = _canonical(str(_m.get("Source", "")))
                            if _s is not None and work is not None:
                                try:
                                    _w = work.resolve()
                                    if _s == _w or _w in _s.parents:
                                        _live_mounts_work = True
                                except OSError:
                                    pass
            except (ValidationBlocked, ValidationError, ValidationUnknown):
                _live_mounts_work = True  # inspection failed → preserve
                _inspect_uncertain = True
            if _inspect_uncertain:
                _live_mounts_work = True  # nonzero/failed readback ≠ verified absence
            if (work is not None and not _is_unknown and not _live_mounts_work and attempt_nonce is not None
                    and _owned_work(work, Path(state_root), nonce=attempt_nonce, candidate_id=digest)):
                shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
        try:
            if network_created and shutil.which("docker") and not _is_unknown and attempt_nonce is not None:
                _remove = False
                try:
                    _nc = run(["docker", "network", "inspect", network], check=False)
                    if _nc.returncode == 0:
                        try:
                            _nobj = json.loads(_nc.stdout or "[]")
                            _nobj = _nobj[0] if isinstance(_nobj, list) and _nobj else {}
                        except (json.JSONDecodeError, IndexError):
                            _nobj = {}
                        _remove = _network_owned(_nobj, expected_nonce=attempt_nonce,
                                                expected_network_id=acquired_network_id)
                    # inspect failure/missing ownership/ID mismatch → preserve.
                except (ValidationBlocked, ValidationError, ValidationUnknown):
                    _remove = False
                if _remove:
                    # Remove by immutable network ID when acquired, else the
                    # verified-owned name; a replaced same-nonce network is
                    # never removed.
                    run(["docker", "network", "rm", acquired_network_id or network], check=False)
        except (ValidationBlocked, ValidationError, ValidationUnknown):
            pass
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
    p.add_argument("--handoff-file", type=Path)
    p.add_argument("--build-input-file", type=Path)
    p.add_argument("--tested-image-file", type=Path)
    p.add_argument("--build-record", type=Path)
    p.add_argument("--publication-file", type=Path)
    p.add_argument("--companion-bundle", type=Path)
    p.add_argument("--muse-secret", type=Path)
    a = p.parse_args()
    _comp = None
    if a.companion_bundle is not None:
        _comp = json.loads(Path(a.companion_bundle).read_text(encoding="utf-8"))
    result = validate(repository=a.repository, digest=a.digest, output=a.output,
                      state_root=a.state_root, uid=a.uid, gid=a.gid, network=a.network,
                      codex_secret=a.codex_secret, codex_base_url=a.codex_base_url,
                      codex_model=a.codex_model, execution_class=a.execution_class,
                      source_root=a.source_root, companion_bundle=_comp,
                      candidate_file=a.candidate_file, handoff_file=a.handoff_file,
                      build_input_file=a.build_input_file,
                      tested_image_file=a.tested_image_file,
                      build_record=a.build_record, publication_file=a.publication_file,
                      muse_secret=a.muse_secret)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else (3 if result["status"] == "BLOCKED" else (4 if result["status"] == "UNKNOWN" else 2))


if __name__ == "__main__":
    raise SystemExit(main())
