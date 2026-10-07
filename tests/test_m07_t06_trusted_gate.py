"""M07-T06 trusted final-gate / first-channel / typed-legacy / Update+Verify tests.

Trust model (changed after R01 RED): hand-authored PASS-shaped records NEVER
prove acceptance. Every trust positive below is acquired through the genuine
shipped producer entrypoints — ``paseo_tower_validator.validate`` in ``real``
mode (M07-T05-harness fake-only Docker/registry/transport boundaries),
``paseo_state_roundtrip.prove`` (real clone/sequence, fake Docker daemon
boundary), ``paseo_transaction_guard.arm`` and real repo-byte bindings
(companion identity, policy/launcher hashes, harness-chain source head).
Hand-shaped records are used ONLY for negatives (malformed shapes and the
exact R01 forgery classes), each asserting rejection AND absence of
disallowed registry/trigger effects while resources still exist.

Classification (synthetic only, no real effects):
- Inference-capable entrypoints (Muse/Codex/provider, real LLM launcher):
  exercised ONLY through the genuine validator under the fake-only harness
  (fake ``paseo``/``pi`` bindirs, local ``http.server`` Codex fixture on
  127.0.0.1, synthetic secret files). No real inference, provider
  auth/admission, ordinary-credential reads, or prompt resends occur.
- Mutation-capable entrypoints:
  - Docker CLI / registry transport: ALWAYS mocked (``inspect_digest`` /
    ``run_checked``) or harness-faked. No daemon, image, network, GHCR,
    Tower, Unraid or production object is touched. ``channel_status`` ints
    carry registry reads; only HTTP 404 is verified absence.
  - Unraid/DockerMan trigger, probes, restore/recovery: fake recording
    callables. Guard/ledger/intent files: disposable ``TemporaryDirectory``
    siblings only. Production lock root faked via temp dirs where the Tower
    domain is exercised.
  - Credentials: synthetic digest-shaped strings and harness fixture secrets
    only; nothing real is admitted.
- Normative bytecode isolation: this module pins the R01 isolated-env shape
  at import (``PYTHONDONTWRITEBYTECODE=1`` + disposable ``PYTHONPYCACHEPREFIX``)
  so harness-spawned staged-python children cannot write bytecode into the
  kernel-watched staged tree (exact diagnosed ambient failure mode; product
  watch and assertions untouched). This is test-scope isolation, documented
  here and in evidence, not a product change and not an assertion relaxation.
- Product entrypoints exercised genuinely: ``paseo_tower_validator.validate``,
  ``paseo_state_roundtrip.prove``, ``paseo_final_gate.assemble``,
  ``paseo_accepted_promotion.promote`` / ``promote_first_channel`` /
  ``classify_channel_status`` / ``verify_channel_absence``,
  ``paseo_legacy_identity.validate`` / ``verify_anchor`` /
  ``verify_imported_image``, ``paseo_known_good`` typed rotation/migration,
  ``paseo_trigger_intent.record`` / ``readback``,
  ``paseo_dockerman_binding.update_and_verify`` / ``wait_for_stock_update``,
  ``paseo_immediate_acceptance.run_transaction``,
  ``paseo_transaction_guard.arm`` / ``load``,
  ``paseo_update_verify_action.running_repo_digest`` /
  ``observe_running_identity``.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

# Normative R01 isolated-env shape at module scope (see header). Record prior
# values for honest reporting; teardown restores them and removes the cache dir.
_PRIOR_ENV = {}
_OWN_CACHE_DIR = None
for _key in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"):
    if _key in os.environ:
        _PRIOR_ENV[_key] = os.environ[_key]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
if "PYTHONPYCACHEPREFIX" not in os.environ:
    _OWN_CACHE_DIR = tempfile.mkdtemp(prefix="m07-t06-pycache-")
    os.environ["PYTHONPYCACHEPREFIX"] = _OWN_CACHE_DIR

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
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
STATE = _load("m07_t06_state", "scripts/paseo_state_roundtrip.py")
BUILD = _load("m07_t06_build", "scripts/paseo_candidate_build.py")
H = _load("m07_t06_harness", "tests/test_m07_t05_validator_adapter.py")
HT = H.T

REPO = HT.REAL_REPOSITORY
CAND_OCI = HT.REAL_OCI_DIGEST          # genuine OCI manifest digest under test
# Genuine pulled local image ID: the harness fake pins it to IMAGE_ID
# (producer fixture), divergent from the OCI digest by construction.
CAND_LOCAL = HT.IMAGE_ID
RUN_OCI = "sha256:" + "a" * 64         # divergent OCI predecessor
RUN_LOCAL = "sha256:" + "7" * 64       # divergent local predecessor image ID
LEGACY_IMG = "sha256:" + "6" * 64      # legacy predecessor image-ID value
CFG = "sha256:" + "d" * 64
OTHER_OCI = "sha256:" + "e" * 64
THIRD = "sha256:" + "f" * 64


def tearDownModule():  # noqa: N802 (unittest hook name is fixed)
    for _key in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"):
        if _key in _PRIOR_ENV:
            os.environ[_key] = _PRIOR_ENV[_key]
        elif _key in os.environ:
            del os.environ[_key]
    if _OWN_CACHE_DIR is not None:
        import shutil
        shutil.rmtree(_OWN_CACHE_DIR, ignore_errors=True)


def _repo_digests(source_root=ROOT):
    companion = BUILD.companion_bundle_identity(Path(source_root))
    pol = Path(source_root) / "config" / "pi-agent" / "policies" / "llm-test-policy.json"
    grd = Path(source_root) / "config" / "pi-agent" / "bin" / "run-llm-test.sh"
    return {
        "companion": companion["source_digest"],
        "policy": "sha256:" + hashlib.sha256(pol.read_bytes()).hexdigest(),
        "launcher": "sha256:" + hashlib.sha256(grd.read_bytes()).hexdigest(),
    }


def _make_baseline(root):
    baseline = Path(root) / "baseline" / ".paseo"
    (baseline / "projects").mkdir(parents=True)
    (baseline / "config.json").write_text('{"daemon":{"relay":{"enabled":true}}}\n')
    (baseline / "daemon-keypair.json").write_text('{"fixture":true}\n')
    (baseline / "server-id").write_text("fixture\n")
    (baseline / "projects" / "projects.json").write_text("{}\n")
    return baseline.parent


def _state_fakes():
    calls = []

    def probe(image, home, name, candidate_state=None):
        calls.append(image)
        if candidate_state is not None:
            marker = Path(home) / ".paseo" / "state-roundtrip-candidate.json"
            marker.write_text(json.dumps(candidate_state) + "\n")
        return True
    return calls, probe


def _setup_chain(parent, kind, *, anchor_bytes=b"legacy-image-bytes"):
    """Build genuine chain inputs WITHOUT acquiring (setup only).

    Same builders as :func:`_acquire` (harness chain, fixture secrets,
    fixture source, actual baseline, armed guard) but stops before any
    acquisition run. Returns a setup dict; the caller runs acquisition
    itself — either shipped ``FG.assemble_from_acquisition`` (as
    :func:`_acquire` does) or the production writer's in-process
    acquisition via :func:`_acquisition_bundle`.
    """
    td = Path(parent) / "chain"
    td.mkdir(parents=True, exist_ok=True)
    codex, muse = H._secrets(td)
    files = H._fixture_chain(td, image_id=CAND_LOCAL)
    chain = dict(zip(("candidate_file", "handoff_file", "build_input_file",
                      "tested_image_file", "build_record_file", "publication_file"), files))
    bindir = HT.make_fake_paseo(td / "bindir")
    wit = td / "witness.jsonl"
    wit.write_text("")
    calls, fstate = [], {"net_exists": False, "network": "pi-unraid-validator",
                         "bindir": str(bindir), "witness_host": str(wit)}
    source_root = HT.fixture_source(td)
    companion = dict(HT.REAL_COMPANION)
    if kind == "oci":
        predecessor = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
        previous_local = RUN_LOCAL
    elif kind == "legacy":
        anchor = Path(parent) / "legacy.tar"
        anchor.write_bytes(anchor_bytes)
        archive_digest = "sha256:" + hashlib.sha256(anchor_bytes).hexdigest()
        predecessor = {"kind": "legacy", "image_id": LEGACY_IMG,
                       "archive_path": str(anchor), "archive_sha256": archive_digest,
                       "config_digest": CFG, "state_identity": "legacy-state-1"}
        previous_local = LEGACY_IMG
    else:
        predecessor = {"kind": "local", "image_id": RUN_LOCAL}
        previous_local = RUN_LOCAL
    baseline_src = _make_baseline(Path(parent) / "st")
    anchor_g = Path(parent) / "rollback.json"
    anchor_g.write_text("{}\n", encoding="utf-8")
    guard_path = Path(parent) / "guard.json"
    running_value = predecessor.get("digest", predecessor.get("image_id"))
    GUARD.arm(guard_path, CAND_OCI, running_value, CFG, anchor_g)
    state_calls, probe = _state_fakes()
    return {
        "parent": Path(parent), "td": td, "codex": codex, "muse": muse,
        "chain": chain, "bindir": bindir, "calls": calls, "fstate": fstate,
        "source_root": source_root, "companion": companion,
        "predecessor": predecessor, "previous_local": previous_local,
        "baseline_src": baseline_src, "guard_path": guard_path,
        "guard": GUARD.load(guard_path), "probe": probe,
        "state_calls": state_calls,
        "validator_state_root": Path(parent) / "vst",
        "validator_output": Path(parent) / "vout.json",
        "state_root": Path(parent) / "sst",
        "state_output": Path(parent) / "sout.json",
    }


@contextlib.contextmanager
def _acquisition_transports(setup):
    """Fake-only transport context for shipped acquisition runs.

    Local Codex server + harness fake Docker/registry + seam patches on the
    shipped producer modules. The producer modules are shared objects, so
    writer-driven in-process acquisition is faked identically to direct
    ``FG.assemble_from_acquisition`` calls. Yields ``(server, fake)``.
    """
    with HT.LocalCodexServer() as server:
        fake = HT.make_fake_docker(digest=CAND_OCI, image_id=CAND_LOCAL, calls=setup["calls"],
                                   state=setup["fstate"], server_base=server.base,
                                   codex_secret_host=setup["codex"], muse_secret_host=setup["muse"])
        with mock.patch.object(FG.tower_validator.shutil, "which",
                               return_value="/usr/bin/docker"), \
             mock.patch.object(FG.tower_validator.os, "chown"), \
             mock.patch.object(FG.tower_validator, "run", side_effect=fake), \
             mock.patch.object(FG.state_prove.shutil, "which",
                               return_value="/usr/bin/docker"), \
             mock.patch.object(FG.state_prove, "image_readback",
                               side_effect=lambda x: x), \
             mock.patch.object(FG.state_prove, "runtime_probe", side_effect=setup["probe"]), \
             mock.patch.object(FG.state_prove.os, "chown"):
            yield server, fake


def _acquisition_bundle(setup, base_url):
    """Locator-only writer acquisition bundle (JSON-serializable).

    Carries file/secret locators plus the ledger-owned typed predecessor
    observation — NEVER producer/validator/state objects. ``base_url`` is
    the fake-only Codex transport base from :func:`_acquisition_transports`.
    """
    chain = setup["chain"]
    return {
        "candidate_file": str(chain["candidate_file"]),
        "handoff_file": str(chain["handoff_file"]),
        "build_input_file": str(chain["build_input_file"]),
        "tested_image_file": str(chain["tested_image_file"]),
        "build_record": str(chain["build_record_file"]),
        "publication_file": str(chain["publication_file"]),
        "source_root": str(setup["source_root"]),
        "companion_bundle": setup["companion"],
        "codex_secret": str(setup["codex"]),
        "codex_base_url": base_url,
        "codex_model": "m",
        "muse_secret": str(setup["muse"]),
        "validator_state_root": str(setup["validator_state_root"]),
        "validator_output": str(setup["validator_output"]),
        "baseline_path": str(setup["baseline_src"]),
        "baseline_local_image_id": setup["previous_local"],
        "state_root": str(setup["state_root"]),
        "state_output": str(setup["state_output"]),
        "predecessor": copy.deepcopy(setup["predecessor"]),
        "guard_path": str(setup["guard_path"]),
    }


def _acquire(kind, parent, *, tamper=None, anchor_bytes=b"legacy-image-bytes"):
    """Acquire→assemble through the SHIPPED integration boundary.

    Builds a genuine harness chain, then invokes shipped
    ``FG.assemble_from_acquisition`` (which itself calls the shipped
    validator, state-prove and guard-readback entrypoints). Only external
    acquisition/transport seams are faked. Returns
    ``(gate, guard, guard_path, state_record, predecessor, info)`` where
    info carries the genuinely acquired validator record and chain bindings.
    """
    td = Path(parent) / "chain"
    td.mkdir(parents=True, exist_ok=True)
    codex, muse = H._secrets(td)
    files = H._fixture_chain(td, image_id=CAND_LOCAL)
    chain = dict(zip(("candidate_file", "handoff_file", "build_input_file",
                      "tested_image_file", "build_record_file", "publication_file"), files))
    if tamper is not None:
        tamper(chain)
    bindir = HT.make_fake_paseo(td / "bindir")
    wit = td / "witness.jsonl"
    wit.write_text("")
    calls, fstate = [], {"net_exists": False, "network": "pi-unraid-validator",
                         "bindir": str(bindir), "witness_host": str(wit)}
    source_root = HT.fixture_source(td)
    companion = dict(HT.REAL_COMPANION)
    if kind == "oci":
        predecessor = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
        previous_local = RUN_LOCAL
    elif kind == "legacy":
        anchor = Path(parent) / "legacy.tar"
        anchor.write_bytes(anchor_bytes)
        archive_digest = "sha256:" + hashlib.sha256(anchor_bytes).hexdigest()
        predecessor = {"kind": "legacy", "image_id": LEGACY_IMG,
                       "archive_path": str(anchor), "archive_sha256": archive_digest,
                       "config_digest": CFG, "state_identity": "legacy-state-1"}
        previous_local = LEGACY_IMG
    else:
        predecessor = {"kind": "local", "image_id": RUN_LOCAL}
        previous_local = RUN_LOCAL
    baseline_src = _make_baseline(Path(parent) / "st")
    anchor_g = Path(parent) / "rollback.json"
    anchor_g.write_text("{}\n", encoding="utf-8")
    guard_path = Path(parent) / "guard.json"
    running_value = predecessor.get("digest", predecessor.get("image_id"))
    GUARD.arm(guard_path, CAND_OCI, running_value, CFG, anchor_g)
    state_calls, probe = _state_fakes()
    with HT.LocalCodexServer() as server:
        fake = HT.make_fake_docker(digest=CAND_OCI, image_id=CAND_LOCAL, calls=calls,
                                   state=fstate, server_base=server.base,
                                   codex_secret_host=codex, muse_secret_host=muse)
        with mock.patch.object(FG.tower_validator.shutil, "which",
                               return_value="/usr/bin/docker"), \
             mock.patch.object(FG.tower_validator.os, "chown"), \
             mock.patch.object(FG.tower_validator, "run", side_effect=fake), \
             mock.patch.object(FG.state_prove.shutil, "which",
                               return_value="/usr/bin/docker"), \
             mock.patch.object(FG.state_prove, "image_readback",
                               side_effect=lambda x: x), \
             mock.patch.object(FG.state_prove, "runtime_probe", side_effect=probe), \
             mock.patch.object(FG.state_prove.os, "chown"):
            gate, ctx = FG.assemble_from_acquisition(
                repository=REPO, candidate_digest=CAND_OCI,
                candidate_file=chain["candidate_file"], handoff_file=chain["handoff_file"],
                build_input_file=chain["build_input_file"],
                tested_image_file=chain["tested_image_file"],
                build_record=chain["build_record_file"],
                publication_file=chain["publication_file"],
                source_root=source_root, companion_bundle=companion,
                codex_secret=codex, codex_base_url=server.base, codex_model="m",
                muse_secret=muse,
                validator_state_root=Path(parent) / "vst",
                validator_output=Path(parent) / "vout.json",
                baseline_path=baseline_src, baseline_local_image_id=previous_local,
                state_root=Path(parent) / "sst", state_output=Path(parent) / "sout.json",
                predecessor=copy.deepcopy(predecessor), guard_path=guard_path)
    assert gate["schema_version"] == 2 and gate["status"] == "GREEN"
    validator = ctx["validator_record"]
    assert [c for c in state_calls] == [validator["subject"]["observed_image_id"],
                                        previous_local]
    live = _repo_digests(source_root)
    assert live["companion"] == validator["subject"]["companion_bundle"]["source_digest"]
    assert live["policy"] == validator["subject"]["policy_identity"]["sha256"]
    assert live["launcher"] == validator["subject"]["launcher_identity"]["sha256"]
    build_input = json.loads(Path(chain["build_input_file"]).read_bytes())
    info = {"validator": validator, "source_head": build_input["source_head"],
            "digests": live, "chain": chain}
    guard = GUARD.load(guard_path)
    return gate, guard, guard_path, ctx["state_record"], predecessor, info


_GEN = {}


def genuine_bundle():
    """One cached genuine validator record + chain bindings (forgery bases).

    Acquired once through the shipped integration boundary (see _acquire);
    callers MUST deepcopy before mutating. The disposable work root persists
    for the session so owned references stay readable.
    """
    if "bundle" in _GEN:
        return _GEN["bundle"]
    work = Path(tempfile.mkdtemp(prefix="m07t06-genuine-"))
    _, _, _, _, _, info = _acquire("oci", work)
    bundle = {"validator": info["validator"], "source_head": info["source_head"],
              "digests": info["digests"]}
    _GEN["bundle"] = bundle
    return bundle


def genuine_state(*, candidate_local, previous_local):
    """Prove A->C->A through the real state entrypoint (fake Docker boundary)."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        baseline = root / "baseline" / ".paseo"
        (baseline / "projects").mkdir(parents=True)
        (baseline / "config.json").write_text('{"daemon":{"relay":{"enabled":true}}}\n')
        (baseline / "daemon-keypair.json").write_text('{"fixture":true}\n')
        (baseline / "server-id").write_text("fixture\n")
        (baseline / "projects" / "projects.json").write_text("{}\n")
        src = baseline.parent
        calls = []

        def probe(image, home, name, candidate_state=None):
            calls.append(image)
            if candidate_state is not None:
                marker = Path(home) / ".paseo" / "state-roundtrip-candidate.json"
                marker.write_text(json.dumps(candidate_state) + "\n")
            return True

        with mock.patch.object(STATE.shutil, "which", return_value="/usr/bin/docker"), \
             mock.patch.object(STATE, "image_readback", side_effect=lambda x: x), \
             mock.patch.object(STATE, "runtime_probe", side_effect=probe), \
             mock.patch.object(STATE.os, "chown"):
            record = STATE.prove(baseline=src, candidate=candidate_local,
                                 previous=previous_local,
                                 state_root=root / "state", output=root / "out.json")
    assert record["status"] == "PASS", record.get("reason")
    assert [c for c in calls] == [candidate_local, previous_local]
    return record


def genuine_guard(tmpdir, *, candidate, previous, config=CFG):
    anchor = Path(tmpdir) / "rollback.json"
    anchor.write_text("{}\n", encoding="utf-8")
    guard_path = Path(tmpdir) / "guard.json"
    guard = GUARD.arm(guard_path, candidate, previous, config, anchor)
    return guard_path, guard, anchor


def assemble_genuine(kind, tmpdir, *, anchor_bytes=b"legacy-image-bytes"):
    """Assemble a final gate through the SHIPPED integration boundary.

    Thin wrapper over _acquire preserving the 5-tuple contract used across
    this file; every gate returned was acquired by shipped code (validator +
    state-prove + guard readback inside ``assemble_from_acquisition``), never
    hand-sequenced in tests.
    """
    gate, guard, guard_path, state, predecessor, _ = _acquire(
        kind, tmpdir, anchor_bytes=anchor_bytes)
    return gate, guard, guard_path, state, predecessor


def core_probes(ok=True):
    return [ACC.CoreProbe(name, (lambda: True) if ok else (lambda: False))
            for name in sorted(ACC.REQUIRED_CORE_PROBES)]


class GenuineTrustTests(unittest.TestCase):
    def test_genuine_real_record_assembles_with_divergent_namespaces(self):
        with tempfile.TemporaryDirectory() as td:
            gate, guard, _, _, predecessor = assemble_genuine("oci", td)
            self.assertEqual(predecessor["kind"], "oci")
            # Divergent OCI vs local values pass; namespaces stay distinct.
            self.assertNotEqual(gate["baseline_oci"], gate["baseline_local_image_id"])
            self.assertEqual(gate["baseline_oci"], RUN_OCI)
            self.assertEqual(gate["baseline_local_image_id"], RUN_LOCAL)
            self.assertNotEqual(gate["candidate_digest"], gate["candidate_local_image_id"])
            # Fixed profile values genuinely observed (not labels).
            observed = genuine_bundle()["validator"]["subject"]["muse_observed_effective"]
            self.assertEqual((observed["provider"], observed["model"], observed["thinking"]),
                             ("meta", "muse-spark-1.3-contributor", "max"))

    def test_genuine_local_predecessor_assembles(self):
        with tempfile.TemporaryDirectory() as td:
            gate, _, _, _, predecessor = assemble_genuine("local", td)
            self.assertEqual(predecessor["kind"], "local")
            self.assertEqual(gate["baseline_oci"], RUN_LOCAL)
            self.assertEqual(gate["baseline_local_image_id"], RUN_LOCAL)

    def test_end_to_end_oci_existing_channel_update(self):
        # Production update path: the writer acquires the trusted gate
        # in-process from the locator bundle (Tower domain faked, registry
        # mocked, acquisition transports faked). Caller gate records —
        # even genuine-valued ones — are refused (see DetachedBypassTests).
        with tempfile.TemporaryDirectory() as td:
            setup = _setup_chain(td, "oci")
            with _acquisition_transports(setup) as (server, _fake):
                bundle = _acquisition_bundle(setup, server.base)
                fake_root = Path(td) / "tower-state"
                fake_root.mkdir()
                with mock.patch.object(PROM.socket, "gethostname", return_value="Tower"), \
                     mock.patch.object(PROM, "PRODUCTION_LOCK_ROOT", fake_root), \
                     mock.patch.object(PROM, "inspect_digest",
                                       side_effect=[RUN_OCI, RUN_OCI, CAND_OCI]) as inspect, \
                     mock.patch.object(PROM, "run_checked") as run:
                    out = PROM.promote(
                        repository=REPO, alias="accepted", candidate_digest=CAND_OCI,
                        expected_current_digest=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        guard=setup["guard"],
                        lock_path=fake_root / "accepted.lock",
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO},
                        acquisition=bundle)
            self.assertTrue(out["production"])
            self.assertEqual(out["readback_digest"], CAND_OCI)
            self.assertEqual(out["running_predecessor"], RUN_OCI)
            self.assertEqual(out["rollback_digest"], RUN_OCI)
            self.assertEqual(inspect.call_count, 3)
            create = run.call_args_list[0].args[0]
            self.assertIn(f"{REPO}@{CAND_OCI}", create)
            self.assertIn(f"{REPO}:accepted", create)

    def test_end_to_end_legacy_first_channel_with_typed_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            gate, guard, _, _, predecessor = assemble_genuine("legacy", td)
            alias = "m07-t06-fixture-legacy"
            with mock.patch.object(PROM, "inspect_digest",
                                   side_effect=[PROM.PromotionError("404 Not Found"),
                                                CAND_OCI]) as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                out = PROM.promote_first_channel(
                    repository=REPO, alias=alias, candidate_digest=CAND_OCI,
                    output_path=Path(td) / "o.json",
                    final_gate=gate, guard=guard,
                    lock_path=Path(td) / "lock",
                    predecessor_mapping=predecessor, channel_status=404)
            self.assertTrue(out["first_create"])
            self.assertEqual(out["running_predecessor"], LEGACY_IMG)
            created = run.call_args_list[0].args[0]
            self.assertIn(f"{REPO}@{CAND_OCI}", created)
            self.assertNotIn(LEGACY_IMG, " ".join(created))
            self.assertEqual(inspect.call_count, 2)
            # Typed ledger migration: legacy current -> candidate, anchors kept.
            ledger = {"current": {"kind": "legacy", "image_id": LEGACY_IMG,
                                  "archive_sha256": predecessor["archive_sha256"],
                                  "config_digest": CFG,
                                  "state_identity": "legacy-state-1"},
                      "previous_1": {"kind": "oci", "digest": OTHER_OCI, "repository": REPO},
                      "previous_2": {"kind": "oci", "digest": THIRD, "repository": REPO}}
            migrated = KG.migrate_with_predecessor(
                ledger, {"kind": "oci", "digest": CAND_OCI, "repository": REPO},
                predecessor_mapping=predecessor, transaction_status="GREEN")
            self.assertEqual(migrated["current"], {"kind": "oci", "digest": CAND_OCI,
                                                   "repository": REPO})
            self.assertEqual(migrated["previous_1"]["kind"], "legacy")
            self.assertEqual(migrated["previous_1"]["archive_sha256"],
                             predecessor["archive_sha256"])
            # Crash-safe intent + immediate acceptance on the same guard.
            self.assertEqual(GUARD.load(Path(td) / "guard.json")["state"], "armed")

    def test_production_accepted_enforces_tower_lock_and_readback(self):
        with tempfile.TemporaryDirectory() as td:
            setup = _setup_chain(td, "oci")
            with _acquisition_transports(setup) as (server, _fake):
                bundle = _acquisition_bundle(setup, server.base)
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
                        candidate_digest=CAND_OCI,
                        output_path=Path(td) / "o.json",
                        guard=setup["guard"], lock_path=lock,
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO},
                        acquisition=bundle,
                        channel_status=404)
            self.assertTrue(out["production"])
            self.assertEqual(out["readback_digest"], CAND_OCI)
            # Out-of-domain fails before any detached/acquisition handling:
            # a caller record is fine here because the domain check fires
            # first (the production detached refusal is proven separately).
            # Own subdirectory: this td already holds the setup chain and
            # must not be rebuilt in place.
            probe_gate, probe_guard, _, _, _ = assemble_genuine(
                "oci", Path(td) / "probe")
            with mock.patch.object(PROM.socket, "gethostname", return_value="not-tower"), \
                 mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "Tower writer domain"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="accepted",
                        candidate_digest=CAND_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=probe_gate, guard=probe_guard,
                        lock_path=Path(td) / "foreign.lock",
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO},
                        channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()


class ForgeryTests(unittest.TestCase):
    """Hand-forged copies of the GENUINE record: every class must reject
    before any registry/trigger effect (mocks assert_not_called)."""

    def _forged_gate(self, td, mutate):
        bundle = genuine_bundle()
        validator = copy.deepcopy(bundle["validator"])
        mutate(validator)
        state = genuine_state(candidate_local=validator["subject"].get(
            "observed_image_id", CAND_LOCAL), previous_local=RUN_LOCAL)
        gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
        return validator, state, guard

    def _assert_no_effect(self, td, validator, state, guard, mapping):
        with mock.patch.object(PROM, "inspect_digest") as inspect, \
             mock.patch.object(PROM, "run_checked") as run:
            with self.assertRaises((FG.FinalGateError, PROM.PromotionError)):
                PROM.promote_first_channel(
                    repository=REPO, alias="m07-t06-fixture-forged",
                    candidate_digest=CAND_OCI,
                    output_path=Path(td) / "o.json",
                    final_gate=self._try_assemble(td, validator, state, guard),
                    guard=guard, lock_path=Path(td) / "lock",
                    predecessor_mapping=mapping, channel_status=404)
            inspect.assert_not_called()
            run.assert_not_called()

    def _try_assemble(self, td, validator, state, guard):
        bundle = genuine_bundle()
        mapping = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
        try:
            return FG.assemble(
                repository=REPO, candidate_digest=CAND_OCI,
                validator_record=validator, state_record=state,
                source_head=bundle["source_head"],
                companion_digest=bundle["digests"]["companion"],
                policy_digest=bundle["digests"]["policy"],
                launcher_digest=bundle["digests"]["launcher"],
                predecessor=mapping,
                guard_binding_digest=guard["binding_digest"], guard_candidate=CAND_OCI)
        except FG.FinalGateError:
            # Assembler correctly rejected: writer must also reject the
            # (unassemblable) attempt; return a schema-2 lookalike that the
            # writer still refuses via its own checks.
            return {"schema_version": 2, "status": "GREEN", "execution_class": "real",
                    "real_validation_satisfied": True, "repository": REPO,
                    "candidate_digest": "sha256:" + "0" * 64,
                    "candidate_local_image_id": CAND_LOCAL,
                    "source_head": bundle["source_head"],
                    "companion_digest": bundle["digests"]["companion"],
                    "policy_digest": bundle["digests"]["policy"],
                    "launcher_digest": bundle["digests"]["launcher"],
                    "predecessor": mapping, "baseline_oci": RUN_OCI,
                    "baseline_local_image_id": RUN_LOCAL,
                    "guard_binding_digest": guard["binding_digest"],
                    "required_gates": {}}

    def _forgery_case(self, mutate):
        with tempfile.TemporaryDirectory() as td:
            validator, state, guard = self._forged_gate(td, mutate)
            # Assembler-level rejection.
            with self.assertRaises(FG.FinalGateError):
                bundle = genuine_bundle()
                FG.assemble(
                    repository=REPO, candidate_digest=CAND_OCI,
                    validator_record=validator, state_record=state,
                    source_head=bundle["source_head"],
                    companion_digest=bundle["digests"]["companion"],
                    policy_digest=bundle["digests"]["policy"],
                    launcher_digest=bundle["digests"]["launcher"],
                    predecessor={"kind": "oci", "digest": RUN_OCI, "repository": REPO},
                    guard_binding_digest=guard["binding_digest"], guard_candidate=CAND_OCI)
            # Writer-level: no registry effect either.
            self._assert_no_effect(
                td, validator, state, guard,
                {"kind": "oci", "digest": RUN_OCI, "repository": REPO})

    def test_empty_effective_rejected(self):
        def mutate(v):
            v["subject"]["muse_effective_config"] = {}
        self._forgery_case(mutate)

    def test_hacked_effective_rejected(self):
        def mutate(v):
            v["subject"]["muse_effective_config"] = {"hacked": "yes"}
        self._forgery_case(mutate)

    def test_forbidden_substituted_profile_rejected(self):
        def mutate(v):
            v["subject"]["muse_profile_preflight"] = {
                "model": "gpt-6-astra", "thinking": "xhigh", "fallback_allowed": True}
            v["subject"]["muse_observed_effective"] = {
                "provider": "gpt", "model": "gpt-6-astra",
                "thinking": "xhigh", "effort": "xhigh"}
        self._forgery_case(mutate)

    def test_clamped_thinking_rejected(self):
        def mutate(v):
            v["subject"]["muse_profile_preflight"] = {
                "model": "meta/muse-spark-1.3-contributor", "thinking": "xhigh"}
            v["subject"]["muse_observed_effective"] = {
                "provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": "xhigh", "effort": "xhigh"}
        self._forgery_case(mutate)

    def test_null_thinking_rejected(self):
        def mutate(v):
            v["subject"]["muse_observed_effective"] = {
                "provider": "meta", "model": "muse-spark-1.3-contributor",
                "thinking": None, "effort": None}
        self._forgery_case(mutate)

    def test_fallback_reenabled_rejected(self):
        def mutate(v):
            v["subject"]["muse_profile_preflight"] = {
                "model": "meta/muse-spark-1.3-contributor", "thinking": "max",
                "fallback_allowed": True}
        self._forgery_case(mutate)

    def test_wrong_provider_rejected(self):
        def mutate(v):
            v["subject"]["muse_observed_effective"] = {
                "provider": "codex-lb", "model": "muse-spark-1.3-contributor",
                "thinking": "max", "effort": "max"}
        self._forgery_case(mutate)

    def test_evil_daemon_endpoint_rejected(self):
        for bad in ("attacker-controlled", "127.attacker.invalid",
                    "https://evil.example:7777", ""):
            def mutate(v, bad=bad):
                v["subject"]["daemon_binding"] = dict(v["subject"]["daemon_binding"])
                v["subject"]["daemon_binding"]["endpoint"] = bad
            self._forgery_case(mutate)

    def test_wrong_daemon_home_and_pi_path_rejected(self):
        def mutate(v):
            v["subject"]["daemon_binding"] = dict(v["subject"]["daemon_binding"])
            v["subject"]["daemon_binding"]["home"] = "/tmp/evil-home"
            v["subject"]["pi_binding"] = dict(v["subject"]["pi_binding"])
            v["subject"]["pi_binding"]["path"] = "/tmp/evil-pi"
        self._forgery_case(mutate)

    def test_version_mismatch_rejected(self):
        def mutate(v):
            v["subject"]["daemon_binding"] = dict(v["subject"]["daemon_binding"])
            v["subject"]["daemon_binding"]["version"] = "9.9.9"
        self._forgery_case(mutate)

    def test_missing_effective_blocks_rejected(self):
        for key in ("muse_effective_config", "muse_observed_effective",
                    "muse_profile_preflight", "daemon_binding", "pi_binding",
                    "muse_owned_child"):
            def mutate(v, key=key):
                v["subject"].pop(key, None)
            self._forgery_case(mutate)

    def test_fixture_execution_class_rejected(self):
        def mutate(v):
            v["execution_class"] = "fixture"
            v["real_validation_satisfied"] = False
        self._forgery_case(mutate)

    def test_wrong_digest_report_rejected(self):
        def mutate(v):
            v["digest"] = OTHER_OCI
        self._forgery_case(mutate)

    def test_stale_source_bundle_config_rejected(self):
        bundle = genuine_bundle()
        # Stale source head / companion / policy / launcher each fail.
        with tempfile.TemporaryDirectory() as td:
            validator = copy.deepcopy(bundle["validator"])
            state = genuine_state(candidate_local=CAND_LOCAL, previous_local=RUN_LOCAL)
            gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
            for field, bad in (("source_head", "00" * 20),
                               ("companion_digest", "sha256:" + "6" * 64),
                               ("policy_digest", "sha256:" + "7" * 64),
                               ("launcher_digest", "sha256:" + "8" * 64)):
                kwargs = dict(repository=REPO, candidate_digest=CAND_OCI,
                              validator_record=copy.deepcopy(validator),
                              state_record=state,
                              source_head=bundle["source_head"],
                              companion_digest=bundle["digests"]["companion"],
                              policy_digest=bundle["digests"]["policy"],
                              launcher_digest=bundle["digests"]["launcher"],
                              predecessor={"kind": "oci", "digest": RUN_OCI,
                                           "repository": REPO},
                              guard_binding_digest=guard["binding_digest"],
                              guard_candidate=CAND_OCI)
                kwargs[field] = bad
                with self.assertRaises(FG.FinalGateError):
                    FG.assemble(**kwargs)

    def test_tampered_handoff_rejected_by_genuine_producer(self):
        # Forgery at the acquisition INPUTS (not the record): flip one byte
        # of the genuine handoff chain file, then drive the full shipped
        # acquisition. The genuine producer must reject before any gate
        # exists (writer unreachable by construction: no gate to consume).
        def tamper(chain):
            p = Path(chain["handoff_file"])
            raw = p.read_bytes()
            p.write_bytes(b"X" + raw[1:])

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FG.FinalGateError):
                _acquire("oci", td, tamper=tamper)

    def test_tampered_candidate_rejected_by_genuine_producer(self):
        def tamper(chain):
            p = Path(chain["candidate_file"])
            raw = p.read_bytes()
            p.write_bytes(raw[:-2] + b"XY")

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FG.FinalGateError):
                _acquire("oci", td, tamper=tamper)

    def test_wrong_guard_binding_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as td:
            gate, guard, _, _, _ = assemble_genuine("oci", td)
            wrong = dict(gate)
            wrong["guard_binding_digest"] = "sha256:" + "8" * 64
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "binding mismatch"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-forged",
                        candidate_digest=CAND_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=wrong, guard=guard,
                        lock_path=Path(td) / "lock",
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO},
                        channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()


class TypedPredecessorTests(unittest.TestCase):
    def test_conflated_oci_local_values_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = genuine_bundle()
            # Forcing the OCI digest to equal the local previous conflates
            # the namespaces the Card requires distinct.
            state = genuine_state(candidate_local=CAND_LOCAL, previous_local=RUN_OCI)
            gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
            with self.assertRaisesRegex(FG.FinalGateError, "distinct values"):
                FG.assemble(
                    repository=REPO, candidate_digest=CAND_OCI,
                    validator_record=copy.deepcopy(bundle["validator"]),
                    state_record=state,
                    source_head=bundle["source_head"],
                    companion_digest=bundle["digests"]["companion"],
                    policy_digest=bundle["digests"]["policy"],
                    launcher_digest=bundle["digests"]["launcher"],
                    predecessor={"kind": "oci", "digest": RUN_OCI, "repository": REPO},
                    guard_binding_digest=guard["binding_digest"], guard_candidate=CAND_OCI)

    def test_ambiguous_and_invalid_mappings_rejected(self):
        bundle = genuine_bundle()
        with tempfile.TemporaryDirectory() as td:
            state = genuine_state(candidate_local=CAND_LOCAL, previous_local=RUN_LOCAL)
            gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
            bad_mappings = [
                {"kind": "weird", "digest": RUN_OCI},
                {"kind": "oci", "digest": RUN_OCI, "image_id": RUN_LOCAL,
                 "repository": REPO},
                {"kind": "oci", "digest": RUN_OCI},
                {"kind": "oci", "digest": RUN_OCI, "repository": "ghcr.io/other/repo"},
                {"kind": "local", "image_id": OTHER_OCI},
                {"kind": "legacy", "image_id": LEGACY_IMG,
                 "archive_sha256": OTHER_OCI, "config_digest": CFG,
                 "state_identity": ""},
            ]
            for bad in bad_mappings:
                with self.subTest(bad=bad.get("kind")):
                    with self.assertRaises((FG.FinalGateError, PROM.PromotionError)):
                        FG.assemble(
                            repository=REPO, candidate_digest=CAND_OCI,
                            validator_record=copy.deepcopy(bundle["validator"]),
                            state_record=state,
                            source_head=bundle["source_head"],
                            companion_digest=bundle["digests"]["companion"],
                            policy_digest=bundle["digests"]["policy"],
                            launcher_digest=bundle["digests"]["launcher"],
                            predecessor=bad,
                            guard_binding_digest=guard["binding_digest"],
                            guard_candidate=CAND_OCI)

    def test_legacy_archive_mismatch_rejected_with_real_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = genuine_bundle()
            anchor = Path(td) / "legacy.tar"
            anchor.write_bytes(b"actual-legacy-bytes")
            mapping = {"kind": "legacy", "image_id": LEGACY_IMG,
                       "archive_path": str(anchor),
                       "archive_sha256": "sha256:" + "0" * 64,
                       "config_digest": CFG, "state_identity": "s"}
            state = genuine_state(candidate_local=CAND_LOCAL, previous_local=LEGACY_IMG)
            gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=LEGACY_IMG)
            with self.assertRaisesRegex(FG.FinalGateError, "archive"):
                FG.assemble(
                    repository=REPO, candidate_digest=CAND_OCI,
                    validator_record=copy.deepcopy(bundle["validator"]),
                    state_record=state,
                    source_head=bundle["source_head"],
                    companion_digest=bundle["digests"]["companion"],
                    policy_digest=bundle["digests"]["policy"],
                    launcher_digest=bundle["digests"]["launcher"],
                    predecessor=mapping,
                    guard_binding_digest=guard["binding_digest"], guard_candidate=CAND_OCI)

    def test_typed_kinds_validate_and_relabel_rejected(self):
        self.assertEqual(
            LEG.validate({"kind": "oci", "digest": CAND_OCI, "repository": REPO})["kind"], "oci")
        self.assertEqual(
            LEG.validate({"kind": "local", "image_id": CAND_LOCAL})["kind"], "local")
        with tempfile.TemporaryDirectory() as td:
            anchor = Path(td) / "archive.tar"
            anchor.write_bytes(b"legacy-bytes")
            digest = "sha256:" + hashlib.sha256(b"legacy-bytes").hexdigest()
            record = {"kind": "legacy", "image_id": CAND_LOCAL,
                      "archive_path": str(anchor), "archive_sha256": digest,
                      "config_digest": CFG, "state_identity": "state-1"}
            out = LEG.verify_anchor(record)
            self.assertEqual(out["archive_sha256"], digest)
            bad = dict(record)
            bad["archive_sha256"] = CAND_OCI
            with self.assertRaises(LEG.LegacyIdentityError):
                LEG.verify_anchor(bad)
            anchor.unlink()
            with self.assertRaises(LEG.LegacyIdentityError):
                LEG.verify_anchor(record)
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.validate({"kind": "weird", "digest": CAND_OCI})
        record = {"kind": "legacy", "image_id": CAND_LOCAL,
                  "archive_path": "/tmp/fake.tar",
                  "archive_sha256": CAND_OCI, "config_digest": CFG,
                  "state_identity": "s"}
        out = LEG.verify_imported_image(record, inspect_image_id=CAND_LOCAL, repo_digests=[])
        self.assertEqual(out["image_id"], CAND_LOCAL)
        with self.assertRaises(LEG.LegacyIdentityError):
            LEG.verify_imported_image(record, inspect_image_id=OTHER_OCI, repo_digests=[])
        with self.assertRaisesRegex(LEG.LegacyIdentityError, "relabeled"):
            LEG.verify_imported_image(record, inspect_image_id=CAND_LOCAL,
                                      repo_digests=[f"{REPO}@{CAND_LOCAL}"])


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

    def test_first_create_race_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            gate, guard, _, _, _ = assemble_genuine("oci", td)
            mapping = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
            with mock.patch.object(PROM, "inspect_digest", return_value=OTHER_OCI), \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "appeared before write"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=guard,
                        lock_path=Path(td) / "lock",
                        predecessor_mapping=mapping, channel_status=404)
                run.assert_not_called()
            with mock.patch.object(PROM, "inspect_digest",
                                   side_effect=PROM.PromotionError("404 nope")), \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaises(PROM.PromotionError):
                    PROM.promote_first_channel(
                        repository=REPO, alias="m07-t06-fixture-absent",
                        candidate_digest=CAND_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=guard,
                        lock_path=Path(td) / "lock",
                        predecessor_mapping=mapping, channel_status=404,
                        channel_status_fn=lambda: 200)
                run.assert_not_called()

    def test_channel_predecessor_distinct_from_running(self):
        with tempfile.TemporaryDirectory() as td:
            gate, guard, _, _, _ = assemble_genuine("oci", td)
            mapping = {"kind": "oci", "digest": RUN_OCI, "repository": REPO}
            with mock.patch.object(PROM, "inspect_digest",
                                   side_effect=[RUN_OCI, RUN_OCI, CAND_OCI]), \
                 mock.patch.object(PROM, "run_checked"):
                out = PROM.promote(
                    repository=REPO, alias="m07-t06-fixture-separate",
                    candidate_digest=CAND_OCI,
                    expected_current_digest=RUN_OCI,
                    output_path=Path(td) / "o.json",
                    final_gate=gate, guard=guard,
                    lock_path=Path(td) / "lock",
                    running_predecessor=RUN_OCI,
                    predecessor_mapping=mapping)
            self.assertEqual(out["running_predecessor"], RUN_OCI)
            bad = {"kind": "oci", "digest": OTHER_OCI, "repository": REPO}
            with mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "mapping mismatch"):
                    PROM.promote(
                        repository=REPO, alias="m07-t06-fixture-separate",
                        candidate_digest=CAND_OCI,
                        expected_current_digest=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=gate, guard=guard,
                        lock_path=Path(td) / "lock",
                        running_predecessor=RUN_OCI,
                        predecessor_mapping=bad)
                inspect.assert_not_called()
                run.assert_not_called()


class DetachedBypassTests(unittest.TestCase):
    """Detached caller records cannot confer accepted promotion eligibility.

    Every case below presents a FULLY POPULATED, value-consistent record at
    an actual CLI/library production boundary — not merely empty/wrong
    fields — and asserts rejection plus zero registry/trigger effects.
    """

    ATTACK_CANDIDATE = "sha256:" + "c" * 64
    ATTACK_LOCAL = "sha256:" + "1" * 64

    def _perfect_forgery(self, td):
        """Strongest fabricable shape for an attacker candidate.

        A genuinely acquired gate rebound with every value self-consistent
        (30/30 required PASS including the six source/isolation checks,
        well-formed digests, baselines == running mapping, guard binding ==
        live armed attacker guard, recomputed binding digest). Only
        provenance is fabricated: no validator/state run ever covered the
        attacker candidate.
        """
        gate, _, _, _, _ = assemble_genuine("oci", td)
        # Attacker guard lives in its own sibling dir: the chain guard file
        # already holds an armed guard and must not be rebound.
        atk = Path(td) / "attacker"
        atk.mkdir(exist_ok=True)
        _, guard_c, _ = genuine_guard(atk, candidate=self.ATTACK_CANDIDATE,
                                       previous=RUN_OCI)
        forged = copy.deepcopy(gate)
        forged["candidate_digest"] = self.ATTACK_CANDIDATE
        forged["candidate_local_image_id"] = self.ATTACK_LOCAL
        forged["baseline_oci"] = RUN_OCI
        forged["baseline_local_image_id"] = RUN_LOCAL
        forged["guard_binding_digest"] = guard_c["binding_digest"]
        forged.pop("acquisition", None)
        forged.pop("eligibility", None)
        body = {key: value for key, value in forged.items()
                if key != "binding_digest"}
        forged["binding_digest"] = (
            "sha256:" + hashlib.sha256(
                json.dumps(body, sort_keys=True,
                           separators=(",", ":")).encode()).hexdigest())
        # Sanity: the forgery IS value-consistent — the helper-level check
        # accepts it, proving content checks alone can never be the trust
        # root. The production boundaries below must still refuse it.
        checked = PROM.validate_trusted_final_gate(
            self.ATTACK_CANDIDATE, REPO, forged, guard_c,
            predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                 "repository": REPO})
        self.assertEqual(checked["candidate_digest"], self.ATTACK_CANDIDATE)
        return forged, guard_c

    def _tower(self, td):
        fake_root = Path(td) / "tower-state"
        fake_root.mkdir(exist_ok=True)
        return (mock.patch.object(PROM.socket, "gethostname", return_value="Tower"),
                mock.patch.object(PROM, "PRODUCTION_LOCK_ROOT", fake_root),
                fake_root)

    def test_perfect_forgery_rejected_at_production_promote(self):
        with tempfile.TemporaryDirectory() as td:
            forged, guard_c = self._perfect_forgery(td)
            host, root, fake_root = self._tower(td)
            with host, root, \
                 mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "diagnostic-only"):
                    PROM.promote(
                        repository=REPO, alias="accepted",
                        candidate_digest=self.ATTACK_CANDIDATE,
                        expected_current_digest=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=forged, guard=guard_c,
                        lock_path=fake_root / "accepted.lock",
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO})
                inspect.assert_not_called()
                run.assert_not_called()

    def test_perfect_forgery_rejected_at_production_first_channel(self):
        with tempfile.TemporaryDirectory() as td:
            forged, guard_c = self._perfect_forgery(td)
            host, root, fake_root = self._tower(td)
            with host, root, \
                 mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "diagnostic-only"):
                    PROM.promote_first_channel(
                        repository=REPO, alias="accepted",
                        candidate_digest=self.ATTACK_CANDIDATE,
                        output_path=Path(td) / "o.json",
                        final_gate=forged, guard=guard_c,
                        lock_path=fake_root / "accepted.lock",
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO},
                        channel_status=404)
                inspect.assert_not_called()
                run.assert_not_called()

    def test_promotion_cli_rejects_gate_file_for_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            forged, guard_c = self._perfect_forgery(td)
            gate_file = Path(td) / "gate.json"
            gate_file.write_text(json.dumps(forged))
            guard_file = Path(td) / "guard.json"
            guard_file.write_text(json.dumps(guard_c))
            host, root, _ = self._tower(td)
            argv = ["paseo_accepted_promotion", "promote", "--repository", REPO,
                    "--alias", "accepted", "--candidate-digest", self.ATTACK_CANDIDATE,
                    "--expected-current-digest", RUN_OCI,
                    "--output", str(Path(td) / "o.json"),
                    "--final-gate", str(gate_file), "--guard", str(guard_file)]
            with host, root, \
                 mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run, \
                 mock.patch.object(sys, "argv", argv):
                self.assertEqual(PROM.main(), 2)
                inspect.assert_not_called()
                run.assert_not_called()
            self.assertFalse((Path(td) / "o.json").exists())

    def test_detached_cli_record_even_genuine_valued_is_non_eligible(self):
        # The detached assembler CLI run over GENUINE records still emits a
        # diagnostic-only record the production writer refuses: even a
        # value-perfect CLI product confers no eligibility.
        with tempfile.TemporaryDirectory() as td:
            bundle = genuine_bundle()
            state = genuine_state(candidate_local=CAND_LOCAL, previous_local=RUN_LOCAL)
            _, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
            validator_file = Path(td) / "validator.json"
            validator_file.write_text(json.dumps(bundle["validator"]))
            state_file = Path(td) / "state.json"
            state_file.write_text(json.dumps(state))
            mapping_file = Path(td) / "mapping.json"
            mapping_file.write_text(json.dumps(
                {"kind": "oci", "digest": RUN_OCI, "repository": REPO}))
            gate_file = Path(td) / "gate.json"
            argv = ["paseo_final_gate", "--repository", REPO,
                    "--candidate-digest", CAND_OCI,
                    "--validator", str(validator_file), "--state", str(state_file),
                    "--source-head", bundle["source_head"],
                    "--companion-digest", bundle["digests"]["companion"],
                    "--policy-digest", bundle["digests"]["policy"],
                    "--launcher-digest", bundle["digests"]["launcher"],
                    "--predecessor", str(mapping_file),
                    "--guard-binding", guard["binding_digest"],
                    "--guard-candidate", CAND_OCI,
                    "--output", str(gate_file)]
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(FG.main(), 0)
            emitted = json.loads(gate_file.read_text())
            self.assertEqual(emitted.get("eligibility"), "diagnostic-only")
            host, root, fake_root = self._tower(td)
            with host, root, \
                 mock.patch.object(PROM, "inspect_digest") as inspect, \
                 mock.patch.object(PROM, "run_checked") as run:
                with self.assertRaisesRegex(PROM.PromotionError, "diagnostic-only"):
                    PROM.promote(
                        repository=REPO, alias="accepted", candidate_digest=CAND_OCI,
                        expected_current_digest=RUN_OCI,
                        output_path=Path(td) / "o.json",
                        final_gate=emitted, guard=guard,
                        lock_path=fake_root / "accepted.lock",
                        predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                             "repository": REPO})
                inspect.assert_not_called()
                run.assert_not_called()

    def test_omitted_source_isolation_gates_fail_closed(self):
        # Each of the six source/isolation checks is explicitly required:
        # omission fails even with every carried check PASS.
        with tempfile.TemporaryDirectory() as td:
            gate, guard, _, _, _ = assemble_genuine("oci", td)
            for missing in ("immutable_source_configuration", "runtime", "uid_gid",
                            "mount_isolation", "network_isolation", "secret_isolation"):
                with self.subTest(missing=missing):
                    clipped = copy.deepcopy(gate)
                    clipped["required_gates"].pop(missing, None)
                    with self.assertRaisesRegex(PROM.PromotionError, missing):
                        PROM.validate_trusted_final_gate(
                            CAND_OCI, REPO, clipped, guard,
                            predecessor_mapping={"kind": "oci", "digest": RUN_OCI,
                                                 "repository": REPO})


class AcquisitionOwnedPromotionTests(unittest.TestCase):
    """Genuine positives through the writer's in-process acquisition."""

    def test_production_first_channel_acquires_legacy_predecessor(self):
        with tempfile.TemporaryDirectory() as td:
            setup = _setup_chain(td, "legacy")
            with _acquisition_transports(setup) as (server, _fake):
                bundle = _acquisition_bundle(setup, server.base)
                fake_root = Path(td) / "tower-state"
                fake_root.mkdir()
                with mock.patch.object(PROM.socket, "gethostname", return_value="Tower"), \
                     mock.patch.object(PROM, "PRODUCTION_LOCK_ROOT", fake_root), \
                     mock.patch.object(PROM, "inspect_digest",
                                       side_effect=[PROM.PromotionError("404 Not Found"),
                                                    CAND_OCI]), \
                     mock.patch.object(PROM, "run_checked"):
                    out = PROM.promote_first_channel(
                        repository=REPO, alias="accepted", candidate_digest=CAND_OCI,
                        output_path=Path(td) / "o.json",
                        guard=setup["guard"], lock_path=fake_root / "accepted.lock",
                        predecessor_mapping=copy.deepcopy(setup["predecessor"]),
                        acquisition=bundle, channel_status=404)
            self.assertTrue(out["production"] and out["first_create"])
            self.assertEqual(out["running_predecessor"], LEGACY_IMG)
            self.assertEqual(out["readback_digest"], CAND_OCI)


class LedgerMigrationTests(unittest.TestCase):
    def test_typed_rotation_and_no_uncertain_commit(self):
        ledger = {"current": {"kind": "oci", "digest": RUN_OCI, "repository": REPO},
                  "previous_1": {"kind": "oci", "digest": OTHER_OCI, "repository": REPO},
                  "previous_2": {"kind": "oci", "digest": THIRD, "repository": REPO}}
        rotated = KG.commit_on_terminal(
            ledger, {"kind": "oci", "digest": CAND_OCI, "repository": REPO},
            transaction_status="GREEN")
        self.assertEqual(rotated["current"], {"kind": "oci", "digest": CAND_OCI,
                                              "repository": REPO})
        self.assertEqual(rotated["previous_1"]["digest"], RUN_OCI)
        for status in ("RED", "RECOVERED", "UNKNOWN", "BLOCKED", "FAIL"):
            with self.assertRaisesRegex(ValueError, "never rotates"):
                KG.commit_on_terminal(
                    ledger, {"kind": "oci", "digest": CAND_OCI, "repository": REPO},
                    transaction_status=status)

    def test_legacy_migration_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ledger.json"
            p.write_text(json.dumps({"current": RUN_OCI, "previous_1": OTHER_OCI,
                                     "previous_2": THIRD}))
            migrated = KG.migrate_legacy_ledger(json.loads(p.read_text()))
            KG.atomic_write(p, migrated)
            loaded = KG.load(p)
            self.assertEqual(loaded["current"], {"kind": "oci", "digest": RUN_OCI})


class TriggerIntentTests(unittest.TestCase):
    def test_no_intent_before_trigger_safe_to_trigger(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
            self.assertIsNone(TI.readback(gp, guard["binding_digest"]))
            record = TI.record(gp, guard["binding_digest"])
            self.assertEqual(record["binding_digest"], guard["binding_digest"])
            self.assertEqual(TI.readback(gp, guard["binding_digest"])["binding_digest"],
                             guard["binding_digest"])

    def test_stale_intent_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            gp, guard, _ = genuine_guard(td, candidate=CAND_OCI, previous=RUN_OCI)
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
            calls = []
            seq = iter([RUN_OCI, RUN_OCI, CAND_OCI])

            def trigger():
                calls.append("trigger")

            def inspect():
                calls.append("inspect")
                return next(seq)

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

            seq = iter([RUN_OCI, CAND_OCI])

            def inspect():
                return next(seq)

            out = DOCK.update_and_verify(
                gp, guard["binding_digest"], trigger, inspect,
                self._probes(), lambda _: None, lambda _: True,
                attempts=2, interval=0, sleeper=lambda _: None)
            self.assertEqual(out["state"], "committed")
            self.assertEqual(calls.count("trigger"), 1)
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

    def test_legacy_restore_observes_typed_identity(self):
        with tempfile.TemporaryDirectory() as td:
            anchor = Path(td) / "legacy.tar"
            anchor.write_bytes(b"restore-bytes")
            archive_digest = "sha256:" + hashlib.sha256(b"restore-bytes").hexdigest()
            mapping = {"kind": "legacy", "image_id": LEGACY_IMG,
                       "archive_path": str(anchor), "archive_sha256": archive_digest,
                       "config_digest": CFG, "state_identity": "legacy-state-1"}

            def runner(argv):
                if argv[1] == "inspect":
                    return "legacy-container-image"
                if argv[1] == "image" and "{{.Id}}" in " ".join(argv):
                    return LEGACY_IMG + "\n"
                return json.dumps([])

            observed = UVA.observe_running_identity("pi-unraid-paseo", runner,
                                                    predecessor=mapping)
            self.assertEqual(observed, {"kind": "legacy", "image_id": LEGACY_IMG})
            # RED transaction restores the exact legacy-typed value.
            gp = Path(td) / "guard.json"
            anchor2 = Path(td) / "rollback.json"
            anchor2.write_text("{}\n")
            guard = GUARD.arm(gp, CAND_OCI, LEGACY_IMG, CFG, anchor2)
            seen = []
            out = ACC.run_transaction(
                gp, guard["binding_digest"], self._probes(),
                seen.append, lambda value: value == LEGACY_IMG,
                inject_red=True)
            self.assertEqual(out["state"], "recovered")
            self.assertEqual(seen, [LEGACY_IMG])


class OciLocalAmbiguityTests(unittest.TestCase):
    def test_single_repo_digest_required(self):
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

    def test_legacy_local_observation_rejects_relabel_and_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            anchor = Path(td) / "legacy.tar"
            anchor.write_bytes(b"obs-bytes")
            archive_digest = "sha256:" + hashlib.sha256(b"obs-bytes").hexdigest()
            mapping = {"kind": "legacy", "image_id": LEGACY_IMG,
                       "archive_path": str(anchor), "archive_sha256": archive_digest,
                       "config_digest": CFG, "state_identity": "s"}

            def runner(argv):
                if argv[1] == "inspect":
                    return "img"
                if argv[1] == "image" and "{{.Id}}" in " ".join(argv):
                    return LEGACY_IMG + "\n"
                return json.dumps([])

            self.assertEqual(
                UVA.observe_running_identity("c", runner, predecessor=mapping),
                {"kind": "legacy", "image_id": LEGACY_IMG})

            def relabel_runner(argv):
                if argv[1] == "inspect":
                    return "img"
                if argv[1] == "image" and "{{.Id}}" in " ".join(argv):
                    return LEGACY_IMG + "\n"
                return json.dumps([f"{REPO}@{LEGACY_IMG}"])

            with self.assertRaisesRegex(RuntimeError, "relabeled"):
                UVA.observe_running_identity("c", relabel_runner, predecessor=mapping)

            def mismatch_runner(argv):
                if argv[1] == "inspect":
                    return "img"
                if argv[1] == "image" and "{{.Id}}" in " ".join(argv):
                    return OTHER_OCI + "\n"
                return json.dumps([])

            with self.assertRaisesRegex(RuntimeError, "mismatch"):
                UVA.observe_running_identity("c", mismatch_runner, predecessor=mapping)

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
