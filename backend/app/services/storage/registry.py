import asyncio
import io
import logging
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from fastapi import HTTPException, UploadFile, status
from PIL import Image, features
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import ReportUploadPolicy
from app.services.settings_service import ResolvedSettings, resolve_settings
from app.services.storage.base import StorageProvider
from app.services.storage.cloudinary_provider import CloudinaryStorageProvider
from app.services.storage.local_provider import LocalStorageProvider
from app.services.storage.s3_provider import S3CompatibleStorageProvider

PIL_FORMAT_TO_EXT = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
    "AVIF": ("avif", "image/avif"),
}
MAX_REPORT_PHOTOS = 5
BYTES_PER_MB = 1024 * 1024
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidatedPhoto:
    file: UploadFile
    extension: str
    content_type: str
    size: int


def report_upload_policy(resolved: ResolvedSettings) -> ReportUploadPolicy:
    max_file_mb = resolved.max_file_size_mb
    max_total_mb = max_file_mb * MAX_REPORT_PHOTOS
    if os.environ.get("VERCEL") == "1":
        # Leave room for multipart headers and report fields under Vercel's request limit.
        max_total_mb = min(max_total_mb, 4)
        max_file_mb = min(max_file_mb, max_total_mb)

    return ReportUploadPolicy(
        max_file_size_mb=max_file_mb,
        allowed_extensions=[ext for ext in resolved.allowed_extensions if ext != "avif" or features.check("avif")],
        max_photos=MAX_REPORT_PHOTOS,
        max_total_size_mb=max_total_mb,
    )


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


def validate_image_contents(contents: bytes, original_ext: str) -> tuple[str, str]:
    try:
        with Image.open(io.BytesIO(contents)) as image:
            detected_format = image.format
            image.verify()
        if detected_format == "AVIF":
            with Image.open(io.BytesIO(contents)) as image:
                if image.is_animated:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a still AVIF photo.")
                image.load()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is not a valid image.") from exc

    detected = PIL_FORMAT_TO_EXT.get(detected_format or "")
    expected_extension = "jpg" if original_ext == "jpeg" else original_ext
    if not detected or detected[0] != expected_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The image format does not match its filename extension.",
        )
    return detected


async def validate_photo(file: UploadFile, policy: ReportUploadPolicy) -> ValidatedPhoto:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")

    original_ext = Path(file.filename).suffix.lower().lstrip(".")
    if original_ext not in policy.allowed_extensions:
        allowed = ", ".join(sorted(policy.allowed_extensions))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{original_ext}'. Allowed: {allowed}.",
        )

    max_bytes = policy.max_file_size_mb * BYTES_PER_MB
    contents = await file.read(max_bytes + 1)
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Each photo must be {policy.max_file_size_mb} MB or smaller.",
        )

    extension, content_type = await asyncio.to_thread(validate_image_contents, contents, original_ext)
    await file.seek(0)
    return ValidatedPhoto(file, extension, content_type, len(contents))


@asynccontextmanager
async def store_report_photos(files: list[UploadFile], db: Session) -> AsyncIterator[list[str]]:
    if not files:
        yield []
        return

    resolved = resolve_settings(db)
    policy = report_upload_policy(resolved)
    if len(files) > policy.max_photos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Attach up to {policy.max_photos} photos.")

    validated: list[ValidatedPhoto] = []
    total_bytes = 0
    for file in files:
        photo = await validate_photo(file, policy)
        total_bytes += photo.size
        if total_bytes > policy.max_total_size_mb * BYTES_PER_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All photos together must be {policy.max_total_size_mb} MB or smaller.",
            )
        validated.append(photo)

    provider = build_storage_provider(resolved)
    attempted: list[tuple[str, str]] = []
    paths: list[str] = []
    try:
        for photo in validated:
            public_id = uuid.uuid4().hex
            contents = await photo.file.read()
            attempted.append((public_id, photo.extension))
            upload = asyncio.create_task(
                asyncio.to_thread(provider.upload, contents, public_id, photo.extension, photo.content_type)
            )
            try:
                paths.append(await asyncio.shield(upload))
            except asyncio.CancelledError:
                # The worker can finish writing even if the request is cancelled.
                await asyncio.gather(upload, return_exceptions=True)
                raise
        yield paths
    except BaseException:
        for public_id, extension in reversed(attempted):
            try:
                await asyncio.to_thread(provider.delete, public_id, extension)
            except Exception:
                logger.warning("Could not remove failed report upload %s from %s", public_id, provider.metadata.id)
        raise


def delete_report_photos(photo_urls: list[str], db: Session) -> None:
    """Best-effort cleanup of stored report photos from the configured storage provider."""
    if not photo_urls:
        return

    resolved = resolve_settings(db)
    active_provider = build_storage_provider(resolved)
    local_provider = LocalStorageProvider(upload_dir=settings.UPLOAD_DIR)

    for url in photo_urls:
        if not url:
            continue
        parsed_path = urlparse(url).path
        filename = Path(parsed_path).name
        if "." not in filename:
            continue
        public_id = Path(filename).stem
        extension = Path(filename).suffix.lstrip(".").lower()
        if not public_id or not extension:
            continue

        target_provider = local_provider if url.startswith("/uploads/") else active_provider
        try:
            target_provider.delete(public_id, extension)
        except Exception:
            logger.warning("Could not delete report photo %s from %s", url, target_provider.metadata.id)
