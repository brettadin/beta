from astropy import units as u

from spectral_app.datafetch import nist


def test_fetch_reference_lines_fallback(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(nist, "_query_vizier", _raise)

    lines = nist.fetch_reference_lines("H", 400 * u.nm, 700 * u.nm, intensity_threshold=0.5)

    assert lines
    assert all(line.wavelength.unit == u.nm for line in lines)
