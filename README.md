# beta

going to try to go one at a time.

## Maintaining Implementation Notes

Each time you add or modify functionality:

1. Record the work in `IMPLEMENTATION_NOTES.md` using the provided template sections (Feature Summaries, Documentation URLs Consulted, Parsed Data Fields with Provenance, Validation Steps).
2. When noting documentation, rely on the parsed link list derived from [`Training Documents/Reference Links for app v3.docx`](Training%20Documents/Reference%20Links%20for%20app%20v3.docx) as the authoritative source and include any additional references consulted.
3. Update the parsed data fields section with every new or modified field, including its provenance and usage.
4. Document the commands or tests executed to validate the work, along with any pertinent output or evidence.
5. Commit the updates to `IMPLEMENTATION_NOTES.md` alongside the code changes so the history remains synchronized with project development.

## Command Line Usage

The JWST spectral viewer can discover products by program identifier or by target name:

- `python -m jwst_viewer 2730` — fetches spectra for program **2730** using the proposal identifier.
- `python -m jwst_viewer --target "WASP-39"` — performs a name-based search, which is useful when the program ID is unknown.
- Both arguments may be combined to further constrain results: `python -m jwst_viewer 2730 --target "WASP-39"`.

At least one of the program identifier or `--target` flag must be supplied before the tool will query MAST.

Within the generated HTML viewer you can narrow the Mission & Instrument table using the target filter and quickly plot the top-matching spectrum by pressing **Enter** or clicking the **Add first match** button.
