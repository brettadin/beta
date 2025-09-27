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
