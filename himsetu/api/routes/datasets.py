"""HIMSETU — Dataset Management & Ingestion REST Endpoints."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from himsetu.api.schemas import (
    DatasetDetailResponse,
    DatasetListResponse,
    DatasetSummary,
    UploadDatasetResponse,
)
from himsetu.ingestion.metadata import MetadataExtractor
from himsetu.ingestion.models import DatasetMetadata
from himsetu.ingestion.validator import FileValidator

router = APIRouter(prefix="/api/v1/datasets", tags=["Datasets"])


def _record_to_summary(meta: DatasetMetadata) -> DatasetSummary:
    """Convert DatasetMetadata into API response summary."""
    sp = meta.spatial_info
    min_lon = sp.bounds[0] if sp and sp.bounds and len(sp.bounds) >= 4 else None
    min_lat = sp.bounds[1] if sp and sp.bounds and len(sp.bounds) >= 4 else None
    max_lon = sp.bounds[2] if sp and sp.bounds and len(sp.bounds) >= 4 else None
    max_lat = sp.bounds[3] if sp and sp.bounds and len(sp.bounds) >= 4 else None
    crs = sp.crs if sp else None
    res = sp.resolution_m if sp else None
    tags = meta.extra.get("tags", [])

    return DatasetSummary(
        id=meta.dataset_id,
        name=meta.filename,
        file_path=meta.original_path,
        category=meta.data_category.value if hasattr(meta.data_category, "value") else str(meta.data_category),
        file_format=meta.format.value if hasattr(meta.format, "value") else str(meta.format),
        file_size_bytes=meta.file_size_bytes or 0,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        crs=crs,
        resolution_meters=res,
        tags=tags,
        created_at=meta.upload_timestamp,
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    request: Request,
    category: Optional[str] = None,
    file_format: Optional[str] = None,
    search: Optional[str] = None,
) -> DatasetListResponse:
    """List all registered lunar datasets with optional filters."""
    db_repo = getattr(request.app.state, "dataset_repo", None)
    registry = getattr(request.app.state, "registry", None)

    summaries = []
    if db_repo:
        rows = db_repo.list_all(category=category, file_format=file_format, search=search)
        for r in rows:
            summaries.append(
                DatasetSummary(
                    id=r["id"],
                    name=r["name"],
                    file_path=r["file_path"],
                    category=r["category"],
                    file_format=r["file_format"],
                    file_size_bytes=r["file_size_bytes"],
                    min_lat=r.get("min_lat"),
                    max_lat=r.get("max_lat"),
                    min_lon=r.get("min_lon"),
                    max_lon=r.get("max_lon"),
                    crs=r.get("crs"),
                    resolution_meters=r.get("resolution_meters"),
                    tags=r.get("tags", []),
                    created_at=r["created_at"],
                )
            )
    elif registry:
        for ds in registry.list_all():
            if category and ds.data_category.value != category:
                continue
            if file_format and ds.format.value != file_format:
                continue
            summaries.append(_record_to_summary(ds))

    return DatasetListResponse(count=len(summaries), datasets=summaries)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(dataset_id: str, request: Request) -> DatasetDetailResponse:
    """Retrieve detailed metadata for a single dataset."""
    db_repo = getattr(request.app.state, "dataset_repo", None)
    registry = getattr(request.app.state, "registry", None)

    if db_repo:
        rec = db_repo.get_by_id(dataset_id)
        if rec is not None:
            summary = DatasetSummary(
                id=rec["id"],
                name=rec["name"],
                file_path=rec["file_path"],
                category=rec["category"],
                file_format=rec["file_format"],
                file_size_bytes=rec["file_size_bytes"],
                min_lat=rec.get("min_lat"),
                max_lat=rec.get("max_lat"),
                min_lon=rec.get("min_lon"),
                max_lon=rec.get("max_lon"),
                crs=rec.get("crs"),
                resolution_meters=rec.get("resolution_meters"),
                tags=rec.get("tags", []),
                created_at=rec["created_at"],
            )
            return DatasetDetailResponse(dataset=summary, metadata=rec)

    if registry:
        ds = registry.get(dataset_id)
        if ds is not None:
            return DatasetDetailResponse(dataset=_record_to_summary(ds), metadata=ds.model_dump())

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Dataset with ID '{dataset_id}' not found.",
    )


@router.post("/upload", response_model=UploadDatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    custom_name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
) -> UploadDatasetResponse:
    """Upload and ingest a lunar dataset file (GeoTIFF, CSV, GeoJSON, etc.)."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    dest_path = raw_dir / file.filename
    try:
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {e}",
        )

    # 1. Validation
    validator = FileValidator()
    validation = validator.validate(dest_path)
    if validation.status.value != "VALID":
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file failed validation: {validation.notes}",
        )

    # 2. Extract metadata
    extractor = MetadataExtractor()
    meta = extractor.extract(dest_path, source_attribution=custom_name)

    if custom_name:
        meta.filename = custom_name

    if tags:
        parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]
        meta.extra.setdefault("tags", []).extend(parsed_tags)

    # 3. Save to Registry & SQLite DB
    registry = getattr(request.app.state, "registry", None)
    if registry:
        registry.add(meta)

    db_repo = getattr(request.app.state, "dataset_repo", None)
    if db_repo:
        db_repo.save(meta)

    summary = _record_to_summary(meta)

    return UploadDatasetResponse(
        success=True,
        message=f"Dataset '{meta.filename}' successfully ingested and registered.",
        dataset=summary,
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK)
async def delete_dataset(dataset_id: str, request: Request):
    """Unregister and remove dataset metadata."""
    db_repo = getattr(request.app.state, "dataset_repo", None)
    registry = getattr(request.app.state, "registry", None)

    deleted = False
    if db_repo:
        deleted = db_repo.delete(dataset_id)
    if registry:
        reg_del = registry.remove(dataset_id)
        deleted = deleted or reg_del

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )

    return {"success": True, "message": f"Dataset '{dataset_id}' successfully removed."}
