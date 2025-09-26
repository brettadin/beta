"""Interactive viewer utilities built on Plotly."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from astropy import units as u
from specutils import Spectrum1D  # type: ignore

from .mast_client import JWSTProductMetadata


def _format_metadata_items(metadata: Iterable[JWSTProductMetadata]) -> List[Dict[str, Optional[str]]]:
    return [
        {
            "Observation ID": item.observation_id,
            "Program ID": item.program_id,
            "Instrument": item.instrument,
            "Target": item.target_name,
            "PI": item.proposal_pi,
            "Collection": item.obs_collection,
            "Download": str(item.download_path) if item.download_path else item.product_url,
        }
        for item in metadata
    ]


def _build_figure(
    spectrum: Spectrum1D,
    *,
    alternate_flux_unit: u.Unit = u.Unit("erg / (cm2 s Angstrom)"),
    alternate_wave_unit: u.Unit = u.AA,
) -> go.Figure:
    wavelength_primary = spectrum.spectral_axis.to(spectrum.spectral_axis.unit)
    flux_primary = spectrum.flux.to(spectrum.flux.unit)
    wavelength_alt = spectrum.spectral_axis.to(alternate_wave_unit)
    flux_alt = spectrum.flux.to(alternate_flux_unit)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=wavelength_primary.value,
            y=flux_primary.value,
            mode="lines",
            name=f"{spectrum.spectral_axis.unit:latex_inline} / {spectrum.flux.unit:latex_inline}",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=wavelength_alt.value,
            y=flux_alt.value,
            mode="lines",
            visible=False,
            name=f"{alternate_wave_unit.to_string()} / {alternate_flux_unit.to_string()}",
        )
    )

    fig.update_layout(
        title="JWST Spectrum",
        xaxis_title=f"Wavelength [{spectrum.spectral_axis.unit}]",
        yaxis_title=f"Flux [{spectrum.flux.unit}]",
        hovermode="x",
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": f"{spectrum.spectral_axis.unit.to_string()} / {spectrum.flux.unit.to_string()}",
                        "method": "update",
                        "args": [
                            {"visible": [True, False]},
                            {
                                "xaxis": {"title": f"Wavelength [{spectrum.spectral_axis.unit}]"},
                                "yaxis": {"title": f"Flux [{spectrum.flux.unit}]"},
                            },
                        ],
                    },
                    {
                        "label": f"{alternate_wave_unit.to_string()} / {alternate_flux_unit.to_string()}",
                        "method": "update",
                        "args": [
                            {"visible": [False, True]},
                            {
                                "xaxis": {"title": f"Wavelength [{alternate_wave_unit}]"},
                                "yaxis": {"title": f"Flux [{alternate_flux_unit}]"},
                            },
                        ],
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "type": "buttons",
                "x": 0.5,
                "xanchor": "center",
                "y": 1.15,
                "yanchor": "top",
            }
        ],
    )

    return fig


def render_viewer_html(
    spectrum: Spectrum1D,
    *,
    metadata: Iterable[JWSTProductMetadata],
    header_metadata: Dict[str, Optional[str]],
    output_path: Optional[Path] = None,
) -> str:
    """Render the spectrum and metadata into a standalone HTML document."""

    figure = _build_figure(spectrum)
    figure_json = json.dumps(figure, cls=PlotlyJSONEncoder)
    metadata_rows = _format_metadata_items(metadata)

    provenance_rows = "".join(
        f"""
        <tr>
            <td>{key}</td>
            <td>{value or ""}</td>
        </tr>
        """
        for key, value in header_metadata.items()
    )

    obs_rows = "".join(
        f"""
        <tr>
            <td>{row['Observation ID']}</td>
            <td>{row['Program ID']}</td>
            <td>{row['Instrument']}</td>
            <td>{row['Target']}</td>
            <td>{row['PI'] or ''}</td>
            <td>{row['Collection']}</td>
            <td><a href='{row['Download']}' target='_blank' rel='noopener'>{row['Download']}</a></td>
        </tr>
        """
        for row in metadata_rows
    )

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>JWST Spectrum Viewer</title>
  <script src=\"https://cdn.plot.ly/plotly-latest.min.js\"></script>
  <style>
    body {{ font-family: sans-serif; margin: 0; padding: 0; background: #10141a; color: #edf2ff; }}
    header {{ padding: 1rem 2rem; background: #1f2a36; }}
    main {{ padding: 2rem; }}
    section {{ margin-bottom: 2rem; background: #16202b; padding: 1.5rem; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #2a3848; padding: 0.5rem; text-align: left; }}
    th {{ background: #243244; }}
    a {{ color: #8bbfff; }}
    .panel-title {{ margin-top: 0; }}
  </style>
</head>
<body>
  <header>
    <h1>JWST Spectral Explorer</h1>
  </header>
  <main>
    <section>
      <div id=\"jwst-spectrum\"></div>
    </section>
    <section>
      <h2 class=\"panel-title\">Citations / Provenance</h2>
      <table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {provenance_rows}
        </tbody>
      </table>
    </section>
    <section>
      <h2 class=\"panel-title\">Mission &amp; Instrument Details</h2>
      <table>
        <thead>
          <tr>
            <th>Observation ID</th>
            <th>Program ID</th>
            <th>Instrument</th>
            <th>Target</th>
            <th>PI</th>
            <th>Collection</th>
            <th>Download</th>
          </tr>
        </thead>
        <tbody>
          {obs_rows}
        </tbody>
      </table>
    </section>
  </main>
  <script>
    const figureSpec = {figure_json};
    Plotly.newPlot('jwst-spectrum', figureSpec.data, figureSpec.layout, {{responsive: true}});
  </script>
</body>
</html>
"""

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
    return html
