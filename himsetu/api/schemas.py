"""HIMSETU — Pydantic Schemas for REST API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.3.0"
    engine_state: str
    datasets_count: int
    uptime_seconds: float = 0.0


class SystemStatusResponse(BaseModel):
    status: str
    engine_state: str
    active_permissions: str
    version: str = "0.3.0"
    registered_datasets: int


class DatasetSummary(BaseModel):
    id: str
    name: str
    file_path: str
    category: str
    file_format: str
    file_size_bytes: int
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None
    crs: Optional[str] = None
    resolution_meters: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    created_at: str


class DatasetListResponse(BaseModel):
    count: int
    datasets: List[DatasetSummary]


class DatasetDetailResponse(BaseModel):
    dataset: DatasetSummary
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UploadDatasetResponse(BaseModel):
    success: bool
    message: str
    dataset: DatasetSummary


class TerrainFeatureRequest(BaseModel):
    elevation_grid: List[List[float]]
    cell_size_meters: float = 100.0


class TerrainFeatureResponse(BaseModel):
    shape: List[int]
    cell_size_meters: float
    slope_deg: List[List[float]]
    aspect_deg: List[List[float]]
    roughness: List[List[float]]


class SpatialAlignRequest(BaseModel):
    layer_names: List[str]
    target_resolution_meters: float = 100.0
    grid_shape: List[int] = Field(default_factory=lambda: [100, 100])


class SpatialAlignResponse(BaseModel):
    success: bool
    grid_shape: List[int]
    resolution_meters: float
    aligned_layers: List[str]
    crs: str = "IAU2000:30120"


class FeatureStackRequest(BaseModel):
    dataset_ids: List[str] = Field(default_factory=list)
    auto_derive_terrain: bool = True
    target_shape: List[int] = Field(default_factory=lambda: [100, 100])


class FeatureStackResponse(BaseModel):
    success: bool
    channels: List[str]
    available_features: List[str]
    missing_features: List[str]
    shape: List[int]
