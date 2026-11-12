"""GeoJSON vector format handler for HIMSETU ingestion pipeline.

Extracts vector metadata (feature count, geometry types, property keys,
bounding box) from GeoJSON files using the standard json module only.
No external geospatial dependencies required for basic metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract(path: Path) -> Dict[str, Any]:
    """Extract vector metadata from a GeoJSON file.

    Args:
        path: Path to the GeoJSON file.

    Returns:
        Dictionary with keys: feature_count, geometry_types,
        property_keys, bounds, and notes.

    Raises:
        ValueError: If the file is not valid GeoJSON.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read GeoJSON file '{path}': {exc}") from exc

    notes: list[str] = []

    geojson_type = data.get("type", "")
    if geojson_type not in ("FeatureCollection", "Feature", "GeometryCollection"):
        notes.append(
            f"Unexpected GeoJSON top-level type '{geojson_type}'; "
            "expected FeatureCollection."
        )

    # Extract features list
    if geojson_type == "FeatureCollection":
        features: list[dict] = data.get("features", [])
    elif geojson_type == "Feature":
        features = [data]
    else:
        features = []
        notes.append("No feature list found in GeoJSON.")

    feature_count = len(features)

    # Collect unique geometry types
    geometry_types_set: set[str] = set()
    for feat in features:
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        if gtype:
            geometry_types_set.add(gtype)
    geometry_types: List[str] = sorted(geometry_types_set)

    # Collect unique property keys from first feature
    property_keys: List[str] = []
    if features:
        props = features[0].get("properties") or {}
        property_keys = list(props.keys())

    # Compute bounding box from CRS-agnostic coordinate scan
    bounds: Optional[List[float]] = _compute_bounds(features)

    return {
        "feature_count": feature_count,
        "geometry_types": geometry_types,
        "property_keys": property_keys,
        "bounds": bounds,
        "notes": notes,
    }


def _compute_bounds(features: list[dict]) -> Optional[List[float]]:
    """Compute [west, south, east, north] bounding box from feature coordinates."""
    lons: list[float] = []
    lats: list[float] = []

    for feat in features:
        geom = feat.get("geometry") or {}
        _collect_coords(geom.get("coordinates"), lons, lats)

    if lons and lats:
        return [min(lons), min(lats), max(lons), max(lats)]
    return None


def _collect_coords(coords: Any, lons: list, lats: list) -> None:
    """Recursively collect lon/lat values from a GeoJSON coordinates structure."""
    if coords is None:
        return
    if isinstance(coords, (list, tuple)):
        if coords and isinstance(coords[0], (int, float)):
            # Leaf coordinate pair [lon, lat, ...]
            if len(coords) >= 2:
                lons.append(float(coords[0]))
                lats.append(float(coords[1]))
        else:
            for item in coords:
                _collect_coords(item, lons, lats)
