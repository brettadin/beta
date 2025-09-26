# Implementation Notes

This document records the work completed on the project across iterations. Each update should summarize the features delivered,
the documentation consulted, any parsed data fields with their provenance, and the validation steps that confirmed the changes.
Treat the parsed link list derived from [`Training Documents/Reference Links for app v3.docx`](Training%20Documents/Reference%20Links%20for%20app%20v3.docx) as the authoritative source when referencing external documentation.

## Feature Summaries
- _Iteration:_ Initial JWST viewer build
  - _Summary:_ Added a modular JWST spectral viewer package with MAST discovery, Specutils-based parsing, Plotly interactivity, and provenance surfacing wired into the CLI entry point.
  - _Related Issues / Tickets:_ N/A

## Documentation URLs Consulted
- _Iteration:_ Initial JWST viewer build
  - _Authoritative Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Additional References:_
    - https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
    - https://astroquery.readthedocs.io/en/latest/mast/mast.html#observation-products
    - https://mast.stsci.edu/api/v0/pyex.html
    - https://specutils.readthedocs.io/en/stable/spectrum1d.html#reading-from-files

## Parsed Data Fields with Provenance
- _Iteration:_ Initial JWST viewer build
  - _Source:_ `Training Documents/Reference Links for app v3.docx`
  - _Field:_ JWST observation metadata (program ID, instrument, target, PI, collection) from MAST Observations and product tables.
  - _Usage:_ Displayed within the Mission & Instrument panel for provenance and linking back to MAST resources.
  - _Field:_ FITS header metadata (telescope, instrument, program, observation, visit, target, pipeline version).
  - _Usage:_ Rendered in the Citations / Provenance panel to expose product lineage and calibration context.

## Validation Steps
- _Iteration:_ Initial JWST viewer build
  - _Checks Performed:_ `PYTHONPATH=src python -m jwst_viewer --help`
  - _Command Output / Evidence:_ Help text rendered confirming CLI wiring.
