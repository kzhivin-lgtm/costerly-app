from use_cases.estimation_originals import ORIGINALS_BUCKET, persist_estimation_original


class _Bucket:
    def __init__(self):
        self.uploads = []

    def upload(self, path, data, file_options):
        self.uploads.append((path, data, file_options))


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
