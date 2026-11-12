"""HIMSETU — Spatial Grid Alignment Engine.

Harmonizes heterogeneous lunar datasets (varying dimensions, bounding coordinates,
and spatial resolutions) onto a standardized, unified spatial coordinate grid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from himsetu.processing.coordinates import BoundingBox
from himsetu.processing.resampler import resample_array, ResamplingMethod


@dataclass
class AlignedGrid:
    """Specification of a standardized target spatial grid."""
    shape: Tuple[int, int]  # (rows, cols)
    bbox: BoundingBox
    resolution_meters: float
    crs: str = "IAU2000:30120"

    @property
    def rows(self) -> int:
        return self.shape[0]

    @property
    def cols(self) -> int:
        return self.shape[1]

    def to_dict(self) -> dict:
        return {
            "shape": list(self.shape),
            "rows": self.rows,
            "cols": self.cols,
            "bbox": self.bbox.to_dict(),
            "resolution_meters": self.resolution_meters,
            "crs": self.crs,
        }


class SpatialAligner:
    """Aligns multiple spatial raster arrays to a unified spatial reference grid."""

    def __init__(self, target_grid: AlignedGrid) -> None:
        self.target_grid = target_grid

    def align_layer(
        self,
        data: np.ndarray,
        src_bbox: Optional[BoundingBox] = None,
        fill_value: float = np.nan,
        method: ResamplingMethod | str = ResamplingMethod.BILINEAR,
    ) -> np.ndarray:
        """Align an individual 2D raster layer to the target spatial grid.

        Args:
            data: 2D numpy array.
            src_bbox: Optional bounding box of source data.
            fill_value: Value used to pad regions outside the source coverage.
            method: Resampling method ('nearest' or 'bilinear').

        Returns:
            2D numpy array of shape self.target_grid.shape.
        """
        if data.ndim != 2:
            raise ValueError("Input data layer must be 2-dimensional.")

        target_shape = self.target_grid.shape

        # If already exactly matching shape and no bbox shift needed
        if data.shape == target_shape and src_bbox is None:
            return data.astype(np.float32).copy()

        # Resample to match target grid dimensions
        aligned = resample_array(
            data=data.astype(np.float32),
            target_shape=target_shape,
            method=method,
        )

        return aligned

    def align_layers(
        self,
        layers: Dict[str, np.ndarray],
    ) -> Dict[str, np.ndarray]:
        """Align multiple named layers simultaneously to the target grid.

        Args:
            layers: Dict mapping layer name (e.g. 'elevation', 'thermal') to 2D numpy arrays.

        Returns:
            Dict mapping layer name to aligned 2D numpy arrays of uniform shape.
        """
        aligned_dict = {}
        for name, arr in layers.items():
            aligned_dict[name] = self.align_layer(arr)
        return aligned_dict

    @classmethod
    def create_common_grid(
        cls,
        shape: Tuple[int, int] = (100, 100),
        bbox: Optional[BoundingBox] = None,
        resolution_meters: float = 100.0,
    ) -> SpatialAligner:
        """Convenience factory creating a SpatialAligner with a default polar stereographic grid."""
        if bbox is None:
            # Default south pole study window: -89.5 to -85.0 latitude
            bbox = BoundingBox(min_lat=-89.5, max_lat=-85.0, min_lon=-180.0, max_lon=180.0)

        grid = AlignedGrid(
            shape=shape,
            bbox=bbox,
            resolution_meters=resolution_meters,
        )
        return cls(target_grid=grid)
