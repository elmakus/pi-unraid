#!/usr/bin/env python3
"""Trusted Tower final-gate assembler for M07-T06.

Consumes the exact independently GREEN M07-T05 producer record (real
validator output), the actual-baseline state round-trip record, frozen
source/companion/policy/launcher bindings and the armed guard binding.
Emits one narrow final-gate record that the single Tower writer consumes
before any registry create/update. Caller generic GREEN/PASS strings,
fixture/rehearsal records or arbitrary JSON are never evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA_VERSION = 1
VALIDATOR_SCHEMA = 2
FIXED_PROVIDER = "meta"
FIXED_MODEL = "muse-spark-1.3-contributor"
FIXED_THINKING = "max"

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
    # Effective-max proof is not waivable: the profile, effective-config and
    # effective-readback checks above already enforce it, but an explicit
    # subject binding is also required so a bare PASS map cannot pass.
    subject = record.get("subject")
    if not isinstance(subject, dict):
        raise FinalGateError("validator subject binding is missing")
    if subject.get("candidate_id") is None or not DIGEST.fullmatch(str(subject.get("candidate_id") or "")):
        raise FinalGateError("validator candidate_id binding is missing")
    observed = subject.get("observed_image_id")
    _req_digest(observed, "validator observed local image identity")
    if observed == candidate_digest:
        raise FinalGateError("OCI manifest and local image identities must remain distinct types")
    # Muse fixed-policy binding: effective profile must be the fixed
    # meta/muse-spark-1.3-contributor/max triple with no fallback. The
    # producer proves it via muse_effective_profile PASS plus the staged
    # effective-config/readback PASS values required above; a record that
    # omits the effective subject binding cannot satisfy the gate.
    eff = subject.get("muse_effective_config")
    if not isinstance(eff, dict):
        raise FinalGateError("absent effective max binding")
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
             baseline_digest: str, guard_binding_digest: str,
             guard_candidate: str) -> dict:
    """Assemble the trusted final-gate record or raise FinalGateError."""
    candidate = _req_digest(candidate_digest, "candidate digest")
    repo = repository.strip().lower()
    if not repo:
        raise FinalGateError("repository is required")
    source_head = _req_git_sha(source_head, "source head")
    companion_digest = _req_digest(companion_digest, "companion digest")
    policy_digest = _req_digest(policy_digest, "policy digest")
    launcher_digest = _req_digest(launcher_digest, "launcher digest")
    baseline = _req_digest(baseline_digest, "baseline digest")
    _req_digest(guard_binding_digest, "guard binding digest")
    if guard_candidate != candidate:
        raise FinalGateError("guard candidate mismatch vs final candidate")
    if baseline == candidate:
        raise FinalGateError("baseline equals candidate; no stale self-promotion")

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

    # State round-trip must prove the actual baseline -> candidate ->
    # baseline transition. The previous local identity is carried by the
    # caller (ledger/guard running predecessor mapping); the candidate local
    # identity comes from the validator's distinct local mapping. The
    # assembled baseline digest must equal the proven state previous by
    # value so a stale baseline cannot be bound to a fresh round-trip.
    # (Synthetic scope represents the running OCI/local predecessor by one
    # value; the candidate OCI/local pair remains distinctly typed.)
    if not isinstance(state_record, dict):
        raise FinalGateError("state record must be an object")
    previous_local = str(state_record.get("previous_image_id") or "")
    _req_digest(previous_local, "state previous local image")
    if baseline != previous_local:
        raise FinalGateError("stale baseline: final-gate baseline mismatch vs running predecessor")
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
        "baseline_digest": baseline,
        "baseline_local_image_id": previous_local,
        "guard_binding_digest": guard_binding_digest,
        "required_gates": required,
    }
    raw = json.dumps(gate, sort_keys=True, separators=(",", ":"))
    gate["binding_digest"] = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    return gate


def main() -> int:
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--candidate-digest", required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--companion-digest", required=True)
    parser.add_argument("--policy-digest", required=True)
    parser.add_argument("--launcher-digest", required=True)
    parser.add_argument("--baseline-digest", required=True)
    parser.add_argument("--guard-binding", required=True)
    parser.add_argument("--guard-candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        validator_record = json.loads(args.validator.read_text(encoding="utf-8"))
        state_record = json.loads(args.state.read_text(encoding="utf-8"))
        gate = assemble(
            repository=args.repository, candidate_digest=args.candidate_digest,
            validator_record=validator_record, state_record=state_record,
            source_head=args.source_head, companion_digest=args.companion_digest,
            policy_digest=args.policy_digest, launcher_digest=args.launcher_digest,
            baseline_digest=args.baseline_digest,
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
