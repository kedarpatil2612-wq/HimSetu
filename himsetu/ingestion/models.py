"""Pydantic data models for HIMSETU ingestion pipeline.

Defines enumerations and structured records for dataset metadata,
validation results, and format categorization.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataCategory(str, Enum):
    """Scientific category of a lunar dataset."""

    TERRAIN = "TERRAIN"          # DEM, elevation, slope, aspect
    THERMAL = "THERMAL"          # Diviner temperature, thermal inertia
    RADAR = "RADAR"              # L-band / S-band DFSAR data
    ILLUMINATION = "ILLUMINATION"  # PSR masks, solar illumination maps
    GEOLOGICAL = "GEOLOGICAL"    # Crater databases, rock abundance, vector features
    IMAGERY = "IMAGERY"          # Visual/optical images, video frames
    TABULAR = "TABULAR"          # CSV measurements, tabular point data
    UNKNOWN = "UNKNOWN"          # Unclassified or unrecognised content


class DataFormat(str, Enum):
    """Detected file format."""

    CSV = "CSV"
    GEOTIFF = "GeoTIFF"
    GEOJSON = "GeoJSON"
    JSON = "JSON"
    TXT = "TXT"
    NETCDF = "NetCDF"
    HDF5 = "HDF5"
    PNG = "PNG"
    JPEG = "JPEG"
    MP4 = "MP4"
    UNKNOWN = "UNKNOWN"


# Backward-compatibility aliases
LunarDataCategory = DataCategory
FileFormat = DataFormat


class ValidationStatus(str, Enum):
    """Result of format/schema validation."""

    VALID = "VALID"
    INVALID = "INVALID"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class ProcessingStatus(str, Enum):
    """Lifecycle stage of the dataset in the pipeline."""

    RAW = "RAW"
    VALIDATED = "VALIDATED"
    PREPROCESSING = "PREPROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ValidationResult(BaseModel):
    """Structured output from FileValidator."""

    status: ValidationStatus
    notes: List[str] = Field(default_factory=list)
    file_size_bytes: Optional[int] = None


class SpatialInfo(BaseModel):
    """Metadata for raster / spatial datasets."""

    crs: Optional[str] = None
    bounds: Optional[List[float]] = None   # [west, south, east, north]
    resolution_m: Optional[float] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    band_count: Optional[int] = None
    band_names: List[str] = Field(default_factory=list)
    nodata_value: Optional[float] = None


class TabularInfo(BaseModel):
    """Metadata for CSV / tabular datasets."""

    row_count: Optional[int] = None
    column_count: Optional[int] = None
    column_names: List[str] = Field(default_factory=list)
    numeric_columns: List[str] = Field(default_factory=list)


class VectorInfo(BaseModel):
    """Metadata for GeoJSON / vector datasets."""

    feature_count: Optional[int] = None
    geometry_types: List[str] = Field(default_factory=list)
    property_keys: List[str] = Field(default_factory=list)
    bounds: Optional[List[float]] = None   # [west, south, east, north]


class DatasetMetadata(BaseModel):
    """Complete provenance and metadata record for a registered lunar dataset."""

    dataset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_path: str
    format: DataFormat
    data_category: DataCategory
    source_attribution: Optional[str] = None
    file_size_bytes: Optional[int] = None
    upload_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    validation_status: ValidationStatus = ValidationStatus.SKIPPED
    validation_notes: List[str] = Field(default_factory=list)
    spatial_info: Optional[SpatialInfo] = None
    tabular_info: Optional[TabularInfo] = None
    vector_info: Optional[VectorInfo] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
    processing_status: ProcessingStatus = ProcessingStatus.RAW

    @classmethod
    def from_path(cls, path: Path, **kwargs: Any) -> "DatasetMetadata":
        """Convenience constructor from a filesystem path.

        If 'file_size_bytes' is already present in kwargs (e.g. from the
        validator result), use that value instead of re-reading from disk
        to avoid duplicate keyword argument errors.
        """
        if "file_size_bytes" not in kwargs:
            kwargs["file_size_bytes"] = path.stat().st_size if path.exists() else None
        return cls(
            filename=path.name,
            original_path=str(path.resolve()),
            **kwargs,
        )
