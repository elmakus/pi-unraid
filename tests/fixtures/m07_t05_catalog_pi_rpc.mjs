// Separate external Pi RPC fake: metadata only, every effect command rejected.
// Reads public official model data; does not resolve auth or call a provider.
import fs from 'node:fs';
import readline from 'node:readline';
import {pathToFileURL} from 'node:url';
const {metaProvider} = await import(pathToFileURL(`${process.env.PUD_SYNTHETIC_PI_ROOT}/node_modules/@earendil-works/pi-ai/dist/providers/meta.js`).href);
const models = metaProvider().getModels();
const {clampThinkingLevel} = await import(pathToFileURL(`${process.env.PUD_SYNTHETIC_PI_ROOT}/node_modules/@earendil-works/pi-ai/dist/models.js`).href);
const model = models.find(m=>m.id==='muse-spark-1.3-contributor');
const thinkingIndex = process.argv.indexOf('--thinking');
const requested = thinkingIndex < 0 ? 'off' : process.argv[thinkingIndex+1];
// Fake only the external RPC frame. The effective-level calculation is the
// unmodified official Pi function, never a hand-authored xhigh response.
const state = {sessionId:`synthetic-pi-${process.pid}`, model,
  thinkingLevel:clampThinkingLevel(model,requested), isStreaming:false};
fs.appendFileSync(process.env.PUD_SYNTHETIC_RPC_TRACE,
  JSON.stringify({kind:'spawn', pid:process.pid, ppid:process.ppid,
    argv:process.argv.slice(2), syntheticAuthInherited:process.env.META_API_KEY==='synthetic-disposable-credential'})+'\n');
for await (const line of readline.createInterface({input:process.stdin})) {
  const req = JSON.parse(line);
  fs.appendFileSync(process.env.PUD_SYNTHETIC_RPC_TRACE, JSON.stringify({kind:'rpc', type:req.type, id:req.id})+'\n');
  const success = ['get_available_models','get_state'].includes(req.type);
  process.stdout.write(JSON.stringify({type:'response', command:req.type, id:req.id, success,
    ...(success ? {data:req.type==='get_available_models' ? {models} : state}
      : {error:'synthetic fake forbids all non-metadata commands'})})+'\n');
}
