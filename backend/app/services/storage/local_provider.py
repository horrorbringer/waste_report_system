from pathlib import Path

from app.services.storage.base import ProviderMetadata, StorageProvider


class LocalStorageProvider(StorageProvider):
    metadata = ProviderMetadata(
        id="local",
        label="Local Disk Storage",
        description="Stores uploaded images on the backend server filesystem (ideal for offline development).",
        supports_cdn=False,
    )

    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir

    def upload(self, contents: bytes, public_id: str, extension: str, content_type: str) -> str:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{public_id}.{extension}"
        target_path = self.upload_dir / filename
        target_path.write_bytes(contents)
        return f"/uploads/{filename}"

    def test_connection(self) -> tuple[bool, str]:
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            probe = self.upload_dir / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True, f"Local upload directory '{self.upload_dir.name}/' is writable."
        except OSError as exc:
            return False, f"Local directory check failed: {exc}"
