from __future__ import annotations


def load_latest_estimate_route(client, company_id: str) -> dict[str, str] | None:
    """Return the newest company-owned estimate that can reopen Objects.

    Estimate rows are durable while browser session state is not.  This lookup
    intentionally reads only the owning company's latest shell and never
    creates, recalculates, or mutates an estimate.
    """
    rows = (
        client.table("rfq_estimates")
        .select("estimate_id,run_id")
        .eq("company_id", str(company_id))
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    row = rows[0]
    estimate_id = str(row.get("estimate_id") or "")
    run_id = str(row.get("run_id") or "")
    if not estimate_id or not run_id:
        return None
    return {"estimate_id": estimate_id, "run_id": run_id}


def load_latest_file_review_route(client, company_id: str) -> dict[str, str] | None:
    """Return the newest successfully processed RFQ for the header restore action.

    File Review is available before a user presses Continue and creates an
    ``rfq_estimates`` shell.  The header action therefore must be based on the
    completed Processing ledger, not on estimates alone.  This avoids opening
    an unrelated older file after ``New Estimate``.
    """
    rows = (
        client.table("agent_usage_events")
        .select("run_id")
        .eq("company_id", str(company_id))
        .eq("agent_name", "orchestration")
        .eq("operation", "rfq_processing_cycle")
        .eq("status", "succeeded")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    run_id = str(rows[0].get("run_id") or "").strip()
    return {"estimate_id": "", "run_id": run_id} if run_id else None


def load_latest_estimate_route_for_run(
    client,
    company_id: str,
    run_id: str,
) -> dict[str, object] | None:
    """Find the saved result for one authorized RFQ, including older estimates."""
    rows = (
        client.table("rfq_estimates")
        .select(
            "estimate_id,run_id,"
            "objects:rfq_object_estimates(object_id,object_name,quantity,status,self_cost_ex_vat),"
            "plan:rfq_estimate_material_plans(plan_status,unresolved:plan_payload->unresolved_requirement_ids)"
        )
        .eq("company_id", str(company_id))
        .eq("run_id", str(run_id))
        .order("created_at", desc=True)
        .order("estimate_id", desc=True)
        .execute()
        .data
        or []
    )
    candidates = [
        row for row in rows
        if row.get("estimate_id") and row.get("run_id") == str(run_id)
    ]
    if not candidates:
        return None

    published = [row for row in candidates if _has_published_objects(row)]
    chosen = candidates[0]
    if published:
        chosen = published[0]
        scope = _object_scope(chosen)
        if chosen["plan"]["plan_status"] == "needs_review" and chosen["plan"].get("unresolved"):
            # Recovery could create a poorer duplicate for exactly the same
            # inputs. An explicitly changed object selection is a new scope.
            chosen = next(
                (row for row in published if _object_scope(row) == scope
                 and row["plan"]["plan_status"] in {"planned", "needs_review"}
                 and row["plan"].get("unresolved") == []
                 and all(obj.get("self_cost_ex_vat") is not None for obj in row["objects"])),
                chosen,
            )

    return {
        "estimate_id": str(chosen["estimate_id"]),
        "run_id": str(run_id),
        "object_ids": [str(row["object_id"]) for row in chosen.get("objects") or []],
    }


def _has_published_objects(row: dict) -> bool:
    plan = row.get("plan") or {}
    objects = row.get("objects") or []
    return (
        plan.get("plan_status") in {"planned", "needs_review", "stale", "running", "failed"}
        and bool(objects)
        and all(
            obj.get("status") in {"completed", "review_required"}
            for obj in objects
        )
    )


def _object_scope(row: dict) -> frozenset:
    return frozenset(
        (obj["object_id"], obj["object_name"], obj["quantity"])
        for obj in row["objects"]
    )
