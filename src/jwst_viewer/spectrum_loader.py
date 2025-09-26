"""Spectrum loading utilities for JWST Level-2 products."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from astropy import units as u
from astropy.io import fits
from specutils import Spectrum1D  # type: ignore


@dataclass
class SpectrumBundle:
    """Container for the parsed spectrum and associated metadata."""

    spectrum: Spectrum1D
    header_metadata: Dict[str, Any]
    round_trip_verified: bool


class JWSTSpectrumLoader:
    """Parse JWST spectral products into :class:`specutils.Spectrum1D`."""

    def __init__(self, *, preferred_flux_unit: u.Unit = u.Jy, preferred_wave_unit: u.Unit = u.micron) -> None:
        self.preferred_flux_unit = preferred_flux_unit
        self.preferred_wave_unit = preferred_wave_unit

    def load(self, file_path: Path | str) -> SpectrumBundle:
        """Load a JWST spectral FITS file into memory."""

        file_path = Path(file_path)
        # Spectrum1D.read is the recommended API from the specutils docs:
        # https://specutils.readthedocs.io/en/stable/spectrum1d.html#reading-from-files
        spectrum = Spectrum1D.read(file_path)

        header_metadata = self._extract_header_metadata(file_path)
        converted_spectrum, verified = self._apply_preferred_units(spectrum)
        return SpectrumBundle(
            spectrum=converted_spectrum,
            header_metadata=header_metadata,
            round_trip_verified=verified,
        )

    def _apply_preferred_units(self, spectrum: Spectrum1D) -> Tuple[Spectrum1D, bool]:
        """Convert the spectrum into the preferred units while checking reversibility."""

        converted = spectrum
        if spectrum.flux.unit != self.preferred_flux_unit:
            converted = converted.to(unit=self.preferred_flux_unit)
        if spectrum.spectral_axis.unit != self.preferred_wave_unit:
            converted = Spectrum1D(
                flux=converted.flux,
                spectral_axis=converted.spectral_axis.to(self.preferred_wave_unit),
            )

        verified = self._verify_round_trip(converted)
        return converted, verified

    def _verify_round_trip(self, spectrum: Spectrum1D, *, atol: float = 1e-12) -> bool:
        """Ensure unit conversions round-trip without numerical drift."""

        flux_back = spectrum.flux.to(spectrum.flux.unit).value
        spectral_back = spectrum.spectral_axis.to(spectrum.spectral_axis.unit).value
        flux_original = spectrum.flux.value
        spectral_original = spectrum.spectral_axis.value
        flux_close = np.allclose(flux_back, flux_original, atol=atol, rtol=1e-9)
        spectral_close = np.allclose(spectral_back, spectral_original, atol=atol, rtol=1e-9)
        return bool(flux_close and spectral_close)

    def _extract_header_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Collect the header keywords required for provenance."""

        metadata: Dict[str, Any] = {}
        with fits.open(file_path) as hdul:
            header = hdul[0].header
            metadata.update({
                "telescope": header.get("TELESCOP"),
                "instrument": header.get("INSTRUME"),
                "program_id": header.get("PROGRAM"),
                "observation": header.get("OBS_ID"),
                "visit": header.get("VISIT"),
                "target": header.get("TARGNAME"),
                "pipeline_version": header.get("CAL_VER"),
            })
        return metadata

    def convert_units(
        self,
        spectrum: Spectrum1D,
        *,
        flux_unit: Optional[u.Unit] = None,
        spectral_axis_unit: Optional[u.Unit] = None,
    ) -> Tuple[Spectrum1D, bool]:
        """Return a new spectrum converted to the requested units plus round-trip status."""

        flux_unit = flux_unit or self.preferred_flux_unit
        spectral_axis_unit = spectral_axis_unit or self.preferred_wave_unit
        converted = Spectrum1D(
            flux=spectrum.flux.to(flux_unit),
            spectral_axis=spectrum.spectral_axis.to(spectral_axis_unit),
        )
        verified = self._verify_round_trip(converted)
        return converted, verified
