"""HIMSETU — Lunar Data Processing Engine.

Milestone 3: Data preprocessing, coordinate reprojection, spatial alignment,
terrain feature extraction, and multi-source feature cube stacking.
"""

from himsetu.processing.coordinates import (
    LunarCoordinates,
    BoundingBox,
    latlon_to_polar_stereo,
    polar_stereo_to_latlon,
)
from himsetu.processing.terrain import (
    compute_slope,
    compute_aspect,
    compute_roughness,
    compute_terrain_features,
)
from himsetu.processing.resampler import (
    resample_array,
    resample_raster,
)
from himsetu.processing.aligner import (
    SpatialAligner,
    AlignedGrid,
)
from himsetu.processing.stacker import (
    FeatureStacker,
    FeatureCube,
)

__all__ = [
    "LunarCoordinates",
    "BoundingBox",
    "latlon_to_polar_stereo",
    "polar_stereo_to_latlon",
    "compute_slope",
    "compute_aspect",
    "compute_roughness",
    "compute_terrain_features",
    "resample_array",
    "resample_raster",
    "SpatialAligner",
    "AlignedGrid",
    "FeatureStacker",
    "FeatureCube",
]
