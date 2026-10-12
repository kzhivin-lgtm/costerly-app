from use_cases.material_family_resolution_policy import resolve_low_impact_compatibility


TARGET_ID = "36dbe342-8535-57ce-b119-12fde85d4693"
TARGET_GLOBAL_ID = "GCM-V1-HW-ADJUSTABLE-CABINET-LEG-ADJUSTABLE-CABINET-LEG"


def _target_material():
    return {
        "material_id": TARGET_ID,
        "active": True,
        "canonical_name": "Adjustable cabinet leg",
        "specifications": {"global_canonical_id": TARGET_GLOBAL_ID},
    }


def test_low_impact_furniture_leg_gets_the_approved_generic_reference_anchor():
    result = resolve_low_impact_compatibility(
        phrase="Furniture Leg 100 mm Blum",
        material_family="furniture leg",
        materials=(_target_material(),),
    )

    assert result is not None
    assert result.material_id == TARGET_ID
    assert result.policy_code == "adjustable_cabinet_leg_v1"


def test_low_impact_policy_never_turns_a_caster_into_a_cabinet_leg():
    result = resolve_low_impact_compatibility(
        phrase="Furniture caster 100 mm",
        material_family="furniture leg",
        materials=(_target_material(),),
    )

    assert result is None


def test_low_impact_policy_requires_one_unambiguous_target():
    result = resolve_low_impact_compatibility(
        phrase="Furniture leg",
        material_family="furniture leg",
        materials=(_target_material(), _target_material()),
    )

    assert result is None
