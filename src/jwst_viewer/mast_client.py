"""MAST client helpers for JWST data discovery and download."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from astroquery.mast import Observations  # type: ignore
from astropy.table import Table


logger = logging.getLogger(__name__)


@dataclass
class JWSTProductMetadata:
    """Metadata captured for provenance displays."""

    observation_id: str
    program_id: str
    instrument: str
    target_name: str
    obs_collection: str
    proposal_pi: Optional[str]
    product_url: Optional[str]
    product_filename: Optional[str]
    download_path: Optional[Path] = None
    additional_fields: Dict[str, Any] | None = None


class JWSTMastClient:
    """High level helper around :mod:`astroquery.mast` for JWST spectra."""

    def __init__(self, download_dir: Path | str = "downloads") -> None:
        self.download_dir = Path(download_dir)
        self._last_query_relaxed_message: Optional[str] = None

    @property
    def last_query_relaxed_message(self) -> Optional[str]:
        """Return a human-readable description when the last query broadened."""

        return self._last_query_relaxed_message

    def discover_observations(
        self,
        *,
        program_id: Optional[str] = None,
        target_name: Optional[str] = None,
        instrument_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Table:
        """Query MAST for JWST observations that contain spectra."""

        query_args: Dict[str, Any] = {
            "obs_collection": "JWST",
            "dataproduct_type": "spectrum",
        }
        if program_id:
            query_args["proposal_id"] = program_id
        if target_name:
            query_args["target_name"] = target_name
        if instrument_name:
            query_args["instrument_name"] = instrument_name
        if filters:
            query_args.update(filters)

        # Usage follows the Observations query workflow documented at:
        # https://astroquery.readthedocs.io/en/latest/mast/mast_obsquery.html
        observations = Observations.query_criteria(**query_args)
        return observations

    def discover_products(self, observations: Table) -> Table:
        """Return the filtered list of Level-2 spectral products for the observations."""

        if len(observations) == 0:
            return Table()

        # The product listing/filters follow the documented pattern:
        # https://astroquery.readthedocs.io/en/latest/mast/mast.html#observation-products
        product_list = Observations.get_product_list(observations)
        spectral_products = Observations.filter_products(
            product_list,
            productType="SCIENCE",
            productLevel="2",
            extension="fits",
        )
        return spectral_products

    def download_products(
        self, products: Table, *, mrp_only: bool = True, cache: bool = True
    ) -> List[Path]:
        """Download the requested products if any exist."""

        if len(products) == 0:
            return []

        self.download_dir.mkdir(parents=True, exist_ok=True)
        # Download helper per the MAST API examples:
        # https://mast.stsci.edu/api/v0/pyex.html
        manifest = Observations.download_products(
            products,
            download_dir=str(self.download_dir),
            mrp_only=mrp_only,
            cache=cache,
        )
        if manifest is None:
            return []

        paths: List[Path] = []
        for row in manifest:
            local_path = Path(row["Local Path"])
            if local_path.exists():
                paths.append(local_path)
        return paths

    def collect_metadata(
        self, observations: Table, products: Table, downloaded_paths: Iterable[Path]
    ) -> List[JWSTProductMetadata]:
        """Assemble metadata records for provenance display."""

        paths_by_name = {path.name: path for path in downloaded_paths}
        metadata: List[JWSTProductMetadata] = []
        for product in products:
            obs_id = product.get("obsid")
            obs_rows = observations[observations["obsid"] == obs_id]
            program_id = product.get("proposal_id")
            instrument = product.get("instrument_name")
            target_name = product.get("target_name")
            obs_collection = product.get("obs_collection")
            proposal_pi = (
                obs_rows[0].get("proposal_pi") if len(obs_rows) else product.get("proposal_pi")
            )
            filename = product.get("productFilename")
            download_path = paths_by_name.get(filename) if filename else None
            metadata.append(
                JWSTProductMetadata(
                    observation_id=str(obs_id),
                    program_id=str(program_id) if program_id is not None else "",
                    instrument=str(instrument) if instrument is not None else "",
                    target_name=str(target_name) if target_name is not None else "",
                    obs_collection=str(obs_collection) if obs_collection is not None else "",
                    proposal_pi=str(proposal_pi) if proposal_pi is not None else None,
                    product_url=product.get("dataURI"),
                    product_filename=filename,
                    download_path=download_path,
                    additional_fields={
                        "obs_title": product.get("obs_title"),
                        "t_exptime": product.get("t_exptime"),
                        "instrument_id": product.get("instrument_id"),
                    },
                )
            )
        return metadata

    def discover_and_download(
        self,
        *,
        program_id: Optional[str] = None,
        target_name: Optional[str] = None,
        instrument_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        mrp_only: bool = True,
        cache: bool = True,
    ) -> tuple[Table, Table, List[Path], List[JWSTProductMetadata]]:
        """Full workflow: discover observations, filter spectral products, download, and collect metadata."""

        self._last_query_relaxed_message = None
        observations = self.discover_observations(
            program_id=program_id,
            target_name=target_name,
            instrument_name=instrument_name,
            filters=filters,
        )
        if len(observations) == 0 and program_id and target_name:
            relaxed_message = (
                "Exact target match '%s' within program %s returned no JWST observations; "
                "broadening the search to all targets in that program."
            )
            message = relaxed_message % (target_name, program_id)
            logger.warning(message)
            self._last_query_relaxed_message = message
            observations = self.discover_observations(
                program_id=program_id,
                instrument_name=instrument_name,
                filters=filters,
            )
            if len(observations) == 0:
                logger.warning(
                    "Relaxed JWST search for program %s still returned no observations.",
                    program_id,
                )
        elif len(observations) == 0 and target_name and not program_id:
            relaxed_message = (
                "Exact target match '%s' returned no JWST observations; "
                "broadening the search using wildcard and positional lookups."
            )
            message = relaxed_message % target_name
            logger.warning(message)
            self._last_query_relaxed_message = message

            wildcard_target = f"{target_name}*"
            observations = self.discover_observations(
                target_name=wildcard_target,
                instrument_name=instrument_name,
                filters=filters,
            )
            if len(observations) == 0:
                logger.warning(
                    "Wildcard JWST search for target '%s' returned no observations; "
                    "attempting positional lookup.",
                    target_name,
                )
                try:
                    broader_results = Observations.query_object(
                        target_name, radius="0d0m30s"
                    )
                except Exception as exc:  # pragma: no cover - remote lookup guard
                    logger.warning(
                        "Positional lookup for target '%s' failed: %s", target_name, exc
                    )
                    broader_results = Table()

                filtered_results = broader_results
                if len(filtered_results) and "obs_collection" in filtered_results.colnames:
                    filtered_results = filtered_results[
                        filtered_results["obs_collection"] == "JWST"
                    ]
                if len(filtered_results) and "dataproduct_type" in filtered_results.colnames:
                    filtered_results = filtered_results[
                        filtered_results["dataproduct_type"] == "spectrum"
                    ]
                if instrument_name and "instrument_name" in filtered_results.colnames:
                    filtered_results = filtered_results[
                        filtered_results["instrument_name"] == instrument_name
                    ]
                if filters and len(filtered_results):
                    for key, value in filters.items():
                        if key not in filtered_results.colnames:
                            continue
                        if isinstance(value, (list, tuple, set)):
                            allowed = set(value)
                            mask = [entry in allowed for entry in filtered_results[key]]
                            filtered_results = filtered_results[mask]
                        else:
                            filtered_results = filtered_results[
                                filtered_results[key] == value
                            ]

                observations = filtered_results
                if len(observations) == 0:
                    logger.warning(
                        "Relaxed JWST search for target '%s' still returned no observations.",
                        target_name,
                    )
        products = self.discover_products(observations)
        downloaded_paths = self.download_products(products, mrp_only=mrp_only, cache=cache)
        metadata = self.collect_metadata(observations, products, downloaded_paths)
        return observations, products, downloaded_paths, metadata
