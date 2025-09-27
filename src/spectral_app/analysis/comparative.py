"""Comparative spectral analysis utilities."""
from __future__ import annotations

from typing import Optional

import numpy as np
from specutils import Spectrum1D  # type: ignore
from specutils.manipulation import LinearInterpolatedResampler  # type: ignore

from ..models import CANONICAL_FLUX_UNIT, CANONICAL_WAVELENGTH_UNIT, SpectrumMetadata, SpectrumRecord


def _resample_to(spectrum: Spectrum1D, target_axis) -> Spectrum1D:
    resampler = LinearInterpolatedResampler(extrapolation_treatment="nan_fill")
    return resampler(spectrum, target_axis)


def _combine_metadata(op: str, first: SpectrumMetadata, second: SpectrumMetadata) -> SpectrumMetadata:
    description = f"{op} of {first.source} and {second.source}"
    extra = {
        "operation": op,
        "primary_source": first.source,
        "secondary_source": second.source,
    }
    extra.update({f"primary_{k}": v for k, v in first.extra.items()})
    extra.update({f"secondary_{k}": v for k, v in second.extra.items()})
    return SpectrumMetadata(source=description, description=description, extra=extra)


def _canonical(record: SpectrumRecord) -> Spectrum1D:
    return record.spectrum


def compute_difference(first: SpectrumRecord, second: SpectrumRecord, identifier: Optional[str] = None) -> SpectrumRecord:
    """Compute a flux difference between two spectra."""
    target_axis = first.spectrum.spectral_axis
    resampled_second = _resample_to(second.spectrum, target_axis)
    flux = first.spectrum.flux - resampled_second.flux
    spectrum = Spectrum1D(flux=flux.to(CANONICAL_FLUX_UNIT), spectral_axis=target_axis.to(CANONICAL_WAVELENGTH_UNIT))
    metadata = _combine_metadata("difference", first.metadata, second.metadata)
    return SpectrumRecord(identifier or f"{first.identifier}-minus-{second.identifier}", spectrum, metadata)


def compute_ratio(first: SpectrumRecord, second: SpectrumRecord, identifier: Optional[str] = None, epsilon: float = 1e-12) -> SpectrumRecord:
    """Compute a flux ratio between two spectra."""
    target_axis = first.spectrum.spectral_axis
    resampled_second = _resample_to(second.spectrum, target_axis)
    safe_flux = resampled_second.flux.copy()
    safe_flux.value[np.abs(safe_flux.value) < epsilon] = epsilon
    ratio_flux = (first.spectrum.flux / safe_flux).decompose()
    spectrum = Spectrum1D(flux=ratio_flux, spectral_axis=target_axis.to(CANONICAL_WAVELENGTH_UNIT))
    metadata = _combine_metadata("ratio", first.metadata, second.metadata)
    return SpectrumRecord(identifier or f"{first.identifier}-over-{second.identifier}", spectrum, metadata)
