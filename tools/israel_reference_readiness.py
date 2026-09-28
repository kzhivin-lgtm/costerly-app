from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import re
import sys


ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from use_cases.reference_material_readiness import (  # noqa: E402
    ReferenceOffer,
    build_reference_readiness_report,
)


PRICE_FILE_PATTERN = "2026_09_28_israel_reference_prices_*.sql"
ADDITIONAL_PRICE_FILES = ("2026_09_28_israel_reference_price_comparisons_v1.sql",)


def _split_sql_values(value_block: str) -> list[list[str]]:
    rows = []
    row_start = None
    depth = 0
    in_string = False
    index = 0
    while index < len(value_block):
        character = value_block[index]
        if character == "'":
            if in_string and index + 1 < len(value_block) and value_block[index + 1] == "'":
                index += 2
                continue
            in_string = not in_string
        elif not in_string:
            if character == "(":
                if depth == 0:
                    row_start = index + 1
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and row_start is not None:
                    row = value_block[row_start:index]
                    rows.append(_split_sql_fields(row))
                    row_start = None
        index += 1
    return rows


def _split_sql_fields(row: str) -> list[str]:
    fields = []
    field_start = 0
    depth = 0
    in_string = False
    index = 0
    while index < len(row):
        character = row[index]
        if character == "'":
            if in_string and index + 1 < len(row) and row[index + 1] == "'":
                index += 2
                continue
            in_string = not in_string
        elif not in_string:
            if character in "([":
                depth += 1
            elif character in ")]":
                depth -= 1
            elif character == "," and depth == 0:
                fields.append(row[field_start:index].strip())
                field_start = index + 1
        index += 1
    fields.append(row[field_start:].strip())
    return fields


def _sql_literal(value: str) -> str | None:
    value = value.strip()
    if value.lower() == "null":
        return None
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def _insert_rows(path: Path, table: str, conflict_columns: str):
    conflict_pattern = r"\s*,\s*".join(
        re.escape(column.strip()) for column in conflict_columns.split(",")
    )
    pattern = re.compile(
        rf"insert into public\.{table}\s*\((.*?)\)\s*values\s*(.*?)"
        rf"on conflict\s*\({conflict_pattern}\)",
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(path.read_text()):
        columns = [column.strip() for column in match.group(1).split(",")]
        for values in _split_sql_values(match.group(2)):
            if len(values) != len(columns):
                raise ValueError(
                    f"{path.name}: {len(values)} values for {len(columns)} "
                    f"columns in public.{table}"
                )
            yield dict(zip(columns, map(_sql_literal, values)))


def load_seed_report():
    sql_root = ROOT / "db/sql"
    price_files = sorted(sql_root.glob(PRICE_FILE_PATTERN))
    price_files.extend(sql_root / name for name in ADDITIONAL_PRICE_FILES)
    material_rows = {}
    offer_rows = {}
    for path in price_files:
        for row in _insert_rows(path, "reference_materials", "material_code"):
            material_rows[row["material_id"]] = row
        for row in _insert_rows(path, "market_material_offers", "market_offer_id"):
            offer_rows[row["market_offer_id"]] = row

    offers = [
        ReferenceOffer(
            offer_id=row["market_offer_id"],
            material_id=row["material_id"],
            market_code=row["market_code"],
            source_id=row["source_id"],
            currency=row["source_currency"],
            price_scope=row["price_scope"],
            vat_mode=row["vat_mode"],
            normalized_price_ex_vat=(
                Decimal(row["normalized_price_ex_vat"])
                if row["normalized_price_ex_vat"] is not None
                else None
            ),
            normalized_unit=row["normalized_unit"],
            status=row["status"],
            region=row.get("region"),
            confidence=Decimal(row["confidence"]),
            source_price=Decimal(row["source_price"]),
            source_unit=row["source_unit"],
            package_quantity=(
                Decimal(row["package_quantity"])
                if row["package_quantity"] is not None
                else None
            ),
            conversion_basis={},
        )
        for row in offer_rows.values()
    ]
    return build_reference_readiness_report(
        material_departments={
            material_id: row["department"]
            for material_id, row in material_rows.items()
        },
        offers=offers,
    )


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def render_markdown(report) -> str:
    lines = [
        "# Israel Reference Price Readiness",
        "",
        f"Market: `{report.market_code}`  ",
        f"Currency: `{report.currency}`",
        "",
        "## Summary",
        "",
        f"- Materials: {report.material_count}",
        f"- Candidate offers: {report.offer_count}",
        f"- Eligible normalized offers: {report.eligible_offer_count}",
        f"- Materials with an eligible price: {report.eligible_material_count}",
        f"- Materials blocked or missing: {report.blocked_material_count}",
        f"- Comparable baseline groups: {report.baseline_group_count}",
        f"- Single-source provisional groups: {report.single_source_group_count}",
        f"- Multi-source candidate groups: {report.multi_source_group_count}",
        "",
        "## Material readiness by department",
        "",
        "| Department | Eligible | Blocked | Missing | Total |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for department, counts in report.department_counts.items():
        lines.append(
            f"| {department} | {counts.get('eligible', 0)} | "
            f"{counts.get('normalization_blocked', 0)} | "
            f"{counts.get('evidence_gap', 0)} | {counts.get('total', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Blocked-offer reasons",
            "",
        ]
    )
    for reason, count in report.blocked_offer_reasons.items():
        lines.append(f"- `{reason}`: {count}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    report = load_seed_report()
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, default=_json_default))
    else:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
