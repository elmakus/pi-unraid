#!/usr/bin/env node

const args = process.argv.slice(2);
const version = process.env.PI_TEST_VERSION || "9.9.9";

if (args[0] === "--version") {
  process.stdout.write(version + "\n");
  process.exit(0);
}

if (process.env.PI_TEST_PROBE_FAIL === "1") {
  process.exit(43);
}

if (args[0] === "--mode" && args[1] === "rpc") {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => { input += chunk; });
  process.stdin.on("end", () => {
    let request;
    try {
      request = JSON.parse(input.trim());
    } catch {
      process.exit(44);
    }
    process.stdout.write(JSON.stringify({
      id: request.id,
      type: "response",
      command: "get_state",
      success: true,
      data: {}
    }) + "\n");
  });
  process.stdin.resume();
} else {
  process.exit(45);
}
