"""Utilities for loading spectra from ASCII/CSV files."""
from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Dict, Iterable, Iterator, List, Optional, Tuple

import numpy as np
from astropy import units as u
from astropy.units import UnitConversionError
from specutils import Spectrum  # type: ignore

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


logger = logging.getLogger(__name__)

CHUNK_SIZE = 200_000
DOWNSAMPLE_TIERS = (512, 2048, 8192)


@dataclass
class ColumnStats:
    """Streaming statistics for a numeric column."""

    count: int = 0
    sum: float = 0.0
    sum_sq: float = 0.0
    min: float = field(default_factory=lambda: float("inf"))
    max: float = field(default_factory=lambda: float("-inf"))

    def update(self, values: np.ndarray) -> None:
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return
        finite_min = float(finite.min())
        finite_max = float(finite.max())
        if self.count == 0:
            self.min = finite_min
            self.max = finite_max
        else:
            self.min = min(self.min, finite_min)
            self.max = max(self.max, finite_max)
        self.count += int(finite.size)
        self.sum += float(finite.sum())
        self.sum_sq += float(np.square(finite).sum())

    def as_dict(self) -> Dict[str, float]:
        if self.count == 0:
            return {}
        mean = self.sum / self.count
        variance = max(self.sum_sq / self.count - mean**2, 0.0)
        std = math.sqrt(variance)
        return {
            "count": float(self.count),
            "min": float(self.min),
            "max": float(self.max),
            "mean": float(mean),
            "std": float(std),
        }


class RowReservoir:
    """Reservoir sampler maintaining downsample tiers for streaming data."""

    def __init__(self, tiers: Iterable[int], seed: int = 0) -> None:
        self._tiers: Dict[int, List[Dict[str, float]]] = {size: [] for size in tiers}
        self._rng = np.random.default_rng(seed)
        self._total_seen = 0

    def add(self, row: Dict[str, float]) -> None:
        if not row:
            return
        self._total_seen += 1
        for size, bucket in self._tiers.items():
            if len(bucket) < size:
                bucket.append(dict(row))
            else:
                idx = int(self._rng.integers(0, self._total_seen))
                if idx < size:
                    bucket[idx] = dict(row)

    def export(self) -> Dict[int, List[Dict[str, float]]]:
        return {size: [dict(row) for row in rows] for size, rows in self._tiers.items()}


class ChunkAccumulator:
    """Accumulate columnar data and analytics while streaming chunks."""

    def __init__(self, columns: Iterable[str]) -> None:
        column_list = list(columns)
        self.columns: List[str] = column_list
        self.buffers: Dict[str, List[np.ndarray]] = {col: [] for col in column_list}
        self.pending_nans: Dict[str, int] = defaultdict(int)
        self.column_has_numeric: Dict[str, bool] = defaultdict(bool)
        self.stats: Dict[str, ColumnStats] = {col: ColumnStats() for col in column_list}
        self.reservoir = RowReservoir(DOWNSAMPLE_TIERS)
        self.row_count: int = 0

    def process_chunk(self, chunk: np.ndarray, columns: List[str]) -> None:
        if chunk.size == 0:
            return
        chunk_len = chunk.shape[0]
        self.row_count += chunk_len
        finite_mask = np.isfinite(chunk)
        for idx, col in enumerate(columns):
            column_values = chunk[:, idx]
            if np.any(finite_mask[:, idx]):
                if self.pending_nans[col]:
                    pending = np.full(self.pending_nans[col], np.nan, dtype=float)
                    self.buffers[col].append(pending)
                    self.pending_nans[col] = 0
                self.buffers[col].append(column_values)
                self.column_has_numeric[col] = True
                self.stats[col].update(column_values)
            else:
                self.pending_nans[col] += chunk_len

        for row_vals, row_mask in zip(chunk, finite_mask):
            row_dict = {
                columns[idx]: float(row_vals[idx])
                for idx, keep in enumerate(row_mask)
                if keep
            }
            if len(row_dict) >= 2:
                self.reservoir.add(row_dict)

    def finalize(
        self,
    ) -> Tuple[
        Dict[str, np.ndarray],
        List[str],
        Dict[str, Dict[str, float]],
        Dict[int, List[Dict[str, float]]],
        int,
    ]:
        column_data: Dict[str, np.ndarray] = {}
        skipped_columns: List[str] = []
        for col in self.columns:
            if self.column_has_numeric[col]:
                if self.pending_nans[col]:
                    pending = np.full(self.pending_nans[col], np.nan, dtype=float)
                    self.buffers[col].append(pending)
                    self.pending_nans[col] = 0
                column_data[col] = np.concatenate(self.buffers[col], dtype=float)
            else:
                skipped_columns.append(col)
        stats = {
            col: data
            for col, data in ((col, self.stats[col].as_dict()) for col in self.columns)
            if data
        }
        return column_data, skipped_columns, stats, self.reservoir.export(), self.row_count


def _rewind_if_possible(handle: IO[str]) -> None:
    if hasattr(handle, "seek"):
        handle.seek(0)


def _iter_clean_lines(stream: IO[str]) -> Iterator[str]:
    for line in stream:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        yield stripped


def _read_table(path: Path | str | IO[str]) -> Tuple[Dict[str, np.ndarray], str, Dict[str, object]]:
    """Read a delimited text file into column-oriented arrays with analytics."""
    if isinstance(path, (str, Path)):
        source = str(path)
        data_source = path
    else:
        source = "in-memory"
        data_source = path

    if pd is not None:
        read_kwargs: Dict[str, object] = {"comment": "#"}
        try:
            sample = pd.read_csv(data_source, sep=None, engine="python", nrows=5, **read_kwargs)
            delimiter_mode = "inferred"
        except pd.errors.ParserError:
            sample = pd.read_csv(data_source, delim_whitespace=True, nrows=5, **read_kwargs)
            delimiter_mode = "whitespace"

        header_option: Optional[int] | str = "infer"
        sample_columns = list(sample.columns)
        if sample_columns == list(range(len(sample_columns))):
            first_row = sample.iloc[0] if not sample.empty else None
            if first_row is not None and not np.all(pd.to_numeric(first_row, errors="coerce").notna()):
                header_option = None

        if not isinstance(data_source, (str, Path)):
            _rewind_if_possible(data_source)  # type: ignore[arg-type]

        iterator_kwargs = dict(read_kwargs)
        if delimiter_mode == "inferred":
            iterator_kwargs.update({"sep": None, "engine": "python"})
        else:
            iterator_kwargs.update({"delim_whitespace": True})
        if header_option != "infer":
            iterator_kwargs["header"] = header_option

        reader = pd.read_csv(data_source, chunksize=CHUNK_SIZE, **iterator_kwargs)

        accumulator: Optional[ChunkAccumulator] = None
        skipped_columns: List[str] = []
        for chunk in reader:
            chunk_columns = [str(col) for col in chunk.columns]
            if accumulator is None:
                accumulator = ChunkAccumulator(chunk_columns)
            numeric_chunk = chunk.apply(pd.to_numeric, errors="coerce")
            accumulator.process_chunk(numeric_chunk.to_numpy(dtype=float), chunk_columns)
        if accumulator is None:
            raise ValueError("No data rows detected in ASCII spectrum")
        column_data, skipped_columns, stats, reservoirs, row_count = accumulator.finalize()
        if not column_data:
            raise ValueError("No numeric columns detected in ASCII spectrum")
        if skipped_columns:
            logger.warning(
                "Skipping non-numeric columns while parsing %s: %s",
                source,
                ", ".join(skipped_columns),
            )
        analytics = {
            "column_statistics": stats,
            "reservoirs": reservoirs,
            "row_count": row_count,
        }
        return column_data, source, analytics

    # Fallback parser using numpy for environments without pandas.
    import csv
    import re

    if isinstance(data_source, (str, Path)):
        stream: IO[str] = open(data_source, "r", encoding="utf-8")
        close_stream = True
    else:
        stream = data_source  # type: ignore[assignment]
        if hasattr(stream, "seek"):
            stream.seek(0)  # type: ignore[arg-type]
        close_stream = False

    try:
        cleaned_lines = _iter_clean_lines(stream)
        try:
            first_line = next(cleaned_lines)
        except StopIteration as exc:  # pragma: no cover - empty file
            raise ValueError("No data rows detected in ASCII spectrum") from exc

        delimiter = "," if "," in first_line else ("	" if "	" in first_line else None)
        if delimiter is None:
            splitter = re.compile(r"\s+")

            def split_line(line: str) -> List[str]:
                return splitter.split(line.strip())

        else:
            def split_line(line: str) -> List[str]:
                reader = csv.reader([line], delimiter=delimiter)
                return next(reader)

        first_tokens = split_line(first_line)
        has_header = any(any(c.isalpha() for c in token) for token in first_tokens)
        if has_header:
            columns = [str(token) for token in first_tokens]
            initial_rows: List[List[str]] = []
        else:
            columns = [f"col{i}" for i in range(len(first_tokens))]
            initial_rows = [first_tokens]

        accumulator = ChunkAccumulator(columns)

        chunk_rows: List[List[str]] = initial_rows
        for line in cleaned_lines:
            chunk_rows.append(split_line(line))
            if len(chunk_rows) >= CHUNK_SIZE:
                _process_fallback_chunk(chunk_rows, columns, accumulator)
                chunk_rows = []
        if chunk_rows:
            _process_fallback_chunk(chunk_rows, columns, accumulator)

        column_data, skipped_columns, stats, reservoirs, row_count = accumulator.finalize()
        if not column_data:
            raise ValueError("No numeric columns detected in ASCII spectrum")
        if skipped_columns:
            logger.warning(
                "Skipping non-numeric columns while parsing %s: %s",
                source,
                ", ".join(skipped_columns),
            )
        analytics = {
            "column_statistics": stats,
            "reservoirs": reservoirs,
            "row_count": row_count,
        }
        return column_data, source, analytics
    finally:
        if close_stream:
            stream.close()


def _process_fallback_chunk(rows: List[List[str]], columns: List[str], accumulator: ChunkAccumulator) -> None:
    if not rows:
        return
    num_cols = len(columns)
    array = np.full((len(rows), num_cols), np.nan, dtype=float)
    for row_idx, row in enumerate(rows):
        for col_idx in range(min(len(row), num_cols)):
            try:
                array[row_idx, col_idx] = float(row[col_idx])
            except (TypeError, ValueError):
                continue
    accumulator.process_chunk(array, columns)


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
    columns, source, analytics = _read_table(path)
    wave_col, flux_col = _select_columns(columns.keys())

    wave_unit = infer_unit_from_label(str(wave_col)) or CANONICAL_WAVELENGTH_UNIT
    flux_unit = infer_unit_from_label(str(flux_col)) or CANONICAL_FLUX_UNIT

    wavelengths = np.asarray(columns[wave_col], dtype=float) * wave_unit
    flux = np.asarray(columns[flux_col], dtype=float) * flux_unit

    canonical_wavelengths = wavelengths.to(CANONICAL_WAVELENGTH_UNIT)
    wave_values = canonical_wavelengths.value
    if len(wave_values) > 1:
        order = np.argsort(wave_values)
        canonical_wavelengths = canonical_wavelengths[order]
        flux = flux[order]
        wave_values = canonical_wavelengths.value

        unique_waves, inverse = np.unique(wave_values, return_inverse=True)
        if unique_waves.size != wave_values.size:
            flux_values = flux.value
            summed_flux = np.zeros(unique_waves.size, dtype=flux_values.dtype)
            counts = np.zeros_like(unique_waves, dtype=int)
            np.add.at(summed_flux, inverse, flux_values)
            np.add.at(counts, inverse, 1)
            averaged_flux = summed_flux / counts
            flux = averaged_flux * flux.unit
            canonical_wavelengths = unique_waves * canonical_wavelengths.unit
            wave_values = canonical_wavelengths.value

        if np.any(np.diff(wave_values) <= 0):
            raise ValueError("Spectral axis must be strictly increasing or decreasing.")

    equivalencies = u.spectral_density(canonical_wavelengths)
    try:
        canonical_flux = flux.to(CANONICAL_FLUX_UNIT)
    except UnitConversionError:
        try:
            canonical_flux = flux.to(CANONICAL_FLUX_UNIT, equivalencies=equivalencies)
        except UnitConversionError:
            canonical_flux = flux

    spectrum = Spectrum(flux=canonical_flux, spectral_axis=canonical_wavelengths)

    reservoirs = analytics.get("reservoirs", {}) if analytics else {}
    downsampled: Dict[int, Dict[str, np.ndarray]] = {}
    for size, rows in reservoirs.items():
        wave_samples: List[float] = []
        flux_samples: List[float] = []
        for row in rows:
            try:
                wave_value = float(row[wave_col])
                flux_value = float(row[flux_col])
            except KeyError:
                continue
            if np.isnan(wave_value) or np.isnan(flux_value):
                continue
            wave_samples.append(wave_value)
            flux_samples.append(flux_value)
        if not wave_samples:
            continue
        sample_wavelengths = u.Quantity(wave_samples, unit=wave_unit).to(
            CANONICAL_WAVELENGTH_UNIT
        )
        sample_flux = u.Quantity(flux_samples, unit=flux_unit)
        try:
            converted_flux = sample_flux.to(CANONICAL_FLUX_UNIT)
        except UnitConversionError:
            try:
                converted_flux = sample_flux.to(
                    CANONICAL_FLUX_UNIT,
                    equivalencies=u.spectral_density(sample_wavelengths),
                )
            except UnitConversionError:
                converted_flux = sample_flux
        downsampled[size] = {
            "wavelength": sample_wavelengths.value,
            "flux": converted_flux.value,
        }
    if downsampled:
        spectrum.meta["downsampled_tiers"] = downsampled

    flux_unit_label = (
        canonical_flux.unit.to_string()
        if hasattr(canonical_flux.unit, "to_string")
        else str(canonical_flux.unit)
    )
    if flux_unit_label in {"", "1"}:
        flux_unit_label = "dimensionless"
    metadata = SpectrumMetadata(
        source=source,
        description="ASCII spectrum",
        extra={
            "wave_column": wave_col,
            "flux_column": flux_col,
            "wavelength_unit": wave_unit.to_string() if hasattr(wave_unit, "to_string") else str(wave_unit),
            "flux_unit": flux_unit_label,
        },
    )

    if analytics:
        extra = dict(metadata.extra)
        if analytics.get("row_count") is not None:
            extra["row_count"] = str(analytics["row_count"])
        column_stats = analytics.get("column_statistics")
        if column_stats:
            extra["column_statistics"] = json.dumps(column_stats)
        if downsampled:
            extra["downsample_tiers"] = ",".join(str(size) for size in sorted(downsampled))
        metadata.extra = extra

    record = SpectrumRecord(identifier=identifier or Path(source).stem, spectrum=spectrum, metadata=metadata)
    return record
