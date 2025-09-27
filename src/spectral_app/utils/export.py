"""Session export utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from astropy import units as u

from ..models import Annotation, ReferenceLine, SessionExport, SpectrumRecord


def _serialize_spectrum(record: SpectrumRecord) -> Dict[str, object]:
    canonical = record.to_canonical_units().spectrum
    flux_unit = canonical.flux.unit
    flux_unit_label = flux_unit.to_string() if hasattr(flux_unit, "to_string") else str(flux_unit)
    if flux_unit_label in {"", "1"}:
        flux_unit_label = "dimensionless"
    return {
        "id": record.identifier,
        "wavelength_nm": canonical.spectral_axis.value.tolist(),
        "flux": canonical.flux.value.tolist(),
        "flux_unit": flux_unit_label,
        "metadata": {
            "source": record.metadata.source,
            "target": record.metadata.target,
            "instrument": record.metadata.instrument,
            "observation_date": record.metadata.observation_date,
            "description": record.metadata.description,
            "extra": record.metadata.extra,
        },
    }


def _serialize_reference_line(line: ReferenceLine) -> Dict[str, object]:
    return {
        "element": line.element,
        "wavelength_nm": line.wavelength.to_value(u.nm),
        "intensity": line.intensity,
        "label": line.label,
    }


def _serialize_annotation(annotation: Annotation) -> Dict[str, object]:
    return {
        "wavelength_nm": annotation.wavelength,
        "flux": annotation.flux,
        "note": annotation.note,
    }


def export_session(export: SessionExport) -> Path:
    """Export the session state to JSON."""
    payload = {
        "spectra": [_serialize_spectrum(record) for record in export.spectra],
        "reference_lines": [_serialize_reference_line(line) for line in export.reference_lines],
        "annotations": [_serialize_annotation(annotation) for annotation in export.annotations],
        "config": export.config,
    }
    output_path = export.export_path or Path("spectral_session.json")
    output_path.write_text(json.dumps(payload, indent=2))
    return output_path
