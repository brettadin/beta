import pytest
from astropy import units as u
from specutils import Spectrum

from spectral_app.analysis.comparative import compute_difference, compute_ratio
from spectral_app.models import SpectrumMetadata, SpectrumRecord


def _make_record(identifier: str, flux_values):
    spectral_axis = u.Quantity([500, 510, 520], u.nm)
    flux = u.Quantity(flux_values, u.Jy)
    spectrum = Spectrum(flux=flux, spectral_axis=spectral_axis)
    metadata = SpectrumMetadata(source=identifier, description="test")
    return SpectrumRecord(identifier=identifier, spectrum=spectrum, metadata=metadata)


def test_compute_difference():
    first = _make_record("A", [2, 4, 6])
    second = _make_record("B", [1, 1, 1])

    result = compute_difference(first, second)

    assert result.metadata.extra["operation"] == "difference"
    assert result.spectrum.flux[0].value == pytest.approx(1)


def test_compute_ratio_handles_zero():
    first = _make_record("A", [2, 4, 6])
    second = _make_record("B", [0, 1, 2])

    result = compute_ratio(first, second)

    assert result.spectrum.flux[0].value > 0
    assert result.spectrum.flux[1].value == pytest.approx(4)
