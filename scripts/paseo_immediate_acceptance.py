#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from scripts.paseo_transaction_guard import GuardError, load, transition

class AcceptanceError(RuntimeError): pass
class RemoteServiceUnavailable(RuntimeError): pass

@dataclass(frozen=True)
class CoreProbe:
    name: str
    check: Callable[[], bool]
    remote: bool = False
    remote_blocking: bool = False

def run_transaction(guard_path: Path, binding: str, probes: list[CoreProbe],
                    restore_predecessor: Callable[[str], None],
                    verify_recovery: Callable[[str], bool],
                    *, inject_red: bool = False) -> dict:
    g=load(guard_path)
    if g['state']=='committed': return {'status':'GREEN','state':'committed','binding_digest':g['binding_digest']}
    if g['state']=='recovered': return {'status':'RED','state':'recovered','binding_digest':g['binding_digest']}
    if g['binding_digest'] != binding: raise AcceptanceError('stale transaction binding')
    if g['state']=='armed': g=transition(guard_path,'observed',binding)
    if g['state']=='observed': g=transition(guard_path,'validating',binding)
    if g['state']!='validating': raise AcceptanceError('transaction is not validating')
    failed=[]
    if inject_red: failed.append('injected-red')
    else:
        for probe in probes:
            try: ok=bool(probe.check())
            except RemoteServiceUnavailable:
                if probe.remote and not probe.remote_blocking: continue
                ok=False
            except Exception: ok=False
            if not ok: failed.append(probe.name)
    if not failed:
        g=transition(guard_path,'committed',binding)
        return {'status':'GREEN','state':g['state'],'binding_digest':binding}
    g=transition(guard_path,'rolling-back',binding)
    try: restore_predecessor(g['previous_digest'])
    except Exception as exc: raise AcceptanceError('predecessor restore failed; guard remains rolling-back') from exc
    if not verify_recovery(g['previous_digest']): raise AcceptanceError('recovery verification failed; guard remains rolling-back')
    g=transition(guard_path,'recovered',binding)
    return {'status':'RED','state':g['state'],'binding_digest':binding,'failed_probes':failed}
