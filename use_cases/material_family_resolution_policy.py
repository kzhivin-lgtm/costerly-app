"""Explicit, narrow compatibility policies for low-impact material families.

These rules never widen an exact material match. They provide a named canonical
anchor when the owner has approved that a family can be estimated at a broader
level. Each rule remains deterministic and rejects an explicit contradictory
object type, such as a caster being treated as a cabinet leg.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from use_cases.material_identity_resolution import normalize_material_phrase


@dataclass(frozen=True)
class LowImpactCompatibilityMatch:
    material_id: str
    policy_code: str


@dataclass(frozen=True)
class _LowImpactCompatibilityPolicy:
    code: str
    source_families: tuple[str, ...]
    target_global_canonical_id: str
    excluded_phrase_tokens: frozenset[str]


# This is deliberately a one-rule registry until more families are explicitly
# approved. The target is a catalog identity, not a supplier SKU or offer.
_POLICIES = (
    _LowImpactCompatibilityPolicy(
        code="adjustable_cabinet_leg_v1",
        source_families=("furniture leg", "adjustable cabinet leg"),
        target_global_canonical_id="GCM-V1-HW-ADJUSTABLE-CABINET-LEG-ADJUSTABLE-CABINET-LEG",
        excluded_phrase_tokens=frozenset({"caster", "castor", "wheel", "ролик", "колесо"}),
    ),
)


def resolve_low_impact_compatibility(
    *,
    phrase: str,
    material_family: str | None,
    materials: Sequence[Mapping[str, object]],
) -> LowImpactCompatibilityMatch | None:
    """Return one approved generic reference anchor, otherwise no match."""
    normalized_family = normalize_material_phrase(material_family)
    phrase_tokens = set(normalize_material_phrase(phrase).split())
    for policy in _POLICIES:
        if normalized_family not in {
            normalize_material_phrase(value) for value in policy.source_families
        }:
            continue
        if phrase_tokens & policy.excluded_phrase_tokens:
            return None
        matches = [
            row for row in materials
            if row.get("active", True)
            and str((row.get("specifications") or {}).get("global_canonical_id") or "")
            == policy.target_global_canonical_id
            and str(row.get("material_id") or "")
        ]
        if len(matches) == 1:
            return LowImpactCompatibilityMatch(
                material_id=str(matches[0]["material_id"]),
                policy_code=policy.code,
            )
    return None
