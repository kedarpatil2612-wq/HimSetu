"""HIMSETU — Multi-Source Feature Cube Stacker.

Combines heterogeneous lunar data layers (DEM, derived slope/aspect, thermal,
radar CPR, PSR masks) into a unified multi-band feature cube.

Strict Scientific Principle:
Missing datasets are explicitly identified and marked as unavailable.
Values for missing layers are NEVER silently fabricated or filled with fake measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from himsetu.processing.aligner import AlignedGrid, SpatialAligner
from himsetu.processing.terrain import compute_terrain_features


# Standard ordered canonical feature channels for lunar subsurface ice analysis
CANONICAL_CHANNELS: List[str] = [
    "elevation",
    "slope",
    "aspect",
    "roughness",
    "thermal",
    "sar_cpr",
    "psr_mask",
    "illumination",
]


@dataclass
class FeatureCube:
    """Multi-channel aligned 3D spatial tensor of lunar geophysical features."""
    data: np.ndarray  # Shape: (channels, rows, cols)
    channel_names: List[str]
    grid: AlignedGrid
    available_features: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)

    @property
    def num_channels(self) -> int:
        return self.data.shape[0]

    @property
    def shape(self) -> tuple:
        return self.data.shape

    def get_channel(self, name: str) -> np.ndarray:
        """Retrieve 2D spatial slice for a named channel."""
        if name not in self.channel_names:
            raise KeyError(f"Channel '{name}' not found in FeatureCube. Available: {self.channel_names}")
        idx = self.channel_names.index(name)
        return self.data[idx]

    def has_feature(self, name: str) -> bool:
        """Check whether a feature was provided with real data."""
        return name in self.available_features

    def to_dict(self) -> dict:
        """Summary representation of the feature cube."""
        return {
            "shape": list(self.data.shape),
            "channels": self.channel_names,
            "available_features": self.available_features,
            "missing_features": self.missing_features,
            "grid": self.grid.to_dict(),
        }


class FeatureStacker:
    """Builds unified multi-channel FeatureCubes from available lunar datasets."""

    def __init__(self, target_grid: AlignedGrid) -> None:
        self.target_grid = target_grid
        self.aligner = SpatialAligner(target_grid=target_grid)

    def stack_layers(
        self,
        raw_layers: Dict[str, np.ndarray],
        auto_derive_terrain: bool = True,
        channels: Optional[List[str]] = None,
    ) -> FeatureCube:
        """Combine provided raw layers into an aligned FeatureCube.

        Args:
            raw_layers: Dict mapping feature name (e.g. 'elevation', 'thermal', 'sar_cpr')
                        to 2D numpy arrays.
            auto_derive_terrain: If True and 'elevation' is supplied, automatically
                                 computes 'slope', 'aspect', and 'roughness'.
            channels: Optional custom list of channels to include (defaults to CANONICAL_CHANNELS).

        Returns:
            FeatureCube instance with aligned 3D tensor and layer availability metadata.
        """
        active_channels = channels or CANONICAL_CHANNELS.copy()
        layers_to_align: Dict[str, np.ndarray] = {}

        # 1. Copy user provided layers
        for key, arr in raw_layers.items():
            layers_to_align[key] = arr

        # 2. Auto-derive terrain morphology if elevation is available
        if auto_derive_terrain and "elevation" in layers_to_align:
            elev_aligned = self.aligner.align_layer(layers_to_align["elevation"])
            terrain_morph = compute_terrain_features(
                elev_aligned,
                cell_size=self.target_grid.resolution_meters,
            )
            for feat_name, feat_arr in terrain_morph.items():
                if feat_name not in layers_to_align or layers_to_align[feat_name] is None:
                    layers_to_align[feat_name] = feat_arr

        # 3. Align all available layers
        aligned_layers: Dict[str, np.ndarray] = {}
        available_features: List[str] = []
        missing_features: List[str] = []

        for ch in active_channels:
            if ch in layers_to_align and layers_to_align[ch] is not None:
                aligned_layers[ch] = self.aligner.align_layer(layers_to_align[ch])
                available_features.append(ch)
            else:
                # Mark as missing: filled with NaN according to scientific data integrity rule
                nan_layer = np.full(self.target_grid.shape, np.nan, dtype=np.float32)
                aligned_layers[ch] = nan_layer
                missing_features.append(ch)

        # 4. Construct 3D tensor (C, H, W)
        cube_tensor = np.stack(
            [aligned_layers[ch] for ch in active_channels],
            axis=0,
        ).astype(np.float32)

        return FeatureCube(
            data=cube_tensor,
            channel_names=active_channels,
            grid=self.target_grid,
            available_features=available_features,
            missing_features=missing_features,
        )
