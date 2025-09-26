"""Command line entry point for the JWST spectral viewer."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional

from astropy import units as u

from .mast_client import JWSTMastClient
from .spectrum_loader import JWSTSpectrumLoader
from .viewer import render_viewer_html


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JWST spectral viewer")
    parser.add_argument("program_id", help="JWST program/proposal identifier")
    parser.add_argument(
        "--instrument",
        dest="instrument",
        help="Instrument name (e.g. NIRSpec, MIRI) to narrow the search",
    )
    parser.add_argument(
        "--target",
        dest="target",
        help="Target name to narrow the query",
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

    flux_unit = u.Unit(args.flux_unit)
    wave_unit = u.Unit(args.wave_unit)

    client = JWSTMastClient(download_dir=args.download_dir)
    observations, products, paths, metadata = client.discover_and_download(
        program_id=args.program_id,
        instrument_name=args.instrument,
        target_name=args.target,
    )

    if not paths:
        parser.error("No spectral products were found for the specified query.")

    loader = JWSTSpectrumLoader(preferred_flux_unit=flux_unit, preferred_wave_unit=wave_unit)
    bundle = loader.load(paths[0])

    provenance: Dict[str, Optional[str]] = {
        **{key: (str(value) if value is not None else None) for key, value in bundle.header_metadata.items()},
        "round_trip_verified": str(bundle.round_trip_verified),
        "primary_product": paths[0].name,
    }

    render_viewer_html(
        bundle.spectrum,
        metadata=metadata,
        header_metadata=provenance,
        output_path=Path(args.output_html),
    )

    print(f"Viewer written to {args.output_html}")


if __name__ == "__main__":
    main()
