"""HimSetu Mini — Unit Test Suite (Mini Project).

Tests dataset generation, CSV loading, model training/prediction,
and visualizer output correctness.

Run:
    .venv\\Scripts\\python.exe -m pytest mini/tests/test_mini.py -v
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mini.dataset import (
    ALL_FEATURE_COLS,
    LABEL_COL,
    OPTIONAL_FEATURE_COLS,
    REQUIRED_FEATURE_COLS,
    DatasetValidationError,
    generate_synthetic_dataset,
    get_feature_matrix,
    load_csv,
)
from mini.model import IceProbabilityModel, ModelMetrics, PredictionResult


# ──────────────────────────────────────────────────────────────────────────────
# Dataset Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestSyntheticDataset(unittest.TestCase):

    def setUp(self):
        self.df = generate_synthetic_dataset(n_samples=200, seed=0)

    def test_returns_dataframe(self):
        self.assertIsInstance(self.df, pd.DataFrame)

    def test_correct_row_count(self):
        self.assertEqual(len(self.df), 200)

    def test_required_columns_present(self):
        for col in REQUIRED_FEATURE_COLS + OPTIONAL_FEATURE_COLS + [LABEL_COL]:
            self.assertIn(col, self.df.columns, f"Missing column: {col}")

    def test_label_is_binary(self):
        unique = set(self.df[LABEL_COL].unique())
        self.assertTrue(unique.issubset({0, 1}), f"Labels must be 0 or 1, got: {unique}")

    def test_latitude_in_south_polar_range(self):
        self.assertTrue((self.df["latitude"] >= -90.0).all())
        self.assertTrue((self.df["latitude"] <= -65.0).all())

    def test_longitude_in_valid_range(self):
        self.assertTrue((self.df["longitude"] >= -180.0).all())
        self.assertTrue((self.df["longitude"] <= 180.0).all())

    def test_temperature_in_physical_range(self):
        self.assertTrue((self.df["temperature_k"] >= 40.0).all())
        self.assertTrue((self.df["temperature_k"] <= 210.0).all())

    def test_illumination_bounded(self):
        self.assertTrue((self.df["illumination_fraction"] >= 0.0).all())
        self.assertTrue((self.df["illumination_fraction"] <= 1.0).all())

    def test_radar_cpr_positive(self):
        self.assertTrue((self.df["radar_cpr"] >= 0.0).all())

    def test_seed_reproducibility(self):
        df1 = generate_synthetic_dataset(n_samples=100, seed=42)
        df2 = generate_synthetic_dataset(n_samples=100, seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_differ(self):
        df1 = generate_synthetic_dataset(n_samples=100, seed=1)
        df2 = generate_synthetic_dataset(n_samples=100, seed=999)
        self.assertFalse(df1["temperature_k"].equals(df2["temperature_k"]))

    def test_has_both_classes(self):
        """Physics rules must produce at least some ice_potential=1 samples."""
        counts = self.df[LABEL_COL].value_counts()
        self.assertIn(0, counts.index)
        self.assertIn(1, counts.index)

    def test_no_null_values(self):
        self.assertFalse(self.df.isnull().any().any(), "No nulls expected in synthetic data")

    def test_disclaimer_attribute(self):
        self.assertIn("SYNTHETIC", self.df.attrs.get("disclaimer", ""))


class TestCSVLoader(unittest.TestCase):

    def _make_csv(self, data: str) -> io.BytesIO:
        return io.BytesIO(data.encode("utf-8"))

    def test_valid_minimal_csv(self):
        csv = "latitude,longitude,temperature_k\n-89.0,0.0,85.0\n-88.0,10.0,90.0\n"
        df = load_csv(self._make_csv(csv))
        self.assertEqual(len(df), 2)
        self.assertIn("latitude", df.columns)

    def test_missing_required_column_raises(self):
        csv = "latitude,longitude\n-89.0,0.0\n"
        with self.assertRaises(DatasetValidationError):
            load_csv(self._make_csv(csv))

    def test_empty_csv_raises(self):
        csv = "latitude,longitude,temperature_k\n"
        with self.assertRaises(DatasetValidationError):
            load_csv(self._make_csv(csv))

    def test_optional_columns_filled_with_nan(self):
        csv = "latitude,longitude,temperature_k\n-89.0,0.0,85.0\n"
        df = load_csv(self._make_csv(csv))
        for col in OPTIONAL_FEATURE_COLS:
            self.assertIn(col, df.columns)
            self.assertTrue(df[col].isna().all())

    def test_out_of_range_temperature_raises(self):
        csv = "latitude,longitude,temperature_k\n-89.0,0.0,9999.0\n"
        with self.assertRaises(DatasetValidationError):
            load_csv(self._make_csv(csv))

    def test_source_attribute_set(self):
        csv = "latitude,longitude,temperature_k\n-89.0,0.0,85.0\n"
        df = load_csv(self._make_csv(csv))
        self.assertEqual(df.attrs.get("source"), "USER_CSV")


class TestGetFeatureMatrix(unittest.TestCase):

    def test_returns_correct_shape(self):
        df = generate_synthetic_dataset(n_samples=50, seed=1)
        X, names = get_feature_matrix(df)
        self.assertEqual(len(X), 50)
        self.assertTrue(len(names) > 0)

    def test_no_nulls_in_output(self):
        df = generate_synthetic_dataset(n_samples=50, seed=1)
        df.loc[0, "slope_deg"] = np.nan
        X, _ = get_feature_matrix(df)
        self.assertFalse(X.isnull().any().any())


# ──────────────────────────────────────────────────────────────────────────────
# Model Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestIceProbabilityModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = generate_synthetic_dataset(n_samples=300, seed=42)
        cls.model = IceProbabilityModel(n_estimators=50, max_depth=5, random_state=0)
        cls.metrics = cls.model.train(cls.df, test_size=0.25)

    def test_model_is_trained(self):
        self.assertTrue(self.model.is_trained)

    def test_metrics_type(self):
        self.assertIsInstance(self.metrics, ModelMetrics)

    def test_accuracy_reasonable(self):
        self.assertGreater(self.metrics.accuracy, 0.5, "Accuracy should exceed random chance")

    def test_roc_auc_above_random(self):
        self.assertGreater(self.metrics.roc_auc, 0.5)

    def test_confusion_matrix_shape(self):
        cm = self.metrics.confusion_matrix
        self.assertEqual(len(cm), 2)
        self.assertEqual(len(cm[0]), 2)

    def test_feature_names_nonempty(self):
        self.assertGreater(len(self.model.feature_names), 0)

    def test_predict_returns_correct_types(self):
        result = self.model.predict(self.df)
        self.assertIsInstance(result, PredictionResult)
        self.assertIsInstance(result.ice_probability, np.ndarray)
        self.assertIsInstance(result.predicted_class, np.ndarray)

    def test_probability_in_unit_interval(self):
        result = self.model.predict(self.df)
        self.assertTrue((result.ice_probability >= 0.0).all())
        self.assertTrue((result.ice_probability <= 1.0).all())

    def test_predicted_class_binary(self):
        result = self.model.predict(self.df)
        unique = set(result.predicted_class.tolist())
        self.assertTrue(unique.issubset({0, 1}))

    def test_predict_sample_count(self):
        result = self.model.predict(self.df)
        self.assertEqual(result.n_samples, len(self.df))

    def test_feature_importance_sums_to_one(self):
        fi = self.model.get_feature_importance()
        total = sum(fi.values())
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_predict_without_label_column(self):
        """Model should predict on unlabelled data too."""
        df_no_label = self.df.drop(columns=[LABEL_COL])
        result = self.model.predict(df_no_label)
        self.assertEqual(len(result.ice_probability), len(df_no_label))

    def test_untrained_model_raises_on_predict(self):
        untrained = IceProbabilityModel()
        with self.assertRaises(RuntimeError):
            untrained.predict(self.df)

    def test_train_without_label_raises(self):
        df_no_label = self.df.drop(columns=[LABEL_COL])
        fresh = IceProbabilityModel()
        with self.assertRaises(ValueError):
            fresh.train(df_no_label)

    def test_save_and_load_model(self, tmp_path=None):
        """Serialisation round-trip preserves predictions."""
        import tempfile
        import os

        df_small = generate_synthetic_dataset(n_samples=50, seed=7)
        m1 = IceProbabilityModel(n_estimators=20, max_depth=3)
        m1.train(df_small)
        r1 = m1.predict(df_small)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "model.pkl")
            m1.save(save_path)
            m2 = IceProbabilityModel.load(save_path)
            r2 = m2.predict(df_small)

        np.testing.assert_array_almost_equal(r1.ice_probability, r2.ice_probability, decimal=6)


if __name__ == "__main__":
    unittest.main()
