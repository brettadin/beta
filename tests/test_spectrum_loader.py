from pathlib import Path
import sys

import numpy as np
from astropy import units as u
from specutils import Spectrum1D

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jwst_viewer.spectrum_loader import JWSTSpectrumLoader


def test_convert_units_round_trip_jy_to_cgs():
    loader = JWSTSpectrumLoader(
        preferred_flux_unit=u.erg / (u.cm**2 * u.s * u.AA),
        preferred_wave_unit=u.AA,
    )

    wavelengths = np.linspace(1, 5, 5) * u.micron
    flux = np.full(wavelengths.shape, 3.0) * u.Jy

    spectrum = Spectrum1D(flux=flux, spectral_axis=wavelengths)

    converted, verified = loader.convert_units(
        spectrum,
        flux_unit=u.erg / (u.cm**2 * u.s * u.AA),
        spectral_axis_unit=u.AA,
    )

    assert converted.flux.unit.is_equivalent(u.erg / (u.cm**2 * u.s * u.AA))
    assert converted.spectral_axis.unit.is_equivalent(u.AA)
    assert verified is True
