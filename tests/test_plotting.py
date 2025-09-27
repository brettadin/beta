import pytest
from astropy import units as u
from specutils import Spectrum1D

from spectral_app.models import SpectrumMetadata, SpectrumRecord
from spectral_app.plotting.plotly_view import add_spectrum_trace, create_base_figure


def test_add_spectrum_trace():
    spectral_axis = u.Quantity([500, 505, 510], u.nm)
    flux = u.Quantity([1, 2, 3], u.Jy)
    record = SpectrumRecord(
        identifier="sample",
        spectrum=Spectrum1D(flux=flux, spectral_axis=spectral_axis),
        metadata=SpectrumMetadata(source="test"),
    )

    fig = create_base_figure()
    add_spectrum_trace(fig, record, max_points=3)

    assert len(fig.data) == 1
    scatter = fig.data[0]
    assert scatter.x[0] == pytest.approx(500)
    assert scatter.y[2] == pytest.approx(3)
