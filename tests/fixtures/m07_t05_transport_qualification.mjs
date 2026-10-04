// Synthetic ONLY. Actual pinned Pi Agent/ExtensionRunner/provider SDK; fetch
// is replaced in every request by an in-memory transport. No auth registry,
// credential files, real daemon, DNS, sockets or actual inference is used.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const [piRoot, observerPath, scenario] = process.argv.slice(2);
const load = p => import(pathToFileURL(`${piRoot}/${p}`).href);
const {Agent} = await load('node_modules/@earendil-works/pi-agent-core/dist/agent.js');
const {ExtensionRunner} = await load('dist/core/extensions/runner.js');
const {streamSimple} = await load('node_modules/@earendil-works/pi-ai/dist/api/openai-responses.js');
const {metaProvider} = await load('node_modules/@earendil-works/pi-ai/dist/providers/meta.js');
const {getSupportedThinkingLevels, clampThinkingLevel} = await load('node_modules/@earendil-works/pi-ai/dist/models.js');
assert.equal(JSON.parse(fs.readFileSync(`${piRoot}/package.json`)).version, '0.87.1');
const model = metaProvider().getModels().find(m => m.id === 'muse-spark-1.3-contributor');
assert(model && model.provider === 'meta');
assert.equal(model.thinkingLevelMap.max, null);
assert(!getSupportedThinkingLevels(model).includes('max'));
assert.equal(clampThinkingLevel(model, 'max'), 'xhigh');
if (scenario === 'unprivate-witness') fs.writeFileSync(process.env.M07_T05_WITNESS_FILE,'',{mode:0o644});
if (scenario === 'symlink-witness') {
  fs.writeFileSync(`${process.env.M07_T05_WITNESS_FILE}.target`,'synthetic unchanged target',{mode:0o600});
  fs.symlinkSync(`${process.env.M07_T05_WITNESS_FILE}.target`,process.env.M07_T05_WITNESS_FILE);
}
let fetches = 0;
const handlers = new Map();
const extension = {path: observerPath, handlers};
const observer = await import(pathToFileURL(observerPath).href);
observer.default({on: (name, fn) => handlers.set(name, [fn])});
if (scenario === 'throw-only-control') {
  handlers.set('before_provider_request', [() => {throw new Error('synthetic rejection without abort');}]);
}
const runtime = {pendingProviderRegistrations:[], pendingNativeProviderRegistrations:[]};
const runner = new ExtensionRunner([extension], runtime, process.cwd(), {}, {});
let agent;
let caughtErrors = 0;
runner.onError(() => caughtErrors++);
let wireEffort;
agent = new Agent({initialState: {model, thinkingLevel:'max', tools:[], messages:[]},
  streamFn: (selected, context, options) => streamSimple(selected, context, {
    ...options,
    apiKey: 'synthetic-disposable-credential',
    maxRetries: 0,
    fetch: async () => {
      fetches++;
      fs.writeFileSync(process.env.PUD_SYNTHETIC_FETCH_MARKER,'synthetic transport entered');
      return new Response(JSON.stringify({error:{message:'synthetic external transport response'}}),
        {status:400, headers:{'content-type':'application/json'}});
    },
  }),
  onPayload: async payload => {
    wireEffort = payload.reasoning?.effort;
    return runner.emitBeforeProviderRequest(payload);
  },
});
runner.bindCore({getThinkingLevel:()=>agent.state.thinkingLevel}, {
  getModel:()=>agent.state.model,
  getSignal:()=>scenario==='missing-signal' ? undefined : agent.signal,
  abort:()=>{if (scenario!=='broken-abort') agent.abort();}, isIdle:()=>!agent.state.isStreaming,
});
await agent.prompt('synthetic transport qualification only');
assert.equal(wireEffort, 'xhigh');
assert(caughtErrors > 0, 'actual ExtensionRunner must catch the rejection');
if (scenario === 'throw-only-control') {
  assert.equal(fetches, 1, 'throwing alone must demonstrate reachable fake transport');
} else {
  assert.equal(fetches, 0, 'supported abort must prevent even fake transport');
  if (scenario === 'unprivate-witness') {
    assert.equal(fs.readFileSync(process.env.M07_T05_WITNESS_FILE,'utf8'),'');
  } else if (scenario === 'symlink-witness') {
    assert.equal(fs.readFileSync(`${process.env.M07_T05_WITNESS_FILE}.target`,'utf8'),'synthetic unchanged target');
  } else {
    const rows = fs.readFileSync(process.env.M07_T05_WITNESS_FILE, 'utf8').trim().split('\n').map(JSON.parse);
    assert.equal(rows.length, 1);
    assert.equal(rows[0].provider, 'meta');
    assert.equal(rows[0].thinking, 'max');
    assert.equal(rows[0].effort, 'xhigh');
  }
}
console.log(JSON.stringify({scenario, fetches, caughtErrors, wireEffort,
  fixedMaxSupported:false, classification:'synthetic; not real validation'}));
