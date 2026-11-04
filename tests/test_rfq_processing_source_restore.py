from __future__ import annotations

import pandas as pd

from use_cases.rfq_processing import _persisted_estimation_original


def test_file_review_recovers_the_private_original_from_its_durable_source_ledger():
    source = {
        "storage_ref": "storage://rfq-estimation-originals/company-1/abc.pdf",
        "content_sha256": "a" * 64,
        "mime_type": "application/pdf",
        "size_bytes": 42,
    }
    usage = pd.DataFrame([{
        "operation": "rfq_source_original",
        "raw_usage": {"estimation_original": source},
    }])

    assert _persisted_estimation_original(usage) == source


def test_file_review_does_not_guess_a_source_from_incomplete_telemetry():
    usage = pd.DataFrame([{
        "operation": "rfq_source_original",
        "raw_usage": {"estimation_original": {"storage_ref": "storage://rfq-estimation-originals/x"}},
    }])

    assert _persisted_estimation_original(usage) is None
