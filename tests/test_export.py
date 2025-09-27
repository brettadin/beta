import json

from astropy import units as u
from specutils import Spectrum1D

from spectral_app.models import Annotation, ReferenceLine, SessionExport, SpectrumMetadata, SpectrumRecord
from spectral_app.utils.export import export_session


def test_export_session(tmp_path):
    spectral_axis = u.Quantity([500, 510], u.nm)
    flux = u.Quantity([1, 2], u.Jy)
    record = SpectrumRecord(
        identifier="sample",
        spectrum=Spectrum1D(flux=flux, spectral_axis=spectral_axis),
        metadata=SpectrumMetadata(source="test"),
    )
    export = SessionExport(
        spectra=[record],
        reference_lines=[ReferenceLine("H", 656.281 * u.nm, 1.0, "Hα")],
        annotations=[Annotation(656.281, "Balmer alpha", 1.2)],
        config={"note": "demo"},
        export_path=tmp_path / "session.json",
    )

    path = export_session(export)
    payload = json.loads(path.read_text())

    assert payload["spectra"][0]["metadata"]["source"] == "test"
    assert payload["reference_lines"][0]["element"] == "H"
    assert payload["annotations"][0]["note"] == "Balmer alpha"
