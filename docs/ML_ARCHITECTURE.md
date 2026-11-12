# HIMSETU — Machine Learning Architecture & Pipeline

## Overview
Machine Learning serves as the intelligence layer of HIMSETU. Its primary objective is to estimate whether a lunar region possesses physical characteristics consistent with subsurface water ice deposits using available scientifically relevant features. Model outputs are treated as probabilistic predictions, not direct physical proof of ice.

---

## ML Stage 1 — Problem Definition
* **Primary Task**: Binary Classification (`Potential Ice` vs. `No / Lower Ice Potential`) or Multi-class classification when scientifically justified.
* **Primary Model Output**: `ice_probability` ($\in [0.0, 1.0]$). Probability represents model belief under calibrated training assumptions, not direct physical ice concentration or thickness.

---

## ML Stage 2 — Data Collection & Multimodal Inputs
* **Radar**: DFSAR L-band & S-band Circular Polarization Ratio (CPR), backscatter coefficients.
* **Thermal**: Diviner maximum surface temperature, annual mean/minimum temperature, thermal inertia.
* **Terrain**: Lunar DEM elevation, surface slope, aspect, terrain roughness.
* **Lighting**: Solar illumination maps, PSR membership masks.
* **Geological / Contextual**: Crater catalog proximity, latitude, longitude, solar zenith angle.
* **Visual Imagery**: Contextual image layers used strictly for visual inspection and feature matching.

---

## ML Stage 3 — Data Validation & Preprocessing
* File and schema format validation.
* Metadata extraction and spatial coordinate reference system (CRS) alignment.
* Missing value detection without silent fabrication.
* Outlier handling and standardization/normalization ($Z$-score / MinMax scaling).
* Spatial resampling to unified grid resolution maintaining data provenance.

---

## ML Stage 4 — Feature Engineering
* **Radar Features**: L-band / S-band CPR ratios, polarization differences.
* **Thermal Features**: Maximum surface temperature thresholds ($T_{\max} < 110\text{ K}$ for surface stability), thermal amplitude.
* **Terrain Features**: Slope gradient, aspect direction, terrain ruggedness index (TRI).
* **Lighting Features**: Illumination fraction, PSR spatial masks.
* **Contextual Features**: Proximity to crater rims/floors, polar latitude distance.

---

## ML Stage 5 — Multi-Source Data Fusion (Core Innovation)
Combines compatible aligned features across sensor modalities into unified feature vectors:

$$\mathbf{x}_{\text{fused}} = \left[ \mathbf{x}_{\text{radar}} \;\Vert\; \mathbf{x}_{\text{thermal}} \;\Vert\; \mathbf{x}_{\text{terrain}} \;\Vert\; \mathbf{x}_{\text{lighting}} \;\Vert\; \mathbf{x}_{\text{context}} \right]$$

Fusion strategies:
1. **Aligned Raster Feature Stacks**: Pixel-aligned multi-band spatial rasters.
2. **Tabular Feature Fusion**: Spatial join across point/polygon vector features.

---

## ML Stage 6 — Candidate Model Architecture
* **Logistic Regression**: Baseline linear benchmark for interpretability.
* **Random Forest**: Non-linear tree ensemble providing feature importance rankings.
* **Gradient Boosting (XGBoost / LightGBM)**: High-performance tabular gradient boosting baseline.
* **Neural Network (PyTorch)**: Multi-layer perceptron (MLP) / Deep learning architecture for non-linear multi-sensor feature interaction when training sample size justifies it.

---

## ML Stage 7 — Training, Validation & Evaluation
* **Spatial Cross-Validation**: Spatial block splitting to prevent spatial data leakage between adjacent lunar pixels.
* **Evaluation Metrics**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, Precision-Recall AUC, and Confusion Matrices.
* **Imbalance Handling**: Class weighting / SMOTE techniques to handle sparse positive ice indicators.

---

## ML Stage 8 — Prediction Engine
Outputs for target spatial regions:
1. `predicted_class`: Binary label (`Potential Ice` / `Lower Potential`).
2. `ice_probability`: Calibrated confidence probability.
3. `prediction_metadata`: Model version, features used, and timestamp.

---

## ML Stage 9 — Uncertainty & Confidence Modeling
Computes a composite Confidence Index based on:
1. Model output probability calibration.
2. Input data completeness (fraction of active sensor layers available).
3. Spatial resolution and measurement quality metrics.

---

## ML Stage 10 — Explainable AI (XAI)
Provides interpretable explanations for predictions:
* **Feature Importance Ranking**: Global Gini / Permutation importance.
* **SHAP Values (SHapley Additive exPlanations)**: Local attribution showing exact feature contributions (e.g., $+0.35$ from Diviner temperature $<100\text{ K}$, $+0.25$ from High L-band CPR).

---

## ML Stage 11 — Ice Volume & Quantity Estimation (Optional / Advanced)
* Ice volume or thickness estimation is **only** performed when validated physical models and ground-truth calibration datasets exist.
* If physical calibration data is unavailable, ice volume features remain explicitly marked as **UNAVAILABLE / NOT VALIDATED**.

---

## ML Stage 12 — Model Management & Versioning
* Model artifact registration (parameters, hyperparameters, scalar artifacts).
* Training dataset hash tagging and dataset provenance tracking.
* Reproducible inference pipeline execution.
