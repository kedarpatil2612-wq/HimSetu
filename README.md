# 🌕 HimSetu Mini
### AI-Based Lunar Ice Probability Prediction and Visualization System

> **College Mini Project** | Derived from the HimSetu Mega Project (ISRO Hackathon PS8)

<p align="center">

[🚀 **LAUNCH LIVE DEMO**]( https://himsetu-cgpr6hrdbqvtjbkdkpmurr.streamlit.app/ )

</p>

**Live Application:**( https://himsetu-cgpr6hrdbqvtjbkdkpmurr.streamlit.app/)

---

## 📌 Overview

**HimSetu Mini** is a machine-learning-powered web application that predicts the probability of water-ice deposits at the **lunar south pole** using multi-sensor proxy features:

| Feature | Sensor Proxy | Ice Indicator |
|---|---|---|
| `temperature_k` | Diviner (LRO/Chandrayaan) | < 110 K |
| `illumination_fraction` | PSR mapping | < 0.10 (Permanently Shadowed) |
| `radar_cpr` | DFSAR (Chandrayaan-2) | > 1.0 (volume scattering) |
| `slope_deg` | Lunar DEM terrain | < 20° (stable surface) |

> ⚠️ **Disclaimer:** This version uses **synthetic prototype data** generated using physics-motivated thresholds. It is NOT real Chandrayaan-2 or Diviner ice detection data.

---

## 🚀 Quick Start

### 1. Install dependencies
```powershell
# Clone the repo
git clone https://github.com/kedarpatil2612-wq/HimSetu.git
cd HimSetu

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
pip install -r mini/requirements_mini.txt
```

### 2. Run the Mini Dashboard
```powershell
python -m streamlit run mini/app.py --server.headless true --browser.gatherUsageStats false
```
Then open **http://localhost:8501** in your browser.

### 3. Run all tests
```powershell
python -m pytest tests/ mini/tests/ -v
```

---

## 🖥️ Dashboard Features

| Tab | What You See |
|---|---|
| 📊 Dataset Overview | Sample data, stats, feature descriptions |
| 🗺️ Ice Probability Map | Lat/Lon scatter coloured by ice probability |
| 🤖 Model & Metrics | Accuracy, F1, ROC-AUC, confusion matrix, feature importance |
| 🔬 Feature Analysis | Violin plots, correlation heatmap, science background |
| ℹ️ About | Architecture, tech stack, roadmap |

---

## 📁 Project Structure

```text
HimSetu/
├── mini/                        ← Mini Project (this demo)
│   ├── app.py                   ← Streamlit dashboard (5 tabs)
│   ├── dataset.py               ← Synthetic data generator & CSV loader
│   ├── model.py                 ← IceProbabilityModel (Random Forest)
│   ├── visualizer.py            ← Plotly charts & maps
│   ├── requirements_mini.txt    ← Mini project dependencies
│   └── tests/
│       └── test_mini.py         ← Unit tests (31 tests)
│
├── himsetu/                     ← Full HimSetu Backend (Mega Project)
│   ├── engine.py                ← Core orchestration engine
│   ├── ingestion/               ← File detection, validation, metadata
│   ├── processing/              ← Terrain analysis, coordinates
│   ├── api/                     ← FastAPI REST server
│   └── db/                      ← SQLite persistence
│
├── tests/                       ← M1–M3 test suite (76 tests)
├── docs/                        ← Architecture docs & milestone status
├── data/raw/                    ← Sample datasets
└── requirements.txt             ← Core dependencies
```

---

## 🧠 ML Model

- **Algorithm**: Random Forest Classifier (scikit-learn)
- **Input Features**: temperature_k, slope_deg, illumination_fraction, radar_cpr, latitude, longitude
- **Output**: `ice_probability` ∈ [0.0, 1.0] per grid point
- **Class Balancing**: `class_weight="balanced"` to handle sparse positive labels
- **Evaluation**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix

---

## 🛣️ Full Roadmap (HimSetu Mega Project)

| Milestone | Description | Status |
|---|---|---|
| ✅ M1 | Core Engine, Config, CLI | Complete |
| ✅ M2 | Lunar Data Ingestion Pipeline | Complete |
| ✅ M3 | FastAPI Backend + SQLite | Complete |
| 🌟 Mini | AI Ice Probability Dashboard (this) | Complete |
| ⏳ M4 | Real Multi-source AI/ML Model | Planned |
| ⏳ M5 | React + CesiumJS 3D Lunar Map | Planned |
| ⏳ M6 | Landing Site Scoring + Rover Path | Planned |
| ⏳ M7 | SHAP Explainability + Validation | Planned |
| ⏳ M8 | Docker Deployment + Release | Planned |

---

## 📚 Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit |
| ML | scikit-learn (Random Forest) |
| Data | Pandas, NumPy |
| Visualizations | Plotly |
| API Backend | FastAPI + Uvicorn |
| Persistence | SQLite (via Python sqlite3) |
| Config | Pydantic + YAML |

---

## 👨‍💻 Author

**Kedar Patil** — College Mini Project, 2026  
Inspired by ISRO Hackathon Problem Statement PS8: Lunar Water Ice Detection

---

## 📄 License

MIT License — Free to use for educational purposes.
