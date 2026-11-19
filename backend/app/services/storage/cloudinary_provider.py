import io
import cloudinary
import cloudinary.api
import cloudinary.uploader
from fastapi import HTTPException, status

from app.services.storage.base import ProviderMetadata, StorageProvider


class CloudinaryStorageProvider(StorageProvider):
    metadata = ProviderMetadata(
        id="cloudinary",
        label="Cloudinary",
        description="Managed cloud media storage with global HTTPS CDN delivery and image optimization.",
        supports_cdn=True,
    )

    def __init__(
        self,
        cloud_name: str = "",
        api_key: str = "",
        api_secret: str = "",
        cloudinary_url: str = "",
        folder: str = "waste_reports",
    ) -> None:
        self.cloud_name = cloud_name.strip()
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.cloudinary_url = cloudinary_url.strip()
        self.folder = folder.strip() or "waste_reports"

    @property
    def is_configured(self) -> bool:
        return bool(self.cloudinary_url or (self.cloud_name and self.api_key and self.api_secret))

    def _configure(self) -> None:
        if not self.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Cloudinary storage is not configured. Configure credentials in "
                    "Admin Console -> Settings -> File Storage (or in backend/.env)."
                ),
            )
        if self.cloudinary_url and not (self.cloud_name and self.api_key and self.api_secret):
            cloudinary.config(cloudinary_url=self.cloudinary_url, secure=True)
        else:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True,
            )

    def upload(self, contents: bytes, public_id: str, extension: str, content_type: str) -> str:
        self._configure()
        try:
            result = cloudinary.uploader.upload(
                io.BytesIO(contents),
                folder=self.folder,
                public_id=public_id,
                resource_type="image",
                overwrite=False,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload image to Cloudinary: {exc}",
            ) from exc

        secure_url = result.get("secure_url")
        if not secure_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Cloudinary did not return a valid image URL.",
            )
        return str(secure_url)

    def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Missing Cloudinary credentials (cloud name, API key, and API secret)."
        try:
            self._configure()
            response = cloudinary.api.ping()
            if response.get("status") == "ok":
                return True, f"Connected to Cloudinary cloud '{self.cloud_name or 'configured'}' successfully."
            return False, f"Unexpected response from Cloudinary: {response}"
        except Exception as exc:
            return False, f"Cloudinary connection failed: {exc}"
