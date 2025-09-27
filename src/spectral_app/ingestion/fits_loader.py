"""FITS ingestion utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from astropy.io import fits
from astropy import units as u
from specutils import Spectrum1D  # type: ignore

from ..models import CANONICAL_FLUX_UNIT, CANONICAL_WAVELENGTH_UNIT, SpectrumMetadata, SpectrumRecord


def _extract_metadata(header: fits.Header) -> Dict[str, str]:
    keys = [
        "OBJECT",
        "DATE-OBS",
        "TELESCOP",
        "INSTRUME",
        "DETECTOR",
        "OBSERVER",
        "ORIGIN",
    ]
    return {key.lower(): str(header.get(key, "")) for key in keys if key in header}


def load_fits_spectrum(path: Path | str, identifier: Optional[str] = None) -> SpectrumRecord:
    """Load a 1D spectrum from a FITS file."""
    spectrum = Spectrum1D.read(path)

    spectral_axis = spectrum.spectral_axis.to(CANONICAL_WAVELENGTH_UNIT)
    flux = spectrum.flux.to(CANONICAL_FLUX_UNIT)
    canonical = Spectrum1D(flux=flux, spectral_axis=spectral_axis)

    with fits.open(path) as hdul:
        header = hdul[0].header
        metadata_entries = _extract_metadata(header)
    metadata = SpectrumMetadata(
        source=str(path),
        target=metadata_entries.get("object"),
        instrument=metadata_entries.get("instrume"),
        observation_date=metadata_entries.get("date-obs"),
        description="FITS spectrum",
        extra=metadata_entries,
    )

    return SpectrumRecord(identifier=identifier or Path(str(path)).stem, spectrum=canonical, metadata=metadata)
