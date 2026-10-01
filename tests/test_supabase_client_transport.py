from db import supabase_client


def test_supabase_http_client_disables_http2_for_shared_sync_runtime(monkeypatch):
    captured = {}

    class _Client:
        pass

    def _client(**kwargs):
        captured.update(kwargs)
        return _Client()

    monkeypatch.setattr(supabase_client.httpx, "Client", _client)

    result = supabase_client._create_http_client()

    assert isinstance(result, _Client)
    assert captured["http2"] is False
    assert captured["timeout"] is supabase_client._SUPABASE_TIMEOUT
    assert captured["limits"] is supabase_client._SUPABASE_LIMITS
