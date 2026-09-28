import json,tempfile,unittest
from pathlib import Path
from scripts.paseo_transaction_guard import GuardError,arm,load,transition
A="sha256:"+"a"*64; B="sha256:"+"b"*64; C="sha256:"+"c"*64
class GuardTests(unittest.TestCase):
 def fixture(self,d):
  a=Path(d)/"rollback.json"; a.write_text("{}"); return a,Path(d)/"guard.json"
 def test_arm_readback_and_idempotent_restart(self):
  with tempfile.TemporaryDirectory() as d:
   a,p=self.fixture(d); g=arm(p,B,A,C,a); self.assertEqual(load(p),g); self.assertEqual(arm(p,B,A,C,a),g)
 def test_exact_binding_and_invalid_rebind_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   a,p=self.fixture(d); g=arm(p,B,A,C,a); before=p.read_bytes()
   with self.assertRaises(GuardError): arm(p,"sha256:"+"d"*64,A,C,a)
   self.assertEqual(p.read_bytes(),before); bad=json.loads(p.read_text()); bad["config_digest"]="sha256:"+"e"*64; p.write_text(json.dumps(bad))
   with self.assertRaises(GuardError): load(p)
 def test_state_machine_and_stale_binding(self):
  with tempfile.TemporaryDirectory() as d:
   a,p=self.fixture(d); g=arm(p,B,A,C,a)
   with self.assertRaises(GuardError): transition(p,"committed",g["binding_digest"])
   g=transition(p,"observed",g["binding_digest"]); g=transition(p,"validating",g["binding_digest"])
   self.assertEqual(transition(p,"committed",g["binding_digest"])["state"],"committed")
   with self.assertRaises(GuardError): transition(p,"observed","sha256:"+"f"*64)
 def test_rollback_path_and_terminal_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   a,p=self.fixture(d); g=arm(p,B,A,C,a); g=transition(p,"observed",g["binding_digest"]); g=transition(p,"rolling-back",g["binding_digest"]); g=transition(p,"recovered",g["binding_digest"])
   self.assertEqual(load(p)["state"],"recovered")
   with self.assertRaises(GuardError): transition(p,"armed",g["binding_digest"])
if __name__=="__main__": unittest.main()
