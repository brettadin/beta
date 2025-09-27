"""Tests for unit inference helpers."""

from astropy import units as u

from spectral_app.utils.units import infer_unit_from_label


def test_irradiance_unit_uses_composite_flux_density():
    """Labels with composite tokens should build flux-density style units."""

    unit = infer_unit_from_label("irradiance_w_m2_nm")
    assert unit is not None
    assert unit.is_equivalent(u.W / (u.m ** 2 * u.nm))
    assert not unit.is_equivalent(u.nm)


def test_wavelength_label_still_maps_to_wavelength():
    """Basic wavelength labels should continue to map to wavelength units."""

    unit = infer_unit_from_label("wavelength_nm")
    assert unit == u.nm
