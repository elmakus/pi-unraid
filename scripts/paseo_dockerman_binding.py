#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Callable
from scripts.paseo_immediate_acceptance import CoreProbe, run_transaction
from scripts.paseo_transaction_guard import GuardError, load, req_digest

class DockerManBindingError(RuntimeError): pass

def observe_stock_update(guard_path: Path, binding: str,
                         inspect_digest: Callable[[], str],
                         probes: list[CoreProbe],
                         restore_predecessor: Callable[[str], None],
                         verify_recovery: Callable[[str], bool]) -> dict:
    """Bind a stock DockerMan update to an already-armed exact guard.

    Docker inspect/readback is authority. DockerMan update-status/cache is
    deliberately not an input.
    """
    g=load(guard_path)
    if g['binding_digest'] != binding:
        raise DockerManBindingError('stale transaction binding')
    if g['state'] in ('committed','recovered'):
        return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)
    try:
        running=req_digest(inspect_digest(),'running image')
    except (GuardError,Exception) as exc:
        raise DockerManBindingError('authoritative container inspect unavailable') from exc
    if running != g['candidate_digest']:
        raise DockerManBindingError('running digest does not match armed candidate')
    return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)
