"""Generic handler for TXT, JSON, and HDF5 files in HIMSETU ingestion pipeline.

Provides minimal metadata extraction for formats without dedicated handlers.
HDF5 support requires the optional 'h5py' package; soft-fails gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def extract(path: Path) -> Dict[str, Any]:
    """Extract minimal metadata from TXT, JSON, or HDF5 files.

    Args:
        path: Path to the file.

    Returns:
        Dictionary with available metadata and notes.
    """
    ext = path.suffix.lower()

    if ext == ".json":
        return _extract_json(path)
    elif ext in (".h5", ".hdf5"):
        return _extract_hdf5(path)
    else:
        return _extract_text(path)


def _extract_text(path: Path) -> Dict[str, Any]:
    """Extract character/line count from a plain text file."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        char_count = len(content)
        return {
            "line_count": line_count,
            "char_count": char_count,
            "notes": [],
        }
    except Exception as exc:
        raise ValueError(f"Failed to read text file '{path}': {exc}") from exc


def _extract_json(path: Path) -> Dict[str, Any]:
    """Extract top-level keys from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, dict):
            top_keys = list(data.keys())
        elif isinstance(data, list):
            top_keys = [f"array[{len(data)}]"]
        else:
            top_keys = [str(type(data).__name__)]
        return {
            "top_level_keys": top_keys,
            "notes": [],
        }
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read JSON file '{path}': {exc}") from exc


def _extract_hdf5(path: Path) -> Dict[str, Any]:
    """Extract dataset and group names from an HDF5 file."""
    try:
        import h5py  # type: ignore
    except ImportError:
        return {
            "available": False,
            "notes": [
                "HDF5 support requires the 'h5py' package. "
                "Install with: pip install h5py"
            ],
        }

    try:
        items: list[str] = []

        def _visitor(name: str, obj: Any) -> None:
            items.append(name)

        with h5py.File(str(path), "r") as f:
            f.visititems(_visitor)

        return {
            "available": True,
            "item_count": len(items),
            "items": items[:50],  # cap at 50 for display
            "notes": [] if len(items) <= 50 else [f"Showing first 50 of {len(items)} items."],
        }
    except Exception as exc:
        raise ValueError(
            f"Failed to open HDF5 file '{path}': {exc}"
        ) from exc
