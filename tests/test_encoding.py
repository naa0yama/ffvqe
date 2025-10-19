#!/usr/bin/env python3
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
"""Tests for encoding functions."""

import json
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from ffvqe.encoding.encoder import encoding
from ffvqe.encoding.encoder import get_versions
from ffvqe.encoding.encoder import getprobe
from ffvqe.encoding.encoder import getvmaf
from ffvqe.encoding.frame_info import _calculate_max_consecutive_b_frames
from ffvqe.encoding.frame_info import _extract_encoder_params
from ffvqe.encoding.frame_info import getframeinfo


@pytest.fixture
def mock_probe_log() -> dict:
    """Create a mock probe log for testing."""
    return {
        "frames": [
            {"pict_type": "I"},
            {"pict_type": "P"},
            {"pict_type": "B"},
            {"pict_type": "I"},
        ],
        "streams": [{"has_b_frames": 1, "refs": 1}],
    }


@pytest.fixture
def mock_encode_cfg() -> dict:
    """Create a mock encoding configuration for testing."""
    return {
        "hwaccels": "",
        "infile": {"option": "", "filename": "input.mp4"},
        "outfile": {"options": "", "filename": "output", "codec": "libx264", "preset": "medium"},
        "codec": "libx264",
        "preset": "medium",
    }


def test_getframeinfo(mock_probe_log: dict) -> None:
    """Test getframeinfo function."""
    # Without encode options
    with patch("pathlib.Path.open", mock_open(read_data=json.dumps(mock_probe_log))):
        result = getframeinfo("dummy_path")
        assert result["frames"]["I"] == 2
        assert result["frames"]["P"] == 1
        assert result["frames"]["B"] == 1
        assert result["gop"] == 1
        assert result["max_consecutive_bframes"] == 1
        assert result["refs"] == 1

    # With encode options (encoder parameters take priority)
    with patch("pathlib.Path.open", mock_open(read_data=json.dumps(mock_probe_log))):
        result_with_options = getframeinfo("dummy_path", "-crf 23 -bf 9 -refs 5")
        assert result_with_options["frames"]["I"] == 2
        assert result_with_options["frames"]["P"] == 1
        assert result_with_options["frames"]["B"] == 1
        assert result_with_options["gop"] == 1
        assert result_with_options["max_consecutive_bframes"] == 9  # From encode options
        assert result_with_options["refs"] == 5  # From encode options


def test_encoding(mock_encode_cfg: dict, mock_probe_log: dict) -> None:
    """Test encoding function."""
    with (
        patch("subprocess.Popen") as mock_popen,
        patch(
            "ffmpeg_progress_yield.FfmpegProgress.run_command_with_progress",
            return_value=[0, 50, 100],
        ),
        patch("pathlib.Path.open", mock_open(read_data=json.dumps(mock_probe_log))),
    ):
        mock_popen.return_value.poll.return_value = 0
        result = encoding(mock_encode_cfg, 10, 4)
        assert "commandline" in result
        assert "elapsed_time" in result
        assert "elapsed_prbt" in result
        assert "stream" in result


def test_getvmaf(mock_encode_cfg: dict) -> None:
    """Test getvmaf function."""
    with patch(
        "ffmpeg_progress_yield.FfmpegProgress.run_command_with_progress",
        return_value=[0, 50, 100],
    ):
        result = getvmaf(mock_encode_cfg, 4)
        assert "commandline" in result
        assert "elapsed_time" in result


def test_getprobe() -> None:
    """Test getprobe function."""
    with patch("subprocess.run") as mock_run:
        getprobe("dummy_video.mp4")
        mock_run.assert_called_once()


def test_get_versions() -> None:
    """Test get_versions function."""
    mock_versions_log = {
        "program_version": "n7.1",
        "library_versions": [{"name": "libavcodec", "ident": "Lavc61.19.100"}],
    }
    with (
        patch("subprocess.run"),
        patch("pathlib.Path.open", mock_open(read_data=json.dumps(mock_versions_log))),
        patch("pathlib.Path.unlink"),
    ):
        result = get_versions("dummy_config")
        assert result["ffmpege"]["program_version"] == "n7.1"
        assert result["ffmpege"]["library_versions"][0]["name"] == "libavcodec"
        assert result["ffmpege"]["library_versions"][0]["ident"] == "Lavc61.19.100"


def test_calculate_max_consecutive_b_frames() -> None:
    """Test _calculate_max_consecutive_b_frames function."""
    # Case 1: Only one consecutive B-frame
    frames_case1 = [
        {"pict_type": "I"},
        {"pict_type": "B"},
        {"pict_type": "P"},
    ]
    assert _calculate_max_consecutive_b_frames(frames_case1) == 1

    # Case 2: Three consecutive B-frames
    frames_case2 = [
        {"pict_type": "I"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "P"},
    ]
    assert _calculate_max_consecutive_b_frames(frames_case2) == 3

    # Case 3: Multiple B-frame groups with maximum of 15
    frames_case3 = [
        {"pict_type": "I"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "P"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "P"},
    ]
    assert _calculate_max_consecutive_b_frames(frames_case3) == 15

    # Case 4: No B-frames
    frames_case4 = [
        {"pict_type": "I"},
        {"pict_type": "P"},
        {"pict_type": "I"},
        {"pict_type": "P"},
    ]
    assert _calculate_max_consecutive_b_frames(frames_case4) == 0

    # Case 5: All B-frames
    frames_case5 = [
        {"pict_type": "B"},
        {"pict_type": "B"},
        {"pict_type": "B"},
    ]
    assert _calculate_max_consecutive_b_frames(frames_case5) == 3


def test_extract_encoder_params() -> None:
    """Test _extract_encoder_params function."""
    # Case 1: Both -bf and -refs are present
    options1 = "-crf 23 -g 250 -bf 9 -refs 1"
    result1 = _extract_encoder_params(options1)
    assert result1["bf"] == 9
    assert result1["refs"] == 1

    # Case 2: Only -refs is present
    options2 = "-crf 23 -refs 8"
    result2 = _extract_encoder_params(options2)
    assert result2["bf"] is None
    assert result2["refs"] == 8

    # Case 3: Only -bf is present
    options3 = "-crf 23 -bf 15"
    result3 = _extract_encoder_params(options3)
    assert result3["bf"] == 15
    assert result3["refs"] is None

    # Case 4: Neither parameter is present
    options4 = "-crf 23 -preset medium"
    result4 = _extract_encoder_params(options4)
    assert result4["bf"] is None
    assert result4["refs"] is None

    # Case 5: Multi-digit values
    options5 = "-bf 15 -refs 16"
    result5 = _extract_encoder_params(options5)
    assert result5["bf"] == 15
    assert result5["refs"] == 16
