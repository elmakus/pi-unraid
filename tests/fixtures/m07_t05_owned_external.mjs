// External-only synthetic CLI / daemon / Pi. No provider or auth resolver import.
import fs from 'node:fs';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import readline from 'node:readline';
import {buildPiLaunch} from '/usr/local/lib/node_modules/@getpaseo/server/dist/server/server/agent/providers/pi/runtime.js';
import {PersistedConfigSchema} from '/usr/local/lib/node_modules/@getpaseo/server/dist/server/server/persisted-config.js';
const home = process.env.HOME;
const statusFile = `${home}/.paseo/fake-status.json`;
const faultFile = `${home}/fake-fault.json`;
const fault = fs.existsSync(faultFile) ? JSON.parse(fs.readFileSync(faultFile)) : {};
const fixed = 'meta/muse-spark-1.3-contributor';
function record(method, facts={}) { fs.appendFileSync(`${home}/fake-calls.jsonl`, JSON.stringify({method,pid:process.pid,...facts})+'\n'); }
export async function connectToDaemon() {
  const status = JSON.parse(fs.readFileSync(statusFile));
  const socket = net.createConnection(status.port, '127.0.0.1');
  await new Promise((yes,no)=>{socket.once('connect',yes);socket.once('error',no);});
  let next=0; const pending=new Map();
  readline.createInterface({input:socket}).on('line', line=>{
    const row=JSON.parse(line), p=pending.get(row.id); pending.delete(row.id);
    row.error ? p.reject(new Error('synthetic transport failure')) : p.resolve(row.value);
  });
  socket.on('close',()=>{for(const p of pending.values())p.reject(new Error('synthetic closed'));pending.clear();});
  const call=(method,arg)=>new Promise((resolve,reject)=>{const id=++next;pending.set(id,{resolve,reject});socket.write(JSON.stringify({id,method,arg})+'\n');});
  return {getLastServerInfoMessage:()=>({serverId:fault.wrong_server?'other':status.serverId,version:'0.9.2',
      features:{creationLifecycle:!fault.unsupported_creation}}),
    createWorkspace:arg=>call('workspace',arg),createAgent:arg=>call('create',arg),fetchAgent:arg=>call('inspect',arg),
    sendMessage:(agent,text)=>call('prompt',{agent,text}),waitForFinish:agent=>call('wait',{agent}),
    close:async()=>socket.destroy()};
}
async function daemon() {
  const config=PersistedConfigSchema.parse(JSON.parse(fs.readFileSync(`${home}/.paseo/config.json`)));
  const agents=new Map(); let workspace;
  async function pi(session, agentId) {
    const launch=buildPiLaunch({command:['/disallowed/default/pi'],runtimeSettings:{command:{mode:'replace',argv:config.agents.providers.pi.command}},session});
    record('selected-process');
    const env={...process.env,...launch.env};
    if(agentId)env.PASEO_AGENT_ID=fault.wrong_agent_env?'other':agentId;
    if(agentId && fault.auth)delete env.META_API_KEY;
    if(agentId && fault.selector)env.PASEO_WORKSPACE_ID='foreign';
    const child=spawn(launch.argv[0],launch.argv.slice(1),{cwd:launch.cwd,env,stdio:['pipe','pipe','ignore']});
    const pending=new Map(); let n=0;
    readline.createInterface({input:child.stdout}).on('line',line=>{const row=JSON.parse(line);const p=pending.get(row.id);if(p){pending.delete(row.id);p.resolve(row.data);}});
    child.once('exit',()=>{for(const p of pending.values())p.reject(new Error('synthetic Pi closed'));pending.clear();});
    return {child,call:(type)=>new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});child.stdin.write(JSON.stringify({id,type})+'\n');})};
  }
  async function snapshot(a) {
    const state=await a.rpc.call('get_state');
    return {id:fault.wrong_agent?'other':a.id,workspaceId:fault.workspace?'other':workspace.id,
      cwd: a.cwd,provider:'pi',model:state.model.provider+'/'+state.model.id,
      runtimeInfo:{model:state.model.provider+'/'+state.model.id},effectiveThinkingOptionId:state.thinkingLevel,status:'idle',labels:{}};
  }
  const server=net.createServer(socket=>{
    readline.createInterface({input:socket}).on('line',async line=>{
      const row=JSON.parse(line);record(row.method);
      try {
        let value;
        if(row.method==='catalog') {
          const rpc=await pi({cwd:home,model:fixed,thinkingOptionId:'max'},null);
          value=await rpc.call('get_available_models');rpc.child.kill();
        } else if(row.method==='workspace') {
          workspace={id:row.arg.workspaceId,workspaceDirectory:row.arg.source.path};
          if(fault.workspace_uncertain)throw new Error();value={workspace};
        } else if(row.method==='create') {
          record('create-env', {names:Object.keys(row.arg.env??{}).sort(),
            initial_prompt:Boolean(row.arg.initialPrompt),agent_id:row.arg.agentId,workspace_id:row.arg.workspaceId});
          if(row.arg.initialPrompt)throw new Error('creation must be non-inference');
          const id=row.arg.agentId;
          if(fault.process_collision) {
            const file=`${home}/.m07-t05/processes/${id}.json`;
            fs.writeFileSync(file,'private unrelated acquisition',{mode:0o600,flag:'wx'});
          }
          const rpc=await pi({cwd:row.arg.cwd,model:row.arg.model,thinkingOptionId:row.arg.thinkingOptionId,env:row.arg.env},id);
          const agent={id,rpc,cwd:row.arg.cwd}; agents.set(id,agent);
          await rpc.call('get_state');
          if(fault.config_replacement) {
            const file=`${home}/.paseo/config.json`;fs.renameSync(file,`${file}.old`);
            fs.copyFileSync(`${file}.old`,file);fs.chmodSync(file,0o600);
          }
          if(fault.reference_replacement) {
            const file=`${home}/.m07-t05/owned.json`;fs.renameSync(file,`${file}.old`);
            fs.copyFileSync(`${file}.old`,file);fs.chmodSync(file,0o600);
          }
          if(fault.wrong_pi_bytes || fault.extra_proof) {
            const file=`${home}/.m07-t05/processes/${id}.json`;
            const proof=JSON.parse(fs.readFileSync(file));
            if(fault.wrong_pi_bytes)proof.sha256='sha256:'+('0'.repeat(64));
            if(fault.extra_proof)proof.untrusted='synthetic-sensitive-never-emit';
            fs.writeFileSync(file,JSON.stringify(proof));
          }
          if(fault.create_pending)return; // No response: async occurrence remains uncertain.
          if(fault.create_uncertain)throw new Error();value=await snapshot(agent);
        } else if(row.method==='inspect') {
          if(fault.inspection)throw new Error();value={agent:await snapshot(agents.get(row.arg.agentId))};
        } else if(row.method==='prompt') {
          if(fault.prompt_uncertain)throw new Error();
          if(fault.binding_replacement) {
            const file=`${home}/.m07-t05/binding.json`;fs.renameSync(file,`${file}.old`);
            fs.copyFileSync(`${file}.old`,file);fs.chmodSync(file,0o600);
          }
          value=await agents.get(row.arg.agent).rpc.call('prompt');
        } else if(row.method==='wait') {
          value={status:fault.completion?'timeout':'idle',final:await snapshot(agents.get(row.arg.agent))};
        } else throw new Error();
        socket.write(JSON.stringify({id:row.id,value})+'\n');
      } catch {socket.write(JSON.stringify({id:row.id,error:true})+'\n');}
    });
  });
  server.listen(0,'127.0.0.1',()=>{
    fs.writeFileSync(statusFile,JSON.stringify({port:server.address().port,pid:process.pid,serverId:crypto.randomUUID()}));
  });
  process.on('SIGTERM',()=>{for(const a of agents.values())a.rpc.child.kill();server.close(()=>process.exit());});
}
export async function runFakePi() {
  const handlers={};
  const observer=await import(pathToFileURL(`${home}/.pi/agent/extensions/m07-t05-witness.js`));
  observer.default({on:(name,handler)=>handlers[name]=handler});
  const model={provider:fault.profile?'codex-lb':'meta',id:'muse-spark-1.3-contributor'};
  const thinking=fault.thinking?'xhigh':'max';
  readline.createInterface({input:process.stdin}).on('line',async line=>{
    const row=JSON.parse(line); record('pi:'+row.type);let data;
    if(row.type==='get_state')data={model,thinkingLevel:thinking};
    else if(row.type==='get_available_models')data=[{id:fixed,thinkingOptionIds:['max']}];
    else if(row.type==='prompt') {
      const controller=new AbortController();
      const ctx={model:fault.request_profile?{...model,provider:'codex-lb'}:model,
        thinkingLevel:thinking,signal:controller.signal,abort:()=>controller.abort()};
      if(!fault.omit_witness) {
        try {await handlers.before_provider_request({payload:{model:model.id,reasoning:{effort:fault.effort??'max'}}},ctx);}catch{}
        if(!controller.signal.aborted) {
          record('fake-transport');handlers.after_provider_response({status:fault.response??200});
          handlers.turn_end({outcome:fault.turn??'completed'});handlers.agent_end({messages:[]});
          if(!fault.omit_settled)handlers.agent_settled();
        }
      }
      data={};
    } else process.exit(42);
    console.log(JSON.stringify({id:row.id,data}));
  });
}
async function cli() {
  const args=process.argv.slice(3);
  if(args[0]==='daemon'&&args[1]==='start') {
    const child=spawn(process.execPath,[process.argv[1],'daemon'],{detached:true,env:process.env,stdio:'ignore'});child.unref();
    for(let i=0;i<200&&!fs.existsSync(statusFile);i++)await new Promise(r=>setTimeout(r,10));
    const status=JSON.parse(fs.readFileSync(statusFile));
    console.log(JSON.stringify({action:'started',home:`${home}/.paseo`,pid:status.pid,listen:`127.0.0.1:${status.port}`}));
  } else if(args[0]==='status') {
    const status=JSON.parse(fs.readFileSync(statusFile));
    console.log(JSON.stringify({home:`${home}/.paseo`,pid:status.pid,workerPid:fault.process?status.pid+1:status.pid,
      listen:`127.0.0.1:${status.port}`,daemonVersion:'0.9.2',localDaemon:'running',connectedDaemon:'reachable',
      serverId:status.serverId,daemonNode:process.execPath,providers:[{provider:'pi',available:true}]}));
  } else if(args[0]==='provider') {
    const client=await connectToDaemon();
    // Catalog uses the same server-selected wrapper and separate metadata Pi.
    const status=JSON.parse(fs.readFileSync(statusFile));
    const socket=net.createConnection(status.port,'127.0.0.1');
    socket.on('connect',()=>socket.write(JSON.stringify({id:1,method:'catalog'})+'\n'));
    readline.createInterface({input:socket}).once('line',line=>{console.log(JSON.stringify(JSON.parse(line).value));socket.destroy();client.close();});
  } else process.exit(42);
}
if(process.argv[2]==='daemon')await daemon();
else if(process.argv[2]==='pi')await runFakePi();
else if(process.argv[2]==='cli')await cli();
