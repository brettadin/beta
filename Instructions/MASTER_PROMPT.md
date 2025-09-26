\# MASTER\_PROMPT.md



\*\*Project:\*\* JWST fetch + local upload compare + NIST line overlays

\*\*Repository:\*\* `brettadin/beta`

\*\*Source of truth for external docs:\*\* a `.docx` file in this repo containing the reference links (the same links provided at environment creation). Do not rely on memory; parse the docx each run.



---



\## How to start every session



1\. Locate and parse the `.docx` in `brettadin/beta` that lists reference links. Extract all URLs and deduplicate.

2\. Use only those links as primary documentation. They cover MAST/JWST discovery and data formats, JWST pipeline/calibration, Astroquery/Specutils/JDAViz, NIST ASD lines, and related tooling.

3\. Before coding, identify which objective or bugfix is next and which specific docs support it. Record those URLs as inline code comments and in `IMPLEMENTATION\_NOTES.md` for that change set.



---



\## Scope and goals



We are building three concrete capabilities, in order, without breaking existing behavior. Improvements are iterative and must remain aligned to these goals.



1\. \*\*Fetch JWST data and display it interactively\*\*



\* Discover and download JWST spectroscopy products from MAST according to the linked docs (program/obs IDs, instrument modes, file formats, calibration levels).

\* Load at least one spectral product end-to-end: discover → download → parse → render with pan/zoom, axis unit toggles, and point inspection where appropriate.

\* Surface provenance in the UI: mission, instrument, target, program ID, observation/exposure, calibration level, processing version, and any DOI/bibcode fields specified by the docs.

\* Implement mathematically correct, idempotent unit handling exactly as documented (wavelength, wavenumber, air/vacuum as applicable).



\*\*Acceptance checks\*\*



\* A JWST spectrum can be discovered and rendered with populated metadata/provenance from headers/service responses.

\* Axis unit toggles round-trip with no numeric drift.

\* A “Citations/Provenance” panel displays fields and links mandated by the docs (e.g., MAST/JWST usage and citation guidance).



2\. \*\*Upload locally recorded spectra and compare to JWST\*\*



\* Add a stable upload path for lab spectra (CSV/TXT per common conventions in the docs).

\* Parse headers safely; record but do not crash on non-numeric metadata.

\* Overlay uploaded data with JWST traces with correct unit conversions, optional resampling, and normalization as documented.

\* Provide at least two comparison ops commonly referenced in spectral workflows (e.g., subtraction and ratio), and log operation provenance and parameters.



\*\*Acceptance checks\*\*



\* A user file can be uploaded, overlaid with JWST, units can be toggled, optional resampling applied, and A−B or A/B computed without numerical blow-ups or silent failures.

\* “Export what I see” produces data plus a manifest containing operation provenance and citations to the exact links that informed the implementation.



3\. \*\*Fetch NIST spectral lines and draw accurate overlays\*\*



\* Implement a lines lookup that follows NIST ASD documentation: query parameters, element/ion stage notation, wavelength ranges, intensity/uncertainty fields, and air vs vacuum conventions.

\* Render line overlays as vertical markers with readable labels and non-destructive plot layout. Provide filters (element, ion stage, wavelength window, minimum intensity) strictly as supported by the docs.

\* Apply any required air↔vacuum conversions using the documented formulas only.



\*\*Acceptance checks\*\*



\* Lines for a specified species (e.g., “Fe II”) over a chosen window appear at correct positions, filterable by intensity, with proper air/vac treatment.

\* Labels are deduplicated and legible. Provenance credits NIST ASD and cites the exact help pages used.



---



\## Rules of engagement



\* \*\*Do not introduce or propose a new architecture or redesign.\*\* Work within the existing code and UI, adding the minimum necessary to meet each objective. Defaults remain unchanged.

\* \*\*Don’t break current behavior.\*\* If a change might be breaking, guard it behind a flag and keep current defaults.

\* \*\*Units are sacred.\*\* Conversions must be exact and idempotent. No cumulative scaling errors on repeated toggles.

\* \*\*Every external behavior must map to a doc link.\*\* Add inline comments with the specific URL next to the implementation.

\* \*\*Citations and acknowledgments\*\* required by the docs (MAST/JWST usage, NIST ASD) must be implemented verbatim in UI and exports.

\* \*\*Error handling:\*\* never crash on non-numeric metadata in uploaded files; capture it in logs/provenance.

\* \*\*Overlay hygiene:\*\* manage labels/legends to avoid clutter and duplicates; ensure overlays remain readable.



---



\## Deliverables per iteration



1\. \*\*Focused commits\*\* that implement one measurable step for objective 1, then 2, then 3.



&nbsp;  \* Commit message template:



&nbsp;    ```

&nbsp;    feat(scope): <concise change>

&nbsp;    Docs: <one or more exact URLs used>

&nbsp;    Notes: <edge cases handled, assumptions explicitly tied to docs>

&nbsp;    ```

2\. \*\*`IMPLEMENTATION\_NOTES.md`\*\* updated with:



&nbsp;  \* Feature summary

&nbsp;  \* Exact docs URLs consulted

&nbsp;  \* Data fields parsed and their provenance

&nbsp;  \* Edge cases and validation steps

3\. \*\*Tiny smoke checklist\*\* runnable by a human:



&nbsp;  \* Fetch 1 JWST spectrum and render with provenance

&nbsp;  \* Upload 1 local file and overlay + compare (A−B, A/B)

&nbsp;  \* Fetch and overlay NIST lines in a known window

&nbsp;  \* Export “what I see” including manifest with citations



---



\## Data handling and provenance



\* Respect the documented instrument modes, calibration levels, file formats, and headers.

\* Persist provenance for each displayed trace: source, identifiers, processing level, unit state, and operations applied.

\* Manifest for “Export what I see” must include: app version, units at render time, transforms applied, input sources, and citations to the exact docs pages used.



---



\## Future-facing hooks (do not build yet)



\* Exoplanet atmosphere comparison: identify where line-ID tables, cross-sections, or species templates would plug in; mark clear TODOs with the relevant links from the parsed `.docx`.

\* Keep comparison interfaces generic enough to support exoplanet vs stellar spectra overlays when those data sources are introduced.



---



\## Stop criteria for a change set



\* All acceptance checks for the targeted objective pass.

\* Provenance and required citations are visible and correct.

\* No regressions to existing behavior.

\* Notes and citations are added to `IMPLEMENTATION\_NOTES.md`.



---



\## Source list ingestion



\* The `.docx` of links is the authoritative index of external documentation.

\* Parse it each run; do not hardcode doc URLs elsewhere.

\* If a required topic is missing from the `.docx`, add a TODO with the missing topic description and proceed only with features that are fully documented by the current link set.



---







