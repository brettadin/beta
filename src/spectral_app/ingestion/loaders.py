"""High-level spectrum loaders."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from astropy import units as u

from ..models import SpectrumRecord
from .ascii_loader import load_ascii_spectrum
from .fits_loader import load_fits_spectrum

SUPPORTED_EXTENSIONS = {".csv", ".txt", ".tsv", ".dat", ".fits", ".fit", ".fts"}


def load_spectrum(path: Path | str, identifier: str | None = None) -> SpectrumRecord:
    """Load a spectrum from the appropriate loader based on the file extension."""
    extension = Path(str(path)).suffix.lower()
    if extension in {".fits", ".fit", ".fts"}:
        return load_fits_spectrum(path, identifier=identifier)
    if extension in {".csv", ".txt", ".tsv", ".dat"}:
        return load_ascii_spectrum(path, identifier=identifier)
    raise ValueError(f"Unsupported spectrum format: {extension}")


def load_multiple(paths: Iterable[Path | str]) -> List[SpectrumRecord]:
    return [load_spectrum(path) for path in paths]
