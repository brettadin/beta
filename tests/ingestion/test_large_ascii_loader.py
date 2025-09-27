import json
import numpy as np

from spectral_app.ingestion.ascii_loader import load_ascii_spectrum


def test_load_ascii_handles_multi_million_rows(tmp_path):
    total_points = 2_000_000
    wavelengths = np.linspace(400.0, 800.0, total_points, dtype=np.float64)
    flux = np.sin(np.linspace(0, 8 * np.pi, total_points, dtype=np.float64)) + 5.0

    path = tmp_path / "multi_million.csv"
    with path.open("w", encoding="utf-8") as handle:
        handle.write("wavelength (nm),flux (Jy)\n")
        np.savetxt(
            handle,
            np.column_stack((wavelengths, flux)),
            fmt="%.6f",
            delimiter=",",
        )

    record = load_ascii_spectrum(path)
    spectrum = record.spectrum

    assert len(spectrum.spectral_axis) == total_points
    assert len(spectrum.flux) == total_points

    downsampled = spectrum.meta.get("downsampled_tiers")
    assert downsampled, "Downsampled tiers should be generated for large spectra"
    for size, payload in downsampled.items():
        wave_preview = payload["wavelength"]
        flux_preview = payload["flux"]
        assert len(wave_preview) <= int(size)
        assert len(wave_preview) == len(flux_preview)

    extra = record.metadata.extra
    assert extra.get("row_count") == str(total_points)

    stats = json.loads(extra["column_statistics"])
    assert "wavelength (nm)" in stats
    assert "flux (Jy)" in stats
