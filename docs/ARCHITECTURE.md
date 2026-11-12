# HIMSETU — Complete System Architecture

## 1. System Pipeline Overview

```text
                 HIMSETU
                    │
          ┌─────────┴─────────┐
          │                   │
      DATA LAYER         WEB PLATFORM
          │                   │
          ▼                   ▼
   Data Ingestion       React Dashboard
          │
          ▼
   Data Validation
          │
          ▼
   Preprocessing
          │
          ▼
 Feature Engineering
          │
          ▼
 Multi-Source Fusion
          │
          ▼
      AI / ML
          │
          ▼
   Ice Probability
          │
          ▼
   Confidence Score
          │
          ▼
 Explainable AI
          │
          ├───────────────────┐
          │                   │
          ▼                   ▼
 Landing Analysis       Mission Analytics
          │
          ▼
 Rover Path Planning
          │
          ▼
 Mission Report
```

---

## 2. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React, TypeScript, Vite | User Interface & Scientific Mission Dashboard |
| **Backend** | Python 3.11, FastAPI, Uvicorn | High-Performance Asynchronous REST API Server |
| **CLI & Core Engine** | HimSetuEngine, Rich, Pydantic | Baseline REPL, config management, logging, security tiers |
| **AI / ML** | PyTorch, NumPy, scikit-learn, XGBoost | Multi-sensor data fusion, ice probability modeling, XAI |
| **Geospatial Processing** | Rasterio, GeoPandas, Shapely | GeoTIFF raster parsing, vector GIS operations, spatial alignment |
| **Visualization** | Leaflet, Plotly, CesiumJS | Interactive 2D/3D lunar spatial map and analytical charts |
| **Database & Storage** | PostgreSQL, Local File Storage | Dataset metadata, task results, raster tile storage |
| **Deployment** | Docker | Containerized web application deployment |

---

## 3. Data Architecture & Storage Layout

```text
data/
├── raw/         # Raw uploaded source files (GeoTIFF, CSV, GeoJSON, etc.)
├── processed/   # Preprocessed, reprojected, and aligned raster/tabular stacks
├── metadata/    # JSON metadata records and dataset provenance tags
└── models/      # Serialized ML model artifacts and scaler parameters
```

---

## 4. Dynamic Data Adaptation Rule
HIMSETU dynamically detects available data layers and enables matching analytical pipelines:

* **DEM Only**: Enables terrain analysis (elevation, slope, aspect).
* **Thermal Only**: Enables surface temperature & thermal stability analysis.
* **Radar Only**: Enables dielectric / CPR radar feature extraction.
* **Radar + Thermal + DEM + PSR**: Enables multi-source fusion and subsurface ice probability modeling.
* **Missing Layers**: Disables unsupported features with clear UI notifications (**UNAVAILABLE / REQUIRES MORE DATA**). Missing measurements are **NEVER** silently fabricated.
