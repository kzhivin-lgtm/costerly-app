from copy import deepcopy
from types import SimpleNamespace

from use_cases.price_source_material_resolution import (
    _load_resolution_index,
    invalidate_global_resolution_index,
    resolve_price_source_material_identities,
)
from use_cases.material_pricing_identity_resolution import (
    build_material_pricing_identity_index,
    resolve_material_pricing_identity,
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

    def range(self, start, end):
        self.row_range = (start, end)
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
        if hasattr(self, "row_range"):
            start, end = self.row_range
            matches = matches[start:end + 1]
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
        "reference_material_pricing_identities": [],
        "company_price_sources": [
            {"source_id": "source-1", "company_id": "company-1", "supplier_id": None}
        ],
        "company_suppliers": [],
        "company_material_items": [
            {
                "company_material_id": "company-material-1",
                "company_id": "company-1",
            "reference_material_id": None,
                "pricing_identity_id": None,
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


def test_catalog_v1_is_not_selected_before_v2_is_active():
    tables = _tables()
    tables["reference_materials"].append(
        {
            "material_id": "catalog-v1-mdf",
            "department": "wood",
            "category_code": "gcm_mdf",
            "canonical_name": "Global MDF 18 mm",
            "base_unit": "sqm",
            "specifications": {"catalog_version": "israel_global_catalog_v1"},
            "active": True,
        }
    )

    index = _load_resolution_index(_Client(tables), company_id="company-1", market_code="IL")

    assert {row["material_id"] for row in index["materials"]} == {
        "reference-mdf",
        "catalog-v1-mdf",
    }

    tables["material_resolver_versions"][0]["resolver_version"] = "material_identity_v2"
    index = _load_resolution_index(_Client(tables), company_id="company-1", market_code="IL")

    assert [row["material_id"] for row in index["materials"]] == ["catalog-v1-mdf"]


def test_catalog_index_reads_past_the_default_postgrest_page():
    tables = _tables()
    tables["material_resolver_versions"][0]["resolver_version"] = "material_identity_v2"
    tables["reference_materials"] = [
        {
            "material_id": f"catalog-{index}",
            "department": "wood",
            "category_code": "gcm_mdf",
            "canonical_name": f"Global MDF {index}",
            "base_unit": "sqm",
            "specifications": {"catalog_version": "israel_global_catalog_v1"},
            "active": True,
        }
        for index in range(1_001)
    ]

    index = _load_resolution_index(_Client(tables), company_id="company-1", market_code="IL")

    assert len(index["materials"]) == 1_001


def test_global_catalog_index_is_reused_until_explicitly_invalidated():
    tables = _tables()
    client = _Client(tables)
    invalidate_global_resolution_index()

    first = _load_resolution_index(client, company_id="company-1", market_code="IL")
    first_reference_selects = client.calls.count(("reference_materials", "select"))
    second = _load_resolution_index(client, company_id="company-1", market_code="IL")

    assert first["global_index_cache_hit"] is False
    assert second["global_index_cache_hit"] is True
    assert client.calls.count(("reference_materials", "select")) == first_reference_selects

    invalidate_global_resolution_index(market_code="IL")
    third = _load_resolution_index(client, company_id="company-1", market_code="IL")

    assert third["global_index_cache_hit"] is False
    assert client.calls.count(("reference_materials", "select")) == first_reference_selects + 1

    tables["material_resolver_versions"][0]["catalog_fingerprint"] = "catalog-after-update"
    fourth = _load_resolution_index(client, company_id="company-1", market_code="IL")

    assert fourth["global_index_cache_hit"] is False
    assert client.calls.count(("reference_materials", "select")) == first_reference_selects + 2


def test_pricing_identity_index_preserves_resolution_and_skips_other_families():
    identities = [
        {
            "pricing_identity_id": "mdf-18",
            "market_code": "IL",
            "status": "active",
            "price_attributes": {"material_family": "mdf", "thickness_mm": 18},
        },
        {
            "pricing_identity_id": "plywood-18",
            "market_code": "IL",
            "status": "active",
            "price_attributes": {"material_family": "plywood", "thickness_mm": 18},
        },
        {
            "pricing_identity_id": "legacy-familyless",
            "market_code": "IL",
            "status": "active",
            "price_attributes": {"thickness_mm": 18},
        },
    ]
    index = build_material_pricing_identity_index(identities)

    unindexed = resolve_material_pricing_identity(
        material_family="MDF",
        specifications={"thickness_mm": 18},
        market_code="IL",
        pricing_identities=identities,
    )
    indexed = resolve_material_pricing_identity(
        material_family="MDF",
        specifications={"thickness_mm": 18},
        market_code="IL",
        pricing_identities=identities,
        pricing_identity_index=index,
    )

    assert indexed == unindexed
    assert {item["pricing_identity_id"] for item in index[("IL", "mdf")]} == {
        "mdf-18",
        "legacy-familyless",
    }


def test_v3_uses_pricing_identity_before_detail_identity():
    tables = _tables(exact_alias=False)
    tables["material_resolver_versions"][0]["resolver_version"] = "material_identity_v3"
    tables["reference_materials"][0]["specifications"] = {
        "catalog_version": "israel_global_catalog_v1",
        "thickness_mm": 18,
    }
    tables["company_price_source_rows"][0]["evidence"] = {
        "material_type": "Wood Sheets",
        "material_family": "mdf",
        "identity_attributes": {"thickness_mm": 18, "surface": "exposed"},
    }
    tables["reference_material_pricing_identities"] = [{
        "pricing_identity_id": "price-mdf-18-raw",
        "market_code": "IL",
        "department": "wood",
        "canonical_name": "MDF, raw, 18 mm",
        "base_unit": "m2",
        "price_attributes": {
            "material_family": "mdf",
            "construction": "raw",
            "thickness_mm": 18,
        },
        "status": "active",
    }]

    batch = resolve_price_source_material_identities(
        _Client(tables), company_id="company-1", source_id="source-1"
    )

    assert batch.resolved == 1
    assert tables["company_material_items"][0]["pricing_identity_id"] == "price-mdf-18-raw"
    assert tables["company_price_source_rows"][0]["pricing_identity_id"] == "price-mdf-18-raw"
    assert tables["material_identity_resolution_events"][0]["selected_pricing_identity_id"] == "price-mdf-18-raw"
    assert tables["material_identity_candidates"] == []


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


def test_identity_agent_auto_links_only_a_high_confidence_bounded_candidate():
    tables = _tables(exact_alias=False)

    def identity_agent(requests):
        assert len(requests) == 1
        assert len(requests[0]["candidates"]) == 1
        return [{
            "source_row_id": "row-1",
            "decision": "link_existing",
            "selected_material_id": "reference-mdf",
            "confidence": 93,
            "reason": "Same material and thickness",
        }]

    batch = resolve_price_source_material_identities(
        _Client(tables),
        company_id="company-1",
        source_id="source-1",
        identity_agent=identity_agent,
    )

    assert batch.resolved == 1
    assert batch.shortlisted == 0
    assert tables["company_material_items"][0]["reference_material_id"] == "reference-mdf"
    assert tables["material_identity_candidates"] == []
    assert tables["company_price_source_rows"][0]["identity_route"] == "identity_agent_link_existing"


def test_low_confidence_identity_agent_decision_stays_in_review():
    tables = _tables(exact_alias=False)

    batch = resolve_price_source_material_identities(
        _Client(tables),
        company_id="company-1",
        source_id="source-1",
        identity_agent=lambda _requests: [{
            "source_row_id": "row-1",
            "decision": "link_existing",
            "selected_material_id": "reference-mdf",
            "confidence": 89,
            "reason": "Insufficient evidence",
        }],
    )

    assert batch.shortlisted == 1
    assert batch.resolved == 0
    assert tables["company_material_items"][0]["reference_material_id"] is None
    assert len(tables["material_identity_candidates"]) == 1


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
