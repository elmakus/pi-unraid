// Frozen, opt-in candidate-only observation; never observe ordinary agents.
import fs from 'node:fs';
export default function (ctx) {
  const witness = process.env.M07_T05_WITNESS_FILE;
  const testId = process.env.M07_T05_TEST_ID;
  if (!witness || !testId || !witness.startsWith('/') || !/^[A-Za-z0-9_.-]{1,64}$/.test(testId)) return;
  function emit(obj) {
    const allow = { test_id: String(testId).slice(0,64) };
    for (const k of ['model','effort','status','kind']) {
      if (obj[k] !== undefined) allow[k] = String(obj[k]).slice(0,128);
    }
    try { fs.appendFileSync(witness, JSON.stringify(allow)+'\n', {mode: 0o600}); } catch {}
  }
  ctx.on('before_provider_request', (ev) => {
    try {
      const p = ev.payload || {};
      const r = p.reasoning || {};
      emit({kind:'request', model: p.model, effort: (r.effort || p.reasoningEffort)});
    } catch {}
    return ev.payload;
  });
  ctx.on('after_provider_response', (ev) => {
    try { emit({kind:'response', status: ev.status}); } catch {}
  });
  ctx.on('turn_end', (ev) => {
    try { emit({kind:'terminal', status: (ev && ev.outcome) || 'unknown'}); } catch {}
  });
  ctx.on('agent_end', (ev) => {
    try {
      let neg = false;
      const msgs = (ev && ev.messages) || [];
      for (const m of msgs) {
        if (m && (m.stopReason === 'aborted' || m.stopReason === 'error')) { neg = true; break; }
      }
      emit({kind:'terminal', status: neg ? 'aborted' : 'ended'});
    } catch {}
  });
  ctx.on('agent_settled', (ev) => {
    try { emit({kind:'terminal', status:'settled'}); } catch {}
  });
}
