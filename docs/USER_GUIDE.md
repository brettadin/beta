# Spectral Analysis App — User Guide

## Uploading Spectra
1. Open the app via `streamlit run -m spectral_app.interface.streamlit_app`.
2. Use the **Data Upload** section in the sidebar to upload CSV/TXT (ASCII) or FITS files.
3. The loader automatically detects wavelength/flux columns and converts them into vacuum nanometres and Jansky, respectively.

## Overlaying Reference Lines
1. Choose elements from the **Reference Lines** multiselect.
2. Adjust the intensity threshold slider to hide weaker transitions.
3. Lines are drawn as dotted vertical markers and labelled with their transition names when available.

## Comparative Analysis
1. Load at least two spectra.
2. In the **Analysis** panel, choose the primary and secondary spectra.
3. Select **Difference** or **Ratio** and click **Compute** to add the derived spectrum to the plot.

## Annotations
1. Enter the wavelength, optional flux, and note text in the **Annotations** section.
2. Click **Add annotation** to render the marker in the plot and list it in the annotations tab.

## Exporting Sessions
1. After loading spectra, click **Download session JSON** in the **Export** section.
2. The exported manifest contains all spectra, reference lines, annotations, and basic configuration for reproducibility.

## Fetching MAST Spectra
MAST discovery functions are available in `spectral_app.datafetch.mast`. Integrate them into the UI as desired by
leveraging `search_mast_spectra`, `download_mast_products`, and `load_downloaded_products` helpers.
