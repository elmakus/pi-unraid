import tempfile,unittest
from pathlib import Path
from scripts.paseo_transaction_guard import GuardError,arm,load,transition
from scripts.paseo_immediate_acceptance import AcceptanceError,CoreProbe,RemoteServiceUnavailable,run_transaction
A='sha256:'+'a'*64; B='sha256:'+'b'*64; C='sha256:'+'c'*64
class Tests(unittest.TestCase):
 def fx(self):
  d=tempfile.TemporaryDirectory(); root=Path(d.name); anchor=root/'rollback'; anchor.write_text('{}'); gp=root/'guard'; g=arm(gp,B,A,C,anchor); return d,gp,g
 def probes(self): return [CoreProbe(x,lambda:True) for x in ('exact-digest','health','rpc-provider','mounts-ownership','core-invariants')]
 def test_green_commits_and_disables_rollback(self):
  d,p,g=self.fx()
  with d:
   out=run_transaction(p,g['binding_digest'],self.probes(),lambda _:self.fail(),lambda _:True); self.assertEqual(out['state'],'committed')
   with self.assertRaises(GuardError): transition(p,'rolling-back',g['binding_digest'])
   self.assertEqual(run_transaction(p,g['binding_digest'],[],lambda _:None,lambda _:True)['state'],'committed')
 def test_missing_or_duplicate_required_probe_fails_closed(self):
  for probes in ([], self.probes()[:-1], self.probes()+[CoreProbe('health',lambda:True)]):
   d,p,g=self.fx()
   with d:
    with self.assertRaises(AcceptanceError): run_transaction(p,g['binding_digest'],probes,lambda _:self.fail(),lambda _:True)
    self.assertEqual(load(p)['state'],'armed')
 def test_injected_red_restores_exact_predecessor_and_recovers(self):
  d,p,g=self.fx(); seen=[]
  with d:
   out=run_transaction(p,g['binding_digest'],self.probes(),seen.append,lambda x:x==A,inject_red=True); self.assertEqual((out['state'],seen),('recovered',[A]))
 def test_failed_recovery_stays_rolling_back(self):
  d,p,g=self.fx()
  with d:
   with self.assertRaises(AcceptanceError): run_transaction(p,g['binding_digest'],self.probes(),lambda _:None,lambda _:False,inject_red=True)
   self.assertEqual(load(p)['state'],'rolling-back')
 def test_failed_local_probe_rolls_back(self):
  d,p,g=self.fx(); seen=[]
  with d:
   self.assertEqual(run_transaction(p,g['binding_digest'],[CoreProbe('exact-digest',lambda:False)]+self.probes()[1:],seen.append,lambda _:True)['state'],'recovered'); self.assertEqual(seen,[A])
 def test_transient_remote_outage_nonblocking_by_default(self):
  d,p,g=self.fx()
  with d:
   def outage(): raise RemoteServiceUnavailable()
   self.assertEqual(run_transaction(p,g['binding_digest'],self.probes()+[CoreProbe('remote',outage,remote=True)],lambda _:self.fail(),lambda _:True)['state'],'committed')
 def test_contract_blocking_remote_outage_rolls_back(self):
  d,p,g=self.fx(); seen=[]
  with d:
   def outage(): raise RemoteServiceUnavailable()
   self.assertEqual(run_transaction(p,g['binding_digest'],self.probes()+[CoreProbe('remote',outage,remote=True,remote_blocking=True)],seen.append,lambda _:True)['state'],'recovered'); self.assertEqual(seen,[A])
 def test_stale_binding_fails_without_restore(self):
  d,p,g=self.fx(); seen=[]
  with d:
   with self.assertRaises(AcceptanceError): run_transaction(p,'sha256:'+'f'*64,self.probes(),seen.append,lambda _:True)
   self.assertEqual(seen,[]); self.assertEqual(load(p)['state'],'armed')
if __name__=='__main__': unittest.main()
