import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  conservativeModelDefinition,
  createDynamicProviderConfig,
  definitionsFromCatalog,
  createSessionRefreshController,
  loadBootstrapConfig,
  parseCatalog,
} from "../config/pi-agent/extensions/lib/codex-lb-dynamic-model-catalog-core.mjs";

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cldmc-core-"));
const home = path.join(tmp, "home");
const agent = path.join(home, ".pi", "agent");
fs.mkdirSync(agent, { recursive: true });
fs.writeFileSync(
  path.join(agent, "models.json"),
  JSON.stringify({
    untouched: { marker: true },
    providers: {
      other: { api: "openai-completions", baseUrl: "http://example.invalid/v1", apiKey: "placeholder", models: [{ id: "other" }] },
      "codex-lb": {
        baseUrl: "http://codex-lb.test/v1",
        api: "openai-responses",
        apiKey: "${CODEX_LB_API_KEY}",
        models: [{ id: "seed-model" }],
      },
    },
  }),
);

const bootstrap = loadBootstrapConfig({ env: { HOME: home }, home });
assert.equal(bootstrap.baseUrl, "http://codex-lb.test/v1");
assert.deepEqual(bootstrap.staticModelIds, ["seed-model"]);
assert.equal(bootstrap.refreshIntervalMs, 300000);
assert.throws(
  () => loadBootstrapConfig({
    env: { HOME: home, PI_CODEX_LB_BASE_URL: "http://different.test/v1" },
    home,
  }),
  /conflicts with models\.json/,
);

assert.deepEqual(
  parseCatalog({ data: [{ id: "zeta" }, { id: "alpha" }, { id: "alpha" }] }),
  ["alpha", "zeta"],
);
for (const payload of [{}, { data: [] }, { data: [{ id: "" }] }, { data: [{ id: "bad id" }] }]) {
  assert.throws(() => parseCatalog(payload));
}
assert.deepEqual(conservativeModelDefinition("alpha"), {
  id: "alpha",
  name: "alpha",
  reasoning: false,
  input: ["text"],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  contextWindow: 128000,
  maxTokens: 16384,
});

const verifiedDefinition = definitionsFromCatalog({
  data: [{
    id: "verified-reasoning-model",
    supports_reasoning: true,
    context_length: 272000,
    metadata: {
      supported_reasoning_levels: [
        { effort: "low" },
        { effort: "medium" },
        { effort: "high" },
        { effort: "xhigh" },
        { effort: "max" },
      ],
    },
  }],
})[0];
assert.equal(verifiedDefinition.reasoning, true);
assert.equal(verifiedDefinition.contextWindow, 272000);
assert.equal(verifiedDefinition.maxTokens, 16384);
assert.deepEqual(verifiedDefinition.thinkingLevelMap, {
  off: null,
  minimal: null,
  low: "low",
  medium: "medium",
  high: "high",
  xhigh: "xhigh",
  max: "max",
});
const unverifiedDefinition = definitionsFromCatalog({
  data: [{ id: "verified-reasoning-model" }],
})[0];
assert.equal(unverifiedDefinition.reasoning, false);
assert.equal(unverifiedDefinition.thinkingLevelMap, undefined);
assert.equal(unverifiedDefinition.contextWindow, 128000);

const published = [];
let seenAuth;
const provider = createDynamicProviderConfig(bootstrap, {
  now: () => 123456,
  fetchFn: async (url, options) => {
    seenAuth = options.headers.authorization;
    assert.equal(url, "http://codex-lb.test/v1/models");
    return new Response(
      JSON.stringify({
        object: "list",
        data: [
          {
            id: "beta",
            capabilities: { supports_reasoning: true, context_length: 256000 },
            metadata: { supported_reasoning_levels: [{ effort: "low" }, { effort: "high" }] },
          },
          { id: "alpha" },
          { id: "beta" },
        ],
      }),
      {
        status: 200,
        headers: {
          "content-type": "application/json",
          etag: '"catalog-v1"',
          "last-modified": "Sun, 27 Sep 2026 20:00:00 GMT",
        },
      },
    );
  },
});
const abort = new AbortController();
const ctx = {
  allowNetwork: true,
  credential: { type: "api_key", key: "fixture-secret-never-log" },
  signal: abort.signal,
  stored: undefined,
  async publish(value) {
    published.push(value);
    return true;
  },
};
const refreshed = await provider.refreshModels(ctx);
assert.deepEqual(refreshed.map((model) => model.id), ["alpha", "beta"]);
const refreshedBeta = refreshed.find((model) => model.id === "beta");
assert.equal(refreshedBeta.reasoning, true);
assert.equal(refreshedBeta.contextWindow, 256000);
assert.equal(refreshedBeta.thinkingLevelMap.low, "low");
assert.equal(refreshedBeta.thinkingLevelMap.medium, null);
assert.equal(refreshedBeta.thinkingLevelMap.high, "high");
assert.equal(seenAuth, "Bearer fixture-secret-never-log");
assert.equal(published.length, 1);
assert.deepEqual(published[0].persist.models.map((model) => model.id), ["alpha", "beta"]);
assert.ok(published[0].persist.models.every((model) => model.provider === "codex-lb"));
assert.ok(published[0].persist.models.every((model) => model.api === "openai-responses"));
assert.equal(published[0].persist.checkedAt, 123456);
assert.equal(published[0].persist.etag, '"catalog-v1"');

const stored = published[0].persist;
let networkCalled = false;
const offlineProvider = createDynamicProviderConfig(
  { ...bootstrap, staticModelIds: [] },
  {
    fetchFn: async () => {
      networkCalled = true;
      throw new Error("should not run");
    },
  },
);
const offline = await offlineProvider.refreshModels({
  allowNetwork: false,
  signal: new AbortController().signal,
  stored,
  async publish() {
    throw new Error("cache-only refresh must not publish");
  },
});
assert.deepEqual(offline.map((model) => model.id), ["alpha", "beta"]);
const offlineBeta = offline.find((model) => model.id === "beta");
assert.equal(offlineBeta.reasoning, true);
assert.equal(offlineBeta.contextWindow, 256000);
assert.equal(offlineBeta.thinkingLevelMap.low, "low");
assert.equal(offlineBeta.thinkingLevelMap.medium, null);
assert.equal(networkCalled, false);

let validatorSeen;
const fullRefreshProvider = createDynamicProviderConfig(bootstrap, {
  fetchFn: async (_url, options) => {
    validatorSeen = options.headers["if-none-match"];
    return new Response(JSON.stringify({ data: [{ id: "beta" }] }), { status: 200 });
  },
});
await fullRefreshProvider.refreshModels({
  allowNetwork: true,
  credential: { type: "api_key", key: "fixture-secret-never-log" },
  signal: new AbortController().signal,
  stored,
  async publish() { return true; },
});
assert.equal(validatorSeen, undefined);

async function assertFailurePreservesStored(testProvider, pattern) {
  let publishCount = 0;
  await assert.rejects(
    testProvider.refreshModels({
      allowNetwork: true,
      credential: { type: "api_key", key: "fixture-secret-never-log" },
      signal: new AbortController().signal,
      stored,
      async publish() {
        publishCount += 1;
        return true;
      },
    }),
    pattern,
  );
  assert.equal(publishCount, 0);
}

const invalidJsonProvider = createDynamicProviderConfig(bootstrap, {
  fetchFn: async () => new Response("{", { status: 200 }),
});
await assertFailurePreservesStored(invalidJsonProvider, /not valid JSON/);

const invalidShapeProvider = createDynamicProviderConfig(bootstrap, {
  fetchFn: async () => new Response(JSON.stringify({ object: "list", data: "not-an-array" }), { status: 200 }),
});
await assertFailurePreservesStored(invalidShapeProvider, /not an OpenAI-compatible catalog/);

const timeoutProvider = createDynamicProviderConfig(bootstrap, {
  timeoutMs: 5,
  fetchFn: async (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener("abort", () => reject(new Error("aborted by timeout")), { once: true });
  }),
});
await assertFailurePreservesStored(timeoutProvider, /model catalog request failed/);

let badPublishCount = 0;
const badProvider = createDynamicProviderConfig(bootstrap, {
  fetchFn: async () => new Response(JSON.stringify({ data: [{ id: "bad id" }] }), { status: 200 }),
});
await assert.rejects(
  badProvider.refreshModels({
    allowNetwork: true,
    credential: { type: "api_key", key: "fixture-secret-never-log" },
    signal: new AbortController().signal,
    stored,
    async publish() {
      badPublishCount += 1;
      return true;
    },
  }),
  /invalid model id/,
);
assert.equal(badPublishCount, 0);

const authProvider = createDynamicProviderConfig(bootstrap, {
  fetchFn: async () => new Response("", { status: 401 }),
});
let authError;
try {
  await authProvider.refreshModels({
    allowNetwork: true,
    credential: { type: "api_key", key: "secret-401-value" },
    signal: new AbortController().signal,
    stored,
    async publish() {
      throw new Error("must not publish auth failure");
    },
  });
} catch (error) {
  authError = String(error);
}
assert.match(authError, /authentication rejected/);
assert.ok(!authError.includes("secret-401-value"));

let refreshCalls = 0;
let releaseRefresh;
const pending = new Promise((resolve) => {
  releaseRefresh = resolve;
});
let intervalCallback;
let cleared = false;
const controller = createSessionRefreshController({
  intervalMs: 1000,
  setIntervalFn(callback) {
    intervalCallback = callback;
    return { unref() {} };
  },
  clearIntervalFn() {
    cleared = true;
  },
  onDiagnostic() {
    throw new Error("unexpected diagnostic");
  },
});
const refreshContext = {
  modelRegistry: {
    async refresh(options) {
      refreshCalls += 1;
      assert.deepEqual(options, { providers: ["codex-lb"], allowNetwork: true });
      await pending;
      return { aborted: false, errors: new Map() };
    },
  },
};
controller.start(refreshContext);
assert.equal(typeof intervalCallback, "function");
const first = controller.refreshNow(refreshContext);
const second = controller.refreshNow(refreshContext);
assert.equal(first, second);
assert.equal(refreshCalls, 1);
releaseRefresh();
await first;
assert.equal(controller.isRefreshInFlight(), false);
controller.stop();
assert.equal(cleared, true);

fs.rmSync(tmp, { recursive: true, force: true });
console.log("codex-lb dynamic catalog core tests: GREEN");