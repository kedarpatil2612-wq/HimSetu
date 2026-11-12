"""HIMSETU — Lunar Coordinate System and Reprojection Utilities.

Standardizes coordinate reference systems for lunar datasets, specializing in
the Lunar South Pole Stereographic projection (IAU2000:30120 / Moon_South_Pole_Stereographic).
"""

from __future__ import annotations

import math
from typing import NamedTuple, Tuple
import numpy as np


# IAU Lunar Mean Radius in meters (IAU 2000 / 2015 recommendation)
MOON_RADIUS_METERS: float = 1737400.0

# PROJ4 string for Lunar South Pole Stereographic
LUNAR_SOUTH_POLE_PROJ4: str = (
    "+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"
)

# Standard IAU EPSG-like identifier
LUNAR_SOUTH_POLE_CRS_CODE: str = "IAU2000:30120"


class BoundingBox(NamedTuple):
    """Geographic bounding box for lunar datasets (degrees)."""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    def is_valid(self) -> bool:
        """Validate latitude and longitude ranges."""
        return (
            -90.0 <= self.min_lat <= self.max_lat <= 90.0
            and -180.0 <= self.min_lon <= self.max_lon <= 360.0
        )

    def is_south_polar(self, threshold_lat: float = -60.0) -> bool:
        """Check if bounding box lies completely or mostly within the south polar region."""
        return self.max_lat <= threshold_lat

    def to_dict(self) -> dict:
        return {
            "min_lat": float(self.min_lat),
            "max_lat": float(self.max_lat),
            "min_lon": float(self.min_lon),
            "max_lon": float(self.max_lon),
        }

    @classmethod
    def from_dict(cls, data: dict) -> BoundingBox:
        return cls(
            min_lat=float(data.get("min_lat", -90.0)),
            max_lat=float(data.get("max_lat", -60.0)),
            min_lon=float(data.get("min_lon", -180.0)),
            max_lon=float(data.get("max_lon", 180.0)),
        )


def latlon_to_polar_stereo(
    lat: float | np.ndarray,
    lon: float | np.ndarray,
    radius: float = MOON_RADIUS_METERS,
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    """Convert lunar latitude and longitude to South Pole Stereographic coordinates (x, y meters).

    Args:
        lat: Latitude in degrees (-90 to 0).
        lon: Longitude in degrees (-180 to 180 or 0 to 360).
        radius: Lunar spherical radius in meters.

    Returns:
        Tuple of (x, y) coordinates in meters relative to South Pole (0, 0).
    """
    is_scalar = np.isscalar(lat)
    lat_arr = np.asarray(lat, dtype=float)
    lon_arr = np.asarray(lon, dtype=float)

    # Colatitude from South Pole: 90 + lat (degrees)
    colat_deg = 90.0 + lat_arr
    colat_rad = np.radians(colat_deg)
    lon_rad = np.radians(lon_arr)

    # Tangent-plane radial distance from pole: r = 2 * R * tan(colat / 2)
    r = 2.0 * radius * np.tan(colat_rad / 2.0)

    # Projected coordinates: x along 90E, y along 0 meridian
    x = r * np.sin(lon_rad)
    y = r * np.cos(lon_rad)

    if is_scalar:
        return float(x), float(y)
    return x, y


def polar_stereo_to_latlon(
    x: float | np.ndarray,
    y: float | np.ndarray,
    radius: float = MOON_RADIUS_METERS,
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    """Convert South Pole Stereographic coordinates (x, y meters) to lunar latitude and longitude.

    Args:
        x: Projected x coordinate in meters.
        y: Projected y coordinate in meters.
        radius: Lunar spherical radius in meters.

    Returns:
        Tuple of (latitude, longitude) in degrees.
    """
    is_scalar = np.isscalar(x)
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    r = np.sqrt(x_arr**2 + y_arr**2)

    # Inverse radial distance: colat = 2 * arctan(r / (2 * R))
    colat_rad = 2.0 * np.arctan(r / (2.0 * radius))
    colat_deg = np.degrees(colat_rad)

    lat = -90.0 + colat_deg
    lon = np.degrees(np.arctan2(x_arr, y_arr))

    if is_scalar:
        return float(lat), float(lon)
    return lat, lon


class LunarCoordinates:
    """Helper class for lunar coordinate management and bounds calculations."""

    PROJ4_SOUTH_POLE = LUNAR_SOUTH_POLE_PROJ4
    CRS_CODE = LUNAR_SOUTH_POLE_CRS_CODE
    RADIUS_METERS = MOON_RADIUS_METERS

    @staticmethod
    def bbox_to_projected_extents(bbox: BoundingBox) -> Tuple[float, float, float, float]:
        """Compute projected (min_x, max_x, min_y, max_y) in meters from geographic bbox."""
        lats = [bbox.min_lat, bbox.max_lat]
        lons = [bbox.min_lon, bbox.max_lon]
        pts_x = []
        pts_y = []
        for lat in lats:
            for lon in lons:
                x, y = latlon_to_polar_stereo(lat, lon)
                pts_x.append(x)
                pts_y.append(y)
        return min(pts_x), max(pts_x), min(pts_y), max(pts_y)

    @staticmethod
    def is_in_south_polar_zone(lat: float) -> bool:
        """Return True if latitude is <= -60 deg."""
        return lat <= -60.0
