"""CSV format handler for HIMSETU ingestion pipeline.

Extracts tabular metadata (row count, columns, numeric columns) from
CSV files without loading the entire file into memory.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Any


def extract(path: Path) -> Dict[str, Any]:
    """Extract tabular metadata from a CSV file.

    Reads only the header row and counts data rows without loading
    the full dataset into memory.

    Args:
        path: Path to the CSV file.

    Returns:
        Dictionary with keys: row_count, column_count,
        column_names, numeric_columns, and any notes.

    Raises:
        ValueError: If the file cannot be parsed as CSV.
    """
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return {
                    "row_count": 0,
                    "column_count": 0,
                    "column_names": [],
                    "numeric_columns": [],
                    "notes": ["CSV file has no rows."],
                }

            column_names = [col.strip() for col in header]
            column_count = len(column_names)

            # Count rows and sample first row to detect numeric columns
            first_data_row: list[str] = []
            row_count = 0
            for row in reader:
                if row_count == 0:
                    first_data_row = row
                row_count += 1

        # Detect numeric columns from first data row
        numeric_columns: list[str] = []
        if first_data_row:
            for col_name, val in zip(column_names, first_data_row):
                try:
                    float(val.strip())
                    numeric_columns.append(col_name)
                except (ValueError, AttributeError):
                    pass

        return {
            "row_count": row_count,
            "column_count": column_count,
            "column_names": column_names,
            "numeric_columns": numeric_columns,
            "notes": [],
        }

    except Exception as exc:
        raise ValueError(f"Failed to parse CSV file '{path}': {exc}") from exc
