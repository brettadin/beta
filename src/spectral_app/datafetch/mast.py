"""Utilities for querying spectral products from MAST."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from astropy.table import Table
from astroquery.exceptions import InvalidQueryError  # type: ignore
from astroquery.mast import Observations  # type: ignore

from ..ingestion.loaders import load_spectrum
from ..models import SpectrumRecord


@dataclass
class MastProduct:
    observation_id: str
    product_id: str
    description: str
    download_path: Path


def search_mast_spectra(target: Optional[str] = None, obs_collection: Optional[str] = None) -> Table:
    """Search MAST for available spectral products."""
    criteria: Dict[str, str] = {"dataproduct_type": "spectrum"}
    if target:
        criteria["target_name"] = target
    if obs_collection:
        criteria["obs_collection"] = obs_collection
    try:
        return Observations.query_criteria(**criteria)
    except InvalidQueryError as exc:
        raise ValueError(f"MAST query failed: {exc}") from exc


def download_mast_products(table: Table, download_dir: Path) -> List[MastProduct]:
    """Download spectral products listed in the provided table."""
    products = Observations.get_product_list(table)
    manifest = Observations.download_products(products, download_dir=download_dir, mrp_only=False)
    results: List[MastProduct] = []
    for row in manifest:
        local_path = Path(row["Local Path"])
        results.append(
            MastProduct(
                observation_id=row.get("obs_id", ""),
                product_id=row.get("productFilename", local_path.name),
                description=row.get("description", ""),
                download_path=local_path,
            )
        )
    return results


def load_downloaded_products(products: Iterable[MastProduct]) -> List[SpectrumRecord]:
    return [load_spectrum(product.download_path, identifier=product.product_id) for product in products]
