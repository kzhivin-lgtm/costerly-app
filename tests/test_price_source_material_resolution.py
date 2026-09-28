from copy import deepcopy
from types import SimpleNamespace

from use_cases.price_source_material_resolution import (
    resolve_price_source_material_identities,
)


class _Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.filters = []
        self.operation = "select"
        self.payload = None
        self.row_limit = None

    def select(self, *_args):
        return self

    def eq(self, key, value):
        self.filters.append(("eq", key, value))
        return self

    def neq(self, key, value):
        self.filters.append(("neq", key, value))
        return self

    def in_(self, key, values):
        self.filters.append(("in", key, set(values)))
        return self

    def is_(self, key, value):
        self.filters.append(("is", key, value))
        return self

    def limit(self, value):
        self.row_limit = value
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = deepcopy(payload)
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = deepcopy(payload)
        return self

    def upsert(self, payload, **_kwargs):
        self.operation = "upsert"
        self.payload = deepcopy(payload)
        return self

    def _matches(self, row):
        for operation, key, value in self.filters:
            if operation == "eq" and row.get(key) != value:
                return False
            if operation == "neq" and row.get(key) == value:
                return False
            if operation == "in" and row.get(key) not in value:
                return False
            if operation == "is" and value == "null" and row.get(key) is not None:
                return False
        return True

    def execute(self):
        self.client.calls.append((self.table, self.operation))
        rows = self.client.tables[self.table]
        if self.operation == "insert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted_rows = []
            id_fields = {
                "material_identity_candidates": "candidate_id",
                "material_identity_resolution_events": "resolution_event_id",
            }
            id_field = id_fields.get(self.table)
            for payload in payloads:
                inserted = deepcopy(payload)
                if id_field:
                    inserted.setdefault(id_field, f"{self.table}-{len(rows) + 1}")
                inserted.setdefault("status", "pending")
                rows.append(inserted)
                inserted_rows.append(deepcopy(inserted))
            return SimpleNamespace(data=inserted_rows)
        if self.operation == "upsert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            primary_keys = {
                "company_price_source_rows": "row_id",
            }
            primary_key = primary_keys[self.table]
            upserted = []
            for payload in payloads:
                existing = next(
                    (
                        row
                        for row in rows
                        if row.get(primary_key) == payload.get(primary_key)
                    ),
                    None,
                )
                if existing is None:
                    existing = deepcopy(payload)
                    rows.append(existing)
                else:
                    existing.update(deepcopy(payload))
                upserted.append(deepcopy(existing))
            return SimpleNamespace(data=upserted)
        matches = [row for row in rows if self._matches(row)]
        if self.row_limit is not None:
            matches = matches[: self.row_limit]
        if self.operation == "update":
            for row in matches:
                row.update(deepcopy(self.payload))
        return SimpleNamespace(data=deepcopy(matches))


class _Client:
    def __init__(self, tables):
        self.tables = tables
        self.calls = []

    def table(self, name):
        return _Query(self, name)


def _tables(*, exact_alias=True):
    aliases = [
        {
            "material_id": "reference-mdf",
            "market_code": "IL",
            "alias_text": "MDF 18 mm",
            "exact_identity": exact_alias,
            "confidence": 100,
            "active": True,
        }
    ]
    return {
        "material_resolver_versions": [
            {
                "resolver_version": "material_identity_v1",
                "market_code": "IL",
                "status": "active",
            }
        ],
        "reference_materials": [
            {
                "material_id": "reference-mdf",
                "department": "wood",
                "category_code": "mdf",
                "canonical_name": "MDF 18 mm",
                "base_unit": "sqm",
                "specifications": {"thickness_mm": 18},
                "active": True,
            }
        ],
        "reference_material_aliases": aliases,
        "company_material_aliases": [],
        "market_material_offers": [],
        "company_price_sources": [
            {"source_id": "source-1", "company_id": "company-1", "supplier_id": None}
        ],
        "company_suppliers": [],
        "company_material_items": [
            {
                "company_material_id": "company-material-1",
                "company_id": "company-1",
                "reference_material_id": None,
                "category": "Wood Sheets",
                "canonical_name": "MDF 18 mm",
                "specifications": {},
                "status": "private",
            }
        ],
        "company_price_source_rows": [
            {
                "row_id": "row-1",
                "source_id": "source-1",
                "company_id": "company-1",
                "company_material_id": "company-material-1",
                "normalized_name": "MDF 18 mm",
                "raw_description": "MDF 18 mm",
                "raw_sku": None,
                "result_status": "new",
                "evidence": {"material_type": "Wood Sheets"},
            }
        ],
        "company_material_offers": [
            {
                "offer_id": "offer-1",
                "company_id": "company-1",
                "source_row_id": "row-1",
            }
        ],
        "material_identity_candidates": [],
        "material_identity_resolution_events": [],
    }


def test_exact_alias_links_company_material_and_records_immutable_event():
    tables = _tables()
    batch = resolve_price_source_material_identities(
        _Client(tables), company_id="company-1", source_id="source-1"
    )

    assert batch.resolved == 1
    assert tables["company_material_items"][0]["reference_material_id"] == "reference-mdf"
    assert tables["company_price_source_rows"][0]["reference_material_id"] == "reference-mdf"
    assert tables["company_price_source_rows"][0]["identity_route"] == "exact_market_alias"
    assert tables["company_material_offers"][0]["identity_confidence"] == 100
    assert tables["material_identity_candidates"] == []
    assert len(tables["material_identity_resolution_events"]) == 1


def test_non_exact_match_stays_private_and_enters_review_buffer():
    tables = _tables(exact_alias=False)
    batch = resolve_price_source_material_identities(
        _Client(tables), company_id="company-1", source_id="source-1"
    )

    assert batch.shortlisted == 1
    assert tables["company_material_items"][0]["reference_material_id"] is None
    assert tables["company_price_source_rows"][0]["reference_material_id"] is None
    assert len(tables["material_identity_candidates"]) == 1
    assert tables["material_identity_candidates"][0]["status"] == "pending"
    assert len(tables["material_identity_candidates"][0]["candidate_materials"]) == 1


def test_repeat_run_does_not_duplicate_same_version_event():
    tables = _tables()
    client = _Client(tables)
    resolve_price_source_material_identities(
        client, company_id="company-1", source_id="source-1"
    )
    second = resolve_price_source_material_identities(
        client, company_id="company-1", source_id="source-1"
    )

    assert second.unchanged == 1
    assert len(tables["material_identity_resolution_events"]) == 1


def test_large_shortlist_batch_uses_one_write_per_destination_table():
    tables = _tables(exact_alias=False)
    template = tables["company_price_source_rows"][0]
    tables["company_price_source_rows"] = [
        {**template, "row_id": f"row-{index}"}
        for index in range(40)
    ]
    client = _Client(tables)

    batch = resolve_price_source_material_identities(
        client, company_id="company-1", source_id="source-1"
    )

    assert batch.shortlisted == 40
    assert client.calls.count(("material_identity_candidates", "insert")) == 1
    assert client.calls.count(("company_price_source_rows", "upsert")) == 1
    assert client.calls.count(("material_identity_resolution_events", "insert")) == 1
