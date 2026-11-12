"""HimSetu Mini — Lunar Dataset Loader & Synthetic Data Generator.

Provides two data sources:
  1. SYNTHETIC_DATASET: Clearly labelled prototype dataset using
     physics-motivated rules for the lunar south polar region.
     *** NOT real measured ice labels. FOR DEMONSTRATION ONLY. ***
  2. load_csv(): Loads user-supplied CSV files, validates schema.

Reuses himsetu.ingestion validators where applicable.
"""

from __future__ import annotations

import io
import warnings
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# Column schema expected for the mini project
# ──────────────────────────────────────────────────────────────────────────────
REQUIRED_FEATURE_COLS = ["latitude", "longitude", "temperature_k"]
OPTIONAL_FEATURE_COLS = ["slope_deg", "illumination_fraction", "radar_cpr"]
LABEL_COL = "ice_potential"

ALL_FEATURE_COLS = REQUIRED_FEATURE_COLS + OPTIONAL_FEATURE_COLS
FEATURE_DESCRIPTIONS = {
    "latitude": "Selenographic latitude (degrees, −90 to 0)",
    "longitude": "Selenographic longitude (degrees, −180 to 180)",
    "temperature_k": "Max annual surface temperature (Kelvin) — Diviner-derived proxy",
    "slope_deg": "Terrain slope in degrees — DEM-derived",
    "illumination_fraction": "Fraction of time illuminated by Sun (0 = PSR, 1 = always lit)",
    "radar_cpr": "Radar Circular Polarization Ratio — DFSAR proxy (high CPR ≈ volume scattering)",
}

SYNTHETIC_DISCLAIMER = (
    "⚠️  SYNTHETIC / PROTOTYPE DATA — These are algorithmically generated labels "
    "using physics-motivated thresholds (Tmax < 110 K, PSR, high CPR). "
    "They are NOT real Chandrayaan-2 DFSAR or Diviner ice detections. "
    "This dataset is for college demonstration purposes only."
)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Synthetic Dataset Generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_synthetic_dataset(n_samples: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic lunar south polar dataset for Mini V1.0 demonstration.

    Physics-motivated labelling rules (NOT real science):
      ice_potential = 1 when ALL of:
        - temperature_k  < 110 K  (surface ice stability threshold)
        - illumination_fraction < 0.10  (near-PSR region)
        - radar_cpr  > 1.0   (indicative of volume scattering)

    *** SYNTHETIC DATA — NOT real lunar observations ***
    """
    rng = np.random.default_rng(seed)

    # Latitude: south polar region only (−90 to −65 degrees)
    latitudes = rng.uniform(-90.0, -65.0, n_samples)
    longitudes = rng.uniform(-180.0, 180.0, n_samples)

    # Temperature: higher near equator of study region, lower deep south
    # Base temp inversely correlated with |lat| — deeper = colder
    base_temp = 60 + (latitudes + 90) * 2.5 + rng.normal(0, 12, n_samples)
    temperature_k = np.clip(base_temp, 40.0, 210.0)

    # Slope: mostly gentle, some steep crater walls
    slope_deg = np.abs(rng.exponential(scale=8.0, size=n_samples))
    slope_deg = np.clip(slope_deg, 0.0, 45.0)

    # Illumination: strongly correlated with temperature
    illum_base = (temperature_k - 40) / 170.0
    illumination_fraction = np.clip(
        illum_base + rng.normal(0, 0.12, n_samples), 0.0, 1.0
    )

    # Radar CPR: high where ice suspected (inverse of illumination)
    cpr_base = 1.8 - illumination_fraction * 1.4 + rng.normal(0, 0.25, n_samples)
    radar_cpr = np.clip(cpr_base, 0.05, 3.0)

    # Physics-motivated label (NOT validated science)
    ice_potential = (
        (temperature_k < 110.0) &
        (illumination_fraction < 0.10) &
        (radar_cpr > 1.0)
    ).astype(int)

    df = pd.DataFrame({
        "latitude": latitudes.round(4),
        "longitude": longitudes.round(4),
        "temperature_k": temperature_k.round(2),
        "slope_deg": slope_deg.round(2),
        "illumination_fraction": illumination_fraction.round(4),
        "radar_cpr": radar_cpr.round(4),
        "ice_potential": ice_potential,
    })

    df.attrs["source"] = "SYNTHETIC"
    df.attrs["disclaimer"] = SYNTHETIC_DISCLAIMER
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 2. CSV Loader & Validator
# ──────────────────────────────────────────────────────────────────────────────

class DatasetValidationError(ValueError):
    """Raised when the uploaded CSV does not meet the schema requirements."""
    pass


def load_csv(path: str | Path | io.IOBase) -> pd.DataFrame:
    """Load and validate a user-supplied CSV file for the mini dashboard.

    Expected minimum columns: latitude, longitude, temperature_k
    Optional columns: slope_deg, illumination_fraction, radar_cpr, ice_potential

    Raises DatasetValidationError with a descriptive message if the schema
    or data quality does not meet requirements.
    """
    try:
        if isinstance(path, (str, Path)):
            df = pd.read_csv(path)
        else:
            df = pd.read_csv(path)
    except Exception as e:
        raise DatasetValidationError(f"Failed to read CSV file: {e}") from e

    if df.empty:
        raise DatasetValidationError("CSV file contains no data rows.")

    # Check required columns
    missing = [c for c in REQUIRED_FEATURE_COLS if c not in df.columns]
    if missing:
        raise DatasetValidationError(
            f"Missing required columns: {missing}. "
            f"Required: {REQUIRED_FEATURE_COLS}"
        )

    # Fill missing optional columns with NaN
    for col in OPTIONAL_FEATURE_COLS:
        if col not in df.columns:
            df[col] = np.nan
            warnings.warn(f"Optional column '{col}' not found — filled with NaN.", stacklevel=2)

    # Range checks
    lat_ok = df["latitude"].between(-90.0, 0.0)
    if not lat_ok.all():
        n_bad = (~lat_ok).sum()
        warnings.warn(
            f"{n_bad} rows have latitude outside lunar south polar range (−90 to 0°). "
            "These rows will be retained but flagged.",
            stacklevel=2,
        )

    temp_ok = df["temperature_k"].between(10.0, 400.0)
    if not temp_ok.all():
        n_bad = (~temp_ok).sum()
        raise DatasetValidationError(
            f"{n_bad} rows have temperature_k outside physically plausible range (10–400 K)."
        )

    df.attrs["source"] = "USER_CSV"
    df.attrs["disclaimer"] = (
        "User-supplied CSV. Verify that columns match expected lunar data definitions."
    )
    return df


def get_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Extract the feature matrix from a dataframe.

    Returns (X, feature_names) where X contains all available non-NaN feature columns.
    """
    available = [c for c in ALL_FEATURE_COLS if c in df.columns and df[c].notna().any()]
    X = df[available].copy()
    # Fill remaining NaN with column medians (not fabrication — imputation is explicit)
    for col in available:
        if X[col].isna().any():
            X[col].fillna(X[col].median(), inplace=True)
    return X, available
