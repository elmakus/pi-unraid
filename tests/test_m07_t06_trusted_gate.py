"""M07-T06 trusted final-gate / first-channel / typed-legacy / Update+Verify tests.

Classification (synthetic only, no real effects):
- Inference-capable entrypoints (Muse/Codex/provider, real LLM launcher):
  NEVER invoked. Validator Muse/Codex dispatch is represented only by
  producer-shaped synthetic records consumed through the actual
  final-gate assembler; no prompt, /responses, /chat/completions or
  provider auth occurs.
- Mutation-capable entrypoints:
  - Docker CLI (inspect/buildx/imagetools/run/exec): ALWAYS mocked via
    ``mock.patch.object`` on ``inspect_digest``/``run_checked`` or fake
    runner callables. No daemon, image, container or network is touched.
  - Registry HTTP/transport: faked via ``channel_status``/``channel_error``
    integers, never a live GHCR read. 404 is the only verified absence;
    401/403/network/timeout are never absence.
  - Unraid/DockerMan trigger, probes, restore/recovery: fake callables
    recording invocation; no container, engine or production action.
  - Guard/ledger/intent files: disposable ``tempfile.TemporaryDirectory``
    siblings only; no production HOME/runtime/config/ledger/guard/template
    mutation. Production lock root is faked via temp dirs where needed.
  - Credentials: synthetic digest-shaped strings only; no real secret,
    ordinary HOME/auth read, or provider credential admission.
- Product entrypoints exercised genuinely (not helper-only):
  ``paseo_final_gate.assemble``, ``paseo_accepted_promotion.promote`` /
  ``promote_first_channel`` / ``classify_channel_status`` /
  ``verify_channel_absence``, ``paseo_legacy_identity.validate`` /
  ``verify_anchor`` / ``verify_imported_image``,
  ``paseo_known_good.commit_on_terminal`` /
  ``migrate_with_predecessor``, ``paseo_trigger_intent.record`` /
  ``readback``, ``paseo_dockerman_binding.update_and_verify`` /
  ``wait_for_stock_update``, ``paseo_immediate_acceptance.run_transaction``,
  ``paseo_transaction_guard.arm``/``load``, and
  ``paseo_update_verify_action.running_repo_digest``.
- Generic hand-authored PASS strings never substitute for end-to-end
  proof: positive gates are assembled through the actual assembler from
  producer-shaped bound records; negatives assert the exact failure AND
  absence of disallowed writes/triggers while resources still exist.
"""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    import sys
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FG = _load("m07_t06_final_gate", "scripts/paseo_final_gate.py")
PROM = _load("m07_t06_promotion", "scripts/paseo_accepted_promotion.py")
LEG = _load("m07_t06_legacy", "scripts/paseo_legacy_identity.py")
KG = _load("m07_t06_known_good", "scripts/paseo_known_good.py")
TI = _load("m07_t06_intent", "scripts/paseo_trigger_intent.py")
GUARD = _load("m07_t06_guard", "scripts/paseo_transaction_guard.py")
ACC = _load("m07_t06_acceptance", "scripts/paseo_immediate_acceptance.py")
DOCK = _load("m07_t06_dockerman", "scripts/paseo_dockerman_binding.py")
UVA = _load("m07_t06_update_verify", "scripts/paseo_update_verify_action.py")

REPO = "ghcr.io/elmakus/pi-unraid"
RUN_OCI = "sha256:" + "a" * 64
CAND_OCI = "sha256:" + "b" * 64
CAND_LOCAL = "sha256:" + "c" * 64
CFG = "sha256:" + "d" * 64
COMP = "sha256:" + "1" * 64
POL = "sha256:" + "2" * 64
LAUNCH = "sha256:" + "3" * 64
CAND_ID = "sha256:" + "9" * 64
OTHER_OCI = "sha256:" + "e" * 64
THIRD = "sha256:" + "f" * 64
SOURCE_HEAD = "ab" * 20


def make_validator(*, candidate=CAND_OCI, local=CAND_LOCAL,
                   execution_class="real", status="PASS",
                   real_satisfied=True, missing=(), extra_checks=None,
                   candidate_id=CAND_ID, source_head=SOURCE_HEAD,
                   companion=COMP, policy=POL, launcher=LAUNCH,
                   cleanup="COMPLETE"):
    checks = {}
    for name in (*FG.REQUIRED_VALIDATOR_CHECKS, *FG.REQUIRED_SOURCE_ISOLATION_CHECKS):
        checks[name] = "PASS"
    for name in missing:
        checks[name] = "SKIP"
    if extra_checks:
        checks.update(extra_checks)
    return {
        "schema_version": 2,
        "execution_class": execution_class,
        "status": status,
        "terminal_class": "terminal" if status != "UNKNOWN" else "unknown",
        "digest": candidate,
        "repository": REPO,
        "immutable_ref": f"{REPO}@{candidate}",
        "checks": checks,
        "subject": {
            "repository": REPO,
            "expected_digest": candidate,
            "observed_image_id": local,
            "candidate_id": candidate_id,
            "companion_bundle": {"source_digest": companion},
            "policy_identity": {"sha256": policy},
            "launcher_identity": {"sha256": launcher},
            "source_binding": {"head": source_head},
            "muse_effective_config": {"effective": {"sha256": "sha256:" + "4" * 64}},
            "daemon_binding": {"endpoint": "fake"},
            "pi_binding": {"path": "fake"},
        },
        "real_validation_satisfied": real_satisfied,
        "real_reason": "synthetic",
        "cleanup": {"status": cleanup, "issues": []},
    }


def make_state(*, candidate_local=CAND_LOCAL, previous_local=RUN_OCI,
               status="PASS", missing=()):
    checks = {name: "PASS" for name in FG.REQUIRED_STATE_CHECKS}
    for name in missing:
        checks[name] = "FAIL"
    return {
        "schema_version": 1,
        "status": status,
        "checks": checks,
        "candidate_image_id": candidate_local,
        "previous_image_id": previous_local,
        "baseline_provenance": {"source": "/tmp/fake-baseline",
                                "files": {"config.json": "abc"}},
        "candidate_state_sha256": "sha256:" + "5" * 64,
    }


def make_guard(tmpdir, *, candidate=CAND_OCI, previous=RUN_OCI, config=CFG):
    anchor = Path(tmpdir) / "rollback.json"
    anchor.write_text("{}\n", encoding="utf-8")
    guard_path = Path(tmpdir) / "guard.json"
    guard = GUARD.arm(guard_path, candidate, previous, config, anchor)
    return guard_path, guard, anchor


def make_final_gate(validator, state, guard, *, baseline=RUN_OCI):
    return FG.assemble(
        repository=REPO, candidate_digest=CAND_OCI,
        validator_record=validator, state_record=state,
        source_head=SOURCE_HEAD, companion_digest=COMP,
        policy_digest=POL, launcher_digest=LAUNCH,
        baseline_digest=baseline,
        guard_binding_digest=guard["binding_digest"],
        guard_candidate=CAND_OCI)


def core_probes(ok=True):
    return [ACC.CoreProbe(name, (lambda: True) if ok else (lambda: False))
            for name in sorted(ACC.REQUIRED_CORE_PROBES)]


class FinalGateAssemblerTests(unittest.TestCase):
    def test_positive_assembles_through_actual_entrypoint(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            gate = make_final_gate(make_validator(), make_state(), guard)
            self.assertEqual(gate["status"], "GREEN")
            self.assertEqual(gate["candidate_digest"], CAND_OCI)
            self.assertEqual(gate["candidate_local_image_id"], CAND_LOCAL)
            self.assertEqual(gate["baseline_digest"], RUN_OCI)
            self.assertEqual(gate["guard_binding_digest"], guard["binding_digest"])
            self.assertIn("binding_digest", gate)

    def test_fixture_never_satisfies_real_gate(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            for execution_class in ("fixture", "rehearsal"):
                with self.assertRaises(FG.FinalGateError):
                    make_final_gate(make_validator(execution_class=execution_class),
                                    make_state(), guard)

    def test_missing_forged_or_failed_gate_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            # Missing check.
            with self.assertRaisesRegex(FG.FinalGateError, "muse_dispatch PASS"):
                make_final_gate(make_validator(missing=("muse_dispatch",)),
                                make_state(), guard)
            # Missing effective-max binding.
            validator = make_validator()
            del validator["subject"]["muse_effective_config"]
            with self.assertRaisesRegex(FG.FinalGateError, "effective max"):
                make_final_gate(validator, make_state(), guard)
            # Wrong digest report.
            with self.assertRaisesRegex(FG.FinalGateError, "another digest"):
                make_final_gate(make_validator(candidate=OTHER_OCI),
                                make_state(), guard)
            # Failed validator status.
            with self.assertRaises(FG.FinalGateError):
                make_final_gate(make_validator(status="FAIL", real_satisfied=False),
                                make_state(), guard)
            # Unknown terminal.
            with self.assertRaises(FG.FinalGateError):
                make_final_gate(make_validator(status="UNKNOWN", real_satisfied=False),
                                make_state(), guard)
            # Generic PASS map without required set still fails (absent key).
            validator = make_validator()
            del validator["checks"]["codex_health"]
            with self.assertRaisesRegex(FG.FinalGateError, "codex_health PASS"):
                make_final_gate(validator, make_state(), guard)

    def test_stale_source_bundle_config_baseline_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            # Stale source head.
            with self.assertRaisesRegex(FG.FinalGateError, "source head mismatch"):
                FG.assemble(repository=REPO, candidate_digest=CAND_OCI,
                            validator_record=make_validator(source_head="00" * 20),
                            state_record=make_state(),
                            source_head=SOURCE_HEAD, companion_digest=COMP,
                            policy_digest=POL, launcher_digest=LAUNCH,
                            baseline_digest=RUN_OCI,
                            guard_binding_digest=guard["binding_digest"],
                            guard_candidate=CAND_OCI)
            # Wrong companion.
            with self.assertRaisesRegex(FG.FinalGateError, "companion digest mismatch"):
                FG.assemble(repository=REPO, candidate_digest=CAND_OCI,
                            validator_record=make_validator(companion="sha256:" + "6" * 64),
                            state_record=make_state(),
                            source_head=SOURCE_HEAD, companion_digest=COMP,
                            policy_digest=POL, launcher_digest=LAUNCH,
                            baseline_digest=RUN_OCI,
                            guard_binding_digest=guard["binding_digest"],
                            guard_candidate=CAND_OCI)
            # Wrong policy.
            with self.assertRaisesRegex(FG.FinalGateError, "policy digest mismatch"):
                FG.assemble(repository=REPO, candidate_digest=CAND_OCI,
                            validator_record=make_validator(policy="sha256:" + "7" * 64),
                            state_record=make_state(),
                            source_head=SOURCE_HEAD, companion_digest=COMP,
                            policy_digest=POL, launcher_digest=LAUNCH,
                            baseline_digest=RUN_OCI,
                            guard_binding_digest=guard["binding_digest"],
                            guard_candidate=CAND_OCI)
            # Stale baseline.
            with self.assertRaisesRegex(FG.FinalGateError, "stale baseline"):
                make_final_gate(make_validator(), make_state(), guard,
                                baseline=OTHER_OCI)
            # Wrong guard candidate.
            with self.assertRaisesRegex(FG.FinalGateError, "guard candidate mismatch"):
                FG.assemble(repository=REPO, candidate_digest=CAND_OCI,
                            validator_record=make_validator(),
                            state_record=make_state(),
                            source_head=SOURCE_HEAD, companion_digest=COMP,
                            policy_digest=POL, launcher_digest=LAUNCH,
                            baseline_digest=RUN_OCI,
                            guard_binding_digest=guard["binding_digest"],
                            guard_candidate=OTHER_OCI)

    def test_state_gates_required(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            with self.assertRaisesRegex(FG.FinalGateError, "state round-trip requires"):
                make_final_gate(make_validator(),
                                make_state(missing=("direct_skip_path",)), guard)
            with self.assertRaisesRegex(FG.FinalGateError, "stale baseline"):
                make_final_gate(make_validator(),
                                make_state(previous_local=OTHER_OCI), guard)
            with self.assertRaisesRegex(FG.FinalGateError, "state candidate"):
                make_final_gate(make_validator(),
                                make_state(candidate_local=OTHER_OCI), guard)

    def test_oci_local_distinctness_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            with self.assertRaisesRegex(FG.FinalGateError, "distinct types"):
                make_final_gate(make_validator(local=CAND_OCI),
                                make_state(candidate_local=CAND_OCI), guard)


class ChannelAbsenceTests(unittest.TestCase):
    def test_verified_404_is_absence(self):
        PROM.verify_channel_absence(status=404)
        self.assertEqual(PROM.classify_channel_status(404), "absent")

    def test_auth_network_timeout_never_absence(self):
        for status in (401, 403):
            with self.assertRaisesRegex(PROM.PromotionError, "auth failure"):
                PROM.verify_channel_absence(status=status)
        for error in ("timeout", "network", "connection", "dns", "tls", "boom"):
            with self.assertRaisesRegex(PROM.PromotionError, "uncertain"):
                PROM.verify_channel_absence(status=None, error=error)
        with self.assertRaisesRegex(PROM.PromotionError, "uncertain|present"):
            PROM.verify_channel_absence(status=200)
        with self.assertRaisesRegex(PROM.PromotionError, "uncertain"):
            PROM.verify_channel_absence(status=500)
        with self.assertRaisesRegex(PROM.PromotionError, "uncertain"):
            PROM.verify_channel_absence(status=None)


class FirstChannelPromotionTests(unittest.TestCase):
    def _gate_and_guard(self, td):
        gp, guard, _ = make_guard(td)
        gate = make_final_gate(make_validator(), make_state(), guard)
        return gp, guard, gate

    def test_absent_channel_positive_with_readback(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, gate = self._gate_and_guard(td)
            alias = "m07-t06-fixture-absent"
            reads = [PROM.PromotionError("404 Not Found"), CAND_OCI]
            with mock.patch.object(PROM, "inspect_digest", side_effect=reads) as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                out = PROM.promote_first_channel(
                    repository=REPO, alias=alias, candidate_digest=CAND_OCI,
                    running_predecessor=RUN_OCI,
                    output_path=Path(td) / "out.json",
                    final_gate=gate, guard=guard,
                    lock_path=Path(td) / "lock",
                    channel_status=404)
            self.assertEqual(out["readback_digest"], CAND_OCI)
            self.assertTrue(out["first_create"])
            self.assertEqual(out["running_predecessor"], RUN_OCI)
            self.assertEqual(inspect.call_count, 2)
            create_argv = run.call_args_list[0].args[0]
            self.assertIn(f"{REPO}@{CAND_OCI}", create_argv)
            self.assertIn(f"{REPO}:{alias}", create_argv)

    def test_first_create_rejects_auth_network_as_absence(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, gate = self._gate_and_guard(td)
            for status, error in ((401, None), (403, None), (None, "timeout"),
                                  (None, "network"), (200, None)):
                with mock.patch.object(PROM, "inspect_digest") as inspect, \
                     mock.patch.object(PROM, "run_checked") as run:
                    with self.assertRaises(PROM.PromotionError):
                        PROM.promote_first_channel(
                            repository=REPO, alias="m07-t06-fixture-absent",
                            candidate_digest=CAND_OCI,
                            running_predecessor=RUN_OCI,
                            output_path=Path(td) / "o.json",
                            final_gate=gate, guard=guard,
                            lock_path=Path(td) / "lock",
                            channel_status=status, channel_error=error)
                    inspect.assert_not_called()
                    run.assert_not_called()

    def test_first_create_race_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, gate = self._gate_and_guard(td)
            # Channel appears between absence check and write.
            with mock.patch.object(PROM, "inspect_digest", return_value=OTHER_OCI), \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "appeared before write"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=guard,
                        lock_path=Path(td) / "lock", channel_status=404)
                run.assert_not_called()
            # Fresh status_fn reports present inside the lock.
            with mock.patch.object(PROM, "inspect_digest",
                                   side_effect=PROM.PromotionError("404 nope")), \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaises(PROM.PromotionError):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=guard,
                        lock_path=Path(td) / "lock", channel_status=404,
                        channel_status_fn=lambda: 200)
                run.assert_not_called()

    def test_first_create_requires_gates_and_guard_before_write(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, gate = self._gate_and_guard(td)
            # Missing gate.
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "trusted final-gate"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=None, guard=guard,
                        lock_path=Path(td) / "lock", channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()
            # Fixture gate.
            fixture_gate = dict(gate)
            fixture_gate["execution_class"] = "fixture"
            fixture_gate["real_validation_satisfied"] = False
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "fixture/rehearsal"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=fixture_gate, guard=guard,
                        lock_path=Path(td) / "lock", channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()
            # Wrong guard (candidate mismatch) fails before registry.
            bad_guard = dict(guard)
            bad_guard["candidate_digest"] = OTHER_OCI
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaises(PROM.PromotionError):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=bad_guard,
                        lock_path=Path(td) / "lock", channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()
            # Wrong guard binding fails before registry.
            wrong_bound = dict(gate)
            wrong_bound["guard_binding_digest"] = "sha256:" + "8" * 64
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "binding mismatch"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=wrong_bound, guard=guard,
                        lock_path=Path(td) / "lock", channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()

    def test_channel_predecessor_distinct_from_running(self):
        # Existing-channel update binds the registry observation (expected)
        # while the guard binds the actually running predecessor. A typed
        # mapping pins the running value even when it differs in kind.
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)  # guard previous == RUN_OCI
            gate = make_final_gate(make_validator(), make_state(), guard)
            mapping = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
            with mock.patch.object(PROM, "inspect_digest",
                                   side_effect=[RUN_OCI, RUN_OCI, CAND_OCI]), \
                 mock.patch.object(PROM, "run_checked"):
                out = PROM.promote(
                    repository=REPO, alias="m07-t06-fixture-separate",
                    candidate_digest=CAND_OCI,
                    expected_current_digest=RUN_OCI,
                    output_path=Path(td) / "o.json",
                    running_predecessor=RUN_OCI,
                    predecessor_mapping=mapping)
            self.assertEqual(out["running_predecessor"], RUN_OCI)
            # Mapping mismatch vs running fails closed.
            bad = {"kind": "oci", "digest": OTHER_OCI, "repository": REPO}
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "mapping mismatch"):
                    PROM.promote(
                        repository=REPO, alias="m07-t06-fixture-separate",
                        candidate_digest=CAND_OCI,
                        expected_current_digest=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        running_predecessor=RUN_OCI,
                        predecessor_mapping=bad)
                inspect.assert_not_called()
                run.assert_not_called()

    def test_production_accepted_enforces_tower_lock_and_readback(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, gate = self._gate_and_guard(td)
            fake_root = Path(td) / "tower-state"
            fake_root.mkdir()
            lock = fake_root / "accepted.lock"
            with mock.patch.object(PROM.socket, "gethostname", return_value="Tower"), \
                 mock.patch.object(PROM, "PRODUCTION_LOCK_ROOT", fake_root), \
                 mock.patch.object(PROM, "inspect_digest",
                                   side_effect=[PROM.PromotionError("404 missing"), CAND_OCI]), \
                 mock.patch.object(PROM, "run_checked"):
                out = PROM.promote_first_channel(
                    repository=REPO, alias="accepted",
                    candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                    output_path=Path(td) / "o.json",
                    final_gate=gate, guard=guard, lock_path=lock,
                    channel_status=404)
            self.assertTrue(out["production"])
            self.assertEqual(out["readback_digest"], CAND_OCI)
            self.assertTrue(str(lock).startswith(str(fake_root)))
            # Out-of-domain hostname still fails before mutation.
            with mock.patch.object(PROM.socket, "gethostname", return_value="not-tower"), \
                 mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "Tower writer domain"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="accepted",
                        candidate_digest=CAND_OCI, running_predecessor=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=guard,
                        lock_path=Path(td) / "foreign.lock",
                        channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()


class LegacyIdentityTests(unittest.TestCase):
    def test_typed_kinds_validate(self):
        self.assertEqual(
            LEG.validate({"kind": "oci", "digest": CAND_OCI, "repository": REPO})["kind"], "oci")
        self.assertEqual(
            LEG.validate({"kind": "local", "image_id": CAND_LOCAL})["kind"], "local")
        with tempfile.TemporaryDirectory() as td:
            anchor = Path(td) / "archive.tar"
            anchor.write_bytes(b"legacy-bytes")
            import hashlib
            digest = "sha256:" + hashlib.sha256(b"legacy-bytes").hexdigest()
            record = {"kind": "legacy", "image_id": CAND_LOCAL,
                      "archive_path": str(anchor), "archive_sha256": digest,
                      "config_digest": CFG, "state_identity": "state-1"}
            out = LEG.verify_anchor(record)
            self.assertEqual(out["archive_sha256"], digest)
            # Archive/config mismatch fails.
            bad = dict(record)
            bad["archive_sha256"] = CAND_OCI
            with self.assertRaises(LEG.LegacyIdentityError):
                LEG.verify_anchor(bad)
            # Missing anchor fails.
            anchor.unlink()
            with self.assertRaises(LEG.LegacyIdentityError):
                LEG.verify_anchor(record)

    def test_unsupported_multiple_unmapped_rejected(self):
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.validate({"kind": "weird", "digest": CAND_OCI})
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.validate({"kind": "oci", "digest": CAND_OCI,
                          "repository": REPO, "image_id": CAND_LOCAL})
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.validate({"kind": "oci", "digest": "not-a-digest",
                          "repository": REPO})
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.validate({"kind": "legacy", "image_id": CAND_LOCAL,
                          "archive_path": "/tmp/x", "archive_sha256": CAND_OCI,
                          "config_digest": CFG, "state_identity": ""})

    def test_imported_image_never_relabels_id_as_digest(self):
        record = {"kind": "legacy", "image_id": CAND_LOCAL,
                  "archive_path": "/tmp/fake.tar",
                  "archive_sha256": CAND_OCI, "config_digest": CFG,
                  "state_identity": "s"}
        # Matching inspect passes when RepoDigests is empty (never published).
        out = LEG.verify_imported_image(record, inspect_image_id=CAND_LOCAL,
                                        repo_digests=[])
        self.assertEqual(out["image_id"], CAND_LOCAL)
        # Mismatched image fails.
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.verify_imported_image(record, inspect_image_id=OTHER_OCI,
                                      repo_digests=[])
        # Relabeling the image-ID as a manifest digest fails.
        with self.assertRaisesRegex(LEG.LegacyIdentityError, "relabeled"):
            LEG.verify_imported_image(
                record, inspect_image_id=CAND_LOCAL,
                repo_digests=[f"{REPO}@{CAND_LOCAL}"])

    def test_legacy_first_create_binds_running_without_publishing(self):
        with tempfile.TemporaryDirectory() as td:
            anchor = Path(td) / "legacy.tar"
            anchor.write_bytes(b"legacy-image-bytes")
            import hashlib
            archive_digest = "sha256:" + hashlib.sha256(b"legacy-image-bytes").hexdigest()
            legacy_running = CAND_LOCAL  # platform image-ID value, typed legacy
            mapping = {"kind": "legacy", "image_id": legacy_running,
                       "archive_path": str(anchor),
                       "archive_sha256": archive_digest,
                       "config_digest": CFG, "state_identity": "legacy-state-1"}
            verified = LEG.verify_anchor(mapping)
            LEG.verify_imported_image(verified, inspect_image_id=legacy_running,
                                      repo_digests=[])
            # Guard/ledger/final-gate bind the legacy running value by value;
            # the kind keeps the OCI manifest namespace distinct.
            gp, guard, _ = make_guard(td, previous=legacy_running)
            state = make_state(candidate_local=CAND_OCI.replace("b", "c") if False else CAND_OCI,
                               previous_local=legacy_running)
            # Build a validator whose local is the new candidate local and
            # whose state previous is the legacy image-ID.
            validator = make_validator(local="sha256:" + "d" * 63 + "e")
            cand_local = validator["subject"]["observed_image_id"]
            state = make_state(candidate_local=cand_local,
                               previous_local=legacy_running)
            gate = FG.assemble(
                repository=REPO, candidate_digest=CAND_OCI,
                validator_record=validator, state_record=state,
                source_head=SOURCE_HEAD, companion_digest=COMP,
                policy_digest=POL, launcher_digest=LAUNCH,
                baseline_digest=legacy_running,
                guard_binding_digest=guard["binding_digest"],
                guard_candidate=CAND_OCI)
            self.assertEqual(gate["baseline_digest"], legacy_running)
            # First-create with the legacy mapping succeeds without ever
            # publishing the legacy image (only the candidate is created).
            with mock.patch.object(PROM, "inspect_digest",
                                   side_effect=[PROM.PromotionError("404 absent"), CAND_OCI]) as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                out = PROM.promote_first_channel(
                    repository=REPO, alias="m07-t06-fixture-legacy",
                    candidate_digest=CAND_OCI,
                    running_predecessor=legacy_running,
                    output_path=Path(td) / "o.json",
                    final_gate=gate, guard=guard,
                    lock_path=Path(td) / "lock",
                    predecessor_mapping=mapping,
                    channel_status=404)
            self.assertEqual(out["running_predecessor"], legacy_running)
            created = run.call_args_list[0].args[0]
            self.assertIn(f"{REPO}@{CAND_OCI}", created)
            self.assertNotIn(legacy_running, " ".join(created))


class LedgerMigrationTests(unittest.TestCase):
    LEDGER = {"current": RUN_OCI, "previous_1": OTHER_OCI, "previous_2": THIRD}

    def test_coherent_rotation_and_retention(self):
        ledger = dict(self.LEDGER)
        rotated = KG.rotate(ledger, CAND_OCI)
        self.assertEqual(rotated, {"current": CAND_OCI, "previous_1": RUN_OCI,
                                   "previous_2": OTHER_OCI})
        # Stale identities cannot become current.
        with self.assertRaises(ValueError):
            KG.rotate(ledger, OTHER_OCI)
        with self.assertRaises(ValueError):
            KG.rotate(ledger, THIRD)

    def test_never_rotates_on_rejected_or_uncertain(self):
        ledger = dict(self.LEDGER)
        for status in ("RED", "RECOVERED", "UNKNOWN", "BLOCKED", "FAIL"):
            with self.assertRaisesRegex(ValueError, "never rotates"):
                KG.commit_on_terminal(ledger, CAND_OCI, transaction_status=status)
        # Only GREEN/committed rotates.
        self.assertEqual(
            KG.commit_on_terminal(ledger, CAND_OCI, transaction_status="GREEN")["current"],
            CAND_OCI)
        self.assertEqual(
            KG.commit_on_terminal(ledger, CAND_OCI, transaction_status="committed")["current"],
            CAND_OCI)

    def test_migration_binds_typed_predecessor(self):
        ledger = dict(self.LEDGER)
        oci_map = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
        out = KG.migrate_with_predecessor(ledger, CAND_OCI,
                                          predecessor_mapping=oci_map,
                                          transaction_status="GREEN")
        self.assertEqual(out["current"], CAND_OCI)
        # Wrong predecessor fails.
        bad = {"kind": "oci", "digest": OTHER_OCI, "repository": REPO}
        with self.assertRaises(ValueError):
            KG.migrate_with_predecessor(ledger, CAND_OCI,
                                        predecessor_mapping=bad,
                                        transaction_status="GREEN")
        # Legacy migration binds the image-ID value with anchor/state.
        legacy_map = {"kind": "legacy", "image_id": RUN_OCI,
                      "archive_path": "/tmp/a.tar",
                      "archive_sha256": CAND_OCI, "config_digest": CFG,
                      "state_identity": "s"}
        out = KG.migrate_with_predecessor(ledger, CAND_OCI,
                                          predecessor_mapping=legacy_map,
                                          transaction_status="GREEN")
        self.assertEqual(out["previous_1"], RUN_OCI)
        # Even a correct mapping never rotates on RED.
        with self.assertRaises(ValueError):
            KG.migrate_with_predecessor(ledger, CAND_OCI,
                                        predecessor_mapping=oci_map,
                                        transaction_status="RED")


class TriggerIntentTests(unittest.TestCase):
    def test_no_intent_before_trigger_safe_to_trigger(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            self.assertIsNone(TI.readback(gp, guard["binding_digest"]))
            record = TI.record(gp, guard["binding_digest"])
            self.assertEqual(record["binding_digest"], guard["binding_digest"])
            self.assertEqual(TI.readback(gp, guard["binding_digest"])["binding_digest"],
                             guard["binding_digest"])

    def test_stale_intent_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = make_guard(td)
            TI.record(gp, guard["binding_digest"])
            with self.assertRaises(TI.TriggerIntentError):
                TI.readback(gp, "sha256:" + "f" * 64)
            with self.assertRaises(TI.TriggerIntentError):
                TI.record(gp, "sha256:" + "f" * 64)


class UpdateVerifyCrashSafetyTests(unittest.TestCase):
    def _guard(self, td):
        anchor = Path(td) / "anchor"
        anchor.write_text("x", encoding="utf-8")
        gp = Path(td) / "guard.json"
        guard = GUARD.arm(gp, CAND_OCI, RUN_OCI, CFG, anchor)
        return gp, guard

    def _probes(self):
        return [ACC.CoreProbe(name, lambda: True)
                for name in sorted(ACC.REQUIRED_CORE_PROBES)]

    def test_interruption_before_trigger_leaves_no_intent(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            # No intent yet: update_and_verify must trigger exactly once.
            calls = []
            seq = iter([RUN_OCI, RUN_OCI, CAND_OCI])

            def trigger():
                calls.append("trigger")

            def inspect():
                calls.append("inspect")
                value = next(seq)
                if isinstance(value, Exception):
                    raise value
                return value

            out = DOCK.update_and_verify(
                gp, guard["binding_digest"], trigger, inspect,
                self._probes(), lambda _: None, lambda _: True,
                attempts=3, interval=0, sleeper=lambda _: None)
            self.assertEqual(out["state"], "committed")
            self.assertEqual(calls[0], "trigger")
            self.assertEqual(calls.count("trigger"), 1)

    def test_interruption_after_trigger_observes_without_reissue(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            # Simulate a pre-restart trigger: durable intent already exists,
            # guard still armed, running already converged to candidate.
            TI.record(gp, guard["binding_digest"])
            calls = []

            def trigger():
                calls.append("trigger")
                raise AssertionError("must not reissue uncertain update")

            out = DOCK.update_and_verify(
                gp, guard["binding_digest"], trigger, lambda: CAND_OCI,
                self._probes(), lambda _: calls.append("restore") or None,
                lambda _: True, attempts=1, interval=0,
                sleeper=lambda _: None)
            self.assertEqual(out["state"], "committed")
            self.assertNotIn("trigger", calls)

    def test_trigger_exception_becomes_uncertain_observe_not_reissue(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            calls = []

            def trigger():
                calls.append("trigger")
                raise RuntimeError("helper crashed after possible effect")

            # First attempt crashes during trigger; the intent is durable.
            # Second attempt (restart) must observe, not trigger again.
            seq = iter([RUN_OCI, CAND_OCI])

            def inspect():
                return next(seq)

            out = DOCK.update_and_verify(
                gp, guard["binding_digest"], trigger, inspect,
                self._probes(), lambda _: None, lambda _: True,
                attempts=2, interval=0, sleeper=lambda _: None)
            self.assertEqual(out["state"], "committed")
            self.assertEqual(calls.count("trigger"), 1)
            # Restart after commit never triggers again (post-GREEN).
            out2 = DOCK.update_and_verify(
                gp, guard["binding_digest"],
                lambda: calls.append("trigger2"), lambda: CAND_OCI,
                [], lambda _: None, lambda _: True,
                attempts=1, interval=0, sleeper=lambda _: None)
            self.assertEqual(out2["state"], "committed")
            self.assertNotIn("trigger2", calls)

    def test_missing_container_window_converges(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            seq = iter([RUN_OCI, OSError("missing"), CAND_OCI])

            def inspect():
                value = next(seq)
                if isinstance(value, Exception):
                    raise value
                return value

            out = DOCK.wait_for_stock_update(
                gp, guard["binding_digest"], inspect, self._probes(),
                lambda _: None, lambda _: True,
                attempts=3, interval=0, sleeper=lambda _: None)
            self.assertEqual(out["state"], "committed")

    def test_ambiguous_third_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            with self.assertRaises(DOCK.DockerManBindingError):
                DOCK.wait_for_stock_update(
                    gp, guard["binding_digest"], lambda: THIRD,
                    self._probes(), lambda _: None, lambda _: True,
                    attempts=1, interval=0)
            self.assertEqual(GUARD.load(gp)["state"], "armed")

    def test_immediate_red_restores_exact_predecessor(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            seen = []
            out = ACC.run_transaction(
                gp, guard["binding_digest"], self._probes(),
                seen.append, lambda value: value == RUN_OCI,
                inject_red=True)
            self.assertEqual(out["state"], "recovered")
            self.assertEqual(seen, [RUN_OCI])

    def test_post_green_rollback_denied(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            out = ACC.run_transaction(
                gp, guard["binding_digest"], self._probes(),
                lambda _: None, lambda _: True)
            self.assertEqual(out["state"], "committed")
            # Automatic rollback authority ends on GREEN: committed cannot
            # transition to rolling-back, and a second transaction returns
            # GREEN without restoring.
            with self.assertRaises(GUARD.GuardError):
                GUARD.transition(gp, "rolling-back", guard["binding_digest"])
            out2 = ACC.run_transaction(
                gp, guard["binding_digest"], [],
                lambda _: (_ for _ in ()).throw(AssertionError("must not restore")),
                lambda _: True)
            self.assertEqual(out2["state"], "committed")

    def test_stale_binding_rejected_before_trigger(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard = self._guard(td)
            called = []
            with self.assertRaises(DOCK.DockerManBindingError):
                DOCK.update_and_verify(
                    gp, "sha256:" + "f" * 64,
                    lambda: called.append(True), lambda: CAND_OCI,
                    self._probes(), lambda _: None, lambda _: True,
                    attempts=1, interval=0)
            self.assertEqual(called, [])
            self.assertEqual(GUARD.load(gp)["state"], "armed")
            self.assertIsNone(TI.readback(gp, guard["binding_digest"]))


class OciLocalAmbiguityTests(unittest.TestCase):
    def test_single_repo_digest_required(self):
        # Exactly one RepoDigest is authoritative; zero/multiple fail.
        self.assertEqual(
            UVA.running_repo_digest(
                "c", lambda argv: "img" if argv[1] == "inspect"
                else json.dumps([f"{REPO}@{CAND_OCI}"]),
            ), CAND_OCI)
        with self.assertRaises(RuntimeError):
            UVA.running_repo_digest(
                "c", lambda argv: "img" if argv[1] == "inspect" else json.dumps([]))
        with self.assertRaises(RuntimeError):
            UVA.running_repo_digest(
                "c", lambda argv: "img" if argv[1] == "inspect"
                else json.dumps([f"{REPO}@{CAND_OCI}", f"{REPO}@{OTHER_OCI}"]))

    def test_lock_contention_single_winner(self):
        with tempfile.TemporaryDirectory() as td:
            state = {"digest": RUN_OCI}
            writes = []
            first_write = threading.Event()

            def inspect(_ref):
                return state["digest"]

            def run(argv):
                candidate = argv[-1].split("@", 1)[1]
                writes.append(candidate)
                if candidate == CAND_OCI:
                    first_write.set()
                    time.sleep(0.1)
                state["digest"] = candidate
                return mock.Mock(stdout="")

            errors = []

            def worker(candidate):
                try:
                    PROM.promote(
                        repository=REPO, alias="m07-t06-fixture-lock",
                        candidate_digest=candidate,
                        expected_current_digest=RUN_OCI,
                        output_path=Path(td) / f"{candidate[-1]}.json",
                        lock_path=Path(td) / "promotion.lock")
                except PROM.PromotionError as exc:
                    errors.append(str(exc))

            with mock.patch.object(PROM, "inspect_digest", side_effect=inspect), \
                 mock.patch.object(PROM, "run_checked", side_effect=run):
                one = threading.Thread(target=worker, args=(CAND_OCI,))
                two = threading.Thread(target=worker, args=(OTHER_OCI,))
                one.start()
                self.assertTrue(first_write.wait(2))
                two.start()
                one.join()
                two.join()
            self.assertEqual(writes, [CAND_OCI])
            self.assertEqual(len(errors), 1)
            self.assertIn("stale/superseded", errors[0])


if __name__ == "__main__":
    unittest.main()
