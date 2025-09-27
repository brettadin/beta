"""Spectral analysis application package."""
from .models import (
    Annotation,
    ReferenceLine,
    SessionExport,
    SpectrumMetadata,
    SpectrumRecord,
    CANONICAL_FLUX_UNIT,
    CANONICAL_WAVELENGTH_UNIT,
)


def run_app() -> None:
    """Launch the Streamlit interface."""
    from .interface.streamlit_app import run

    run()

__all__ = [
    "Annotation",
    "ReferenceLine",
    "SessionExport",
    "SpectrumMetadata",
    "SpectrumRecord",
    "CANONICAL_FLUX_UNIT",
    "CANONICAL_WAVELENGTH_UNIT",
    "run_app",
]
