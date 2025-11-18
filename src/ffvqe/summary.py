#!/usr/bin/env python3
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
"""duckdb."""

from logging import INFO
from logging import StreamHandler
from logging import getLogger
from typing import Any

import duckdb

from ffvqe.config.loader import load_config

logger = getLogger(__name__)
logger.setLevel(INFO)

handler = StreamHandler()
handler.setLevel(INFO)
logger.addHandler(handler)


# Codec default values
CODEC_DEFAULTS = {
    "libsvtav1_crf": {
        "codec": "libsvtav1",
        "type": "CRF",
        "preset": "6",
        "outfile_size_kbyte": 46329.668619791664,
        "outfile_bit_rate_kbs": 3089.0047200520835,
        "enc_sec": 184.39687065283456,
        "outfile_size_percent": 0.1853507712385174,
        "ssim_mean": 0.9960268333333334,
        "vmaf_min": 81.40379733333333,
        "vmaf_mean": 93.419376,
        "gop_min": 161.0,
        "gop_avg": 161.0,
        "gop_max": 161.0,
        "bf": 0.0,
        "refs": 1.0,
        "FI": 23.0,
        "FP": 3573.0,
        "FB": 0.0,
        "outfile_options": "-crf 35(default 2.3.0)",
    },
    "libx264_crf": {
        "codec": "libx264",
        "type": "CRF",
        "preset": "medium",
        "outfile_size_kbyte": 92495.0546875,
        "outfile_bit_rate_kbs": 6167.055826822917,
        "enc_sec": 69.69460356235504,
        "outfile_size_percent": 0.3829334637190249,
        "ssim_mean": 0.9978736666666665,
        "vmaf_min": 85.90102866666666,
        "vmaf_mean": 94.88088049999999,
        "gop_min": 126.0,
        "gop_avg": 220.667,
        "gop_max": 250.0,
        "bf": 3.0,
        "refs": 4.0,
        "FI": 39.0,
        "FP": 2617.0,
        "FB": 1648.0,
        "outfile_options": "-crf 23(default b35605ac)",
    },
    "libx265_crf": {
        "codec": "libx265",
        "type": "CRF",
        "preset": "medium",
        "outfile_size_kbyte": 43395.785807291664,
        "outfile_bit_rate_kbs": 2893.3894856770835,
        "enc_sec": 181.0555251042048,
        "outfile_size_percent": 0.17359940573609892,
        "ssim_mean": 0.9939566666666667,
        "vmaf_min": 74.36156183333333,
        "vmaf_mean": 90.09887733333335,
        "gop_min": 198.0,
        "gop_avg": 241.333,
        "gop_max": 250.0,
        "bf": 4.0,
        "refs": 1.0,
        "FI": 25.0,
        "FP": 2046.0,
        "FB": 2432.0,
        "outfile_options": "-crf 28(default 4.0)",
    },
    "h264_qsv_cqp": {
        "codec": "h264_qsv",
        "type": "CQP",
        "preset": "veryslow",
        "outfile_size_kbyte": 49721.69775390625,
        "outfile_bit_rate_kbs": 3315.1661783854165,
        "enc_sec": 11.65939450263977,
        "outfile_size_percent": 0.22155824481239103,
        "ssim_mean": 0.99267,
        "vmaf_min": 67.94664,
        "vmaf_mean": 94.197446,
        "gop_min": 256.0,
        "gop_avg": 256.0,
        "gop_max": 256.0,
        "bf": 3.0,
        "refs": 3.0,
        "FI": 15.0,
        "FP": 899.0,
        "FB": 2682.0,
        "outfile_options": "-q:v 27 (base)",
    },
    "h264_qsv_icq": {
        "codec": "h264_qsv",
        "type": "ICQ",
        "preset": "veryslow",
        "outfile_size_kbyte": 55614.1943359375,
        "outfile_bit_rate_kbs": 3708.0450846354165,
        "enc_sec": 11.561723550160727,
        "outfile_size_percent": 0.22308368651201305,
        "ssim_mean": 0.9936656666666668,
        "vmaf_min": 77.082578,
        "vmaf_mean": 91.03732016666669,
        "gop_min": 256.0,
        "gop_avg": 256.0,
        "gop_max": 256.0,
        "bf": 3.0,
        "refs": 3.0,
        "FI": 899.0,
        "FP": 2682.0,
        "FB": 3596.0,
        "outfile_options": "-global_quality 29 (default)",
    },
    "_t_crf": {
        "codec": "_t",
        "type": "CRF",
        "preset": "medium",
        "outfile_size_kbyte": 0.0,
        "outfile_bit_rate_kbs": 0.0,
        "enc_sec": 0.0,
        "outfile_size_percent": 0.0,
        "ssim_mean": 0.0,
        "vmaf_min": 0.0,
        "vmaf_mean": 0.0,
        "gop_min": 0.0,
        "gop_avg": 0.0,
        "gop_max": 0.0,
        "bf": 0.0,
        "refs": 0.0,
        "FI": 0.0,
        "FP": 0.0,
        "FB": 0.0,
        "outfile_options": "(default)",
    },
}


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


def insert_codec_defaults() -> None:
    """Insert codec default values into the encodes table only for codecs that exist in the data."""
    existing_codec_types = duckdb.execute(
        "SELECT DISTINCT codec, type FROM encodes WHERE codec IS NOT NULL AND type IS NOT NULL",
    ).fetchall()
    existing_codec_type_pairs = {(row[0], row[1]) for row in existing_codec_types}

    for defaults in CODEC_DEFAULTS.values():
        if (defaults["codec"], defaults["type"]) in existing_codec_type_pairs:
            logger.info(
                "[Default] Inserting default values for: %s_%s",
                defaults["codec"],
                defaults["type"],
            )
            duckdb.execute(
                """
                    INSERT INTO encodes (
                        codec, type, preset, gop, max_consecutive_bframes, refs,
                        ref_type, outfile_size_kbyte, outfile_bit_rate_kbs, enc_sec,
                        outfile_size_percent, ssim_mean, vmaf_min, vmaf_mean,
                        fI, fP, fB, outfile_options
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'default', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    defaults["codec"],
                    defaults["type"],
                    defaults["preset"],
                    defaults["gop_avg"],
                    defaults["bf"],
                    defaults["refs"],
                    defaults["outfile_size_kbyte"],
                    defaults["outfile_bit_rate_kbs"],
                    defaults["enc_sec"],
                    defaults["outfile_size_percent"],
                    defaults["ssim_mean"],
                    defaults["vmaf_min"],
                    defaults["vmaf_mean"],
                    defaults["FI"],
                    defaults["FP"],
                    defaults["FB"],
                    defaults["outfile_options"],
                ],
            )

    default_count = duckdb.execute(
        "SELECT COUNT(*) FROM encodes WHERE ref_type = 'default'",
    ).fetchone()[0]
    logger.info("[Default] Total default rows inserted: %s", default_count)


def generate_grouped_csvs(csvfile_type: str, csvfile_option: str) -> None:
    """Generate grouped CSV files with pre-calculated scores.

    Args:
        csvfile_type: Path to output _gby_type.csv
        csvfile_option: Path to output _gby_option.csv
    """
    logger.info("[CSV] Generating grouped CSV files with scores...")

    # Generate _gby_type.csv: grouped by ref_type and options
    duckdb.sql(
        """
        WITH scored_data AS (
            SELECT
                *,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS score
            FROM encodes
        )
        SELECT
            row_number() OVER () - 1                AS index,
            codec,
            type,
            preset,
            threads,
            MIN(gop)                                AS gop_min,
            AVG(gop)                                AS gop_avg,
            MAX(gop)                                AS gop_max,
            MAX(max_consecutive_bframes)            AS max_consecutive_bframes,
            MAX(refs)                               AS refs,
            MAX(fI)                                 AS fI,
            MAX(fP)                                 AS fP,
            MAX(fB)                                 AS fB,
            MAX(fT)                                 AS fT,
            ref_type,
            AVG(outfile_size_kbyte)                 AS outfile_size_kbyte,
            AVG(outfile_bit_rate_kbs)               AS outfile_bit_rate_kbs,
            outfile_options,
            AVG(enc_sec)                            AS enc_sec,
            AVG(outfile_size_percent)               AS outfile_size_percent,
            AVG(enc_speed)                          AS enc_speed,
            AVG(vmaf_sec)                           AS vmaf_sec,
            AVG(ssim_min)                           AS ssim_min,
            AVG(ssim_mean)                          AS ssim_mean,
            AVG(vmaf_min)                           AS vmaf_min,
            AVG(vmaf_mean)                          AS vmaf_mean,
            AVG(score)                              AS score
        FROM scored_data
        GROUP BY codec, type, preset, threads, ref_type, outfile_options
        """,
    ).write_csv(csvfile_type)
    logger.info("[CSV] Generated %s", csvfile_type)

    # Generate _gby_option.csv: grouped by options only
    duckdb.sql(
        """
        WITH scored_data AS (
            SELECT
                *,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS score
            FROM encodes
        )
        SELECT
            row_number() OVER () - 1                AS index,
            codec,
            type,
            preset,
            threads,
            MIN(gop)                                AS gop_min,
            AVG(gop)                                AS gop_avg,
            MAX(gop)                                AS gop_max,
            MAX(max_consecutive_bframes)            AS max_consecutive_bframes,
            MAX(refs)                               AS refs,
            MAX(fI)                                 AS fI,
            MAX(fP)                                 AS fP,
            MAX(fB)                                 AS fB,
            MAX(fT)                                 AS fT,
            AVG(outfile_size_kbyte)                 AS outfile_size_kbyte,
            AVG(outfile_bit_rate_kbs)               AS outfile_bit_rate_kbs,
            outfile_options,
            AVG(enc_sec)                            AS enc_sec,
            AVG(outfile_size_percent)               AS outfile_size_percent,
            AVG(enc_speed)                          AS enc_speed,
            AVG(vmaf_sec)                           AS vmaf_sec,
            AVG(ssim_min)                           AS ssim_min,
            AVG(ssim_mean)                          AS ssim_mean,
            AVG(vmaf_min)                           AS vmaf_min,
            AVG(vmaf_mean)                          AS vmaf_mean,
            AVG(score)                              AS score
        FROM scored_data
        GROUP BY codec, type, preset, threads, outfile_options
        """,
    ).write_csv(csvfile_option)
    logger.info("[CSV] Generated %s", csvfile_option)


def show_aggregated_results() -> None:
    """Show aggregated results for entries with VMAF mean greater than or equal to 93.00."""
    # Get existing codec/type combinations
    existing_codec_types = duckdb.execute(
        "SELECT DISTINCT codec, type FROM encodes WHERE codec IS NOT NULL AND type IS NOT NULL AND ref_type != 'default'",
    ).fetchall()
    existing_codec_type_pairs = {(row[0], row[1]) for row in existing_codec_types}

    # Build default_values from CODEC_DEFAULTS only for existing codec/type combinations
    default_values_list = []
    for defaults in CODEC_DEFAULTS.values():
        if (
            defaults["codec"] != "_t"
            and (defaults["codec"], defaults["type"]) in existing_codec_type_pairs
        ):
            default_values_list.append(
                f"('{defaults['codec']}', CAST({defaults['outfile_size_percent']} AS DOUBLE), "
                f"CAST({defaults['vmaf_min']} AS DOUBLE), CAST({defaults['vmaf_mean']} AS DOUBLE))",
            )

    if not default_values_list:
        logger.warning("[WARNING] No default values found for existing codecs")
        return

    default_values_sql = ", ".join(default_values_list)

    # Anime results
    duckdb.sql(
        f"""
        WITH default_values_raw AS (
            SELECT * FROM (VALUES {default_values_sql})
            AS t(codec, outfile_size_percent, vmaf_min, vmaf_mean)
        ),
        default_values AS (
            SELECT
                codec,
                outfile_size_percent,
                vmaf_min,
                vmaf_mean,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS default_score
            FROM default_values_raw
        ),
        scored_data AS (
            SELECT
                *,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS score
            FROM encodes
            WHERE
                ref_type like 'Anime' AND
                vmaf_mean >= 93.00 AND
                vmaf_mean <= 100.00
        )
        SELECT
            ref_type,
            preset,
            printf('%.3f', ROUND(AVG(outfile_size_kbyte), 3))        AS outfile_size_kbyte,
            printf('%.3f', ROUND(AVG(outfile_bit_rate_kbs), 3))      AS outfile_bit_rate_kbs,
            printf('%.3f', ROUND(AVG(enc_sec), 3))                   AS enc_sec,
            printf('%.3f', ROUND(AVG(outfile_size_percent), 3))      AS outfile_size_percent,
            printf('%.3f', ROUND(AVG(ssim_mean), 3))                 AS ssim_mean,
            printf('%.3f', ROUND(AVG(vmaf_min), 3))                  AS vmaf_min,
            printf('%.3f', ROUND(AVG(vmaf_mean), 3))                 AS vmaf_mean,
            CONCAT(
                printf('%.3f', ROUND(AVG(score), 3)),
                ' (',
                printf('%+7.3f', ROUND(AVG(score), 3) - (SELECT default_score FROM default_values d WHERE d.codec = scored_data.codec LIMIT 1)),
                ')'
            ) AS score,
            outfile_options
        FROM scored_data
        GROUP BY codec, ref_type, preset, outfile_options
        ORDER BY AVG(score) DESC
        LIMIT 5
    """,
    ).show()
    # Nature results
    duckdb.sql(
        f"""
        WITH default_values_raw AS (
            SELECT * FROM (VALUES {default_values_sql})
            AS t(codec, outfile_size_percent, vmaf_min, vmaf_mean)
        ),
        default_values AS (
            SELECT
                codec,
                outfile_size_percent,
                vmaf_min,
                vmaf_mean,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS default_score
            FROM default_values_raw
        ),
        scored_data AS (
            SELECT
                *,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS score
            FROM encodes
            WHERE
                ref_type like 'Nature' AND
                vmaf_mean >= 93.00 AND
                vmaf_mean <= 100.00
        )
        SELECT
            ref_type,
            preset,
            printf('%.3f', ROUND(AVG(outfile_size_kbyte), 3))        AS outfile_size_kbyte,
            printf('%.3f', ROUND(AVG(outfile_bit_rate_kbs), 3))      AS outfile_bit_rate_kbs,
            printf('%.3f', ROUND(AVG(enc_sec), 3))                   AS enc_sec,
            printf('%.3f', ROUND(AVG(outfile_size_percent), 3))      AS outfile_size_percent,
            printf('%.3f', ROUND(AVG(ssim_mean), 3))                 AS ssim_mean,
            printf('%.3f', ROUND(AVG(vmaf_min), 3))                  AS vmaf_min,
            printf('%.3f', ROUND(AVG(vmaf_mean), 3))                 AS vmaf_mean,
            CONCAT(
                printf('%.3f', ROUND(AVG(score), 3)),
                ' (',
                printf('%+7.3f', ROUND(AVG(score), 3) - (SELECT default_score FROM default_values d WHERE d.codec = scored_data.codec LIMIT 1)),
                ')'
            ) AS score,
            outfile_options
        FROM scored_data
        GROUP BY codec, ref_type, preset, outfile_options
        ORDER BY AVG(score) DESC
        LIMIT 5
    """,
    ).show()

    # Build complete default_values with all columns from CODEC_DEFAULTS
    default_full_values_list = []
    for defaults in CODEC_DEFAULTS.values():
        if (
            defaults["codec"] != "_t"
            and (defaults["codec"], defaults["type"]) in existing_codec_type_pairs
        ):
            default_full_values_list.append(
                f"('{defaults['codec']}', '{defaults['type']}', '{defaults['preset']}', "
                f"CAST({defaults['outfile_size_kbyte']} AS DOUBLE), CAST({defaults['outfile_bit_rate_kbs']} AS DOUBLE), "
                f"CAST({defaults['enc_sec']} AS DOUBLE), CAST({defaults['outfile_size_percent']} AS DOUBLE), "
                f"CAST({defaults['ssim_mean']} AS DOUBLE), CAST({defaults['vmaf_min']} AS DOUBLE), CAST({defaults['vmaf_mean']} AS DOUBLE), "
                f"CAST({defaults['gop_min']} AS DOUBLE), CAST({defaults['gop_avg']} AS DOUBLE), CAST({defaults['gop_max']} AS DOUBLE), "
                f"CAST({defaults['bf']} AS DOUBLE), CAST({defaults['refs']} AS DOUBLE), "
                f"CAST({float(defaults['FI'])} AS DOUBLE), CAST({float(defaults['FP'])} AS DOUBLE), CAST({float(defaults['FB'])} AS DOUBLE), "  # type: ignore[arg-type]
                f"'{defaults['outfile_options']}')",
            )

    if not default_full_values_list:
        logger.warning("[WARNING] No full default values found for existing codecs")
        return

    default_full_values_sql = ", ".join(default_full_values_list)

    duckdb.sql(
        f"""
        WITH default_values_raw AS (
            SELECT * FROM (VALUES {default_full_values_sql})
            AS t(codec, type, preset, outfile_size_kbyte, outfile_bit_rate_kbs,
                 enc_sec, outfile_size_percent, ssim_mean, vmaf_min, vmaf_mean,
                 gop_min, gop_avg, gop_max, bf, refs, fI, fP, fB, outfile_options)
        ),
        default_values AS (
            SELECT
                codec, type, preset,
                outfile_size_kbyte,
                outfile_bit_rate_kbs,
                ROUND(outfile_bit_rate_kbs * (60*24)/8/1024, 3) AS "24min/size_mb",
                enc_sec,
                outfile_size_percent,
                ssim_mean,
                vmaf_min,
                vmaf_mean,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS score,
                gop_min, gop_avg, gop_max,
                bf, refs,
                CONCAT(printf('%.1f', fI), ' / ', printf('%.1f', fP), ' / ', printf('%.1f', fB)) AS "I/P/B frames",
                outfile_options,
                0 AS sort_order
            FROM default_values_raw
        ),
        scored_encodes AS (
            SELECT
                *,
                (1 - outfile_size_percent) * 85 +
                CASE
                    WHEN vmaf_mean >= 93.0 AND vmaf_mean < 94.0 THEN 10 - ABS(vmaf_mean - 93.5) * 2
                    WHEN vmaf_mean < 93.0 THEN GREATEST(0, 10 - (93.0 - vmaf_mean) * 2)
                    ELSE GREATEST(0, 10 - (vmaf_mean - 94.0) * 2)
                END +
                (vmaf_min / 100) * 5 AS score
            FROM encodes
            WHERE
                ref_type != 'default' AND
                outfile_size_percent <= 0.50 AND
                ssim_mean >= 0.99 AND
                vmaf_mean >= 93.00 AND
                vmaf_mean <= 100.00
        ),
        aggregated_results AS (
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
                ROUND(AVG(score), 3)                     AS score,
                ROUND(MIN(gop), 1)                       AS gop_min,
                ROUND(AVG(gop), 1)                       AS gop_avg,
                ROUND(MAX(gop), 1)                       AS gop_max,
                ROUND(AVG(max_consecutive_bframes), 3)   AS bf,
                ROUND(AVG(refs), 3)                      AS refs,
                CONCAT(ROUND(AVG(fI), 3), ' / ',
                    ROUND(AVG(fP), 3), ' / ',
                    ROUND(AVG(fB), 3))                   AS "I/P/B frames",
                outfile_options,
                1 AS sort_order
            FROM scored_encodes
            GROUP BY codec, type, preset, outfile_options
        ),
        combined AS (
            SELECT * FROM default_values
            UNION ALL
            SELECT * FROM aggregated_results
        )
        SELECT
            codec, type, preset,
            printf('%.3f', outfile_size_kbyte) AS outfile_size_kbyte,
            printf('%.3f', outfile_bit_rate_kbs) AS outfile_bit_rate_kbs,
            printf('%.3f', "24min/size_mb") AS "24min/size_mb",
            printf('%.3f', enc_sec) AS enc_sec,
            printf('%.3f', outfile_size_percent) AS outfile_size_percent,
            printf('%.3f', ssim_mean) AS ssim_mean,
            printf('%.3f', vmaf_min) AS vmaf_min,
            printf('%.3f', vmaf_mean) AS vmaf_mean,
            CASE
                WHEN sort_order = 0 THEN printf('%.3f', score)
                ELSE CONCAT(
                    printf('%.3f', score),
                    ' (',
                    printf('%+7.3f', score - (SELECT score FROM default_values d WHERE d.codec = combined.codec AND d.type = combined.type)),
                    ')'
                )
            END AS score,
            CONCAT(printf('%.1f', CAST(gop_min AS DOUBLE)), ' / ', printf('%.1f', CAST(gop_avg AS DOUBLE)), ' / ', printf('%.1f', CAST(gop_max AS DOUBLE))) AS "min/avg/max GOP",
            printf('%.1f', bf) AS bf,
            printf('%.1f', refs) AS refs,
            "I/P/B frames", outfile_options
        FROM combined
        ORDER BY codec, sort_order, COALESCE(score, 0) DESC
        """,
    ).show()


def main(config_path: str, args: object) -> None:
    """Main function to parse arguments and execute the workflow."""
    __configs: dict[str, Any] = load_config(configfile=config_path, args=args)
    __datafile: str = __configs["datafile"]
    csvfile_all: str = __datafile.replace(".json", "_all.csv")
    csvfile_type: str = __datafile.replace(".json", "_gby_type.csv")
    csvfile_option: str = __datafile.replace(".json", "_gby_option.csv")
    create_temp_table(csvfile_all)
    generate_grouped_csvs(csvfile_type, csvfile_option)
    insert_codec_defaults()
    show_aggregated_results()
