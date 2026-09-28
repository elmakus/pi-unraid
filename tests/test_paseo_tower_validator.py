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
            def fake(argv, timeout=300, check=True):
                if argv[:4]==["docker","buildx","imagetools","inspect"]: return mock.Mock(returncode=0,stdout=f"Digest: {digest}\n",stderr="")
                if argv[:3]==["docker","image","inspect"]: return mock.Mock(returncode=0,stdout=image_id+"\n",stderr="")
                if argv[:2]==["docker","network"]: return mock.Mock(returncode=0,stdout="",stderr="")
                if argv[:2]==["docker","inspect"]:
                    run_call=next(c.args[0] for c in runner.call_args_list if c.args[0][:2]==["docker","run"])
                    mounts=[]
                    for i,x in enumerate(run_call):
                        if x=="-v":
                            src,dst,_=run_call[i+1].split(":"); mounts.append({"Source":src,"Destination":dst})
                    obj={"Config":{"User":"99:100","Env":["TZ=Europe/Zurich","HOME=/home/paseo"]},"HostConfig":{"NetworkMode":"pi-unraid-validator"},"Mounts":mounts,"State":{"Status":"running"}}
                    return mock.Mock(returncode=0,stdout=json.dumps([obj]),stderr="")
                return mock.Mock(returncode=0,stdout="",stderr="")
            with mock.patch.object(V.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(V.os,"chown"), mock.patch.object(V,"run",side_effect=fake) as runner:
                out=Path(td)/"result.json"
                result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=out,state_root=Path(td))
            self.assertEqual(result["status"],"PASS")
            run_call=next(c.args[0] for c in runner.call_args_list if c.args[0][:2]==["docker","run"])
            joined=" ".join(run_call)
            self.assertNotIn("/var/run/docker.sock",joined); self.assertNotIn("codex-lb",joined); self.assertNotIn("unraid-api.key",joined)
            self.assertIn("--read-only",run_call)

    def test_blocked_is_structured(self):
        digest="sha256:"+"a"*64
        with tempfile.TemporaryDirectory() as td, mock.patch.object(V.shutil,"which",return_value=None):
            out=Path(td)/"result.json"; result=V.validate(repository="ghcr.io/elmakus/pi-unraid",digest=digest,output=out,state_root=Path(td))
            self.assertEqual(result["status"],"BLOCKED"); self.assertEqual(json.loads(out.read_text())["status"],"BLOCKED")

if __name__=="__main__": unittest.main()
