import pytest

from use_cases.estimation_originals import (
    ORIGINALS_BUCKET,
    load_estimation_original,
    persist_estimation_original,
    stored_original_from_metadata,
    stored_original_metadata,
)


class _Bucket:
    def __init__(self):
        self.uploads = []
        self.downloads = []

    def upload(self, path, data, file_options):
        self.uploads.append((path, data, file_options))

    def download(self, path):
        self.downloads.append(path)
        return self.uploads[0][1]


class _Storage:
    def __init__(self, bucket):
        self.bucket = bucket

    def from_(self, name):
        assert name == ORIGINALS_BUCKET
        return self.bucket


class _Client:
    def __init__(self):
        self.bucket = _Bucket()
        self.storage = _Storage(self.bucket)


def test_original_upload_uses_private_deterministic_content_reference():
    client = _Client()
    result = persist_estimation_original(
        client=client, company_id="company-1", file_name="quote.pdf", file_bytes=b"source"
    )

    assert result.storage_ref.startswith("storage://rfq-estimation-originals/company-1/")
    assert result.mime_type == "application/pdf"
    assert result.size_bytes == 6
    path, _data, options = client.bucket.uploads[0]
    assert path.endswith(".pdf")
    assert options["upsert"] == "false"


def test_original_metadata_round_trips_through_a_verified_company_scoped_download():
    client = _Client()
    stored = persist_estimation_original(
        client=client, company_id="company-1", file_name="quote.pdf", file_bytes=b"source"
    )

    restored = stored_original_from_metadata(stored_original_metadata(stored))

    assert restored == stored
    assert load_estimation_original(
        client=client, company_id="company-1", stored=restored,
    ) == b"source"
    assert client.bucket.downloads == ["company-1/" + stored.content_sha256 + ".pdf"]


def test_original_download_rejects_a_foreign_company_prefix():
    client = _Client()
    stored = persist_estimation_original(
        client=client, company_id="company-1", file_name="quote.pdf", file_bytes=b"source"
    )

    with pytest.raises(PermissionError):
        load_estimation_original(client=client, company_id="company-2", stored=stored)


def test_original_reuses_only_an_identical_deterministic_storage_conflict():
    client = _Client()
    persist_estimation_original(
        client=client, company_id="company-1", file_name="quote.pdf", file_bytes=b"source"
    )

    def conflict(*_args, **_kwargs):
        raise RuntimeError("already exists")

    client.bucket.upload = conflict
    stored = persist_estimation_original(
        client=client, company_id="company-1", file_name="quote.pdf", file_bytes=b"source"
    )

    assert stored.content_sha256
    assert client.bucket.downloads == ["company-1/" + stored.content_sha256 + ".pdf"]
