import tempfile,unittest
from pathlib import Path
from scripts.paseo_dockerman_binding import DockerManBindingError,observe_stock_update,wait_for_stock_update,update_and_verify
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
 def test_waiter_converges_through_stop_remove_create_window(self):
  d,p,g=self.fx(); seq=iter([A,OSError('missing'),B])
  def inspect():
   x=next(seq)
   if isinstance(x,Exception): raise x
   return x
  with d: self.assertEqual(wait_for_stock_update(p,g['binding_digest'],inspect,self.probes(),lambda _:self.fail(),lambda _:True,attempts=3,interval=0,sleeper=lambda _:None)['state'],'committed')
 def test_waiter_restart_resumes_from_durable_armed_guard(self):
  d,p,g=self.fx()
  with d:
   with self.assertRaises(DockerManBindingError): wait_for_stock_update(p,g['binding_digest'],lambda:A,self.probes(),lambda _:None,lambda _:True,attempts=1,interval=0)
   self.assertEqual(load(p)['state'],'armed')
   self.assertEqual(wait_for_stock_update(p,g['binding_digest'],lambda:B,self.probes(),lambda _:self.fail(),lambda _:True,attempts=1,interval=0)['state'],'committed')
 def test_waiter_rejects_ambiguous_third_digest(self):
  d,p,g=self.fx()
  with d:
   with self.assertRaises(DockerManBindingError): wait_for_stock_update(p,g['binding_digest'],lambda:C,self.probes(),lambda _:None,lambda _:True,attempts=1,interval=0)
   self.assertEqual(load(p)['state'],'armed')
 def test_restart_readback_is_idempotent_after_commit(self):
  d,p,g=self.fx()
  with d:
   observe_stock_update(p,g['binding_digest'],lambda:B,self.probes(),lambda _:self.fail(),lambda _:True)
   self.assertEqual(observe_stock_update(p,g['binding_digest'],lambda:A,[],lambda _:self.fail(),lambda _:True)['state'],'committed')
 def test_update_and_verify_owns_trigger_and_acceptance_lifecycle(self):
  d,p,g=self.fx(); events=[]; seq=iter([A,OSError('missing'),B])
  def trigger(): events.append('trigger')
  def inspect():
   events.append('inspect'); x=next(seq)
   if isinstance(x,Exception): raise x
   return x
  with d:
   out=update_and_verify(p,g['binding_digest'],trigger,inspect,self.probes(),lambda _:self.fail(),lambda _:True,attempts=3,interval=0,sleeper=lambda _:None)
   self.assertEqual(out['state'],'committed'); self.assertEqual(events[0],'trigger')
 def test_update_and_verify_rejects_stale_binding_before_trigger(self):
  d,p,g=self.fx(); called=[]
  with d:
   with self.assertRaises(DockerManBindingError): update_and_verify(p,C,lambda:called.append(True),lambda:B,self.probes(),lambda _:None,lambda _:True,attempts=1,interval=0)
   self.assertEqual(called,[]); self.assertEqual(load(p)['state'],'armed')
if __name__=='__main__': unittest.main()
