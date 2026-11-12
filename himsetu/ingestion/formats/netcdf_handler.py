"""NetCDF format handler for HIMSETU ingestion pipeline.

Extracts variable names, dimensions, and global attributes from NetCDF
files. Soft-fails gracefully when netcdf4 is not installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def extract(path: Path) -> Dict[str, Any]:
    """Extract metadata from a NetCDF file.

    Requires the optional 'netcdf4' package. Returns a graceful error
    dictionary if netcdf4 is not installed rather than raising.

    Args:
        path: Path to the NetCDF (.nc / .nc4) file.

    Returns:
        Dictionary with keys: variables, dimensions, global_attributes,
        and notes. On missing dependency: available=False, notes=[...].
    """
    try:
        import netCDF4  # type: ignore  # noqa: N813
    except ImportError:
        return {
            "available": False,
            "notes": [
                "NetCDF support requires the 'netcdf4' package. "
                "Install with: pip install netcdf4"
            ],
        }

    try:
        with netCDF4.Dataset(str(path), "r") as ds:
            variables = list(ds.variables.keys())
            dimensions = {
                name: len(dim) for name, dim in ds.dimensions.items()
            }
            global_attrs: Dict[str, Any] = {}
            for attr in ds.ncattrs():
                val = ds.getncattr(attr)
                # Convert numpy scalars to Python native types for JSON safety
                try:
                    global_attrs[attr] = val.item() if hasattr(val, "item") else str(val)
                except Exception:
                    global_attrs[attr] = str(val)

        return {
            "available": True,
            "variables": variables,
            "dimensions": dimensions,
            "global_attributes": global_attrs,
            "notes": [],
        }
    except Exception as exc:
        raise ValueError(
            f"Failed to open NetCDF file '{path}': {exc}"
        ) from exc
