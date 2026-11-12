"""HIMSETU — Database Repositories for Datasets & Processing Jobs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from himsetu.db.database import Database
from himsetu.ingestion.models import DatasetMetadata, LunarDataCategory, FileFormat


class DatasetRepository:
    """CRUD repository for dataset metadata stored in SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, meta: Any) -> None:
        """Insert or replace a dataset record."""
        dataset_id = getattr(meta, "dataset_id", None) or str(uuid.uuid4())
        name = getattr(meta, "filename", None) or getattr(meta, "name", "dataset")
        file_path = getattr(meta, "original_path", None) or getattr(meta, "file_path", "")
        category_obj = getattr(meta, "data_category", None) or getattr(meta, "category", "UNKNOWN")
        category_val = category_obj.value if hasattr(category_obj, "value") else str(category_obj)
        format_obj = getattr(meta, "format", None) or getattr(meta, "file_format", "UNKNOWN")
        format_val = format_obj.value if hasattr(format_obj, "value") else str(format_obj)
        file_size = getattr(meta, "file_size_bytes", 0) or 0
        created_at = (
            getattr(meta, "upload_timestamp", None)
            or getattr(meta, "created_at", None)
            or datetime.now(timezone.utc).isoformat()
        )
        tags = getattr(meta, "tags", None) or getattr(meta, "extra", {}).get("tags", [])

        min_lat = getattr(meta, "min_lat", None)
        max_lat = getattr(meta, "max_lat", None)
        min_lon = getattr(meta, "min_lon", None)
        max_lon = getattr(meta, "max_lon", None)
        crs = getattr(meta, "crs", None)
        resolution = getattr(meta, "resolution_meters", None)

        spatial = getattr(meta, "spatial_info", None)
        if spatial:
            if crs is None:
                crs = spatial.crs
            if resolution is None:
                resolution = spatial.resolution_m
            if spatial.bounds and len(spatial.bounds) == 4 and min_lat is None:
                min_lon, min_lat, max_lon, max_lat = spatial.bounds

        tags_json = json.dumps(tags)
        query = """
        INSERT OR REPLACE INTO datasets (
            id, name, file_path, category, file_format, file_size_bytes,
            min_lat, max_lat, min_lon, max_lon, crs, resolution_meters,
            tags, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            conn.execute(
                query,
                (
                    dataset_id,
                    name,
                    file_path,
                    category_val,
                    format_val,
                    file_size,
                    min_lat,
                    max_lat,
                    min_lon,
                    max_lon,
                    crs,
                    resolution,
                    tags_json,
                    created_at,
                ),
            )
            conn.commit()

    def get_by_id(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single dataset by its unique dataset_id."""
        query = "SELECT * FROM datasets WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (dataset_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            res = dict(row)
            res["tags"] = json.loads(res.get("tags") or "[]")
            return res

    def list_all(
        self,
        category: Optional[str] = None,
        file_format: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List datasets with optional filtering."""
        query = "SELECT * FROM datasets WHERE 1=1"
        params: List[Any] = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if file_format:
            query += " AND file_format = ?"
            params.append(file_format)
        if search:
            query += " AND (name LIKE ? OR file_path LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term])

        query += " ORDER BY created_at DESC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["tags"] = json.loads(item.get("tags") or "[]")
                results.append(item)
            return results

    def delete(self, dataset_id: str) -> bool:
        """Delete a dataset by ID. Returns True if deleted."""
        query = "DELETE FROM datasets WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (dataset_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total count of datasets."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM datasets")
            return int(cursor.fetchone()[0])


class JobRepository:
    """CRUD repository for asynchronous processing jobs."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_job(
        self,
        job_id: str,
        job_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new job in PENDING status."""
        now = datetime.now(timezone.utc).isoformat()
        params_json = json.dumps(parameters or {})
        query = """
        INSERT INTO processing_jobs (id, job_type, status, parameters, created_at)
        VALUES (?, ?, 'PENDING', ?, ?)
        """
        with self.db.get_connection() as conn:
            conn.execute(query, (job_id, job_type, params_json, now))
            conn.commit()

        return {
            "id": job_id,
            "job_type": job_type,
            "status": "PENDING",
            "parameters": parameters or {},
            "created_at": now,
        }

    def update_status(
        self,
        job_id: str,
        status: str,
        output_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job execution status."""
        now = datetime.now(timezone.utc).isoformat() if status in ("COMPLETED", "FAILED") else None
        query = """
        UPDATE processing_jobs
        SET status = ?, output_path = COALESCE(?, output_path),
            error_message = COALESCE(?, error_message),
            completed_at = COALESCE(?, completed_at)
        WHERE id = ?
        """
        with self.db.get_connection() as conn:
            conn.execute(query, (status, output_path, error_message, now, job_id))
            conn.commit()

    def get_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch job record by ID."""
        query = "SELECT * FROM processing_jobs WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (job_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            res = dict(row)
            res["parameters"] = json.loads(res.get("parameters") or "{}")
            return res

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent processing jobs."""
        query = "SELECT * FROM processing_jobs ORDER BY created_at DESC LIMIT ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["parameters"] = json.loads(item.get("parameters") or "{}")
                results.append(item)
            return results
