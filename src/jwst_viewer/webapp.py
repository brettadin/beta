"""FastAPI web application for the JWST spectral viewer."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn

from astropy import units as u
from specutils import Spectrum1D  # type: ignore

from .mast_client import JWSTMastClient, JWSTDiscoveryError
from .spectrum_loader import JWSTSpectrumLoader
from .viewer import build_viewer_payload

APP = FastAPI(title="JWST Spectral Explorer")


def _build_client(download_dir: Path) -> JWSTMastClient:
    """Instantiate a MAST client rooted at ``download_dir``.

    The discovery call follows the observations query guidance in the Astroquery
    docs.  See https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
    for the documented parameters and workflow.
    """

    return JWSTMastClient(download_dir=str(download_dir))


def _build_loader(flux_unit: u.Unit, wave_unit: u.Unit) -> JWSTSpectrumLoader:
    """Create a loader configured for the preferred units documented by Specutils.

    Specutils unit handling guidance lives at
    https://specutils.readthedocs.io/en/stable/spectrum1d.html which documents
    the preferred ``Spectrum1D`` APIs for conversions.
    """

    return JWSTSpectrumLoader(preferred_flux_unit=flux_unit, preferred_wave_unit=wave_unit)


def _render_shell() -> str:
    """Return the static HTML shell for the interactive viewer."""

    return """
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>JWST Spectral Explorer</title>
    <script src=\"https://cdn.plot.ly/plotly-latest.min.js\"></script>
    <style>
      body { font-family: sans-serif; margin: 0; padding: 0; background: #10141a; color: #edf2ff; }
      header { padding: 1rem 2rem; background: #1f2a36; }
      main { padding: 2rem; display: grid; gap: 1.5rem; }
      section { background: #16202b; padding: 1.5rem; border-radius: 8px; }
      form { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; align-items: flex-end; }
      label { display: flex; flex-direction: column; font-weight: 600; gap: 0.4rem; }
      input, select { padding: 0.5rem; border-radius: 4px; border: 1px solid #2a3848; background: #10141a; color: #edf2ff; }
      button { padding: 0.55rem 0.9rem; border-radius: 4px; border: 1px solid #2a3848; background: #243244; color: #edf2ff; font-weight: 600; cursor: pointer; }
      button:hover { background: #2f4054; }
      .panel-title { margin-top: 0; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border: 1px solid #2a3848; padding: 0.45rem; text-align: left; }
      th { background: #243244; }
      a { color: #8bbfff; }
      .checkbox-cell { text-align: center; }
      .status { min-height: 1.5rem; font-size: 0.95rem; color: #8bbfff; }
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <header>
      <h1>JWST Spectral Explorer</h1>
    </header>
    <main>
      <section>
        <h2 class=\"panel-title\">Search JWST Spectra</h2>
        <form id=\"search-form\">
          <label>Program ID
            <input type=\"text\" id=\"program-id\" placeholder=\"e.g. 2730\" />
          </label>
          <label>Target name
            <input type=\"text\" id=\"target-name\" placeholder=\"e.g. WASP-39b\" />
          </label>
          <label>Instrument
            <input type=\"text\" id=\"instrument-name\" placeholder=\"Optional\" />
          </label>
          <label>Flux unit
            <input type=\"text\" id=\"flux-unit\" value=\"Jy\" />
          </label>
          <label>Wave unit
            <input type=\"text\" id=\"wave-unit\" value=\"micron\" />
          </label>
          <button type=\"submit\">Fetch spectra</button>
        </form>
        <p id=\"search-status\" class=\"status\"></p>
      </section>
      <section>
        <div class=\"unit-toggle\">
          <label for=\"unit-mode\">Display units:</label>
          <select id=\"unit-mode\" disabled>
            <option value=\"primary\">Preferred</option>
            <option value=\"alternate\">Alternate</option>
          </select>
        </div>
        <div id=\"jwst-spectrum\"></div>
      </section>
      <section>
        <h2 class=\"panel-title\">Citations / Provenance</h2>
        <table>
          <thead>
            <tr><th>Field</th><th>Value</th></tr>
          </thead>
          <tbody id=\"provenance-body\"></tbody>
        </table>
      </section>
      <section>
        <h2 class=\"panel-title\">Mission &amp; Instrument Details</h2>
        <p id=\"table-status\" class=\"status\"></p>
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
      </section>
    </main>
    <script>
      let spectraPayload = [];
      const spectraById = new Map();
      const traceRegistry = new Map();
      let currentUnitMode = 'primary';
      let primarySpectrumId = null;

      const form = document.getElementById('search-form');
      const status = document.getElementById('search-status');
      const tableStatus = document.getElementById('table-status');
      const metadataBody = document.getElementById('metadata-body');
      const provenanceBody = document.getElementById('provenance-body');
      const unitSelect = document.getElementById('unit-mode');
      const plotElement = document.getElementById('jwst-spectrum');

      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const programId = document.getElementById('program-id').value.trim();
        const targetName = document.getElementById('target-name').value.trim();
        const instrumentName = document.getElementById('instrument-name').value.trim();
        const fluxUnit = document.getElementById('flux-unit').value.trim() || 'Jy';
        const waveUnit = document.getElementById('wave-unit').value.trim() || 'micron';

        if (!programId && !targetName) {
          status.textContent = 'Provide a program ID or target name.';
          return;
        }

        status.textContent = 'Fetching spectra…';
        tableStatus.textContent = '';
        provenanceBody.innerHTML = '';
        metadataBody.innerHTML = '';
        unitSelect.disabled = true;
        spectraPayload = [];
        spectraById.clear();
        traceRegistry.clear();
        Plotly.purge(plotElement);

        const params = new URLSearchParams();
        if (programId) params.set('program_id', programId);
        if (targetName) params.set('target', targetName);
        if (instrumentName) params.set('instrument', instrumentName);
        params.set('flux_unit', fluxUnit);
        params.set('wave_unit', waveUnit);

        try {
          const response = await fetch(`/api/spectra?${params.toString()}`);
          if (!response.ok) {
            const detail = await response.json();
            throw new Error(detail.detail || 'Unable to fetch spectra.');
          }
          const payload = await response.json();
          handlePayload(payload);
          status.textContent = `Loaded ${payload.spectra.length} spectra.`;
        } catch (error) {
          console.error(error);
          status.textContent = error.message || 'Failed to fetch spectra.';
        }
      });

      unitSelect.addEventListener('change', (event) => {
        const mode = event.target.value === 'alternate' ? 'alternate' : 'primary';
        setUnitMode(mode);
      });

      function handlePayload(payload) {
        spectraPayload = payload.spectra || [];
        primarySpectrumId = payload.primary_spectrum_id || null;
        spectraById.clear();
        spectraPayload.forEach((item) => spectraById.set(item.id, item));

        populateProvenance(payload.provenance_html || '');
        populateMetadata(payload.metadata || []);
        Plotly.newPlot('jwst-spectrum', payload.figure.data, payload.figure.layout, {responsive: true}).then(() => {
          traceRegistry.clear();
          if (primarySpectrumId && spectraById.has(primarySpectrumId)) {
            traceRegistry.set(primarySpectrumId, 0);
          }
          unitSelect.disabled = false;
          unitSelect.value = 'primary';
          currentUnitMode = 'primary';
        });
      }

      function populateProvenance(html) {
        provenanceBody.innerHTML = html || '';
      }

      function populateMetadata(records) {
        metadataBody.innerHTML = '';
        if (!records || records.length === 0) {
          tableStatus.textContent = 'No observations available for the supplied criteria.';
          return;
        }
        tableStatus.textContent = '';
        records.forEach((record) => {
          const row = document.createElement('tr');
          row.dataset.spectrumId = record['spectrum_id'] || '';
          addCell(row, record['Observation ID']);
          addCell(row, record['Program ID']);
          addCell(row, record['Instrument']);
          addCell(row, record['Target']);
          addCell(row, record['PI'] || '');
          addCell(row, record['Collection']);
          addLinkCell(row, record['Download']);
          addCheckboxCell(row, record['spectrum_id']);
          metadataBody.appendChild(row);
        });
      }

      function addCell(row, value) {
        const cell = document.createElement('td');
        cell.textContent = value == null ? '' : value;
        row.appendChild(cell);
      }

      function addLinkCell(row, value) {
        const cell = document.createElement('td');
        if (value && value.href) {
          const link = document.createElement('a');
          link.href = value.href;
          link.target = '_blank';
          link.rel = 'noopener';
          link.textContent = value.label || 'Download';
          cell.appendChild(link);
        }
        row.appendChild(cell);
      }

      function addCheckboxCell(row, spectrumId) {
        const cell = document.createElement('td');
        cell.classList.add('checkbox-cell');
        if (spectrumId && spectraById.has(spectrumId)) {
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.checked = traceRegistry.has(spectrumId);
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
              addSpectrumTrace(spectrumId);
            } else {
              removeSpectrumTrace(spectrumId);
            }
          });
          cell.appendChild(checkbox);
        } else {
          cell.textContent = '—';
        }
        row.appendChild(cell);
      }

      function addSpectrumTrace(spectrumId) {
        if (traceRegistry.has(spectrumId)) {
          return;
        }
        const payload = spectraById.get(spectrumId);
        if (!payload) {
          return;
        }
        const data = payload[currentUnitMode];
        Plotly.addTraces(plotElement, {
          x: data.x,
          y: data.y,
          mode: 'lines',
          name: data.trace_name,
        }).then((indices) => {
          traceRegistry.set(spectrumId, indices[0]);
        });
      }

      function removeSpectrumTrace(spectrumId) {
        const index = traceRegistry.get(spectrumId);
        if (index == null) {
          return;
        }
        Plotly.deleteTraces(plotElement, [index]).then(() => {
          traceRegistry.delete(spectrumId);
          const entries = Array.from(traceRegistry.entries());
          entries.sort((a, b) => a[1] - b[1]);
          entries.forEach(([id, idx]) => {
            const newIndex = idx > index ? idx - 1 : idx;
            traceRegistry.set(id, newIndex);
          });
        });
      }

      function setUnitMode(mode) {
        currentUnitMode = mode;
        const firstPayload = spectraPayload[0];
        if (firstPayload) {
          Plotly.relayout(plotElement, {
            'xaxis.title': firstPayload[mode].axis_title,
            'yaxis.title': firstPayload[mode].flux_title,
          });
        }
        traceRegistry.forEach((traceIndex, spectrumId) => {
          const payload = spectraById.get(spectrumId);
          if (!payload) {
            return;
          }
          const data = payload[mode];
          Plotly.restyle(plotElement, {
            x: [data.x],
            y: [data.y],
            name: [data.trace_name],
          }, [traceIndex]);
        });
      }
    </script>
  </body>
</html>
"""


@APP.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the interactive viewer shell."""

    return HTMLResponse(content=_render_shell())


@APP.get("/api/spectra")
async def fetch_spectra(
    program_id: Optional[str] = Query(default=None),
    target: Optional[str] = Query(default=None),
    instrument: Optional[str] = Query(default=None),
    flux_unit: str = Query(default="Jy"),
    wave_unit: str = Query(default="micron"),
    download_dir: str = Query(default="downloads"),
) -> Dict[str, object]:
    """Return serialized spectra for the requested criteria."""

    if not program_id and not target:
        raise HTTPException(status_code=400, detail="Provide a program_id or target name.")

    try:
        flux = u.Unit(flux_unit)
        wave = u.Unit(wave_unit)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid unit specification: {exc}")

    client = _build_client(Path(download_dir))
    try:
        observations, products, paths, metadata = client.discover_and_download(
            program_id=program_id,
            instrument_name=instrument,
            target_name=target,
        )
    except JWSTDiscoveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not paths:
        raise HTTPException(status_code=404, detail="No spectral products were found.")

    loader = _build_loader(flux, wave)
    spectra: Dict[str, Spectrum1D] = {}
    header_metadata: Dict[str, Optional[str]] = {}
    primary_spectrum_id: Optional[str] = None

    for index, path in enumerate(paths):
        try:
            bundle = loader.load(path)
        except Exception as exc:  # pragma: no cover - defensive against FITS parsing issues
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load spectrum '{path.name}': {exc}",
            ) from exc
        spectra[path.name] = bundle.spectrum
        if index == 0:
            header_metadata = {
                **{
                    key: (str(value) if value is not None else None)
                    for key, value in bundle.header_metadata.items()
                },
                "round_trip_verified": str(bundle.round_trip_verified),
                "primary_product": path.name,
            }
            primary_spectrum_id = path.name

    figure_spec, metadata_rows, spectra_payload, primary_id, provenance_rows = build_viewer_payload(
        spectra,
        metadata=metadata,
        header_metadata=header_metadata,
        primary_spectrum_id=primary_spectrum_id,
    )

    response: Dict[str, object] = {
        "figure": figure_spec,
        "metadata": metadata_rows,
        "spectra": spectra_payload,
        "primary_spectrum_id": primary_id,
        "provenance_html": provenance_rows,
    }
    if client.last_query_relaxed_message:
        response["warning"] = client.last_query_relaxed_message
    return response


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the JWST Spectral Explorer web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface for the FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the FastAPI server")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload (development only)"
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    uvicorn.run("jwst_viewer.webapp:APP", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
