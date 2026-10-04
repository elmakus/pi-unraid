#!/usr/bin/env python3
"""Prepare and package one exact M03 candidate build without re-resolution."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SCHEMA_VERSION = 1


class CandidateBuildError(RuntimeError):
    pass


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise CandidateBuildError('hash input is not a regular file')
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def load_json_bytes(path: Path) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateBuildError(f"unreadable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise CandidateBuildError(f"JSON object required: {path}")
    return value, raw


def load_buildx(root: Path):
    path = root / "scripts" / "paseo_buildx.py"
    spec = importlib.util.spec_from_file_location("paseo_buildx_candidate_stage", path)
    if spec is None or spec.loader is None:
        raise CandidateBuildError(f"cannot load build verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPANION_SOURCE_REL = Path("config/pi-agent")
COMPANION_SCHEMA_VERSION = 1
VALIDATION_SOURCE_FILES = (
    'scripts/paseo_tower_validator.py',
    'scripts/paseo_candidate_muse_adapter.py',
    'scripts/paseo_codex_noninference.py',
    'scripts/paseo_codex_candidate_check.py',
    'scripts/pi_instruction_plane.py',
    'scripts/paseo_candidate_build.py',
    'scripts/resolve-paseo-candidate.py',
    'scripts/paseo_core_compat.py',
    'scripts/paseo_independent_resolution.py',
)


def load_instruction_plane():
    # Installer rules come from this builder's own tooling (not from the
    # candidate source under inspection) so the declared identity is exactly
    # what ``apply`` enforces.
    path = Path(__file__).resolve().parent / "pi_instruction_plane.py"
    spec = importlib.util.spec_from_file_location("pi_instruction_plane_companion_stage", path)
    if spec is None or spec.loader is None:
        raise CandidateBuildError(f"cannot load instruction-plane installer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def companion_bundle_identity(source_root: Path) -> dict:
    """Declare the frozen companion policy/provider/instruction bundle.

    The identity (file set, per-path modes, content digest) is computed with
    the installer's own ``safe_files``/``managed_mode``/``digest_source`` so
    the declared binding is exactly what ``apply`` enforces: ``bin/*`` tools
    deploy as ``0755``, every other instruction file as ``0644``. The payload
    itself is delivered by the instruction plane from this frozen source, not
    by the image; this record binds the image inputs and the companion to one
    source state for eligibility. Secret-free: paths, modes and digests only.
    """
    try:
        installer = load_instruction_plane()
        source = source_root / COMPANION_SOURCE_REL
        files = installer.safe_files(source)
        modes = {rel.as_posix(): f"{installer.managed_mode(rel):04o}" for rel in files}
        digest = installer.digest_source(source, files)
    except CandidateBuildError:
        raise
    except (SystemExit, Exception) as exc:
        # Installer refuses unsafe/missing sources via SystemExit; either way
        # the bundle is unverifiable and must fail closed, never bind.
        raise CandidateBuildError(f"companion bundle is unverifiable: {exc}") from exc
    return {
        "schema_version": COMPANION_SCHEMA_VERSION,
        "source": COMPANION_SOURCE_REL.as_posix(),
        "files": [rel.as_posix() for rel in files],
        "modes": modes,
        "source_digest": digest,
        # Existing prepared/build/package companion envelope freezes the
        # host-side validation behavior too; no post-stage digest blessing.
        "validation_sources": {rel: sha256_file(source_root / rel)
                               for rel in VALIDATION_SOURCE_FILES},
    }


def verify_companion_binding(source_root: Path, declared: dict) -> dict:
    """Fail closed unless the source tree matches the declared binding.

    Changed content, added/removed files, wrong modes, wrong digest, missing
    source or malformed declarations never preserve the same binding: each
    raises ``CandidateBuildError`` instead of reporting bound state.
    """
    if not isinstance(declared, dict):
        raise CandidateBuildError("companion binding declaration must be an object")
    if declared.get("schema_version") != COMPANION_SCHEMA_VERSION:
        raise CandidateBuildError("companion binding schema is unsupported")
    if declared.get("source") != COMPANION_SOURCE_REL.as_posix():
        raise CandidateBuildError("companion binding source is not the frozen instruction bundle")
    declared_files = declared.get("files")
    declared_modes = declared.get("modes")
    declared_digest = declared.get("source_digest")
    if not isinstance(declared_files, list) or not all(isinstance(item, str) for item in declared_files):
        raise CandidateBuildError("companion binding files must be a list of paths")
    if not isinstance(declared_modes, dict) or not isinstance(declared_digest, str):
        raise CandidateBuildError("companion binding modes/digest are malformed")
    actual = companion_bundle_identity(source_root)
    if actual["files"] != declared_files:
        missing = sorted(set(declared_files) - set(actual["files"]))
        added = sorted(set(actual["files"]) - set(declared_files))
        raise CandidateBuildError(
            f"companion bundle file set changed (missing={missing} added={added})"
        )
    mismatched = sorted(
        rel for rel in declared_files if actual["modes"].get(rel) != declared_modes.get(rel)
    )
    if mismatched:
        raise CandidateBuildError(f"companion bundle modes changed: {mismatched}")
    if actual["source_digest"] != declared_digest:
        raise CandidateBuildError("companion bundle digest mismatch")
    if actual['validation_sources'] != declared.get('validation_sources'):
        raise CandidateBuildError('frozen validation source/configuration mismatch')
    return {
        "status": "bound",
        "source": actual["source"],
        "source_digest": actual["source_digest"],
        "files": len(actual["files"]),
    }


def verify_handoff(
    candidate_path: Path,
    evidence_path: Path,
    accepted_path: Path,
    *,
    source_parent: str,
    expected_source_ref: str,
) -> tuple[dict, bytes, dict, bytes, dict]:
    candidate, candidate_raw = load_json_bytes(candidate_path)
    evidence, evidence_raw = load_json_bytes(evidence_path)
    accepted, _ = load_json_bytes(accepted_path)

    candidate_id = str(candidate.get("candidate_id") or "")
    accepted_id = str(accepted.get("candidate_id") or "")
    if not SHA256.fullmatch(candidate_id) or not SHA256.fullmatch(accepted_id):
        raise CandidateBuildError("candidate identities must be immutable sha256 values")
    if evidence.get("schema_version") != 1 or evidence.get("status") != "update":
        raise CandidateBuildError("handoff evidence is not a material-change record")
    if evidence.get("candidate_id") != candidate_id:
        raise CandidateBuildError("handoff candidate identity mismatch")
    if evidence.get("accepted_candidate_id") != accepted_id:
        raise CandidateBuildError("handoff accepted-candidate identity mismatch")
    if candidate_id == accepted_id:
        raise CandidateBuildError("material-change handoff cannot equal the accepted candidate")
    if evidence.get("candidate_file_sha256") != sha256_bytes(candidate_raw):
        raise CandidateBuildError("handoff candidate byte digest mismatch")
    if evidence.get("source_sha") != source_parent:
        raise CandidateBuildError("candidate branch parent does not match frozen discovery source SHA")
    if evidence.get("source_ref") != expected_source_ref:
        raise CandidateBuildError("candidate discovery source ref is not the expected default branch")
    return candidate, candidate_raw, evidence, evidence_raw, accepted


def _component(candidate: dict, name: str) -> dict:
    try:
        value = candidate["components"][name]
    except (KeyError, TypeError) as exc:
        raise CandidateBuildError(f"candidate lacks component {name}") from exc
    if not isinstance(value, dict):
        raise CandidateBuildError(f"candidate component is invalid: {name}")
    return value


def replace_exact(text: str, old: str, new: str, description: str) -> str:
    if old == new:
        if old not in text:
            raise CandidateBuildError(f"Dockerfile lacks accepted {description}")
        return text
    count = text.count(old)
    if count != 1:
        raise CandidateBuildError(
            f"Dockerfile accepted {description} must occur exactly once; found {count}"
        )
    return text.replace(old, new, 1)


def render_dockerfile(text: str, accepted: dict, candidate: dict) -> str:
    """Render only candidate-bound Dockerfile literals from accepted to candidate."""
    a = accepted
    c = candidate

    mappings: list[tuple[str, str, str]] = [
        (
            f"FROM {_component(a, 'paseo')['artifact']['reference']}",
            f"FROM {_component(c, 'paseo')['artifact']['reference']}",
            "Paseo parent reference",
        ),
        (
            f'io.pi-unraid.candidate-id="{a["candidate_id"]}"',
            f'io.pi-unraid.candidate-id="{c["candidate_id"]}"',
            "candidate label",
        ),
        (
            f'PI_UNRAID_CANDIDATE_ID="{a["candidate_id"]}"',
            f'PI_UNRAID_CANDIDATE_ID="{c["candidate_id"]}"',
            "candidate environment identity",
        ),
    ]

    label_components = (
        ("paseo", "io.pi-unraid.paseo-version"),
        ("pi", "io.pi-unraid.pi-version"),
        ("specpi", "io.pi-unraid.specpi-version"),
        ("pi_mcp_adapter", "io.pi-unraid.pi-mcp-adapter-version"),
        ("playwright", "io.pi-unraid.playwright-version"),
    )
    for name, label in label_components:
        mappings.append(
            (
                f'{label}="{_component(a, name)["version"]}"',
                f'{label}="{_component(c, name)["version"]}"',
                f"{name} label",
            )
        )

    env_components = (
        ("pi", "PI_UNRAID_PI_VERSION"),
        ("specpi", "PI_UNRAID_SPECPI_VERSION"),
        ("pi_mcp_adapter", "PI_UNRAID_PI_MCP_ADAPTER_VERSION"),
        ("playwright", "PI_UNRAID_PLAYWRIGHT_VERSION"),
        ("github_cli", "PI_UNRAID_GH_VERSION"),
        ("docker_cli", "PI_UNRAID_DOCKER_CLI_VERSION"),
        ("docker_compose", "PI_UNRAID_DOCKER_COMPOSE_VERSION"),
    )
    for name, env_name in env_components:
        mappings.append(
            (
                f'{env_name}="{_component(a, name)["version"]}"',
                f'{env_name}="{_component(c, name)["version"]}"',
                f"{name} environment version",
            )
        )

    for old, new, description in mappings:
        text = replace_exact(text, old, new, description)

    for name in ("github_cli", "docker_compose"):
        old_digest = _component(a, name)["artifact"]["digest"].removeprefix("sha256:")
        new_digest = _component(c, name)["artifact"]["digest"].removeprefix("sha256:")
        text = replace_exact(text, old_digest, new_digest, f"{name} artifact digest")

    return text


def git_source_identity(source_root: Path, source_head: str, source_parent: str,
                        source_ref: str) -> dict:
    """Read the immutable Git subject AND every used checkout byte/mode.

    No fetch, checkout or mutation. Git's object database proves the commit/tree;
    a clean-looking index or a caller's nine-file map is not the proof. Ignored
    and untracked build inputs are rejected too. Only Git administration and
    Python interpreter caches (not copied into the stage) are excluded.
    """
    git_env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    git_env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null')
    def git(*args):
        p = subprocess.run(['git', '--no-replace-objects', '-C', str(source_root), *args],
                           env=git_env, capture_output=True, timeout=30)
        if p.returncode:
            raise CandidateBuildError('immutable Git source is unavailable')
        return p.stdout
    if not all(re.fullmatch(r'[0-9a-f]{40}', v or '') for v in (source_head, source_parent)):
        raise CandidateBuildError('exact Git head/parent required')
    if not re.fullmatch(r'refs/heads/[A-Za-z0-9._/-]+', source_ref or ''):
        raise CandidateBuildError('discovery branch ref required')
    if git('rev-parse', 'HEAD').decode().strip() != source_head:
        raise CandidateBuildError('used checkout is not the declared source head')
    commit = git('cat-file', 'commit', source_head)
    headers = commit.split(b'\n\n', 1)[0].splitlines()
    parents = [v[7:].decode() for v in headers if v.startswith(b'parent ')]
    if parents != [source_parent]:
        raise CandidateBuildError('source commit does not have the exact single discovery parent')
    tree = next(v[5:].decode() for v in headers if v.startswith(b'tree '))
    # Discovery may race forward; it must still contain the frozen parent.
    ref = source_ref
    if subprocess.run(['git', '--no-replace-objects', '-C', str(source_root),
                       'show-ref', '--verify', '--quiet', ref], env=git_env, capture_output=True).returncode:
        ref = 'refs/remotes/origin/' + source_ref.removeprefix('refs/heads/')
    git('merge-base', '--is-ancestor', source_parent, ref)
    files = {}
    for row in git('ls-tree', '-rz', '--full-tree', source_head).split(b'\0'):
        if not row:
            continue
        header, raw_path = row.split(b'\t', 1)
        mode, kind, oid = header.decode().split()
        rel = raw_path.decode()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise CandidateBuildError('unsupported source tree member')
        raw = git('cat-file', 'blob', oid)
        files[rel] = {'mode': mode, 'sha256': sha256_bytes(raw)}
    verify_tree_bytes(source_root, files)
    return {'schema_version': 1, 'commit_sha256': sha256_bytes(commit),
            'tree': tree, 'files': files}


def verify_tree_bytes(root: Path, files: dict, *, generated=()) -> None:
    """Exact file-set/content/executable proof, including ignored inputs."""
    if not isinstance(files, dict) or not files:
        raise CandidateBuildError('source tree file map is absent')
    actual = set()
    for p in root.rglob('*'):
        rel = p.relative_to(root)
        if '.git' in rel.parts or '__pycache__' in rel.parts or p.name.endswith('.pyc'):
            continue
        if p.is_symlink():
            raise CandidateBuildError('source/stage symlink is not a frozen regular file')
        if p.is_dir():
            continue
        name = rel.as_posix()
        if name in generated:
            continue
        actual.add(name)
        value = files.get(name)
        if (not isinstance(value, dict) or set(value) != {'mode', 'sha256'}
                or value['mode'] not in ('100644', '100755')
                or value['sha256'] != sha256_file(p)
                or bool(p.stat().st_mode & 0o111) != (value['mode'] == '100755')):
            raise CandidateBuildError('source/stage bytes or executable configuration changed')
    if actual != set(files):
        raise CandidateBuildError('source/stage file set changed')


def verify_prepared_source(source_root: Path, prepared: dict, candidate: dict,
                           *, stage_root: Path | None = None) -> dict:
    """Reconstruct the actual prepare transformation, not a declared readback."""
    proof = git_source_identity(source_root, prepared.get('source_head'),
                                prepared.get('source_parent'), prepared.get('source_ref'))
    if prepared.get('source_identity') != proof:
        raise CandidateBuildError('prepared immutable source proof mismatch')
    accepted, accepted_raw = load_json_bytes(source_root / 'config/paseo-candidate.json')
    if prepared.get('accepted_candidate_id') != accepted.get('candidate_id'):
        raise CandidateBuildError('prepared accepted source candidate mismatch')
    original = (source_root / 'Dockerfile').read_text()
    rendered = render_dockerfile(original, accepted, candidate)
    expected_files = dict(proof['files'])
    expected_files['Dockerfile'] = {**expected_files['Dockerfile'],
                                  'sha256': sha256_bytes(rendered.encode())}
    # The candidate byte link is distinct from its resolution identity.
    expected_files['config/paseo-candidate.json'] = {
        **expected_files['config/paseo-candidate.json'],
        'sha256': prepared.get('candidate_file_sha256')}
    if prepared.get('staged_files') != expected_files:
        raise CandidateBuildError('prepared transformation file map mismatch')
    candidate_raw = (stage_root / 'config/paseo-candidate.json').read_bytes() if stage_root else None
    if candidate_raw is not None:
        if sha256_bytes(candidate_raw) != prepared.get('candidate_file_sha256'):
            raise CandidateBuildError('staged candidate bytes changed')
        expected_files['config/paseo-candidate.json'] = {
            **expected_files['config/paseo-candidate.json'], 'sha256': sha256_bytes(candidate_raw)}
        verify_tree_bytes(stage_root, expected_files,
                          generated=('.pi-unraid-candidate-build-input.json',))
    buildx = load_buildx(source_root)
    readback = buildx.verify_build_inputs(candidate, rendered, stage_root or source_root)
    if prepared.get('build_readback') != readback:
        raise CandidateBuildError('prepared build configuration readback mismatch')
    return proof


def prepare_context(
    *,
    candidate_path: Path,
    evidence_path: Path,
    accepted_path: Path,
    source_root: Path,
    stage_dir: Path,
    source_head: str,
    source_parent: str,
    expected_source_ref: str,
) -> dict:
    if stage_dir.exists():
        raise CandidateBuildError(f"stage directory already exists: {stage_dir}")
    if not source_head.strip() or not source_parent.strip():
        raise CandidateBuildError("source head/parent are required")

    candidate, candidate_raw, evidence, evidence_raw, accepted = verify_handoff(
        candidate_path,
        evidence_path,
        accepted_path,
        source_parent=source_parent,
        expected_source_ref=expected_source_ref,
    )
    dockerfile_path = source_root / "Dockerfile"
    try:
        original_dockerfile = dockerfile_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CandidateBuildError(f"source Dockerfile is unreadable: {dockerfile_path}") from exc

    # Non-Git compatibility fixtures retain explicit unbound provenance; they
    # cannot pass the real Tower source gate. Real checkouts prove every input.
    source_identity = (git_source_identity(source_root, source_head, source_parent, expected_source_ref)
                       if (source_root / '.git').exists() else None)
    rendered = render_dockerfile(original_dockerfile, accepted, candidate)
    shutil.copytree(
        source_root,
        stage_dir,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )
    staged_dockerfile = stage_dir / "Dockerfile"
    staged_dockerfile.write_text(rendered, encoding="utf-8")
    staged_candidate = stage_dir / "config" / "paseo-candidate.json"
    staged_candidate.write_bytes(candidate_raw)

    buildx = load_buildx(source_root)
    try:
        readback = buildx.verify_build_inputs(candidate, rendered, stage_dir)
    except Exception as exc:
        raise CandidateBuildError(f"rendered context failed exact build-input verification: {exc}") from exc

    companion = companion_bundle_identity(source_root)
    # Enforce the declared binding against the actual staged payload before
    # any record is written: a divergent staged copy fails here, not downstream.
    verify_companion_binding(stage_dir, companion)
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "prepared",
        "candidate_id": candidate["candidate_id"],
        "accepted_candidate_id": accepted["candidate_id"],
        "candidate_file_sha256": sha256_bytes(candidate_raw),
        "handoff_evidence_sha256": sha256_bytes(evidence_raw),
        "source_head": source_head,
        "source_parent": source_parent,
        "source_ref": evidence["source_ref"],
        "stage_dir": str(stage_dir),
        "build_readback": readback,
        "source_identity": source_identity,
        "companion_bundle": companion,
    }
    if source_identity is not None:
        staged_files = dict(source_identity['files'])
        staged_files['Dockerfile'] = {**staged_files['Dockerfile'],
                                     'sha256': sha256_bytes(rendered.encode())}
        staged_files['config/paseo-candidate.json'] = {
            **staged_files['config/paseo-candidate.json'], 'sha256': sha256_bytes(candidate_raw)}
        verify_tree_bytes(stage_dir, staged_files)
        result['staged_files'] = staged_files
    (stage_dir / ".pi-unraid-candidate-build-input.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def run_checked(argv: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CandidateBuildError(f"command failed to execute: {argv[0]}") from exc
    if proc.returncode != 0:
        raise CandidateBuildError(
            f"command failed ({proc.returncode}): {' '.join(argv)}: "
            f"{(proc.stderr or proc.stdout)[-2000:]}"
        )
    return proc


def package_tested_image(
    *,
    candidate_path: Path,
    handoff_evidence_path: Path,
    build_record_path: Path,
    archive_path: Path,
    evidence_path: Path,
    source_head: str,
    build_input_path: Path,
) -> dict:
    candidate, candidate_raw = load_json_bytes(candidate_path)
    handoff, handoff_raw = load_json_bytes(handoff_evidence_path)
    record, record_raw = load_json_bytes(build_record_path)

    candidate_id = candidate.get("candidate_id")
    if not SHA256.fullmatch(str(candidate_id or "")):
        raise CandidateBuildError("candidate identity is invalid")
    if handoff.get("candidate_id") != candidate_id:
        raise CandidateBuildError("build package handoff candidate mismatch")
    if handoff.get("candidate_file_sha256") != sha256_bytes(candidate_raw):
        raise CandidateBuildError("build package candidate byte digest mismatch")
    if (record.get("candidate") or {}).get("candidate_id") != candidate_id:
        raise CandidateBuildError("build record candidate mismatch")
    phases = record.get("phases") or {}
    for phase in ("resolution_readback", "builder_ensure", "build", "test"):
        if (phases.get(phase) or {}).get("status") != "ok":
            raise CandidateBuildError(f"build record phase is not GREEN: {phase}")

    # R2 companion gate: the prepared declaration and its full
    # source/candidate/handoff/prepared/build linkage are checked here,
    # BEFORE any docker invocation. Omission is not a silent bypass: the
    # build-input record is required, legacy unbound build records are
    # rejected, and any divergence fails closed with zero external calls.
    build_input = _require_build_input_record(build_input_path)
    companion_declared = _require_companion_linkage(
        build_input, candidate_id, candidate_raw, handoff, handoff_raw, source_head
    )
    record_companion = record.get("companion_bundle")
    if not isinstance(record_companion, dict):
        raise CandidateBuildError(
            "build record lacks the bound companion bundle: "
            "unbound legacy records are not R2-eligible"
        )
    if record_companion != companion_declared:
        raise CandidateBuildError("build-record/prepared companion binding mismatch")

    if build_input.get('source_identity') is not None and record.get('prepared_source') != build_input:
        raise CandidateBuildError('built/prepared source configuration mismatch')
    tag = str(record.get("tag") or "")
    image_id = str((record.get("image") or {}).get("id") or "")
    if not tag or not SHA256.fullmatch(image_id):
        raise CandidateBuildError("build record lacks exact tested image identity")

    companion_declared = None
    if build_input_path is not None:
        # Retain and check the prepared companion declaration through the
        # package evidence before any external action: a missing/malformed
        # declaration or an inconsistent candidate linkage fails here, before
        # any docker invocation. Omitted input preserves the prior behavior.
        try:
            build_input = json.loads(Path(build_input_path).read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise CandidateBuildError(f"build-input record is unreadable: {exc}") from exc
        if not isinstance(build_input, dict):
            raise CandidateBuildError("build-input record must be an object")
        if build_input.get("candidate_id") != candidate_id:
            raise CandidateBuildError("build-input record candidate mismatch")
        companion_declared = build_input.get("companion_bundle")
        if not isinstance(companion_declared, dict):
            raise CandidateBuildError("build-input record lacks companion bundle declaration")
        if companion_declared.get("schema_version") != COMPANION_SCHEMA_VERSION:
            raise CandidateBuildError("build-input companion declaration schema is unsupported")
    before = run_checked(["docker", "image", "inspect", tag, "--format", "{{.Id}}"]).stdout.strip()
    if before != image_id:
        raise CandidateBuildError("local tested image no longer matches build record")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        raise CandidateBuildError(f"image archive already exists: {archive_path}")
    run_checked(["docker", "image", "save", "-o", str(archive_path), tag])
    after = run_checked(["docker", "image", "inspect", tag, "--format", "{{.Id}}"]).stdout.strip()
    if after != image_id:
        raise CandidateBuildError("local image identity changed while preserving tested artifact")
    if build_input.get('source_identity') is not None:
        verify_docker_save(archive_path, image_id, tag)

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "tested_image_preserved",
        "candidate_id": candidate_id,
        "accepted_candidate_id": handoff.get("accepted_candidate_id"),
        "candidate_file_sha256": sha256_bytes(candidate_raw),
        "handoff_evidence_sha256": sha256_bytes(handoff_raw),
        "build_record_sha256": sha256_bytes(record_raw),
        "image_id": image_id,
        "image_archive_format": "docker-save",
        "image_archive_sha256": sha256_file(archive_path),
        "source_head": source_head,
        "discovery_source_sha": handoff.get("source_sha"),
        "discovery_source_ref": handoff.get("source_ref"),
    }
    result["companion_bundle"] = companion_declared
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def verify_build_record_configuration(record: dict, prepared: dict, source_root: Path) -> None:
    """Reconstruct the producer's actual Buildx command and internal smoke detail."""
    if record.get('prepared_source') != prepared:
        raise CandidateBuildError('build did not retain exact prepared inputs')
    config = record.get('build_configuration')
    if (not isinstance(config, dict) or set(config) !=
            {'argv', 'progress', 'labels', 'metadata_file', 'with_smoke', 'smoke_profile'}
            or config['with_smoke'] is not True
            or config['smoke_profile'] not in ('core', 'full')
            or config['progress'] not in ('plain', 'auto', 'tty')
            or not isinstance(config['labels'], list)
            or not all(isinstance(v, str) and '=' in v for v in config['labels'])
            or (config['metadata_file'] is not None and not isinstance(config['metadata_file'], str))):
        raise CandidateBuildError('build configuration is malformed or lacks required smoke')
    builder = record.get('builder')
    if not isinstance(builder, dict) or not isinstance(builder.get('name'), str):
        raise CandidateBuildError('actual builder configuration missing')
    buildx = load_buildx(source_root)
    buildx.validate_builder_name(builder['name'])
    argv = ['docker', 'buildx', 'build', '--builder', builder['name'], '--load',
            '--progress', config['progress'], '-t', record.get('tag')]
    cache = record.get('cache')
    if not isinstance(cache, dict):
        raise CandidateBuildError('cache configuration missing')
    if cache.get('local_dir'):
        if not isinstance(cache['local_dir'], str):
            raise CandidateBuildError('cache configuration has incorrect type')
        argv += ['--cache-from', 'type=local,src=' + cache['local_dir'],
                 '--cache-to', 'type=local,mode=max,dest=' + cache['local_dir']]
    for label in config['labels']:
        argv += ['--label', label]
    if config['metadata_file']:
        argv += ['--metadata-file', config['metadata_file']]
    argv += [record.get('context')]
    if config['argv'] != argv or record.get('context') != prepared.get('stage_dir'):
        raise CandidateBuildError('actual Buildx command/context reconstruction mismatch')
    phases = record.get('phases')
    if not isinstance(phases, dict):
        raise CandidateBuildError('build phases missing')
    for name in ('resolution_readback', 'builder_ensure', 'build', 'test'):
        phase = phases.get(name)
        if (not isinstance(phase, dict) or phase.get('status') != 'ok'
                or type(phase.get('duration_ms')) is not int or phase['duration_ms'] < 0
                or not isinstance(phase.get('detail'), dict)):
            raise CandidateBuildError('required build phase schema/type/status rejected')
    readback = phases['resolution_readback']['detail']
    expected = {**prepared['build_readback'],
                'candidate_path': record['candidate']['path'],
                'companion_bundle': prepared['companion_bundle']}
    if readback != expected:
        raise CandidateBuildError('build resolution readback reconstruction mismatch')
    if phases['builder_ensure']['detail'] != {k: v for k, v in builder.items() if k != 'state_dir'}:
        raise CandidateBuildError('builder phase/readback mismatch')
    detail = phases['build']['detail']
    if detail.get('tag') != record.get('tag') or detail.get('image_id') != record['image']['id']:
        raise CandidateBuildError('built image/readback mismatch')
    test = phases['test']['detail']
    expected_names = [name for name, _ in buildx.smoke_suite(record['tag'],
        record['candidate']['path'], Path(record['context']), config['smoke_profile'])]
    smokes = test.get('smokes')
    if (test.get('profile') != config['smoke_profile'] or not isinstance(smokes, list)
            or [v.get('name') for v in smokes if isinstance(v, dict)] != expected_names
            or any(not isinstance(v, dict) or v.get('status') != 'ok'
                or type(v.get('duration_ms')) is not int or v['duration_ms'] < 0 for v in smokes)):
        raise CandidateBuildError('actual smoke dispatch/aggregation mismatch')


def verify_docker_save(archive: Path, image_id: str, tag: str) -> dict:
    """Hash the actual preserved config, inspect format links without extracting."""
    try:
        with tarfile.open(archive, 'r:') as bundle:
            members = bundle.getmembers()
            names = [m.name for m in members]
            if len(names) != len(set(names)):
                raise CandidateBuildError('docker-save duplicate member')
            for m in members:
                rel = Path(m.name)
                if rel.is_absolute() or '..' in rel.parts or not (m.isfile() or m.isdir()):
                    raise CandidateBuildError('docker-save unsafe member')
            manifest_member = bundle.getmember('manifest.json')
            if manifest_member.size > 65536:
                raise CandidateBuildError('docker-save manifest exceeds bound')
            manifest = json.load(bundle.extractfile(manifest_member))
            if (not isinstance(manifest, list) or len(manifest) != 1
                    or not isinstance(manifest[0], dict)):
                raise CandidateBuildError('docker-save must contain one tested image')
            item = manifest[0]
            if (not isinstance(item.get('Config'), str)
                    or item.get('RepoTags') != [tag]
                    or not isinstance(item.get('Layers'), list)
                    or not all(isinstance(v, str) for v in item['Layers'])):
                raise CandidateBuildError('docker-save image/tag/format link mismatch')
            config_member = bundle.getmember(item['Config'])
            if not config_member.isfile() or config_member.size > 1048576:
                raise CandidateBuildError('docker-save image configuration exceeds bound')
            config = bundle.extractfile(config_member).read()
            config_document = json.loads(config)
            if sha256_bytes(config) != image_id or not isinstance(config_document, dict):
                raise CandidateBuildError('docker-save config does not hash to tested local image ID')
            rootfs = config_document.get('rootfs')
            if (not isinstance(rootfs, dict) or rootfs.get('type') != 'layers'
                    or not isinstance(rootfs.get('diff_ids'), list)
                    or len(rootfs['diff_ids']) != len(item['Layers'])
                    or not all(isinstance(v, str) and SHA256.fullmatch(v) for v in rootfs['diff_ids'])):
                raise CandidateBuildError('docker-save rootfs/layer identity links are malformed')
            for layer, diff_id in zip(item['Layers'], rootfs['diff_ids']):
                if not bundle.getmember(layer).isfile():
                    raise CandidateBuildError('docker-save layer missing')
                layer_hash = hashlib.sha256()
                with bundle.extractfile(layer) as stream:
                    for chunk in iter(lambda: stream.read(1048576), b''):
                        layer_hash.update(chunk)
                if 'sha256:' + layer_hash.hexdigest() != diff_id:
                    raise CandidateBuildError('docker-save layer bytes do not match configuration diff-ID')
                # Inspect structure only; never extract candidate filesystem bytes.
                with bundle.extractfile(layer) as stream, tarfile.open(fileobj=stream, mode='r:') as layer_tar:
                    for _ in layer_tar:
                        pass
            if not isinstance(config_document.get('config'), dict):
                raise CandidateBuildError('docker-save runtime configuration is absent')
            return config_document['config']
    except (OSError, tarfile.TarError, KeyError, ValueError, TypeError) as exc:
        raise CandidateBuildError('docker-save archive is malformed') from exc


def _require_build_input_record(build_input_path: Path) -> dict:
    """Load the prepare-stage build-input record, failing closed on omission."""
    if build_input_path is None:
        raise CandidateBuildError(
            "build-input record is required: omission preserves no R2 binding"
        )
    try:
        build_input = json.loads(Path(build_input_path).read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateBuildError(f"build-input record is unreadable: {exc}") from exc
    if not isinstance(build_input, dict):
        raise CandidateBuildError("build-input record must be an object")
    return build_input


def _require_companion_linkage(
    build_input: dict,
    candidate_id: str,
    candidate_raw: bytes,
    handoff: dict,
    handoff_raw: bytes,
    source_head: str,
) -> dict:
    """Check the full prepared identity linkage before any external action.

    Verifies declaration types/digest/modes, the prepared byte digests
    against the actual candidate/handoff inputs, the prepared
    source/candidate/handoff provenance, and the invoking source head.
    Returns the declared companion for retention in the package evidence.
    """
    if build_input.get("schema_version") != SCHEMA_VERSION:
        raise CandidateBuildError("build-input record uses an unsupported schema")
    if build_input.get("status") != "prepared":
        raise CandidateBuildError("build-input record is not a prepared binding")
    if build_input.get("candidate_id") != candidate_id:
        raise CandidateBuildError("build-input record candidate mismatch")
    companion = build_input.get("companion_bundle")
    if not isinstance(companion, dict):
        raise CandidateBuildError("build-input record lacks companion bundle declaration")
    if companion.get("schema_version") != COMPANION_SCHEMA_VERSION:
        raise CandidateBuildError("build-input companion declaration schema is unsupported")
    if companion.get("source") != COMPANION_SOURCE_REL.as_posix():
        raise CandidateBuildError(
            "build-input companion declaration source is not the frozen bundle"
        )
    files = companion.get("files")
    modes = companion.get("modes")
    digest = companion.get("source_digest")
    if (
        not isinstance(files, list)
        or not files
        or not all(isinstance(item, str) and item for item in files)
    ):
        raise CandidateBuildError("build-input companion declaration files are malformed")
    if not isinstance(modes, dict) or set(modes) != set(files):
        raise CandidateBuildError("build-input companion declaration modes are malformed")
    if not SHA256.fullmatch(str(digest or "")):
        raise CandidateBuildError("build-input companion declaration digest is malformed")
    validation = companion.get('validation_sources')
    if (not isinstance(validation, dict) or set(validation) != set(VALIDATION_SOURCE_FILES)
            or any(not isinstance(v, str) or not SHA256.fullmatch(v) for v in validation.values())):
        raise CandidateBuildError('build-input frozen validation source declaration is malformed')
    if build_input.get("candidate_file_sha256") != sha256_bytes(candidate_raw):
        raise CandidateBuildError("build-input prepared candidate digest mismatch")
    if build_input.get("handoff_evidence_sha256") != sha256_bytes(handoff_raw):
        raise CandidateBuildError("build-input prepared handoff digest mismatch")
    if build_input.get("source_parent") != handoff.get("source_sha"):
        raise CandidateBuildError("build-input prepared source-parent mismatch")
    if build_input.get("source_ref") != handoff.get("source_ref"):
        raise CandidateBuildError("build-input prepared source-ref mismatch")
    if build_input.get("source_head") != source_head:
        raise CandidateBuildError("build-input prepared source-head mismatch")
    return companion


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--candidate", type=Path, required=True)
    prepare.add_argument("--handoff-evidence", type=Path, required=True)
    prepare.add_argument("--accepted", type=Path, required=True)
    prepare.add_argument("--source-root", type=Path, required=True)
    prepare.add_argument("--stage-dir", type=Path, required=True)
    prepare.add_argument("--source-head", required=True)
    prepare.add_argument("--source-parent", required=True)
    prepare.add_argument("--expected-source-ref", required=True)

    package = sub.add_parser("package")
    package.add_argument("--candidate", type=Path, required=True)
    package.add_argument("--handoff-evidence", type=Path, required=True)
    package.add_argument("--build-record", type=Path, required=True)
    package.add_argument("--archive", type=Path, required=True)
    package.add_argument("--evidence", type=Path, required=True)
    package.add_argument("--source-head", required=True)
    package.add_argument(
        "--build-input",
        type=Path,
        required=True,
        help="required prepare-stage build-input record carrying the frozen "
        "companion bundle declaration (omission rejects: no silent bypass)",
    )

    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_context(
                candidate_path=args.candidate,
                evidence_path=args.handoff_evidence,
                accepted_path=args.accepted,
                source_root=args.source_root,
                stage_dir=args.stage_dir,
                source_head=args.source_head,
                source_parent=args.source_parent,
                expected_source_ref=args.expected_source_ref,
            )
        else:
            result = package_tested_image(
                candidate_path=args.candidate,
                handoff_evidence_path=args.handoff_evidence,
                build_record_path=args.build_record,
                archive_path=args.archive,
                evidence_path=args.evidence,
                source_head=args.source_head,
                build_input_path=args.build_input,
            )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CandidateBuildError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"candidate build handoff failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
