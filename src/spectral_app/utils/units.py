"""Helpers for interpreting units from text labels."""
from __future__ import annotations

import re
from typing import Optional

from astropy import units as u

UNIT_KEYWORDS = {
    "angstrom": u.AA,
    "ang": u.AA,
    "nm": u.nm,
    "nanometer": u.nm,
    "micron": u.micron,
    "um": u.micron,
    "hz": u.Hz,
    "jy": u.Jy,
    "erg": u.erg / (u.s * u.cm ** 2),
}

UNIT_PATTERN = re.compile(r"\((?P<label>[^\)]+)\)|\[(?P<bracket>[^\]]+)\]", re.IGNORECASE)


def infer_unit_from_label(label: str) -> Optional[u.Unit]:
    """Return an astropy unit inferred from a column label."""
    match = UNIT_PATTERN.search(label)
    unit_token = None
    if match:
        unit_token = match.group("label") or match.group("bracket")
    else:
        unit_token = label
    if unit_token is None:
        return None
    cleaned = unit_token.strip().lower()
    if cleaned in UNIT_KEYWORDS:
        return UNIT_KEYWORDS[cleaned]
    for key, unit in UNIT_KEYWORDS.items():
        if cleaned.endswith(key) or key in cleaned:
            return unit
    try:
        return u.Unit(cleaned)
    except Exception:
        return None
