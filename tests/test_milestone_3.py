"""Unit and integration test suite for HIMSETU Milestone 3:
Lunar Data Processing Engine, Reprojection, SQLite Persistence, and REST API Backend.
"""

from __future__ import annotations

import io
import math
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np

from himsetu.api.app import create_app
from himsetu.db.database import Database
from himsetu.db.repository import DatasetRepository, JobRepository
from himsetu.engine import HimSetuEngine
from himsetu.ingestion.models import (
    DataCategory,
    DataFormat,
    DatasetMetadata,
    SpatialInfo,
)
from himsetu.ingestion.registry import DatasetRegistry
from himsetu.processing.aligner import AlignedGrid, SpatialAligner
from himsetu.processing.coordinates import (
    BoundingBox,
    LunarCoordinates,
    latlon_to_polar_stereo,
    polar_stereo_to_latlon,
)
from himsetu.processing.resampler import resample_array, ResamplingMethod
from himsetu.processing.stacker import FeatureCube, FeatureStacker
from himsetu.processing.terrain import (
    compute_aspect,
    compute_roughness,
    compute_slope,
    compute_terrain_features,
)


class TestMilestone3Coordinates(unittest.TestCase):
    """Test suite for Lunar coordinate systems and Polar Stereographic reprojection."""

    def test_south_pole_center_projection(self):
        """South Pole (-90, 0) must project exactly to origin (0, 0)."""
        x, y = latlon_to_polar_stereo(-90.0, 0.0)
        self.assertAlmostEqual(x, 0.0, places=4)
        self.assertAlmostEqual(y, 0.0, places=4)

        lat, lon = polar_stereo_to_latlon(0.0, 0.0)
        self.assertAlmostEqual(lat, -90.0, places=4)

    def test_coordinate_round_trip(self):
        """Converting lat/lon to stereographic and back should restore original coordinates."""
        test_points = [
            (-89.9, 0.0),
            (-85.0, 45.0),
            (-80.0, -120.0),
            (-75.0, 180.0),
        ]
        for lat_in, lon_in in test_points:
            x, y = latlon_to_polar_stereo(lat_in, lon_in)
            lat_out, lon_out = polar_stereo_to_latlon(x, y)
            self.assertAlmostEqual(lat_in, lat_out, places=4)
            # Normalize longitude difference
            lon_diff = (lon_in - lon_out + 180.0) % 360.0 - 180.0
            self.assertAlmostEqual(lon_diff, 0.0, places=4)

    def test_vectorized_coordinates(self):
        """Vectorized numpy array coordinate conversion."""
        lats = np.array([-90.0, -88.0, -85.0])
        lons = np.array([0.0, 90.0, 180.0])
        x, y = latlon_to_polar_stereo(lats, lons)
        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)
        lats_back, lons_back = polar_stereo_to_latlon(x, y)
        np.testing.assert_allclose(lats, lats_back, atol=1e-4)

    def test_bounding_box_validity(self):
        bbox = BoundingBox(min_lat=-89.0, max_lat=-80.0, min_lon=-180.0, max_lon=180.0)
        self.assertTrue(bbox.is_valid())
        self.assertTrue(bbox.is_south_polar())

        invalid_bbox = BoundingBox(min_lat=10.0, max_lat=-10.0, min_lon=0.0, max_lon=10.0)
        self.assertFalse(invalid_bbox.is_valid())

        d = bbox.to_dict()
        self.assertEqual(d["min_lat"], -89.0)
        reloaded = BoundingBox.from_dict(d)
        self.assertEqual(reloaded, bbox)


class TestMilestone3Terrain(unittest.TestCase):
    """Test suite for Lunar terrain morphology calculations (slope, aspect, roughness)."""

    def test_flat_terrain_slope_zero(self):
        """Flat elevation grid must produce 0-degree slope."""
        flat = np.full((20, 20), 1000.0, dtype=np.float32)
        slope = compute_slope(flat, cell_size=100.0)
        np.testing.assert_allclose(slope, 0.0, atol=1e-5)

    def test_inclined_plane_slope(self):
        """Inclined plane rising 100m over 100m horizontal distance has 45 deg slope."""
        cols = np.arange(20, dtype=np.float32) * 100.0  # dz/dx = 1.0
        elev = np.tile(cols, (20, 1))
        slope = compute_slope(elev, cell_size=100.0)
        # Inner cells away from borders should be ~45 degrees
        inner_slope = slope[2:-2, 2:-2]
        np.testing.assert_allclose(inner_slope, 45.0, atol=1e-2)

    def test_aspect_calculation(self):
        """Aspect returns values in range [0, 360] or -1 for flat."""
        flat = np.full((10, 10), 500.0, dtype=np.float32)
        aspect_flat = compute_aspect(flat, cell_size=100.0)
        self.assertTrue(np.all(aspect_flat == -1.0))

    def test_roughness_calculation(self):
        """Roughness on smooth flat terrain must be zero; on noisy terrain must be > 0."""
        flat = np.full((15, 15), 200.0, dtype=np.float32)
        r_flat = compute_roughness(flat, window_size=3)
        np.testing.assert_allclose(r_flat, 0.0, atol=1e-5)

        noisy = flat.copy()
        noisy[7, 7] = 500.0
        r_noisy = compute_roughness(noisy, window_size=3)
        self.assertGreater(r_noisy[7, 7], 0.0)

    def test_compute_terrain_features_bundle(self):
        elev = np.random.uniform(0, 1000, (25, 25)).astype(np.float32)
        feats = compute_terrain_features(elev, cell_size=50.0)
        self.assertIn("elevation", feats)
        self.assertIn("slope", feats)
        self.assertIn("aspect", feats)
        self.assertIn("roughness", feats)
        self.assertEqual(feats["slope"].shape, (25, 25))


class TestMilestone3ResamplingAndAlignment(unittest.TestCase):
    """Test suite for array resampling, spatial grid alignment, and feature cube stacking."""

    def test_resample_array_nearest_and_bilinear(self):
        data = np.arange(16, dtype=np.float32).reshape((4, 4))

        # Upsample to 8x8
        resampled_up = resample_array(data, target_shape=(8, 8), method=ResamplingMethod.BILINEAR)
        self.assertEqual(resampled_up.shape, (8, 8))

        # Downsample to 2x2
        resampled_down = resample_array(data, target_shape=(2, 2), method=ResamplingMethod.NEAREST)
        self.assertEqual(resampled_down.shape, (2, 2))

    def test_spatial_aligner_single_layer(self):
        grid = AlignedGrid(
            shape=(50, 50),
            bbox=BoundingBox(min_lat=-89.0, max_lat=-85.0, min_lon=-180.0, max_lon=180.0),
            resolution_meters=100.0,
        )
        aligner = SpatialAligner(target_grid=grid)

        layer_10x10 = np.ones((10, 10), dtype=np.float32) * 5.0
        aligned = aligner.align_layer(layer_10x10)
        self.assertEqual(aligned.shape, (50, 50))
        np.testing.assert_allclose(aligned, 5.0, atol=1e-4)

    def test_feature_stacker_with_missing_layers(self):
        """FeatureStacker must track available vs missing layers without fabricating fake data."""
        grid = AlignedGrid(
            shape=(30, 30),
            bbox=BoundingBox(min_lat=-89.0, max_lat=-86.0, min_lon=-180.0, max_lon=180.0),
            resolution_meters=100.0,
        )
        stacker = FeatureStacker(target_grid=grid)

        # Provide only elevation and thermal; sar_cpr and psr_mask are omitted
        raw_layers = {
            "elevation": np.full((30, 30), 1200.0, dtype=np.float32),
            "thermal": np.full((30, 30), 85.0, dtype=np.float32),
        }

        cube = stacker.stack_layers(raw_layers, auto_derive_terrain=True)

        self.assertIsInstance(cube, FeatureCube)
        self.assertIn("elevation", cube.available_features)
        self.assertIn("slope", cube.available_features)  # auto-derived
        self.assertIn("aspect", cube.available_features)  # auto-derived
        self.assertIn("thermal", cube.available_features)

        # sar_cpr must be missing and filled with NaN
        self.assertIn("sar_cpr", cube.missing_features)
        sar_slice = cube.get_channel("sar_cpr")
        self.assertTrue(np.all(np.isnan(sar_slice)))


class TestMilestone3Database(unittest.TestCase):
    """Test suite for SQLite metadata repository and job tracking."""

    def setUp(self):
        self.db = Database(":memory:")
        self.repo = DatasetRepository(self.db)
        self.job_repo = JobRepository(self.db)

    def test_save_and_retrieve_dataset(self):
        meta = DatasetMetadata(
            dataset_id="test_ds_01",
            filename="LOLA_DEM_SouthPole.tif",
            original_path="data/raw/LOLA_DEM_SouthPole.tif",
            data_category=DataCategory.TERRAIN,
            format=DataFormat.GEOTIFF,
            file_size_bytes=1048576,
            spatial_info=SpatialInfo(
                crs="IAU2000:30120",
                bounds=[-180.0, -89.5, 180.0, -87.0],
                resolution_m=20.0,
            ),
            extra={"tags": ["polar", "elevation"]},
        )
        self.repo.save(meta)
        self.assertEqual(self.repo.count(), 1)

        retrieved = self.repo.get_by_id("test_ds_01")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "LOLA_DEM_SouthPole.tif")
        self.assertEqual(retrieved["category"], "TERRAIN")
        self.assertEqual(retrieved["tags"], ["polar", "elevation"])

    def test_dataset_filtering_and_deletion(self):
        ds1 = DatasetMetadata(
            dataset_id="ds_1",
            filename="dem.tif",
            original_path="dem.tif",
            data_category=DataCategory.TERRAIN,
            format=DataFormat.GEOTIFF,
        )
        ds2 = DatasetMetadata(
            dataset_id="ds_2",
            filename="thermal.csv",
            original_path="thermal.csv",
            data_category=DataCategory.THERMAL,
            format=DataFormat.CSV,
        )
        self.repo.save(ds1)
        self.repo.save(ds2)

        # Filter by category
        dem_list = self.repo.list_all(category="TERRAIN")
        self.assertEqual(len(dem_list), 1)
        self.assertEqual(dem_list[0]["id"], "ds_1")

        # Deletion
        deleted = self.repo.delete("ds_1")
        self.assertTrue(deleted)
        self.assertEqual(self.repo.count(), 1)
        self.assertIsNone(self.repo.get_by_id("ds_1"))

    def test_job_repository_lifecycle(self):
        job = self.job_repo.create_job(
            job_id="job_align_99",
            job_type="align",
            parameters={"resolution": 50.0},
        )
        self.assertEqual(job["status"], "PENDING")

        self.job_repo.update_status(
            job_id="job_align_99",
            status="COMPLETED",
            output_path="data/processed/aligned_cube.npy",
        )
        retrieved = self.job_repo.get_by_id("job_align_99")
        self.assertEqual(retrieved["status"], "COMPLETED")
        self.assertEqual(retrieved["output_path"], "data/processed/aligned_cube.npy")


class TestMilestone3FastAPI(unittest.TestCase):
    """Test suite for FastAPI endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.engine = HimSetuEngine()
        cls.engine.initialize()
        cls.db = Database(":memory:")
        cls.registry = DatasetRegistry()
        cls.app = create_app(engine=cls.engine, registry=cls.registry, db=cls.db)
        cls.client = TestClient(cls.app)

    def test_health_endpoints(self):
        for route in ("/health", "/api/v1/health"):
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["version"], "0.3.0")
            self.assertEqual(data["engine_state"], "READY")

    def test_system_status(self):
        res = self.client.get("/api/v1/system/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "operational")
        self.assertEqual(data["engine_state"], "READY")

    def test_dataset_upload_and_crud(self):
        csv_content = b"lat,lon,temperature\n-89.5,0.0,85.2\n-89.6,10.0,90.4\n"
        files = {
            "file": ("diviner_sample_test.csv", io.BytesIO(csv_content), "text/csv"),
        }
        res = self.client.post(
            "/api/v1/datasets/upload",
            files=files,
            data={"custom_name": "Diviner Sample Test", "tags": "diviner,thermal"},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["success"])
        ds_id = data["dataset"]["id"]

        # Fetch detail
        detail_res = self.client.get(f"/api/v1/datasets/{ds_id}")
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.json()["dataset"]["name"], "Diviner Sample Test")

        # List all
        list_res = self.client.get("/api/v1/datasets")
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(list_res.json()["count"], 1)

        # Delete
        del_res = self.client.delete(f"/api/v1/datasets/{ds_id}")
        self.assertEqual(del_res.status_code, 200)

        # Verify 404
        after_del = self.client.get(f"/api/v1/datasets/{ds_id}")
        self.assertEqual(after_del.status_code, 404)

    def test_processing_terrain_endpoint(self):
        elev_matrix = [
            [100.0, 100.0, 100.0],
            [100.0, 100.0, 100.0],
            [100.0, 100.0, 100.0],
        ]
        res = self.client.post(
            "/api/v1/processing/terrain",
            json={"elevation_grid": elev_matrix, "cell_size_meters": 100.0},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["shape"], [3, 3])
        # Flat slope must be 0.0
        self.assertAlmostEqual(data["slope_deg"][1][1], 0.0, places=4)

    def test_processing_align_endpoint(self):
        res = self.client.post(
            "/api/v1/processing/align",
            json={
                "layer_names": ["elevation", "thermal"],
                "target_resolution_meters": 50.0,
                "grid_shape": [64, 64],
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["grid_shape"], [64, 64])
        self.assertEqual(data["crs"], "IAU2000:30120")

    def test_processing_stack_endpoint(self):
        res = self.client.post(
            "/api/v1/processing/stack",
            json={
                "dataset_ids": [],
                "auto_derive_terrain": True,
                "target_shape": [50, 50],
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("elevation", data["channels"])
        self.assertIn("sar_cpr", data["channels"])


if __name__ == "__main__":
    unittest.main()
