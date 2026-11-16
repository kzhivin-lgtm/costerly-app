// This path is relative to the configured Cloudflare Pages root: cloudflare/.
const MAX_BODY_BYTES = 16 * 1024;
const MAX_EVENTS = 50;
const SAFE_NAME = /^[a-z0-9_.:-]{1,80}$/;
const STATUSES = new Set(["ok", "error", "timeout", "dropped", "unknown"]);
const FAILURE_KINDS = new Set(["wrapper_error", "wrapper_rejection", "app_error", "app_rejection",
                               "server_exception_rendered", "error_alert_rendered"]);
const ERROR_TYPES = new Set(["error", "typeerror", "rangeerror", "referenceerror", "syntaxerror",
                             "networkerror", "securityerror", "notfounderror", "aborterror",
                             "quotaexceedederror", "dom_remove_child"]);

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
  const timestamp = new Date(raw.occurred_at || Date.now());
  if (!Number.isFinite(timestamp.getTime())) return null;
  const status = safeName(raw.status, "ok");
  const event = safeName(raw.event_name, "invalid_event");
  const timing = (value, original) => original != null && Number.isFinite(value) && value >= 0 && value < 1e11
    ? value : null;
  let metadata = safeMetadata(raw.metadata);
  if (event === "browser.runtime_failure") {
    // Do not accept freeform client message, stack, URL, or DOM contents.
    const kind = safeName(metadata.kind, "unknown");
    const errorType = safeName(metadata.error_type, "unknown");
    metadata = {
      kind: FAILURE_KINDS.has(kind) ? kind : "unknown",
      error_type: ERROR_TYPES.has(errorType) ? errorType : "unknown",
      line: Number.isInteger(metadata.line) && metadata.line > 0 && metadata.line < 1000000
        ? metadata.line : null,
    };
  }
  return {
    occurred_at: timestamp.toISOString(),
    schema_version: "runtime_v1",
    build_version: safeName(raw.build_version, "unknown"),
    source: "browser",
    trace_id: raw.trace_id,
    session_id: validUuid(raw.session_id) ? raw.session_id : null,
    run_id: validUuid(raw.run_id) ? raw.run_id : null,
    event_name: event,
    screen: safeName(raw.screen, "unknown"),
    status: STATUSES.has(status) ? status : "unknown",
    elapsed_ms: timing(elapsed, raw.elapsed_ms),
    duration_ms: timing(duration, raw.duration_ms),
    metadata,
  };
}

export async function onRequest(context) {
  const { request, env } = context;
  if (request.method !== "POST") return response(405, "method not allowed");
  const allowedOrigins = new Set([
    "https://app.costerly.ai",
    "https://staging.costerly.ai",
  ]);
  if (env.COSTERLY_ALLOWED_ORIGIN) {
    allowedOrigins.add(env.COSTERLY_ALLOWED_ORIGIN);
  }
  if (!allowedOrigins.has(request.headers.get("origin"))) {
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

  try {
    const stored = await fetch(`${env.SUPABASE_URL.replace(/\/$/, "")}/rest/v1/app_runtime_events`, {
      method: "POST",
      headers: {
        apikey: env.SUPABASE_SERVICE_ROLE_KEY,
        authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
        "content-type": "application/json",
        prefer: "return=minimal",
      },
      body: JSON.stringify(events),
      signal: AbortSignal.timeout(3500),
    });
    if (!stored.ok) {
      console.warn("runtime_events_upstream_rejected", stored.status, events.length);
      return response(502, "telemetry storage failed");
    }
  } catch (_) {
    console.warn("runtime_events_upstream_unavailable", events.length);
    return response(502, "telemetry storage unavailable");
  }
  return response(202);
}
