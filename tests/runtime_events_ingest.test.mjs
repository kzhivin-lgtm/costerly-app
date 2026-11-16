import assert from "node:assert/strict";
import { test } from "node:test";
import { onRequest } from "../cloudflare/functions/api/runtime-events.js";

const origin = "https://app.costerly.ai";
const env = { SUPABASE_URL: "https://supabase.invalid", SUPABASE_SERVICE_ROLE_KEY: "test-only" };
const trace = "11111111-1111-4111-8111-111111111111";
const run = "22222222-2222-4222-8222-222222222222";

function request(event) {
  return new Request(origin + "/api/runtime-events", {
    method: "POST", headers: { origin }, body: JSON.stringify(event),
  });
}

test("the browser receives a failure when durable storage rejects the batch", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("", { status: 503 }));
  const response = await onRequest({ request: request({ trace_id: trace }), env });
  assert.equal(response.status, 502);
});

test("acknowledges a stored browser error with correlation and only approved fields", async (t) => {
  let stored;
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    [stored] = JSON.parse(options.body);
    return new Response(null, { status: 204 });
  });
  const event = {
    trace_id: trace, run_id: run, event_name: "browser.runtime_failure", screen: "objects", status: "error",
    metadata: { kind: "app_error", error_type: "TypeError", line: 81, message: "private",
                stack: "private", url: "private" },
  };
  assert.equal((await onRequest({ request: request(event), env })).status, 202);
  assert.equal(stored.run_id, run);
  assert.equal(stored.trace_id, trace);
  assert.equal(stored.status, "error");
  assert.deepEqual(stored.metadata, { kind: "app_error", error_type: "typeerror", line: 81 });
});
