// Frozen, opt-in candidate-only observation; never observe ordinary agents.
import fs from 'node:fs';
export default function (api) {
  const witness = process.env.M07_T05_WITNESS_FILE;
  const testId = process.env.M07_T05_TEST_ID;
  if (!witness || !testId || !witness.startsWith('/') || !/^[A-Za-z0-9_.-]{1,64}$/.test(testId)) return;
  function emit(obj) {
    const row = { test_id: testId };
    const levels = ['off','minimal','low','medium','high','xhigh','max'];
    if (obj.provider !== undefined) row.provider = ['meta','codex-lb'].includes(obj.provider) ? obj.provider : 'other';
    if (obj.thinking !== undefined) row.thinking = levels.includes(obj.thinking) ? obj.thinking : 'unknown';
    if (obj.model !== undefined) row.model = obj.model === 'muse-spark-1.3-contributor' ? obj.model : 'unexpected-model';
    if (obj.effort !== undefined) row.effort = levels.includes(obj.effort) ? obj.effort : 'unknown';
    if (obj.status !== undefined) {
      const status = String(obj.status);
      row.status = /^(?:[1-5][0-9]{2}|completed|aborted|error|unknown|ended|settled)$/.test(status) ? status : 'invalid';
    }
    row.kind = obj.kind;
    // Never follow a candidate-local symlink or append to a non-private file.
    const fd = fs.openSync(witness, fs.constants.O_WRONLY | fs.constants.O_APPEND
      | fs.constants.O_CREAT | fs.constants.O_NOFOLLOW, 0o600);
    try {
      const st = fs.fstatSync(fd);
      if (!st.isFile() || (st.mode & 0o777) !== 0o600
          || (process.getuid && st.uid !== process.getuid()) || st.size > 65536) {
        throw new Error('candidate observation file is not private');
      }
      fs.writeSync(fd, JSON.stringify(row)+'\n');
    } finally { fs.closeSync(fd); }
  }
  function stop(ctx) {
    // Supported abort is preferred. If context/abort is missing, stale, broken
    // or cannot prove a synchronously aborted signal, terminate ONLY this
    // explicitly opted-in test Pi process. An exception caught by the runner
    // must never allow transport to continue. Host outcome stays unsatisfied.
    try {
      ctx?.abort?.();
      if (ctx?.signal?.aborted === true) return;
    } catch {}
    process.exit(42);
  }
  api.on('before_provider_request', (ev, ctx) => {
    let valid = false;
    try {
      const p = ev?.payload || {};
      const effort = p.reasoning?.effort ?? p.reasoningEffort;
      // Actual supported context, never policy or an inferred model prefix.
      const provider = ctx?.model?.provider;
      const thinking = ctx?.thinkingLevel;
      valid = provider === 'meta' && ctx?.model?.id === 'muse-spark-1.3-contributor'
        && p.model === ctx.model.id && thinking === 'max' && effort === 'max'
        && ctx.signal && !ctx.signal.aborted && typeof ctx.abort === 'function';
      emit({kind:'request', provider: provider ?? 'unknown', thinking: thinking ?? 'unknown',
        model: p.model ?? 'unknown', effort: effort ?? 'unknown'});
    } catch {
      stop(ctx);
      throw new Error('candidate observation unavailable; run aborted');
    }
    if (!valid) {
      stop(ctx);
      // Pinned OpenAI SDK checks the supported aborted signal before fetch;
      // the unqualified-context branch above never returns to that SDK.
      throw new Error('candidate effective profile mismatch; run aborted');
    }
    return ev.payload;
  });
  api.on('after_provider_response', (ev) => {
    emit({kind:'response', status: ev.status});
  });
  api.on('turn_end', (ev) => {
    emit({kind:'terminal', status: (ev && ev.outcome) || 'unknown'});
  });
  api.on('agent_end', (ev) => {
    const msgs = (ev && ev.messages) || [];
    const negative = msgs.some(m => m && (m.stopReason === 'aborted' || m.stopReason === 'error'));
    emit({kind:'terminal', status: negative ? 'aborted' : 'ended'});
  });
  api.on('agent_settled', () => {
    emit({kind:'terminal', status:'settled'});
  });
}
