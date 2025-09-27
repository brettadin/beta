# Implementation Notes

This document records the work completed on the project across iterations. Each update should summarize the features delivered,
the documentation consulted, any parsed data fields with their provenance, and the validation steps that confirmed the changes.
Treat the parsed link list derived from [`Training Documents/Reference Links for app v3.docx`](Training%20Documents/Reference%20Links%20for%20app%20v3.docx) as the authoritative source when referencing external documentation.

## Feature Summaries
- _Iteration:_ Initial JWST viewer build
  - _Summary:_ Added a modular JWST spectral viewer package with MAST discovery, Specutils-based parsing, Plotly interactivity, and provenance surfacing wired into the CLI entry point.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ Optional program/target discovery
  - _Summary:_ Allowed the CLI to resolve spectra via either program ID or target name and documented the name-based search workflow.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ Multi-product viewer enhancements
  - _Summary:_ Embedded mission metadata within the HTML output, added target filtering controls, and enabled Plotly trace toggling for multiple spectra loaded via the CLI.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ Search-driven quick plotting
  - _Summary:_ Added an "Add first match" control (and Enter-key shortcut) that filters mission metadata and plots the first visible spectrum directly from the search box.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ Program/target fallback search
  - _Summary:_ Logged and surfaced CLI warnings when an exact target/program match fails, then re-ran discovery with a relaxed target constraint so downloads can proceed when canonical names differ.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ FastAPI web interface
  - _Summary:_ Added a persistent FastAPI-powered site that exposes search controls for JWST spectra, reuses the Plotly viewer payloads, and responds with interactive metadata and provenance without regenerating static HTML.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ MAST resilience updates
  - _Summary:_ Hardened the MAST discovery pipeline against transient outages and broadened target-only searches via cone lookups so star-name queries surface spectra when exact matches fail.

- _Iteration:_ Threaded spectrum discovery
  - _Summary:_ Routed the blocking MAST discovery/download and FITS parsing pipeline through FastAPI's threadpool helper so concurrent API requests no longer stall the event loop.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ Fetch failure UX resilience
  - _Summary:_ Deferred spectrum clearing until after a successful API response so prior plots and tables remain visible when a request fails, and surfaced errors without purging the existing view.
  - _Related Issues / Tickets:_ N/A
- _Iteration:_ Relaxed search warning UX
  - _Summary:_ Surfaced API-provided relaxed-search warnings ahead of plotting so users understand when the query broadened before reviewing the spectra.
  - _Related Issues / Tickets:_ N/A

- _Iteration:_ Spectral analysis app rebuild
  - _Summary:_ Replaced the JWST-only tooling with a modular spectral analysis suite featuring CSV/FITS ingestion, Plotly visualisation, NIST line overlays, comparative analysis, session export, and a Streamlit UI scaffold.
  - _Related Issues / Tickets:_ N/A

## Documentation URLs Consulted
- _Iteration:_ Initial JWST viewer build
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
    - https://astroquery.readthedocs.io/en/latest/mast/mast.html#observation-products
    - https://mast.stsci.edu/api/v0/pyex.html
    - https://specutils.readthedocs.io/en/stable/spectrum1d.html#reading-from-files
- _Iteration:_ Optional program/target discovery
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_ N/A
- _Iteration:_ Multi-product viewer enhancements
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
- _Iteration:_ Search-driven quick plotting
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_ N/A
- _Iteration:_ Program/target fallback search
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html
- _Iteration:_ FastAPI web interface
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
    - https://specutils.readthedocs.io/en/stable/spectrum1d.html
- _Iteration:_ MAST resilience updates
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
- _Iteration:_ Relaxed search warning UX
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://outerspace.stsci.edu/display/MASTDOCS/Portal+Guide

- _Iteration:_ Spectral analysis app rebuild
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://specutils.readthedocs.io/en/stable/spectrum1d.html
    - https://docs.streamlit.io/library/api-reference
    - https://astroquery.readthedocs.io/en/latest/index.html


## Parsed Data Fields with Provenance
- _Iteration:_ Initial JWST viewer build
  - _Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Field:_ JWST observation metadata (program ID, instrument, target, PI, collection) from MAST Observations and product tables.
  - _Usage:_ Displayed within the Mission & Instrument panel for provenance and linking back to MAST resources.
  - _Field:_ FITS header metadata (telescope, instrument, program, observation, visit, target, pipeline version).
  - _Usage:_ Rendered in the Citations / Provenance panel to expose product lineage and calibration context.
- _Iteration:_ Optional program/target discovery
  - _Source:_ Existing MAST metadata fields; no new data fields introduced.
  - _Field:_ N/A
  - _Usage:_ N/A
- _Iteration:_ Multi-product viewer enhancements
  - _Source:_ MAST observation/product metadata returned by the Observations service and serialized Specutils spectra arrays.
  - _Field:_ Observation metadata augmented with spectrum identifiers for UI filtering and Plotly trace wiring.
  - _Usage:_ Drives the mission table search results and associates checkboxes with serialized spectra traces in the HTML payload.
- _Iteration:_ Program/target fallback search
  - _Source:_ N/A (no new data fields introduced; the change relaxes discovery queries only when necessary).
  - _Field:_ N/A
  - _Usage:_ N/A
- _Iteration:_ FastAPI web interface
  - _Source:_ MAST observations/product metadata plus JWST FITS headers parsed through the Specutils loader.
  - _Field:_ Same provenance fields as the CLI viewer, now serialized through the API for the browser shell.
  - _Usage:_ Returned via the `/api/spectra` endpoint to populate the mission table and provenance panel dynamically.

- _Iteration:_ MAST resilience updates
  - _Source:_ Existing MAST observation/product metadata returned by relaxed cone-search discovery.
  - _Field:_ No new fields; the change preserves previous provenance data while ensuring broader target search coverage.
  - _Usage:_ Allows the UI to populate existing panels when spectra are located via the fallback discovery path.


- _Iteration:_ Spectral analysis app rebuild
  - _Source:_ User-supplied ASCII/FITS metadata plus fallback NIST line samples.
  - _Field:_ `SpectrumMetadata` (source, target, instrument, observation_date, description, extra) stored alongside each loaded spectrum.
  - _Usage:_ Powers metadata tabs in the Streamlit UI and persists provenance in exported session manifests.
  - _Field:_ `ReferenceLine` (element, wavelength, intensity, label) entries sourced from NIST queries or bundled fallbacks.
  - _Usage:_ Rendered as Plotly vertical markers and included in session exports for reproducibility.


## Validation Steps
- _Iteration:_ Initial JWST viewer build
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer --help`
  - _Command Output / Evidence:_ Help text rendered confirming CLI wiring.
- _Iteration:_ Optional program/target discovery
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer --help`
  - _Command Output / Evidence:_ Help text now advertises optional program ID and target-based search path.
- _Iteration:_ Multi-product viewer enhancements
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer --help`
  - _Command Output / Evidence:_ CLI help confirms the entry point remains available after multi-spectrum wiring.
- _Iteration:_ Search-driven quick plotting
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer --help`
  - _Command Output / Evidence:_ Help text continues to render after wiring the new HTML search controls.
- _Iteration:_ Program/target fallback search
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer --help`
  - _Command Output / Evidence:_ Help text prints successfully after surfacing relaxed-search warnings.
- _Iteration:_ FastAPI web interface
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer.webapp --host 127.0.0.1 --port 8000 --help`
  - _Command Output / Evidence:_ FastAPI launcher arguments render, confirming the server entry point.

- _Iteration:_ MAST resilience updates
  - _Checks Performed:_ `pytest`
  - _Command Output / Evidence:_ Test suite passes, confirming spectrum conversions remain stable after the discovery updates.

- _Iteration:_ Threaded spectrum discovery
  - _Checks Performed:_ Manually issued overlapping `/api/spectra` requests via a browser and `curl` to verify they complete in parallel without stalling the UI.
  - _Command Output / Evidence:_ Concurrent responses returned promptly with independent payloads, confirming the regression fix.
- _Iteration:_ Fetch failure UX resilience
  - _Checks Performed:_ Manually forced a `404` from `/api/spectra` via browser devtools to confirm the previous spectrum and metadata stayed visible while an error banner appeared in the status text.
  - _Command Output / Evidence:_ Prior plot remained rendered with the new error message shown, verifying the UX regression fix.
- _Iteration:_ Relaxed search warning UX
  - _Checks Performed:_ Manually triggered a relaxed target fallback in the web UI and confirmed the warning banner appeared before the spectrum refreshed.
  - _Command Output / Evidence:_ Observed the relaxed-search message rendered in the banner with the existing plot updating afterward.

- _Iteration:_ Spectral analysis app rebuild
  - _Checks Performed:_ `pytest`
  - _Command Output / Evidence:_ Test suite covering ingestion, analysis, plotting, NIST fallback, and export passes, validating the rebuilt architecture.

