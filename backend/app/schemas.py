from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ReportStatus = Literal["Pending", "In Progress", "Resolved"]
UserRole = Literal["resident", "admin"]
EmailField = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailField
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailField
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    name_km: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    description_km: str | None = Field(default=None, max_length=600)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(BaseModel):
    id: int
    name: str
    name_km: str | None = None
    description: str | None
    description_km: str | None = None
    created_at: datetime
    report_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class StatusHistoryResponse(BaseModel):
    id: int
    report_id: int
    changed_by: int
    actor_name: str
    actor_role: str
    old_status: str | None
    new_status: str
    note: str | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportUpdateStatus(BaseModel):
    status: ReportStatus
    note: str | None = Field(default=None, max_length=1000)


class ReportResponse(BaseModel):
    id: int
    user_id: int
    reporter_name: str
    reporter_email: str
    category_id: int
    category_name: str
    category_name_km: str | None = None
    title: str
    description: str
    location_text: str
    latitude: float | None
    longitude: float | None
    photo_path: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportDetailResponse(ReportResponse):
    status_history: list[StatusHistoryResponse] = []


class PublicStatsResponse(BaseModel):
    total_reports: int
    pending_reports: int
    in_progress_reports: int
    resolved_reports: int
    total_categories: int


class StatusDistributionItem(BaseModel):
    status: str
    count: int


class CategoryDistributionItem(BaseModel):
    category: str
    category_km: str | None = None
    count: int


class AdminDashboardStats(BaseModel):
    total_reports: int
    pending_count: int
    in_progress_count: int
    resolved_count: int
    total_users: int
    total_categories: int
    status_distribution: list[StatusDistributionItem]
    category_distribution: list[CategoryDistributionItem]
    recent_reports: list[ReportResponse]


StorageProviderId = Literal["cloudinary", "s3_compatible", "local"]


class ProviderOptionResponse(BaseModel):
    id: str
    label: str
    description: str
    supports_cdn: bool


class CloudinarySettingsResponse(BaseModel):
    cloud_name: str
    api_key: str
    api_secret_masked: str
    has_api_secret: bool
    folder: str


class S3SettingsResponse(BaseModel):
    endpoint_url: str
    region: str
    bucket: str
    access_key_id: str
    secret_access_key_masked: str
    has_secret_access_key: bool
    public_base_url: str
    folder: str


class StorageSettingsResponse(BaseModel):
    provider: StorageProviderId
    max_file_size_mb: int
    allowed_extensions: list[str]
    cloudinary: CloudinarySettingsResponse
    s3: S3SettingsResponse


class GeneralSettingsResponse(BaseModel):
    site_name: str
    allow_registration: bool


class AdminSettingsResponse(BaseModel):
    general: GeneralSettingsResponse
    storage: StorageSettingsResponse
    available_providers: list[ProviderOptionResponse]
    last_updated_at: datetime | None = None
    last_updated_by: str | None = None


class CloudinarySettingsUpdate(BaseModel):
    cloud_name: str = Field(default="", max_length=120)
    api_key: str = Field(default="", max_length=200)
    api_secret: str | None = Field(default=None, max_length=255)
    folder: str = Field(default="waste_reports", max_length=120)


class S3SettingsUpdate(BaseModel):
    endpoint_url: str = Field(default="", max_length=300)
    region: str = Field(default="us-east-1", max_length=80)
    bucket: str = Field(default="", max_length=150)
    access_key_id: str = Field(default="", max_length=200)
    secret_access_key: str | None = Field(default=None, max_length=255)
    public_base_url: str = Field(default="", max_length=300)
    folder: str = Field(default="waste_reports", max_length=120)


class StorageSettingsUpdate(BaseModel):
    provider: StorageProviderId
    max_file_size_mb: int = Field(default=5, ge=1, le=25)
    allowed_extensions: list[str] = Field(default_factory=lambda: ["png", "jpg", "jpeg", "webp"])
    cloudinary: CloudinarySettingsUpdate
    s3: S3SettingsUpdate


class GeneralSettingsUpdate(BaseModel):
    site_name: str = Field(..., min_length=2, max_length=120)
    allow_registration: bool = True


class AdminSettingsUpdate(BaseModel):
    general: GeneralSettingsUpdate
    storage: StorageSettingsUpdate


class StorageTestResponse(BaseModel):
    ok: bool
    provider: str
    message: str
