// This path is relative to the configured Cloudflare Pages root: cloudflare/.
const MAX_BODY_BYTES = 16 * 1024;
const MAX_EVENTS = 50;
const SAFE_NAME = /^[a-z0-9_.:-]{1,80}$/;

function response(status, body = "") {
  return new Response(body, {
    status,
    headers: {
      "cache-control": "no-store",
      "content-type": "text/plain; charset=utf-8",
    },
  });
}

function safeName(value, fallback) {
  const text = String(value || "").trim().toLowerCase();
  return SAFE_NAME.test(text) ? text : fallback;
}

function safeMetadata(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const result = {};
  for (const [rawKey, rawValue] of Object.entries(value).slice(0, 30)) {
    const key = String(rawKey).slice(0, 80);
    if (
      key.toLowerCase() !== "dom_content_loaded_ms" &&
      /token|password|secret|email|file|content/i.test(key)
    ) {
      result[key] = "[redacted]";
    } else if (rawValue === null || ["boolean", "number"].includes(typeof rawValue)) {
      result[key] = rawValue;
    } else if (typeof rawValue === "string") {
      result[key] = rawValue.slice(0, 300);
    }
  }
  return result;
}

function validUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    String(value || "")
  );
}

function normalizeEvent(raw) {
  if (!raw || typeof raw !== "object" || !validUuid(raw.trace_id)) return null;
  const elapsed = Number(raw.elapsed_ms);
  const duration = Number(raw.duration_ms);
  return {
    occurred_at: new Date(raw.occurred_at || Date.now()).toISOString(),
    schema_version: "runtime_v1",
    build_version: String(raw.build_version || "3.1.2").slice(0, 40),
    source: "browser",
    trace_id: raw.trace_id,
    session_id: validUuid(raw.session_id) ? raw.session_id : null,
    run_id: validUuid(raw.run_id) ? raw.run_id : null,
    event_name: safeName(raw.event_name, "invalid_event"),
    screen: safeName(raw.screen, "unknown"),
    status: safeName(raw.status, "ok"),
    elapsed_ms: Number.isFinite(elapsed) ? Math.max(0, elapsed) : null,
    duration_ms: Number.isFinite(duration) ? Math.max(0, duration) : null,
    metadata: safeMetadata(raw.metadata),
  };
}

export async function onRequest(context) {
  const { request, env } = context;
  if (request.method !== "POST") return response(405, "method not allowed");
  const allowedOrigin = env.COSTERLY_ALLOWED_ORIGIN || "https://app.costerly.ai";
  if (request.headers.get("origin") !== allowedOrigin) {
    return response(403, "origin not allowed");
  }
  const length = Number(request.headers.get("content-length") || 0);
  if (length > MAX_BODY_BYTES) return response(413, "payload too large");
  if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) {
    return response(503, "telemetry unavailable");
  }

  let payload;
  try {
    const body = await request.text();
    if (new TextEncoder().encode(body).byteLength > MAX_BODY_BYTES) {
      return response(413, "payload too large");
    }
    payload = JSON.parse(body);
  } catch (_) {
    return response(400, "invalid json");
  }
  const rawEvents = Array.isArray(payload) ? payload : [payload];
  if (!rawEvents.length || rawEvents.length > MAX_EVENTS) {
    return response(400, "invalid event count");
  }
  const events = rawEvents.map(normalizeEvent).filter(Boolean);
  if (!events.length) return response(400, "invalid events");

  const persist = fetch(`${env.SUPABASE_URL.replace(/\/$/, "")}/rest/v1/app_runtime_events`, {
    method: "POST",
    headers: {
      apikey: env.SUPABASE_SERVICE_ROLE_KEY,
      authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
      "content-type": "application/json",
      prefer: "return=minimal",
    },
    body: JSON.stringify(events),
  });
  context.waitUntil(persist);
  return response(202);
}
