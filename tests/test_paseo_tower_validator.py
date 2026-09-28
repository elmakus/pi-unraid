from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"paseo_tower_validator.py"
spec=importlib.util.spec_from_file_location("paseo_tower_validator",SCRIPT)
V=importlib.util.module_from_spec(spec); spec.loader.exec_module(V)

class TowerValidatorTests(unittest.TestCase):
    def test_requires_immutable_digest(self):
        with self.assertRaises(V.ValidationError): V.immutable_ref("ghcr.io/elmakus/pi-unraid","accepted")
        self.assertEqual(V.immutable_ref("ghcr.io/elmakus/pi-unraid","sha256:"+"a"*64),"ghcr.io/elmakus/pi-unraid@sha256:"+"a"*64)

    def test_pass_is_disposable_and_secret_free(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        with tempfile.TemporaryDirectory() as td:
            inspect_calls = 0
            def fake(argv, timeout=300, check=True):
                nonlocal inspect_calls
                if argv[:4]==["docker","buildx","imagetools","inspect"]: return mock.Mock(returncode=0,stdout=f"Digest: {digest}\n",stderr="")
                if argv[:3]==["docker","image","inspect"]: return mock.Mock(returncode=0,stdout=image_id+"\n",stderr="")
                if argv[:2]==["docker","network"]: return mock.Mock(returncode=0,stdout="",stderr="")
                if argv[:2]==["docker","inspect"]:
                    run_call=next(c.args[0] for c in runner.call_args_list if c.args[0][:2]==["docker","run"])
                    mounts=[]
                    for i,x in enumerate(run_call):
                        if x=="-v":
                            src,dst,_=run_call[i+1].split(":"); mounts.append({"Source":src,"Destination":dst})
                    inspect_calls += 1
                    health = "starting" if inspect_calls == 1 else "healthy"
                    obj={"Config":{"User":"99:100","Env":["TZ=Europe/Zurich","HOME=/home/paseo"]},"HostConfig":{"NetworkMode":"pi-unraid-validator"},"Mounts":mounts,"State":{"Status":"running","Health":{"Status":health}}}
                    return mock.Mock(returncode=0,stdout=json.dumps([obj]),stderr="")
                return mock.Mock(returncode=0,stdout="",stderr="")
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake) as runner:
                out=Path(td)/"result.json"
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=out,state_root=Path(td))
            self.assertEqual(result["status"],"PASS")
            self.assertGreaterEqual(inspect_calls, 2)
            run_call=next(c.args[0] for c in runner.call_args_list if c.args[0][:2]==["docker","run"])
            joined=" ".join(run_call)
            self.assertNotIn("/var/run/docker.sock",joined); self.assertNotIn("codex-lb",joined); self.assertNotIn("unraid-api.key",joined)
            self.assertIn("--read-only",run_call)

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

    def test_codex_smoke_uses_dedicated_read_only_mount_and_classifies_failures(self):
        digest="sha256:"+"a"*64; image_id="sha256:"+"b"*64
        for smoke_rc, expected in ((0,"PASS"),(20,"BLOCKED"),(21,"FAIL"),(23,"FAIL")):
            with self.subTest(smoke_rc=smoke_rc), tempfile.TemporaryDirectory() as td:
                secret=Path(td)/"codex.env"; secret.write_text("CODEX_LB_API_KEY=fixture-not-real\n")
                calls=[]
                def fake(argv, timeout=300, check=True):
                    calls.append(argv)
                    if argv[:4]==["docker","buildx","imagetools","inspect"]: return mock.Mock(returncode=0,stdout=f"Digest: {digest}\n",stderr="")
                    if argv[:3]==["docker","image","inspect"]: return mock.Mock(returncode=0,stdout=image_id+"\n",stderr="")
                    if argv[:2]==["docker","network"]: return mock.Mock(returncode=0,stdout="",stderr="")
                    if argv[:2]==["docker","inspect"]:
                        run_call=next(x for x in calls if x[:2]==["docker","run"]); mounts=[]
                        for i,x in enumerate(run_call):
                            if x=="-v":
                                src,dst,mode=run_call[i+1].split(":"); mounts.append({"Source":src,"Destination":dst,"RW":mode!="ro"})
                        obj={"Config":{"User":"99:100","Env":["HOME=/home/paseo"]},"HostConfig":{"NetworkMode":"pi-unraid-validator"},"Mounts":mounts,"State":{"Status":"running","Health":{"Status":"healthy"}}}
                        return mock.Mock(returncode=0,stdout=json.dumps([obj]),stderr="")
                    if argv[:2]==["docker","exec"]: return mock.Mock(returncode=smoke_rc,stdout="",stderr="")
                    return mock.Mock(returncode=0,stdout="",stderr="")
                with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake):
                    result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=Path(td)/"out.json",state_root=Path(td)/"state",codex_secret=secret,codex_base_url="http://host.docker.internal:2455/v1",codex_model="fixture-model")
                self.assertEqual(result["status"],expected)
                run_call=next(x for x in calls if x[:2]==["docker","run"])
                self.assertIn(f"{secret.resolve()}:{V.CODEX_SECRET_TARGET}:ro",run_call)
                self.assertNotIn("fixture-not-real"," ".join(" ".join(x) for x in calls))
                exec_call=next(x for x in calls if x[:2]==["docker","exec"])
                self.assertIn("JSON.parse", exec_call[-1])
                self.assertNotIn("grep -q", exec_call[-1])
                if expected=="PASS": self.assertEqual(result["checks"]["codex_lb_smoke"],"PASS")

    def test_blocked_is_structured(self):
        digest="sha256:"+"a"*64
        with tempfile.TemporaryDirectory() as td, mock.patch.object(V.shutil,"which",return_value=None):
            out=Path(td)/"result.json"; result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=out,state_root=Path(td))
            self.assertEqual(result["status"],"BLOCKED"); self.assertEqual(json.loads(out.read_text())["status"],"BLOCKED")

if __name__=="__main__": unittest.main()
