"""Plotly helpers for the spectral analysis app."""
from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np
import plotly.graph_objects as go

from ..models import Annotation, ReferenceLine, SpectrumRecord


def create_base_figure(title: str = "Spectral Analysis") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis_title="Wavelength (nm)",
        yaxis_title="Flux",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(type="linear")
    fig.update_yaxes(type="linear")
    return fig


def _downsample(values: np.ndarray, max_points: int) -> np.ndarray:
    if values.size <= max_points:
        return np.arange(values.size)
    return np.linspace(0, values.size - 1, max_points).astype(int)


def add_spectrum_trace(
    fig: go.Figure,
    record: SpectrumRecord,
    color: Optional[str] = None,
    max_points: Optional[int] = 5000,
    secondary_y: bool = False,
) -> None:
    canonical_record = record.to_canonical_units()
    spectrum = canonical_record.spectrum
    wavelengths = spectrum.spectral_axis.value
    flux = spectrum.flux.value
    flux_unit = spectrum.flux.unit
    flux_unit_label = flux_unit.to_string() if hasattr(flux_unit, "to_string") else str(flux_unit)
    if flux_unit_label in {"", "1"}:
        flux_unit_label = "dimensionless"
    fig.update_yaxes(title=f"Flux ({flux_unit_label})")
    if max_points is not None:
        indices = _downsample(wavelengths, max_points)
        wavelengths = wavelengths[indices]
        flux = flux[indices]
    fig.add_trace(
        go.Scatter(
            x=wavelengths,
            y=flux,
            name=record.identifier,
            mode="lines",
            line=dict(color=color),
            hovertemplate=f"λ=%{{x:.3f}} nm<br>F=%{{y:.3e}} {flux_unit_label}",)
    )
    if secondary_y:
        fig.update_layout(yaxis2=dict(title="Derived", overlaying="y", side="right"))
        fig.data[-1].update(yaxis="y2")


def add_reference_lines(
    fig: go.Figure,
    lines: Iterable[ReferenceLine],
    color: str = "rgba(200,0,0,0.5)",
    show_labels: bool = True,
) -> None:
    for line in lines:
        fig.add_vline(
            x=line.wavelength.to_value(),
            line=dict(color=color, dash="dot"),
            annotation=dict(text=line.label or line.element, showarrow=False) if show_labels else None,
        )


def add_annotations(fig: go.Figure, annotations: Iterable[Annotation]) -> None:
    for note in annotations:
        fig.add_annotation(
            x=note.wavelength,
            y=note.flux if note.flux is not None else 0,
            text=note.note,
            showarrow=True,
            arrowhead=2,
        )
