# Spectral Analysis App

This repository contains an interactive, educational spectral-analysis environment. Users can upload their own spectra, overlay
reference line lists, fetch archival data, run comparative analysis, add annotations, and export their work for
reproducibility.

## Features
- Ingest spectra from ASCII/CSV text files and FITS products with automatic unit harmonisation.
- Visualise multiple spectra simultaneously with Plotly, including optional downsampling for large datasets.
- Overlay reference lines fetched from NIST (with graceful fallbacks) and annotate interesting wavelengths.
- Compute difference and ratio spectra by interpolating onto a common wavelength grid.
- Query public MAST archives to download additional spectra for comparison.
- Export the current session—including spectra, reference lines, annotations, and configuration—to JSON for sharing or
  reproducibility.

## Environment Setup
1. Ensure Python 3.10 or newer is available.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Running the App
Launch the Streamlit interface with:
```bash
streamlit run -m spectral_app.interface.streamlit_app
```
The sidebar provides controls for uploading files, requesting reference lines, performing analysis, adding annotations, and
exporting the session manifest.

## Tests
Execute the automated test suite with:
```bash
pytest
```

## Repository Layout
- `src/spectral_app/ingestion/` — CSV/ASCII and FITS ingestion utilities.
- `src/spectral_app/plotting/` — Plotly helpers for building interactive figures.
- `src/spectral_app/analysis/` — Comparative analysis routines (difference, ratio).
- `src/spectral_app/datafetch/` — Integrations for NIST line lists and MAST archive queries.
- `src/spectral_app/interface/` — Streamlit application wiring and UI helpers.
- `src/spectral_app/utils/` — Shared utilities (unit parsing, export helpers).
- `tests/` — Unit tests covering ingestion, analysis, plotting, reference data fetching, and export flows.
- `docs/` — User documentation and implementation notes.

## Maintaining Implementation Notes

Each time you add or modify functionality:

1. Record the work in `IMPLEMENTATION_NOTES.md` using the provided template sections (Feature Summaries, Documentation URLs
   Consulted, Parsed Data Fields with Provenance, Validation Steps).
2. When noting documentation, rely on the parsed link list derived from
   [`Training Documents/Reference Links for app v3.docx`](Training%20Documents/Reference%20Links%20for%20app%20v3.docx) as the
   authoritative source and include any additional references consulted.
3. Update the parsed data fields section with every new or modified field, including its provenance and usage.
4. Document the commands or tests executed to validate the work, along with any pertinent output or evidence.
5. Commit the updates to `IMPLEMENTATION_NOTES.md` alongside the code changes so the history remains synchronized with project
   development.
