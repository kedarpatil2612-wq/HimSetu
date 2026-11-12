# HIMSETU — Changelog

All notable changes to the HIMSETU project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-10-25

### Added — Milestone 3: Lunar Data Processing & REST API Backend
* **`himsetu/api/` package**: High-performance asynchronous REST API server built with FastAPI.
  - `app.py`: FastAPI application factory with CORS middleware, healthcheck routes, dependency injection, and automatic state wiring.
  - `schemas.py`: Pydantic request and response schemas for all API operations.
  - `routes/health.py`: Endpoints for `/health`, `/api/v1/health`, and `/api/v1/system/status`.
  - `routes/datasets.py`: REST CRUD endpoints for listing, detailed query, multipart file upload & ingestion, and dataset deletion.
  - `routes/processing.py`: Scientific REST endpoints for terrain extraction, spatial alignment, and multi-source feature cube stacking.
* **`himsetu/processing/` package**: Geospatial and geophysical analysis engine.
  - `coordinates.py`: Lunar South Pole Stereographic projection utilities (`IAU2000:30120`), exact forward & inverse transformations (`latlon_to_polar_stereo`, `polar_stereo_to_latlon`), and `BoundingBox` validation.
  - `terrain.py`: Morphology feature extraction from DEMs (`compute_slope`, `compute_aspect`, `compute_roughness`, `compute_terrain_features`).
  - `resampler.py`: Spatial grid resampling via bilinear and nearest-neighbor interpolation (`resample_array`, `resample_raster`).
  - `aligner.py`: `SpatialAligner` and `AlignedGrid` for harmonizing heterogeneous datasets onto a standardized polar grid.
  - `stacker.py`: `FeatureStacker` and `FeatureCube` for multi-source data fusion with explicit missing-feature tracking conforming to the zero-fabrication scientific rule.
* **`himsetu/db/` package**: SQLite persistence repository for datasets and asynchronous jobs.
  - `database.py`: Thread-safe SQLite database manager and schema initialization.
  - `repository.py`: `DatasetRepository` and `JobRepository` with CRUD and query capabilities.
* **CLI & Runner Enhancements**:
  - `main.py` & `himsetu/cli.py`: Integrated `serve` subcommand (`python main.py serve --port 8000`) powered by Uvicorn.
* **Automated Unit Tests**:
  - `tests/test_milestone_3.py`: 21 comprehensive test cases covering coordinates, terrain analysis, resampling, alignment, database persistence, and FastAPI endpoints.
  - Full suite now runs 76 passed tests (M1: 20, M2: 35, M3: 21).

### Changed
* `pyproject.toml` and `requirements.txt`: Bumped version to `0.3.0`; added `fastapi`, `uvicorn`, `python-multipart`, and `httpx`.
* `docs/MILESTONE_STATUS.md` and `docs/ROADMAP.md`: Updated to reflect Milestone 3 completion.

---

## [0.2.0] - 2026-10-25

### Added — Milestone 2: Lunar Data Ingestion Pipeline
* **`himsetu/ingestion/` package**: Complete modular data ingestion pipeline.
* **`FileDetector`** (`detector.py`): Extension + filename-keyword based file type and `DataCategory` detection (TERRAIN, THERMAL, RADAR, ILLUMINATION, GEOLOGICAL, IMAGERY, TABULAR, UNKNOWN).
* **`FileValidator`** (`validator.py`): File existence, type, and size checks returning structured `ValidationResult`.
* **`MetadataExtractor`** (`metadata.py`): Dispatcher orchestrating validation, detection, and format-handler dispatch into unified `DatasetMetadata` Pydantic records.
* **`DatasetRegistry`** (`registry.py`): JSON-backed persistent dataset registry with add, get, remove, list, count, and find-by-category operations.
* **Format Handlers** (`formats/`): Six dedicated handlers — CSV (row/column stats), GeoTIFF (CRS, bounds, resolution, bands via rasterio), GeoJSON (features, geometry types, bounds), NetCDF (soft-fail), PNG/JPEG (Pillow), Generic (TXT, JSON, HDF5 soft-fail).
* **`DatasetMetadata` Pydantic model** (`models.py`): Full provenance schema with spatial_info, tabular_info, vector_info, source_attribution, validation status, processing status, and UUID-based dataset_id.
* **`data/` directory structure**: `data/raw/`, `data/processed/`, `data/metadata/` — non-destructive storage layout.
* **M2 Unit Test Suite**: `tests/test_milestone_2.py` with 35/35 tests passing (55 total with M1).

### Changed
* `pyproject.toml`: version bumped to `0.2.0`; rasterio, numpy, pillow added as core dependencies; science extras added (netcdf4, h5py).
* `requirements.txt`: rasterio, numpy, pillow added.

### Not Changed (M1 Core Preserved)
* `himsetu/engine.py`, `himsetu/cli.py`, `himsetu/config.py`, `himsetu/commands.py`, `himsetu/permissions.py`, `himsetu/logging.py` — unchanged.
* `tests/test_milestone_1.py` — unchanged; all 20 tests still passing.

---

## [0.1.0] - 2026-09-02


### Added
* **Core Engine Baseline**: `HimSetuEngine` lifecycle state machine (`INITIALIZING`, `READY`, `PROCESSING`, `STOPPED`).
* **Configuration Module**: `AppConfig` supporting Pydantic validation, environment variables (`HIMSETU_`), and YAML configuration files.
* **Logging System**: Structured console and file logger via `rich` and standard Python `logging`.
* **Security Foundation**: `PermissionManager` and `PermissionLevel` hierarchy (`READ_ONLY`, `LOW_RISK`, `HIGH_RISK`, `ADMIN`).
* **Command System**: `CommandRegistry` and `IntentDispatcher` supporting intent parsing, permission checks, slash normalization, and structured `CommandResult` output.
* **Built-in CLI Commands**: `/help`, `/status`, `/config`, and `/exit`.
* **Interactive Terminal CLI**: `main.py` entrypoint providing terminal REPL loop.
* **Automated Unit Test Suite**: `tests/test_milestone_1.py` with 20/20 test cases passing cleanly.
* **Master Documentation Suite**:
  - `docs/PROJECT_MASTER_BLUEPRINT.md` (Project vision, scientific rules, 11-page web app layout)
  - `docs/ARCHITECTURE.md` (System flow diagram, tech stack, data architecture)
  - `docs/PROJECT_STRUCTURE.md` (Complete folder tree with M1 vs Future labels)
  - `docs/ROADMAP.md` (Frozen 8-milestone development timeline)
  - `docs/MILESTONE_STATUS.md` (Milestone matrix and completion metrics)
  - `docs/ML_ARCHITECTURE.md` (12-stage Machine Learning architecture & multi-sensor fusion plan)
  - `docs/CHANGELOG.md` (Initial release changelog)
