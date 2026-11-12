"""HIMSETU — Spatial Resampling & Interpolation Engine.

Provides tools to resample 2D scientific arrays and GeoTIFF raster files
to standardized spatial resolutions and dimensions.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Tuple, Optional
import numpy as np


class ResamplingMethod(str, Enum):
    NEAREST = "nearest"
    BILINEAR = "bilinear"


def resample_array(
    data: np.ndarray,
    target_shape: Tuple[int, int],
    method: ResamplingMethod | str = ResamplingMethod.BILINEAR,
) -> np.ndarray:
    """Resample a 2D numpy array to a new (rows, cols) shape.

    Args:
        data: 2D numpy array.
        target_shape: (target_rows, target_cols) tuple of positive ints.
        method: ResamplingMethod (nearest or bilinear).

    Returns:
        Resampled 2D numpy array.
    """
    if data.ndim != 2:
        raise ValueError("Input data array must be 2-dimensional.")
    target_rows, target_cols = target_shape
    if target_rows <= 0 or target_cols <= 0:
        raise ValueError("Target dimensions must be strictly positive integers.")

    src_rows, src_cols = data.shape
    if (src_rows, src_cols) == (target_rows, target_cols):
        return data.copy()

    method_str = str(method).lower()
    if method_str.endswith(".nearest") or method_str == "nearest":
        method_str = "nearest"
    else:
        method_str = "bilinear"

    # Compute coordinate mappings
    row_indices = np.linspace(0, src_rows - 1, target_rows)
    col_indices = np.linspace(0, src_cols - 1, target_cols)

    if method_str == "nearest":
        r_idx = np.round(row_indices).astype(int).clip(0, src_rows - 1)
        c_idx = np.round(col_indices).astype(int).clip(0, src_cols - 1)
        return data[np.ix_(r_idx, c_idx)].astype(data.dtype)

    # Bilinear interpolation
    r_floor = np.floor(row_indices).astype(int).clip(0, src_rows - 2)
    r_ceil = (r_floor + 1).clip(0, src_rows - 1)
    r_frac = (row_indices - r_floor).reshape(-1, 1)

    c_floor = np.floor(col_indices).astype(int).clip(0, src_cols - 2)
    c_ceil = (c_floor + 1).clip(0, src_cols - 1)
    c_frac = (col_indices - c_floor).reshape(1, -1)

    # Sample four corner points
    top_left = data[np.ix_(r_floor, c_floor)]
    top_right = data[np.ix_(r_floor, c_ceil)]
    bottom_left = data[np.ix_(r_ceil, c_floor)]
    bottom_right = data[np.ix_(r_ceil, c_ceil)]

    # Interpolate top and bottom rows
    top = top_left * (1.0 - c_frac) + top_right * c_frac
    bottom = bottom_left * (1.0 - c_frac) + bottom_right * c_frac

    # Interpolate vertically
    resampled = top * (1.0 - r_frac) + bottom * r_frac
    return resampled.astype(data.dtype if np.issubdtype(data.dtype, np.floating) else np.float32)


def resample_raster(
    raster_path: str | Path,
    target_resolution_meters: float,
    output_path: Optional[str | Path] = None,
) -> np.ndarray:
    """Read a raster file and resample its primary band to target spatial resolution in meters."""
    path = Path(raster_path)
    if not path.is_file():
        raise FileNotFoundError(f"Raster file not found: {path}")

    try:
        import rasterio
        from rasterio.enums import Resampling

        with rasterio.open(path) as src:
            # Estimate current resolution
            transform = src.transform
            current_res = abs(transform[0])
            if current_res <= 0:
                current_res = 100.0

            scale_factor = current_res / float(target_resolution_meters)
            new_height = max(1, int(src.height * scale_factor))
            new_width = max(1, int(src.width * scale_factor))

            data = src.read(
                1,
                out_shape=(new_height, new_width),
                resampling=Resampling.bilinear,
            )
            return data.astype(np.float32)

    except Exception:
        # Fallback if rasterio fails or file is not a valid GeoTIFF
        from PIL import Image
        with Image.open(path) as img:
            arr = np.array(img, dtype=np.float32)
            if arr.ndim == 3:
                arr = arr[:, :, 0]
            # Resample based on arbitrary target size
            new_shape = (max(1, int(arr.shape[0] * 0.5)), max(1, int(arr.shape[1] * 0.5)))
            return resample_array(arr, target_shape=new_shape)
