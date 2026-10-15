#!/usr/bin/env python3
"""Read-only audit of the active Material pipeline contracts.

This checks catalog-driven compatibility, rather than a hand-picked material
fixture.  It deliberately makes no Price Source, Company Catalog, Israel
Reference or Estimate writes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client
from use_cases.catalog_aliases import load_estimation_alias_context, load_price_source_alias_context
from use_cases.estimation_v3_material_contract import SPECIFICATION_KEYS
from use_cases.israel_reference_catalog import load_active_israel_reference_positions
from use_cases.material_engine_adapter import israel_reference_supply_candidates
from use_cases.material_identity_status import (
    material_pricing_selection_key,
    pricing_key_fact_fields,
    pricing_policy_by_family_code,
)
from use_cases.material_price_resolver import _canonical_unit


# These are deterministic formula rows, not purchasable Material Demands.  They
# remain in the catalog for Price Source history, but a missing Israel purchase
# candidate must not be reported as a Resolver gap.
_FORMULA_OVERHEAD_FAMILIES = frozenset({
    "hardware_fastener",
    "packaging_material",
    "paint_lacquer_stain",
    "powder_coating",
    "primer",
    "filler_hardener_thinner",
})


def _rows(client: Any, table: str, *, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    start = 0
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        page = query.range(start, start + 999).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < 1000:
            return result
        start += 1000


def _ineligible_reference_reason(
    *, position: Mapping[str, Any], family_code: str,
    policies: Mapping[str, Mapping[str, Any]], price_scope: str,
) -> str:
    """Classify why one listed position could not become a Resolver candidate."""
    if material_pricing_selection_key(
        material_family=family_code,
        specifications=dict(position.get("specifications") or {}),
        pricing_policies=policies,
    ) is None:
        return "pricing_key_incomplete"
    prices = [
        row for row in position.get("prices") or ()
        if str(row.get("status") or "") == "active"
        and str(row.get("currency") or "").upper() == "ILS"
        and str(row.get("price_scope") or "") == price_scope
        and row.get("price_typical") not in (None, "", 0, 0.0)
    ]
    if not prices:
        return "active_scope_price_missing"
    continuous = any(_canonical_unit(row.get("unit")) in {"sqm", "lm"} for row in prices)
    if continuous and not tuple(position.get("supply_formats") or ()):
        return "listing_purchase_format_missing"
    return "candidate_conversion_failed"


def audit_material_pipeline(
    *,
    material_families: Sequence[Mapping[str, Any]],
    material_pricing_policies: Sequence[Mapping[str, Any]],
    price_source_family_aliases: Mapping[str, Sequence[str]],
    estimation_alias_context: Mapping[str, Mapping[str, object]],
    reference_positions: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    """Return one contract status per active Family, without selecting a price."""
    policies = pricing_policy_by_family_code(material_pricing_policies, families=material_families)
    rows: list[dict[str, object]] = []
    for family in sorted(material_families, key=lambda row: str(row.get("family_code") or "")):
        family_code = str(family.get("family_code") or "")
        policy = policies.get(family_code)
        if not family_code or policy is None:
            continue
        resolution_scope = (
            "formula_overhead" if family_code in _FORMULA_OVERHEAD_FAMILIES else "resolver"
        )
        pricing_fields = tuple(dict.fromkeys(
            field
            for attribute in policy.get("pricing_key_attribute_codes") or ()
            for field in pricing_key_fact_fields(str(attribute))
            if field in SPECIFICATION_KEYS
        ))
        unsupported_v3_fields = tuple(
            str(attribute)
            for attribute in policy.get("pricing_key_attribute_codes") or ()
            if not any(field in SPECIFICATION_KEYS for field in pricing_key_fact_fields(str(attribute)))
        )
        price_source_aliases = tuple(price_source_family_aliases.get(family_code) or ())
        estimation_context = estimation_alias_context.get(family_code) or {}
        estimation_aliases = tuple(estimation_context.get("family_aliases") or ())
        position_count = candidate_position_count = 0
        ineligible_reasons: Counter[str] = Counter()
        price_scope = "retail_package" if family_code.startswith("hardware_") else "material_only"
        for position in reference_positions:
            if str(position.get("family_code") or "") != family_code:
                continue
            position_count += 1
            _selection_key, candidates = israel_reference_supply_candidates(
                material_family=family_code,
                specifications=dict(position.get("specifications") or {}),
                reference_positions=reference_positions,
                material_pricing_policies=material_pricing_policies,
                material_families=material_families,
                price_scope=price_scope,
                reference_position_id=str(position.get("reference_position_id") or ""),
            )
            if candidates:
                candidate_position_count += 1
            else:
                ineligible_reasons[_ineligible_reference_reason(
                    position=position,
                    family_code=family_code,
                    policies=policies,
                    price_scope=price_scope,
                )] += 1
        issues: list[str] = []
        if resolution_scope == "resolver" and unsupported_v3_fields:
            issues.append("v3_contract_missing:" + ",".join(unsupported_v3_fields))
        if resolution_scope == "resolver" and not price_source_aliases:
            issues.append("price_source_family_alias_missing")
        if resolution_scope == "resolver" and not estimation_aliases:
            issues.append("estimation_family_alias_missing")
        if resolution_scope == "resolver" and position_count and candidate_position_count == 0:
            issues.append("israel_positions_not_resolver_eligible")
        rows.append({
            "family_code": family_code,
            "resolution_scope": resolution_scope,
            "pricing_key_fields": pricing_fields,
            "israel_positions": position_count,
            "resolver_eligible_israel_positions": candidate_position_count,
            "ineligible_reference_reasons": tuple(sorted(ineligible_reasons.items())),
            "issues": tuple(issues),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()
    client = get_supabase_client()
    families = _rows(client, "reference_material_families", filters={"active": True})
    policies = _rows(client, "reference_material_family_pricing_policies", filters={"active": True})
    policies_by_family = pricing_policy_by_family_code(policies, families=families)
    fields_by_family = {
        family_code: tuple(dict.fromkeys(
            field
            for attribute in policy.get("pricing_key_attribute_codes") or ()
            for field in pricing_key_fact_fields(str(attribute))
            if field in SPECIFICATION_KEYS
        ))
        for family_code, policy in policies_by_family.items()
    }
    price_source_context = load_price_source_alias_context(client)
    estimation_context = load_estimation_alias_context(
        client,
        family_codes=tuple(policies_by_family),
        pricing_key_fields_by_family=fields_by_family,
    )
    rows = audit_material_pipeline(
        material_families=families,
        material_pricing_policies=policies,
        price_source_family_aliases=price_source_context.family_aliases,
        estimation_alias_context=estimation_context,
        reference_positions=load_active_israel_reference_positions(client),
    )
    issue_counts = Counter(issue for row in rows for issue in row["issues"])
    resolver_rows = [row for row in rows if row["resolution_scope"] == "resolver"]
    summary = (
        f"{len(rows)} active Families, {len(resolver_rows)} Resolver Families, "
        f"{sum(not row['issues'] for row in resolver_rows)} Resolver-contract-clean"
    )
    report = ["# Material Pipeline Audit", "", "Status: read-only catalog-driven audit.", "", f"Summary: {summary}", ""]
    if issue_counts:
        report.extend(["## Issues", "", *(f"- {issue}: {count}" for issue, count in sorted(issue_counts.items())), ""])
    report.extend(["## Family coverage", "", "| Family | Scope | Pricing Key fields | Israel positions | Resolver-eligible positions | Ineligible reasons | Issues |", "| --- | --- | --- | ---: | ---: | --- | --- |"])
    for row in rows:
        report.append(
            f"| {row['family_code']} | {row['resolution_scope']} | {', '.join(row['pricing_key_fields']) or 'none'} | "
            f"{row['israel_positions']} | {row['resolver_eligible_israel_positions']} | "
            f"{', '.join(f'{reason}:{count}' for reason, count in row['ineligible_reference_reasons']) or 'none'} | "
            f"{', '.join(row['issues']) or 'none'} |"
        )
    output = "\n".join(report) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
