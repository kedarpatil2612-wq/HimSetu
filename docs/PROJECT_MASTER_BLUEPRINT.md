# HIMSETU — Complete Master Project Blueprint

## Project Vision
* **Project Name**: HIMSETU
* **Domain**: Lunar Science + AI/ML + Geospatial Analysis + Mission Planning
* **Project Type**: College Mini Project
* **One-Line Definition**: AI-Based Subsurface Lunar Ice Detection & Mission Planning System.

---

## 1. Core Vision & Objectives
HIMSETU is a lunar science software system designed to fuse multi-source lunar remote-sensing data, detect regions with high probability of subsurface water ice, evaluate confidence based on available evidence, and provide decision support for lunar landing-site selection and surface rover route planning.

### Core Scientific Principle: Multi-Source Data Fusion
HIMSETU does **NOT** rely on a single sensor or single data format. It combines available lunar data sources, including:
* DFSAR L-band radar
* DFSAR S-band radar
* Diviner thermal / temperature data
* DEM / Elevation models
* Derived Slope & Aspect
* Solar Illumination maps
* Permanently Shadowed Regions (PSR)
* Lunar Crater Databases
* Visual / Optical imagery & Video frames (when scientifically relevant)

---

## 2. Scientific Data Rules & Policy
1. **Zero Data Fabrication**: HIMSETU never generates fake lunar measurements, synthetic ice volume calculations, or artificial confidence metrics presented as real observations.
2. **Provenance & Source Attribution**: Original dataset sources (e.g. NASA PDS, ISRO ISDA repositories) and metadata are strictly preserved.
3. **Clear Output Categorization**:
   - Original / Source Data
   - Derived Features (e.g. slope from DEM)
   - ML Predictions (Probabilities, not physical proof of ice)
   - Mission Planning Recommendations

---

## 3. Complete Web Application Structure (11 Pages)
1. **DASHBOARD**: Overall mission status, dataset counts, high-potential regions, quick actions.
2. **ADD LUNAR DATA**: Manual upload (CSV, GeoTIFF, GeoJSON, NetCDF, HDF5, images, video) and API remote fetcher with file/metadata detection.
3. **LUNAR DATA EXPLORER**: Dataset registry, filtering, metadata inspector, variable/band viewer, and map previews.
4. **LUNAR MAP / REGION EXPLORER**: Interactive 2D/3D lunar map focused on south-pole regions, coordinates, PSR boundaries, craters, and data layers.
5. **ICE DETECTION**: Core AI/ML analysis page with dynamic dataset adaptation, feature selection, multi-source fusion, ice probability, confidence, and Explainable AI (SHAP/feature importance).
6. **LANDING SITE ANALYSIS**: Multi-criteria candidate landing zone evaluation balancing scientific value (ice proximity) against terrain risk (slope, illumination, crater hazards).
7. **ROVER PATH PLANNER**: Terrain-aware surface route planning avoiding high slopes and terrain hazards with distance/cost metrics.
8. **MISSION ANALYTICS**: Statistical dashboards, prediction distribution, dataset coverage, and landing/rover metric aggregations.
9. **ANALYSIS / RESULTS REPORT**: Comprehensive exportable scientific reports linking predictions to specific source datasets and model versions.
10. **SETTINGS**: System configurations, data directories, model settings, and secure API key management.
11. **ABOUT / DOCUMENTATION**: In-app documentation, problem statement, architecture specs, ML pipeline explanation, and scientific limitations.

---

## 4. Target Deliverables
* Fully modular Python backend core (`himsetu` engine & FastAPI REST server).
* React + TypeScript scientific web app interface.
* Multi-source data fusion and ice probability estimation engine (PyTorch + NumPy).
* Safe cost-surface rover pathfinding module (A* algorithm).
* Reproducible benchmark test suite and documentation baseline.
