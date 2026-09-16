from __future__ import annotations

import re


_LOCAL_PART = re.compile(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+\Z")
_DOMAIN_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
_TOP_LEVEL_DOMAIN = re.compile(r"(?:[A-Za-z]{2,63}|xn--[A-Za-z0-9-]{2,59})\Z")


def is_valid_email_address(value: str) -> bool:
    """Validate the useful public-email shape, not mailbox ownership or DNS."""
    address = value.strip()
    if len(address) > 254 or address.count("@") != 1:
        return False
    local, domain = address.split("@")
    if not local or len(local.encode("utf-8")) > 64:
        return False
    if not _LOCAL_PART.fullmatch(local) or local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    if len(ascii_domain) > 253:
        return False
    labels = ascii_domain.split(".")
    return (
        len(labels) >= 2
        and all(_DOMAIN_LABEL.fullmatch(label) for label in labels)
        and bool(_TOP_LEVEL_DOMAIN.fullmatch(labels[-1]))
    )
