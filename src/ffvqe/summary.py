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
    "libsvtav1_crf": {  # libsvtav1_crf (score: 81.573, rows aggregated: 6)
        "codec": "libsvtav1",
        "type": "CRF",
        "preset": "6",
        "outfile_size_kbyte": 47650.0963541667,
        "outfile_bit_rate_kbs": 3177.0432942708,
        "enc_sec": 194.3044428031,
        "outfile_size_percent": 0.1913428069,
        "ssim_mean": 0.9959423333,
        "vmaf_min": 81.4382878333,
        "vmaf_mean": 93.3403821667,
        "gop_min": 161,
        "gop_avg": 161.0,
        "gop_max": 161,
        "bf": 0.0,
        "refs": 1.0,
        "FI": 23.0,
        "FP": 3573.0,
        "FB": 0.0,
        "outfile_base": "",
        "outfile_options": "A: -crf 40 / N: -crf 32",
    },
    "libx264_crf": {  # libx264_crf (score: 72.828, rows aggregated: 6)
        "codec": "libx264",
        "type": "CRF",
        "preset": "medium",
        "outfile_size_kbyte": 71712.9611002604,
        "outfile_bit_rate_kbs": 4781.4215494792,
        "enc_sec": 65.403972586,
        "outfile_size_percent": 0.2977345135,
        "ssim_mean": 0.9968961667,
        "vmaf_min": 82.7678093333,
        "vmaf_mean": 93.1822235,
        "gop_min": 126,
        "gop_avg": 220.667,
        "gop_max": 250,
        "bf": 3.0,
        "refs": 4.0,
        "FI": 27.8,
        "FP": 2325.7,
        "FB": 1242.5,
        "outfile_base": "",
        "outfile_options": "A: -crf 26 / N: -crf 24",
    },
    "libx265_crf": {  # libx265_crf (score: 74.677, rows aggregated: 6)
        "codec": "libx265",
        "type": "CRF",
        "preset": "medium",
        "outfile_size_kbyte": 66761.4985351563,
        "outfile_bit_rate_kbs": 4451.28515625,
        "enc_sec": 206.2659320037,
        "outfile_size_percent": 0.2688580066,
        "ssim_mean": 0.995851,
        "vmaf_min": 79.8866041667,
        "vmaf_mean": 92.8919911667,
        "gop_min": 198,
        "gop_avg": 241.333,
        "gop_max": 250,
        "bf": 4.0,
        "refs": 1.0,
        "FI": 18.3,
        "FP": 1645.5,
        "FB": 1932.2,
        "outfile_base": "",
        "outfile_options": "A: -crf 27 / N: -crf 24",
    },
    "h264_qsv_cqp": {  # h264_qsv_cqp (score: 68.770, rows aggregated: 6)
        "codec": "h264_qsv",
        "type": "CQP",
        "preset": "veryslow",
        "outfile_size_kbyte": 83837.9708658854,
        "outfile_bit_rate_kbs": 5589.8497721354,
        "enc_sec": 11.4286951621,
        "outfile_size_percent": 0.3402962721,
        "ssim_mean": 0.9958746667,
        "vmaf_min": 81.7303305,
        "vmaf_mean": 93.9021446667,
        "gop_min": 256,
        "gop_avg": 256.0,
        "gop_max": 256,
        "bf": 3.0,
        "refs": 3.0,
        "FI": 15.0,
        "FP": 899.0,
        "FB": 2682.0,
        "outfile_base": "",
        "outfile_options": "A: -q:v 26 / N: -q:v 22",
    },
    "h264_qsv_icq": {  # h264_qsv_icq (score: 72.352, rows aggregated: 6)
        "codec": "h264_qsv",
        "type": "ICQ",
        "preset": "veryslow",
        "outfile_size_kbyte": 72589.984375,
        "outfile_bit_rate_kbs": 4839.8963216146,
        "enc_sec": 11.6173173984,
        "outfile_size_percent": 0.2921679401,
        "ssim_mean": 0.9949263333,
        "vmaf_min": 79.7564926667,
        "vmaf_mean": 92.7945841667,
        "gop_min": 256,
        "gop_avg": 256.0,
        "gop_max": 256,
        "bf": 3.0,
        "refs": 3.0,
        "FI": 15.0,
        "FP": 899.0,
        "FB": 2682.0,
        "outfile_base": "",
        "outfile_options": "A: -global_quality 29 / N: 26",
    },
    "h264_qsv_la_icq": {  # h264_qsv_la_icq (score: 72.352, rows aggregated: 6)
        "codec": "h264_qsv",
        "type": "LA_ICQ",
        "preset": "veryslow",
        "outfile_size_kbyte": 72589.984375,
        "outfile_bit_rate_kbs": 4839.8963216146,
        "enc_sec": 11.6256463528,
        "outfile_size_percent": 0.2921679401,
        "ssim_mean": 0.9949263333,
        "vmaf_min": 79.7564926667,
        "vmaf_mean": 92.7945841667,
        "gop_min": 256,
        "gop_avg": 256.0,
        "gop_max": 256,
        "bf": 3.0,
        "refs": 3.0,
        "FI": 15.0,
        "FP": 899.0,
        "FB": 2682.0,
        "outfile_base": "",
        "outfile_options": "A: -global_quality 29 -look_ahead 1 / N: 26",
    },
    "hevc_qsv_cqp": {  # hevc_qsv_cqp (score: 76.861, rows aggregated: 6)
        "codec": "hevc_qsv",
        "type": "CQP",
        "preset": "veryslow",
        "outfile_size_kbyte": 60720.7854817708,
        "outfile_bit_rate_kbs": 4048.5240885417,
        "enc_sec": 12.4511560996,
        "outfile_size_percent": 0.2453834429,
        "ssim_mean": 0.9957706667,
        "vmaf_min": 79.9821381667,
        "vmaf_mean": 92.9947841667,
        "gop_min": 248,
        "gop_avg": 248.0,
        "gop_max": 248,
        "bf": 247.0,
        "refs": 1.0,
        "FI": 15.0,
        "FP": 0.0,
        "FB": 3581.0,
        "outfile_base": "",
        "outfile_options": "A: -q:v 25 / N: 21",
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
        "outfile_base": "",
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
                        fI, fP, fB, outfile_base, outfile_options
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'default', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    defaults["outfile_base"],
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
            STRING_AGG(DISTINCT outfile_base, ' / ' ORDER BY outfile_base) AS outfile_base,
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
            STRING_AGG(DISTINCT outfile_base, ' / ' ORDER BY outfile_base) AS outfile_base,
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
            STRING_AGG(DISTINCT outfile_base, ' / ' ORDER BY outfile_base) AS outfile_base,
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
            STRING_AGG(DISTINCT outfile_base, ' / ' ORDER BY outfile_base) AS outfile_base,
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
                f"'{defaults['outfile_base']}', '{defaults['outfile_options']}')",
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
                 gop_min, gop_avg, gop_max, bf, refs, fI, fP, fB, outfile_base, outfile_options)
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
                outfile_base,
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
                STRING_AGG(DISTINCT outfile_base, ' / ' ORDER BY outfile_base) AS outfile_base,
                outfile_options,
                1 AS sort_order
            FROM scored_encodes
            GROUP BY codec, type, preset, outfile_options
            HAVING COUNT(DISTINCT ref_type) >= 2
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
            "I/P/B frames", outfile_base, outfile_options
        FROM combined
        ORDER BY codec, sort_order, COALESCE(score, 0) DESC
        """,
    ).show()


def generate_codec_defaults_from_bases(base_options: str) -> None:
    """Generate CODEC_DEFAULTS dict from selected base options.

    Args:
        base_options: Comma-separated base options (e.g., "-q:v 26,-q:v 22")
                     First value for Anime, second value for Nature
    """
    expected_option_count = 2
    options = [opt.strip() for opt in base_options.split(",")]
    if len(options) != expected_option_count:
        logger.error(
            "Error: --select-base requires exactly 2 comma-separated values (Anime,Nature)",
        )
        return

    anime_base, nature_base = options[0], options[1]
    logger.info("[CODEC_DEFAULTS] Anime base : %s", anime_base)
    logger.info("[CODEC_DEFAULTS] Nature base: %s", nature_base)

    # Query to aggregate selected base executions
    result = duckdb.execute(
        """
        WITH filtered_data AS (
            -- Anime data (3 rows)
            SELECT * FROM encodes
            WHERE ref_type = 'Anime'
              AND outfile_base IS NULL
              AND outfile_options = ?
            UNION ALL
            -- Nature data (3 rows)
            SELECT * FROM encodes
            WHERE ref_type = 'Nature'
              AND outfile_base IS NULL
              AND outfile_options = ?
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
            FROM filtered_data
        )
        SELECT
            codec,
            type,
            preset,
            ROUND(AVG(outfile_size_kbyte), 10) AS outfile_size_kbyte,
            ROUND(AVG(outfile_bit_rate_kbs), 10) AS outfile_bit_rate_kbs,
            ROUND(AVG(enc_sec), 10) AS enc_sec,
            ROUND(AVG(outfile_size_percent), 10) AS outfile_size_percent,
            ROUND(AVG(ssim_mean), 10) AS ssim_mean,
            ROUND(AVG(vmaf_min), 10) AS vmaf_min,
            ROUND(AVG(vmaf_mean), 10) AS vmaf_mean,
            ROUND(MIN(gop), 1) AS gop_min,
            ROUND(AVG(gop), 3) AS gop_avg,
            ROUND(MAX(gop), 1) AS gop_max,
            ROUND(AVG(max_consecutive_bframes), 1) AS bf,
            ROUND(AVG(refs), 1) AS refs,
            ROUND(AVG(fI), 1) AS fI,
            ROUND(AVG(fP), 1) AS fP,
            ROUND(AVG(fB), 1) AS fB,
            ROUND(AVG(score), 3) AS score,
            COUNT(*) AS row_count
        FROM scored_data
        GROUP BY codec, type, preset
        """,
        [anime_base, nature_base],
    ).fetchall()

    if not result:
        logger.error("Error: No data found for the specified base options")
        return

    # Output CODEC_DEFAULTS format
    separator = "=" * 80
    logger.info("\n%s", separator)
    logger.info("CODEC_DEFAULTS Update Data")
    logger.info("%s", separator)

    for row in result:
        (
            codec,
            type_,
            preset,
            outfile_size_kbyte,
            outfile_bit_rate_kbs,
            enc_sec,
            outfile_size_percent,
            ssim_mean,
            vmaf_min,
            vmaf_mean,
            gop_min,
            gop_avg,
            gop_max,
            bf,
            refs,
            fi,
            fp,
            fb,
            score,
            row_count,
        ) = row

        dict_key = f"{codec}_{type_.lower()}"

        logger.info(
            '"%s": {  # %s (score: %.3f, rows aggregated: %d)',
            dict_key,
            dict_key,
            score,
            row_count,
        )
        logger.info('    "codec": "%s",', codec)
        logger.info('    "type": "%s",', type_)
        logger.info('    "preset": "%s",', preset)
        logger.info('    "outfile_size_kbyte": %s,', outfile_size_kbyte)
        logger.info('    "outfile_bit_rate_kbs": %s,', outfile_bit_rate_kbs)
        logger.info('    "enc_sec": %s,', enc_sec)
        logger.info('    "outfile_size_percent": %s,', outfile_size_percent)
        logger.info('    "ssim_mean": %s,', ssim_mean)
        logger.info('    "vmaf_min": %s,', vmaf_min)
        logger.info('    "vmaf_mean": %s,', vmaf_mean)
        logger.info('    "gop_min": %s,', gop_min)
        logger.info('    "gop_avg": %s,', gop_avg)
        logger.info('    "gop_max": %s,', gop_max)
        logger.info('    "bf": %s,', bf)
        logger.info('    "refs": %s,', refs)
        logger.info('    "FI": %s,', fi)
        logger.info('    "FP": %s,', fp)
        logger.info('    "FB": %s,', fb)
        logger.info('    "outfile_base": "",')
        logger.info('    "outfile_options": "A: %s / N: %s",', anime_base, nature_base)
        logger.info("},")

    separator = "=" * 80
    logger.info("\n%s", separator)


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

    # Handle --select-base if provided
    if hasattr(args, "select_base") and args.select_base:
        generate_codec_defaults_from_bases(args.select_base)
