import tempfile,unittest
from pathlib import Path
from scripts.paseo_dockerman_binding import DockerManBindingError,observe_stock_update
from scripts.paseo_immediate_acceptance import CoreProbe
from scripts.paseo_transaction_guard import arm,load
A='sha256:'+'a'*64; B='sha256:'+'b'*64; C='sha256:'+'c'*64
class Tests(unittest.TestCase):
 def fx(self):
  d=tempfile.TemporaryDirectory(); r=Path(d.name); a=r/'rollback'; a.write_text('{}'); p=r/'guard'; g=arm(p,B,A,C,a); return d,p,g
 def probes(self): return [CoreProbe(x,lambda:True) for x in ('exact-digest','health','rpc-provider','mounts-ownership','core-invariants')]
 def test_exact_inspect_binds_stock_update(self):
  d,p,g=self.fx()
  with d: self.assertEqual(observe_stock_update(p,g['binding_digest'],lambda:B,self.probes(),lambda _:self.fail(),lambda _:True)['state'],'committed')
 def test_stale_status_cannot_masquerade_as_success(self):
  d,p,g=self.fx()
  with d:
   with self.assertRaises(DockerManBindingError): observe_stock_update(p,g['binding_digest'],lambda:A,self.probes(),lambda _:None,lambda _:True)
   self.assertEqual(load(p)['state'],'armed')
 def test_inspect_failure_fails_closed(self):
  d,p,g=self.fx()
  with d:
   def bad(): raise OSError('inspect failed')
   with self.assertRaises(DockerManBindingError): observe_stock_update(p,g['binding_digest'],bad,self.probes(),lambda _:None,lambda _:True)
   self.assertEqual(load(p)['state'],'armed')
 def test_restart_readback_is_idempotent_after_commit(self):
  d,p,g=self.fx()
  with d:
   observe_stock_update(p,g['binding_digest'],lambda:B,self.probes(),lambda _:self.fail(),lambda _:True)
   self.assertEqual(observe_stock_update(p,g['binding_digest'],lambda:A,[],lambda _:self.fail(),lambda _:True)['state'],'committed')
if __name__=='__main__': unittest.main()
