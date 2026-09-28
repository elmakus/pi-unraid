#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from urllib.parse import quote
from scripts.paseo_dockerman_binding import update_and_verify
from scripts.paseo_immediate_acceptance import CoreProbe, REQUIRED_CORE_PROBES

DOCKERMAN_UPDATE='/usr/local/emhttp/plugins/dynamix.docker.manager/scripts/update_container'

def run(argv): return subprocess.run(argv,check=True,text=True,capture_output=True).stdout.strip()
def shell(command): subprocess.run(command,shell=True,check=True)
def running_repo_digest(container, runner=run):
    image=runner(['docker','inspect','-f','{{.Image}}',container])
    raw=runner(['docker','image','inspect','-f','{{json .RepoDigests}}',image])
    values=json.loads(raw)
    digests={v.rsplit('@',1)[1] for v in values if '@sha256:' in v}
    if len(digests)!=1: raise RuntimeError('running image does not expose one authoritative RepoDigest')
    return next(iter(digests))
def trigger_dockerman(container, runner=run): runner([DOCKERMAN_UPDATE,quote(container,safe='')])
def command_ok(command):
    return subprocess.run(command,shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def main(argv=None):
    p=argparse.ArgumentParser(description='Bounded Unraid Update + Verify action')
    p.add_argument('--guard',type=Path,required=True); p.add_argument('--binding',required=True)
    p.add_argument('--container',default='pi-unraid-paseo')
    p.add_argument('--probe',action='append',default=[],metavar='NAME=COMMAND')
    p.add_argument('--restore-command',required=True,help='shell command containing {digest}')
    p.add_argument('--recovery-command',required=True,help='shell command containing {digest}')
    p.add_argument('--attempts',type=int,default=120); p.add_argument('--interval',type=float,default=1.0)
    a=p.parse_args(argv)
    probes={}
    for item in a.probe:
        name,sep,cmd=item.partition('=')
        if not sep or name not in REQUIRED_CORE_PROBES or name in probes: p.error('each required probe must be NAME=COMMAND exactly once')
        probes[name]=cmd
    if set(probes)!=REQUIRED_CORE_PROBES: p.error('all five required local core probes are required')
    if '{digest}' not in a.restore_command or '{digest}' not in a.recovery_command: p.error('restore/recovery commands must contain {digest}')
    core=[CoreProbe(name,lambda cmd=probes[name]: command_ok(cmd)) for name in sorted(REQUIRED_CORE_PROBES)]
    out=update_and_verify(a.guard,a.binding,lambda:trigger_dockerman(a.container),lambda:running_repo_digest(a.container),core,
        lambda d:shell(a.restore_command.format(digest=d)),lambda d:command_ok(a.recovery_command.format(digest=d)),attempts=a.attempts,interval=a.interval)
    print(json.dumps(out,sort_keys=True)); return 0 if out.get('status')=='GREEN' else 2
if __name__=='__main__': raise SystemExit(main())
