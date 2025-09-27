"""Helpers for interpreting units from text labels."""
from __future__ import annotations

import re
from typing import Optional

from astropy import units as u

UNIT_KEYWORDS = {
    "angstrom": u.AA,
    "ang": u.AA,
    "aa": u.AA,
    "nm": u.nm,
    "nanometer": u.nm,
    "micron": u.micron,
    "um": u.micron,
    "hz": u.Hz,
    "jy": u.Jy,
    "erg": u.erg / (u.s * u.cm ** 2),
    "w": u.W,
    "watt": u.W,
    "watts": u.W,
    "s": u.s,
    "sec": u.s,
    "second": u.s,
    "seconds": u.s,
    "m": u.m,
    "m2": u.m ** 2,
    "m3": u.m ** 3,
    "cm": u.cm,
    "cm2": u.cm ** 2,
    "cm3": u.cm ** 3,
}

TOKEN_UNIT_MAP = {
    "angstrom": u.AA,
    "ang": u.AA,
    "aa": u.AA,
    "nm": u.nm,
    "nanometer": u.nm,
    "micron": u.micron,
    "um": u.micron,
    "hz": u.Hz,
    "jy": u.Jy,
    "erg": u.erg,
    "w": u.W,
    "watt": u.W,
    "watts": u.W,
    "s": u.s,
    "sec": u.s,
    "second": u.s,
    "seconds": u.s,
    "m": u.m,
    "m2": u.m ** 2,
    "m3": u.m ** 3,
    "cm": u.cm,
    "cm2": u.cm ** 2,
    "cm3": u.cm ** 3,
}

TOKEN_SKIP_WORDS = {"per", "of", "to", "in", "at"}

UNIT_PATTERN = re.compile(r"\((?P<label>[^\)]+)\)|\[(?P<bracket>[^\]]+)\]", re.IGNORECASE)


def _extract_tokens(text: str) -> list[str]:
    """Return lowercase tokens extracted from ``text``."""

    cleaned = text.lower()
    tokens = re.findall(r"[a-z0-9]+", cleaned)
    merged: list[str] = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        # Merge sequences like "m", "2" into "m2" if that composite is known.
        if idx + 1 < len(tokens):
            combined = token + tokens[idx + 1]
            if combined in UNIT_KEYWORDS or combined in TOKEN_UNIT_MAP:
                merged.append(combined)
                idx += 2
                continue
        merged.append(token)
        idx += 1
    return merged


def _unit_from_composite(tokens: list[str]) -> Optional[u.Unit]:
    """Try to build a composite unit from the ordered ``tokens``."""

    unit_sequence: list[u.Unit] = []
    for token in tokens:
        if token in TOKEN_SKIP_WORDS:
            continue
        unit = TOKEN_UNIT_MAP.get(token)
        if unit is not None:
            unit_sequence.append(unit)

    if len(unit_sequence) < 2:
        return None

    composite = unit_sequence[0]
    for unit in unit_sequence[1:]:
        composite = composite / unit
    return composite


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
    cleaned = unit_token.strip()
    tokens = _extract_tokens(cleaned)

    if not tokens:
        return None

    normalized = "".join(tokens)
    if normalized in UNIT_KEYWORDS:
        return UNIT_KEYWORDS[normalized]

    composite = _unit_from_composite(tokens)
    if composite is not None:
        return composite

    for token in tokens:
        if token in UNIT_KEYWORDS:
            return UNIT_KEYWORDS[token]
    try:
        return u.Unit(cleaned)
    except Exception:
        return None
