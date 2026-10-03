from __future__ import annotations

import secrets
from typing import Any


_ROUTE_SCOPES = {"run", "estimate", "object"}


def workflow_route_key(
    *,
    scope: str,
    run_id: str,
    estimate_id: str | None = None,
    object_id: str | None = None,
) -> str:
    if scope not in _ROUTE_SCOPES:
        raise ValueError(f"Unsupported workflow route scope: {scope}")
    if not run_id:
        raise ValueError("Workflow route requires run_id.")
    if scope == "run":
        return f"run:{run_id}"
    if not estimate_id:
        raise ValueError("Estimate and object routes require estimate_id.")
    if scope == "estimate":
        return f"estimate:{estimate_id}"
    if not object_id:
        raise ValueError("Object routes require object_id.")
    return f"object:{estimate_id}:{object_id}"


def _read_token(client: Any, route_key: str) -> str | None:
    rows = (
        client.table("rfq_workflow_routes")
        .select("route_token")
        .eq("route_key", route_key)
        .limit(1)
        .execute()
        .data
        or []
    )
    token = str(rows[0].get("route_token") or "") if rows else ""
    return token or None


def ensure_workflow_route_token(
    client: Any,
    *,
    company_id: str,
    scope: str,
    run_id: str,
    estimate_id: str | None = None,
    object_id: str | None = None,
) -> str:
    """Return one durable, non-semantic token for a workflow resource.

    The token shortens the browser URL only. It is never an access grant: the
    caller must still check the resolved row's company before using its IDs.
    """
    route_key = workflow_route_key(
        scope=scope,
        run_id=run_id,
        estimate_id=estimate_id,
        object_id=object_id,
    )
    existing = _read_token(client, route_key)
    if existing:
        return existing

    payload = {
        "route_key": route_key,
        "company_id": str(company_id),
        "scope": scope,
        "run_id": str(run_id),
        "estimate_id": str(estimate_id) if estimate_id else None,
        "object_id": str(object_id) if object_id else None,
    }
    for _ in range(3):
        payload["route_token"] = secrets.token_urlsafe(9)
        try:
            client.table("rfq_workflow_routes").insert(payload).execute()
        except Exception:
            # A concurrent renderer may have created this route first, or the
            # random token could theoretically collide. Prefer the canonical
            # route-key row before generating another token.
            existing = _read_token(client, route_key)
            if existing:
                return existing
            continue
        return str(payload["route_token"])
    raise RuntimeError("Could not allocate a workflow route token.")


def ensure_object_workflow_route_tokens(
    client: Any,
    *,
    company_id: str,
    run_id: str,
    estimate_id: str,
    object_ids: list[str],
) -> dict[str, str]:
    """Return durable object routes with one batched read and at most one insert."""
    unique_ids = list(dict.fromkeys(str(value) for value in object_ids if value))
    if not unique_ids:
        return {}
    keys = {
        object_id: workflow_route_key(
            scope="object",
            run_id=run_id,
            estimate_id=estimate_id,
            object_id=object_id,
        )
        for object_id in unique_ids
    }
    existing_rows = (
        client.table("rfq_workflow_routes")
        .select("route_key,route_token")
        .in_("route_key", list(keys.values()))
        .execute()
        .data
        or []
    )
    tokens_by_key = {
        str(row.get("route_key") or ""): str(row.get("route_token") or "")
        for row in existing_rows
    }
    missing = [object_id for object_id, key in keys.items() if not tokens_by_key.get(key)]
    if missing:
        payloads = [
            {
                "route_key": keys[object_id],
                "route_token": secrets.token_urlsafe(9),
                "company_id": str(company_id),
                "scope": "object",
                "run_id": str(run_id),
                "estimate_id": str(estimate_id),
                "object_id": object_id,
            }
            for object_id in missing
        ]
        try:
            client.table("rfq_workflow_routes").insert(payloads).execute()
            tokens_by_key.update({row["route_key"]: row["route_token"] for row in payloads})
        except Exception:
            # A concurrent screen may have inserted the same route keys.
            refreshed = (
                client.table("rfq_workflow_routes")
                .select("route_key,route_token")
                .in_("route_key", list(keys.values()))
                .execute()
                .data
                or []
            )
            tokens_by_key = {
                str(row.get("route_key") or ""): str(row.get("route_token") or "")
                for row in refreshed
            }
    result = {object_id: tokens_by_key.get(key, "") for object_id, key in keys.items()}
    if any(not token for token in result.values()):
        raise RuntimeError("Could not allocate all object workflow route tokens.")
    return result


def resolve_workflow_route_token(
    client: Any,
    *,
    route_token: str,
    company_id: str,
    expected_scope: str,
) -> dict[str, str]:
    """Resolve a short route after enforcing its owner and expected screen."""
    if expected_scope not in _ROUTE_SCOPES:
        raise ValueError(f"Unsupported workflow route scope: {expected_scope}")
    rows = (
        client.table("rfq_workflow_routes")
        .select("company_id,scope,run_id,estimate_id,object_id")
        .eq("route_token", str(route_token))
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise ValueError("Workflow route was not found.")
    row = rows[0]
    if str(row.get("company_id") or "") != str(company_id):
        raise PermissionError("Workflow route is not available to this company.")
    if str(row.get("scope") or "") != expected_scope:
        raise ValueError("Workflow route does not match this screen.")

    resolved = {"run_id": str(row.get("run_id") or "")}
    estimate_id = str(row.get("estimate_id") or "")
    object_id = str(row.get("object_id") or "")
    if estimate_id:
        resolved["estimate_id"] = estimate_id
    if object_id:
        resolved["object_id"] = object_id
    if not resolved["run_id"]:
        raise ValueError("Workflow route is missing its RFQ run.")
    return resolved
