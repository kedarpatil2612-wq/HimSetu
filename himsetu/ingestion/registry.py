"""JSON-backed dataset registry for HIMSETU ingestion pipeline.

Persists DatasetMetadata records to a local JSON file.
No database server required in M2; PostgreSQL will be added in M3.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from himsetu.ingestion.models import DatasetMetadata


class DatasetRegistry:
    """Manages a persistent JSON-backed registry of ingested lunar datasets.

    Each record is stored by its dataset_id (UUID string) and
    serialised as a complete DatasetMetadata JSON object.

    Args:
        registry_path: Path to the JSON registry file.
                       Default: data/metadata/registry.json (relative to CWD).
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        if registry_path is None:
            registry_path = Path("data") / "metadata" / "registry.json"
        self._path = Path(registry_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, dict] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, dict]:
        """Load records from disk. Returns empty dict if file absent."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self) -> None:
        """Persist all records to disk."""
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def add(self, metadata: DatasetMetadata) -> str:
        """Register a dataset. Returns the dataset_id.

        If a record with the same dataset_id already exists it is
        overwritten (update semantics).
        """
        self._records[metadata.dataset_id] = metadata.model_dump(mode="json")
        self._save()
        return metadata.dataset_id

    def get(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """Retrieve a DatasetMetadata record by ID. Returns None if not found."""
        raw = self._records.get(dataset_id)
        if raw is None:
            return None
        return DatasetMetadata.model_validate(raw)

    def remove(self, dataset_id: str) -> bool:
        """Remove a record by ID. Returns True if removed, False if not found."""
        if dataset_id in self._records:
            del self._records[dataset_id]
            self._save()
            return True
        return False

    def list_all(self) -> List[DatasetMetadata]:
        """Return all registered DatasetMetadata records sorted by upload timestamp."""
        records = [
            DatasetMetadata.model_validate(raw)
            for raw in self._records.values()
        ]
        return sorted(records, key=lambda r: r.upload_timestamp)

    def count(self) -> int:
        """Return the total number of registered datasets."""
        return len(self._records)

    def find_by_category(self, category: str) -> List[DatasetMetadata]:
        """Return all records matching a given DataCategory string."""
        return [
            DatasetMetadata.model_validate(raw)
            for raw in self._records.values()
            if raw.get("data_category") == category
        ]

    def clear(self) -> None:
        """Remove all records (test utility — use with care)."""
        self._records = {}
        self._save()
