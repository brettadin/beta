"""Utilities for loading spectra from ASCII/CSV files."""
from __future__ import annotations

from pathlib import Path
from typing import IO, Dict, Iterable, Optional, Tuple

import numpy as np
from astropy import units as u
from specutils import Spectrum1D  # type: ignore

try:  # Optional dependency for rich parsing
    import pandas as pd
except ImportError:  # pragma: no cover - fallback path
    pd = None

from ..models import CANONICAL_FLUX_UNIT, CANONICAL_WAVELENGTH_UNIT, SpectrumMetadata, SpectrumRecord
from ..utils.units import infer_unit_from_label


COLUMN_PRIORITY = (
    "wavelength",
    "lambda",
    "wave",
    "wl",
)

FLUX_PRIORITY = (
    "flux",
    "intensity",
    "power",
    "counts",
)


def _read_table(path: Path | str | IO[str]) -> Tuple[Dict[str, np.ndarray], str]:
    """Read a delimited text file into column-oriented arrays."""
    if isinstance(path, (str, Path)):
        source = str(path)
        data_source = path
    else:
        source = "in-memory"
        data_source = path

    if pd is not None:
        try:
            df = pd.read_csv(data_source, sep=None, engine="python", comment="#")
        except pd.errors.ParserError:
            df = pd.read_csv(data_source, delim_whitespace=True, comment="#")
        if df.columns.tolist() == list(range(len(df.columns))):
            first_row = df.iloc[0]
            if not np.all(pd.to_numeric(first_row, errors="coerce").notna()):
                df = pd.read_csv(data_source, sep=None, engine="python", header=None, comment="#")
        df = df.dropna(axis=1, how="all")
        columns = list(df.columns.astype(str))
        column_data = {col: df[col].astype(float).to_numpy() for col in columns}
        return column_data, source

    # Fallback parser using numpy for environments without pandas.
    import re
    import csv

    if isinstance(data_source, (str, Path)):
        text = Path(data_source).read_text()
    else:
        text = data_source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8")

    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        raise ValueError("No data rows detected in ASCII spectrum")
    delimiter = "," if "," in lines[0] else ("\t" if "\t" in lines[0] else None)
    if delimiter is None:
        splitter = re.compile(r"\s+")
        rows = [splitter.split(line.strip()) for line in lines]
    else:
        reader = csv.reader(lines, delimiter=delimiter)
        rows = list(reader)

    header_tokens = rows[0]
    has_header = any(any(c.isalpha() for c in token) for token in header_tokens)
    data_rows = rows[1:] if has_header else rows
    columns = header_tokens if has_header else [f"col{i}" for i in range(len(header_tokens))]
    array = np.array([[float(value) for value in row] for row in data_rows], dtype=float)
    column_data = {col: array[:, idx] for idx, col in enumerate(columns)}
    return column_data, source


def _resolve_column(name_candidates: Iterable[str], columns: Iterable[str]) -> Optional[str]:
    lowered = {col.lower(): col for col in columns}
    for candidate in name_candidates:
        if candidate in lowered:
            return lowered[candidate]
    for col in columns:
        if any(col.lower().startswith(prefix) for prefix in name_candidates):
            return col
    return None


def _select_columns(columns: Iterable[str]) -> Tuple[str, str]:
    columns = list(columns)
    wave_col = _resolve_column(COLUMN_PRIORITY, columns)
    flux_col = _resolve_column(FLUX_PRIORITY, columns)
    if wave_col is None:
        wave_col = columns[0]
    if flux_col is None:
        flux_candidates = [col for col in columns if col != wave_col]
        flux_col = flux_candidates[0] if flux_candidates else wave_col
    return wave_col, flux_col


def load_ascii_spectrum(path: Path | str | IO[str], identifier: Optional[str] = None) -> SpectrumRecord:
    """Load a spectrum from an ASCII/CSV file and convert to canonical units."""
    columns, source = _read_table(path)
    wave_col, flux_col = _select_columns(columns.keys())

    wave_unit = infer_unit_from_label(str(wave_col)) or CANONICAL_WAVELENGTH_UNIT
    flux_unit = infer_unit_from_label(str(flux_col)) or CANONICAL_FLUX_UNIT

    wavelengths = np.asarray(columns[wave_col], dtype=float) * wave_unit
    flux = np.asarray(columns[flux_col], dtype=float) * flux_unit

    spectrum = Spectrum1D(flux=flux.to(CANONICAL_FLUX_UNIT), spectral_axis=wavelengths.to(CANONICAL_WAVELENGTH_UNIT))

    metadata = SpectrumMetadata(
        source=source,
        description="ASCII spectrum",
        extra={"wave_column": wave_col, "flux_column": flux_col},
    )
    record = SpectrumRecord(identifier=identifier or Path(source).stem, spectrum=spectrum, metadata=metadata)
    return record
