from use_cases.estimation_v2_revisions import (
    build_composition_idempotency_key,
    plan_object_revision,
)


PREVIOUS = {
    "object_id": "object-1",
    "object_name": "Original name",
    "quantity": 1,
    "ignored": False,
    "evidence_signature": "evidence-v1",
    "object_input_revision": 3,
}


def _current(**overrides):
    result = {key: value for key, value in PREVIOUS.items() if key != "object_input_revision"}
    result.update(overrides)
    return result


def _versions(**overrides):
    result = {
        "material_catalog": "materials-v1",
        "pricing_catalog": "pricing-il-v1",
        "labor_catalog": "labor-v0",
        "machinery_snapshot": "machinery-company-1-v4",
        "overhead_policy": "overhead-company-1-v2",
        "pricing_policy": "self-cost-plus-30-v1",
    }
    result.update(overrides)
    return result


def test_e04_file_review_changes_are_classified_without_unrelated_work():
    renamed = plan_object_revision(previous=PREVIOUS, current=_current(object_name="Approved name"))
    quantity = plan_object_revision(previous=PREVIOUS, current=_current(quantity=2))
    ignored = plan_object_revision(previous=PREVIOUS, current=_current(ignored=True))

    assert renamed["action"] == "update_display_name"
    assert renamed["queue_extraction"] is False and renamed["recalculate"] is False
    assert quantity["action"] == "reaggregate_quantity"
    assert quantity["reuse_facts"] is True and quantity["next_object_input_revision"] == 4
    assert ignored["action"] == "deactivate"
    assert ignored["active"] is False and ignored["recalculate"] is False


def test_e10_same_input_and_versions_have_one_stable_idempotency_key():
    first = build_composition_idempotency_key(
        input_id="input-1", object_input_revision=3, versions=_versions()
    )
    reordered = dict(reversed(list(_versions().items())))
    second = build_composition_idempotency_key(
        input_id="input-1", object_input_revision=3, versions=reordered
    )
    changed = build_composition_idempotency_key(
        input_id="input-1", object_input_revision=3,
        versions=_versions(pricing_catalog="pricing-il-v2"),
    )

    assert first == second
    assert first.startswith("estimation-v2:")
    assert first != changed


def test_e11_name_only_change_never_creates_revision_or_recalculation():
    result = plan_object_revision(
        previous=PREVIOUS,
        current=_current(object_name="User approved display name"),
    )

    assert result == {
        "action": "update_display_name",
        "next_object_input_revision": 3,
        "active": True,
        "reuse_facts": True,
        "queue_extraction": False,
        "recalculate": False,
        "display_name_changed": True,
        "quantity_changed": False,
        "evidence_changed": False,
    }


def test_e12_quantity_ignore_and_restore_change_only_membership_or_aggregation():
    quantity = plan_object_revision(previous=PREVIOUS, current=_current(quantity=4))
    ignored = plan_object_revision(previous=PREVIOUS, current=_current(ignored=True))
    previously_ignored = {**PREVIOUS, "ignored": True}
    restored = plan_object_revision(previous=previously_ignored, current=_current())

    assert quantity["action"] == "reaggregate_quantity"
    assert quantity["queue_extraction"] is False and quantity["recalculate"] is True
    assert ignored["action"] == "deactivate" and ignored["active"] is False
    assert restored["action"] == "reactivate_reuse"
    assert restored["next_object_input_revision"] == 3
    assert restored["queue_extraction"] is False and restored["recalculate"] is True


def test_changed_evidence_is_the_only_file_review_change_that_queues_extraction():
    result = plan_object_revision(
        previous=PREVIOUS,
        current=_current(evidence_signature="evidence-v2"),
    )

    assert result["action"] == "reextract"
    assert result["next_object_input_revision"] == 4
    assert result["reuse_facts"] is False
    assert result["queue_extraction"] is True
