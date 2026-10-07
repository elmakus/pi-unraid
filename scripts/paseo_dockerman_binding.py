#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from time import sleep
from typing import Callable
from scripts.paseo_immediate_acceptance import CoreProbe, run_transaction
from scripts.paseo_transaction_guard import GuardError, load, req_digest

class DockerManBindingError(RuntimeError): pass

def observe_stock_update(guard_path: Path, binding: str,
                         inspect_digest: Callable[[], str],
                         probes: list[CoreProbe],
                         restore_predecessor: Callable[[str], None],
                         verify_recovery: Callable[[str], bool]) -> dict:
    """Accept only an authoritative observation of the armed candidate."""
    g=load(guard_path)
    if g['binding_digest'] != binding:
        raise DockerManBindingError('stale transaction binding')
    if g['state'] in ('committed','recovered'):
        return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)
    try:
        running=req_digest(inspect_digest(),'running image')
    except Exception as exc:
        raise DockerManBindingError('authoritative container inspect unavailable') from exc
    if running != g['candidate_digest']:
        raise DockerManBindingError('running digest does not match armed candidate')
    return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)

def wait_for_stock_update(guard_path: Path, binding: str,
                          inspect_digest: Callable[[], str],
                          probes: list[CoreProbe],
                          restore_predecessor: Callable[[str], None],
                          verify_recovery: Callable[[str], bool],
                          *, attempts: int = 120, interval: float = 1.0,
                          sleeper: Callable[[float], None] = sleep) -> dict:
    """Pre-startable/restartable observer for DockerMan's stop/remove/create window.

    Start this before the operator invokes stock Update. Missing-container reads and
    the exact predecessor are transient. Any third digest is ambiguous and fails
    closed. Restarting this observer is safe because the durable guard is authority.
    """
    if attempts < 1:
        raise ValueError('attempts must be positive')
    for n in range(attempts):
        g=load(guard_path)
        if g['binding_digest'] != binding:
            raise DockerManBindingError('stale transaction binding')
        if g['state'] in ('committed','recovered'):
            return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)
        try:
            running=req_digest(inspect_digest(),'running image')
        except Exception:
            running=None
        if running == g['candidate_digest']:
            return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)
        if running not in (None,g['previous_digest']):
            raise DockerManBindingError('ambiguous running digest during stock update')
        if n + 1 < attempts:
            sleeper(interval)
    raise DockerManBindingError('candidate not observed before binding timeout')


def update_and_verify(guard_path: Path, binding: str,
                      trigger_update: Callable[[], None],
                      inspect_digest: Callable[[], str],
                      probes: list[CoreProbe],
                      restore_predecessor: Callable[[str], None],
                      verify_recovery: Callable[[str], bool],
                      *, attempts: int = 120, interval: float = 1.0,
                      sleeper: Callable[[float], None] = sleep) -> dict:
    """Single Update + Verify fallback action with crash-safe trigger intent.

    The action owns both sides of the lifecycle: validate the durable
    armed guard, persist a narrow guard-local trigger intent, trigger
    the update only after that validation, then remain attached to the
    restartable observer until immediate acceptance reaches a terminal
    result. A restart that finds a durable intent for the same binding
    never reissues the trigger: it reads back the uncertain occurrence
    and observes instead. Interruption before the intent leaves no
    record (safe to trigger); interruption after the intent observes
    only. No universal action ledger is introduced.
    """
    from scripts.paseo_trigger_intent import TriggerIntentError, readback, record as record_intent
    g=load(guard_path)
    if g['binding_digest'] != binding:
        raise DockerManBindingError('stale transaction binding')
    if g['state'] != 'armed':
        # A committed/recovered guard that restarts here must not
        # re-trigger: delegate to the terminal-state readback so
        # post-GREEN rollback stays denied and RED stays recovered.
        if g['state'] in ('committed','recovered'):
            return run_transaction(guard_path,binding,probes,restore_predecessor,verify_recovery)
        raise DockerManBindingError('Update + Verify requires an armed guard')
    try:
        existing = readback(guard_path, binding)
    except TriggerIntentError as exc:
        raise DockerManBindingError(f'uncertain trigger occurrence; observe, never reissue: {exc}') from exc
    if existing is None:
        try:
            record_intent(guard_path, binding)
        except TriggerIntentError as exc:
            raise DockerManBindingError(f'uncertain trigger occurrence; observe, never reissue: {exc}') from exc
        try:
            trigger_update()
        except Exception:
            # The intent is durable: trigger occurrence is now uncertain.
            # The caller restarts into the observer below instead of
            # blindly reissuing a second update.
            return wait_for_stock_update(
                guard_path,binding,inspect_digest,probes,restore_predecessor,verify_recovery,
                attempts=attempts,interval=interval,sleeper=sleeper)
    # Intent exists (this attempt or a pre-restart attempt): never
    # re-trigger an uncertain update; observe the authoritative state.
    return wait_for_stock_update(
        guard_path,binding,inspect_digest,probes,restore_predecessor,verify_recovery,
        attempts=attempts,interval=interval,sleeper=sleeper)
