from astropy import units as u
from specutils import Spectrum

from spectral_app.ingestion.fits_loader import load_fits_spectrum


def test_load_fits_spectrum(tmp_path):
    wave = [500, 510, 520] * u.nm
    flux = [1, 2, 3] * u.Jy
    spectrum = Spectrum(flux=flux, spectral_axis=wave)

    path = tmp_path / "sample.fits"
    spectrum.write(path)

    record = load_fits_spectrum(path)

    assert record.metadata.description == "FITS spectrum"
    assert record.spectrum.spectral_axis.unit == u.nm
    assert record.spectrum.flux.unit == u.Jy
    assert record.spectrum.flux[0].value == 1
