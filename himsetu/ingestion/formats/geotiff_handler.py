"""GeoTIFF raster format handler for HIMSETU ingestion pipeline.

Extracts spatial metadata (CRS, bounds, resolution, band count) from
GeoTIFF files using rasterio. Read-only; never modifies source files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def extract(path: Path) -> Dict[str, Any]:
    """Extract spatial metadata from a GeoTIFF file.

    Args:
        path: Path to the GeoTIFF file.

    Returns:
        Dictionary with spatial metadata keys: crs, bounds,
        resolution_m, width_px, height_px, band_count, band_names,
        nodata_value.

    Raises:
        ImportError: If rasterio is not installed.
        ValueError: If the file cannot be opened as a raster.
    """
    try:
        import rasterio  # type: ignore
        from rasterio.crs import CRS  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "rasterio is required for GeoTIFF support. "
            "Install with: pip install rasterio"
        ) from exc

    try:
        with rasterio.open(path) as ds:
            crs_str: Optional[str] = None
            if ds.crs is not None:
                try:
                    crs_str = ds.crs.to_epsg()
                    if crs_str:
                        crs_str = f"EPSG:{crs_str}"
                    else:
                        crs_str = ds.crs.to_string()
                except Exception:
                    crs_str = str(ds.crs)

            bounds = list(ds.bounds)  # [left, bottom, right, top]
            width = ds.width
            height = ds.height
            band_count = ds.count

            # Estimate pixel resolution in map units (degrees or metres)
            res_x = abs(ds.transform.a)
            res_y = abs(ds.transform.e)
            # Store as mean of x/y pixel size in native map units
            resolution = round((res_x + res_y) / 2, 8) if res_x and res_y else None

            # Band names / descriptions
            band_names: List[str] = []
            for i in range(1, band_count + 1):
                desc = ds.descriptions[i - 1]
                band_names.append(desc if desc else f"Band_{i}")

            nodata = ds.nodata

            return {
                "crs": crs_str,
                "bounds": bounds,
                "resolution_m": resolution,
                "width_px": width,
                "height_px": height,
                "band_count": band_count,
                "band_names": band_names,
                "nodata_value": nodata,
                "notes": [],
            }

    except Exception as exc:
        raise ValueError(
            f"Failed to open GeoTIFF file '{path}': {exc}"
        ) from exc
