import asyncio
import io
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.config import settings
from app.services.settings_service import ResolvedSettings, resolve_settings
from app.services.storage.base import StorageProvider
from app.services.storage.cloudinary_provider import CloudinaryStorageProvider
from app.services.storage.local_provider import LocalStorageProvider
from app.services.storage.s3_provider import S3CompatibleStorageProvider

PIL_FORMAT_TO_EXT = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


def build_storage_provider(resolved: ResolvedSettings) -> StorageProvider:
    """Factory resolving the active StorageProvider from runtime settings."""
    if resolved.storage_provider == "cloudinary":
        return CloudinaryStorageProvider(
            cloud_name=resolved.cloudinary_cloud_name,
            api_key=resolved.cloudinary_api_key,
            api_secret=resolved.cloudinary_api_secret,
            cloudinary_url=resolved.cloudinary_url,
            folder=resolved.cloudinary_folder,
        )
    if resolved.storage_provider == "s3_compatible":
        return S3CompatibleStorageProvider(
            endpoint_url=resolved.s3_endpoint_url,
            region=resolved.s3_region,
            bucket=resolved.s3_bucket,
            access_key_id=resolved.s3_access_key_id,
            secret_access_key=resolved.s3_secret_access_key,
            public_base_url=resolved.s3_public_base_url,
            folder=resolved.s3_folder,
        )
    return LocalStorageProvider(upload_dir=settings.UPLOAD_DIR)


async def validate_and_upload_image(file: UploadFile, db: Session) -> str:
    """Validate uploaded image using live Admin Settings policy and Pillow, then upload via active provider."""
    resolved = resolve_settings(db)

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")

    allowed_exts = set(resolved.allowed_extensions)
    original_ext = Path(file.filename).suffix.lower().lstrip(".")
    if original_ext not in allowed_exts:
        allowed = ", ".join(sorted(allowed_exts))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{original_ext}'. Allowed: {allowed}.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    max_bytes = resolved.max_file_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {resolved.max_file_size_mb} MB.",
        )

    # Verify actual image binary content using Pillow before dispatching to cloud storage
    try:
        with Image.open(io.BytesIO(contents)) as img:
            img.verify()
        with Image.open(io.BytesIO(contents)) as img:
            detected_format = img.format
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image.",
        )

    if detected_format not in PIL_FORMAT_TO_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Please upload PNG, JPG, or WEBP.",
        )

    safe_ext, content_type = PIL_FORMAT_TO_EXT[detected_format]
    public_id = uuid.uuid4().hex
    provider = build_storage_provider(resolved)

    return await asyncio.to_thread(provider.upload, contents, public_id, safe_ext, content_type)
