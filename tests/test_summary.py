#!/usr/bin/env python3
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
"""Test for summary."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ffvqe.summary import create_temp_table
from ffvqe.summary import generate_grouped_csvs
from ffvqe.summary import insert_codec_defaults
from ffvqe.summary import show_aggregated_results


@pytest.fixture
def mock_yaml_data() -> dict:
    return {
        "configs": {
            "datafile": "test_data.json",
        },
    }


@pytest.fixture
def mock_csv_data(tmp_path: Path) -> str:
    csv_content = """ref_type,outfile_size_kbyte,outfile_bit_rate_kbs,enc_sec,comp_ratio_persent,ssim_mean,vmaf_min,vmaf_mean,outfile_options
type1,1000,2000,10,50,0.95,90,95,-test-option
type2,1500,3000,15,60,0.98,92,96,-other-option"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


def test_create_temp_table(mock_csv_data: str) -> None:
    with patch("duckdb.execute") as mock_execute:
        create_temp_table(mock_csv_data)
        mock_execute.assert_called_once()


def test_show_aggregated_results() -> None:
    with (
        patch("duckdb.sql") as mock_sql,
        patch("duckdb.execute") as mock_execute,
    ):
        # Mock execute to return empty result for existing codecs query
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_execute.return_value = mock_result

        mock_sql.return_value = MagicMock()
        show_aggregated_results()

        # The function should return early if no codecs exist
        # So execute should be called at least once (to get existing codecs)
        assert mock_execute.call_count >= 1


def test_insert_codec_defaults() -> None:
    """Test inserting codec default values."""
    with (
        patch("duckdb.execute") as mock_execute,
        patch("ffvqe.summary.logger") as mock_logger,
    ):
        # Mock existing codec/type combinations
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("libx264", "CRF"), ("libx265", "CRF")]
        mock_result.fetchone.return_value = (2,)
        mock_execute.return_value = mock_result

        insert_codec_defaults()

        # Verify execute was called to get existing codec/type pairs and insert defaults
        assert mock_execute.call_count >= 3  # Get codec/type pairs, insert x2, get count
        mock_logger.info.assert_called()


def test_generate_grouped_csvs() -> None:
    """Test generating grouped CSV files."""
    with (
        patch("duckdb.sql") as mock_sql,
        patch("ffvqe.summary.logger") as mock_logger,
    ):
        mock_result = MagicMock()
        mock_sql.return_value = mock_result

        generate_grouped_csvs("test_type.csv", "test_option.csv")

        # Verify SQL was called twice (once for each CSV)
        assert mock_sql.call_count == 2
        assert mock_result.write_csv.call_count == 2

        # Verify the correct filenames were used
        mock_result.write_csv.assert_any_call("test_type.csv")
        mock_result.write_csv.assert_any_call("test_option.csv")

        # Verify logging
        mock_logger.info.assert_called()
