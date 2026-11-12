# HIMSETU — 8-Milestone Development Roadmap

## Milestone Timeline

### ✅ Milestone 1: Core Foundation (v0.1.0) — COMPLETE
- [x] Baseline project structure setup (`himsetu` package).
- [x] Configuration system (Pydantic-backed `AppConfig` supporting YAML & environment variables).
- [x] Structured console and file logging module.
- [x] Security permission management framework (`READ_ONLY`, `LOW_RISK`, `HIGH_RISK`, `ADMIN`).
- [x] Command registry & intent dispatcher.
- [x] Interactive Terminal REPL CLI (`main.py`).
- [x] Comprehensive test suite (`20/20` unit tests passing).

---

### ✅ Milestone 2: Lunar Data Ingestion (v0.2.0) — COMPLETE
- [x] Manual upload pipeline (CSV, GeoTIFF, GeoJSON, JSON, TXT, NetCDF, HDF5, PNG, JPG, MP4).
- [x] API-ready remote data source connector architecture.
- [x] Dataset registry and provenance tracking.
- [x] Automated file type detection and format validation.
- [x] Metadata extractor (bounding coordinates, CRS, resolution, bands).
- [x] Raw data storage manager.

---

### ✅ Milestone 3: Backend APIs & Data Processing (v0.3.0) — COMPLETE
- [x] FastAPI application setup and CORS configuration.
- [x] Dataset management & upload REST APIs.
- [x] Data validation and preprocessing pipeline.
- [x] Spatial resolution alignment & coordinate reprojection (IAU2000:30120).
- [x] Database integration (SQLite metadata persistence and job tracking).
- [x] Comprehensive test suite (21 unit & integration tests passing).

---

### ⏳ Milestone 4: AI / ML Ice Detection Engine (Next Up)
- [ ] ML dataset preparation and spatial cross-validation splitting.
- [ ] Feature engineering (radar CPR, thermal stability, slope gradient, illumination).
- [ ] Multi-source data fusion module.
- [ ] Model training (Logistic Regression, Random Forest, XGBoost, PyTorch MLP).
- [ ] Ice probability estimation & probability calibration.
- [ ] Model artifact versioning and provenance tracking.

---

### 🌐 Milestone 5: Web Dashboard UI (Not Started)
- [ ] React + TypeScript + Vite project initialization.
- [ ] 11-page scientific application structure.
- [ ] Interactive 2D/3D lunar map integration (Leaflet / Plotly / CesiumJS).
- [ ] Real-time job status monitors & result visualizers.

---

### 🛰 Milestone 6: Mission Analytics & Path Planning (Not Started)
- [ ] Candidate landing site scoring module (ice potential vs. terrain hazards).
- [ ] Terrain-aware rover path planner (cost-surface A* routing algorithm).
- [ ] Mission risk report generator.

---

### 🧪 Milestone 7: System Validation & Analytics (Not Started)
- [ ] Model uncertainty and confidence scoring.
- [ ] Explainable AI (XAI) output generator (SHAP / Feature Importance).
- [ ] End-to-end integration testing against lunar polar benchmarks.
- [ ] Scientific limitations documentation.

---

### 🚀 Milestone 8: Final Integration & Deployment (Not Started)
- [ ] Full end-to-end integration and UI polish.
- [ ] Security review & performance optimization.
- [ ] Docker containerization.
- [ ] User documentation, project report, and presentation materials.
