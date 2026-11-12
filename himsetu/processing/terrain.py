"""HIMSETU — Lunar Terrain Analysis & Feature Extraction.

Extracts terrain morphology features from Digital Elevation Models (DEMs)
such as slope, aspect, terrain ruggedness (TRI), and surface curvature.
These features are essential for both ice stability analysis (sunlight shielding)
and mission planning (rover traversability and landing hazards).
"""

from __future__ import annotations

from typing import Dict
import numpy as np


def compute_slope(
    elevation: np.ndarray,
    cell_size: float = 100.0,
) -> np.ndarray:
    """Compute terrain slope in degrees from a 2D elevation grid using central differences.

    Args:
        elevation: 2D numpy array representing elevation (meters).
        cell_size: Spatial resolution of each cell in meters.

    Returns:
        2D numpy array representing slope in degrees [0, 90].
    """
    if elevation.ndim != 2:
        raise ValueError("Elevation array must be 2-dimensional.")
    if cell_size <= 0:
        raise ValueError("Cell size must be strictly positive.")

    # Calculate gradient along both axes
    dz_dy, dz_dx = np.gradient(elevation, cell_size, cell_size)

    # Slope in radians: arctan(sqrt((dz/dx)^2 + (dz/dy)^2))
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = np.degrees(slope_rad)
    return slope_deg


def compute_aspect(
    elevation: np.ndarray,
    cell_size: float = 100.0,
) -> np.ndarray:
    """Compute terrain aspect (slope direction) in degrees [0, 360] clockwise from North.

    Args:
        elevation: 2D numpy array representing elevation (meters).
        cell_size: Spatial resolution of each cell in meters.

    Returns:
        2D numpy array of aspect values where:
        0 = North, 90 = East, 180 = South, 270 = West.
        Flat terrain is assigned -1.0.
    """
    if elevation.ndim != 2:
        raise ValueError("Elevation array must be 2-dimensional.")
    if cell_size <= 0:
        raise ValueError("Cell size must be strictly positive.")

    dz_dy, dz_dx = np.gradient(elevation, cell_size, cell_size)

    # Standard GIS aspect calculation: 0 = North, 90 = East, 180 = South, 270 = West
    aspect_rad = np.arctan2(dz_dx, -dz_dy)
    aspect_deg = np.degrees(aspect_rad)
    # Convert from [-180, 180] to [0, 360]
    aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360.0, aspect_deg)

    # Flat areas (near-zero gradient) have no defined aspect
    flat_mask = np.isclose(dz_dx**2 + dz_dy**2, 0.0, atol=1e-8)
    aspect_deg[flat_mask] = -1.0

    return aspect_deg


def compute_roughness(
    elevation: np.ndarray,
    window_size: int = 3,
) -> np.ndarray:
    """Compute Terrain Ruggedness Index (TRI) representing local elevation standard deviation.

    Args:
        elevation: 2D numpy array of elevation.
        window_size: Moving window size (must be an odd integer, default 3).

    Returns:
        2D numpy array of local elevation standard deviation (meters).
    """
    if elevation.ndim != 2:
        raise ValueError("Elevation array must be 2-dimensional.")
    if window_size % 2 == 0 or window_size < 3:
        raise ValueError("Window size must be an odd integer >= 3.")

    pad = window_size // 2
    padded = np.pad(elevation, pad, mode="reflect")
    rows, cols = elevation.shape
    roughness = np.zeros((rows, cols), dtype=np.float32)

    # Compute moving standard deviation
    for r in range(rows):
        for c in range(cols):
            window = padded[r : r + window_size, c : c + window_size]
            roughness[r, c] = np.std(window)

    return roughness


def compute_terrain_features(
    elevation: np.ndarray,
    cell_size: float = 100.0,
) -> Dict[str, np.ndarray]:
    """Compute comprehensive suite of terrain morphology features.

    Returns:
        Dict containing:
        - 'elevation': original elevation array
        - 'slope': slope in degrees
        - 'aspect': aspect in degrees
        - 'roughness': local roughness/ruggedness index
    """
    slope = compute_slope(elevation, cell_size=cell_size)
    aspect = compute_aspect(elevation, cell_size=cell_size)
    roughness = compute_roughness(elevation, window_size=3)

    return {
        "elevation": elevation.copy(),
        "slope": slope,
        "aspect": aspect,
        "roughness": roughness,
    }
