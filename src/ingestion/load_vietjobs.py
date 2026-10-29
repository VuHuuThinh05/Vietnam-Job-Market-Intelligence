
import argparse
import csv
import os
import sys
from pathlib import Path

import psycopg


# ============================================================
# 1. Configuration
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT_DIR / "data" / "raw" / "external" / "VietJobs.csv"

TARGET_TABLE = "public.raw_vietjobs"
STAGING_TABLE = "vietjobs_staging"

COLUMNS = [
    "job_title",
    "location",
    "country",
    "qualifications",
    "technical_skills",
    "soft_skills",
    "languages_required",
    "experience_required",
    "salary",
    "contract_type",
    "working_hours",
    "benefits",
    "description",
    "requirements_text",
    "category",
    "salary_min",
    "salary_max",
    "salary_avg",
]

NUMERIC_COLUMNS = {"salary_min", "salary_max"}
TEXT_COLUMNS = [
    column for column in COLUMNS
    if column not in NUMERIC_COLUMNS
]

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "vietjobs"),
    "user": os.getenv("DB_USER", "vietjobs"),
    "password": os.getenv("DB_PASSWORD"),
}


# ============================================================
# 2. Validate source CSV
# ============================================================

def validate_csv(path: Path) -> int:
    """Validate the CSV header and return the number of data rows."""

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

        if header != COLUMNS:
            raise ValueError(
                "CSV columns do not match the expected schema.\n"
                f"Expected: {COLUMNS}\n"
                f"Actual:   {header}"
            )

        row_count = 0

        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(COLUMNS):
                raise ValueError(
                    f"CSV line {line_number} has {len(row)} fields; "
                    f"expected {len(COLUMNS)}."
                )
            row_count += 1

    if row_count == 0:
        raise ValueError("CSV contains no data rows.")

    return row_count


# ============================================================
# 3. Build SQL expressions
# ============================================================

def quote_columns(columns: list[str]) -> str:
    """Quote column names for SQL statements."""

    return ", ".join(f'"{column}"' for column in columns)


def build_staging_definition() -> str:
    """Create staging columns as text to preserve source values."""

    return ", ".join(f'"{column}" TEXT' for column in COLUMNS)


def build_select_expressions() -> str:
    """
    Convert blank text values to NULL.
    Convert salary_min and salary_max to integers.
    """

    expressions = []

    for column in COLUMNS:
        if column in NUMERIC_COLUMNS:
            expression = (
                f'NULLIF(BTRIM("{column}"), \'\')::INTEGER'
            )
        else:
            expression = f'NULLIF(BTRIM("{column}"), \'\')'

        expressions.append(expression)

    return ", ".join(expressions)


# ============================================================
# 4. Load data into PostgreSQL
# ============================================================

def load_data(expected_rows: int, replace: bool = False) -> int:
    """Load the CSV safely through a temporary staging table."""

    if not DB_CONFIG["password"]:
        raise ValueError(
            "DB_PASSWORD is not set. Set it in PowerShell before "
            "running this script."
        )

    target_columns = quote_columns(COLUMNS)
    staging_definition = build_staging_definition()
    select_expressions = build_select_expressions()

    # Exceptions raised inside this connection context trigger rollback.
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            # Verify the target table exists and inspect its row count.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM public.raw_vietjobs
                """
            )
            existing_rows = cur.fetchone()[0]

            if existing_rows > 0 and not replace:
                raise ValueError(
                    f"{TARGET_TABLE} already contains "
                    f"{existing_rows:,} rows. "
                    "Use --replace to replace the existing data."
                )

            # Create a temporary table for this connection only.
            cur.execute(
                f"""
                CREATE TEMP TABLE {STAGING_TABLE} (
                    {staging_definition}
                ) ON COMMIT DROP
                """
            )

            # Stream the source CSV into staging.
            with CSV_PATH.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                with cur.copy(
                    f"""
                    COPY {STAGING_TABLE} ({target_columns})
                    FROM STDIN
                    WITH (FORMAT CSV, HEADER TRUE, NULL '')
                    """
                ) as copy:
                    while True:
                        chunk = file.read(1024 * 1024)
                        if not chunk:
                            break
                        copy.write(chunk)

            # Validate staging row count.
            cur.execute(
                f"SELECT COUNT(*) FROM {STAGING_TABLE}"
            )
            staged_rows = cur.fetchone()[0]

            if staged_rows != expected_rows:
                raise ValueError(
                    f"Staging row-count mismatch: "
                    f"expected {expected_rows:,}, "
                    f"received {staged_rows:,}."
                )

            # Reject non-integer salary bounds before changing the target.
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM {STAGING_TABLE}
                WHERE (
                    NULLIF(BTRIM(salary_min), '') IS NOT NULL
                    AND BTRIM(salary_min) !~ '^[+-]?[0-9]+$'
                )
                OR (
                    NULLIF(BTRIM(salary_max), '') IS NOT NULL
                    AND BTRIM(salary_max) !~ '^[+-]?[0-9]+$'
                )
                """
            )
            invalid_numeric_rows = cur.fetchone()[0]

            if invalid_numeric_rows:
                raise ValueError(
                    f"Found {invalid_numeric_rows} rows with invalid "
                    "salary_min or salary_max values. "
                    "Target table was not replaced."
                )

            # Replace the target contents inside the current transaction.
            if replace:
                cur.execute(f"TRUNCATE TABLE {TARGET_TABLE}")

            cur.execute(
                f"""
                INSERT INTO {TARGET_TABLE} ({target_columns})
                SELECT {select_expressions}
                FROM {STAGING_TABLE}
                """
            )

            # Verify final row count before committing.
            cur.execute(f"SELECT COUNT(*) FROM {TARGET_TABLE}")
            final_rows = cur.fetchone()[0]

            expected_final_rows = expected_rows

            if final_rows != expected_final_rows:
                raise ValueError(
                    f"Target row-count mismatch: expected "
                    f"{expected_final_rows:,}, got {final_rows:,}."
                )

    # The connection context commits only if no exception occurred.
    return final_rows


# ============================================================
# 5. Main entry point
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Load VietJobs CSV into PostgreSQL public.raw_vietjobs."
        )
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Replace existing target data after staging validation. "
            "Without this option, the script refuses to load into a "
            "non-empty target table."
        ),
    )
    args = parser.parse_args()

    try:
        expected_rows = validate_csv(CSV_PATH)

        print(f"Source file: {CSV_PATH}")
        print(f"Validated CSV rows: {expected_rows:,}")
        print(f"Target table: {TARGET_TABLE}")

        loaded_rows = load_data(
            expected_rows=expected_rows,
            replace=args.replace,
        )

        print("\nIngestion completed successfully.")
        print(f"Rows loaded: {loaded_rows:,}")
        print(f"Target: {TARGET_TABLE}")
        return 0

    except (
        FileNotFoundError,
        ValueError,
        psycopg.Error,
        OSError,
        csv.Error,
    ) as exc:
        print(f"\nIngestion failed: {exc}", file=sys.stderr)
        print(
            "The transaction was rolled back if database changes "
            "had started.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
