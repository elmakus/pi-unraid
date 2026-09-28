from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/"scripts"/"paseo_state_roundtrip.py"
spec=importlib.util.spec_from_file_location("paseo_state_roundtrip",SCRIPT); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
class StateRoundTripTests(unittest.TestCase):
    def baseline(self,root):
        p=root/"baseline"/".paseo"; (p/"projects").mkdir(parents=True)
        (p/"config.json").write_text('{"daemon":{"relay":{"enabled":true}}}\n'); (p/"daemon-keypair.json").write_text('{"fixture":true}\n'); (p/"server-id").write_text("fixture\n"); (p/"projects"/"projects.json").write_text("{}\n")
        return p.parent
    def test_clone_records_hashes_without_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=self.baseline(root); dst=root/"clone"; dst.mkdir(); x=M.clone_representative(src,dst)
            self.assertEqual(x["source"],str(src.resolve())); self.assertIn("config.json",x["files"]); self.assertNotIn("fixture",json.dumps(x["files"]))
    def test_roundtrip_uses_candidate_then_previous_and_preserves_marker(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=self.baseline(root); calls=[]; cand="sha256:"+"a"*64; prev="sha256:"+"b"*64
            def probe(image,home,name): calls.append((image,str(home))); return True
            with mock.patch.object(M.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(M,"image_readback",side_effect=lambda x:x), mock.patch.object(M,"runtime_probe",side_effect=probe), mock.patch.object(M.os,"chown"):
                r=M.prove(baseline=src,candidate=cand,previous=prev,state_root=root/"state",output=root/"out.json")
            self.assertEqual(r["status"],"PASS"); self.assertEqual([x[0] for x in calls],[cand,prev]); self.assertEqual(r["checks"]["direct_skip_path"],"PASS")
    def test_irreversible_is_blocked_before_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=self.baseline(root); cand="sha256:"+"a"*64; prev="sha256:"+"b"*64
            with mock.patch.object(M.shutil,"which",return_value="/usr/bin/docker"), mock.patch.object(M,"image_readback",side_effect=lambda x:x), mock.patch.object(M.os,"chown"), mock.patch.object(M,"runtime_probe") as probe:
                r=M.prove(baseline=src,candidate=cand,previous=prev,state_root=root/"state",output=root/"out.json",inject_irreversible=True)
            self.assertEqual(r["status"],"BLOCKED"); self.assertEqual(r["checks"]["irreversible_transition"],"BLOCKED"); probe.assert_not_called()
    def test_requires_immutable_image_id(self):
        with self.assertRaises(M.ProofError): M.image_readback("accepted")
if __name__=="__main__": unittest.main()
