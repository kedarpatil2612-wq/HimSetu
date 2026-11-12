"""HIMSETU Data Ingestion Package — M2.

Provides modular lunar dataset ingestion: file detection, validation,
metadata extraction, format handlers, and dataset registry.
"""

from himsetu.ingestion.models import (
    DataCategory,
    DataFormat,
    ValidationStatus,
    ProcessingStatus,
    ValidationResult,
    SpatialInfo,
    TabularInfo,
    VectorInfo,
    DatasetMetadata,
)
from himsetu.ingestion.detector import FileDetector
from himsetu.ingestion.validator import FileValidator
from himsetu.ingestion.metadata import MetadataExtractor
from himsetu.ingestion.registry import DatasetRegistry

__all__ = [
    "DataCategory",
    "DataFormat",
    "ValidationStatus",
    "ProcessingStatus",
    "ValidationResult",
    "SpatialInfo",
    "TabularInfo",
    "VectorInfo",
    "DatasetMetadata",
    "FileDetector",
    "FileValidator",
    "MetadataExtractor",
    "DatasetRegistry",
]
