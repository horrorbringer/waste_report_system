import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models import User
from app.schemas import AdminSettingsResponse, AdminSettingsUpdate, StorageTestResponse
from app.services.settings_service import (
    resolve_settings,
    to_admin_settings_response,
    update_settings,
)
from app.services.storage.registry import build_storage_provider

router = APIRouter(prefix="/api/admin/settings", tags=["Admin Settings"])


@router.get("", response_model=AdminSettingsResponse)
def get_admin_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("settings:manage")),
) -> AdminSettingsResponse:
    resolved = resolve_settings(db)
    return to_admin_settings_response(resolved)


@router.put("", response_model=AdminSettingsResponse)
def save_admin_settings(
    payload: AdminSettingsUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_permission("settings:manage")),
) -> AdminSettingsResponse:
    resolved = update_settings(db, payload, admin_user)
    return to_admin_settings_response(resolved)


@router.post("/storage/test", response_model=StorageTestResponse)
async def test_storage_connection(
    payload: AdminSettingsUpdate | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("settings:manage")),
) -> StorageTestResponse:
    """Test active (or unsaved draft) storage provider credentials live."""
    resolved = resolve_settings(db)

    if payload is not None:
        resolved.storage_provider = payload.storage.provider
        resolved.cloudinary_cloud_name = payload.storage.cloudinary.cloud_name.strip()
        resolved.cloudinary_api_key = payload.storage.cloudinary.api_key.strip()
        resolved.cloudinary_folder = payload.storage.cloudinary.folder.strip() or "waste_reports"
        if (
            payload.storage.cloudinary.api_secret
            and not payload.storage.cloudinary.api_secret.startswith("••••")
        ):
            resolved.cloudinary_api_secret = payload.storage.cloudinary.api_secret.strip()

        resolved.s3_endpoint_url = payload.storage.s3.endpoint_url.strip()
        resolved.s3_region = payload.storage.s3.region.strip() or "us-east-1"
        resolved.s3_bucket = payload.storage.s3.bucket.strip()
        resolved.s3_access_key_id = payload.storage.s3.access_key_id.strip()
        resolved.s3_public_base_url = payload.storage.s3.public_base_url.strip()
        resolved.s3_folder = payload.storage.s3.folder.strip() or "waste_reports"
        if (
            payload.storage.s3.secret_access_key
            and not payload.storage.s3.secret_access_key.startswith("••••")
        ):
            resolved.s3_secret_access_key = payload.storage.s3.secret_access_key.strip()

    provider = build_storage_provider(resolved)
    ok, message = await asyncio.to_thread(provider.test_connection)
    return StorageTestResponse(ok=ok, provider=resolved.storage_provider, message=message)
