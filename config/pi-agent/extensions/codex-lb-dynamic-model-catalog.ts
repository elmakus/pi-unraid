import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

import {
  createDynamicProviderConfig,
  createSessionRefreshController,
  loadBootstrapConfig,
} from "./lib/codex-lb-dynamic-model-catalog-core.mjs";

const PROVIDER_ID = "codex-lb";

export default function (pi: ExtensionAPI) {
  const bootstrap = loadBootstrapConfig();
  pi.registerProvider(PROVIDER_ID, createDynamicProviderConfig(bootstrap));

  const refresher = createSessionRefreshController({
    providerId: PROVIDER_ID,
    intervalMs: bootstrap.refreshIntervalMs,
    onDiagnostic: () => {
      console.warn("[codex-lb-catalog] model catalog refresh failed; keeping the current catalog");
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    refresher.start(ctx);
    await refresher.refreshNow(ctx);
  });

  pi.on("session_shutdown", () => {
    refresher.stop();
  });
}