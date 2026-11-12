"""Unit test suite for HIMSETU Milestone 2: Lunar Data Ingestion Pipeline.

Tests cover: FileDetector, FileValidator, format handlers (CSV, GeoTIFF,
GeoJSON, image), MetadataExtractor, and DatasetRegistry.

All sample files used are generated synthetically and clearly labelled [SAMPLE/MOCK].
No real lunar data is fabricated or presented as original scientific measurements.
"""

from __future__ import annotations

import csv
import json
import struct
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers — synthetic [SAMPLE/MOCK] file generators
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows: int = 5) -> Path:
    """Write a minimal [SAMPLE/MOCK] CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["latitude", "longitude", "temperature_k", "label"])
        for i in range(rows):
            writer.writerow([-89.5 + i * 0.1, 0.0 + i * 0.1, 100.0 + i, "MOCK"])
    return path


def _write_geojson(path: Path, n_features: int = 3) -> Path:
    """Write a minimal [SAMPLE/MOCK] GeoJSON FeatureCollection."""
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [i * 10.0, -89.0 + i]},
            "properties": {"name": f"crater_{i}", "diameter_km": i * 2.0},
        }
        for i in range(n_features)
    ]
    data = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _write_minimal_geotiff(path: Path) -> Path:
    """Write a minimal valid [SAMPLE/MOCK] 1×1 pixel GeoTIFF using rasterio."""
    try:
        import numpy as np
        import rasterio
        from rasterio.transform import from_bounds

        transform = from_bounds(-180, -90, 180, 90, 1, 1)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=1,
            width=1,
            count=1,
            dtype=np.float32,
            crs="EPSG:4326",
            transform=transform,
        ) as ds:
            import numpy as np
            ds.write(np.array([[[1.0]]], dtype=np.float32))
    except Exception:
        # Fallback: write an empty placeholder if rasterio write fails
        path.write_bytes(b"\x00" * 256)
    return path


def _write_png(path: Path) -> Path:
    """Write a minimal 1×1 [SAMPLE/MOCK] PNG file."""
    # Minimal valid PNG (1×1 red pixel)
    import zlib
    def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    png_sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _make_chunk(b"IHDR", ihdr_data)
    raw_row = b"\x00\xff\x00\x00"  # filter byte + RGB pixel
    idat = _make_chunk(b"IDAT", zlib.compress(raw_row))
    iend = _make_chunk(b"IEND", b"")
    path.write_bytes(png_sig + ihdr + idat + iend)
    return path


def _write_json(path: Path) -> Path:
    """Write a minimal [SAMPLE/MOCK] JSON metadata file."""
    data = {"source": "MOCK", "mission": "HIMSETU_TEST", "version": "0.2.0"}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _write_txt(path: Path) -> Path:
    """Write a minimal [SAMPLE/MOCK] plain text file."""
    path.write_text("[SAMPLE/MOCK] HIMSETU test dataset.\nLine 2.\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestMilestone2(unittest.TestCase):
    """Milestone 2 — Lunar Data Ingestion Pipeline test suite."""

    def setUp(self) -> None:
        """Create a temporary working directory for all test files."""
        self._tmpdir = tempfile.mkdtemp(prefix="himsetu_m2_test_")
        self._tmp = Path(self._tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. FileDetector — extension-based detection
    # ------------------------------------------------------------------

    def test_detector_csv(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat, DataCategory
        d = FileDetector()
        fmt, cat = d.detect(Path("sample_tabular.csv"))
        self.assertEqual(fmt, DataFormat.CSV)
        self.assertEqual(cat, DataCategory.TABULAR)

    def test_detector_geotiff(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat
        d = FileDetector()
        fmt, _ = d.detect(Path("dem_sample.tif"))
        self.assertEqual(fmt, DataFormat.GEOTIFF)

    def test_detector_geotiff_tiff_ext(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat
        d = FileDetector()
        fmt, _ = d.detect(Path("elevation.tiff"))
        self.assertEqual(fmt, DataFormat.GEOTIFF)

    def test_detector_geojson(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat, DataCategory
        d = FileDetector()
        fmt, cat = d.detect(Path("craters.geojson"))
        self.assertEqual(fmt, DataFormat.GEOJSON)
        self.assertEqual(cat, DataCategory.GEOLOGICAL)

    def test_detector_png(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat, DataCategory
        d = FileDetector()
        fmt, cat = d.detect(Path("lunar_image.png"))
        self.assertEqual(fmt, DataFormat.PNG)
        self.assertEqual(cat, DataCategory.IMAGERY)

    def test_detector_mp4(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat, DataCategory
        d = FileDetector()
        fmt, cat = d.detect(Path("flyover.mp4"))
        self.assertEqual(fmt, DataFormat.MP4)
        self.assertEqual(cat, DataCategory.IMAGERY)

    def test_detector_unknown_extension(self):
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataFormat, DataCategory
        d = FileDetector()
        fmt, cat = d.detect(Path("mystery.xyz"))
        self.assertEqual(fmt, DataFormat.UNKNOWN)
        self.assertEqual(cat, DataCategory.UNKNOWN)

    def test_detector_keyword_refinement_dem(self):
        """Filename 'lola_dem.tif' should refine category to TERRAIN."""
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataCategory
        d = FileDetector()
        _, cat = d.detect(Path("lola_dem.tif"))
        self.assertEqual(cat, DataCategory.TERRAIN)

    def test_detector_keyword_refinement_thermal(self):
        """Filename 'diviner_thermal.tif' should refine category to THERMAL."""
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataCategory
        d = FileDetector()
        _, cat = d.detect(Path("diviner_thermal.tif"))
        self.assertEqual(cat, DataCategory.THERMAL)

    def test_detector_keyword_refinement_radar(self):
        """Filename 'dfsar_lband.tif' should refine category to RADAR."""
        from himsetu.ingestion.detector import FileDetector
        from himsetu.ingestion.models import DataCategory
        d = FileDetector()
        _, cat = d.detect(Path("dfsar_lband.tif"))
        self.assertEqual(cat, DataCategory.RADAR)

    # ------------------------------------------------------------------
    # 2. FileValidator
    # ------------------------------------------------------------------

    def test_validator_nonexistent_file(self):
        from himsetu.ingestion.validator import FileValidator
        from himsetu.ingestion.models import ValidationStatus
        v = FileValidator()
        result = v.validate(self._tmp / "does_not_exist.csv")
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(any("does not exist" in n for n in result.notes))

    def test_validator_empty_file(self):
        from himsetu.ingestion.validator import FileValidator
        from himsetu.ingestion.models import ValidationStatus
        p = self._tmp / "empty.csv"
        p.write_bytes(b"")
        v = FileValidator()
        result = v.validate(p)
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertEqual(result.file_size_bytes, 0)

    def test_validator_valid_file(self):
        from himsetu.ingestion.validator import FileValidator
        from himsetu.ingestion.models import ValidationStatus
        p = _write_csv(self._tmp / "valid.csv")
        v = FileValidator()
        result = v.validate(p)
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertGreater(result.file_size_bytes, 0)

    def test_validator_directory_rejected(self):
        from himsetu.ingestion.validator import FileValidator
        from himsetu.ingestion.models import ValidationStatus
        v = FileValidator()
        result = v.validate(self._tmp)  # directory, not a file
        self.assertEqual(result.status, ValidationStatus.INVALID)

    # ------------------------------------------------------------------
    # 3. CSV handler
    # ------------------------------------------------------------------

    def test_csv_handler_basic(self):
        from himsetu.ingestion.formats.csv_handler import extract
        p = _write_csv(self._tmp / "test.csv", rows=5)
        info = extract(p)
        self.assertEqual(info["row_count"], 5)
        self.assertEqual(info["column_count"], 4)
        self.assertIn("latitude", info["column_names"])
        self.assertIn("longitude", info["column_names"])

    def test_csv_handler_numeric_detection(self):
        from himsetu.ingestion.formats.csv_handler import extract
        p = _write_csv(self._tmp / "numeric.csv", rows=3)
        info = extract(p)
        self.assertIn("latitude", info["numeric_columns"])
        self.assertIn("temperature_k", info["numeric_columns"])

    def test_csv_handler_empty_raises(self):
        from himsetu.ingestion.formats.csv_handler import extract
        p = self._tmp / "empty.csv"
        p.write_bytes(b"")
        # Empty file: should return 0 rows gracefully
        info = extract(p)
        self.assertEqual(info["row_count"], 0)

    # ------------------------------------------------------------------
    # 4. GeoJSON handler
    # ------------------------------------------------------------------

    def test_geojson_handler_feature_count(self):
        from himsetu.ingestion.formats.geojson_handler import extract
        p = _write_geojson(self._tmp / "craters.geojson", n_features=5)
        info = extract(p)
        self.assertEqual(info["feature_count"], 5)

    def test_geojson_handler_geometry_type(self):
        from himsetu.ingestion.formats.geojson_handler import extract
        p = _write_geojson(self._tmp / "points.geojson", n_features=2)
        info = extract(p)
        self.assertIn("Point", info["geometry_types"])

    def test_geojson_handler_property_keys(self):
        from himsetu.ingestion.formats.geojson_handler import extract
        p = _write_geojson(self._tmp / "props.geojson", n_features=1)
        info = extract(p)
        self.assertIn("name", info["property_keys"])
        self.assertIn("diameter_km", info["property_keys"])

    def test_geojson_handler_bounds(self):
        from himsetu.ingestion.formats.geojson_handler import extract
        p = _write_geojson(self._tmp / "bounds.geojson", n_features=3)
        info = extract(p)
        self.assertIsNotNone(info["bounds"])
        self.assertEqual(len(info["bounds"]), 4)

    def test_geojson_handler_invalid_raises(self):
        from himsetu.ingestion.formats.geojson_handler import extract
        p = self._tmp / "bad.geojson"
        p.write_text("NOT JSON {{{", encoding="utf-8")
        with self.assertRaises(ValueError):
            extract(p)

    # ------------------------------------------------------------------
    # 5. Image handler
    # ------------------------------------------------------------------

    def test_image_handler_png(self):
        from himsetu.ingestion.formats.image_handler import extract
        p = _write_png(self._tmp / "lunar.png")
        info = extract(p)
        self.assertEqual(info["width_px"], 1)
        self.assertEqual(info["height_px"], 1)
        self.assertTrue(any("IMAGERY" in n for n in info["notes"]))

    # ------------------------------------------------------------------
    # 6. Generic / JSON handler
    # ------------------------------------------------------------------

    def test_generic_json_handler(self):
        from himsetu.ingestion.formats.generic_handler import extract
        p = _write_json(self._tmp / "meta.json")
        info = extract(p)
        self.assertIn("source", info["top_level_keys"])

    def test_generic_txt_handler(self):
        from himsetu.ingestion.formats.generic_handler import extract
        p = _write_txt(self._tmp / "notes.txt")
        info = extract(p)
        self.assertGreaterEqual(info["line_count"], 1)

    # ------------------------------------------------------------------
    # 7. MetadataExtractor — end-to-end
    # ------------------------------------------------------------------

    def test_extractor_csv_end_to_end(self):
        from himsetu.ingestion.metadata import MetadataExtractor
        from himsetu.ingestion.models import DataFormat, DataCategory, ValidationStatus
        p = _write_csv(self._tmp / "e2e.csv", rows=10)
        ext = MetadataExtractor()
        record = ext.extract(p, source_attribution="[SAMPLE/MOCK]")
        self.assertEqual(record.format, DataFormat.CSV)
        self.assertEqual(record.data_category, DataCategory.TABULAR)
        self.assertEqual(record.validation_status, ValidationStatus.VALID)
        self.assertIsNotNone(record.tabular_info)
        self.assertEqual(record.tabular_info.row_count, 10)
        self.assertEqual(record.source_attribution, "[SAMPLE/MOCK]")

    def test_extractor_geojson_end_to_end(self):
        from himsetu.ingestion.metadata import MetadataExtractor
        from himsetu.ingestion.models import DataFormat
        p = _write_geojson(self._tmp / "e2e.geojson", n_features=4)
        ext = MetadataExtractor()
        record = ext.extract(p)
        self.assertEqual(record.format, DataFormat.GEOJSON)
        self.assertIsNotNone(record.vector_info)
        self.assertEqual(record.vector_info.feature_count, 4)

    def test_extractor_invalid_file(self):
        from himsetu.ingestion.metadata import MetadataExtractor
        from himsetu.ingestion.models import ValidationStatus
        ext = MetadataExtractor()
        record = ext.extract(self._tmp / "missing.csv")
        self.assertEqual(record.validation_status, ValidationStatus.INVALID)
        self.assertIsNone(record.tabular_info)

    def test_extractor_unknown_format(self):
        from himsetu.ingestion.metadata import MetadataExtractor
        from himsetu.ingestion.models import DataFormat, DataCategory
        p = self._tmp / "mystery.xyz"
        p.write_text("hello world", encoding="utf-8")
        ext = MetadataExtractor()
        record = ext.extract(p)
        self.assertEqual(record.format, DataFormat.UNKNOWN)
        self.assertEqual(record.data_category, DataCategory.UNKNOWN)

    # ------------------------------------------------------------------
    # 8. DatasetRegistry
    # ------------------------------------------------------------------

    def test_registry_add_and_get(self):
        from himsetu.ingestion.registry import DatasetRegistry
        from himsetu.ingestion.metadata import MetadataExtractor
        reg_path = self._tmp / "registry.json"
        registry = DatasetRegistry(registry_path=reg_path)
        p = _write_csv(self._tmp / "reg_test.csv", rows=3)
        ext = MetadataExtractor()
        record = ext.extract(p)
        dataset_id = registry.add(record)
        retrieved = registry.get(dataset_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.dataset_id, dataset_id)
        self.assertEqual(retrieved.filename, "reg_test.csv")

    def test_registry_list_all(self):
        from himsetu.ingestion.registry import DatasetRegistry
        from himsetu.ingestion.metadata import MetadataExtractor
        reg_path = self._tmp / "registry2.json"
        registry = DatasetRegistry(registry_path=reg_path)
        ext = MetadataExtractor()
        for i in range(3):
            p = _write_csv(self._tmp / f"file_{i}.csv", rows=2)
            registry.add(ext.extract(p))
        all_records = registry.list_all()
        self.assertEqual(len(all_records), 3)

    def test_registry_remove(self):
        from himsetu.ingestion.registry import DatasetRegistry
        from himsetu.ingestion.metadata import MetadataExtractor
        reg_path = self._tmp / "registry3.json"
        registry = DatasetRegistry(registry_path=reg_path)
        p = _write_csv(self._tmp / "removable.csv", rows=2)
        ext = MetadataExtractor()
        did = registry.add(ext.extract(p))
        self.assertTrue(registry.remove(did))
        self.assertIsNone(registry.get(did))
        self.assertFalse(registry.remove(did))

    def test_registry_count(self):
        from himsetu.ingestion.registry import DatasetRegistry
        from himsetu.ingestion.metadata import MetadataExtractor
        reg_path = self._tmp / "registry4.json"
        registry = DatasetRegistry(registry_path=reg_path)
        ext = MetadataExtractor()
        self.assertEqual(registry.count(), 0)
        p = _write_csv(self._tmp / "counted.csv", rows=1)
        registry.add(ext.extract(p))
        self.assertEqual(registry.count(), 1)

    def test_registry_persistence(self):
        """Records persist across DatasetRegistry instances (reload from disk)."""
        from himsetu.ingestion.registry import DatasetRegistry
        from himsetu.ingestion.metadata import MetadataExtractor
        reg_path = self._tmp / "persist.json"
        ext = MetadataExtractor()
        p = _write_csv(self._tmp / "persist.csv", rows=2)

        r1 = DatasetRegistry(registry_path=reg_path)
        did = r1.add(ext.extract(p))

        r2 = DatasetRegistry(registry_path=reg_path)
        loaded = r2.get(did)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.dataset_id, did)

    def test_registry_find_by_category(self):
        from himsetu.ingestion.registry import DatasetRegistry
        from himsetu.ingestion.metadata import MetadataExtractor
        reg_path = self._tmp / "registry5.json"
        registry = DatasetRegistry(registry_path=reg_path)
        ext = MetadataExtractor()
        csv_p = _write_csv(self._tmp / "tabular.csv", rows=2)
        geojson_p = _write_geojson(self._tmp / "vector.geojson", n_features=2)
        registry.add(ext.extract(csv_p))
        registry.add(ext.extract(geojson_p))
        tabular = registry.find_by_category("TABULAR")
        self.assertEqual(len(tabular), 1)
        geological = registry.find_by_category("GEOLOGICAL")
        self.assertEqual(len(geological), 1)


if __name__ == "__main__":
    unittest.main()
