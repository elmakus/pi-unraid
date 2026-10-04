#!/usr/bin/env node
// Supported Paseo client APIs, private candidate only. No provider/auth API.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

function requireFact(ok) { if (!ok) throw new Error('candidate runtime binding rejected'); }
function privateJSON(file) {
  const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    const st = fs.fstatSync(fd);
    requireFact(st.isFile() && (st.mode & 0o777) === 0o600 && st.uid === process.getuid() && st.size <= 65536);
    return JSON.parse(fs.readFileSync(fd, 'utf8'));
  } finally { fs.closeSync(fd); }
}
function identity(file) {
  const st = fs.lstatSync(file, {bigint: true});
  requireFact(st.isFile() && !st.isSymbolicLink() && (st.mode & 0o777n) === 0o600n && st.uid === BigInt(process.getuid()));
  return `${st.dev}:${st.ino}`;
}
function recorder(file, initial) {
  // Creation must not replace an old attempt's usable references.
  const fd = fs.openSync(file, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o600);
  fs.writeFileSync(fd, JSON.stringify(initial)); fs.fsyncSync(fd); fs.closeSync(fd);
  let owned = identity(file);
  return (doc) => {
    requireFact(identity(file) === owned);
    const temporary = `${file}.next`;
    const next = fs.openSync(temporary, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o600);
    try { fs.writeFileSync(next, JSON.stringify(doc)); fs.fsyncSync(next); } finally { fs.closeSync(next); }
    requireFact(identity(file) === owned);
    fs.renameSync(temporary, file); owned = identity(file);
    const directory = fs.openSync(path.dirname(file), fs.constants.O_RDONLY);
    try { fs.fsyncSync(directory); } finally { fs.closeSync(directory); }
  };
}
const usableID = (v) => typeof v === 'string' && /^[A-Za-z0-9_.-]{1,128}$/.test(v);

// Only the transport/client is an injectable external boundary for fixtures.
// Production main always imports the frozen pinned CLI client at the fixed path.
export async function runOwnedTest(config, connect) {
  const fixed = 'meta/muse-spark-1.3-contributor';
  const safeDaemon = Object.fromEntries(['home','endpoint','pid','version','worker_pid','server_id','node']
    .map(key => [key, config.daemon?.[key]]));
  let state = {schema_version: 1, test_id: config.test_id, daemon: safeDaemon,
    workspace_id: null, agent_id: null,
    requested_workspace_id: crypto.randomUUID(), requested_agent_id: crypto.randomUUID(),
    workspace_request_id: crypto.randomUUID(), agent_request_id: crypto.randomUUID(),
    message_id: crypto.randomUUID(), dispatch: 'not_started', replay: false};
  let client, persist, effect = false;
  const deadline = Date.now() + 110000;
  async function bounded(operation, maximum = 10000) {
    const remaining = Math.min(maximum, deadline - Date.now());
    requireFact(remaining > 0);
    let timer;
    try {
      return await Promise.race([operation, new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('candidate observation timeout')), remaining);
      })]);
    } finally { clearTimeout(timer); }
  }
  try {
    requireFact(usableID(config.test_id) && config.daemon.home === '/home/paseo/.paseo'
      && config.cwd === '/tmp' && config.pi.path === '/usr/local/bin/pi'
      && config.guard === '/home/paseo/.pi/agent/bin/run-llm-test.sh'
      && config.reference === '/home/paseo/.m07-t05/owned.json'
      && config.binding === '/home/paseo/.m07-t05/binding.json'
      && config.process_dir === '/home/paseo/.m07-t05/processes'
      && config.witness === '/tmp/m07-t05-witness.jsonl'
      && Object.keys(config.daemon).sort().join(',') === Object.keys(safeDaemon).sort().join(','));
    requireFact(JSON.stringify(config.daemon_config?.agents?.providers?.pi?.command)
      === JSON.stringify(['/home/paseo/.pi/agent/bin/m07-t05-pi-owned.py'])
      && Object.keys(config.daemon_config.agents.providers).join(',') === 'pi'
      && Object.keys(config.daemon_config.agents.providers.pi).join(',') === 'command'
      && config.daemon_config.pluginsEnabled === false
      && config.daemon_config.daemon?.relay?.enabled === false
      && config.daemon_config.daemon?.mcp?.enabled === false
      && config.daemon_config.daemon?.mcp?.injectIntoAgents === false
      && config.daemon_config.daemon?.browserTools?.enabled === false);
    const daemonConfig = path.join(config.daemon.home, 'config.json');
    const daemonConfigIdentity = identity(daemonConfig);
    function configuration() {
      requireFact(identity(daemonConfig) === daemonConfigIdentity
        && JSON.stringify(privateJSON(daemonConfig)) === JSON.stringify(config.daemon_config));
    }
    configuration();
    const guard = spawnSync('bash', [config.guard, '--native-create-agent-args'], {
      env: {PATH: '/usr/local/bin:/usr/bin:/bin', HOME: '/home/paseo'}, encoding: 'utf8', timeout: 10000});
    requireFact(guard.status === 0);
    const shape = JSON.parse(guard.stdout);
    requireFact(shape.provider === `pi/${fixed}` && shape.settings?.thinkingOptionId === 'max'
      && shape.notifyOnFinish === true && Object.keys(shape.settings).length === 1);
    persist = recorder(config.reference, state);
    client = await bounded(connect({target: {kind: 'instance', home: config.daemon.home}, timeout: 10000}));
    function server() {
      configuration();
      const info = client.getLastServerInfoMessage();
      requireFact(info?.serverId === config.daemon.server_id && info?.version === config.daemon.version
        && info?.features?.creationLifecycle === true);
    }
    server();
    state.dispatch = 'workspace_create_pending'; persist(state); effect = true;
    const createdWorkspace = await bounded(client.createWorkspace({source: {kind: 'directory', path: config.cwd},
      title: `LLM-TEST:${config.test_id}`, workspaceId: state.requested_workspace_id,
      requestId: state.workspace_request_id, idempotencyKey: `m07t05-workspace:${config.test_id}`}));
    requireFact(createdWorkspace.workspace?.id === state.requested_workspace_id);
    state.workspace_id = createdWorkspace.workspace.id; state.dispatch = 'workspace_created'; persist(state);
    requireFact(createdWorkspace.workspace.workspaceDirectory === config.cwd);
    server();
    state.dispatch = 'agent_create_pending'; persist(state);
    const agent = await bounded(client.createAgent({provider: 'pi', model: fixed,
      agentId: state.requested_agent_id, requestId: state.agent_request_id,
      idempotencyKey: `m07t05-agent:${config.test_id}`,
      thinkingOptionId: shape.settings.thinkingOptionId, cwd: config.cwd,
      workspaceId: state.workspace_id, title: `LLM-TEST:${config.test_id}`,
      env: {M07_T05_TEST_ID: config.test_id, M07_T05_WITNESS_FILE: config.witness,
        M07_T05_RUNTIME_BINDING: config.binding, M07_T05_PROCESS_DIR: config.process_dir,
        META_API_KEY_FILE: '/run/secrets/pi-unraid-meta'}}));
    // NO initialPrompt: actual IDs and effective process readback precede send.
    requireFact(agent.id === state.requested_agent_id); state.agent_id = agent.id; state.dispatch = 'agent_created'; persist(state);
    async function inspect() {
      server();
      const read = await bounded(client.fetchAgent({agentId: state.agent_id}));
      const a = read?.agent;
      requireFact(a?.id === state.agent_id && a.workspaceId === state.workspace_id
        && a.cwd === config.cwd && a.provider === 'pi'
        && a.runtimeInfo?.model === fixed && a.effectiveThinkingOptionId === 'max'
        && !a.labels?.['paseo.parent-agent-id']);
      return a;
    }
    await inspect();
    const proof = privateJSON(path.join(config.process_dir, `${state.agent_id}.json`));
    requireFact(Object.keys(proof).sort().join(',') ===
      ['agent_id','test_id','pid','ppid','start_time','parent_start_time','executable','sha256','auth_inherited'].sort().join(',')
      && typeof proof.start_time === 'string' && /^[0-9]{1,32}$/.test(proof.start_time)
      && typeof proof.parent_start_time === 'string' && /^[0-9]{1,32}$/.test(proof.parent_start_time)
      && proof.agent_id === state.agent_id && proof.test_id === config.test_id
      && Number.isInteger(proof.pid) && proof.pid > 0 && proof.ppid === config.daemon.worker_pid
      && proof.auth_inherited === true && proof.executable === config.pi.path && proof.sha256 === config.pi.sha256);
    function processBinding() {
      const stat = (pid) => fs.readFileSync(`/proc/${pid}/stat`, 'utf8').split(')').slice(1).join(')').trim().split(/\s+/)[19];
      requireFact(stat(proof.pid) === proof.start_time && stat(proof.ppid) === proof.parent_start_time);
      requireFact(fs.realpathSync(`/proc/${proof.ppid}/exe`) === fs.realpathSync(config.daemon.node));
      const argv = fs.readFileSync(`/proc/${proof.pid}/cmdline`, 'utf8').split('\0');
      requireFact(argv.includes(config.pi.path) && argv.includes('--mode') && argv.includes('rpc')
        && argv.includes('--model') && argv.includes(fixed) && argv.includes('--thinking') && argv.includes('max'));
    }
    processBinding();
    const binding = {...proof, workspace_id: state.workspace_id, server_id: config.daemon.server_id};
    const bindingFd = fs.openSync(config.binding, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o600);
    try {
      const st = fs.fstatSync(bindingFd, {bigint: true}); binding.file_identity = `${st.dev}:${st.ino}`;
      fs.writeFileSync(bindingFd, JSON.stringify(binding)); fs.fsyncSync(bindingFd);
    } finally { fs.closeSync(bindingFd); }
    state.process = binding; state.dispatch = 'prompt_pending'; persist(state);
    server(); await inspect(); processBinding();
    requireFact(identity(config.binding) === binding.file_identity);
    requireFact(Date.now() < deadline);
    await bounded(client.sendMessage(state.agent_id, `M07-T05 bounded smoke ${config.test_id}`, {messageId: state.message_id}));
    state.dispatch = 'prompt_sent'; persist(state);
    const finish = await bounded(client.waitForFinish(state.agent_id, 90000), 90000);
    requireFact(finish.final?.id === state.agent_id);
    if (finish.status !== 'idle') throw new Error('completion uncertain');
    await inspect();
    requireFact(JSON.stringify(privateJSON(config.binding)) === JSON.stringify(binding));
    requireFact(identity(config.binding) === binding.file_identity);
    processBinding(); // PID reuse/replacement cannot borrow the old exchange.
    state.dispatch = 'settled'; persist(state);
    return {status: 'PASS', reference: config.reference, ...state};
  } catch {
    // Once an acquisition may have occurred, retain refs and never replay/clean.
    // Validation failure before effects is terminal; uncertain inspection is not.
    return {status: effect ? 'UNKNOWN' : 'FAIL', reference: config.reference, ...state};
  } finally { if (client) await bounded(client.close(), 1000).catch(() => {}); }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const config = privateJSON(process.argv[2]);
    const {connectToDaemon} = await import('/usr/local/lib/node_modules/@getpaseo/cli/dist/utils/client.js');
    const result = await runOwnedTest(config, connectToDaemon);
    console.log(JSON.stringify(result)); process.exitCode = result.status === 'PASS' ? 0 : 20;
  } catch { console.log(JSON.stringify({status: 'UNKNOWN', replay: false})); process.exitCode = 20; }
}
