#!/usr/bin/env python3
"""Trusted Tower final-gate assembler for M07-T06.

Consumes the exact independently GREEN M07-T05 producer record (real
validator output acquired through the shipped ``paseo_tower_validator``
entrypoint), the actual-baseline state round-trip record, frozen
source/companion/policy/launcher bindings, a TYPED predecessor mapping
(``oci``/``local``/``legacy``) and the armed guard binding. Emits one
narrow final-gate record that the single Tower writer consumes before any
registry create/update.

Caller generic GREEN/PASS strings, fixture/rehearsal records or arbitrary
JSON are never evidence: every required check must be terminal PASS AND
every fixed-policy/effective/daemon/Pi value must read back exactly.
The fixed ``meta/muse-spark-1.3-contributor/max`` profile with no fallback
is value-enforced here (not merely label-checked), and predecessor OCI
manifest vs platform-local namespaces stay distinctly typed end to end.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paseo_legacy_identity import (  # noqa: E402  genuine shipped mapping authority
    LegacyIdentityError,
    validate as validate_predecessor_shape,
    verify_anchor,
)
import paseo_tower_validator as tower_validator  # noqa: E402  shipped producer authority
import paseo_state_roundtrip as state_prove  # noqa: E402  shipped round-trip authority
import paseo_transaction_guard as guard_mod  # noqa: E402  shipped guard authority
import paseo_candidate_build as build_mod  # noqa: E402  shipped companion authority

SCHEMA_VERSION = 2
VALIDATOR_SCHEMA = 2
FIXED_PROVIDER = "meta"
FIXED_MODEL = "muse-spark-1.3-contributor"
FIXED_THINKING = "max"
FIXED_MODEL_ID = f"{FIXED_PROVIDER}/{FIXED_MODEL}"
FIXED_PI_PATH = "/usr/local/bin/pi"
FIXED_DAEMON_HOME = "/home/paseo/.paseo"
FIXED_FRAGMENT_MODE = "0644"
FIXED_EFFECTIVE_MODE = "0600"

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")

# Exact validator real-mode required checks (M07-T05 producer contract).
REQUIRED_VALIDATOR_CHECKS = (
    "registry_digest",
    "image_mapping",
    "image_config",
    "frozen_chain",
    "companion_binding",
    "policy_binding",
    "daemon_binding",
    "pi_binding",
    "codex_catalog",
    "codex_auth",
    "codex_health",
    "muse_guard_readback",
    "muse_policy_readback",
    "muse_dispatch",
    "muse_effective_profile",
    "muse_owned_child",
    "muse_profile_preflight",
    "applied_payload_interval",
    "muse_effective_config",
    "muse_effective_readback",
)

# Source/isolation bindings required by P4 M07-T06 on top of the producer
# required list. The validator emits these as PASS on the real path; a
# missing/SKIP/FAIL value leaves the final gate unsatisfied.
REQUIRED_SOURCE_ISOLATION_CHECKS = (
    "immutable_source_configuration",
    "runtime",
    "uid_gid",
    "mount_isolation",
    "network_isolation",
    "secret_isolation",
)

REQUIRED_STATE_CHECKS = (
    "baseline_clone_isolated",
    "candidate_state_mutation",
    "previous_runtime_reopen",
    "direct_skip_path",
)


class FinalGateError(RuntimeError):
    pass


def _req_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise FinalGateError(f"{label} must be an immutable sha256 digest")
    return value


def _req_git_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not GIT_SHA.fullmatch(value):
        raise FinalGateError(f"{label} must be an exact 40-hex Git SHA")
    return value


def _reject_fallback(value: object, label: str) -> None:
    """Reject any truthy ``fallback_allowed`` anywhere in a bound block.

    Genuine producer records never carry the key; a forged block that keeps
    correct triple values but re-enables fallback is still a substitution.
    """
    if isinstance(value, dict):
        if value.get("fallback_allowed"):
            raise FinalGateError(f"{label} allows fallback")
        for sub in value.values():
            _reject_fallback(sub, label)
    elif isinstance(value, list):
        for sub in value:
            _reject_fallback(sub, label)


def _require_loopback_endpoint(value: object) -> str:
    """Mirror the shipped adapter's candidate-local endpoint rule.

    Only IP-literal loopback (127/8, ::1), ``localhost`` or wildcard bind
    inside the candidate netns is accepted. Strings that merely start with
    ``127.`` but are not IP literals (e.g. ``127.attacker.invalid``) fail
    closed without any DNS lookup.
    """
    if not isinstance(value, str) or not value.strip():
        raise FinalGateError("daemon endpoint is missing")
    text = value.strip()
    host = text.split("://", 1)[-1].split("/", 1)[0].split("@")[-1]
    host_only = host.rsplit(":", 1)[0] if ":" in host and not host.startswith("[") else host.strip("[]")
    if host_only in ("localhost", "0.0.0.0", "::"):
        return text
    try:
        addr = ipaddress.ip_address(host_only)
    except ValueError as exc:
        raise FinalGateError("daemon endpoint is not a candidate-local literal") from exc
    if not (addr.is_loopback or str(addr) in ("0.0.0.0", "::")):
        raise FinalGateError("daemon endpoint is not candidate-local")
    return text


def _validate_effective_config(subject: dict) -> None:
    """Value-check the fixed max-delivery binding (fragment + effective)."""
    block = subject.get("muse_effective_config")
    if not isinstance(block, dict):
        raise FinalGateError("absent effective max binding")
    _reject_fallback(block, "effective max binding")
    fragment = block.get("fragment")
    if not isinstance(fragment, dict):
        raise FinalGateError("effective max fragment binding is missing")
    _req_digest(fragment.get("sha256"), "effective fragment digest")
    if fragment.get("mode") != FIXED_FRAGMENT_MODE:
        raise FinalGateError("effective fragment mode is not 0644")
    effective = block.get("effective")
    if not isinstance(effective, dict):
        raise FinalGateError("effective max configuration binding is missing")
    _req_digest(effective.get("sha256"), "effective configuration digest")
    if effective.get("mode") != FIXED_EFFECTIVE_MODE:
        raise FinalGateError("effective configuration mode is not 0600")
    size = effective.get("bytes")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise FinalGateError("effective configuration bytes are missing")
    if not str(effective.get("path") or "").endswith("models.json"):
        raise FinalGateError("effective configuration path is not models.json")
    readback = subject.get("muse_effective_readback")
    if not isinstance(readback, dict):
        raise FinalGateError("effective readback binding is missing")
    _req_digest(readback.get("sha256"), "effective readback digest")
    if readback.get("mode") != FIXED_EFFECTIVE_MODE:
        raise FinalGateError("effective readback mode is not 0600")
    if readback.get("sha256") != effective.get("sha256"):
        raise FinalGateError("effective readback digest mismatch vs staged effective")


def _validate_fixed_profile(subject: dict, *, provider: str, model: str, thinking: str) -> None:
    """Value-check the fixed Muse profile triple with no fallback.

    The expected triple is passed explicitly from the single call site so
    the fixed ``meta/muse-spark-1.3-contributor/max`` invariant is visibly
    owned by the validator-record gate (not buried in a helper default)."""
    preflight = subject.get("muse_profile_preflight")
    if not isinstance(preflight, dict):
        raise FinalGateError("muse profile preflight binding is missing")
    _reject_fallback(preflight, "muse profile preflight")
    if preflight.get("model") != f"{provider}/{model}":
        raise FinalGateError(
            f"wrong model: {preflight.get('model')!r} (expected {provider}/{model!r})")
    if preflight.get("thinking") != thinking:
        raise FinalGateError(
            f"unsupported contribution: {preflight.get('thinking')!r} (expected {thinking!r})")
    observed = subject.get("muse_observed_effective")
    if not isinstance(observed, dict):
        raise FinalGateError("observed effective profile binding is missing")
    _reject_fallback(observed, "observed effective profile")
    if observed.get("provider") != provider:
        raise FinalGateError(
            f"wrong provider: {observed.get('provider')!r} (expected {provider!r})")
    if observed.get("model") != model:
        raise FinalGateError(
            f"wrong model: {observed.get('model')!r} (expected {model!r})")
    if observed.get("thinking") != thinking:
        raise FinalGateError(
            f"unsupported contribution: {observed.get('thinking')!r} (expected {thinking!r})")
    if observed.get("effort") != thinking:
        raise FinalGateError("on-wire effort is not max")
    child = subject.get("muse_owned_child")
    if not isinstance(child, dict):
        raise FinalGateError("owned-child binding is missing")
    _reject_fallback(child, "owned-child binding")
    if child.get("thinking") != thinking:
        raise FinalGateError("owned-child effective thinking is not max")
    if not child.get("id"):
        raise FinalGateError("owned-child agent identity is missing")


def _validate_daemon_pi(subject: dict) -> None:
    """Value-check daemon/Pi bindings (loopback, exact Pi path, versions)."""
    daemon = subject.get("daemon_binding")
    if not isinstance(daemon, dict):
        raise FinalGateError("daemon binding is missing")
    _require_loopback_endpoint(daemon.get("endpoint"))
    if daemon.get("home") != FIXED_DAEMON_HOME:
        raise FinalGateError("daemon home is not the candidate home")
    for key in ("pid", "worker_pid"):
        value = daemon.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise FinalGateError(f"daemon {key.replace('_', ' ')} identity is missing")
    expected_paseo = subject.get("expected_paseo_version")
    if not isinstance(expected_paseo, str) or not expected_paseo:
        raise FinalGateError("frozen Paseo version binding is missing")
    if str(daemon.get("version")) != str(expected_paseo):
        raise FinalGateError("daemon version mismatch vs frozen candidate")
    if not isinstance(daemon.get("server_id"), str) or not daemon.get("server_id"):
        raise FinalGateError("daemon server identity is missing")
    node = daemon.get("node")
    if not isinstance(node, str) or not node.startswith("/"):
        raise FinalGateError("daemon Node executable identity is missing")
    pi = subject.get("pi_binding")
    if not isinstance(pi, dict):
        raise FinalGateError("Pi binding is missing")
    if pi.get("path") != FIXED_PI_PATH:
        raise FinalGateError("Pi resolution does not match the controlled image executable")
    expected_pi = subject.get("expected_pi_version")
    if not isinstance(expected_pi, str) or not expected_pi:
        raise FinalGateError("frozen Pi version binding is missing")
    if str(pi.get("version")) != str(expected_pi):
        raise FinalGateError("Pi version mismatch vs frozen candidate")
    _req_digest(pi.get("sha256"), "Pi executable digest")


def validate_validator_record(record: object, *, candidate_digest: str, repository: str) -> dict:
    """Strictly validate the M07-T05 producer record for one OCI candidate."""
    if not isinstance(record, dict):
        raise FinalGateError("validator record must be an object")
    if record.get("schema_version") != VALIDATOR_SCHEMA:
        raise FinalGateError("validator record uses an unsupported schema")
    if record.get("execution_class") != "real":
        raise FinalGateError("fixture/rehearsal never satisfies the final real gate")
    if record.get("status") != "PASS":
        raise FinalGateError("validator record is not positively terminal PASS")
    if record.get("terminal_class") != "terminal":
        raise FinalGateError("validator occurrence is not terminal")
    if record.get("real_validation_satisfied") is not True:
        raise FinalGateError("real validation is not satisfied")
    if record.get("digest") != candidate_digest:
        raise FinalGateError("validator report is for another digest")
    repo = str(record.get("repository") or "").strip().lower()
    if repo != repository.strip().lower():
        raise FinalGateError("validator repository mismatch")
    if record.get("immutable_ref") != f"{repository.strip().lower()}@{candidate_digest}":
        raise FinalGateError("validator immutable_ref mismatch vs candidate")
    checks = record.get("checks")
    if not isinstance(checks, dict):
        raise FinalGateError("validator checks are missing")
    for name in REQUIRED_VALIDATOR_CHECKS:
        if checks.get(name) != "PASS":
            raise FinalGateError(f"real validation requires {name} PASS")
    for name in REQUIRED_SOURCE_ISOLATION_CHECKS:
        if checks.get(name) != "PASS":
            raise FinalGateError(f"final gate requires {name} PASS")
    subject = record.get("subject")
    if not isinstance(subject, dict):
        raise FinalGateError("validator subject binding is missing")
    if subject.get("candidate_id") is None or not DIGEST.fullmatch(str(subject.get("candidate_id") or "")):
        raise FinalGateError("validator candidate_id binding is missing")
    observed = subject.get("observed_image_id")
    _req_digest(observed, "validator observed local image identity")
    if observed == candidate_digest:
        raise FinalGateError("OCI manifest and local image identities must remain distinct types")
    # Fixed Muse/max/no-fallback value bindings (not presence/labels).
    _validate_effective_config(subject)
    _validate_fixed_profile(subject, provider=FIXED_PROVIDER,
                            model=FIXED_MODEL, thinking=FIXED_THINKING)
    _validate_daemon_pi(subject)
    # Codex trust boundary: the contract forbids persisting response bodies,
    # so no Codex value block exists by design; trust is the real-execution
    # catalog/auth/health checks above plus genuine-entrypoint acquisition
    # proven by end-to-end tests (never hand-authored records).
    cleanup = record.get("cleanup")
    if not isinstance(cleanup, dict) or cleanup.get("status") != "COMPLETE":
        raise FinalGateError("disposable cleanup is not COMPLETE")
    return record


def validate_state_record(record: object, *, candidate_local: str, previous_local: str) -> dict:
    """Validate the actual-baseline A->C->A round-trip for local image IDs."""
    if not isinstance(record, dict):
        raise FinalGateError("state record must be an object")
    if record.get("schema_version") != 1:
        raise FinalGateError("state record uses an unsupported schema")
    if record.get("status") != "PASS":
        raise FinalGateError("state round-trip is not PASS")
    checks = record.get("checks")
    if not isinstance(checks, dict):
        raise FinalGateError("state checks are missing")
    for name in REQUIRED_STATE_CHECKS:
        if checks.get(name) != "PASS":
            raise FinalGateError(f"state round-trip requires {name} PASS")
    if record.get("candidate_image_id") != candidate_local:
        raise FinalGateError("state candidate does not match validated local image")
    if record.get("previous_image_id") != previous_local:
        raise FinalGateError("state previous does not match running baseline")
    prov = record.get("baseline_provenance")
    if not isinstance(prov, dict) or not prov.get("source") or not isinstance(prov.get("files"), dict):
        raise FinalGateError("state baseline provenance is missing")
    if not record.get("candidate_state_sha256"):
        raise FinalGateError("state candidate marker is missing")
    return record


def assemble(*, repository: str, candidate_digest: str,
             validator_record: dict, state_record: dict,
             source_head: str, companion_digest: str,
             policy_digest: str, launcher_digest: str,
             predecessor: dict,
             guard_binding_digest: str,
             guard_candidate: str) -> dict:
    """Assemble the trusted final-gate record or raise FinalGateError.

    ``predecessor`` is the typed running-predecessor mapping
    (``oci``/``local``/``legacy`` per the shipped legacy-identity
    authority). OCI manifest digest and platform-local image ID stay
    distinct values: divergent namespaces pass, ambiguity fails closed.
    Legacy predecessors additionally require a verified recoverable
    archive/configuration anchor (real file bytes, not labels).
    """
    candidate = _req_digest(candidate_digest, "candidate digest")
    repo = repository.strip().lower()
    if not repo:
        raise FinalGateError("repository is required")
    source_head = _req_git_sha(source_head, "source head")
    companion_digest = _req_digest(companion_digest, "companion digest")
    policy_digest = _req_digest(policy_digest, "policy digest")
    launcher_digest = _req_digest(launcher_digest, "launcher digest")
    _req_digest(guard_binding_digest, "guard binding digest")
    if guard_candidate != candidate:
        raise FinalGateError("guard candidate mismatch vs final candidate")
    try:
        typed = validate_predecessor_shape(predecessor)
    except LegacyIdentityError as exc:
        raise FinalGateError(f"unsupported predecessor mapping: {exc}") from exc
    if typed["kind"] == "oci" and typed.get("repository") != repo:
        raise FinalGateError("predecessor repository mismatch")

    validator_record = validate_validator_record(
        validator_record, candidate_digest=candidate, repository=repo)
    subject = validator_record["subject"]
    candidate_local = str(subject["observed_image_id"])

    # Source/companion/policy/launcher bindings must match the exact frozen
    # identities the validator bound. A stale bundle or configuration that
    # differs from the validated bytes fails closed here, not at the writer.
    source_binding = subject.get("source_binding") or {}
    if source_binding.get("head") != source_head:
        raise FinalGateError("stale source/bundle: source head mismatch")
    companion_subject = subject.get("companion_bundle") or {}
    if companion_subject.get("source_digest") != companion_digest:
        raise FinalGateError("wrong companion/bundle: companion digest mismatch")
    policy_subject = subject.get("policy_identity") or {}
    if policy_subject.get("sha256") != policy_digest:
        raise FinalGateError("wrong configuration: policy digest mismatch")
    launcher_subject = subject.get("launcher_identity") or {}
    if launcher_subject.get("sha256") != launcher_digest:
        raise FinalGateError("wrong configuration: launcher digest mismatch")

    # Typed predecessor binding. The state round-trip proves the local
    # namespace (previous local image ID); the mapping proves the running
    # namespace actually relied upon (OCI digest or local/legacy image ID).
    # Divergent OCI vs local values pass; conflation is rejected.
    if not isinstance(state_record, dict):
        raise FinalGateError("state record must be an object")
    previous_local = str(state_record.get("previous_image_id") or "")
    _req_digest(previous_local, "state previous local image")
    if previous_local == candidate_local:
        raise FinalGateError("state previous equals candidate; no stale self-promotion")
    kind = typed["kind"]
    if kind == "oci":
        baseline_oci = typed["digest"]
        baseline_local = previous_local
        if baseline_local == baseline_oci:
            raise FinalGateError(
                "predecessor OCI manifest and platform-local identities must be distinct values")
    elif kind == "local":
        baseline_oci = typed["image_id"]
        baseline_local = previous_local
        if baseline_local != typed["image_id"]:
            raise FinalGateError("state previous mismatch vs local predecessor identity")
    else:  # legacy
        try:
            verified = verify_anchor(typed)
        except LegacyIdentityError as exc:
            raise FinalGateError(f"legacy predecessor anchor/state is missing: {exc}") from exc
        typed = verified
        baseline_oci = typed["image_id"]
        baseline_local = previous_local
        if baseline_local != typed["image_id"]:
            raise FinalGateError("state previous mismatch vs legacy predecessor identity")
    if baseline_oci == candidate:
        raise FinalGateError("baseline equals candidate; no stale self-promotion")
    validate_state_record(state_record, candidate_local=candidate_local,
                          previous_local=previous_local)

    # The guard binding ties this gate to one armed guard. The writer
    # re-validates the live guard readback; this assembler only binds the
    # expected digest so a wrong-guard attempt fails before any registry
    # access.
    required = {name: "PASS" for name in
                (*REQUIRED_VALIDATOR_CHECKS, *REQUIRED_SOURCE_ISOLATION_CHECKS)}
    required.update({f"state.{name}": "PASS" for name in REQUIRED_STATE_CHECKS})
    gate = {
        "schema_version": SCHEMA_VERSION,
        "status": "GREEN",
        "execution_class": "real",
        "real_validation_satisfied": True,
        "repository": repo,
        "candidate_digest": candidate,
        "candidate_local_image_id": candidate_local,
        "candidate_id": subject.get("candidate_id"),
        "source_head": source_head,
        "companion_digest": companion_digest,
        "policy_digest": policy_digest,
        "launcher_digest": launcher_digest,
        "predecessor": typed,
        "baseline_oci": baseline_oci,
        "baseline_local_image_id": baseline_local,
        "guard_binding_digest": guard_binding_digest,
        "required_gates": required,
    }
    raw = json.dumps(gate, sort_keys=True, separators=(",", ":"))
    gate["binding_digest"] = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    return gate


def assemble_from_acquisition(*, repository: str, candidate_digest: str,
        candidate_file, handoff_file, build_input_file, tested_image_file,
        build_record, publication_file, source_root, companion_bundle,
        codex_secret, codex_base_url, codex_model, muse_secret,
        validator_state_root, validator_output,
        baseline_path, baseline_local_image_id, state_root, state_output,
        predecessor: dict, guard_path):
    """Acquire, verify and assemble through shipped entrypoints (provenance boundary).

    This is the genuine shipped acquisition→assembler integration: it invokes
    the shipped ``paseo_tower_validator.validate`` producer (``real`` mode),
    the shipped ``paseo_state_roundtrip.prove`` round-trip and the shipped
    guard readback itself, then delegates to :func:`assemble`. Caller data
    never substitutes for acquisition: companion/policy/launcher bindings are
    recomputed from ``source_root`` bytes inside (a caller-supplied companion
    declaration must equal the recomputation), the source head is read from
    the genuine chain bytes, and the guard binding is read from the live
    guard file. Only the typed ``predecessor`` mapping, the ledger-owned
    ``baseline_local_image_id`` observation and file/secret locators arrive
    from the caller layers that own them. External acquisition/transport
    effects (Docker/registry/probe) are the only fakeable boundaries and
    live behind the producer modules' own transport seams, which tests
    exercise via the same mocks the producer harness uses.
    """
    candidate = _req_digest(candidate_digest, "candidate digest")
    repo = repository.strip().lower()
    if not repo:
        raise FinalGateError("repository is required")
    baseline_local_image_id = _req_digest(baseline_local_image_id,
                                          "baseline local image identity")
    try:
        computed_companion = build_mod.companion_bundle_identity(Path(source_root))
    except Exception as exc:
        raise FinalGateError(f"companion identity unavailable: {exc}") from exc
    if companion_bundle is not None:
        if not isinstance(companion_bundle, dict):
            raise FinalGateError("companion bundle declaration must be an object")
        for key in ("source_digest", "files"):
            if companion_bundle.get(key) != computed_companion.get(key):
                raise FinalGateError("companion declaration mismatch vs source recomputation")
    policy_file = Path(source_root) / "config" / "pi-agent" / "policies" / "llm-test-policy.json"
    launcher_file = Path(source_root) / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
    try:
        policy_digest = "sha256:" + hashlib.sha256(policy_file.read_bytes()).hexdigest()
        launcher_digest = "sha256:" + hashlib.sha256(launcher_file.read_bytes()).hexdigest()
    except OSError as exc:
        raise FinalGateError(f"policy/launcher bytes unavailable: {exc}") from exc
    try:
        build_input_doc = json.loads(Path(build_input_file).read_bytes())
    except (OSError, ValueError) as exc:
        raise FinalGateError(f"build-input chain bytes unavailable: {exc}") from exc
    source_head = build_input_doc.get("source_head")
    try:
        record = tower_validator.validate(
            repository=repo, digest=candidate, output=Path(validator_output),
            state_root=Path(validator_state_root),
            codex_secret=codex_secret, codex_base_url=codex_base_url,
            codex_model=codex_model, execution_class="real",
            source_root=Path(source_root), companion_bundle=computed_companion,
            candidate_file=candidate_file, handoff_file=handoff_file,
            build_input_file=build_input_file, tested_image_file=tested_image_file,
            build_record=build_record, publication_file=publication_file,
            muse_secret=muse_secret)
    except FinalGateError:
        raise
    except Exception as exc:
        raise FinalGateError(f"producer acquisition failed: {exc}") from exc
    observed_local = (record.get("subject") or {}).get("observed_image_id")
    try:
        state_record = state_prove.prove(
            baseline=Path(baseline_path), candidate=str(observed_local),
            previous=baseline_local_image_id,
            state_root=Path(state_root), output=Path(state_output))
    except Exception as exc:
        raise FinalGateError(f"state acquisition failed: {exc}") from exc
    if not isinstance(state_record, dict) or state_record.get("status") != "PASS":
        raise FinalGateError("state round-trip is not PASS")
    try:
        guard_record = guard_mod.load(Path(guard_path))
    except Exception as exc:
        raise FinalGateError(f"guard readback failed: {exc}") from exc
    gate = assemble(
        repository=repo, candidate_digest=candidate,
        validator_record=record, state_record=state_record,
        source_head=_req_git_sha(source_head, "source head"),
        companion_digest=_req_digest(computed_companion["source_digest"], "companion digest"),
        policy_digest=policy_digest, launcher_digest=launcher_digest,
        predecessor=predecessor,
        guard_binding_digest=_req_digest(guard_record.get("binding_digest"), "guard binding digest"),
        guard_candidate=str(guard_record.get("candidate_digest")))
    return gate, {"validator_record": record, "state_record": state_record,
                   "guard_record": guard_record}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--candidate-digest", required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--companion-digest", required=True)
    parser.add_argument("--policy-digest", required=True)
    parser.add_argument("--launcher-digest", required=True)
    parser.add_argument("--predecessor", type=Path, required=True,
                        help="JSON file with the typed predecessor mapping")
    parser.add_argument("--guard-binding", required=True)
    parser.add_argument("--guard-candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        validator_record = json.loads(args.validator.read_text(encoding="utf-8"))
        state_record = json.loads(args.state.read_text(encoding="utf-8"))
        predecessor = json.loads(args.predecessor.read_text(encoding="utf-8"))
        gate = assemble(
            repository=args.repository, candidate_digest=args.candidate_digest,
            validator_record=validator_record, state_record=state_record,
            source_head=args.source_head, companion_digest=args.companion_digest,
            policy_digest=args.policy_digest, launcher_digest=args.launcher_digest,
            predecessor=predecessor,
            guard_binding_digest=args.guard_binding,
            guard_candidate=args.guard_candidate)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(gate, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
        print(json.dumps(gate, sort_keys=True))
        return 0
    except (FinalGateError, OSError, ValueError) as exc:
        print(f"final gate failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
