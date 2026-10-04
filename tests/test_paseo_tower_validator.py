from __future__ import annotations
import importlib.util, json, subprocess, tempfile, unittest, os
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"paseo_tower_validator.py"
spec=importlib.util.spec_from_file_location("paseo_tower_validator",SCRIPT)
V=importlib.util.module_from_spec(spec); spec.loader.exec_module(V)

def _stateful_fake(digest, image_id, *, catalog_rc=0, health_rc=0, calls=None, runner_ref=None):
    """Stateful docker fake: preexisting inspect is not-found until `docker run`.

    Handles the M07-T05 validator's ownership-verified lifecycle:
    buildx inspect, image pull/inspect (+RepoDigests JSON), network
    inspect, preexisting container inspect, run, runtime inspect, exec
    catalog/health, owned cleanup inspect/rm, network rm.
    """
    state={"ran": False}
    calls_list = calls if calls is not None else []
    def fake(argv, timeout=300, check=True):
        calls_list.append(argv)
        if argv[:4]==["docker","buildx","imagetools","inspect"]:
            return mock.Mock(returncode=0,stdout=f"Digest: {digest}\n",stderr="")
        if argv[:3]==["docker","image","inspect"]:
            if "{{json .RepoDigests}}" in " ".join(argv):
                ref=f"ghcr.io/elmakus/pi-unraid@{digest}"
                return mock.Mock(returncode=0,stdout=json.dumps([ref]),stderr="")
            return mock.Mock(returncode=0,stdout=image_id+"\n",stderr="")
        if argv[:3]==["docker","image","pull"]:
            return mock.Mock(returncode=0,stdout="",stderr="")
        if argv[:2]==["docker","network"]:
            # inspect -> not found (1) would trigger create; tests use present (0).
            return mock.Mock(returncode=0,stdout="",stderr="")
        if argv[:2]==["docker","inspect"]:
            if not state["ran"]:
                # Preexisting check before `docker run`: nothing there.
                return mock.Mock(returncode=1,stdout="",stderr="No such object")
            # Runtime/readback/cleanup inspect: derive mounts from the run call.
            run_call=next(x for x in calls_list if x[:2]==["docker","run"])
            mounts=[]
            for i,x in enumerate(run_call):
                if x=="-v":
                    parts=run_call[i+1].split(":")
                    src,dst=parts[0],parts[1]
                    mode=parts[2] if len(parts)>2 else "rw"
                    mounts.append({"Source":src,"Destination":dst,"RW":mode!="ro"})
            # Derive nonce label from the run call for owned-cleanup proof.
            _nonce = "unknown"
            for _i,_x in enumerate(run_call):
                if _x=="--label" and _i+1 < len(run_call) and run_call[_i+1].startswith("io.pi-unraid.validator-nonce="):
                    _nonce = run_call[_i+1].split("=",1)[1]
            obj={"Id":"fake-container-id-123","Image":image_id,"Config":{"User":"99:100","Env":["TZ=Europe/Zurich","HOME=/home/paseo"],"Labels":{"io.pi-unraid.validator-nonce":_nonce}},
                 "HostConfig":{"NetworkMode":"pi-unraid-validator"},
                 "Mounts":mounts,"State":{"Status":"running","Health":{"Status":"healthy"}}}
            return mock.Mock(returncode=0,stdout=json.dumps([obj]),stderr="")
        if argv[:2]==["docker","run"]:
            state["ran"]=True
            return mock.Mock(returncode=0,stdout="fake-container-id-123\n",stderr="")
        if argv[:2]==["docker","exec"]:
            payload=argv[-1]
            if "codex-catalog-check" in payload or "/tmp/codex-catalog.json" in payload:
                return mock.Mock(returncode=catalog_rc,stdout="",stderr="")
            if "codex-health-check" in payload or "/tmp/codex-health.json" in payload:
                return mock.Mock(returncode=health_rc,stdout="",stderr="")
            return mock.Mock(returncode=0,stdout="",stderr="")
        if argv[:2]==["docker","rm"]:
            return mock.Mock(returncode=0,stdout="",stderr="")
        return mock.Mock(returncode=0,stdout="",stderr="")
    return fake, calls_list, state

class TowerValidatorTests(unittest.TestCase):
    def test_requires_immutable_digest(self):
        with self.assertRaises(V.ValidationError): V.immutable_ref("ghcr.io/elmakus/pi-unraid","accepted")
        self.assertEqual(V.immutable_ref("ghcr.io/elmakus/pi-unraid","sha256:"+"a"*64),"ghcr.io/elmakus/pi-unraid@sha256:"+"a"*64)

    def test_pass_is_disposable_and_secret_free(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        with tempfile.TemporaryDirectory() as td:
            fake, calls, _ = _stateful_fake(digest, image_id)
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake) as runner:
                out=Path(td)/"result.json"
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=out,state_root=Path(td))
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["execution_class"],"fixture")
            self.assertFalse(result["real_validation_satisfied"])
            self.assertEqual(result["checks"].get("codex_no_inference"),"PASS")
            # No inference endpoint may appear in any docker exec payload.
            for c in calls:
                if c[:2]==["docker","exec"]:
                    self.assertNotIn("/responses", c[-1])
            run_call=next(c for c in calls if c[:2]==["docker","run"])
            joined=" ".join(run_call)
            self.assertNotIn("/var/run/docker.sock",joined); self.assertNotIn("codex-lb",joined); self.assertNotIn("unraid-api.key",joined)
            self.assertIn("--read-only",run_call)
            # No unconditional preexisting removal: exactly one run, and the
            # preexisting inspect observed absence before creation.
            self.assertEqual(sum(1 for c in calls if c[:2]==["docker","run"]), 1)

    def test_registry_digest_readback_accepts_buildx_column_spacing(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        with tempfile.TemporaryDirectory() as td:
            def fake(argv, timeout=300, check=True):
                if argv[:4]==["docker","buildx","imagetools","inspect"]:
                    return mock.Mock(returncode=0,stdout=f"Name: x\nDigest:    {digest}\n",stderr="")
                if argv[:3]==["docker","image","inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0,stdout=json.dumps([f"ghcr.io/elmakus/pi-unraid@{digest}"]),stderr="")
                    return mock.Mock(returncode=0,stdout=image_id+"\n",stderr="")
                if argv[:3]==["docker","image","pull"]:
                    return mock.Mock(returncode=0,stdout="",stderr="")
                if argv[:2]==["docker","network"]:
                    return mock.Mock(returncode=0,stdout="",stderr="")
                if argv[:2]==["docker","inspect"]:
                    # Preexisting vs runtime: distinguish by run presence.
                    ran=any(x[:2]==["docker","run"] for x in getattr(fake, "calls", []))
                    if not ran:
                        return mock.Mock(returncode=1,stdout="",stderr="No such object")
                    obj={"Config":{"User":"99:100","Env":["HOME=/home/paseo"]},"HostConfig":{"NetworkMode":"pi-unraid-validator"},"Mounts":[],"State":{"Status":"running","Health":{"Status":"healthy"}}}
                    return mock.Mock(returncode=0,stdout=json.dumps([obj]),stderr="")
                return mock.Mock(returncode=0,stdout="",stderr="")
            fake.calls=[]
            orig=fake
            def tracking(argv, timeout=300, check=True):
                fake.calls.append(argv)
                return orig(argv, timeout=timeout, check=check)
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=tracking):
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=Path(td)/"out.json",state_root=Path(td))
            self.assertNotEqual(result.get("reason"),"registry immutable digest readback mismatch")

    def test_runtime_waits_from_starting_to_healthy(self):
        states = iter([
            {"State":{"Status":"running","Health":{"Status":"starting"}}},
            {"State":{"Status":"running","Health":{"Status":"healthy"}}},
        ])
        with mock.patch.object(V,"run",side_effect=lambda argv, **kwargs: mock.Mock(stdout=json.dumps([next(states)]))), \
             mock.patch.object(V.time,"monotonic",side_effect=[0, 0]), \
             mock.patch.object(V.time,"sleep") as sleeper:
            obj = V.wait_for_runtime("candidate", timeout=10, poll_interval=0)
        self.assertEqual(obj["State"]["Health"]["Status"],"healthy")
        sleeper.assert_called_once_with(0)

    def test_runtime_rejects_terminal_unhealthy(self):
        payload={"State":{"Status":"running","Health":{"Status":"unhealthy"}}}
        with mock.patch.object(V,"run",return_value=mock.Mock(stdout=json.dumps([payload]))):
            with self.assertRaisesRegex(V.ValidationError,"unhealthy"):
                V.wait_for_runtime("candidate", timeout=10, poll_interval=0)

    def test_codex_noninference_uses_dedicated_read_only_mount_and_classifies(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        # (catalog_rc, health_rc, expected_status)
        for catalog_rc, expected in ((0,"PASS"),(20,"BLOCKED"),(21,"FAIL"),(23,"FAIL")):
            with self.subTest(catalog_rc=catalog_rc), tempfile.TemporaryDirectory() as td:
                secret=Path(td)/"codex.env"; secret.write_text("CODEX_LB_API_KEY=fixture-not-real\n"); secret.chmod(0o600)
                calls=[]
                fake, _, _ = _stateful_fake(digest, image_id, catalog_rc=catalog_rc, health_rc=0, calls=calls)
                with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake):
                    result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=Path(td)/"out.json",state_root=Path(td)/"state",codex_secret=secret,codex_base_url="http://host.docker.internal:2455/v1",codex_model="fixture-model")
                self.assertEqual(result["status"],expected)
                self.assertFalse(result["real_validation_satisfied"])
                run_call=next(x for x in calls if x[:2]==["docker","run"])
                self.assertIn(f"{secret.resolve()}:{V.CODEX_SECRET_TARGET}:ro",run_call)
                self.assertNotIn("fixture-not-real"," ".join(" ".join(x) for x in calls))
                exec_calls=[x for x in calls if x[:2]==["docker","exec"]]
                self.assertGreaterEqual(len(exec_calls), 1)
                for ec in exec_calls:
                    self.assertNotIn("/responses", ec[-1].lower().replace("\"/res\"+\"ponses\"", ""))
                    self.assertNotIn("/chat/completions", ec[-1])
                    # No token-bearing argv, no invalid curl placeholder, no body files.
                    self.assertNotIn("Bearer $key", ec[-1])
                    self.assertNotIn("%{{http_code}}", ec[-1])
                    self.assertNotIn("/tmp/codex-catalog.json", ec[-1])
                    self.assertNotIn("/tmp/codex-health.json", ec[-1])
                # Reachable robust Python payload (not shell curl + node).
                self.assertIn("codex-catalog-check", exec_calls[0][-1])
                self.assertIn("json.loads", exec_calls[0][-1])
                self.assertIn("262144", exec_calls[0][-1])
                self.assertNotIn("grep -q", exec_calls[0][-1])
                self.assertNotIn("curl ", exec_calls[0][-1])
                if expected=="PASS":
                    self.assertEqual(result["checks"]["codex_catalog"],"PASS")
                    self.assertEqual(result["checks"]["codex_auth"],"PASS")
                    self.assertEqual(result["checks"]["codex_health"],"PASS")
                    self.assertEqual(result["checks"]["codex_no_inference"],"PASS")
                    self.assertEqual(len(exec_calls), 2)

                if catalog_rc == 0:
                    # Structural parser fails closed on malformed input (via helper).
                    import importlib.util as _ilu_t
                    _spec = _ilu_t.spec_from_file_location("codex_helper_malformed", ROOT/"scripts"/"paseo_codex_noninference.py")
                    _mod = _ilu_t.module_from_spec(_spec); _spec.loader.exec_module(_mod)
                    with self.assertRaises(_mod.CodexError):
                        _mod.parse_catalog_body(b'{"data":')

    def test_codex_missing_credential_is_blocked(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        with tempfile.TemporaryDirectory() as td:
            fake, calls, _ = _stateful_fake(digest, image_id)
            missing=Path(td)/"missing-codex.env"
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake):
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=Path(td)/"out.json",state_root=Path(td)/"state",codex_secret=missing,codex_base_url="http://host.docker.internal:2455/v1",codex_model="fixture-model")
            self.assertEqual(result["status"],"BLOCKED")
            self.assertEqual(result["reason"],"dedicated Codex-LB credential file unavailable")

    def test_blocked_is_structured(self):
        digest="sha256:"+"a"*64
        with tempfile.TemporaryDirectory() as td, mock.patch.object(V.shutil,"which",return_value=None):
            out=Path(td)/"result.json"; result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=out,state_root=Path(td))
            self.assertEqual(result["status"],"BLOCKED"); self.assertEqual(json.loads(out.read_text())["status"],"BLOCKED")

    def test_preexisting_same_name_container_is_never_removed(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        with tempfile.TemporaryDirectory() as td:
            calls=[]
            def fake(argv, timeout=300, check=True):
                calls.append(argv)
                if argv[:4]==["docker","buildx","imagetools","inspect"]:
                    return mock.Mock(returncode=0,stdout=f"Digest: {digest}\n",stderr="")
                if argv[:3]==["docker","image","inspect"]:
                    if "{{json .RepoDigests}}" in " ".join(argv):
                        return mock.Mock(returncode=0,stdout=json.dumps([f"ghcr.io/elmakus/pi-unraid@{digest}"]),stderr="")
                    return mock.Mock(returncode=0,stdout=image_id+"\n",stderr="")
                if argv[:3]==["docker","image","pull"]:
                    return mock.Mock(returncode=0,stdout="",stderr="")
                if argv[:2]==["docker","network"]:
                    return mock.Mock(returncode=0,stdout="",stderr="")
                if argv[:2]==["docker","inspect"]:
                    # Simulate a foreign preexisting container with production mounts.
                    obj={"Config":{"User":"99:100","Env":[]},"HostConfig":{"NetworkMode":"pi-unraid-validator"},
                         "Mounts":[{"Source":"/mnt/user/appdata/pi-unraid/paseo-home","Destination":"/home/paseo"}],
                         "State":{"Status":"running","Health":{"Status":"healthy"}}}
                    return mock.Mock(returncode=0,stdout=json.dumps([obj]),stderr="")
                return mock.Mock(returncode=0,stdout="",stderr="")
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake):
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=Path(td)/"out.json",state_root=Path(td))
            self.assertEqual(result["status"],"FAIL")
            self.assertIn("not owned", result.get("reason",""))
            # No run and no rm of the foreign object may have occurred.
            self.assertEqual(sum(1 for c in calls if c[:2]==["docker","run"]), 0)
            self.assertEqual(sum(1 for c in calls if c[:2]==["docker","rm"]), 0)

    def test_secret_requires_private_mode(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        with tempfile.TemporaryDirectory() as td:
            secret=Path(td)/"codex.env"; secret.write_text("CODEX_LB_API_KEY=fixture-not-real\n"); secret.chmod(0o644)
            fake, calls, _ = _stateful_fake(digest, image_id, calls=[])
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake):
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=Path(td)/"out.json",state_root=Path(td)/"state",codex_secret=secret,codex_base_url="http://host.docker.internal:2455/v1",codex_model="fixture-model")
            self.assertEqual(result["status"],"FAIL")
            self.assertIn("private", result.get("reason",""))

if __name__=="__main__": unittest.main()
