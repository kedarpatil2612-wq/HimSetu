"""File type and data-category detector for HIMSETU ingestion pipeline.

Determines the DataFormat and DataCategory of a lunar dataset file based
on file extension and optional content sniffing. Never fabricates values.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from himsetu.ingestion.models import DataCategory, DataFormat

# Extension → (DataFormat, DataCategory) mapping
_EXT_MAP: dict[str, Tuple[DataFormat, DataCategory]] = {
    ".csv": (DataFormat.CSV, DataCategory.TABULAR),
    ".tif": (DataFormat.GEOTIFF, DataCategory.TERRAIN),
    ".tiff": (DataFormat.GEOTIFF, DataCategory.TERRAIN),
    ".geojson": (DataFormat.GEOJSON, DataCategory.GEOLOGICAL),
    ".nc": (DataFormat.NETCDF, DataCategory.UNKNOWN),
    ".nc4": (DataFormat.NETCDF, DataCategory.UNKNOWN),
    ".h5": (DataFormat.HDF5, DataCategory.UNKNOWN),
    ".hdf5": (DataFormat.HDF5, DataCategory.UNKNOWN),
    ".json": (DataFormat.JSON, DataCategory.UNKNOWN),
    ".txt": (DataFormat.TXT, DataCategory.UNKNOWN),
    ".png": (DataFormat.PNG, DataCategory.IMAGERY),
    ".jpg": (DataFormat.JPEG, DataCategory.IMAGERY),
    ".jpeg": (DataFormat.JPEG, DataCategory.IMAGERY),
    ".mp4": (DataFormat.MP4, DataCategory.IMAGERY),
}

# Keywords in filenames that help refine DataCategory
_CATEGORY_KEYWORDS: dict[str, DataCategory] = {
    "dem": DataCategory.TERRAIN,
    "elevation": DataCategory.TERRAIN,
    "slope": DataCategory.TERRAIN,
    "aspect": DataCategory.TERRAIN,
    "topo": DataCategory.TERRAIN,
    "thermal": DataCategory.THERMAL,
    "temperature": DataCategory.THERMAL,
    "diviner": DataCategory.THERMAL,
    "lola": DataCategory.TERRAIN,
    "radar": DataCategory.RADAR,
    "dfsar": DataCategory.RADAR,
    "lband": DataCategory.RADAR,
    "sband": DataCategory.RADAR,
    "cpr": DataCategory.RADAR,
    "psr": DataCategory.ILLUMINATION,
    "illumination": DataCategory.ILLUMINATION,
    "shadow": DataCategory.ILLUMINATION,
    "crater": DataCategory.GEOLOGICAL,
    "feature": DataCategory.GEOLOGICAL,
    "geology": DataCategory.GEOLOGICAL,
    "image": DataCategory.IMAGERY,
    "photo": DataCategory.IMAGERY,
    "optical": DataCategory.IMAGERY,
    "nac": DataCategory.IMAGERY,
    "wac": DataCategory.IMAGERY,
}


class FileDetector:
    """Detects DataFormat and DataCategory from a file path.

    Uses extension-based lookup as primary strategy, then refines the
    DataCategory using filename keyword matching. Never modifies files.
    """

    def detect(self, path: Path) -> Tuple[DataFormat, DataCategory]:
        """Return (DataFormat, DataCategory) for the given file path.

        Args:
            path: Path to the file to inspect.

        Returns:
            Tuple of detected DataFormat and DataCategory.
        """
        ext = path.suffix.lower()
        fmt, category = _EXT_MAP.get(ext, (DataFormat.UNKNOWN, DataCategory.UNKNOWN))

        # Refine category using filename keywords (case-insensitive)
        if category in (DataCategory.UNKNOWN, DataCategory.TERRAIN):
            stem_lower = path.stem.lower()
            for keyword, refined_cat in _CATEGORY_KEYWORDS.items():
                if keyword in stem_lower:
                    category = refined_cat
                    break

        return fmt, category

    def detect_format(self, path: Path) -> DataFormat:
        """Return DataFormat only."""
        return self.detect(path)[0]

    def detect_category(self, path: Path) -> DataCategory:
        """Return DataCategory only."""
        return self.detect(path)[1]
