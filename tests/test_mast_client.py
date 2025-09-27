"""Tests for the JWST MAST client discovery workflow."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable, List

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from astropy.table import Table

from jwst_viewer import mast_client
from jwst_viewer.mast_client import JWSTMastClient


def _make_dummy_observations(
    query_returns: Iterable[Table], query_object_return: Table | None = None
):
    """Return a dummy :class:`Observations` stand-in with recorded calls."""

    query_return_list = list(query_returns)
    object_return = query_object_return or Table()

    class DummyObservations:
        query_returns: List[Table] = query_return_list
        query_calls: List[dict] = []
        query_object_calls: List[tuple] = []
        query_object_return: Table = object_return

        @classmethod
        def query_criteria(cls, **kwargs):
            cls.query_calls.append(kwargs)
            if cls.query_returns:
                return cls.query_returns.pop(0)
            return Table()

        @classmethod
        def query_object(cls, *args, **kwargs):
            cls.query_object_calls.append((args, kwargs))
            return cls.query_object_return

        @staticmethod
        def get_product_list(observations):
            return Table()

        @staticmethod
        def filter_products(*args, **kwargs):
            return Table()

        @staticmethod
        def download_products(*args, **kwargs):
            return None

    return DummyObservations


def test_target_relax_wildcard(monkeypatch, tmp_path):
    """Target-only searches should retry with wildcard matching."""

    wildcard_results = Table(
        names=["obsid", "target_name"],
        rows=[(123, "Test Target Extended")],
    )
    dummy = _make_dummy_observations([Table(), wildcard_results])
    monkeypatch.setattr(mast_client, "Observations", dummy)

    client = JWSTMastClient(download_dir=tmp_path)
    observations, products, paths, metadata = client.discover_and_download(
        target_name="Test Target"
    )

    assert len(observations) == 1
    assert not len(products)
    assert not paths
    assert not metadata
    assert dummy.query_calls[0]["target_name"] == "Test Target"
    assert dummy.query_calls[1]["target_name"] == "Test Target*"
    assert client.last_query_relaxed_message is not None


def test_target_relax_object_lookup(monkeypatch, tmp_path):
    """When wildcard fails, the client should fall back to a positional lookup."""

    positional_results = Table(
        names=[
            "obsid",
            "obs_collection",
            "dataproduct_type",
            "instrument_name",
            "intentType",
            "target_name",
        ],
        rows=[
            (10, "JWST", "spectrum", "NIRSpec", "SCIENCE", "Target A"),
            (11, "HST", "spectrum", "NIRSpec", "SCIENCE", "Target A"),
            (12, "JWST", "image", "NIRSpec", "SCIENCE", "Target A"),
            (13, "JWST", "spectrum", "MIRI", "SCIENCE", "Target A"),
            (14, "JWST", "spectrum", "NIRSpec", "CALIBRATION", "Target A"),
        ],
    )
    dummy = _make_dummy_observations([Table(), Table()], positional_results)
    monkeypatch.setattr(mast_client, "Observations", dummy)

    client = JWSTMastClient(download_dir=tmp_path)
    observations, products, paths, metadata = client.discover_and_download(
        target_name="Target A",
        instrument_name="NIRSpec",
        filters={"intentType": ["SCIENCE"]},
    )

    assert len(observations) == 1
    assert observations[0]["obsid"] == 10
    assert dummy.query_object_calls
    assert client.last_query_relaxed_message is not None

