"""Streamlit interface for the spectral analysis application."""
from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import List

import streamlit as st

from spectral_app.analysis.comparative import compute_difference, compute_ratio
from spectral_app.datafetch.nist import fetch_reference_lines
from spectral_app.ingestion.ascii_loader import load_ascii_spectrum
from spectral_app.ingestion.fits_loader import load_fits_spectrum
from spectral_app.models import Annotation, ReferenceLine, SessionExport, SpectrumRecord
from spectral_app.plotting.plotly_view import add_annotations, add_reference_lines, add_spectrum_trace, create_base_figure
from spectral_app.utils.export import export_session


def _init_state() -> None:
    if "spectra" not in st.session_state:
        st.session_state.spectra: List[SpectrumRecord] = []
    if "reference_lines" not in st.session_state:
        st.session_state.reference_lines: List[ReferenceLine] = []
    if "annotations" not in st.session_state:
        st.session_state.annotations: List[Annotation] = []


def _load_uploaded_file(uploaded_file) -> SpectrumRecord:
    name = uploaded_file.name
    if name.lower().endswith((".fits", ".fit", ".fts")):
        with tempfile.NamedTemporaryFile(suffix=name, delete=False) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = Path(tmp.name)
        record = load_fits_spectrum(tmp_path, identifier=name)
        tmp_path.unlink(missing_ok=True)
        return record
    else:
        text = uploaded_file.getvalue().decode("utf-8")
        return load_ascii_spectrum(io.StringIO(text), identifier=name)


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("Data Upload")
        uploaded = st.file_uploader(
            "Upload spectral files (CSV/TXT/FITS)",
            type=["csv", "txt", "tsv", "dat", "fits", "fit", "fts"],
            accept_multiple_files=True,
        )
        for file in uploaded or []:
            try:
                record = _load_uploaded_file(file)
                st.session_state.spectra.append(record)
                st.success(f"Loaded {file.name}")
            except Exception as exc:
                st.error(f"Failed to load {file.name}: {exc}")

        st.header("Reference Lines")
        selected_elements = st.multiselect("Elements", ["H", "He", "C", "Na"])
        intensity = st.slider("Intensity threshold", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
        if selected_elements and st.session_state.spectra:
            wave_axis = st.session_state.spectra[0].spectrum.spectral_axis
            wave_min = wave_axis.min()
            wave_max = wave_axis.max()
            lines: List[ReferenceLine] = []
            for element in selected_elements:
                try:
                    lines.extend(fetch_reference_lines(element, wave_min, wave_max, intensity))
                except Exception as exc:
                    st.warning(f"Failed to fetch {element}: {exc}")
            st.session_state.reference_lines = lines

        st.header("Analysis")
        if len(st.session_state.spectra) >= 2:
            names = [record.identifier for record in st.session_state.spectra]
            primary = st.selectbox("Primary spectrum", names, key="primary_spectrum")
            secondary = st.selectbox("Secondary spectrum", names, index=1, key="secondary_spectrum")
            if primary != secondary:
                op = st.radio("Operation", ["Difference", "Ratio"], horizontal=True)
                if st.button("Compute"):
                    first = next(record for record in st.session_state.spectra if record.identifier == primary)
                    second = next(record for record in st.session_state.spectra if record.identifier == secondary)
                    if op == "Difference":
                        result = compute_difference(first, second)
                    else:
                        result = compute_ratio(first, second)
                    st.session_state.spectra.append(result)
                    st.success(f"Added {result.identifier}")

        st.header("Annotations")
        wavelength = st.number_input("Wavelength (nm)", min_value=0.0, step=0.1)
        flux = st.number_input("Flux (Jy)", value=0.0, step=0.1)
        note = st.text_input("Note")
        if st.button("Add annotation") and note:
            st.session_state.annotations.append(Annotation(wavelength=wavelength, flux=flux, note=note))

        st.header("Export")
        if st.session_state.spectra:
            with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
                export_path = Path(tmp.name)
            export_path = export_session(
                SessionExport(
                    spectra=st.session_state.spectra,
                    reference_lines=st.session_state.reference_lines,
                    annotations=st.session_state.annotations,
                    config={"log_scale": "False"},
                    export_path=export_path,
                )
            )
            with open(export_path, "r", encoding="utf-8") as handle:
                st.download_button("Download session JSON", handle.read(), file_name="spectral_session.json")
            export_path.unlink(missing_ok=True)


def _render_main_panel() -> None:
    st.title("Spectral Analysis App")
    tabs = st.tabs(["Plot", "Metadata", "Annotations"])

    with tabs[0]:
        fig = create_base_figure()
        for record in st.session_state.spectra:
            add_spectrum_trace(fig, record)
        add_reference_lines(fig, st.session_state.reference_lines)
        add_annotations(fig, st.session_state.annotations)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        for record in st.session_state.spectra:
            st.subheader(record.identifier)
            st.json(
                {
                    "source": record.metadata.source,
                    "target": record.metadata.target,
                    "instrument": record.metadata.instrument,
                    "observation_date": record.metadata.observation_date,
                    "description": record.metadata.description,
                    "extra": record.metadata.extra,
                }
            )

    with tabs[2]:
        if st.session_state.annotations:
            for annotation in st.session_state.annotations:
                st.markdown(f"**{annotation.wavelength:.3f} nm** — {annotation.note}")
        else:
            st.info("No annotations yet.")


def run() -> None:
    """Entry point for launching the Streamlit interface."""
    st.set_page_config(page_title="Spectral Analysis App", layout="wide")
    _init_state()
    _render_sidebar()
    _render_main_panel()


if __name__ == "__main__":
    run()
