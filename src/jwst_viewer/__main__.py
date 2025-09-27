"""Command line entry point for the JWST spectral viewer."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from astropy import units as u
from specutils import Spectrum1D  # type: ignore

from .mast_client import JWSTMastClient
from .spectrum_loader import JWSTSpectrumLoader
from .viewer import render_viewer_html


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="JWST spectral viewer",
        epilog=(
            "Provide a JWST program identifier or use --target to resolve spectra by "
            "target name. Supplying both will further narrow the query."
        ),
    )
    parser.add_argument(
        "program_id",
        nargs="?",
        help="JWST program/proposal identifier. Optional when --target is provided.",
    )
    parser.add_argument(
        "--instrument",
        dest="instrument",
        help="Instrument name (e.g. NIRSpec, MIRI) to narrow the search",
    )
    parser.add_argument(
        "--target",
        dest="target",
        help=(
            "Target name to narrow the query or to drive a name-based search when "
            "no program ID is supplied."
        ),
    )
    parser.add_argument(
        "--download-dir",
        dest="download_dir",
        default="downloads",
        help="Directory where products are cached",
    )
    parser.add_argument(
        "--output-html",
        dest="output_html",
        default="jwst_viewer.html",
        help="Path to write the interactive HTML viewer",
    )
    parser.add_argument(
        "--flux-unit",
        dest="flux_unit",
        default="Jy",
        help="Flux unit for display (astropy unit string)",
    )
    parser.add_argument(
        "--wave-unit",
        dest="wave_unit",
        default="micron",
        help="Spectral axis unit for display (astropy unit string)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.program_id and not args.target:
        parser.error("You must provide a JWST program ID or specify --target for a name-based search.")

    flux_unit = u.Unit(args.flux_unit)
    wave_unit = u.Unit(args.wave_unit)

    client = JWSTMastClient(download_dir=args.download_dir)
    # The discovery+download workflow mirrors the Observations query guidance:
    # https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
    observations, products, paths, metadata = client.discover_and_download(
        program_id=args.program_id if args.program_id else None,
        instrument_name=args.instrument,
        target_name=args.target if args.target else None,
    )

    if client.last_query_relaxed_message:
        print(f"WARNING: {client.last_query_relaxed_message}", file=sys.stderr)

    if not paths:
        parser.error(
            "No spectral products were found for the supplied program ID/target search."
        )

    loader = JWSTSpectrumLoader(preferred_flux_unit=flux_unit, preferred_wave_unit=wave_unit)
    spectra: Dict[str, Spectrum1D] = {}
    provenance: Dict[str, Optional[str]] = {}
    primary_product_id: Optional[str] = None
    for idx, path in enumerate(paths):
        bundle = loader.load(path)
        product_id = path.name
        spectra[product_id] = bundle.spectrum
        if idx == 0:
            provenance = {
                **{
                    key: (str(value) if value is not None else None)
                    for key, value in bundle.header_metadata.items()
                },
                "round_trip_verified": str(bundle.round_trip_verified),
                "primary_product": product_id,
            }
            primary_product_id = product_id

    render_viewer_html(
        spectra,
        metadata=metadata,
        header_metadata=provenance,
        primary_spectrum_id=primary_product_id,
        output_path=Path(args.output_html),
    )

    print(f"Viewer written to {args.output_html}")


if __name__ == "__main__":
    main()
