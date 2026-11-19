from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import SystemSetting, User
from app.schemas import (
    AdminSettingsResponse,
    AdminSettingsUpdate,
    CloudinarySettingsResponse,
    GeneralSettingsResponse,
    ProviderOptionResponse,
    S3SettingsResponse,
    StorageSettingsResponse,
)
from app.security import decrypt_secret, encrypt_secret, mask_secret
from app.services.storage.cloudinary_provider import CloudinaryStorageProvider
from app.services.storage.local_provider import LocalStorageProvider
from app.services.storage.s3_provider import S3CompatibleStorageProvider

SUPPORTED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

AVAILABLE_PROVIDERS = [
    CloudinaryStorageProvider.metadata,
    S3CompatibleStorageProvider.metadata,
    LocalStorageProvider.metadata,
]


@dataclass
class ResolvedSettings:
    # General
    site_name: str
    allow_registration: bool
    # Storage core
    storage_provider: str
    max_file_size_mb: int
    allowed_extensions: list[str]
    # Cloudinary
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    cloudinary_url: str
    cloudinary_folder: str
    # S3-Compatible (Sabay Cloud / AWS / R2 / MinIO)
    s3_endpoint_url: str
    s3_region: str
    s3_bucket: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_public_base_url: str
    s3_folder: str
    # Audit metadata
    last_updated_at: datetime | None = None
    last_updated_by: str | None = None


def _load_rows(db: Session) -> dict[str, SystemSetting]:
    rows = db.scalars(select(SystemSetting).options(joinedload(SystemSetting.editor))).all()
    return {row.key: row for row in rows}


def _read_plain(rows: dict[str, SystemSetting], key: str, fallback: str) -> str:
    row = rows.get(key)
    if row is None or row.value is None:
        return fallback
    return row.value


def _read_secret(rows: dict[str, SystemSetting], key: str, fallback: str) -> str:
    row = rows.get(key)
    if row is None or not row.value:
        return fallback
    decrypted = decrypt_secret(row.value)
    return decrypted if decrypted else fallback


def resolve_settings(db: Session) -> ResolvedSettings:
    """Resolve effective settings by merging PostgreSQL system_settings over .env defaults."""
    rows = _load_rows(db)

    raw_exts = _read_plain(
        rows,
        "storage.allowed_extensions",
        ",".join(sorted(settings.ALLOWED_EXTENSIONS)),
    )
    parsed_exts = [
        ext.strip().lower().lstrip(".")
        for ext in raw_exts.split(",")
        if ext.strip().lower().lstrip(".") in SUPPORTED_EXTENSIONS
    ]
    if not parsed_exts:
        parsed_exts = ["png", "jpg", "jpeg", "webp"]

    try:
        max_mb = int(
            _read_plain(
                rows,
                "storage.max_file_size_mb",
                str(max(1, settings.MAX_FILE_SIZE // (1024 * 1024))),
            )
        )
        max_mb = max(1, min(25, max_mb))
    except ValueError:
        max_mb = 5

    provider = _read_plain(rows, "storage.provider", settings.STORAGE_BACKEND).lower()
    if provider not in {"cloudinary", "s3_compatible", "local"}:
        provider = "cloudinary"

    allow_reg_raw = _read_plain(rows, "general.allow_registration", "true").lower()
    allow_registration = allow_reg_raw not in {"false", "0", "no"}

    latest_row = max(rows.values(), key=lambda r: r.updated_at, default=None)

    return ResolvedSettings(
        site_name=_read_plain(rows, "general.site_name", "EcoWatch"),
        allow_registration=allow_registration,
        storage_provider=provider,
        max_file_size_mb=max_mb,
        allowed_extensions=parsed_exts,
        cloudinary_cloud_name=_read_plain(rows, "cloudinary.cloud_name", settings.CLOUDINARY_CLOUD_NAME),
        cloudinary_api_key=_read_plain(rows, "cloudinary.api_key", settings.CLOUDINARY_API_KEY),
        cloudinary_api_secret=_read_secret(rows, "cloudinary.api_secret", settings.CLOUDINARY_API_SECRET),
        cloudinary_url=settings.CLOUDINARY_URL,
        cloudinary_folder=_read_plain(rows, "cloudinary.folder", settings.CLOUDINARY_FOLDER),
        s3_endpoint_url=_read_plain(rows, "s3.endpoint_url", settings.S3_ENDPOINT_URL),
        s3_region=_read_plain(rows, "s3.region", settings.S3_REGION),
        s3_bucket=_read_plain(rows, "s3.bucket", settings.S3_BUCKET),
        s3_access_key_id=_read_plain(rows, "s3.access_key_id", settings.S3_ACCESS_KEY_ID),
        s3_secret_access_key=_read_secret(rows, "s3.secret_access_key", settings.S3_SECRET_ACCESS_KEY),
        s3_public_base_url=_read_plain(rows, "s3.public_base_url", settings.S3_PUBLIC_BASE_URL),
        s3_folder=_read_plain(rows, "s3.folder", settings.S3_FOLDER),
        last_updated_at=latest_row.updated_at if latest_row else None,
        last_updated_by=latest_row.editor.full_name if (latest_row and latest_row.editor) else None,
    )


def _upsert_setting(
    db: Session,
    rows: dict[str, SystemSetting],
    key: str,
    value: str,
    category: str,
    admin_id: int,
    is_secret: bool = False,
) -> None:
    stored_value = encrypt_secret(value) if is_secret else value
    now = datetime.now(timezone.utc)
    existing = rows.get(key)
    if existing is None:
        entry = SystemSetting(
            key=key,
            value=stored_value,
            category=category,
            is_secret=is_secret,
            updated_by=admin_id,
            updated_at=now,
        )
        db.add(entry)
        rows[key] = entry
    else:
        existing.value = stored_value
        existing.category = category
        existing.is_secret = is_secret
        existing.updated_by = admin_id
        existing.updated_at = now


def update_settings(db: Session, payload: AdminSettingsUpdate, admin_user: User) -> ResolvedSettings:
    rows = _load_rows(db)

    clean_exts = [
        ext.strip().lower().lstrip(".")
        for ext in payload.storage.allowed_extensions
        if ext.strip().lower().lstrip(".") in SUPPORTED_EXTENSIONS
    ]
    if not clean_exts:
        clean_exts = ["png", "jpg", "jpeg", "webp"]

    # General settings
    _upsert_setting(db, rows, "general.site_name", payload.general.site_name.strip(), "general", admin_user.id)
    _upsert_setting(
        db,
        rows,
        "general.allow_registration",
        "true" if payload.general.allow_registration else "false",
        "general",
        admin_user.id,
    )

    # Storage core policy
    _upsert_setting(db, rows, "storage.provider", payload.storage.provider, "storage", admin_user.id)
    _upsert_setting(
        db,
        rows,
        "storage.max_file_size_mb",
        str(payload.storage.max_file_size_mb),
        "storage",
        admin_user.id,
    )
    _upsert_setting(
        db,
        rows,
        "storage.allowed_extensions",
        ",".join(dict.fromkeys(clean_exts)),
        "storage",
        admin_user.id,
    )

    # Cloudinary settings (preserve existing secret if blank or masked)
    _upsert_setting(
        db,
        rows,
        "cloudinary.cloud_name",
        payload.storage.cloudinary.cloud_name.strip(),
        "storage",
        admin_user.id,
    )
    _upsert_setting(
        db,
        rows,
        "cloudinary.api_key",
        payload.storage.cloudinary.api_key.strip(),
        "storage",
        admin_user.id,
    )
    _upsert_setting(
        db,
        rows,
        "cloudinary.folder",
        payload.storage.cloudinary.folder.strip() or "waste_reports",
        "storage",
        admin_user.id,
    )
    new_cld_secret = payload.storage.cloudinary.api_secret
    if new_cld_secret is not None and new_cld_secret.strip() and not new_cld_secret.startswith("••••"):
        _upsert_setting(
            db,
            rows,
            "cloudinary.api_secret",
            new_cld_secret.strip(),
            "storage",
            admin_user.id,
            is_secret=True,
        )

    # S3-Compatible settings (preserve existing secret if blank or masked)
    _upsert_setting(
        db, rows, "s3.endpoint_url", payload.storage.s3.endpoint_url.strip(), "storage", admin_user.id
    )
    _upsert_setting(
        db, rows, "s3.region", payload.storage.s3.region.strip() or "us-east-1", "storage", admin_user.id
    )
    _upsert_setting(db, rows, "s3.bucket", payload.storage.s3.bucket.strip(), "storage", admin_user.id)
    _upsert_setting(
        db, rows, "s3.access_key_id", payload.storage.s3.access_key_id.strip(), "storage", admin_user.id
    )
    _upsert_setting(
        db, rows, "s3.public_base_url", payload.storage.s3.public_base_url.strip(), "storage", admin_user.id
    )
    _upsert_setting(
        db,
        rows,
        "s3.folder",
        payload.storage.s3.folder.strip() or "waste_reports",
        "storage",
        admin_user.id,
    )
    new_s3_secret = payload.storage.s3.secret_access_key
    if new_s3_secret is not None and new_s3_secret.strip() and not new_s3_secret.startswith("••••"):
        _upsert_setting(
            db,
            rows,
            "s3.secret_access_key",
            new_s3_secret.strip(),
            "storage",
            admin_user.id,
            is_secret=True,
        )

    db.commit()
    return resolve_settings(db)


def to_admin_settings_response(resolved: ResolvedSettings) -> AdminSettingsResponse:
    return AdminSettingsResponse(
        general=GeneralSettingsResponse(
            site_name=resolved.site_name,
            allow_registration=resolved.allow_registration,
        ),
        storage=StorageSettingsResponse(
            provider=resolved.storage_provider,  # type: ignore[arg-type]
            max_file_size_mb=resolved.max_file_size_mb,
            allowed_extensions=resolved.allowed_extensions,
            cloudinary=CloudinarySettingsResponse(
                cloud_name=resolved.cloudinary_cloud_name,
                api_key=resolved.cloudinary_api_key,
                api_secret_masked=mask_secret(resolved.cloudinary_api_secret),
                has_api_secret=bool(resolved.cloudinary_api_secret or resolved.cloudinary_url),
                folder=resolved.cloudinary_folder,
            ),
            s3=S3SettingsResponse(
                endpoint_url=resolved.s3_endpoint_url,
                region=resolved.s3_region,
                bucket=resolved.s3_bucket,
                access_key_id=resolved.s3_access_key_id,
                secret_access_key_masked=mask_secret(resolved.s3_secret_access_key),
                has_secret_access_key=bool(resolved.s3_secret_access_key),
                public_base_url=resolved.s3_public_base_url,
                folder=resolved.s3_folder,
            ),
        ),
        available_providers=[
            ProviderOptionResponse(
                id=p.id,
                label=p.label,
                description=p.description,
                supports_cdn=p.supports_cdn,
            )
            for p in AVAILABLE_PROVIDERS
        ],
        last_updated_at=resolved.last_updated_at,
        last_updated_by=resolved.last_updated_by,
    )
