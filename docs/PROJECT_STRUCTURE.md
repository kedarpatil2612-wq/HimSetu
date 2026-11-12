# HIMSETU — Complete Project Directory Structure

```text
HIMSETU/
│
├── .venv/                   [EXISTING - M1] Python 3.11 Virtual Environment
├── docs/                    [EXISTING - M1] Master Project Documentation
│   ├── ARCHITECTURE.md      - System pipeline & tech stack
│   ├── CHANGELOG.md         - Version changelog
│   ├── MILESTONE_STATUS.md  - Milestone completion matrix
│   ├── ML_ARCHITECTURE.md   - 12-stage machine learning architecture
│   ├── PROJECT_MASTER_BLUEPRINT.md - Vision & 11-page application blueprint
│   ├── PROJECT_STRUCTURE.md - Directory layout specification
│   └── ROADMAP.md           - Frozen 8-milestone roadmap
│
├── himsetu/                 [EXISTING - M1] Core Engine Package
│   ├── __init__.py          - Public API exports
│   ├── cli.py               - Terminal REPL interface
│   ├── commands.py          - Command registry & intent dispatcher
│   ├── config.py            - Pydantic application settings
│   ├── engine.py            - HimSetuEngine lifecycle state machine
│   ├── logging.py           - Structured logger configuration
│   └── permissions.py       - Security permission manager
│
├── tests/                   [EXISTING - M1] Unit Test Suite
│   └── test_milestone_1.py  - 20/20 verified test cases
│
├── main.py                  [EXISTING - M1] Application CLI Entrypoint
├── pyproject.toml           [EXISTING - M1] Build metadata & dependency declarations
├── requirements.txt         [EXISTING - M1] Python dependency specifications
│
├── backend/                 [FUTURE - M3] FastAPI Web Server & REST API Endpoints
├── frontend/                [FUTURE - M5] React + TypeScript Dashboard (Vite)
├── ai/                      [FUTURE - M4] Data Fusion & Ice Probability Models
├── data/                    [FUTURE - M2] Lunar Dataset Storage
│   ├── raw/                 - Raw uploaded raster/vector/tabular datasets
│   ├── processed/           - Aligned & preprocessed feature rasters
│   ├── metadata/            - JSON metadata records
│   └── models/              - Saved ML model weights and parameter artifacts
├── database/                [FUTURE - M3] PostgreSQL / SQLite persistence schema
├── shared/                  [FUTURE - M2] Shared schemas & TypeScript interfaces
└── deployment/              [FUTURE - M8] Dockerfile & deployment manifests
```

---

## Folder Status Summary
* **`[EXISTING - M1]`**: Implemented, tested, verified, and archived in Milestone 1.
* **`[FUTURE - M2 to M8]`**: Specified in roadmap; no source code files created yet.
