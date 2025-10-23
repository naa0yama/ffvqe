#!/usr/bin/env python3
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
"""duckdb."""

from logging import INFO
from logging import StreamHandler
from logging import getLogger
from pathlib import Path
from typing import Any

import duckdb

from ffvqe.config.loader import load_config

logger = getLogger(__name__)
logger.setLevel(INFO)

handler = StreamHandler()
handler.setLevel(INFO)
logger.addHandler(handler)


def create_temp_table(csvfile_type: str) -> None:
    """Create a temporary table in DuckDB from the CSV file.

    Args:
        csvfile_type (str): Path to the CSV file.
    """
    logger.info("[CSV] loading %s", csvfile_type)
    duckdb.execute(
        """
            CREATE TEMPORARY TABLE encodes AS
            SELECT *
            FROM read_csv(?)
        """,
        [csvfile_type],
    )


def show_aggregated_results() -> None:
    """Show aggregated results for entries with VMAF mean greater than or equal to 93.00."""
    duckdb.sql(
        """
        SELECT
            ref_type,
            preset,
            ROUND(AVG(outfile_size_kbyte), 3)        AS outfile_size_kbyte,
            ROUND(AVG(outfile_bit_rate_kbs), 3)      AS outfile_bit_rate_kbs,
            ROUND(AVG(enc_sec), 3)                   AS enc_sec,
            ROUND(AVG(outfile_size_percent), 3)      AS outfile_size_percent,
            ROUND(AVG(ssim_mean), 3)                 AS ssim_mean,
            ROUND(AVG(vmaf_min), 3)                  AS vmaf_min,
            ROUND(AVG(vmaf_mean), 3)                 AS vmaf_mean,
            ROUND(
                AVG(
                    (1 - outfile_size_percent) * 85 +            -- 圧縮効率(85%)
                    GREATEST(0, 10 - (vmaf_mean - 93) * 2) +     -- 93がベスト、超過でペナルティ(10%)
                    (vmaf_min / 100) * 5                         -- 最低品質(5%)
                ), 3)                                AS score,
            outfile_options
        FROM encodes
        WHERE
            ref_type like 'Anime' AND
            vmaf_mean >= 93.00 AND
            vmaf_mean <= 100.00
        GROUP BY ref_type, preset, outfile_options
        ORDER BY score DESC
        LIMIT 5
    """,
    ).show()
    duckdb.sql(
        """
        SELECT
            ref_type,
            preset,
            ROUND(AVG(outfile_size_kbyte), 3)        AS outfile_size_kbyte,
            ROUND(AVG(outfile_bit_rate_kbs), 3)      AS outfile_bit_rate_kbs,
            ROUND(AVG(enc_sec), 3)                   AS enc_sec,
            ROUND(AVG(outfile_size_percent), 3)      AS outfile_size_percent,
            ROUND(AVG(ssim_mean), 3)                 AS ssim_mean,
            ROUND(AVG(vmaf_min), 3)                  AS vmaf_min,
            ROUND(AVG(vmaf_mean), 3)                 AS vmaf_mean,
            ROUND(
                AVG(
                    (1 - outfile_size_percent) * 85 +            -- 圧縮効率(85%)
                    GREATEST(0, 10 - (vmaf_mean - 93) * 2) +     -- 93がベスト、超過でペナルティ(10%)
                    (vmaf_min / 100) * 5                         -- 最低品質(5%)
                ), 3)                                AS score,
            outfile_options
        FROM encodes
        WHERE
            ref_type like 'Nature' AND
            vmaf_mean >= 93.00 AND
            vmaf_mean <= 100.00
        GROUP BY ref_type, preset, outfile_options
        ORDER BY score DESC
        LIMIT 5
    """,
    ).show()

    duckdb.sql(
        """
        SELECT
            codec,
            type,
            preset,
            ROUND(AVG(outfile_size_kbyte), 3)        AS outfile_size_kbyte,
            ROUND(AVG(outfile_bit_rate_kbs), 3)      AS outfile_bit_rate_kbs,
            ROUND(AVG(outfile_bit_rate_kbs) * (60*24)/8/1024, 3) AS "24min/size_mb",
            ROUND(AVG(enc_sec), 3)                   AS enc_sec,
            ROUND(AVG(outfile_size_percent), 3)      AS outfile_size_percent,
            ROUND(AVG(ssim_mean), 3)                 AS ssim_mean,
            ROUND(AVG(vmaf_min), 3)                  AS vmaf_min,
            ROUND(AVG(vmaf_mean), 3)                 AS vmaf_mean,
            ROUND(
                AVG(
                    (1 - outfile_size_percent) * 85 +            -- 圧縮効率(85%)
                    GREATEST(0, 10 - (vmaf_mean - 93) * 2) +     -- 93がベスト、超過でペナルティ(10%)
                    (vmaf_min / 100) * 5                         -- 最低品質(5%)
                ), 3)                                AS score,
            ROUND(AVG(gop), 3)                       AS gop,
            ROUND(AVG(max_consecutive_bframes), 3)   AS bf,
            ROUND(AVG(refs), 3)                      AS refs,
            CONCAT(ROUND(AVG(FI), 3), ' / ',
                ROUND(AVG(FP), 3), ' / ',
                ROUND(AVG(FB), 3))                   AS "I/P/B frames",
            outfile_options
        FROM encodes
        WHERE
            outfile_size_percent <= 0.50 AND
            ssim_mean >= 0.99 AND
            vmaf_mean >= 93.00 AND
            vmaf_mean <= 100.00
        GROUP BY codec, type, preset, outfile_options
        ORDER BY score DESC
        """,
    ).show()


def main(config_path: str, args: object) -> None:
    """Main function to parse arguments and execute the workflow."""
    __configs: dict[str, Any] = load_config(configfile=config_path, args=args)
    __datafile: Path = Path(f"{__configs['configs']['datafile']}")
    csvfile_type: str = f"{__datafile}".replace(".json", "_gby_type.csv")
    create_temp_table(csvfile_type)
    show_aggregated_results()
