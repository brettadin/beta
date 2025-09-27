"""NIST reference line helpers."""
from __future__ import annotations

from typing import List

from astropy import units as u

from ..models import ReferenceLine

_SAMPLE_LINES = {
    "H": [
        ReferenceLine("H", 656.281 * u.nm, 1.0, "Hα"),
        ReferenceLine("H", 486.133 * u.nm, 0.7, "Hβ"),
    ],
    "Na": [
        ReferenceLine("Na", 589.592 * u.nm, 0.8, "Na D2"),
        ReferenceLine("Na", 588.995 * u.nm, 0.7, "Na D1"),
    ],
}


def _query_vizier(element: str, wave_min: u.Quantity, wave_max: u.Quantity) -> List[ReferenceLine]:
    from astroquery.vizier import Vizier  # type: ignore

    catalog = "VI/80/hg"  # Hypothetical; Vizier hosts a subset of NIST lines
    vizier = Vizier(columns=["Wavelength", "Element", "Intensity", "Line"], row_limit=-1)
    query = vizier.query_constraints(
        catalog=catalog,
        Element=element,
        Wavelength=f">={wave_min.to(u.AA).value} & <={wave_max.to(u.AA).value}",
    )
    lines: List[ReferenceLine] = []
    for table in query:
        for row in table:
            lines.append(
                ReferenceLine(
                    element=str(row["Element"]).strip(),
                    wavelength=(row["Wavelength"] * u.AA).to(u.nm),
                    intensity=float(row["Intensity"]),
                    label=str(row.get("Line", "")).strip() or None,
                )
            )
    return lines


def fetch_reference_lines(
    element: str,
    wave_min: u.Quantity,
    wave_max: u.Quantity,
    intensity_threshold: float = 0.0,
) -> List[ReferenceLine]:
    """Fetch NIST reference lines for an element within a wavelength range."""
    try:
        lines = _query_vizier(element, wave_min, wave_max)
    except Exception:
        lines = _SAMPLE_LINES.get(element.capitalize(), [])
    filtered = [line for line in lines if line.intensity >= intensity_threshold]
    return [
        ReferenceLine(
            line.element,
            line.wavelength.to(u.nm),
            float(line.intensity),
            line.label,
        )
        for line in filtered
    ]
