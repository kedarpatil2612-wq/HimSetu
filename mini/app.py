"""HimSetu Mini — Streamlit Dashboard.

Title: HimSetu Mini: AI-Based Lunar Ice Probability Prediction and Visualization
Version: 1.0 (College Mini Project Demonstration)

Run:
    .venv\\Scripts\\python.exe -m streamlit run mini/app.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Ensure the project root is importable regardless of CWD
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
import streamlit as st

from mini.dataset import (
    ALL_FEATURE_COLS,
    FEATURE_DESCRIPTIONS,
    OPTIONAL_FEATURE_COLS,
    REQUIRED_FEATURE_COLS,
    SYNTHETIC_DISCLAIMER,
    DatasetValidationError,
    generate_synthetic_dataset,
    get_feature_matrix,
    load_csv,
)
from mini.model import IceProbabilityModel, ModelMetrics, PredictionResult
from mini.visualizer import (
    plot_confusion_matrix,
    plot_correlation_heatmap,
    plot_feature_distributions,
    plot_feature_importance,
    plot_ice_probability_map,
    plot_probability_histogram,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HimSetu Mini — Lunar Ice Prediction",
    page_icon="🌕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #c9d1d9;
  }

  .main-header {
    background: linear-gradient(135deg, #1a1a5e 0%, #1c4e8f 50%, #0d3b6e 100%);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid #21262d;
  }

  .main-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0 0 0.3rem 0;
  }

  .main-header p {
    font-size: 0.95rem;
    color: #8b949e;
    margin: 0;
  }

  .metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
  }

  .metric-card .label {
    font-size: 0.8rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .metric-card .value {
    font-size: 1.7rem;
    font-weight: 700;
    color: #2e9ad0;
    margin: 0.2rem 0 0 0;
  }

  .disclaimer-box {
    background: #1c1f26;
    border-left: 4px solid #f5c518;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin: 0.8rem 0;
    font-size: 0.85rem;
    color: #c9a227;
  }

  .section-header {
    font-size: 1.15rem;
    font-weight: 600;
    color: #e6edf3;
    border-bottom: 2px solid #21262d;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
  }

  div[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #21262d;
  }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Session State Init
# ──────────────────────────────────────────────────────────────────────────────

if "df" not in st.session_state:
    st.session_state.df = None
if "model" not in st.session_state:
    st.session_state.model = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "pred_result" not in st.session_state:
    st.session_state.pred_result = None
if "data_source" not in st.session_state:
    st.session_state.data_source = "synthetic"


# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
  <h1>🌕 HimSetu Mini</h1>
  <p>AI-Based Lunar Ice Probability Prediction &amp; Visualization System &nbsp;·&nbsp;
     College Mini Project Demo &nbsp;·&nbsp; v1.0</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — Data Source & Controls
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🛰️ HimSetu Mini")
    st.markdown("---")

    st.markdown("#### 📂 Dataset")
    data_source = st.radio(
        "Select data source",
        options=["synthetic", "upload"],
        format_func=lambda x: "Synthetic Prototype Data" if x == "synthetic" else "Upload Your CSV",
        key="data_source_radio",
    )

    n_samples = 500
    if data_source == "synthetic":
        n_samples = st.slider("Synthetic samples", min_value=100, max_value=2000, value=500, step=50)
        seed = st.number_input("Random seed", min_value=0, max_value=9999, value=42)

        if st.button("🔄 Generate Dataset", use_container_width=True):
            with st.spinner("Generating synthetic lunar data..."):
                st.session_state.df = generate_synthetic_dataset(n_samples=n_samples, seed=int(seed))
                st.session_state.model = None
                st.session_state.metrics = None
                st.session_state.pred_result = None
                st.session_state.data_source = "synthetic"
            st.success(f"Generated {n_samples} synthetic samples.")

    else:
        uploaded = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help=f"Required columns: {REQUIRED_FEATURE_COLS}\nOptional: {OPTIONAL_FEATURE_COLS}",
        )
        if uploaded is not None:
            try:
                df_up = load_csv(io.BytesIO(uploaded.read()))
                st.session_state.df = df_up
                st.session_state.model = None
                st.session_state.metrics = None
                st.session_state.pred_result = None
                st.session_state.data_source = "csv"
                st.success(f"Loaded {len(df_up)} rows from {uploaded.name}.")
            except DatasetValidationError as e:
                st.error(f"Validation error: {e}")

    st.markdown("---")
    st.markdown("#### 🤖 Model")

    n_trees = st.slider("Number of trees", 50, 500, 200, step=50)
    max_depth = st.slider("Max tree depth", 3, 20, 10)
    test_frac = st.slider("Test set fraction", 0.10, 0.40, 0.25, step=0.05)

    train_disabled = st.session_state.df is None or "ice_potential" not in (
        st.session_state.df.columns if st.session_state.df is not None else []
    )

    if st.button("🚀 Train Model", disabled=train_disabled, use_container_width=True):
        with st.spinner("Training Random Forest model..."):
            model = IceProbabilityModel(n_estimators=n_trees, max_depth=max_depth)
            metrics = model.train(
                st.session_state.df,
                test_size=test_frac,
            )
            pred = model.predict(st.session_state.df)
            st.session_state.model = model
            st.session_state.metrics = metrics
            st.session_state.pred_result = pred
        st.success("Model trained successfully.")

    if train_disabled and st.session_state.df is not None:
        st.info("ℹ️ Upload a CSV with 'ice_potential' column to enable training.")

    st.markdown("---")
    st.caption("HimSetu Mini v1.0 · Lunar Science AI · College Mini Project")


# ──────────────────────────────────────────────────────────────────────────────
# Auto-load synthetic data on first run
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.df is None:
    with st.spinner("Loading default synthetic dataset..."):
        st.session_state.df = generate_synthetic_dataset(n_samples=500, seed=42)
        st.session_state.data_source = "synthetic"


df: pd.DataFrame = st.session_state.df
metrics: ModelMetrics | None = st.session_state.metrics
pred: PredictionResult | None = st.session_state.pred_result
model: IceProbabilityModel | None = st.session_state.model


# ──────────────────────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────────────────────

tabs = st.tabs([
    "📊 Dataset Overview",
    "🗺️ Ice Probability Map",
    "🤖 Model & Metrics",
    "🔬 Feature Analysis",
    "ℹ️ About",
])


# ─── Tab 1: Dataset Overview ──────────────────────────────────────────────────

with tabs[0]:
    st.markdown('<p class="section-header">📊 Dataset Overview</p>', unsafe_allow_html=True)

    if st.session_state.data_source == "synthetic":
        st.markdown(f'<div class="disclaimer-box">{SYNTHETIC_DISCLAIMER}</div>', unsafe_allow_html=True)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    ice_count = int(df["ice_potential"].sum()) if "ice_potential" in df.columns else 0
    ice_frac = ice_count / len(df) if len(df) > 0 else 0.0

    with col1:
        st.markdown(f'<div class="metric-card"><div class="label">Total Samples</div><div class="value">{len(df):,}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="label">Features</div><div class="value">{len([c for c in ALL_FEATURE_COLS if c in df.columns])}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="label">Ice Potential = 1</div><div class="value">{ice_count:,}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="label">Ice Fraction</div><div class="value">{ice_frac:.1%}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown("**Feature Descriptions**")
        desc_df = pd.DataFrame([
            {"Feature": k, "Description": v, "Present": "✅" if k in df.columns else "❌"}
            for k, v in FEATURE_DESCRIPTIONS.items()
        ])
        st.dataframe(desc_df, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("**Statistical Summary**")
        feat_cols = [c for c in ALL_FEATURE_COLS if c in df.columns]
        st.dataframe(df[feat_cols].describe().round(3), use_container_width=True)

    st.markdown("---")
    st.markdown("**Sample Data (first 20 rows)**")
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)


# ─── Tab 2: Ice Probability Map ───────────────────────────────────────────────

with tabs[1]:
    st.markdown('<p class="section-header">🗺️ Lunar Ice Probability Spatial Map</p>', unsafe_allow_html=True)

    if st.session_state.data_source == "synthetic":
        st.markdown(f'<div class="disclaimer-box">{SYNTHETIC_DISCLAIMER}</div>', unsafe_allow_html=True)

    ice_probs = pred.ice_probability if pred is not None else None
    fig_map = plot_ice_probability_map(df, ice_probability=ice_probs)
    st.plotly_chart(fig_map, use_container_width=True)

    if pred is None:
        st.info("🤖 Train the model from the sidebar to display AI-predicted ice probabilities. "
                "Currently showing ice_potential label values.")

    if pred is not None:
        st.markdown("---")
        col_x, col_y = st.columns(2)
        with col_x:
            st.markdown("**Ice Probability Distribution**")
            st.plotly_chart(plot_probability_histogram(pred.ice_probability), use_container_width=True)
        with col_y:
            high_ice = (pred.ice_probability >= 0.5).sum()
            st.markdown("**Prediction Summary**")
            st.metric("High Ice Probability Regions (≥ 0.5)", high_ice)
            st.metric("Low Ice Probability Regions (< 0.5)", len(pred.ice_probability) - high_ice)
            st.metric("Mean Ice Probability", f"{pred.ice_probability.mean():.3f}")
            st.metric("Max Ice Probability", f"{pred.ice_probability.max():.3f}")


# ─── Tab 3: Model & Metrics ───────────────────────────────────────────────────

with tabs[2]:
    st.markdown('<p class="section-header">🤖 Model Performance & Evaluation</p>', unsafe_allow_html=True)

    if metrics is None:
        st.info("👈 Train the model from the sidebar (click **Train Model**) to see evaluation results.")
    else:
        # Top metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        for container, label, val in [
            (m1, "Accuracy", f"{metrics.accuracy:.4f}"),
            (m2, "Precision", f"{metrics.precision:.4f}"),
            (m3, "Recall", f"{metrics.recall:.4f}"),
            (m4, "F1-Score", f"{metrics.f1:.4f}"),
            (m5, "ROC-AUC", f"{metrics.roc_auc:.4f}"),
        ]:
            container.markdown(
                f'<div class="metric-card"><div class="label">{label}</div><div class="value">{val}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        col_cm, col_fi = st.columns(2)
        with col_cm:
            st.markdown("**Confusion Matrix**")
            st.plotly_chart(plot_confusion_matrix(metrics.confusion_matrix), use_container_width=True)
        with col_fi:
            st.markdown("**Feature Importance**")
            fi = model.get_feature_importance()
            st.plotly_chart(plot_feature_importance(fi), use_container_width=True)

        st.markdown("---")
        st.markdown("**Full Classification Report**")
        st.code(metrics.classification_report)

        st.markdown("**Train / Test Split**")
        st.markdown(f"- Training samples: **{metrics.n_train}**")
        st.markdown(f"- Test samples: **{metrics.n_test}**")

        st.markdown("---")
        st.markdown(f'<div class="disclaimer-box">⚠️ {pred.disclaimer}</div>', unsafe_allow_html=True)


# ─── Tab 4: Feature Analysis ──────────────────────────────────────────────────

with tabs[3]:
    st.markdown('<p class="section-header">🔬 Feature Analysis</p>', unsafe_allow_html=True)

    feat_cols = [c for c in ALL_FEATURE_COLS if c in df.columns]

    st.markdown("**Feature Distributions by Ice Potential Class**")
    dist_cols = [c for c in feat_cols if c not in ("latitude", "longitude")]
    if dist_cols:
        fig_dist = plot_feature_distributions(df, dist_cols)
        st.plotly_chart(fig_dist, use_container_width=True)

    st.markdown("---")
    st.markdown("**Feature Correlation Matrix**")
    corr_cols = feat_cols + (["ice_potential"] if "ice_potential" in df.columns else [])
    fig_corr = plot_correlation_heatmap(df, corr_cols)
    st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")
    st.markdown("**Science Background: Ice Stability Indicators**")
    st.markdown("""
| Feature | Ice Favourable Range | Scientific Basis |
|:---|:---|:---|
| `temperature_k` | < 110 K | Water ice is thermally stable below ~110 K on the lunar surface |
| `illumination_fraction` | < 0.10 | Permanently Shadowed Regions (PSR) block solar heating |
| `radar_cpr` | > 1.0 | High Circular Polarization Ratio indicates volume scattering typical of ice |
| `slope_deg` | < 20° | Crater floors with gentle slopes more likely to host PSRs |

> **Note:** These are theoretical physics-based thresholds used to construct the synthetic dataset labels.
> They are **not** direct detections of ice. Real lunar ice characterisation requires multi-instrument cross-validation
> from Chandrayaan-1 M³, Chandrayaan-2 DFSAR/IIRS, LRO LEND/LAMP, and LCROSS impact data.
""")


# ─── Tab 5: About ─────────────────────────────────────────────────────────────

with tabs[4]:
    st.markdown('<p class="section-header">ℹ️ About HimSetu Mini</p>', unsafe_allow_html=True)

    st.markdown("""
### Project Overview

**HimSetu Mini** is a college mini project demonstrating AI-based lunar ice probability prediction,
derived from the larger **HimSetu** platform for AI-based subsurface lunar ice detection and mission planning.

**Full name:** HimSetu Mini: AI-Based Lunar Ice Probability Prediction and Visualization System

---

### System Architecture

```
mini/
├── app.py          ← This Streamlit dashboard
├── dataset.py      ← Dataset generation and CSV loader
├── model.py        ← IceProbabilityModel (scikit-learn Random Forest)
└── visualizer.py   ← Plotly charts and maps

himsetu/            ← Full HimSetu backend platform (reused)
├── ingestion/      ← File detection, validation, metadata
├── processing/     ← Terrain analysis, coordinate transforms
├── api/            ← FastAPI REST server (M3)
└── db/             ← SQLite persistence
```

---

### Technology Stack

| Component | Technology |
|:---|:---|
| Dashboard | Streamlit 1.35+ |
| ML Model | scikit-learn (Random Forest Classifier) |
| Data | Pandas + NumPy |
| Visualizations | Plotly |
| Core Engine | HimSetu v0.3.0 (FastAPI, Pydantic, rasterio) |

---

### Data Disclaimer

The synthetic dataset used in this demo was generated using physics-motivated labelling rules:
- Temperature threshold < 110 K (ice stability)  
- Illumination fraction < 0.10 (permanently shadowed region proxy)
- Radar CPR > 1.0 (volume scattering proxy)

**These are NOT real Chandrayaan-2 DFSAR or Diviner ice measurements.** The model outputs
are probabilistic estimates on synthetic prototype data only.

---

### Future Mega Project Roadmap (HimSetu V2.0)

| Milestone | Scope | Status |
|:---|:---|:---:|
| M4 — AI/ML Ice Detection Engine | Real multi-source data fusion, PyTorch/XGBoost | ⏳ Planned |
| M5 — Web Dashboard | React + TypeScript + CesiumJS 3D lunar map | ⏳ Planned |
| M6 — Mission Planning | Landing site scoring, A* rover path planning | ⏳ Planned |
| M7 — Validation & XAI | SHAP values, benchmark craters, explainability | ⏳ Planned |
| M8 — Docker Release | Containerized deployment, project report | ⏳ Planned |

---

### How to Run

```powershell
# Activate virtual environment
.venv\\Scripts\\Activate.ps1

# Launch dashboard
python -m streamlit run mini/app.py

# Run all tests
python -m pytest tests/ mini/tests/ -v
```
""")
