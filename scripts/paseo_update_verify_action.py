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

def observe_running_identity(container, runner=run, *, predecessor=None):
    """Observe the typed running identity for a container.

    ``oci`` predecessors (or no mapping, preserving the historical
    single-RepoDigest behavior) require exactly one authoritative
    RepoDigest; zero/multiple fail closed. ``local``/``legacy``
    predecessors have no registry identity by design: the platform image
    ID is read back and verified against the typed mapping (legacy
    additionally verified against its archive anchor/state, never
    published and never relabeled as a manifest digest).
    """
    import re as _re
    kind = (predecessor or {}).get("kind", "oci")
    if kind == "oci":
        value = running_repo_digest(container, runner=runner)
        if predecessor is not None and value != predecessor.get("digest"):
            raise RuntimeError("running OCI digest mismatch vs typed predecessor")
        return {"kind": "oci", "digest": value}
    if kind not in ("local", "legacy"):
        raise RuntimeError("unsupported predecessor kind")
    image = runner(['docker', 'inspect', '-f', '{{.Image}}', container])
    raw_id = runner(['docker', 'image', 'inspect', '-f', '{{.Id}}', image])
    image_id = (raw_id or "").strip().splitlines()[-1].strip() if (raw_id or "").strip() else ""
    if not _re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise RuntimeError("running platform image identity unavailable")
    raw_repo = runner(['docker', 'image', 'inspect', '-f', '{{json .RepoDigests}}', image])
    try:
        repo_values = json.loads(raw_repo) if (raw_repo or "").strip() else []
    except ValueError as exc:
        raise RuntimeError("running RepoDigests unreadable") from exc
    if image_id != predecessor.get("image_id"):
        raise RuntimeError("running platform image mismatch vs typed predecessor")
    for entry in repo_values or []:
        if isinstance(entry, str) and "@" in entry and entry.rsplit("@", 1)[1] == image_id:
            raise RuntimeError("local image-ID relabeled as manifest digest")
    if kind == "legacy":
        from scripts.paseo_legacy_identity import (
            LegacyIdentityError, verify_anchor, verify_imported_image)
        try:
            verify_anchor(dict(predecessor))
            verify_imported_image(dict(predecessor), inspect_image_id=image_id,
                                  repo_digests=[e for e in (repo_values or []) if isinstance(e, str)])
        except LegacyIdentityError as exc:
            raise RuntimeError(f"legacy predecessor unverified: {exc}") from exc
    return {"kind": kind, "image_id": image_id}
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
    p.add_argument('--predecessor',default=None,
                   help='typed predecessor mapping JSON (oci/local/legacy); default oci')
    p.add_argument('--attempts',type=int,default=120); p.add_argument('--interval',type=float,default=1.0)
    a=p.parse_args(argv)
    try:
        predecessor=json.loads(a.predecessor) if a.predecessor else None
    except ValueError:
        p.error('predecessor must be JSON')
    if predecessor is not None and predecessor.get("kind") not in ("oci", "local", "legacy"):
        p.error('predecessor kind must be oci, local or legacy')
    probes={}
    for item in a.probe:
        name,sep,cmd=item.partition('=')
        if not sep or name not in REQUIRED_CORE_PROBES or name in probes: p.error('each required probe must be NAME=COMMAND exactly once')
        probes[name]=cmd
    if set(probes)!=REQUIRED_CORE_PROBES: p.error('all five required local core probes are required')
    if '{digest}' not in a.restore_command or '{digest}' not in a.recovery_command: p.error('restore/recovery commands must contain {digest}')
    core=[CoreProbe(name,lambda cmd=probes[name]: command_ok(cmd)) for name in sorted(REQUIRED_CORE_PROBES)]
    def _inspect_running():
        observed=observe_running_identity(a.container,predecessor=predecessor)
        return observed.get("digest", observed.get("image_id"))
    out=update_and_verify(a.guard,a.binding,lambda:trigger_dockerman(a.container),_inspect_running,core,
        lambda d:shell(a.restore_command.format(digest=d)),lambda d:command_ok(a.recovery_command.format(digest=d)),attempts=a.attempts,interval=a.interval)
    print(json.dumps(out,sort_keys=True)); return 0 if out.get('status')=='GREEN' else 2
if __name__=='__main__': raise SystemExit(main())
