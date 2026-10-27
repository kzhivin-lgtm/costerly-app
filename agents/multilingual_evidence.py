"""Small, dependency-free gate for multilingual evidence fallback.

This module intentionally does not name a language or contain language-specific
business aliases.  It merely detects when Fusion carries enough alphabetic text
outside Costerly's primary English, Hebrew and Russian flows to justify a
bounded model read of the already-owned facts.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


DEFAULT_NON_PRIMARY_LETTER_TRIGGER = 12


def count_non_primary_letters(values: Iterable[Any]) -> int:
    """Count alphabetic characters outside ASCII, Hebrew and Cyrillic scripts."""
    count = 0
    for value in values:
        for character in str(value or ""):
            if not character.isalpha():
                continue
            codepoint = ord(character)
            is_primary = (
                character.isascii()
                or 0x0400 <= codepoint <= 0x052F  # Cyrillic incl. extensions.
                or 0x0590 <= codepoint <= 0x05FF  # Hebrew.
            )
            if not is_primary:
                count += 1
    return count


def multilingual_fallback_signal(
    values: Iterable[Any], *, threshold: int = DEFAULT_NON_PRIMARY_LETTER_TRIGGER,
) -> dict[str, int | bool]:
    """Return an auditable, content-only decision for the model fallback."""
    non_primary_letter_count = count_non_primary_letters(values)
    return {
        "eligible": non_primary_letter_count >= threshold,
        "non_primary_letter_count": non_primary_letter_count,
        "threshold": threshold,
    }
