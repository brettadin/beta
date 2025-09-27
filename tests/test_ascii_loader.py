from astropy import units as u
import pytest

from spectral_app.ingestion.ascii_loader import load_ascii_spectrum


def test_load_ascii_with_units(tmp_path):
    data = "wavelength (Angstrom),flux (Jy)\n5000,1.0\n5100,1.5\n"
    path = tmp_path / "sample.csv"
    path.write_text(data)

    record = load_ascii_spectrum(path)

    spectrum = record.spectrum
    assert spectrum.spectral_axis.unit.is_equivalent(u.nm)
    assert spectrum.spectral_axis[0].to_value(u.nm) == pytest.approx(500)
    assert spectrum.flux.unit.is_equivalent(u.Jy)
    assert spectrum.flux[1].value == pytest.approx(1.5)
