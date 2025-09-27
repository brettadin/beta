"""Interactive viewer utilities built on Plotly."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from astropy import units as u
from astropy.units import UnitConversionError
from specutils import Spectrum1D  # type: ignore

from .mast_client import JWSTProductMetadata


def _format_metadata_items(
    metadata: Iterable[JWSTProductMetadata],
) -> List[Dict[str, Optional[str]]]:
    return [
        {
            "Observation ID": item.observation_id,
            "Program ID": item.program_id,
            "Instrument": item.instrument,
            "Target": item.target_name,
            "PI": item.proposal_pi,
            "Collection": item.obs_collection,
            "Download": str(item.download_path) if item.download_path else item.product_url,
            "spectrum_id": item.product_filename or (item.download_path.name if item.download_path else None),
        }
        for item in metadata
    ]


def _serialize_spectrum(
    spectrum: Spectrum1D,
    *,
    label: str,
    alternate_flux_unit: u.Unit = u.Unit("erg / (cm2 s Angstrom)"),
    alternate_wave_unit: u.Unit = u.AA,
) -> Dict[str, Dict[str, object]]:
    wavelength_primary = spectrum.spectral_axis.to(spectrum.spectral_axis.unit)
    spectral_equivalencies = u.spectral_density(spectrum.spectral_axis)
    try:
        flux_primary = spectrum.flux.to(
            spectrum.flux.unit, equivalencies=spectral_equivalencies
        )
        flux_alt = spectrum.flux.to(
            alternate_flux_unit, equivalencies=spectral_equivalencies
        )
    except UnitConversionError as exc:
        raise UnitConversionError(
            "Unable to convert spectrum flux to the requested units. "
            "Ensure the flux units are compatible with the spectral axis "
            "for spectral density conversions."
        ) from exc
    wavelength_alt = spectrum.spectral_axis.to(alternate_wave_unit)
    # ``flux_alt`` is already computed with the proper equivalencies above.

    primary_label = f"{label} [{spectrum.spectral_axis.unit.to_string()} / {spectrum.flux.unit.to_string()}]"
    alternate_label = f"{label} [{alternate_wave_unit.to_string()} / {alternate_flux_unit.to_string()}]"

    return {
        "primary": {
            "x": wavelength_primary.value.tolist(),
            "y": flux_primary.value.tolist(),
            "x_unit": spectrum.spectral_axis.unit.to_string(),
            "y_unit": spectrum.flux.unit.to_string(),
            "axis_title": f"Wavelength [{spectrum.spectral_axis.unit}]",
            "flux_title": f"Flux [{spectrum.flux.unit}]",
            "trace_name": primary_label,
        },
        "alternate": {
            "x": wavelength_alt.value.tolist(),
            "y": flux_alt.value.tolist(),
            "x_unit": alternate_wave_unit.to_string(),
            "y_unit": alternate_flux_unit.to_string(),
            "axis_title": f"Wavelength [{alternate_wave_unit}]",
            "flux_title": f"Flux [{alternate_flux_unit}]",
            "trace_name": alternate_label,
        },
    }


def _build_figure(serialized: Dict[str, Dict[str, object]]) -> go.Figure:
    primary = serialized["primary"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=primary["x"],
            y=primary["y"],
            mode="lines",
            name=primary["trace_name"],
        )
    )
    fig.update_layout(
        title="JWST Spectrum",
        xaxis_title=primary["axis_title"],
        yaxis_title=primary["flux_title"],
        hovermode="x",
    )
    return fig


def render_viewer_html(
    spectra: Dict[str, Spectrum1D],
    *,
    metadata: Iterable[JWSTProductMetadata],
    header_metadata: Dict[str, Optional[str]],
    primary_spectrum_id: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> str:
    """Render the spectrum and metadata into a standalone HTML document."""

    if not spectra:
        raise ValueError("At least one spectrum is required to render the viewer.")

    spectrum_items = list(spectra.items())
    selected_id, selected_spectrum = spectrum_items[0]
    if primary_spectrum_id and primary_spectrum_id in spectra:
        selected_id = primary_spectrum_id
        selected_spectrum = spectra[primary_spectrum_id]

    metadata_rows = _format_metadata_items(metadata)
    label_by_id: Dict[str, str] = {
        row.get("spectrum_id") or "": row.get("Target") or row.get("Observation ID") or ""
        for row in metadata_rows
        if row.get("spectrum_id")
    }

    serialized_spectra: List[Dict[str, object]] = []
    selected_serialized: Optional[Dict[str, Dict[str, object]]] = None
    for product_id, spectrum in spectra.items():
        label = label_by_id.get(product_id, product_id)
        serialized = _serialize_spectrum(spectrum, label=label)
        payload: Dict[str, object] = {
            "id": product_id,
            "label": label,
            "primary": serialized["primary"],
            "alternate": serialized["alternate"],
        }
        serialized_spectra.append(payload)
        if product_id == selected_id:
            selected_serialized = serialized

    if selected_serialized is None:
        # Fallback in the unlikely scenario where the requested ID was not serialized.
        selected_serialized = _serialize_spectrum(selected_spectrum, label=label_by_id.get(selected_id, selected_id))

    serialized_spectra.sort(key=lambda item: 0 if item["id"] == selected_id else 1)

    figure = _build_figure(selected_serialized)
    figure_json = json.dumps(figure, cls=PlotlyJSONEncoder)
    metadata_json = json.dumps(metadata_rows, cls=PlotlyJSONEncoder)
    spectra_json = json.dumps(serialized_spectra, cls=PlotlyJSONEncoder)
    primary_id_json = json.dumps(selected_id)

    provenance_rows = "".join(
        f"""
        <tr>
            <td>{key}</td>
            <td>{value or ""}</td>
        </tr>
        """
        for key, value in header_metadata.items()
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
    .search-controls {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem; align-items: center; }}
    .search-controls label {{ font-weight: 600; }}
    .search-controls input[type="search"] {{ flex: 1 1 260px; padding: 0.5rem; border-radius: 4px; border: 1px solid #2a3848; background: #10141a; color: #edf2ff; }}
    .unit-toggle {{ margin-bottom: 1rem; display: flex; gap: 0.5rem; align-items: center; }}
    .unit-toggle select {{ background: #10141a; color: #edf2ff; border: 1px solid #2a3848; border-radius: 4px; padding: 0.4rem 0.6rem; }}
    .no-results {{ font-style: italic; padding: 0.75rem 0; color: #b0bbcc; }}
    .checkbox-cell {{ text-align: center; }}
  </style>
</head>
<body>
  <header>
    <h1>JWST Spectral Explorer</h1>
  </header>
  <main>
    <section>
      <div class=\"unit-toggle\">
        <label for=\"unit-mode\">Display units:</label>
        <select id=\"unit-mode\">
          <option value=\"primary\">Preferred ({selected_serialized['primary']['x_unit']} / {selected_serialized['primary']['y_unit']})</option>
          <option value=\"alternate\">Alternate ({selected_serialized['alternate']['x_unit']} / {selected_serialized['alternate']['y_unit']})</option>
        </select>
      </div>
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
      <div class=\"search-controls\">
        <label for=\"metadata-search\">Filter by target name</label>
        <input type=\"search\" id=\"metadata-search\" placeholder=\"Search targets...\" />
      </div>
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
            <th>Select</th>
          </tr>
        </thead>
        <tbody id=\"metadata-body\"></tbody>
      </table>
      <div id=\"metadata-empty\" class=\"no-results\" hidden>No observations match the current search.</div>
    </section>
  </main>
  <script>
    const figureSpec = {figure_json};
    const metadataRecords = {metadata_json};
    const spectraPayload = {spectra_json};
    const spectraById = new Map(spectraPayload.map((item) => [item.id, item]));
    const traceRegistry = new Map();
    let currentUnitMode = 'primary';
    const primarySpectrumId = {primary_id_json};

    const plotElement = document.getElementById('jwst-spectrum');
    Plotly.newPlot('jwst-spectrum', figureSpec.data, figureSpec.layout, {{responsive: true}}).then(() => {{
      const initialId = primarySpectrumId || (spectraPayload.length > 0 ? spectraPayload[0].id : null);
      if (initialId && spectraById.has(initialId)) {{
        traceRegistry.set(initialId, 0);
      }}
      syncMetadataTable();
    }});

    const searchInput = document.getElementById('metadata-search');
    const metadataBody = document.getElementById('metadata-body');
    const metadataEmpty = document.getElementById('metadata-empty');
    const unitSelect = document.getElementById('unit-mode');

    searchInput.addEventListener('input', () => {{
      syncMetadataTable();
    }});

    unitSelect.addEventListener('change', (event) => {{
      const newMode = event.target.value === 'alternate' ? 'alternate' : 'primary';
      setUnitMode(newMode);
    }});

    function setUnitMode(mode) {{
      currentUnitMode = mode;
      const firstPayload = spectraPayload[0];
      if (firstPayload) {{
        const axisTitle = firstPayload[mode].axis_title;
        const fluxTitle = firstPayload[mode].flux_title;
        Plotly.relayout(plotElement, {{
          'xaxis.title': axisTitle,
          'yaxis.title': fluxTitle,
        }});
      }}
      traceRegistry.forEach((traceIndex, spectrumId) => {{
        const payload = spectraById.get(spectrumId);
        if (!payload) {{
          return;
        }}
        const data = payload[mode];
        Plotly.restyle(plotElement, {{
          x: [data.x],
          y: [data.y],
          name: [data.trace_name],
        }}, [traceIndex]);
      }});
    }}

    function syncMetadataTable() {{
      const filterTerm = searchInput.value.trim().toLowerCase();
      metadataBody.innerHTML = '';
      let visibleCount = 0;
      metadataRecords.forEach((record) => {{
        const target = (record.Target || '').toLowerCase();
        if (filterTerm && !target.includes(filterTerm)) {{
          return;
        }}
        visibleCount += 1;
        const row = document.createElement('tr');
        addCell(row, record['Observation ID']);
        addCell(row, record['Program ID']);
        addCell(row, record['Instrument']);
        addCell(row, record['Target']);
        addCell(row, record['PI'] || '');
        addCell(row, record['Collection']);
        addLinkCell(row, record['Download']);
        addCheckboxCell(row, record['spectrum_id']);
        metadataBody.appendChild(row);
      }});
      metadataEmpty.hidden = visibleCount !== 0;
    }}

    function addCell(row, value) {{
      const cell = document.createElement('td');
      cell.textContent = value == null ? '' : value;
      row.appendChild(cell);
    }}

    function addLinkCell(row, value) {{
      const cell = document.createElement('td');
      if (value) {{
        const link = document.createElement('a');
        link.href = value;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = value;
        cell.appendChild(link);
      }}
      row.appendChild(cell);
    }}

    function addCheckboxCell(row, spectrumId) {{
      const cell = document.createElement('td');
      cell.classList.add('checkbox-cell');
      if (spectrumId && spectraById.has(spectrumId)) {{
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = traceRegistry.has(spectrumId);
        checkbox.addEventListener('change', () => {{
          if (checkbox.checked) {{
            addSpectrumTrace(spectrumId);
          }} else {{
            removeSpectrumTrace(spectrumId);
          }}
        }});
        cell.appendChild(checkbox);
      }} else {{
        cell.textContent = '—';
      }}
      row.appendChild(cell);
    }}

    function addSpectrumTrace(spectrumId) {{
      if (traceRegistry.has(spectrumId)) {{
        return;
      }}
      const payload = spectraById.get(spectrumId);
      if (!payload) {{
        return;
      }}
      const data = payload[currentUnitMode];
      Plotly.addTraces(plotElement, {{
        x: data.x,
        y: data.y,
        mode: 'lines',
        name: data.trace_name,
      }}).then((indices) => {{
        traceRegistry.set(spectrumId, indices[0]);
        syncMetadataTable();
      }});
    }}

    function removeSpectrumTrace(spectrumId) {{
      const traceIndex = traceRegistry.get(spectrumId);
      if (traceIndex == null) {{
        return;
      }}
      Plotly.deleteTraces(plotElement, [traceIndex]).then(() => {{
        traceRegistry.delete(spectrumId);
        const updatedEntries = Array.from(traceRegistry.entries());
        updatedEntries.sort((a, b) => a[1] - b[1]);
        updatedEntries.forEach(([id, index]) => {{
          const newIndex = index > traceIndex ? index - 1 : index;
          traceRegistry.set(id, newIndex);
        }});
        syncMetadataTable();
      }});
    }}
  </script>
</body>
</html>
"""

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
    return html
