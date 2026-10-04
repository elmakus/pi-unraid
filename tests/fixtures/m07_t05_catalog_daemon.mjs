// Separate isolated synthetic daemon process. The ACTUAL official Paseo
// provider client selects/spawns the external fake Pi via its supported
// replace-command setting; no injected runtime or reconstructed catalog.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const [serverRoot, fakePiPath] = process.argv.slice(2);
const {PiRpcAgentClient} = await import(pathToFileURL(`${serverRoot}/dist/server/server/agent/providers/pi/agent.js`).href);
assert.equal(JSON.parse(fs.readFileSync(`${serverRoot}/package.json`)).version, '0.9.2');
const logger = {debug:()=>{}, warn:()=>{}, info:()=>{}, error:()=>{}, child(){return this;}};
const client = new PiRpcAgentClient({logger, runtimeSettings:{
  command:{mode:'replace', argv:[process.execPath, fakePiPath]},
  env:{PUD_SYNTHETIC_RPC_TRACE:process.env.PUD_SYNTHETIC_RPC_TRACE,
    PUD_SYNTHETIC_PI_ROOT:process.env.PUD_SYNTHETIC_PI_ROOT},
}, providerParams:{rpcTimeoutMs:5000}});
const catalog = await client.fetchCatalog({scope:'global'});
const fixed = catalog.models.find(m => m.id==='meta/muse-spark-1.3-contributor');
assert(fixed);
const options = fixed.thinkingOptions.map(o=>o.id);
assert(!options.includes('max'));
assert(options.includes('xhigh'));
const config = {provider:'pi', cwd:process.cwd(), model:fixed.id, thinkingOptionId:'max', internal:true};
const session = await client.createSession(config);
let info;
try {
  info = await session.getRuntimeInfo();
  assert.equal(info.thinkingOptionId,'xhigh');
  assert.equal(info.model, fixed.id);
  assert.equal(config.thinkingOptionId,'xhigh');
} finally { await session.close(); }
const trace = fs.readFileSync(process.env.PUD_SYNTHETIC_RPC_TRACE,'utf8').trim().split('\n').map(JSON.parse);
assert.equal(trace.filter(r=>r.kind==='spawn').length,2);
assert.equal(trace[0].ppid,process.pid);
assert.notEqual(trace[0].pid,process.pid);
assert.equal(trace[0].syntheticAuthInherited,true);
assert.deepEqual(trace[0].argv,['--mode','rpc']);
assert.deepEqual(trace.filter(r=>r.kind==='rpc').map(r=>r.type),['get_available_models','get_state','get_state']);
const selectedSession = trace.filter(r=>r.kind==='spawn')[1];
assert.equal(selectedSession.ppid,process.pid);
assert.notEqual(selectedSession.pid,trace[0].pid);
assert.equal(selectedSession.syntheticAuthInherited,true);
assert.equal(selectedSession.argv[selectedSession.argv.indexOf('--model')+1],fixed.id);
assert.equal(selectedSession.argv[selectedSession.argv.indexOf('--thinking')+1],'max');
console.log(JSON.stringify({daemonPid:process.pid, selectedPiPid:trace[0].pid,
  fixedModel:fixed.id, options, fixedMaxSupported:false, effectiveSessionThinking:info.thinkingOptionId,
  classification:'synthetic source qualification; not candidate validation'}));
