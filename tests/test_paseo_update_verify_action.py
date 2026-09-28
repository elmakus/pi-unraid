import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.paseo_update_verify_action import DOCKERMAN_UPDATE,main,running_repo_digest,trigger_dockerman
from scripts.paseo_transaction_guard import arm,load
A='sha256:'+'a'*64; B='sha256:'+'b'*64; C='sha256:'+'c'*64
class Tests(unittest.TestCase):
 def test_authoritative_running_digest_comes_from_repo_digests(self):
  seen=[]
  def runner(argv):
   seen.append(argv); return 'image-id' if argv[1]=='inspect' else json.dumps(['ghcr.io/elmakus/pi-unraid@'+B])
  self.assertEqual(running_repo_digest('pi-unraid-paseo',runner),B); self.assertEqual(seen[0][:3],['docker','inspect','-f'])
 def test_real_trigger_is_stock_dockerman_update_container(self):
  seen=[]; trigger_dockerman('pi-unraid-paseo',lambda argv:seen.append(argv) or '')
  self.assertEqual(seen,[[DOCKERMAN_UPDATE,'pi-unraid-paseo']])
 def test_command_surface_owns_bounded_transaction(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); anchor=root/'anchor'; anchor.write_text('x'); guard=root/'guard.json'; g=arm(guard,B,A,C,anchor); seen=[]
   def uv(path,binding,trigger,inspect,probes,restore,recover,**kw):
    self.assertEqual(path,guard); self.assertEqual(binding,g['binding_digest']); self.assertEqual({p.name for p in probes},{'exact-digest','health','rpc-provider','mounts-ownership','core-invariants'}); seen.append('owned'); return {'status':'GREEN','state':'committed'}
   args=['--guard',str(guard),'--binding',g['binding_digest'],'--restore-command','restore {digest}','--recovery-command','recover {digest}']
   for n in ('exact-digest','health','rpc-provider','mounts-ownership','core-invariants'): args += ['--probe',n+'=true']
   with patch('scripts.paseo_update_verify_action.update_and_verify',side_effect=uv): self.assertEqual(main(args),0)
   self.assertEqual(seen,['owned']); self.assertEqual(load(guard)['state'],'armed')
 def test_stale_binding_rejected_before_real_trigger(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); anchor=root/'anchor'; anchor.write_text('x'); guard=root/'guard.json'; g=arm(guard,B,A,C,anchor)
   args=['--guard',str(guard),'--binding',C,'--restore-command','restore {digest}','--recovery-command','recover {digest}']
   for n in ('exact-digest','health','rpc-provider','mounts-ownership','core-invariants'): args += ['--probe',n+'=true']
   with patch('scripts.paseo_update_verify_action.trigger_dockerman') as trigger:
    with self.assertRaises(Exception): main(args)
    trigger.assert_not_called(); self.assertEqual(load(guard)['state'],'armed')
if __name__=='__main__': unittest.main()
