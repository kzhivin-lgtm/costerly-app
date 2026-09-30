import use_cases.estimation_runtime as runtime


def test_estimation_v2_facts_shadow_is_enabled_by_default_after_acceptance(monkeypatch):
    monkeypatch.setattr(runtime, "get_secret", lambda _name, default: default)

    assert runtime._estimation_v2_facts_shadow_enabled() is True


def test_estimation_v2_facts_shadow_has_explicit_false_rollback(monkeypatch):
    monkeypatch.setattr(runtime, "get_secret", lambda _name, _default: "false")

    assert runtime._estimation_v2_facts_shadow_enabled() is False
