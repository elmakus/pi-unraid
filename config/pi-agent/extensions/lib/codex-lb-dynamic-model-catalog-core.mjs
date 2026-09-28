import fs from "node:fs";
import path from "node:path";

export const PROVIDER_ID = "codex-lb";
export const PROVIDER_API = "openai-responses";
export const DEFAULT_REFRESH_INTERVAL_MS = 300_000;
export const MIN_REFRESH_INTERVAL_MS = 1_000;
export const MAX_REFRESH_INTERVAL_MS = 3_600_000;
export const DEFAULT_DISCOVERY_TIMEOUT_MS = 5_000;

const ZERO_COST = Object.freeze({ input: 0, output: 0, cacheRead: 0, cacheWrite: 0 });
const API_KEY_REFS = new Set(["$CODEX_LB_API_KEY", "${CODEX_LB_API_KEY}"]);

function fail(message) {
  throw new Error(`Codex-LB dynamic catalog: ${message}`);
}

export function normalizeBaseUrl(raw) {
  if (typeof raw !== "string" || raw.trim() !== raw || !raw) {
    fail("provider baseUrl must be a non-empty string");
  }
  let url;
  try {
    url = new URL(raw);
  } catch {
    fail("provider baseUrl is not a valid URL");
  }
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    fail("provider baseUrl must be an HTTP(S) URL without credentials, query, or fragment");
  }
  const normalizedPath = url.pathname.replace(/\/+$/, "");
  if (!normalizedPath.endsWith("/v1")) {
    fail("provider baseUrl must end in /v1");
  }
  url.pathname = normalizedPath;
  return url.toString().replace(/\/$/, "");
}

export function parseRefreshInterval(env = process.env) {
  const raw = env.PI_CODEX_LB_MODEL_REFRESH_MS;
  if (raw === undefined || raw === "") return DEFAULT_REFRESH_INTERVAL_MS;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < MIN_REFRESH_INTERVAL_MS || value > MAX_REFRESH_INTERVAL_MS) {
    fail(`PI_CODEX_LB_MODEL_REFRESH_MS must be an integer between ${MIN_REFRESH_INTERVAL_MS} and ${MAX_REFRESH_INTERVAL_MS}`);
  }
  return value;
}

function validModelId(value) {
  return typeof value === "string" &&
    value.length > 0 &&
    value === value.trim() &&
    !/[\s\u0000-\u001f\u007f]/u.test(value);
}

export function parseCatalog(payload) {
  if (!payload || typeof payload !== "object" || !Array.isArray(payload.data)) {
    fail("models response is not an OpenAI-compatible catalog");
  }
  if (payload.data.length === 0) fail("models response contains no models");

  const ids = new Set();
  for (const item of payload.data) {
    if (!item || typeof item !== "object" || !validModelId(item.id)) {
      fail("models response contains an invalid model id");
    }
    ids.add(item.id);
  }
  return [...ids].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

export function conservativeModelDefinition(id) {
  if (!validModelId(id)) fail("invalid model id");
  return {
    id,
    name: id,
    reasoning: false,
    input: ["text"],
    cost: { ...ZERO_COST },
    contextWindow: 128_000,
    maxTokens: 16_384,
  };
}

function storedModelDefinition(model, baseUrl) {
  return {
    ...conservativeModelDefinition(model.id),
    provider: PROVIDER_ID,
    api: PROVIDER_API,
    baseUrl,
  };
}

function definitionsFromStored(stored) {
  if (!stored || !Array.isArray(stored.models)) return [];
  const ids = [];
  for (const model of stored.models) {
    if (!model || typeof model !== "object" || model.provider !== PROVIDER_ID || !validModelId(model.id)) {
      return [];
    }
    ids.push(model.id);
  }
  return [...new Set(ids)]
    .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
    .map(conservativeModelDefinition);
}

function staticDefinitions(ids) {
  return ids.map(conservativeModelDefinition);
}

export function loadBootstrapConfig({
  env = process.env,
  home = env.HOME,
  readFileSync = fs.readFileSync,
} = {}) {
  if (!home) fail("HOME is unavailable");
  const modelsPath = env.PI_MODELS_FILE || path.join(home, ".pi", "agent", "models.json");
  let doc;
  try {
    doc = JSON.parse(readFileSync(modelsPath, "utf8"));
  } catch {
    fail("models.json is unavailable or invalid");
  }
  const provider = doc?.providers?.[PROVIDER_ID];
  if (!provider || typeof provider !== "object" || Array.isArray(provider)) {
    fail("codex-lb provider bootstrap is missing");
  }
  if (provider.api !== PROVIDER_API) fail("codex-lb provider must use openai-responses");
  if (!API_KEY_REFS.has(provider.apiKey)) fail("codex-lb provider must use the CODEX_LB_API_KEY reference");

  const configuredBaseUrl = normalizeBaseUrl(provider.baseUrl);
  const environmentBaseUrl = env.PI_CODEX_LB_BASE_URL
    ? normalizeBaseUrl(env.PI_CODEX_LB_BASE_URL)
    : undefined;
  if (environmentBaseUrl && environmentBaseUrl !== configuredBaseUrl) {
    fail("PI_CODEX_LB_BASE_URL conflicts with models.json");
  }

  const staticModelIds = [];
  if (provider.models !== undefined) {
    if (!Array.isArray(provider.models)) fail("codex-lb provider models must be an array");
    for (const model of provider.models) {
      if (!model || typeof model !== "object" || !validModelId(model.id)) {
        fail("codex-lb provider contains an invalid static model id");
      }
      staticModelIds.push(model.id);
    }
  }

  return {
    baseUrl: environmentBaseUrl || configuredBaseUrl,
    staticModelIds: [...new Set(staticModelIds)].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0)),
    refreshIntervalMs: parseRefreshInterval(env),
  };
}

function apiKeyFromCredential(credential) {
  if (credential?.type !== "api_key" || typeof credential.key !== "string" || !credential.key) {
    fail("resolved provider credential is unavailable");
  }
  return credential.key;
}

function combinedAbortSignal(parentSignal, timeoutMs) {
  const controller = new AbortController();
  const onAbort = () => controller.abort();
  if (parentSignal?.aborted) controller.abort();
  else parentSignal?.addEventListener("abort", onAbort, { once: true });
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return {
    signal: controller.signal,
    dispose() {
      clearTimeout(timer);
      parentSignal?.removeEventListener("abort", onAbort);
    },
  };
}

function headerValue(headers, name) {
  if (!headers || typeof headers.get !== "function") return undefined;
  const value = headers.get(name);
  return value === null ? undefined : value;
}

export function createRefreshModels({
  baseUrl,
  staticModelIds = [],
  fetchFn = globalThis.fetch,
  timeoutMs = DEFAULT_DISCOVERY_TIMEOUT_MS,
  now = () => Date.now(),
} = {}) {
  const normalizedBaseUrl = normalizeBaseUrl(baseUrl);
  if (typeof fetchFn !== "function") fail("fetch is unavailable");
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0 || timeoutMs > 30_000) {
    fail("discovery timeout is outside the accepted bound");
  }
  const staticFallback = staticDefinitions(staticModelIds);

  return async function refreshModels(context) {
    const cached = definitionsFromStored(context.stored);
    const fallback = cached.length > 0 ? cached : staticFallback;
    if (!context.allowNetwork) return fallback;

    const credentialValue = apiKeyFromCredential(context.credential);
    const headers = {
      accept: "application/json",
      authorization: `Bearer ${credentialValue}`,
    };
    if (cached.length > 0 && typeof context.stored?.etag === "string" && context.stored.etag) {
      headers["if-none-match"] = context.stored.etag;
    }

    const bounded = combinedAbortSignal(context.signal, timeoutMs);
    let response;
    try {
      response = await fetchFn(`${normalizedBaseUrl}/models`, {
        method: "GET",
        headers,
        signal: bounded.signal,
      });
    } catch {
      fail("model catalog request failed");
    } finally {
      bounded.dispose();
    }

    if (context.signal?.aborted) return fallback;
    const checkedAt = now();

    if (response.status === 304) {
      if (cached.length === 0 || !context.stored) fail("received 304 without a stored catalog");
      const published = await context.publish({
        persist: { ...context.stored, checkedAt },
      });
      return published === false ? fallback : cached;
    }

    if (response.status === 401 || response.status === 403) {
      fail("model catalog authentication rejected");
    }
    if (!response.ok) fail(`model catalog request returned HTTP ${response.status}`);

    let payload;
    try {
      payload = await response.json();
    } catch {
      fail("models response is not valid JSON");
    }
    const definitions = parseCatalog(payload).map(conservativeModelDefinition);
    const lastModifiedRaw = headerValue(response.headers, "last-modified");
    const lastModified = lastModifiedRaw ? Date.parse(lastModifiedRaw) : Number.NaN;
    const etag = headerValue(response.headers, "etag");

    const entry = {
      models: definitions.map((model) => storedModelDefinition(model, normalizedBaseUrl)),
      checkedAt,
      ...(Number.isNaN(lastModified) ? {} : { lastModified }),
      ...(etag ? { etag } : {}),
    };
    const published = await context.publish({ persist: entry });
    return published === false || context.signal?.aborted ? fallback : definitions;
  };
}

export function createDynamicProviderConfig(bootstrap, dependencies = {}) {
  return {
    name: "Codex-LB",
    baseUrl: normalizeBaseUrl(bootstrap.baseUrl),
    api: PROVIDER_API,
    refreshModels: createRefreshModels({
      baseUrl: bootstrap.baseUrl,
      staticModelIds: bootstrap.staticModelIds,
      ...dependencies,
    }),
  };
}

export function createSessionRefreshController({
  providerId = PROVIDER_ID,
  intervalMs = DEFAULT_REFRESH_INTERVAL_MS,
  setIntervalFn = setInterval,
  clearIntervalFn = clearInterval,
  onDiagnostic = () => {},
} = {}) {
  if (!Number.isInteger(intervalMs) || intervalMs < MIN_REFRESH_INTERVAL_MS || intervalMs > MAX_REFRESH_INTERVAL_MS) {
    fail("session refresh interval is outside the accepted bound");
  }
  let timer;
  let inFlight;

  const refreshNow = (ctx) => {
    if (inFlight) return inFlight;
    inFlight = (async () => {
      try {
        const result = await ctx.modelRegistry.refresh({
          providers: [providerId],
          allowNetwork: true,
        });
        if (result?.errors?.size > 0) onDiagnostic();
      } catch {
        onDiagnostic();
      }
    })().finally(() => {
      inFlight = undefined;
    });
    return inFlight;
  };

  const stop = () => {
    if (timer !== undefined) {
      clearIntervalFn(timer);
      timer = undefined;
    }
  };

  return {
    start(ctx) {
      stop();
      timer = setIntervalFn(() => {
        void refreshNow(ctx);
      }, intervalMs);
      if (timer && typeof timer.unref === "function") timer.unref();
    },
    stop,
    refreshNow,
    isRefreshInFlight: () => inFlight !== undefined,
  };
}