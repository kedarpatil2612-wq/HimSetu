"""Metadata extractor orchestrator for HIMSETU ingestion pipeline.

Dispatches to the appropriate format handler based on detected DataFormat,
assembles the unified DatasetMetadata record, and populates the correct
info sub-model (spatial_info, tabular_info, or vector_info).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from himsetu.ingestion.models import (
    DataCategory,
    DataFormat,
    DatasetMetadata,
    ProcessingStatus,
    SpatialInfo,
    TabularInfo,
    ValidationStatus,
    VectorInfo,
)
from himsetu.ingestion.detector import FileDetector
from himsetu.ingestion.validator import FileValidator


class MetadataExtractor:
    """Orchestrates validation, detection, and format-specific extraction.

    Produces a complete DatasetMetadata record for each ingested file.
    Missing or unextractable values are recorded as None; never fabricated.
    """

    def __init__(self) -> None:
        self._detector = FileDetector()
        self._validator = FileValidator()

    def extract(
        self,
        path: Path,
        source_attribution: Optional[str] = None,
    ) -> DatasetMetadata:
        """Extract full metadata for a file and return a DatasetMetadata record.

        Args:
            path: Path to the file to ingest.
            source_attribution: Optional human-readable source (e.g. "NASA PDS").

        Returns:
            DatasetMetadata populated from validation + format handler.
        """
        # 1. Validate
        validation = self._validator.validate(path)

        # 2. Detect format and category
        fmt, category = self._detector.detect(path)

        # 3. Build base record
        record = DatasetMetadata.from_path(
            path,
            format=fmt,
            data_category=category,
            source_attribution=source_attribution,
            validation_status=validation.status,
            validation_notes=validation.notes,
            file_size_bytes=validation.file_size_bytes,
            processing_status=ProcessingStatus.VALIDATED
            if validation.status == ValidationStatus.VALID
            else ProcessingStatus.RAW,
        )

        # 4. Only extract detailed metadata if file is valid
        if validation.status == ValidationStatus.INVALID:
            return record

        # 5. Dispatch to format handler
        try:
            self._populate_format_info(record, path, fmt)
        except Exception as exc:
            record.validation_notes.append(
                f"Metadata extraction warning: {exc}"
            )

        return record

    def _populate_format_info(
        self, record: DatasetMetadata, path: Path, fmt: DataFormat
    ) -> None:
        """Dispatch to the correct format handler and populate the record."""
        if fmt == DataFormat.CSV:
            from himsetu.ingestion.formats import csv_handler
            info = csv_handler.extract(path)
            record.tabular_info = TabularInfo(
                row_count=info.get("row_count"),
                column_count=info.get("column_count"),
                column_names=info.get("column_names", []),
                numeric_columns=info.get("numeric_columns", []),
            )
            record.validation_notes.extend(info.get("notes", []))

        elif fmt == DataFormat.GEOTIFF:
            from himsetu.ingestion.formats import geotiff_handler
            info = geotiff_handler.extract(path)
            record.spatial_info = SpatialInfo(
                crs=info.get("crs"),
                bounds=info.get("bounds"),
                resolution_m=info.get("resolution_m"),
                width_px=info.get("width_px"),
                height_px=info.get("height_px"),
                band_count=info.get("band_count"),
                band_names=info.get("band_names", []),
                nodata_value=info.get("nodata_value"),
            )
            record.validation_notes.extend(info.get("notes", []))

        elif fmt == DataFormat.GEOJSON:
            from himsetu.ingestion.formats import geojson_handler
            info = geojson_handler.extract(path)
            record.vector_info = VectorInfo(
                feature_count=info.get("feature_count"),
                geometry_types=info.get("geometry_types", []),
                property_keys=info.get("property_keys", []),
                bounds=info.get("bounds"),
            )
            record.validation_notes.extend(info.get("notes", []))

        elif fmt == DataFormat.NETCDF:
            from himsetu.ingestion.formats import netcdf_handler
            info = netcdf_handler.extract(path)
            record.extra.update(info)
            record.validation_notes.extend(info.get("notes", []))

        elif fmt in (DataFormat.PNG, DataFormat.JPEG):
            from himsetu.ingestion.formats import image_handler
            info = image_handler.extract(path)
            record.spatial_info = SpatialInfo(
                width_px=info.get("width_px"),
                height_px=info.get("height_px"),
            )
            record.extra.update(
                {k: v for k, v in info.items() if k not in ("width_px", "height_px", "notes")}
            )
            record.validation_notes.extend(info.get("notes", []))

        elif fmt == DataFormat.MP4:
            from himsetu.ingestion.formats import image_handler
            info = image_handler.extract(path)
            record.extra.update(info)
            record.validation_notes.extend(info.get("notes", []))

        elif fmt in (DataFormat.HDF5, DataFormat.JSON, DataFormat.TXT):
            from himsetu.ingestion.formats import generic_handler
            info = generic_handler.extract(path)
            record.extra.update(info)
            record.validation_notes.extend(info.get("notes", []))
