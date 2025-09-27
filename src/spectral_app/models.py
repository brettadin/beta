"""Core data models for the spectral analysis application."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from astropy import units as u
from specutils import Spectrum  # type: ignore


CANONICAL_WAVELENGTH_UNIT = u.nm
CANONICAL_FLUX_UNIT = u.Jy


@dataclass
class SpectrumMetadata:
    """Metadata describing the provenance of a spectrum."""

    source: str
    target: Optional[str] = None
    instrument: Optional[str] = None
    observation_date: Optional[str] = None
    description: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass
class SpectrumRecord:
    """Bundle tying a Spectrum instance to its metadata."""

    identifier: str
    spectrum: Spectrum
    metadata: SpectrumMetadata

    def to_canonical_units(self) -> "SpectrumRecord":
        """Return a copy of the record in the canonical display units."""
        spectral_axis = self.spectrum.spectral_axis.to(CANONICAL_WAVELENGTH_UNIT)
        flux = self.spectrum.flux.to(CANONICAL_FLUX_UNIT)
        canonical = Spectrum(flux=flux, spectral_axis=spectral_axis)
        return SpectrumRecord(identifier=self.identifier, spectrum=canonical, metadata=self.metadata)


@dataclass
class ReferenceLine:
    """Representation of a reference spectral line."""

    element: str
    wavelength: u.Quantity
    intensity: float
    label: Optional[str] = None


@dataclass
class Annotation:
    """User-supplied annotation anchored to a wavelength (and optionally flux)."""

    wavelength: float
    note: str
    flux: Optional[float] = None


@dataclass
class SessionExport:
    """Serializable manifest capturing the current analysis session."""

    spectra: List[SpectrumRecord]
    reference_lines: List[ReferenceLine]
    annotations: List[Annotation]
    config: Dict[str, str] = field(default_factory=dict)
    export_path: Optional[Path] = None
